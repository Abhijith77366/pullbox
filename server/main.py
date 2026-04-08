from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
import datetime

from server.database import collection
from server.utils import generate_code, get_expiry

app = FastAPI()

# Upload folder (safe for Render)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), expiry: int = Form(30)):
    try:
        code = generate_code()

        filepath = os.path.join(UPLOAD_DIR, file.filename)

        # Save file
        with open(filepath, "wb") as f:
            f.write(await file.read())

        # Store in DB
        collection.insert_one({
            "code": code,
            "filename": file.filename,
            "filepath": filepath,
            "expiry": get_expiry(expiry)
        })

        return {"code": code}

    except Exception as e:
        return {"error": str(e)}


@app.get("/get/{code}")
def get_file(code: str):
    file_data = collection.find_one({"code": code})

    if not file_data:
        return {"error": "Invalid code"}

    # Expiry check
    if datetime.datetime.utcnow() > file_data["expiry"]:
        return {"error": "File expired"}

    filepath = file_data["filepath"]

    # Check file exists
    if not os.path.exists(filepath):
        return {"error": "File not found on server"}

    return FileResponse(
        path=filepath,
        filename=file_data["filename"],
        media_type="application/octet-stream"
    )