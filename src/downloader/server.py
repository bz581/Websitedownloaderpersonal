import io
import os
import socket
import zipfile
import tempfile
import logging
import ipaddress
import asyncio
import datetime
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict
import uuid
import threading

from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from .downloader import Downloader
from urllib.parse import urlparse

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup."""
    # Startup
    threading.Thread(target=cleanup_expired_archives, daemon=True).start()
    yield
    # Shutdown


app = FastAPI(title="Websitedownloaderpersonal - Web UI", lifespan=lifespan)
logger = logging.getLogger(__name__)

# Simple in-memory store for produced archives so result pages can link to them.
results_store: Dict[str, dict] = {}
results_lock = threading.Lock()

# Progress tracking store: {job_id: [event1, event2, ...]}
progress_store: Dict[str, list] = {}
progress_lock = threading.Lock()

ARCHIVE_TTL_SECONDS = 3600  # 1 hour


def cleanup_expired_archives():
    """Background task to clean up expired temp archives every 5 minutes."""
    import time
    while True:
        try:
            time.sleep(300)  # 5 minutes
        except Exception:
            pass
        
        now = datetime.datetime.now()
        expired = []
        
        with results_lock:
            for result_id, entry in list(results_store.items()):
                created_at = entry.get('created_at')
                if created_at and (now - created_at).total_seconds() > ARCHIVE_TTL_SECONDS:
                    expired.append((result_id, entry))
        
        for result_id, entry in expired:
            try:
                tmpdir = entry.get('tmpdir')
                if tmpdir:
                    tmpdir.cleanup()
                with results_lock:
                    results_store.pop(result_id, None)
                logger.info(f"Cleaned up expired archive {result_id}")
            except Exception as exc:
                logger.exception(f"Failed to cleanup archive {result_id}: {exc}")


def _is_public_host(hostname: str) -> bool:
    """Simple check to avoid fetching internal or loopback addresses by default.

    Returns True if hostname resolves to a public IP address. Conservative approach: if hostname
    resolves to a private/loopback address, we return False.
    """
    try:
        ips = socket.getaddrinfo(hostname, None)
    except Exception:
        # If DNS fails, return False to avoid accidental SSRF
        return False

    for family, _, _, _, sockaddr in ips:
        ip = sockaddr[0]
        try:
            parsed = ipaddress.ip_address(ip)
            if parsed.is_private or parsed.is_loopback or parsed.is_reserved or parsed.is_multicast:
                return False
        except Exception:
            # non-IP like IPv6 text — conservative
            return False

    return True


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/download")
def download(
    request: Request,
    url: str = Form(...),
    title: Optional[str] = Form(None),
    render_js: str = Form("false"),
    save_assets: str = Form("false"),
    proxy: Optional[str] = Form(None),
    respect_robots: str = Form("true"),
    favicon: Optional[UploadFile] = File(None),
    start_type: str = Form("download"),
    # crawl-specific
    depth: int = Form(1),
    max_pages: int = Form(10),
    concurrency: int = Form(3),
    warc: str = Form("false"),
    include: Optional[str] = Form(None),
    exclude: Optional[str] = Form(None),
    auth_user: Optional[str] = Form(None),
    auth_pass: Optional[str] = Form(None),
):
    # Basic validations
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed = Downloader().session  # just to access internal defaults (no side-effects)

    # protect against SSRF / internal ip access by default — be conservative
    host = None
    try:
        from urllib.parse import urlparse

        host = urlparse(url).hostname
    except Exception:
        host = None

    if not host or not _is_public_host(host):
        # refuse to fetch private/loopback addresses by default
        return HTMLResponse("Refusing to fetch internal or unresolved hostname.", status_code=400)

    render_js_bool = render_js.lower() == "true"
    save_assets_bool = save_assets.lower() == "true"
    respect_robots_bool = respect_robots.lower() != "false"

    # create temporary working dir
    tmpdir = tempfile.TemporaryDirectory(prefix="wdl-")
    out_dir = Path(tmpdir.name)

    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}

    # Create job ID for progress tracking
    job_id = uuid.uuid4().hex
    with progress_lock:
        progress_store[job_id] = []

    def progress_callback(event):
        """Callback to capture progress events."""
        with progress_lock:
            progress_store[job_id].append(event)

    d = Downloader(output_dir=str(out_dir), user_agent=None, respect_robots=respect_robots_bool, proxies=proxies, timeout=60)

    # optionally save uploaded favicon to output dir so it appears in archive
    if favicon:
        try:
            dfile = out_dir / "favicon_uploaded"
            with open(dfile, "wb") as fh:
                fh.write(favicon.file.read())
        except Exception:
            logger.exception("Failed saving uploaded favicon")

    # Single page download
    try:
        saved = d.fetch(url, render_js=render_js_bool, save_assets=save_assets_bool, progress_callback=progress_callback)
    except Exception as exc:
        tmpdir.cleanup()
        logger.exception("Download failed: %s", exc)
        error_msg = str(exc)
        if "RetryError" in str(type(exc)):
            error_msg = f"Connection failed after multiple attempts. The website may be blocking requests, unavailable, or experiencing issues. Details: {exc}"
        return HTMLResponse(f"Download failed: {error_msg}", status_code=500)

    # create a ZIP file on disk and register it for HTML results
    archive_name = f"downloaded_{host}.zip"
    archive_path = out_dir / archive_name
    with zipfile.ZipFile(str(archive_path), mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(out_dir):
            for f in files:
                path = Path(root) / f
                arcname = path.relative_to(out_dir)
                zf.write(path, arcname)

    result_id = uuid.uuid4().hex
    with results_lock:
        results_store[result_id] = {"path": str(archive_path), "mime": "application/zip", "name": archive_name, "tmpdir": tmpdir, "created_at": datetime.datetime.now()}

    page_html = None
    try:
        page_html = Path(str(saved)).read_text(encoding='utf-8')
    except Exception:
        page_html = None

    return templates.TemplateResponse(request, "result.html", {"result_type": "single", "id": result_id, "saved_path": str(saved), "page_html": page_html, "page_title": title or host, "url": url})


@app.get('/result/{result_id}')
def get_result(result_id: str):
    with results_lock:
        entry = results_store.get(result_id)
    if not entry:
        return HTMLResponse('Result not found', status_code=404)
    path = entry['path']
    mime = entry.get('mime', 'application/octet-stream')
    name = entry.get('name', os.path.basename(path))
    # stream the file
    return StreamingResponse(open(path, 'rb'), media_type=mime, headers={"Content-Disposition": f"attachment; filename={name}"})


@app.get('/status/{job_id}')
def get_status(job_id: str):
    """Get current progress status for a job."""
    with progress_lock:
        events = progress_store.get(job_id, [])
    if not events:
        return {"status": "not_found"}
    
    # Return latest event and event count
    latest = events[-1] if events else {}
    return {
        "status": latest.get("type", "unknown"),
        "total_events": len(events),
        "latest_event": latest
    }


@app.get('/progress/{job_id}')
async def progress_stream(job_id: str):
    """Server-Sent Events (SSE) endpoint for real-time progress streaming."""
    async def event_generator():
        sent_count = 0
        max_wait = 30  # 30 seconds max wait
        start_time = datetime.datetime.now()
        
        while True:
            # Check if job has timed out
            if (datetime.datetime.now() - start_time).total_seconds() > max_wait:
                yield f"data: {{'type': 'timeout'}}\n\n"
                break
            
            with progress_lock:
                events = progress_store.get(job_id, [])
            
            # Send new events since last sent
            if events and len(events) > sent_count:
                for event in events[sent_count:]:
                    import json
                    yield f"data: {json.dumps(event)}\n\n"
                    sent_count = len(events)
                
                # If crawl or download is done, close the stream
                if events[-1].get("type") in ["done", "crawl_done"]:
                    break
            
            await asyncio.sleep(0.5)  # Check every 500ms
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
