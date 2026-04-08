import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def upload(file_path):
    with open(file_path, "rb") as f:
        res = requests.post(
            BASE_URL + "/upload",
            files={"file": f},
            data={"expiry": 30}
        )

    print("Code:", res.json()["code"])

def download(code):
    res = requests.get(BASE_URL + f"/get/{code}")

    if res.status_code == 200:
        with open("downloaded_file", "wb") as f:
            f.write(res.content)
        print("Downloaded")
    else:
        print(res.json())

if __name__ == "__main__":
    if sys.argv[1] == "upload":
        upload(sys.argv[2])
    elif sys.argv[1] == "get":
        download(sys.argv[2])