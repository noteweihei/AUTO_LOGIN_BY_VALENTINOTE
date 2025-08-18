import tkinter as tk
from tkinter import messagebox, ttk
import requests  # ใช้สำหรับดาวน์โหลดไฟล์: pip install requests
import json
import os
import sys
import subprocess
import zipfile
from io import BytesIO

# --- การตั้งค่า ---
VERSION_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/version.json" # URL ของไฟล์ version.json
APP_NAME = "auto_login.exe" # ชื่อไฟล์โปรแกรมหลักของคุณ
LOCAL_VERSION_FILE = "local_version.json"

def get_server_version():
    """ดึงข้อมูลเวอร์ชันล่าสุดจากเซิร์ฟเวอร์"""
    try:
        response = requests.get(VERSION_URL)
        response.raise_for_status() # เช็คว่า request สำเร็จหรือไม่
        return response.json()
    except Exception as e:
        messagebox.showerror("Connection Error", f"ไม่สามารถเชื่อมต่อเพื่อตรวจสอบอัปเดตได้:\n{e}")
        return None

def get_local_version():
    """อ่านเวอร์ชันที่ติดตั้งในเครื่อง"""
    if not os.path.exists(LOCAL_VERSION_FILE):
        return {"version": "0.0.0"} # ถ้าไม่มีไฟล์ ให้ถือว่าเป็นเวอร์ชันเก่าสุด
    try:
        with open(LOCAL_VERSION_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"version": "0.0.0"}

def update_application(download_url, new_version):
    """กระบวนการดาวน์โหลดและติดตั้งอัปเดต"""
    try:
        # 1. ดาวน์โหลดไฟล์ ZIP
        print(f"กำลังดาวน์โหลดเวอร์ชัน {new_version} จาก {download_url}")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # 2. แตกไฟล์ ZIP และเขียนทับไฟล์เก่า
        print("กำลังแตกไฟล์และติดตั้งอัปเดต...")
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(".") # แตกไฟล์ลงในโฟลเดอร์ปัจจุบัน
        
        # 3. อัปเดตไฟล์เวอร์ชันในเครื่อง
        with open(LOCAL_VERSION_FILE, 'w') as f:
            json.dump({"version": new_version}, f)
            
        messagebox.showinfo("อัปเดตสำเร็จ", f"โปรแกรมอัปเดตเป็นเวอร์ชัน {new_version} เรียบร้อยแล้ว\nโปรแกรมจะทำการรีสตาร์ท")
        
        # 4. รีสตาร์ทตัวเอง (เปิด launcher ใหม่) เพื่อเริ่มโปรแกรมหลัก
        os.startfile(sys.executable)
        sys.exit()

    except Exception as e:
        messagebox.showerror("Update Error", f"เกิดข้อผิดพลาดระหว่างการอัปเดต:\n{e}")
        return False
    return True

def launch_app():
    """เปิดโปรแกรมหลัก"""
    if os.path.exists(APP_NAME):
        subprocess.Popen([APP_NAME])
    else:
        messagebox.showwarning("ไม่พบไฟล์", f"ไม่พบไฟล์โปรแกรมหลัก ({APP_NAME})\nกรุณาลองอัปเดตอีกครั้ง")
    sys.exit() # ปิด Launcher หลังเปิดโปรแกรมหลัก

# --- Main Logic ---
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # ซ่อนหน้าต่างหลักของ Tkinter

    print("กำลังตรวจสอบเวอร์ชัน...")
    server_info = get_server_version()
    
    if server_info:
        local_info = get_local_version()
        
        server_version = server_info.get("version", "0.0.0")
        local_version = local_info.get("version", "0.0.0")

        print(f"เวอร์ชันล่าสุด: {server_version}, เวอร์ชันปัจจุบัน: {local_version}")
        
        if server_version > local_version:
            if messagebox.askyesno("พบอัปเดต", f"มีโปรแกรมเวอร์ชันใหม่ ({server_version}) ให้ดาวน์โหลด\nคุณต้องการอัปเดตหรือไม่?"):
                update_application(server_info["url"], server_version)
            else:
                launch_app() # ถ้าไม่ต้องการอัปเดต ก็เปิดโปรแกรมเวอร์ชันเก่า
        else:
            print("คุณใช้โปรแกรมเวอร์ชันล่าสุดแล้ว")
            launch_app()
    else:
        # ถ้าเชื่อมต่อเน็ตไม่ได้ ก็ให้เปิดโปรแกรมที่มีอยู่ไปก่อน
        print("ไม่สามารถตรวจสอบอัปเดตได้, กำลังเปิดโปรแกรม...")
        launch_app()