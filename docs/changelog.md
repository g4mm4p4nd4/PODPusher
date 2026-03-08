# Changelog

## Unreleased
- Added internationalization with English and Spanish translations.
- New language switcher allows changing locale in the dashboard.
- Replaced analytics mock keyword feed with live aggregation from trend ingestion data (`TrendSignal`) plus `Trend` fallback, with validated query bounds and expanded backend tests.
- Hardened live integration validation for Printify and Etsy: live mode now accepts env-backed shop IDs, rejects missing live identifiers, and includes focused service/API test coverage.
- Added trend source provenance (`live` vs `fallback`) to trend scraper outputs and tightened staging smoke to fail when fallback trend seeds are used.
- Removed hardcoded billing webhook ownership fallback (`user_id=1`) by resolving subscription ownership from metadata or `cus_stub_<user_id>` and added focused billing tests for stub-path ownership mapping.
- Removed header-only auth assumption in quota and gateway rate-limit middleware by resolving Bearer session user IDs, with new focused tests for authenticated middleware behavior.
