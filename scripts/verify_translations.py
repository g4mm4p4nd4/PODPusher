import json
from pathlib import Path
import sys

BASE_LOCALE = 'en'
TRANSLATIONS_DIR = Path('client/locales')


def load_locale(locale: str) -> dict:
    path = TRANSLATIONS_DIR / locale / 'common.json'
    if not path.exists():
        raise FileNotFoundError(f'missing translation file: {path}')
    with path.open(encoding='utf-8') as fh:
        return json.load(fh)


def flatten(data: dict, prefix: str = '') -> dict:
    items = {}
    for key, value in data.items():
        full_key = f'{prefix}{key}' if not prefix else f'{prefix}.{key}'
        if isinstance(value, dict):
            items.update(flatten(value, full_key))
        else:
            items[full_key] = value
    return items


def main() -> None:
    base = flatten(load_locale(BASE_LOCALE))
    locales = [p.name for p in TRANSLATIONS_DIR.iterdir() if p.is_dir() and p.name != BASE_LOCALE]
    missing = {}
    for locale in locales:
        current = flatten(load_locale(locale))
        missing_keys = sorted(set(base) - set(current))
        if missing_keys:
            missing[locale] = missing_keys
    if missing:
        print('Missing translation keys:')
        for locale, keys in missing.items():
            print(f'  {locale}:')
            for key in keys:
                print(f'    - {key}')
        sys.exit(1)
    print('All translation files contain the base keys.')


if __name__ == '__main__':
    main()
