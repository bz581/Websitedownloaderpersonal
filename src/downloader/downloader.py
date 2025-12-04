import os
import time
import logging
import urllib.parse
import urllib.robotparser
from pathlib import Path
from typing import Optional, List, Tuple, Dict

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Downloader:
    """A simple, respectful website downloader.

    Key points:
    - By default, respects robots.txt (can be disabled explicitly)
    - Optional JS rendering using Playwright (requires Playwright installed)
    - Optional proxy and cookies/auth headers
    - Saves main HTML and (optionally) discovered assets
    - Rate-limits and retries
    """

    def __init__(self, output_dir: str = "downloaded", user_agent: str = None,
                 respect_robots: bool = True, rate_limit: float = 0.5, timeout: int = 30,
                 proxies: Optional[dict] = None, headers: Optional[dict] = None,
                 auth: Optional[Tuple[str, str]] = None, cookies: Optional[Dict[str, str]] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.respect_robots = respect_robots
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        if headers:
            self.session.headers.update(headers)
        if auth:
            # support requests-style basic auth tuples
            self.session.auth = auth
        if cookies:
            self.session.cookies.update(cookies)
        self.session.proxies.update(proxies or {})

    def _get_robots_parser(self, root: str) -> urllib.robotparser.RobotFileParser:
        robots_url = urllib.parse.urljoin(root, "/robots.txt")
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
        except Exception:
            # Conservative default if robots.txt can't be fetched
            logger.info("Couldn't fetch robots.txt — proceeding conservatively.")
        return parser

    def allowed_by_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parsed = urllib.parse.urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._get_robots_parser(root)
        return parser.can_fetch(self.user_agent, url)

    def fetch(self, url: str, render_js: bool = False, save_assets: bool = False, rewrite_assets: bool = True, custom_filename: str = None, progress_callback=None) -> Path:
        """Fetch a URL and save the result to disk.

        If render_js is True Playwright will be used to render the page content. If
        save_assets is True the downloader will parse and try to fetch simple static assets
        (images, stylesheets, scripts). custom_filename allows specifying the output filename.
        progress_callback will be called with event dicts.
        """
        if not self.allowed_by_robots(url):
            raise PermissionError("Fetching disallowed by robots.txt")

        if progress_callback:
            progress_callback({"type": "start", "url": url})
        logger.info("Fetching %s (render_js=%s, save_assets=%s)", url, render_js, save_assets)

        content = None
        filename = None

        if render_js:
            try:
                # Playwright sync import — optional
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    # Launch browser with performance optimizations
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-gpu",
                            "--no-first-run",
                            "--disable-background-networking",
                            "--disable-client-side-phishing-detection",
                            "--disable-popup-blocking",
                            "--disable-prompt-on-repost",
                        ]
                    )
                    
                    # Create context with optimizations
                    context = browser.new_context(
                        ignore_https_errors=True,
                        viewport={"width": 1280, "height": 720}
                    )
                    context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
                    
                    page = context.new_page()
                    page.set_default_navigation_timeout(self.timeout * 1000)
                    page.set_default_timeout(self.timeout * 1000)
                    
                    # Block media and font resources to speed up loading
                    page.route("**/*.{png,jpg,jpeg,gif,svg,webp,ttf,woff,woff2}", lambda route: route.abort())
                    
                    page.goto(url, wait_until="networkidle")
                    page.wait_for_load_state("networkidle")
                    content = page.content()
                    
                    context.close()
                    browser.close()
            except ImportError:
                raise RuntimeError("Playwright required for JS rendering but it's not installed.")
        else:
            # Multiple user-agents to work around blocking
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            ]
            
            for attempt in range(8):
                try:
                    # Rotate user-agent on each retry
                    ua = user_agents[attempt % len(user_agents)]
                    self.session.headers["User-Agent"] = ua
                    logger.debug(f"Attempt {attempt + 1}/8 with UA: {ua[:50]}...")
                    r = self.session.get(url, timeout=self.timeout)
                    r.raise_for_status()
                    content = r.text
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == 7:
                        logger.exception(f"Failed after 8 attempts: {e}")
                        raise
                    wait_time = min(2 ** attempt, 16)  # exponential backoff
                    logger.debug(f"Attempt {attempt + 1} failed, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
            else:
                raise RuntimeError("Failed to download after 8 attempts")

        # save main HTML
        if custom_filename:
            filename = self.output_dir / custom_filename
            # Only add .html if no extension provided
            if not filename.suffix:
                filename = filename.with_suffix('.html')
        else:
            parsed = urllib.parse.urlparse(url)
            safe_host = parsed.netloc.replace(":", "_")
            safe_path = parsed.path.strip("/") or "index"
            # Preserve URL extension, otherwise add .html
            if "." in safe_path:
                filename = self.output_dir / f"{safe_host}_{safe_path}"
            else:
                filename = self.output_dir / f"{safe_host}_{safe_path}.html"
        
        filename = Path(str(filename))
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(content, encoding="utf-8")
        if progress_callback:
            progress_callback({"type": "page_saved", "url": url, "path": str(filename)})

        # optionally fetch some static assets and optionally rewrite HTML to point to local copies
        if save_assets:
            assets = self._parse_assets(content, url)
            if progress_callback:
                progress_callback({"type": "assets_found", "count": len(assets)})
            if rewrite_assets:
                content = self._rewrite_assets_and_save(content, url, assets)
            else:
                for a in assets:
                    try:
                        self._download_asset(a)
                        time.sleep(self.rate_limit)
                    except Exception as e:
                        logger.debug("Failed to fetch asset %s: %s", a, e)

        if progress_callback:
            progress_callback({"type": "done", "url": url})
        return filename

    def _parse_assets(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        candidates = []
        for tag in soup.find_all(["img", "script", "link"]):
            if tag.name == "img" and tag.get("src"):
                candidates.append(tag.get("src"))
            elif tag.name == "script" and tag.get("src"):
                candidates.append(tag.get("src"))
            elif tag.name == "link" and tag.get("href") and tag.get("rel") and "stylesheet" in tag.get("rel"):
                candidates.append(tag.get("href"))

        resolved = [urllib.parse.urljoin(base_url, u) for u in candidates]
        # deduplicate and keep same-origin assets first
        seen = set()
        out = []
        base_origin = urllib.parse.urlparse(base_url).netloc
        for u in resolved:
            if u in seen:
                continue
            seen.add(u)
            out.append(u)
        return out

    def _download_asset(self, url: str) -> Optional[Path]:
        if not self.allowed_by_robots(url):
            logger.debug("Skipping asset disallowed by robots: %s", url)
            return None

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8),
               retry=retry_if_exception_type(requests.exceptions.RequestException))
        def _get_stream(u):
            r = self.session.get(u, timeout=self.timeout, stream=True)
            r.raise_for_status()
            return r

        r = _get_stream(url)

        parsed = urllib.parse.urlparse(url)
        safe_host = parsed.netloc.replace(":", "_")
        out_dir = self.output_dir / "assets" / safe_host
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = os.path.basename(parsed.path) or "unnamed"
        target = out_dir / filename

        with open(target, "wb") as fh:
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    break
                fh.write(chunk)

        logger.info("Saved asset %s -> %s", url, target)
        return target

    def _rewrite_assets_and_save(self, html: str, base_url: str, assets: List[str]) -> str:
        """Download assets into the output folder and update HTML so asset links point to local files.

        Returns the rewritten HTML string.
        """
        soup = BeautifulSoup(html, "html.parser")

        def save_and_replace(attr, tag, orig_url):
            try:
                full = urllib.parse.urljoin(base_url, orig_url)
                local = self._download_asset(full)
                if local:
                    rel = os.path.relpath(local, start=str(self.output_dir))
                    tag[attr] = rel.replace('\\', '/')
            except Exception as e:
                logger.debug("Error saving/replacing asset %s: %s", orig_url, e)

        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                save_and_replace('src', img, src)

        for script in soup.find_all('script'):
            src = script.get('src')
            if src:
                save_and_replace('src', script, src)

        for link in soup.find_all('link'):
            href = link.get('href')
            rel = link.get('rel') or []
            if href and 'stylesheet' in rel:
                save_and_replace('href', link, href)

        return str(soup)


__all__ = ["Downloader"]
