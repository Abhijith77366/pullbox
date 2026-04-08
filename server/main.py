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
        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: linear-gradient(-45deg, #0f172a, #1e293b, #0ea5e9, #020617);
                background-size: 400% 400%;
                animation: bg 10s ease infinite;
                color: white;
                margin: 0;
                padding: 10px;
            }
            @keyframes bg {
                0% {background-position: 0% 50%;}
                50% {background-position: 100% 50%;}
                100% {background-position: 0% 50%;}
            }
            h1 {margin-top: 30px; color: #38bdf8;}
            .box {
                background: rgba(255,255,255,0.08);
                padding: 20px;
                margin: 20px auto;
                width: 90%;
                max-width: 350px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            input, button {
                margin: 10px;
                padding: 10px;
                width: 90%;
                border-radius: 8px;
                border: none;
            }
            input {background: #0f172a; color: white;}
            button {background: #38bdf8; cursor: pointer; transition: 0.3s;}
            button:hover {transform: scale(1.05); background: #0ea5e9;}
            button:disabled {background: #555; cursor: not-allowed; transform: none;}
            #drop-zone {
                border: 2px dashed #38bdf8;
                padding: 20px;
                margin: 10px;
                border-radius: 10px;
            }
            #preview {max-width: 100%; display: none; border-radius: 10px;}
            #progress {
                width: 90%;
                height: 10px;
                background: #1e293b;
                margin: auto;
                border-radius: 5px;
                overflow: hidden;
                display: none;
            }
            #progress-bar {height: 100%; width: 0%; background: #38bdf8; transition: width 0.2s;}

            /* ✅ Persistent result box */
            #result-box {
                display: none;
                background: rgba(56, 189, 248, 0.1);
                border: 1.5px solid #38bdf8;
                border-radius: 10px;
                padding: 14px;
                margin: 10px auto;
                width: 85%;
            }
            #result-box p {margin: 0 0 8px; font-size: 13px; color: #94a3b8;}
            #code-row {display: flex; align-items: center; justify-content: center; gap: 10px;}
            #code-display {font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #38bdf8;}
            #copy-btn {
                padding: 6px 14px !important;
                width: auto !important;
                font-size: 13px;
                background: #0f172a;
                color: #38bdf8;
                border: 1px solid #38bdf8 !important;
                border-radius: 6px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>🚀 PullBox</h1>
        <p>Fast & Secure File Sharing</p>

        <div class="box">
            <h3>Upload</h3>
            <div id="drop-zone">Drag & Drop File Here</div>
            <input type="file" id="fileInput"><br>
            <img id="preview">
            <div id="progress"><div id="progress-bar"></div></div>
            <button id="upload-btn" onclick="uploadFile()">Upload</button>

            <!-- ✅ Persistent result box with copy button -->
            <div id="result-box">
                <p>Your share code — send this to anyone</p>
                <div id="code-row">
                    <span id="code-display"></span>
                    <button id="copy-btn" onclick="copyCode()">Copy</button>
                </div>
            </div>
        </div>

        <div class="box">
            <h3>Download</h3>
            <input type="text" id="code" placeholder="Enter Code"><br>
            <button onclick="downloadFile()">Download</button>
        </div>

        <script>
            let selectedFile = null;
            let currentCode = null;
            const fileInput = document.getElementById("fileInput");
            const preview = document.getElementById("preview");
            const dropZone = document.getElementById("drop-zone");

            dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.style.background = "#1e293b"; });
            dropZone.addEventListener("dragleave", () => { dropZone.style.background = "transparent"; });
            dropZone.addEventListener("drop", e => {
                e.preventDefault();
                selectedFile = e.dataTransfer.files[0];
                handlePreview(selectedFile);
            });
            fileInput.addEventListener("change", () => {
                selectedFile = fileInput.files[0];
                handlePreview(selectedFile);
            });

            function handlePreview(file) {
                if (file && file.type.startsWith("image")) {
                    const reader = new FileReader();
                    reader.onload = e => { preview.src = e.target.result; preview.style.display = "block"; };
                    reader.readAsDataURL(file);
                } else {
                    preview.style.display = "none";
                }
            }

            function uploadFile() {
                if (!selectedFile) { alert("Please select a file first."); return; }

                const btn = document.getElementById("upload-btn");
                btn.disabled = true;
                btn.textContent = "Uploading…";
                document.getElementById("result-box").style.display = "none";

                let formData = new FormData();
                formData.append("file", selectedFile);
                formData.append("expiry", 30);

                let xhr = new XMLHttpRequest();
                xhr.open("POST", "/upload");

                xhr.upload.onprogress = e => {
                    document.getElementById("progress").style.display = "block";
                    let percent = (e.loaded / e.total) * 100;
                    document.getElementById("progress-bar").style.width = percent + "%";
                };

                xhr.onload = () => {
                    document.getElementById("progress").style.display = "none";
                    document.getElementById("progress-bar").style.width = "0%";
                    btn.disabled = false;
                    btn.textContent = "Upload";

                    if (xhr.status === 200) {
                        try {
                            let res = JSON.parse(xhr.responseText);
                            if (res.code) {
                                currentCode = res.code;
                                document.getElementById("code-display").textContent = res.code;
                                document.getElementById("result-box").style.display = "block";
                                document.getElementById("copy-btn").textContent = "Copy";
                            } else {
                                alert("Error: " + (res.error || "Unknown error"));
                            }
                        } catch {
                            alert("Error parsing server response.");
                        }
                    } else {
                        alert("Upload failed. Server returned status " + xhr.status);
                    }
                };

                xhr.onerror = () => {
                    btn.disabled = false;
                    btn.textContent = "Upload";
                    document.getElementById("progress").style.display = "none";
                    alert("Network error. Please try again.");
                };

                xhr.send(formData);
            }

            function copyCode() {
                if (!currentCode) return;
                navigator.clipboard.writeText(currentCode).then(() => {
                    const btn = document.getElementById("copy-btn");
                    btn.textContent = "Copied!";
                    setTimeout(() => btn.textContent = "Copy", 2000);
                }).catch(() => {
                    // Fallback for older browsers
                    const el = document.createElement("textarea");
                    el.value = currentCode;
                    document.body.appendChild(el);
                    el.select();
                    document.execCommand("copy");
                    document.body.removeChild(el);
                    document.getElementById("copy-btn").textContent = "Copied!";
                    setTimeout(() => document.getElementById("copy-btn").textContent = "Copy", 2000);
                });
            }

            function downloadFile() {
                let code = document.getElementById("code").value.trim();
                if (code) { window.location = "/get/" + code; }
                else { alert("Please enter a code."); }
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
        safe_filename = f"{timestamp}_{file.filename}"   # ✅ prevents overwrite
        filepath = os.path.join(UPLOAD_DIR, safe_filename)

        with open(filepath, "wb") as f:
            f.write(await file.read())

        collection.insert_one({
            "code": code,
            "filename": file.filename,       # original name for download
            "filepath": filepath,            # timestamped path on disk
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
        return {"error": "Invalid code"}
    if datetime.datetime.utcnow() > file_data["expiry"]:
        return {"error": "File expired"}
    if not os.path.exists(file_data["filepath"]):
        return {"error": "File not found on server"}
    return FileResponse(file_data["filepath"], filename=file_data["filename"])