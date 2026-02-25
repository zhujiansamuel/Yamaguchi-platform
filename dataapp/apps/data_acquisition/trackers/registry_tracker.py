from typing import Callable, Any
from .official_website_redirect_to_yamato_tracking import official_website_redirect_to_yamato_tracking
from .redirect_to_japan_post_tracking import redirect_to_japan_post_tracking
from .official_website_tracking import official_website_tracking
from .yamato_tracking_only import yamato_tracking_only
from .japan_post_tracking_only import japan_post_tracking_only
from .japan_post_tracking_10 import japan_post_tracking_10

# Tracker 类型定义：一个接受任意参数并返回任意结果的函数
Tracker = Callable[..., Any]

TRACKERS = {
    "official_website_redirect_to_yamato_tracking": official_website_redirect_to_yamato_tracking,
    "redirect_to_japan_post_tracking": redirect_to_japan_post_tracking,
    "official_website_tracking": official_website_tracking,
    "yamato_tracking_only": yamato_tracking_only,
    "japan_post_tracking_only": japan_post_tracking_only,
    "japan_post_tracking_10": japan_post_tracking_10,
}


def has_tracker(name: str) -> bool:
    """检查 tracker 是否存在"""
    return name in TRACKERS


def get_tracker(name: str) -> Tracker:
    """真正取出 tracker 的函数，后续如果需要用得到"""
    if name not in TRACKERS:
        raise KeyError(f"未注册的追踪器: {name}")
    return TRACKERS[name]


def run_tracker(tracker_key: str, df):
    """运行指定的 tracker"""
    return TRACKERS[tracker_key](df)

