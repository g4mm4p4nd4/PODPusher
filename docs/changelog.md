# Changelog

## Unreleased
- Added internationalization with English and Spanish translations.
- New language switcher allows changing locale in the dashboard.
- Replaced analytics mock keyword feed with live aggregation from trend ingestion data (`TrendSignal`) plus `Trend` fallback, with validated query bounds and expanded backend tests.
- Hardened live integration validation for Printify and Etsy: live mode now accepts env-backed shop IDs, rejects missing live identifiers, and includes focused service/API test coverage.
