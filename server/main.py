from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
import os
import datetime

from server.database import collection
from server.utils import generate_code, get_expiry

app = FastAPI()

# Upload folder
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 🔥 WEB HOMEPAGE (LIKE GUI)
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
                background: #0f172a;
                color: white;
                padding-top: 50px;
            }
            h1 {
                color: #38bdf8;
            }
            .box {
                background: #1e293b;
                padding: 20px;
                margin: 20px auto;
                width: 320px;
                border-radius: 10px;
            }
            input, button {
                margin: 10px;
                padding: 10px;
                width: 80%;
                border-radius: 5px;
                border: none;
            }
            button {
                background: #38bdf8;
                color: black;
                cursor: pointer;
            }
        </style>
    </head>

    <body>
        <h1>🚀 PullBox</h1>
        <p>Upload & Share Files Using Code</p>

        <div class="box">
            <h3>Upload File</h3>
            <form action="/upload" enctype="multipart/form-data" method="post">
                <input type="file" name="file" required><br>
                <input type="number" name="expiry" value="30"><br>
                <button type="submit">Upload</button>
            </form>
        </div>

        <div class="box">
            <h3>Download File</h3>
            <input type="text" id="code" placeholder="Enter Code"><br>
            <button onclick="downloadFile()">Download</button>
        </div>

        <script>
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


# 🔥 UPLOAD API
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


# 🔥 DOWNLOAD API
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