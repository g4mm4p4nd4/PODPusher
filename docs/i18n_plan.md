# i18n Expansion Plan

This document outlines the next steps for broadening localisation coverage.

## Objectives
- Extend translations beyond the dashboard shell to include analytics, scheduling, and bulk upload flows.
- Introduce locale-aware currency/number formatting in both backend serializers and frontend components.
- Add automated lint/check to detect missing translation keys during CI (see `scripts/verify_translations.py`).

## Action Items
1. Audit "client/" for hard-coded strings. Track findings in a localisation backlog.
2. Generate translation extraction script (e.g., "scripts/i18n_extract.ts") that outputs new keys for translators.
3. Integrate ICU formatting for currency/units using Intl.NumberFormat and ensure server responses supply locale metadata.
4. Expand Playwright tests to cover language switching scenarios.
5. Coordinate with Docs team to add style guide for translators.

