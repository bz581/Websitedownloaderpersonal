"""Simple website downloader package for personal use.

This package focuses on ethically downloading public content and rendering JS when requested.
It respects robots.txt by default and provides options for proxy, cookies, and rate limits.
"""

from .downloader import Downloader

__all__ = ["Downloader"]
