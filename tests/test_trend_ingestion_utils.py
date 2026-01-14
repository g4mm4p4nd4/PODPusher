
from services.trend_ingestion.service import normalize_text, compute_engagement, categorize, _parse_metric

def test_normalize_text_removes_emojis_and_stopwords():
    text = "The 🐶 Dog and THE Cat"
    assert normalize_text(text) == "dog cat"


def test_compute_engagement_sum():
    assert compute_engagement(1, 2, 3) == 6


def test_categorize_keyword():
    assert categorize("funny cat video") == "animals"
    assert categorize("unknown term") == "other"
def test_parse_metric_parses_suffixes():
    assert _parse_metric("1.5K") == 1500
    assert _parse_metric("2M") == 2000000
    assert _parse_metric("123") == 123


def test_parse_metric_handles_invalid():
    assert _parse_metric("") == 0
    assert _parse_metric("abc") == 0

