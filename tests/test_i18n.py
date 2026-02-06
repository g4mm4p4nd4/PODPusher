"""Translation key verification tests.

Owner: Unit-Tester (per DEVELOPMENT_PLAN.md Task 1.1)
Reference: FC §7 (Internationalisation)

Ensures all locale files have identical key sets to prevent
missing translations at runtime.
"""
import json
from pathlib import Path

import pytest

LOCALES_DIR = Path('client/locales')
EN_FILE = LOCALES_DIR / 'en' / 'common.json'
ES_FILE = LOCALES_DIR / 'es' / 'common.json'
FR_FILE = LOCALES_DIR / 'fr' / 'common.json'
DE_FILE = LOCALES_DIR / 'de' / 'common.json'

ALL_LOCALE_FILES = {
    'es': ES_FILE,
    'fr': FR_FILE,
    'de': DE_FILE,
}


def flatten(d, prefix=''):
    keys = []
    for k, v in d.items():
        if isinstance(v, dict):
            keys.extend(flatten(v, f"{prefix}{k}."))
        else:
            keys.append(f"{prefix}{k}")
    return keys


def load_keys(filepath: Path) -> set:
    with filepath.open() as f:
        data = json.load(f)
    return set(flatten(data))


@pytest.fixture
def en_keys():
    return load_keys(EN_FILE)


def test_en_locale_file_exists():
    assert EN_FILE.exists(), "English locale file missing"


@pytest.mark.parametrize("locale,filepath", list(ALL_LOCALE_FILES.items()))
def test_locale_file_exists(locale, filepath):
    assert filepath.exists(), f"{locale} locale file missing at {filepath}"


@pytest.mark.parametrize("locale,filepath", list(ALL_LOCALE_FILES.items()))
def test_translation_keys_match(locale, filepath, en_keys):
    target_keys = load_keys(filepath)
    missing = en_keys - target_keys
    extra = target_keys - en_keys
    assert not missing, f"{locale} missing keys: {missing}"
    assert not extra, f"{locale} has extra keys: {extra}"


def test_en_has_minimum_key_count(en_keys):
    # Ensure we have a reasonable number of translation keys
    assert len(en_keys) >= 100, f"EN only has {len(en_keys)} keys, expected >=100"


def test_four_locales_configured():
    """Verify all 4 required locales have files."""
    for locale in ['en', 'es', 'fr', 'de']:
        locale_file = LOCALES_DIR / locale / 'common.json'
        assert locale_file.exists(), f"Missing locale: {locale}"
