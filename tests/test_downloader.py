import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from downloader import Downloader


def test_fetch_example(tmp_path):
    d = Downloader(output_dir=str(tmp_path))
    fname = d.fetch('https://example.com', render_js=False)
    assert isinstance(fname, Path)
    assert fname.exists()
    content = fname.read_text(encoding='utf-8')
    assert '<title>Example Domain</title>' in content
