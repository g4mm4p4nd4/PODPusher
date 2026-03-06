"""Tests for trend scraper platform configuration and service functions.

Owner: Unit-Tester (per DEVELOPMENT_PLAN.md Task 1.2.8)
Reference: DS-01, DS-02, DS-06
"""
from services.trend_ingestion.sources import PLATFORM_CONFIG, SourceConfig, SelectorSet
from services.trend_ingestion.service import (
    normalize_text,
    compute_engagement,
    categorize,
    _parse_metric,
)


class TestPlatformConfig:
    """Verify all 5 required platforms are configured."""

    def test_five_platforms_configured(self):
        assert len(PLATFORM_CONFIG) == 5

    def test_tiktok_in_config(self):
        assert "tiktok" in PLATFORM_CONFIG

    def test_instagram_in_config(self):
        assert "instagram" in PLATFORM_CONFIG

    def test_twitter_in_config(self):
        assert "twitter" in PLATFORM_CONFIG

    def test_pinterest_in_config(self):
        assert "pinterest" in PLATFORM_CONFIG

    def test_etsy_in_config(self):
        assert "etsy" in PLATFORM_CONFIG

    def test_all_configs_are_source_config(self):
        for name, config in PLATFORM_CONFIG.items():
            assert isinstance(config, SourceConfig), f"{name} is not a SourceConfig"

    def test_all_configs_have_selectors(self):
        for name, config in PLATFORM_CONFIG.items():
            selectors = config.selectors
            assert isinstance(selectors, SelectorSet)
            for field in ("item", "title", "hashtags", "likes", "shares", "comments"):
                values = getattr(selectors, field)
                assert isinstance(values, list) and len(values) > 0, (
                    f"Selector '{field}' empty for {name}"
                )

    def test_all_configs_have_url(self):
        for name, config in PLATFORM_CONFIG.items():
            assert config.url.startswith("https://"), f"{name} URL invalid"

    def test_all_configs_have_wait_selector(self):
        for name, config in PLATFORM_CONFIG.items():
            assert config.wait_for_selector, f"{name} missing wait_for_selector"

    def test_pinterest_has_scroll_iterations(self):
        assert PLATFORM_CONFIG["pinterest"].scroll_iterations >= 1


class TestNormalization:
    """Test text normalization per DS-02."""

    def test_lowercase(self):
        assert normalize_text("HELLO WORLD") == "hello world"

    def test_removes_stopwords(self):
        assert normalize_text("the cat and the dog") == "cat dog"

    def test_removes_empty_words(self):
        result = normalize_text("  hello   world  ")
        assert result == "hello world"

    def test_empty_input(self):
        assert normalize_text("") == ""


class TestEngagement:
    def test_sum(self):
        assert compute_engagement(10, 20, 30) == 60

    def test_zeros(self):
        assert compute_engagement(0, 0, 0) == 0


class TestCategorize:
    def test_animals(self):
        assert categorize("cute cat video") == "animals"

    def test_sports(self):
        assert categorize("basketball game") == "sports"

    def test_other(self):
        assert categorize("random topic") == "other"


class TestParseMetric:
    def test_simple_number(self):
        assert _parse_metric("1234") == 1234

    def test_k_suffix(self):
        assert _parse_metric("1.2K") == 1200

    def test_m_suffix(self):
        assert _parse_metric("3.5M") == 3500000

    def test_empty_string(self):
        assert _parse_metric("") == 0

    def test_no_number(self):
        assert _parse_metric("no numbers here") == 0

    def test_commas(self):
        assert _parse_metric("1,234") == 1234
