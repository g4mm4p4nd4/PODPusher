# Scraper Outage Runbook

**Owner:** DevOps-Engineer (DO)
**Last Updated:** February 2026
**Reference:** `agents_dev_ops_engineer.md` §5, `agents_data_seeder.md` §6.1

---

## Overview

PODPusher's trend ingestion system scrapes 5 platforms (TikTok, Instagram, Twitter, Pinterest, Etsy) on a configurable schedule (default: every 6 hours via APScheduler). Each platform is protected by a per-platform **circuit breaker** that prevents cascading failures.

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
# Verify the trend_ingestion service is running
curl -s http://localhost:8000/healthz

# Check application logs
journalctl -u podpusher-trend-ingestion --since "1 hour ago" | grep -i "circuit\|scrape\|error"
```

### Step 2: Check Circuit Breaker States

```bash
curl -s http://localhost:8000/trends/scraper-status
```

If all platforms show `"open"`, the issue is likely systemic (proxy down, network issue). If only one platform is open, the issue is platform-specific.

### Step 3: Review Prometheus Metrics

Open the **Scraper Health** Grafana dashboard and check:

1. **Scrape Success vs Failure Rate** — identify which platform(s) are failing
2. **Scrape Duration (p50/p95/p99)** — look for latency spikes preceding failures
3. **Keywords Extracted** — if scrapes succeed but extract 0 keywords, selectors may need updating
4. **Circuit Breaker Open Events** — correlate with failure spikes

### Step 4: Check Logs for Root Cause

```bash
# Filter for specific platform
journalctl -u podpusher-trend-ingestion | grep "tiktok" | tail -50

# Common error patterns:
# - "TimeoutError" → site slow or blocking
# - "net::ERR_PROXY_CONNECTION_FAILED" → proxy down
# - "Navigation failed" → URL changed or site down
# - "Circuit breaker OPEN" → threshold exceeded
```

---

## 4. Manual Trend Refresh

Trigger an immediate scrape cycle (requires authentication):

```bash
# Replace <TOKEN> with a valid Bearer token or use X-User-Id header
curl -X POST http://localhost:8000/trends/refresh \
  -H "Authorization: Bearer <TOKEN>"

# Or with X-User-Id header
curl -X POST http://localhost:8000/trends/refresh \
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
   systemctl restart podpusher-trend-ingestion
   ```

3. **Verify** with a manual refresh:
   ```bash
   curl -X POST http://localhost:8000/trends/refresh -H "X-User-Id: 1"
   ```

4. **Monitor** the Grafana dashboard for improved success rates.

### Disabling Proxy (Direct Connection)

If no proxy is needed (e.g., development environment):

```bash
unset PLAYWRIGHT_PROXY
systemctl restart podpusher-trend-ingestion
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
   # - title: selectors for trend titles
   # - hashtags: selectors for hashtag elements
   # - likes/shares/comments: selectors for engagement counts
   ```

4. **Test locally** with stub mode disabled:
   ```bash
   TREND_INGESTION_STUB=0 python -c "
   import asyncio
   from services.trend_ingestion.service import _gather_trends
   results = asyncio.run(_gather_trends())
   print(f'Extracted {len(results)} trends')
   for r in results[:5]:
       print(f'  {r[\"source\"]}: {r[\"keyword\"]} (engagement: {r[\"engagement_score\"]})')
   "
   ```

5. **Deploy** the updated selectors and monitor for keyword extraction recovery.

---

## 8. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPE_INTERVAL_HOURS` | `6` | Hours between scheduled scrape cycles |
| `PLAYWRIGHT_PROXY` | (unset) | Proxy URL for Playwright browser (e.g., `http://proxy:8080`) |
| `TREND_INGESTION_TOP_K` | `5` | Max trends to persist per platform per cycle |
| `TREND_INGESTION_TIMEOUT_MS` | `15000` | Page load timeout in milliseconds |
| `TREND_INGESTION_STUB` | `1` | Set to `0` to enable live scraping |

---

## 9. Escalation

If the issue persists after following this runbook:

1. **First escalation:** Architect — for design-level issues with scraping architecture
2. **Second escalation:** Project-Manager — for prioritization and resource allocation
3. **Critical (all platforms down >1 hour):** DevOps-Engineer + CTO
4. **Unresolved >24h:** CTO

Per `agents.md` §6 escalation protocol.
