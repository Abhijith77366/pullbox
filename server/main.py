from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import os
from database import collection
from utils import generate_code, get_expiry
import datetime

app = FastAPI()

UPLOAD_DIR = "../uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), expiry: int = Form(30)):
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

@app.get("/get/{code}")
def get_file(code: str):
    file_data = collection.find_one({"code": code})

    if not file_data:
        return {"error": "Invalid code"}

    if datetime.datetime.utcnow() > file_data["expiry"]:
        return {"error": "Expired"}

    return FileResponse(file_data["filepath"], filename=file_data["filename"])