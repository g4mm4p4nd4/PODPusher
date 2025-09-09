from services.trend_ingestion.service import normalize_text, compute_engagement, categorize


def test_normalize_text_removes_emojis_and_stopwords():
    text = "The 🐶 Dog and THE Cat"
    assert normalize_text(text) == "dog cat"


def test_compute_engagement_sum():
    assert compute_engagement(1, 2, 3) == 6


def test_categorize_keyword():
    assert categorize("funny cat video") == "animals"
    assert categorize("unknown term") == "other"
