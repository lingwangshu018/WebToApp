"""
Recipe Store — Community recipe management.

NOTE: The entries below are illustrative SAMPLE recipes shipped with the
project, not real usage data. They seed the "shared recipes" count on the
homepage and serve as examples of the option flags a recipe can carry.
Replace or extend them as needed.
"""
from typing import Optional


# Sample recipes (illustrative only — not real install/usage figures).
POPULAR_RECIPES = [
    {"id": "yt-pure", "name": "YouTube 纯净版", "url": "https://youtube.com", "icon": "🎬",
     "options": {"strip-ads": True, "strip-popups": True, "turbo": True}},
    {"id": "tw-fast", "name": "Twitter/X 极速版", "url": "https://twitter.com", "icon": "🐦",
     "options": {"strip-ads": True, "strip-popups": True, "dark-mode": True, "turbo": True}},
    {"id": "gh-dark", "name": "GitHub 增强版", "url": "https://github.com", "icon": "🐙",
     "options": {"dark-mode": True, "turbo": True}},
    {"id": "zh-pure", "name": "知乎去广告版", "url": "https://zhihu.com", "icon": "📖",
     "options": {"strip-ads": True, "strip-popups": True, "reader": True, "turbo": True}},
    {"id": "rd-pure", "name": "Reddit 纯净版", "url": "https://old.reddit.com", "icon": "🤖",
     "options": {"strip-ads": True, "strip-popups": True, "turbo": True}},
    {"id": "wb-lite", "name": "微博精简版", "url": "https://m.weibo.cn", "icon": "🌊",
     "options": {"strip-ads": True, "strip-popups": True, "turbo": True}},
]


class RecipeStore:
    def get_popular(self) -> list:
        return POPULAR_RECIPES

    def get_by_id(self, recipe_id: str) -> Optional[dict]:
        return next((r for r in POPULAR_RECIPES if r["id"] == recipe_id), None)
