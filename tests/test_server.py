import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from fastapi.testclient import TestClient
from downloader.server import app
import zipfile
import io


def _extract_result_id_from_html(html_text: str) -> str:
    # naive parse to find /result/<id>
    import re
    m = re.search(r'href="/result/([0-9a-fA-F]+)"', html_text)
    if not m:
        raise AssertionError('no result id found in html')
    return m.group(1)


def test_download_example():
    client = TestClient(app)
    resp = client.post('/download', data={'url': 'https://example.com', 'render_js': 'false', 'save_assets': 'false', 'respect_robots': 'true'})
    assert resp.status_code == 200
    # response should be an HTML page containing the result link
    assert 'Download' in resp.text
    rid = _extract_result_id_from_html(resp.text)
    dl = client.get(f'/result/{rid}')
    assert dl.status_code == 200
    assert dl.headers['content-type'] in ('application/zip', 'application/x-zip-compressed')
    z = zipfile.ZipFile(io.BytesIO(dl.content))
    names = z.namelist()
    assert any(n.endswith('.html') for n in names)


def test_crawl_example_zip():
    client = TestClient(app)
    # instruct the server to perform a crawl (shallow) and return a zip
    resp = client.post('/download', data={
        'url': 'https://example.com',
        'start_type': 'crawl',
        'depth': '0',
        'max_pages': '2',
        'concurrency': '1',
        'warc': 'false',
        'render_js': 'false',
        'save_assets': 'false',
        'respect_robots': 'true'
    })
    assert resp.status_code == 200
    rid = _extract_result_id_from_html(resp.text)
    dl = client.get(f'/result/{rid}')
    assert dl.status_code == 200
    assert dl.headers['content-type'] in ('application/zip', 'application/x-zip-compressed')


def test_crawl_example_warc():
    client = TestClient(app)
    resp = client.post('/download', data={
        'url': 'https://example.com',
        'start_type': 'crawl',
        'depth': '0',
        'max_pages': '2',
        'concurrency': '1',
        'warc': 'true',
        'render_js': 'false',
        'save_assets': 'false',
        'respect_robots': 'true'
    })
    assert resp.status_code == 200
    rid = _extract_result_id_from_html(resp.text)
    dl = client.get(f'/result/{rid}')
    assert dl.status_code == 200
    assert dl.headers['content-type'] in ('application/gzip', 'application/x-gzip')
