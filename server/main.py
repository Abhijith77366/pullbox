from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
import os
import datetime

from server.database import collection
from server.utils import generate_code, get_expiry

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 🌐 WEB UI
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>PullBox | File Sharing</title>

        <meta name="description" content="PullBox - Fast and secure file sharing system">
        <meta name="author" content="Abhijith">

        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: linear-gradient(-45deg, #0f172a, #1e293b, #0ea5e9, #020617);
                background-size: 400% 400%;
                animation: bg 10s ease infinite;
                color: white;
            }

            @keyframes bg {
                0% {background-position: 0% 50%;}
                50% {background-position: 100% 50%;}
                100% {background-position: 0% 50%;}
            }

            h1 {
                margin-top: 30px;
                color: #38bdf8;
            }

            .box {
                background: rgba(255,255,255,0.08);
                padding: 20px;
                margin: 20px auto;
                width: 350px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }

            input, button {
                margin: 10px;
                padding: 10px;
                width: 80%;
                border-radius: 8px;
                border: none;
            }

            input {
                background: #0f172a;
                color: white;
            }

            button {
                background: #38bdf8;
                cursor: pointer;
                transition: 0.3s;
            }

            button:hover {
                transform: scale(1.05);
                background: #0ea5e9;
            }

            #drop-zone {
                border: 2px dashed #38bdf8;
                padding: 20px;
                margin: 10px;
                border-radius: 10px;
            }

            #preview {
                max-width: 100%;
                display: none;
                border-radius: 10px;
            }

            #progress {
                width: 80%;
                height: 10px;
                background: #1e293b;
                margin: auto;
                border-radius: 5px;
                overflow: hidden;
                display: none;
            }

            #progress-bar {
                height: 100%;
                width: 0%;
                background: #38bdf8;
            }

            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #38bdf8;
                color: black;
                padding: 10px;
                border-radius: 8px;
                display: none;
            }
        </style>
    </head>

    <body>

        <h1>🚀 PullBox</h1>
        <p>Fast & Secure File Sharing</p>

        <!-- Upload -->
        <div class="box">
            <h3>Upload</h3>

            <div id="drop-zone">Drag & Drop File Here</div>
            <input type="file" id="fileInput"><br>

            <img id="preview">

            <div id="progress"><div id="progress-bar"></div></div>

            <button onclick="uploadFile()">Upload</button>
        </div>

        <!-- Download -->
        <div class="box">
            <h3>Download</h3>
            <input type="text" id="code" placeholder="Enter Code"><br>
            <button onclick="downloadFile()">Download</button>
        </div>

        <!-- Toast -->
        <div id="toast" class="toast"></div>

        <script>
            let selectedFile = null;

            const fileInput = document.getElementById("fileInput");
            const preview = document.getElementById("preview");
            const dropZone = document.getElementById("drop-zone");

            // Drag & Drop
            dropZone.addEventListener("dragover", e => {
                e.preventDefault();
                dropZone.style.background = "#1e293b";
            });

            dropZone.addEventListener("dragleave", () => {
                dropZone.style.background = "transparent";
            });

            dropZone.addEventListener("drop", e => {
                e.preventDefault();
                selectedFile = e.dataTransfer.files[0];
                handlePreview(selectedFile);
            });

            fileInput.addEventListener("change", () => {
                selectedFile = fileInput.files[0];
                handlePreview(selectedFile);
            });

            function handlePreview(file){
                if(file && file.type.startsWith("image")){
                    const reader = new FileReader();
                    reader.onload = e => {
                        preview.src = e.target.result;
                        preview.style.display = "block";
                    };
                    reader.readAsDataURL(file);
                } else {
                    preview.style.display = "none";
                }
            }

            // Upload
            function uploadFile(){
                if(!selectedFile){
                    showToast("Select file first");
                    return;
                }

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
                    try {
                        let res = JSON.parse(xhr.responseText);
                        if(res.code){
                            showToast("Code: " + res.code);
                        } else {
                            showToast("Upload failed");
                        }
                    } catch {
                        showToast("Error uploading");
                    }
                };

                xhr.send(formData);
            }

            // Download
            function downloadFile(){
                let code = document.getElementById("code").value.trim();
                if(code){
                    window.location = "/get/" + code;
                } else {
                    showToast("Enter code");
                }
            }

            function showToast(msg){
                let t = document.getElementById("toast");
                t.innerText = msg;
                t.style.display = "block";
                setTimeout(()=>{t.style.display="none"},3000);
            }
        </script>

    </body>
    </html>
    """


# 📤 UPLOAD API
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), expiry: int = Form(30)):
    try:
        code = generate_code()
        filepath = os.path.join(UPLOAD_DIR, file.filename)

        with open(filepath, "wb") as f:
            f.write(await file.read())

        collection.insert_one({
            "code": code,
            "filename": file.filename,
            "filepath": filepath,
            "expiry": get_expiry(expiry)
        })

        return {"code": code}

    except Exception as e:
        return {"error": str(e)}


# 📥 DOWNLOAD API
@app.get("/get/{code}")
def get_file(code: str):
    file_data = collection.find_one({"code": code})

    if not file_data:
        return {"error": "Invalid code"}

    if datetime.datetime.utcnow() > file_data["expiry"]:
        return {"error": "File expired"}

    filepath = file_data["filepath"]

    if not os.path.exists(filepath):
        return {"error": "File not found"}

    return FileResponse(filepath, filename=file_data["filename"])