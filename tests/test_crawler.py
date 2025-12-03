import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from downloader.crawler import Crawler
import os


def test_crawl_example(tmp_path):
    out = tmp_path / 'out'
    c = Crawler(output_dir=str(out), max_depth=0, max_pages=5, concurrency=2)
    results = c.crawl('https://example.com', render_js=False, save_assets=False)
    assert len(results) >= 1
    # make sure at least one result saved_path exists
    saved_paths = [r.saved_path for r in results if r.saved_path]
    assert saved_paths
    for p in saved_paths:
        assert Path(p).exists()


def test_export_warc(tmp_path):
    out = tmp_path / 'out'
    c = Crawler(output_dir=str(out), max_depth=0, max_pages=2, concurrency=1)
    results = c.crawl('https://example.com', render_js=False, save_assets=False)
    warc_file = str(tmp_path / 'example.warc.gz')
    res = c.export_warc(results, warc_file)
    assert os.path.exists(res)
    # basic file size check
    assert os.path.getsize(res) > 0
