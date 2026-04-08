from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
import os
import datetime

from server.database import collection
from server.utils import generate_code, get_expiry

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>PullBox | File Sharing</title>
        <meta name="google-site-verification" content="Gn0PnOAEFIm7vpYoYM7vqtVsNpcAGrHJo0fKrUh9ahU" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="PullBox - Fast and secure file sharing system">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

            :root {
                --bg: #050a10;
                --surface: #0d1520;
                --surface2: #111d2e;
                --border: rgba(0,200,255,0.12);
                --border-bright: rgba(0,200,255,0.35);
                --accent: #00c8ff;
                --accent2: #0066ff;
                --text: #e8f4ff;
                --muted: #5a7a99;
                --success: #00e5a0;
                --error: #ff4d6d;
                --font-display: 'Syne', sans-serif;
                --font-mono: 'Space Mono', monospace;
            }

            body {
                font-family: var(--font-display);
                background: var(--bg);
                color: var(--text);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 0 16px 60px;
                overflow-x: hidden;
            }

            /* Animated grid background */
            body::before {
                content: '';
                position: fixed;
                inset: 0;
                background-image:
                    linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px);
                background-size: 40px 40px;
                pointer-events: none;
                z-index: 0;
            }

            /* Glow orbs */
            body::after {
                content: '';
                position: fixed;
                top: -200px;
                left: 50%;
                transform: translateX(-50%);
                width: 600px;
                height: 400px;
                background: radial-gradient(ellipse, rgba(0,100,255,0.08) 0%, transparent 70%);
                pointer-events: none;
                z-index: 0;
            }

            .wrapper {
                position: relative;
                z-index: 1;
                width: 100%;
                max-width: 460px;
            }

            /* Header */
            header {
                text-align: center;
                padding: 48px 0 36px;
            }

            .logo {
                display: inline-flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
            }

            .logo-icon {
                width: 36px;
                height: 36px;
                background: linear-gradient(135deg, var(--accent), var(--accent2));
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                flex-shrink: 0;
            }

            .logo-text {
                font-size: 28px;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: linear-gradient(90deg, var(--accent), #fff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }

            .tagline {
                font-size: 13px;
                color: var(--muted);
                letter-spacing: 2px;
                text-transform: uppercase;
                font-family: var(--font-mono);
            }

            /* Tabs */
            .tabs {
                display: flex;
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 4px;
                margin-bottom: 20px;
                gap: 4px;
            }

            .tab {
                flex: 1;
                padding: 10px;
                border-radius: 10px;
                border: none;
                background: transparent;
                color: var(--muted);
                font-family: var(--font-display);
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                letter-spacing: 0.3px;
            }

            .tab.active {
                background: var(--surface2);
                color: var(--accent);
                border: 1px solid var(--border-bright);
            }

            .tab:hover:not(.active) { color: var(--text); }

            /* Panels */
            .panel { display: none; }
            .panel.active { display: block; }

            /* Card */
            .card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 24px;
                position: relative;
                overflow: hidden;
            }

            .card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, var(--accent), transparent);
                opacity: 0.4;
            }

            /* Drop zone */
            #drop-zone {
                border: 1.5px dashed var(--border-bright);
                border-radius: 12px;
                padding: 28px 20px;
                text-align: center;
                cursor: pointer;
                transition: all 0.25s;
                margin-bottom: 16px;
                position: relative;
            }

            #drop-zone:hover, #drop-zone.drag-over {
                border-color: var(--accent);
                background: rgba(0,200,255,0.04);
            }

            #drop-zone.has-file {
                border-color: var(--success);
                background: rgba(0,229,160,0.04);
            }

            .drop-icon {
                font-size: 28px;
                margin-bottom: 8px;
                display: block;
            }

            .drop-title {
                font-size: 14px;
                font-weight: 600;
                color: var(--text);
                margin-bottom: 4px;
            }

            .drop-sub {
                font-size: 12px;
                color: var(--muted);
                font-family: var(--font-mono);
            }

            #file-name-display {
                font-size: 12px;
                color: var(--success);
                font-family: var(--font-mono);
                margin-top: 6px;
                word-break: break-all;
                display: none;
            }

            /* Hidden file input */
            #fileInput { display: none; }

            /* Image preview */
            #preview {
                max-width: 100%;
                max-height: 160px;
                object-fit: cover;
                border-radius: 10px;
                margin-bottom: 16px;
                display: none;
                border: 1px solid var(--border);
            }

            /* Progress */
            .progress-wrap {
                margin-bottom: 16px;
                display: none;
            }

            .progress-label {
                display: flex;
                justify-content: space-between;
                font-size: 11px;
                font-family: var(--font-mono);
                color: var(--muted);
                margin-bottom: 6px;
            }

            .progress-track {
                width: 100%;
                height: 4px;
                background: var(--surface2);
                border-radius: 2px;
                overflow: hidden;
            }

            #progress-bar {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, var(--accent2), var(--accent));
                border-radius: 2px;
                transition: width 0.2s;
            }

            /* Buttons */
            .btn {
                width: 100%;
                padding: 13px;
                border-radius: 10px;
                border: none;
                font-family: var(--font-display);
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                letter-spacing: 0.3px;
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--accent2), var(--accent));
                color: #000;
            }

            .btn-primary:hover:not(:disabled) {
                transform: translateY(-1px);
                box-shadow: 0 6px 20px rgba(0,200,255,0.25);
            }

            .btn-primary:active:not(:disabled) { transform: translateY(0); }

            .btn-primary:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }

            .btn-outline {
                background: transparent;
                color: var(--accent);
                border: 1px solid var(--border-bright);
            }

            .btn-outline:hover { background: rgba(0,200,255,0.06); }

            /* Result box */
            #result-box {
                display: none;
                margin-top: 20px;
                background: rgba(0,229,160,0.06);
                border: 1px solid rgba(0,229,160,0.25);
                border-radius: 14px;
                padding: 20px;
                animation: fadeIn 0.3s ease;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .result-label {
                font-size: 11px;
                font-family: var(--font-mono);
                color: var(--success);
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .result-label::before {
                content: '';
                display: inline-block;
                width: 6px;
                height: 6px;
                background: var(--success);
                border-radius: 50%;
                animation: pulse 1.5s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }

            .code-display-wrap {
                background: var(--surface2);
                border: 1px solid var(--border);
                border-radius: 10px;
                padding: 16px 18px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 12px;
            }

            #code-display {
                font-family: var(--font-mono);
                font-size: 26px;
                font-weight: 700;
                letter-spacing: 6px;
                color: var(--accent);
                flex: 1;
            }

            #copy-btn {
                flex-shrink: 0;
                padding: 8px 16px;
                background: rgba(0,200,255,0.1);
                border: 1px solid var(--border-bright);
                border-radius: 8px;
                color: var(--accent);
                font-family: var(--font-mono);
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                white-space: nowrap;
            }

            #copy-btn:hover { background: rgba(0,200,255,0.18); }
            #copy-btn.copied { background: rgba(0,229,160,0.15); border-color: rgba(0,229,160,0.4); color: var(--success); }

            .result-hint {
                font-size: 12px;
                color: var(--muted);
                font-family: var(--font-mono);
                text-align: center;
            }

            .result-hint span {
                color: var(--text);
            }

            /* Download input */
            .input-wrap {
                position: relative;
                margin-bottom: 16px;
            }

            .input-label {
                font-size: 11px;
                font-family: var(--font-mono);
                color: var(--muted);
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 8px;
                display: block;
            }

            .code-input {
                width: 100%;
                padding: 14px 18px;
                background: var(--surface2);
                border: 1px solid var(--border);
                border-radius: 10px;
                color: var(--text);
                font-family: var(--font-mono);
                font-size: 18px;
                letter-spacing: 4px;
                text-align: center;
                text-transform: uppercase;
                outline: none;
                transition: border-color 0.2s;
            }

            .code-input::placeholder {
                color: var(--muted);
                letter-spacing: 2px;
                font-size: 13px;
            }

            .code-input:focus { border-color: var(--border-bright); }

            /* Status message */
            #status-msg {
                display: none;
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 13px;
                font-family: var(--font-mono);
                margin-bottom: 14px;
                text-align: center;
            }

            #status-msg.error {
                background: rgba(255,77,109,0.1);
                border: 1px solid rgba(255,77,109,0.3);
                color: var(--error);
            }

            #status-msg.info {
                background: rgba(0,200,255,0.08);
                border: 1px solid var(--border-bright);
                color: var(--accent);
            }

            /* Footer */
            footer {
                text-align: center;
                margin-top: 32px;
                font-size: 11px;
                font-family: var(--font-mono);
                color: var(--muted);
                letter-spacing: 1px;
            }

            /* Expiry badge */
            .expiry-row {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                margin-bottom: 18px;
            }

            .expiry-label {
                font-size: 12px;
                color: var(--muted);
                font-family: var(--font-mono);
            }

            .expiry-options {
                display: flex;
                gap: 6px;
            }

            .expiry-opt {
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid var(--border);
                background: transparent;
                color: var(--muted);
                font-family: var(--font-mono);
                font-size: 11px;
                cursor: pointer;
                transition: all 0.15s;
            }

            .expiry-opt.active, .expiry-opt:hover {
                border-color: var(--border-bright);
                color: var(--accent);
                background: rgba(0,200,255,0.06);
            }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <header>
                <div class="logo">
                    <div class="logo-icon">📦</div>
                    <span class="logo-text">PullBox</span>
                </div>
                <p class="tagline">Instant · Secure · Zero friction</p>
            </header>

            <!-- Tabs -->
            <div class="tabs">
                <button class="tab active" onclick="switchTab('upload', this)">⬆ Upload</button>
                <button class="tab" onclick="switchTab('download', this)">⬇ Download</button>
            </div>

            <!-- Upload Panel -->
            <div id="panel-upload" class="panel active">
                <div class="card">
                    <div id="drop-zone" onclick="document.getElementById('fileInput').click()">
                        <span class="drop-icon">📂</span>
                        <p class="drop-title">Drop your file here</p>
                        <p class="drop-sub">or click to browse</p>
                        <p id="file-name-display"></p>
                    </div>
                    <input type="file" id="fileInput">
                    <img id="preview" alt="Preview">

                    <div class="expiry-row">
                        <span class="expiry-label">Expires in:</span>
                        <div class="expiry-options">
                            <button class="expiry-opt" onclick="setExpiry(10, this)">10m</button>
                            <button class="expiry-opt active" onclick="setExpiry(30, this)">30m</button>
                            <button class="expiry-opt" onclick="setExpiry(60, this)">1h</button>
                            <button class="expiry-opt" onclick="setExpiry(1440, this)">1d</button>
                        </div>
                    </div>

                    <div class="progress-wrap" id="progress-wrap">
                        <div class="progress-label">
                            <span>Uploading…</span>
                            <span id="progress-pct">0%</span>
                        </div>
                        <div class="progress-track">
                            <div id="progress-bar"></div>
                        </div>
                    </div>

                    <button class="btn btn-primary" id="upload-btn" onclick="uploadFile()">Upload File</button>

                    <!-- Result box — stays visible after upload -->
                    <div id="result-box">
                        <div class="result-label">Upload successful</div>
                        <div class="code-display-wrap">
                            <span id="code-display">——————</span>
                            <button id="copy-btn" onclick="copyCode()">Copy</button>
                        </div>
                        <p class="result-hint">Share this code • expires in <span id="expiry-hint">30 min</span></p>
                    </div>
                </div>
            </div>

            <!-- Download Panel -->
            <div id="panel-download" class="panel">
                <div class="card">
                    <label class="input-label" for="code-input">Enter share code</label>
                    <input
                        type="text"
                        id="code-input"
                        class="code-input"
                        placeholder="A1B2C3"
                        maxlength="10"
                        oninput="this.value = this.value.toUpperCase()"
                    >

                    <div id="status-msg"></div>

                    <button class="btn btn-primary" id="download-btn" onclick="downloadFile()">Download File</button>
                </div>
            </div>

            <footer>PullBox &nbsp;·&nbsp; files are automatically deleted after expiry</footer>
        </div>

        <script>
            let selectedFile = null;
            let currentCode = null;
            let expiryMinutes = 30;

            const fileInput = document.getElementById('fileInput');
            const dropZone = document.getElementById('drop-zone');
            const preview = document.getElementById('preview');

            // Tab switching
            function switchTab(name, btn) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('panel-' + name).classList.add('active');
            }

            // Expiry selector
            function setExpiry(mins, btn) {
                expiryMinutes = mins;
                document.querySelectorAll('.expiry-opt').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }

            // Drag & drop
            dropZone.addEventListener('dragover', e => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });
            dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
            dropZone.addEventListener('drop', e => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                const f = e.dataTransfer.files[0];
                if (f) handleFile(f);
            });

            fileInput.addEventListener('change', () => {
                if (fileInput.files[0]) handleFile(fileInput.files[0]);
            });

            function handleFile(file) {
                selectedFile = file;
                const nameEl = document.getElementById('file-name-display');
                nameEl.textContent = '✓ ' + file.name + ' (' + formatSize(file.size) + ')';
                nameEl.style.display = 'block';
                dropZone.classList.add('has-file');

                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = e => {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                } else {
                    preview.style.display = 'none';
                }
            }

            function formatSize(bytes) {
                if (bytes < 1024) return bytes + ' B';
                if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
                return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
            }

            function uploadFile() {
                if (!selectedFile) {
                    showDropZoneError();
                    return;
                }

                const btn = document.getElementById('upload-btn');
                btn.disabled = true;
                btn.textContent = 'Uploading…';
                document.getElementById('result-box').style.display = 'none';

                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('expiry', expiryMinutes);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload');

                xhr.upload.onprogress = e => {
                    const wrap = document.getElementById('progress-wrap');
                    wrap.style.display = 'block';
                    const pct = Math.round((e.loaded / e.total) * 100);
                    document.getElementById('progress-bar').style.width = pct + '%';
                    document.getElementById('progress-pct').textContent = pct + '%';
                };

                xhr.onload = () => {
                    document.getElementById('progress-wrap').style.display = 'none';
                    document.getElementById('progress-bar').style.width = '0%';
                    btn.disabled = false;
                    btn.textContent = 'Upload File';

                    if (xhr.status === 200) {
                        try {
                            const res = JSON.parse(xhr.responseText);
                            if (res.code) {
                                currentCode = res.code;
                                document.getElementById('code-display').textContent = res.code;
                                document.getElementById('copy-btn').textContent = 'Copy';
                                document.getElementById('copy-btn').className = '';
                                document.getElementById('expiry-hint').textContent = formatExpiry(expiryMinutes);
                                document.getElementById('result-box').style.display = 'block';
                            } else {
                                alert('Server error: ' + (res.error || 'Unknown'));
                            }
                        } catch {
                            alert('Failed to parse server response.');
                        }
                    } else {
                        alert('Upload failed. Status: ' + xhr.status);
                    }
                };

                xhr.onerror = () => {
                    document.getElementById('progress-wrap').style.display = 'none';
                    btn.disabled = false;
                    btn.textContent = 'Upload File';
                    alert('Network error. Please try again.');
                };

                xhr.send(formData);
            }

            function formatExpiry(mins) {
                if (mins < 60) return mins + ' min';
                if (mins < 1440) return (mins / 60) + ' hr';
                return (mins / 1440) + ' day';
            }

            function copyCode() {
                if (!currentCode) return;
                const btn = document.getElementById('copy-btn');
                const fallback = () => {
                    const el = document.createElement('textarea');
                    el.value = currentCode;
                    el.style.position = 'fixed';
                    el.style.opacity = '0';
                    document.body.appendChild(el);
                    el.select();
                    document.execCommand('copy');
                    document.body.removeChild(el);
                };
                const done = () => {
                    btn.textContent = '✓ Copied!';
                    btn.classList.add('copied');
                    setTimeout(() => {
                        btn.textContent = 'Copy';
                        btn.classList.remove('copied');
                    }, 2500);
                };
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(currentCode).then(done).catch(() => { fallback(); done(); });
                } else {
                    fallback(); done();
                }
            }

            function downloadFile() {
                const code = document.getElementById('code-input').value.trim();
                const msg = document.getElementById('status-msg');
                if (!code) {
                    msg.textContent = 'Please enter a share code.';
                    msg.className = 'error';
                    msg.style.display = 'block';
                    return;
                }
                msg.textContent = 'Fetching your file…';
                msg.className = 'info';
                msg.style.display = 'block';

                const btn = document.getElementById('download-btn');
                btn.disabled = true;
                btn.textContent = 'Fetching…';

                // Use fetch to check before redirecting so we can show errors
                fetch('/get/' + encodeURIComponent(code))
                    .then(r => {
                        btn.disabled = false;
                        btn.textContent = 'Download File';
                        if (r.ok && r.headers.get('content-disposition')) {
                            // It's a real file response — redirect to trigger download
                            window.location = '/get/' + encodeURIComponent(code);
                            msg.style.display = 'none';
                        } else {
                            return r.json().then(data => {
                                msg.textContent = '✗ ' + (data.error || 'Something went wrong.');
                                msg.className = 'error';
                            });
                        }
                    })
                    .catch(() => {
                        btn.disabled = false;
                        btn.textContent = 'Download File';
                        msg.textContent = '✗ Network error. Try again.';
                        msg.className = 'error';
                    });
            }

            function showDropZoneError() {
                dropZone.style.borderColor = 'var(--error)';
                dropZone.querySelector('.drop-title').style.color = 'var(--error)';
                setTimeout(() => {
                    dropZone.style.borderColor = '';
                    dropZone.querySelector('.drop-title').style.color = '';
                }, 1500);
            }
        </script>
    </body>
    </html>
    """

# 📤 UPLOAD — filename collision fix: prepend timestamp
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), expiry: int = Form(30)):
    try:
        code = generate_code()
        timestamp = int(datetime.datetime.utcnow().timestamp())
        safe_filename = f"{timestamp}_{file.filename}"  # prevents overwrite
        filepath = os.path.join(UPLOAD_DIR, safe_filename)

        contents = await file.read()
        if not contents:
            return {"error": "File is empty"}

        with open(filepath, "wb") as f:
            f.write(contents)

        collection.insert_one({
            "code": code,
            "filename": file.filename,    # original name shown on download
            "filepath": filepath,         # timestamped path on disk
            "expiry": get_expiry(expiry)
        })

        return {"code": code}
    except Exception as e:
        return {"error": str(e)}

# 📥 DOWNLOAD
@app.get("/get/{code}")
def get_file(code: str):
    file_data = collection.find_one({"code": code})
    if not file_data:
        return {"error": "Invalid or expired code"}
    if datetime.datetime.utcnow() > file_data["expiry"]:
        return {"error": "File has expired"}
    if not os.path.exists(file_data["filepath"]):
        return {"error": "File not found on server"}
    return FileResponse(
        file_data["filepath"],
        filename=file_data["filename"],
        media_type="application/octet-stream"
    )