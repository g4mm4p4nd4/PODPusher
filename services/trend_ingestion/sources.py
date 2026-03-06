"""Source configuration for trend ingestion scrapers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class SelectorSet:
    item: List[str]
    title: List[str]
    hashtags: List[str]
    likes: List[str]
    shares: List[str]
    comments: List[str]


@dataclass(frozen=True)
class SourceConfig:
    url: str
    selectors: SelectorSet
    wait_for_selector: str
    pagination_selector: str | None = None
    scroll_iterations: int = 0


PLATFORM_CONFIG: Dict[str, SourceConfig] = {
    "tiktok": SourceConfig(
        url="https://www.tiktok.com/foryou",
        selectors=SelectorSet(
            item=["div[data-e2e='recommend-list-item-container']", "div[data-e2e='search-card']"],
            title=["h3[data-e2e='user-title']", "div[data-e2e='video-desc']"],
            hashtags=["a[data-e2e='browse-hashtag']", "strong[data-e2e='text-tag']"],
            likes=["strong[data-e2e='like-count']", "strong[data-e2e='video-like-count']"],
            shares=["strong[data-e2e='share-count']"],
            comments=["strong[data-e2e='comment-count']"],
        ),
        wait_for_selector="div[data-e2e='recommend-list-item-container']",
        scroll_iterations=2,
    ),
    "instagram": SourceConfig(
        url="https://www.instagram.com/explore/",
        selectors=SelectorSet(
            item=["article div._aabd._aa8k._aanf", "article div._aagu"],
            title=["img"],
            hashtags=["a[href*='/explore/tags/']"],
            likes=["span[aria-label*='likes']"],
            shares=["span[aria-label*='shares']"],
            comments=["span[aria-label*='comments']"],
        ),
        wait_for_selector="article",
        scroll_iterations=1,
    ),
    "twitter": SourceConfig(
        url="https://twitter.com/explore",
        selectors=SelectorSet(
            item=["article[data-testid='tweet']"],
            title=["div[data-testid='tweetText']"],
            hashtags=["a[role='link'][href*='/hashtag']"],
            likes=["div[data-testid='like'] span"],
            shares=["div[data-testid='retweet'] span"],
            comments=["div[data-testid='reply'] span"],
        ),
        wait_for_selector="article[data-testid='tweet']",
        scroll_iterations=1,
    ),
    "pinterest": SourceConfig(
        url="https://www.pinterest.com/today/",
        selectors=SelectorSet(
            item=["div[data-test-id='pin']", "div[data-test-id='pinWrapper']"],
            title=["div[data-test-id='pin-description']", "h3"],
            hashtags=["a[href*='/search/pins/']", "a[data-test-id='hashtag']"],
            likes=["span[data-test-id='save-count']", "span[data-test-id='repin-count']"],
            shares=["span[data-test-id='repin-count']"],
            comments=["span[data-test-id='comment-count']"],
        ),
        wait_for_selector="div[data-test-id='pin']",
        scroll_iterations=2,
    ),
    "etsy": SourceConfig(
        url="https://www.etsy.com/trending-items",
        selectors=SelectorSet(
            item=["li.wt-list-unstyled.wt-show-lg", "li[data-search-results]"],
            title=["h3", "a.listing-link"],
            hashtags=["ul.wt-list-inline a"],
            likes=["span[data-bestseller]", "span[data-favorites]"],
            shares=["span[data-favorites]"],
            comments=["span[data-reviews-count]"],
        ),
        wait_for_selector="li.wt-list-unstyled.wt-show-lg",
        scroll_iterations=0,
    ),
}
