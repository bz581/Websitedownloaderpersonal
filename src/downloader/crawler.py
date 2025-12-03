import io
import os
import time
import logging
import random
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import re
from typing import Optional, Set, Dict, List

from .downloader import Downloader

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    url: str
    saved_path: Optional[str] = None
    error: Optional[str] = None


class Crawler:
    """A simple site crawler built on top of Downloader.

    - max_depth: Crawl maximum link-depth from the start URL
    - max_pages: Stop after visiting this many pages
    - same_domain: Restrict crawling to the start URL's domain
    - concurrency: Number of worker threads
    - per_host_delay: minimal seconds between requests to the same host
    - proxies: list of proxies to rotate for legitimate testing
    - headers/cookies: forwarded to Downloader
    """

    def __init__(self, output_dir: str = "downloaded_crawl", user_agent: str = None,
                 max_depth: int = 2, max_pages: int = 100, same_domain: bool = True,
                 concurrency: int = 4, per_host_delay: float = 0.5, proxies: Optional[List[str]] = None,
                 headers: Optional[dict] = None, cookies: Optional[dict] = None, respect_robots: bool = True,
                 include_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None,
                 auth: Optional[tuple] = None):

        self.output_dir = output_dir
        self.user_agent = user_agent
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.same_domain = same_domain
        self.concurrency = concurrency
        self.per_host_delay = per_host_delay
        self.proxies = proxies or []
        self.headers = headers
        self.cookies = cookies
        self.respect_robots = respect_robots
        self.include_patterns = [re.compile(p) for p in include_patterns or []]
        self.exclude_patterns = [re.compile(p) for p in exclude_patterns or []]
        self.auth = auth

        # crawler state
        self._visited: Set[str] = set()
        self._lock = threading.Lock()
        self._host_last: Dict[str, float] = {}
        self._results: List[CrawlResult] = []

    def _choose_proxy(self):
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def _wait_for_host(self, host: str):
        # ensure at least per_host_delay between requests to same host
        with self._lock:
            last = self._host_last.get(host, 0)
            now = time.time()
            wait = self.per_host_delay - (now - last)
            if wait > 0:
                time.sleep(wait)
            self._host_last[host] = time.time()

    def _discover_links(self, html: str, base_url: str) -> List[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        out = []
        for a in soup.find_all('a'):
            href = a.get('href')
            if not href:
                continue
            # avoid javascript: and mailto:
            if href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            resolved = urllib.parse.urljoin(base_url, href)
            out.append(resolved)
        return out

    def crawl(self, start_url: str, render_js: bool = False, save_assets: bool = False, rewrite_assets: bool = True, progress_callback=None) -> List[CrawlResult]:
        """Crawl from start_url and return list of CrawlResult objects. Uses a breadth-first strategy.
        progress_callback will be called with event dicts during crawl."""

        # prepare
        start_url = start_url.strip()
        if not start_url.startswith('http://') and not start_url.startswith('https://'):
            start_url = 'https://' + start_url

        if progress_callback:
            progress_callback({"type": "crawl_start", "url": start_url, "max_pages": self.max_pages, "max_depth": self.max_depth})

        parsed = urllib.parse.urlparse(start_url)
        start_host = parsed.netloc

        queue = [(start_url, 0)]

        def worker(url, depth):
            if len(self._results) >= self.max_pages:
                return
            if url in self._visited:
                return
            with self._lock:
                self._visited.add(url)

            host = urllib.parse.urlparse(url).netloc
            if self.same_domain and host != start_host:
                logger.debug('Skipping different-domain URL %s', url)
                return

            if self.respect_robots:
                dtmp = Downloader(output_dir=self.output_dir, user_agent=self.user_agent, respect_robots=True)
                if not dtmp.allowed_by_robots(url):
                    logger.debug('Disallowed by robots: %s', url)
                    self._results.append(CrawlResult(url=url, error='Disallowed by robots.txt'))
                    return

            self._wait_for_host(host)

            proxy = self._choose_proxy()
            proxies = {"http": proxy, "https": proxy} if proxy else None

            downloader = Downloader(output_dir=self.output_dir, user_agent=self.user_agent,
                                    respect_robots=self.respect_robots, proxies=proxies, headers=self.headers,
                                    auth=self.auth, cookies=self.cookies)

            try:
                saved = downloader.fetch(url, render_js=render_js, save_assets=save_assets, rewrite_assets=rewrite_assets, progress_callback=progress_callback)
                pathstr = str(saved) if not isinstance(saved, str) else saved
                self._results.append(CrawlResult(url=url, saved_path=pathstr))
                if progress_callback:
                    progress_callback({"type": "page_visited", "url": url, "count": len(self._results)})
                # discover links to expand
                if depth < self.max_depth:
                    try:
                        html = open(saved, encoding='utf-8').read()
                    except Exception:
                        html = ''
                    links = self._discover_links(html, url)
                    with self._lock:
                        for l in links:
                            # apply include/exclude filters
                            if self.include_patterns and not any(p.search(l) for p in self.include_patterns):
                                continue
                            if any(p.search(l) for p in self.exclude_patterns):
                                continue
                            if l not in self._visited and len(self._visited) + len(queue) < self.max_pages:
                                queue.append((l, depth + 1))
            except Exception as exc:
                logger.exception('Failed fetching %s: %s', url, exc)
                self._results.append(CrawlResult(url=url, error=str(exc)))
                if progress_callback:
                    progress_callback({"type": "page_error", "url": url, "error": str(exc)})

        # simple breadth-first worker loop using a threadpool
        with ThreadPoolExecutor(max_workers=self.concurrency) as ex:
            futures = []
            while queue and len(self._results) < self.max_pages:
                url, depth = queue.pop(0)
                futures.append(ex.submit(worker, url, depth))
            # wait for all tasks
            for f in as_completed(futures):
                pass

        if progress_callback:
            progress_callback({"type": "crawl_done", "total": len(self._results)})
        return self._results

    def export_warc(self, results: List[CrawlResult], filename: str) -> str:
        """Export the saved pages + assets to a WARC file (requires warcio). Returns filename.
        Includes warcinfo with enriched crawl metadata."""
        try:
            from warcio.warcwriter import WARCWriter
        except Exception:
            raise RuntimeError('warcio is required to write WARC files')

        outpath = filename
        with open(outpath, 'wb') as fh:
            writer = WARCWriter(fh, gzip=True)

            # write enriched warcinfo record with crawl metadata
            import time as time_module
            warcinfo_fields = [
                ("Software", "websitedownloaderpersonal/1.0"),
                ("Crawl-Start", time_module.strftime('%Y-%m-%dT%H:%M:%SZ', time_module.gmtime())),
                ("Pages-Crawled", str(len(results))),
                ("Max-Depth", str(self.max_depth)),
                ("Max-Pages", str(self.max_pages)),
                ("Concurrency", str(self.concurrency)),
                ("Respect-Robots", str(self.respect_robots)),
            ]
            warcinfo = writer.create_warcinfo_record(os.path.basename(outpath), {k: v for k, v in warcinfo_fields})
            writer.write_record(warcinfo)

            for r in results:
                if r.saved_path and os.path.exists(r.saved_path):
                    with open(r.saved_path, 'rb') as rf:
                        payload = rf.read()
                        # the saved file may be a raw HTML payload (not an HTTP response),
                        # write it as a 'resource' record in the WARC
                        rec = writer.create_warc_record(r.url, 'resource', payload=io.BytesIO(payload))
                        writer.write_record(rec)

                    # try to include assets referenced in the saved HTML
                    try:
                        from bs4 import BeautifulSoup

                        with open(r.saved_path, encoding='utf-8') as fhp:
                            html = fhp.read()
                        soup = BeautifulSoup(html, 'html.parser')
                        asset_refs = []
                        for tag in soup.find_all(['img', 'script', 'link']):
                            if tag.name == 'img' and tag.get('src'):
                                asset_refs.append(tag.get('src'))
                            elif tag.name == 'script' and tag.get('src'):
                                asset_refs.append(tag.get('src'))
                            elif tag.name == 'link' and tag.get('href') and tag.get('rel') and 'stylesheet' in tag.get('rel'):
                                asset_refs.append(tag.get('href'))

                        for a in asset_refs:
                            full = urllib.parse.urljoin(r.url, a)
                            # find corresponding file in output directory
                            parsed = urllib.parse.urlparse(full)
                            safe_host = parsed.netloc.replace(':', '_')
                            filename = os.path.basename(parsed.path) or 'unnamed'
                            candidate = os.path.join(os.path.dirname(r.saved_path), 'assets', safe_host, filename)
                            if os.path.exists(candidate):
                                with open(candidate, 'rb') as afp:
                                    apayload = afp.read()
                                    rec = writer.create_warc_record(full, 'resource', payload=io.BytesIO(apayload))
                                    writer.write_record(rec)
                    except Exception:
                        logger.debug('Failed adding assets for %s to WARC', r.url)

        return outpath


__all__ = ['Crawler', 'CrawlResult']
