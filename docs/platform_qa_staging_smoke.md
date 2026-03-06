# Platform QA: Credential-Backed Staging Smoke

This smoke harness validates one non-stub `trend -> idea -> image -> listing` path when staging credentials are available.

## What Runs

- Test: `tests/test_staging_pipeline_smoke.py`
- Workflow: `.github/workflows/staging-smoke.yml` (manual `workflow_dispatch`)

The test is credential-gated:

- Skips unless `POD_STAGING_SMOKE=1`
- Fails fast if required credentials are missing
- Requires non-stub results from Printify and Etsy stages

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