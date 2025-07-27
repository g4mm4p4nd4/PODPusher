import json
import os
from pathlib import Path

EN_FILE = Path('client/locales/en/common.json')
ES_FILE = Path('client/locales/es/common.json')


def flatten(d, prefix=''):
    keys = []
    for k, v in d.items():
        if isinstance(v, dict):
            keys.extend(flatten(v, f"{prefix}{k}."))
        else:
            keys.append(f"{prefix}{k}")
    return keys


def test_translation_keys_match():
    with EN_FILE.open() as f:
        en = json.load(f)
    with ES_FILE.open() as f:
        es = json.load(f)
    assert set(flatten(en)) == set(flatten(es))
