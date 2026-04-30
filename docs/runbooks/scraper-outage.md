# Scraper Outage Runbook

**Owner:** DevOps-Engineer (DO)
**Last Updated:** April 2026
**Reference:** `agents_dev_ops_engineer.md` §5, `agents_data_seeder.md` §6.1

---

## Overview

PODPusher's trend ingestion system scrapes public-only trend sources on a configurable schedule (default: every 6 hours via APScheduler). Current local sources are TikTok Creative Center, Instagram, X/Twitter, Pinterest, Etsy, Amazon, and Google Trends RSS fallback. Each live platform is protected by a per-platform **circuit breaker** that prevents cascading failures.

This runbook covers diagnosing and resolving scraper outages.

---

## 1. Alerting Thresholds

| Alert | Condition | Severity |
|-------|-----------|----------|
| `ScraperHighFailureRate` | >= 5% failure rate over 15m | Warning |
| `ScraperCriticalFailureRate` | >= 25% failure rate over 15m | Critical |
| `ScraperCircuitBreakerOpen` | Circuit breaker blocking requests | Warning |
| `ScraperNoActivity` | No scrape metrics for 30m | Warning |
| `ScraperSlowDuration` | p95 latency > 20s | Warning |
| `ScraperLowKeywordExtraction` | Successful scrapes but 0 keywords extracted | Warning |
| `ScraperFallbackSpike` | ScrapeGraphAI falls back to selectors repeatedly | Warning |
| `ScraperRssFallbackDominant` | Google Trends RSS supplies most successful trends | Warning |

Alert rules are defined in `prometheus/alerts/scraper.yml`. Grafana dashboard: **Scraper Health** (`grafana/dashboards/scraper-health.json`).

---

## 2. Circuit Breaker States

The circuit breaker (`services/trend_ingestion/circuit_breaker.py`) operates in three states:

### CLOSED (Normal)
- All scrape requests proceed normally.
- Failure counter tracks consecutive failures.
- Transitions to **OPEN** when failures >= `failure_threshold` (default: 3).

### OPEN (Tripped)
- All scrape requests for this platform are **blocked**.
- Metric: `pod_scrape_total{outcome="circuit_open"}` increments.
- Remains OPEN for `recovery_timeout` seconds (default: 300s / 5 minutes).
- Transitions to **HALF_OPEN** automatically after the timeout.

### HALF_OPEN (Probing)
- Allows `half_open_max_calls` (default: 1) test request through.
- If the test request **succeeds**: transitions back to **CLOSED**.
- If the test request **fails**: transitions back to **OPEN** immediately.

### Checking Circuit Breaker State

```bash
# Via the API endpoint (no auth required)
curl -s http://localhost:8000/trends/scraper-status | python -m json.tool
```

Expected response:
```json
{
  "tiktok": "closed",
  "instagram": "closed",
  "twitter": "closed",
  "pinterest": "closed",
  "etsy": "open"
}
```

---

## 3. Diagnosis Steps

### Step 1: Check Service Health

```bash
# Through the gateway
curl -s http://localhost:8000/healthz

# Direct trend ingestion service in Docker Compose
curl -s http://localhost:8007/healthz

# Check local Compose logs
docker compose logs --since=1h trend_ingestion | grep -i "circuit\|scrape\|error\|fallback"
```

### Step 2: Check Circuit Breaker States

```bash
curl -s http://localhost:8000/trends/scraper-status
```

If all platforms show `"open"`, the issue is likely systemic (proxy down, network issue). If only one platform is open, the issue is platform-specific.

### Step 3: Review Refresh Diagnostics

```bash
curl -s http://localhost:8000/api/trends/live/status | python -m json.tool
```

Check:

1. `last_mode` should be `live` for manual smoke.
2. `source_methods` should show `scrapegraph`, `selector_fallback`, or `rss_fallback`; `stub` means the live path was bypassed.
3. `source_diagnostics` should show per-source `status`, `method`, `collected`, `persisted`, and `updated_at`.
4. Fallbacks should include `fallback_from`, `fallback_to`, and `reason`.
5. Circuit-open sources should be listed in `sources_blocked` and `sources_skipped`; they increment `blocked_count` and `skipped_count` rather than being treated as fresh scrape failures.
6. Login, captcha, robot, HTTP 401/403/429, and forced login redirects should also appear as blocked/skipped sources with `method: blocked`. This is expected public-only degradation, not a reason to add cookies, exported browser sessions, usernames, passwords, or login URLs.

### Step 4: Review Prometheus Metrics

Open the **Scraper Health** Grafana dashboard and check:

1. **Scrape Success vs Failure Rate** — identify which platform(s) are failing
2. **Scrape Duration (p50/p95/p99)** — look for latency spikes preceding failures
3. **Keywords Extracted** — if scrapes succeed but extract 0 keywords, selectors may need updating
4. **Fallback Transitions** — `pod_scrape_fallback_total` shows source/method fallback pressure
5. **Circuit Breaker Open Events** — correlate with failure spikes

### Step 5: Check Logs for Root Cause

```bash
# Filter for specific platform
docker compose logs trend_ingestion | grep "tiktok" | tail -50

# Common error patterns:
# - "TimeoutError" → site slow or blocking
# - "net::ERR_PROXY_CONNECTION_FAILED" → proxy down
# - "Navigation failed" → URL changed or site down
# - "Circuit breaker OPEN" → threshold exceeded
# - "ScrapeGraphAI failed" → local Ollama/ScrapeGraphAI path unavailable
# - "Public page blocked or login gated" → source is refusing public extraction; verify it is counted in sources_blocked/sources_skipped
# - "Playwright browser executable unavailable" → local host is missing Playwright browsers; Docker image should provide them, while bare-host runs must not install browsers unless explicitly approved
```

---

## 4. Manual Trend Refresh

Trigger an immediate scrape cycle (requires authentication):

```bash
curl -X POST http://localhost:8000/api/trends/refresh \
  -H "X-User-Id: 1"
```

**Note:** Manual refresh still respects circuit breaker state. If a platform's breaker is OPEN, it will be skipped. Wait for the recovery timeout or manually reset the breaker (see below).

---

## 5. Manual Circuit Breaker Reset

The circuit breaker can be reset programmatically. Currently there is no dedicated API endpoint for this, so use a one-off script:

```python
# Run from project root
import asyncio
from services.trend_ingestion.circuit_breaker import scraper_circuit_breaker

# Reset a specific platform
scraper_circuit_breaker.reset("tiktok")
print("tiktok circuit breaker reset to CLOSED")

# Reset all platforms
for platform in ["tiktok", "instagram", "twitter", "pinterest", "etsy"]:
    scraper_circuit_breaker.reset(platform)
    print(f"{platform} circuit breaker reset to CLOSED")
```

After resetting, trigger a manual refresh to verify the platform is healthy.

---

## 6. Proxy Rotation Troubleshooting

Scrapers use Playwright with optional proxy support configured via the `PLAYWRIGHT_PROXY` environment variable.

### Verifying Proxy Configuration

```bash
# Check if proxy is set
echo $PLAYWRIGHT_PROXY

# Test proxy connectivity
curl -x $PLAYWRIGHT_PROXY https://httpbin.org/ip
```

### Common Proxy Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `net::ERR_PROXY_CONNECTION_FAILED` | Proxy server is down | Rotate to backup proxy or disable proxy |
| `407 Proxy Authentication Required` | Invalid proxy credentials | Update `PLAYWRIGHT_PROXY` with correct credentials |
| Scrapes succeed but return empty data | IP blocked by target site | Rotate proxy IP pool |
| High latency (>15s per scrape) | Proxy server overloaded | Switch to a lower-latency proxy provider |

### Rotating Proxies

1. **Update the environment variable:**
   ```bash
   export PLAYWRIGHT_PROXY="http://new-proxy-host:port"
   ```

2. **Restart the trend_ingestion service** to pick up the new proxy:
   ```bash
   docker compose restart trend_ingestion
   ```

3. **Verify** with a manual refresh:
   ```bash
   curl -X POST http://localhost:8000/api/trends/refresh -H "X-User-Id: 1"
   ```

4. **Monitor** the Grafana dashboard for improved success rates.

### Disabling Proxy (Direct Connection)

If no proxy is needed (e.g., development environment):

```bash
unset PLAYWRIGHT_PROXY
docker compose restart trend_ingestion
```

---

## 7. Selector Updates

If scrapes succeed but extract zero keywords (`ScraperLowKeywordExtraction` alert), the target platform likely changed its DOM structure.

### Steps to Update Selectors

1. **Identify the affected platform** from the Grafana dashboard or logs.

2. **Open the target URL manually** in a browser and inspect the new DOM structure:
   ```bash
   # Platform URLs are defined in services/trend_ingestion/sources.py
   grep -A2 "url=" services/trend_ingestion/sources.py
   ```

3. **Update selectors** in `services/trend_ingestion/sources.py`:
   ```python
   # Each platform has a SourceConfig with a SelectorSet:
   # - item: CSS selectors for content cards
   # - title: selectors for trend titles; image/ARIA/title attributes are used when visible text is empty
   # - hashtags: selectors for hashtag elements
   # - likes/shares/comments: selectors for engagement counts
   ```

4. **Test locally** with stub mode disabled:
   ```bash
   TREND_INGESTION_STUB=0 python -c "
   import asyncio
   from services.trend_ingestion.service import _gather_trends
   results, meta = asyncio.run(_gather_trends())
   print(meta)
   print(f'Extracted {len(results)} trends')
   for r in results[:5]:
       print(f'  {r[\"source\"]}: {r[\"keyword\"]} (engagement: {r[\"engagement_score\"]})')
   "
   ```

5. **Deploy** the updated selectors and monitor for keyword extraction recovery.

### April 30, 2026 Tuning Notes

Use this evidence when triaging local public-source failures:

| Source | Current behavior | Action |
|--------|------------------|--------|
| TikTok Creative Center | Public HTTP 200, but static text is mostly navigation and product-shell labels. | Do not persist shell labels; rely on ScrapeGraph/selector output only when keywords survive normalization. |
| Instagram | Public request returns a robot-gated shell. | Treat as blocked/skipped; do not add account-backed scraping. |
| X/Twitter | Explore redirects to login and JavaScript-gated flow. | Treat as blocked/skipped. |
| Pinterest | Today page exposes captcha markers in some runs and no selector-safe POD rows in others. | Treat captcha as blocked/skipped; otherwise accept a zero-persist selector failure and avoid CAPTCHA or account-backed workarounds. |
| Etsy | Trends and hub pages returned HTTP 403 captcha/JS gate. | Treat as blocked/skipped; keep Etsy API credentials out of this public trend slice. |
| Amazon | Movers and Shakers pages returned public product cards with useful `img alt` titles. | Keep Amazon Arts/Crafts first, then Handmade, Home/Garden, and Fashion; verify selectors still read `img[alt]` and reject brand/UI/bodywear noise plus gift-only phrases. |
| Google Trends RSS | Latest sample contained news/noise terms only. | RSS fallback should persist only concrete POD product nouns and otherwise report no usable RSS items. |

Latest Docker smoke evidence: a live refresh persisted 3 rows from Amazon/TikTok, skipped 2 blocked sources, failed 3 weak/noisy sources with zero persisted rows, and exposed `pod_scrape_method_total`, `pod_scrape_fallback_total`, and `pod_scrape_persisted_total` in Prometheus. Expected tuned behavior: blocked sources increase `blocked_count` and `skipped_count`, weak shell pages produce zero persisted rows instead of navigation keywords, ScrapeGraphAI attempts time out before selector fallback, and public product pages such as Amazon produce condensed POD-oriented phrases with provenance preserved in the live API.

---

## 8. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPE_INTERVAL_HOURS` | `6` | Hours between scheduled scrape cycles |
| `PLAYWRIGHT_PROXY` | (unset) | Proxy URL for Playwright browser (e.g., `http://proxy:8080`) |
| `TREND_INGESTION_TOP_K` | `5` | Max trends to persist per platform per cycle |
| `TREND_INGESTION_TIMEOUT_MS` | `15000` | Page load timeout in milliseconds |
| `TREND_INGESTION_MAX_SOURCE_URLS` | `2` | Max public candidate URLs to try per source during one refresh |
| `TREND_INGESTION_STUB` | `0` in local Compose | Set to `1` only for explicit stub mode |
| `TREND_INGESTION_RSS_FALLBACK` | `1` in local Compose | Set to `0` for strict live-source smoke tests with no Google Trends RSS rows |
| `TREND_INGESTION_ALLOW_STUB_FALLBACK` | `1` in local Compose | Set to `0` to return `live_empty` instead of seeded demo rows when all live sources fail |
| `SCRAPEGRAPH_MODEL` | `ollama/llama3.2` | Use `opencode-go/<model-id>` to route ScrapeGraphAI through OpenCode Go |
| `SCRAPEGRAPH_TIMEOUT_SECONDS` | `45` | Max ScrapeGraphAI wait before selector fallback for a public source URL |
| `OPENCODE_GO_API_KEY` | (unset) | API key for OpenCode Go ScrapeGraphAI model requests |
| `OPENCODE_GO_BASE_URL` | `https://opencode.ai/zen/go/v1` | OpenAI-compatible OpenCode Go API base URL used by ScrapeGraphAI |
| `SCRAPEGRAPH_OPENAI_BASE_URL` | (unset) | Generic OpenAI-compatible base URL for `oneapi/<model>` ScrapeGraphAI requests |
| `SCRAPEGRAPH_API_KEY` | (unset) | Generic API key for `oneapi/<model>` ScrapeGraphAI requests |

---

## 9. Escalation

If the issue persists after following this runbook:

1. **First escalation:** Architect — for design-level issues with scraping architecture
2. **Second escalation:** Project-Manager — for prioritization and resource allocation
3. **Critical (all platforms down >1 hour):** DevOps-Engineer + CTO
4. **Unresolved >24h:** CTO

Per `agents.md` §6 escalation protocol.
