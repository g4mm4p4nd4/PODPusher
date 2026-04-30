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
    candidate_urls: List[str] | None = None
    pagination_selector: str | None = None
    scroll_iterations: int = 0

    def urls(self) -> List[str]:
        return [self.url, *(self.candidate_urls or [])]


PLATFORM_CONFIG: Dict[str, SourceConfig] = {
    "tiktok": SourceConfig(
        url="https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en",
        candidate_urls=[
            "https://ads.tiktok.com/business/creativecenter/inspiration/popular/pc/en",
            "https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pc/en",
            "https://ads.tiktok.com/business/creativecenter/hashtag/earthday/pc/en?countryCode=US&period=7",
            "https://ads.tiktok.com/business/creativecenter/hashtag/gymmotivation/pc/en?countryCode=US&period=120",
        ],
        selectors=SelectorSet(
            item=[
                "div[class*='Card']",
                "div[class*='Item']",
                "tr",
                "div[data-e2e='recommend-list-item-container']",
                "div[data-e2e='search-card']",
            ],
            title=[
                "a[href*='creativecenter/hashtag']",
                "span",
                "h3[data-e2e='user-title']",
                "div[data-e2e='video-desc']",
            ],
            hashtags=[
                "a[href*='creativecenter/hashtag']",
                "a[data-e2e='browse-hashtag']",
                "strong[data-e2e='text-tag']",
            ],
            likes=[
                "span",
                "strong[data-e2e='like-count']",
                "strong[data-e2e='video-like-count']",
            ],
            shares=["strong[data-e2e='share-count']"],
            comments=["strong[data-e2e='comment-count']"],
        ),
        wait_for_selector="div",
        scroll_iterations=2,
    ),
    "instagram": SourceConfig(
        url="https://www.instagram.com/explore/tags/fashion/",
        candidate_urls=[
            "https://www.instagram.com/explore/tags/homedecor/",
            "https://www.instagram.com/explore/tags/wallart/",
            "https://www.instagram.com/explore/tags/gymmotivation/",
            "https://www.instagram.com/explore/tags/earthday/",
            "https://www.instagram.com/reels/audio/960710575495232/million-dollar-baby/",
            "https://www.instagram.com/explore/",
        ],
        selectors=SelectorSet(
            item=[
                "main a[href*='/explore/tags/']",
                "h2",
                "article div._aabd._aa8k._aanf",
                "article div._aagu",
            ],
            title=["span", "h2", "img"],
            hashtags=["a[href*='/explore/tags/']"],
            likes=["span[aria-label*='likes']"],
            shares=["span[aria-label*='shares']"],
            comments=["span[aria-label*='comments']"],
        ),
        wait_for_selector="body",
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
            likes=[
                "span[data-test-id='save-count']",
                "span[data-test-id='repin-count']",
            ],
            shares=["span[data-test-id='repin-count']"],
            comments=["span[data-test-id='comment-count']"],
        ),
        wait_for_selector="div[data-test-id='pin']",
        scroll_iterations=2,
    ),
    "etsy": SourceConfig(
        url="https://www.etsy.com/trends?ref=finds_index",
        candidate_urls=[
            "https://www.etsy.com/featured/hub/ones-to-watch",
            "https://www.etsy.com/featured/hub/fashion-favorites",
            "https://www.etsy.com/featured/hub/home-favorites",
            "https://www.etsy.com/featured/hub/vintage-style",
            "https://www.etsy.com/featured/hub/wall-art",
            "https://www.etsy.com/featured/hub/craft-supplies-guide",
            "https://www.etsy.com/r/curated/2026-color-of-the-year",
            "https://www.etsy.com/market/trending_search",
            "https://www.etsy.com/market/trending_products",
            "https://www.etsy.com/market/trending_niches",
            "https://www.etsy.com/market/most_popular_trends",
            "https://www.etsy.com/market/top_trending_items",
        ],
        selectors=SelectorSet(
            item=[
                "li[data-listing-id]",
                "div[data-listing-id]",
                "a[href*='/listing/']",
                "li.wt-list-unstyled.wt-show-lg",
                "li[data-search-results]",
            ],
            title=["h3", "a.listing-link"],
            hashtags=["ul.wt-list-inline a"],
            likes=["span[data-bestseller]", "span[data-favorites]"],
            shares=["span[data-favorites]"],
            comments=["span[data-reviews-count]"],
        ),
        wait_for_selector="li.wt-list-unstyled.wt-show-lg",
        scroll_iterations=0,
    ),
    "amazon": SourceConfig(
        url="https://www.amazon.com/gp/movers-and-shakers/arts-crafts",
        candidate_urls=[
            "https://www.amazon.com/gp/movers-and-shakers/handmade",
            "https://www.amazon.com/gp/movers-and-shakers/home-garden",
            "https://www.amazon.com/gp/movers-and-shakers/fashion",
        ],
        selectors=SelectorSet(
            item=[
                ".zg-grid-general-faceout",
                ".zg-carousel-general-faceout",
                ".p13n-sc-uncoverable-faceout",
            ],
            title=[
                "img[alt]",
                "._cDEzb_p13n-sc-css-line-clamp-3_g3dy1",
                "._cDEzb_p13n-sc-css-line-clamp-2_EWgCb",
            ],
            hashtags=[
                "a[href*='/gp/bestsellers/']",
                "a[href*='/gp/movers-and-shakers/']",
            ],
            likes=["span.a-icon-alt"],
            shares=["span.a-icon-alt"],
            comments=["span.a-size-small"],
        ),
        wait_for_selector=".zg-grid-general-faceout",
        scroll_iterations=1,
    ),
}
