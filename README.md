# Websitedownloaderpersonal — Respectful Website Downloader (Python)

A small, personal website downloader implemented in Python. Use it to save public pages for offline viewing or testing. The tool focuses on ethically downloading content — respecting robots.txt, rate limits and site policies.

⚠️ Important: Do NOT use this tool to bypass authentication, paywalls, CAPTCHAs or any security measures. Only download content that you have permission to access.

## Features

- Download a single page and optionally fetch simple static assets (images, CSS, JS).
- Optional JavaScript rendering using Playwright.
- Respects robots.txt by default (configurable).
- Proxy support, custom User-Agent and basic rate-limiting.

## Requirements

- Python 3.10+ recommended
- See `requirements.txt` for Python packages used (requests, beautifulsoup4, typer, playwright, tqdm).

## Quickstart — run the downloader locally

1. Create & activate a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

2. If you want JavaScript rendering, install Playwright browsers:

```bash
playwright install
```

3. Download a page (saved into `downloaded/` by default):

```bash
python -m src.downloader.cli download https://example.com -o downloaded
```

4. Download with rendered JS and attempt to save assets:

```bash
python -m src.downloader.cli download https://example.com -o downloaded --render-js --save-assets
```

5. Use a proxy (example):

```bash
python -m src.downloader.cli download https://example.com -o downloaded --proxy http://127.0.0.1:8080
```

## Web UI (HTML-first experience)

The project includes a Web UI for easy single-page downloads with a preview and asset saving.

**Run the web server:**

```bash
python -m uvicorn src.downloader.server:app --host 0.0.0.0 --port 6500
```

Then open **http://localhost:6500** in your browser (or the public URL if deployed).

The web interface allows you to:
- Download any webpage with optional JavaScript rendering
- Save images and stylesheets for offline viewing
- Preview the downloaded page directly in the browser
- Download the result as a ZIP file
- Configure proxy, authentication, and respect robots.txt

## Tests

Run the small integration test which downloads `https://example.com`:

```bash
PYTHONPATH=src pytest -q
```

## Pushing changes to GitHub

To commit and push your changes:

```bash
# Stage all changes
git add -A

# Commit with a message
git commit -m "Your commit message here"

# Push to GitHub
git push
```

Example:
```bash
git add -A
git commit -m "Add custom filename support"
git push
```

## Project layout

- `src/downloader/downloader.py` — Core downloader class
- `src/downloader/cli.py` — Typer-powered CLI wrapper
- `tests/test_downloader.py` — Basic test
- `requirements.txt` — Python dependencies

## Ethical & legal notes

Please treat this repository as a tool for allowed, ethical activity:

- Respect robots.txt and site Terms of Service (the downloader does so by default).
- Do not run large-scale crawls without prior permission — use proper rate limiting and contact the site owner when necessary.
- Do not use the tool to access or share private, copyrighted, or otherwise restricted content.

## Next steps / suggestions

- Add site-wide crawling with per-host rate limits and depth controls.
- Export captures to WARC format for archiving.
- Add proxy rotation and reauthentication helpers for legitimate integration testing environments.
- Add GUI or web front-end for easier use.

If you'd like me to implement any of these next steps, or extend the downloader to better handle particular blocking techniques (again, only for ethical uses), tell me which feature you want next.


