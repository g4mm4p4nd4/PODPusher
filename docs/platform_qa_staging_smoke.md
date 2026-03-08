# Platform QA: Credential-Backed Staging Smoke

This smoke harness validates one non-stub `trend -> idea -> image -> listing` path when staging credentials are available.

## What Runs

- Test: `tests/test_staging_pipeline_smoke.py`
- Workflow: `.github/workflows/staging-smoke.yml` (manual `workflow_dispatch`)

The test is credential-gated:

- Skips unless `POD_STAGING_SMOKE=1`
- Fails fast if required credentials are missing
- Fails fast when `OPENAI_USE_STUB` is enabled
- Requires trend stage outputs with `trend_source == "live"` (fails on fallback trend seeds)
- Requires ideation and image stages to return `generation_source == "openai"`
- Requires image URLs, Printify SKUs, and Etsy listing identifiers/URLs to be non-stub values
- Calls integration service with `require_live=True` and explicit env-backed OAuth credential payloads for Printify and Etsy stages
- Workflow preflight exits early with a missing-secret list before running pytest
- Workflow emits `staging-smoke-junit.xml` and uploads it as `staging-smoke-junit` artifact on every run

## Required Secrets

- `OPENAI_API_KEY`
- `ETSY_CLIENT_ID`
- `ETSY_ACCESS_TOKEN`
- `ETSY_SHOP_ID`
- `PRINTIFY_API_KEY`
- `PRINTIFY_SHOP_ID`

## Flash-Stop Variance Decision (March 8, 2026)

Reviewed detached variance set: `bf81`, `7a5b`, `379d`, `df50`, `781e`, `f083`.

Decision for current smoke scope:
- Keep stub-toggle fail-fast to `OPENAI_USE_STUB` only.
- Do not require `STRIPE_SECRET_KEY` for this smoke path yet.

Rationale:
- This smoke validates trend -> idea -> image -> Printify -> Etsy behavior; billing execution is out of path.
- Adding billing-specific preflight checks would increase false blocking risk without improving this test's signal quality.
- The current credential set is sufficient for the exercised live integration chain.

## Local Dry Run

Without credentials (expected skip):

```bash
python -m pytest -q tests/test_staging_pipeline_smoke.py
```

With credentials (live smoke):

```bash
POD_STAGING_SMOKE=1 OPENAI_USE_STUB=0 ... python -m pytest -q tests/test_staging_pipeline_smoke.py
```

## Workflow Evidence

After a GitHub Actions run of `Staging Pipeline Smoke`:

- Open the `staging-smoke-junit` artifact from the workflow summary.
- Confirm `staging-smoke-junit.xml` exists and contains one executed smoke test.
- If credentials are not configured, expect an early failure in `Validate required staging secrets` listing missing names.
