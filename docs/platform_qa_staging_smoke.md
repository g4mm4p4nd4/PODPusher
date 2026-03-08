# Platform QA: Credential-Backed Staging Smoke

This smoke harness validates one non-stub `trend -> idea -> image -> listing` path when staging credentials are available.

## What Runs

- Test: `tests/test_staging_pipeline_smoke.py`
- Workflow: `.github/workflows/staging-smoke.yml` (manual `workflow_dispatch`)

The test is credential-gated:

- Skips unless `POD_STAGING_SMOKE=1`
- Fails fast if required credentials are missing
- Requires trend stage outputs with `trend_source == "live"` (fails on fallback trend seeds)
- Calls integration service with `require_live=True` for Printify and Etsy stages
- Workflow preflight exits early with a missing-secret list before running pytest
- Workflow emits `staging-smoke-junit.xml` and uploads it as `staging-smoke-junit` artifact on every run

## Required Secrets

- `OPENAI_API_KEY`
- `ETSY_CLIENT_ID`
- `ETSY_ACCESS_TOKEN`
- `ETSY_SHOP_ID`
- `PRINTIFY_API_KEY`
- `PRINTIFY_SHOP_ID`

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
