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


        body {
            font-family: 'Arial', sans-serif;
            background-color: #111;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            transition: background-color 0.3s ease;
        }

        .container {
            background-color: #222;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
            width: 100%;
            max-width: 450px;
        }

        h1 {
            font-size: 2rem;
            text-align: center;
            color: #fff;
            margin-bottom: 20px;
            letter-spacing: 2px;
            text-shadow: 
                0 0 20px rgba(0, 0, 0, 0.6),
                0 0 30px rgba(0, 0, 0, 0.6),
                0 0 40px rgba(0, 0, 0, 0.5),
                0 0 50px rgba(0, 0, 0, 0.4),
                0 0 60px rgba(0, 0, 0, 0.3),
                0 0 70px rgba(0, 0, 0, 0.2);
            animation: auraAnimation 2s infinite alternate, colorChange 3s infinite alternate;
        }

        @keyframes auraAnimation {
            0% {
                text-shadow: 
                    0 0 20px rgba(0, 0, 0, 0.6),
                    0 0 30px rgba(0, 0, 0, 0.6),
                    0 0 40px rgba(0, 0, 0, 0.5),
                    0 0 50px rgba(0, 0, 0, 0.4),
                    0 0 60px rgba(0, 0, 0, 0.3),
                    0 0 70px rgba(0, 0, 0, 0.2);
            }
            50% {
                text-shadow: 
                    0 0 30px rgba(0, 0, 0, 0.7),
                    0 0 40px rgba(0, 0, 0, 0.7),
                    0 0 50px rgba(0, 0, 0, 0.6),
                    0 0 60px rgba(0, 0, 0, 0.5),
                    0 0 70px rgba(0, 0, 0, 0.4),
                    0 0 80px rgba(0, 0, 0, 0.3);
            }
            100% {
                text-shadow: 
                    0 0 40px rgba(0, 0, 0, 0.8),
                    0 0 50px rgba(0, 0, 0, 0.8),
                    0 0 60px rgba(0, 0, 0, 0.7),
                    0 0 70px rgba(0, 0, 0, 0.6),
                    0 0 80px rgba(0, 0, 0, 0.5),
                    0 0 90px rgba(0, 0, 0, 0.4);
            }
        }

        @keyframes colorChange {
            0% {
                color: #fff;
            }
            50% {
                color: #aaa;
            }
            100% {
                color: #fff;
            }
        }

        label {
            display: block;
            font-size: 1rem;
            margin-bottom: 5px;
            color: #ccc;
            font-weight: bold;
        }

        input, select, button {
            width: 100%;
            padding: 12px;
            margin-bottom: 15px;
            border: none;
            border-radius: 8px;
            background-color: #333;
            color: #fff;
            font-size: 1rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        input:focus, select:focus, button:focus {
            outline: none;
            border: 2px solid #007BFF;
        }

        button {
            background-color: #007BFF;
            color: #fff;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }

        button:hover {
            background-color: #0056b3;
            transform: scale(1.05);
        }

        button:active {
            background-color: #003f8e;
            transform: scale(1.1);
        }

        button::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 300%;
            height: 300%;
            background-color: #111;
            transition: width 0.4s ease, height 0.4s ease, top 0.4s ease, left 0.4s ease;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            z-index: 0;
        }

        button:hover::before {
            width: 350%;
            height: 350%;
            top: -25%;
            left: -25%;
        }

        button span {
            position: relative;
            z-index: 1;
        }

        button:hover {
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
        }

        .footer {
            font-size: 0.9rem;
            text-align: center;
            color: #aaa;
            margin-top: 15px;
        }

        .footer a {
            color: #007BFF;
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Download file</h1>
        
        <label for="url-input">url</label>
        <input type="text" id="url-input" placeholder="Enter the URL" />
        
        <label for="title-input">title</label>
        <input type="text" id="title-input" placeholder="Enter the title" />
        
        <label for="favicon-input">icon</label>
        <input type="file" id="favicon-input" accept="image/*" />

        <label for="pre-saved-options">presave</label>
        <select id="pre-saved-options">
            <option value="">Select an option</option>
            <option value="google-classroom">Google Classroom</option>
            <option value="clever">Clever</option>
            <option value="gmail">Gmail</option>
            <option value="schoology">Schoology</option>
            <option value="googledocs">Google Docs</option>
            <option value="googleslides">Google Slides</option>
            <option value="ixl">IXL</option>
            <option value="kahoot">Kahoot</option>
            <option value="wikipedia">Wikipedia</option>
        </select>
        
        <button id="generate-button"><span>Download</span></button>
        
        <div class="footer">
            <a href="https://github.com/Blobby-Boi/">creator</a>
        </div>
      <div class="footer">
        Contributed by <br><a href="https://github.com/jOaawd">FMODE</a><br><a href="https://github.com/sebastian-92">CBass92</a>
      </div>
    </div>

    <script>
        const normalizeUrl = (url) => {
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                return 'https://' + url;
            }
            return url;
        };

        document.getElementById('pre-saved-options').addEventListener('change', (e) => {
            const titleInput = document.getElementById('title-input');
            const faviconInput = document.getElementById('favicon-input');
            if (e.target.value) {
                titleInput.disabled = true;
                faviconInput.disabled = true;
                
                if (e.target.value === 'google-classroom') {
                    titleInput.value = 'Home';
                } else if (e.target.value === 'clever') {
                    titleInput.value = 'Clever | Portal';
                } else if (e.target.value === 'gmail') {
                    titleInput.value = 'Inbox (13,507) - schoolgmail@gmail.com';
                } else if (e.target.value === 'schoology') {
                    titleInput.value = 'Home | Schoology';
                } else if (e.target.value === 'googledocs') {
                    titleInput.value = 'Google Docs';
                } else if (e.target.value === 'googleslides') {
                    titleInput.value = 'Google Slides';
                } else if (e.target.value === 'ixl') {
                    titleInput.value = 'IXL | Dashboard';
                } else if (e.target.value === 'kahoot') {
                    titleInput.value = 'Enter Game PIN - Kahoot!';
                } else if (e.target.value === 'wikipedia') {
                    titleInput.value = 'Carbon steel - Wikipedia';
                }
            } else {
                titleInput.disabled = false;
                faviconInput.disabled = false;
                titleInput.value = '';
            }
        });

        document.getElementById('generate-button').addEventListener('click', () => {
            setTimeout(() => {
  console.log("30 seconds have passed!");
}, 30000);
            const url = normalizeUrl(document.getElementById('url-input').value.trim());
            const titleInput = document.getElementById('title-input');
            const title = titleInput.value.trim() || "Iframe Page";

            const faviconInput = document.getElementById('favicon-input');
            let faviconUrl = '';

            const preSavedOption = document.getElementById('pre-saved-options').value;
            if (preSavedOption === 'google-classroom') {
                faviconUrl = 'https://play-lh.googleusercontent.com/w0s3au7cWptVf648ChCUP7sW6uzdwGFTSTenE178Tz87K_w1P1sFwI6h1CLZUlC2Ug';
            } else if (preSavedOption === 'clever') {
                faviconUrl = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSui5oHbrCBkSX65dyyM48zoF-a0Oxim3C_bg&s';
            } else if (preSavedOption === 'gmail') {
                faviconUrl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Gmail_icon_%282020%29.svg/2560px-Gmail_icon_%282020%29.svg.png';
            } else if (preSavedOption === 'schoology') {
                faviconUrl = 'https://resources.finalsite.net/images/f_auto,q_auto/v1626100427/k12albemarleorg/uj41eppe27bunrvhwnep/PowerSchoolLogos_Vertical-01.png'
            } else if (preSavedOption === 'googledocs') {
                faviconUrl = 'https://cdn-icons-png.flaticon.com/512/5968/5968517.png'
            } else if (preSavedOption === 'googleslides') {
                faviconUrl = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQwjPHuGuwlT6e8jmILXFJBt0KiDUBuFRE66g&s'
            } else if (preSavedOption === 'ixl') {
                faviconUrl = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpDW_Tf_9zWK7CunOwLbpwAiZIdnVLm07qyg&s'
            } else if (preSavedOption === 'kahoot') {
                faviconUrl = 'https://img.utdstc.com/icon/d5c/334/d5c3346c268caf090b36f1a4b9091f7ea88c895ff20d0418e65a8c2c11da9066:200'
            } else if (preSavedOption === 'wikipedia') {
                faviconUrl = 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Wikipedia%27s_W.svg/1024px-Wikipedia%27s_W.svg.png'
            }

            if (faviconInput.files.length > 0) {
                const reader = new FileReader();
                reader.onloadend = function() {
                    faviconUrl = reader.result;
                    generateFile(faviconUrl);
                };
                reader.readAsDataURL(faviconInput.files[0]);
            } else if (!faviconUrl) {
                faviconUrl = `https://www.google.com/s2/favicons?sz=64&domain=${url}`;
                generateFile(faviconUrl);
            } else {
                generateFile(faviconUrl);
            }

            function generateFile(faviconUrl) {
                const htmlContent = `
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>${title}</title>
                        <link rel="icon" href="${faviconUrl}" type="image/x-icon">
                        <style>
                            body, html {
                                margin: 0;
                                padding: 0;
                                height: 100%;
                                overflow: hidden;
                                background-color: #111;
                            }
                            embed {
                                width: 67%;
                                height: 67%;
                                border: none;
                            }
                        </style>
                    </head>
                    <body>
                        <embed src="${url}"></embed>
                    </body>
                    </html>
                `;

                const blob = new Blob([htmlContent], { type: 'text/html' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${title.replace(/\s+/g, '_')}.html`;
                link.click();
            }
        });
    </script>
</body>
</html>