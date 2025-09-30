from services.trend_ingestion.sources import PLATFORM_CONFIG, SourceConfig, SelectorSet


def test_platform_config_has_selectors():
    assert PLATFORM_CONFIG, "Expected platform configuration to be defined"
    for name, config in PLATFORM_CONFIG.items():
        assert isinstance(config, SourceConfig)
        selectors: SelectorSet = config.selectors
        for field in ('item', 'title', 'hashtags', 'likes', 'shares', 'comments'):
            values = getattr(selectors, field)
            assert isinstance(values, list) and values, f"Selector list '{field}' empty for {name}"


def test_tiktok_has_wait_selector():
    tiktok = PLATFORM_CONFIG['tiktok']
    assert tiktok.wait_for_selector.startswith('div')
