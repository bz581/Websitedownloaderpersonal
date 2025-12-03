import sys
import logging
from pathlib import Path
import typer

from .downloader import Downloader
from .crawler import Crawler

app = typer.Typer(help="Website downloader CLI (respectful downloader)")


def _setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


@app.command()
def download(
    url: str = typer.Argument(..., help="The URL to download"),
    output: str = typer.Option("downloaded", "-o", help="Output directory"),
    render_js: bool = typer.Option(False, help="Use Playwright to render JavaScript"),
    save_assets: bool = typer.Option(False, help="Attempt to download static assets (images/scripts/css)"),
    respect_robots: bool = typer.Option(True, help="Respect robots.txt (recommended)"),
    user_agent: str = typer.Option(None, help="Custom user-agent string"),
    proxy: str = typer.Option(None, help="Optional HTTP/HTTPS proxy (e.g., http://127.0.0.1:8080)"),
    verbose: bool = typer.Option(False, "-v", help="Verbose logging"),
):
    """Download a single page and optionally save assets. This tool is meant for legal/ethical uses only.

    Please do not use it to bypass paywalls, authentication, or CAPTCHAs.
    """

    _setup_logging(verbose)

    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}

    d = Downloader(output_dir=output, user_agent=user_agent, respect_robots=respect_robots, proxies=proxies)
    try:
        path = d.fetch(url, render_js=render_js, save_assets=save_assets)
        print(f"Saved page to: {path}")
    except Exception as exc:
        print("Error:\n", exc, file=sys.stderr)


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Start URL for crawl"),
    output: str = typer.Option("downloaded_crawl", "-o", help="Output directory for crawl results"),
    depth: int = typer.Option(2, help="Maximum crawl depth"),
    max_pages: int = typer.Option(100, help="Maximum pages to visit"),
    render_js: bool = typer.Option(False, help="Use Playwright to render JavaScript"),
    save_assets: bool = typer.Option(False, help="Attempt to download static assets"),
    rewrite_assets: bool = typer.Option(True, help="Rewrite HTML to reference local assets"),
    same_domain: bool = typer.Option(True, help="Restrict crawling to start domain"),
    concurrency: int = typer.Option(4, help="Number of worker threads"),
    per_host_delay: float = typer.Option(0.5, help="Minimum delay between requests to same host"),
    proxies: str = typer.Option(None, help="Comma-separated list of proxies to rotate (optional)"),
    auth_user: str = typer.Option(None, help="Basic auth user (optional)"),
    auth_pass: str = typer.Option(None, help="Basic auth password (optional)"),
    warc: bool = typer.Option(False, help="Export crawl to a WARC file"),
    verbose: bool = typer.Option(False, "-v", help="Verbose logging"),
):
    _setup_logging(verbose)

    proxy_list = [p.strip() for p in proxies.split(',')] if proxies else None
    auth = (auth_user, auth_pass) if auth_user and auth_pass else None

    c = Crawler(output_dir=output, user_agent=None, max_depth=depth, max_pages=max_pages,
                same_domain=same_domain, concurrency=concurrency, per_host_delay=per_host_delay,
                proxies=proxy_list, auth=auth)

    print(f"Starting crawl from {url} → output: {output}")
    results = c.crawl(url, render_js=render_js, save_assets=save_assets, rewrite_assets=rewrite_assets)

    if warc:
        outwarc = Path(output) / "crawl.warc.gz"
        print(f"Saving WARC to {outwarc}")
        c.export_warc(results, str(outwarc))
        print("WARC export complete")
    else:
        print(f"Crawl complete — {len(results)} results saved into {output}")


def main():
    app()


if __name__ == "__main__":
    main()
