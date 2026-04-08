import customtkinter as ctk
import requests
from tkinter import filedialog
import os

# 🔥 USE YOUR LIVE SERVER
BASE_URL = "https://pullbox-1.onrender.com"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("PullBox")
app.geometry("420x520")

file_path = ""

# -------- FUNCTIONS --------

def select_file():
    global file_path
    file_path = filedialog.askopenfilename()
    if file_path:
        file_label.configure(text=os.path.basename(file_path))

def upload_file():
    if not file_path:
        status_label.configure(text="Select a file first", text_color="red")
        return

    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                BASE_URL + "/upload",
                files={"file": f},
                data={"expiry": 30}
            )

        data = res.json()

        if "code" in data:
            status_label.configure(text=f"Code: {data['code']}", text_color="green")
        else:
            status_label.configure(text="Upload failed", text_color="red")

    except Exception as e:
        status_label.configure(text="Server error", text_color="red")

def download_file():
    code = code_entry.get()

    if not code:
        status_label.configure(text="Enter code", text_color="red")
        return

    try:
        res = requests.get(BASE_URL + f"/get/{code}")

        if res.status_code == 200:
            filename = f"file_{code}"
            with open(filename, "wb") as f:
                f.write(res.content)

            status_label.configure(text=f"Downloaded: {filename}", text_color="green")
        else:
            status_label.configure(text="Invalid or expired code", text_color="red")

    except:
        status_label.configure(text="Server error", text_color="red")

# -------- UI --------

title = ctk.CTkLabel(app, text="🚀 PullBox", font=("Arial", 26, "bold"))
title.pack(pady=(30, 10))

subtitle = ctk.CTkLabel(app, text="Simple File Sharing", font=("Arial", 12))
subtitle.pack(pady=(0, 20))

# Upload
select_btn = ctk.CTkButton(app, text="Select File", width=200, command=select_file)
select_btn.pack(pady=10)

file_label = ctk.CTkLabel(app, text="No file selected", font=("Arial", 10))
file_label.pack(pady=(0, 15))

upload_btn = ctk.CTkButton(app, text="Upload", width=200, command=upload_file)
upload_btn.pack(pady=10)

# Divider
divider = ctk.CTkLabel(app, text="──────────", font=("Arial", 12))
divider.pack(pady=20)

# Download
code_entry = ctk.CTkEntry(app, placeholder_text="Enter code", width=200)
code_entry.pack(pady=10)

download_btn = ctk.CTkButton(app, text="Download", width=200, command=download_file)
download_btn.pack(pady=10)

# Status
status_label = ctk.CTkLabel(app, text="", font=("Arial", 11))
status_label.pack(pady=25)

app.mainloop()