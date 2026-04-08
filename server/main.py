from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
import os
import datetime

from server.database import collection
from server.utils import generate_code, get_expiry

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 🌐 PRO WEB UI
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>PullBox</title>
        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: linear-gradient(135deg, #0f172a, #1e293b);
                color: white;
                padding-top: 40px;
                animation: fadeIn 1s ease-in;
            }

            h1 {
                color: #38bdf8;
                animation: slideDown 1s ease;
            }

            .box {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(10px);
                padding: 20px;
                margin: 20px auto;
                width: 340px;
                border-radius: 15px;
                box-shadow: 0 0 20px rgba(0,0,0,0.3);
                animation: fadeInUp 1s ease;
            }

            input, button {
                margin: 10px;
                padding: 10px;
                width: 80%;
                border-radius: 8px;
                border: none;
                outline: none;
            }

            input {
                background: #0f172a;
                color: white;
            }

            button {
                background: #38bdf8;
                color: black;
                cursor: pointer;
                transition: 0.3s;
            }

            button:hover {
                background: #0ea5e9;
                transform: scale(1.05);
            }

            #preview {
                margin-top: 10px;
                max-width: 100%;
                border-radius: 10px;
                display: none;
            }

            @keyframes fadeIn {
                from {opacity: 0;}
                to {opacity: 1;}
            }

            @keyframes slideDown {
                from {transform: translateY(-20px); opacity: 0;}
                to {transform: translateY(0); opacity: 1;}
            }

            @keyframes fadeInUp {
                from {transform: translateY(20px); opacity: 0;}
                to {transform: translateY(0); opacity: 1;}
            }
        </style>
    </head>

    <body>

        <h1>🚀 PullBox</h1>
        <p>Modern File Sharing System</p>

        <!-- Upload -->
        <div class="box">
            <h3>Upload File</h3>

            <form action="/upload" enctype="multipart/form-data" method="post">
                <input type="file" name="file" id="fileInput" required><br>

                <!-- 📁 File Preview -->
                <img id="preview"/>

                <input type="number" name="expiry" value="30"><br>
                <button type="submit">Upload</button>
            </form>
        </div>

        <!-- Download -->
        <div class="box">
            <h3>Download File</h3>
            <input type="text" id="code" placeholder="Enter Code"><br>
            <button onclick="downloadFile()">Download</button>
        </div>

        <script>
            // 📁 FILE PREVIEW
            const fileInput = document.getElementById("fileInput");
            const preview = document.getElementById("preview");

            fileInput.addEventListener("change", function() {
                const file = this.files[0];

                if (file && file.type.startsWith("image")) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = "block";
                    }
                    reader.readAsDataURL(file);
                } else {
                    preview.style.display = "none";
                }
            });

            // ⬇ DOWNLOAD
            function downloadFile() {
                var code = document.getElementById("code").value;
                if(code){
                    window.location = "/get/" + code;
                } else {
                    alert("Enter code");
                }
            }
        </script>

    </body>
    </html>
    """


# 📤 UPLOAD
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


# 📥 DOWNLOAD
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

    return FileResponse(
        path=filepath,
        filename=file_data["filename"],
        media_type="application/octet-stream"
    )