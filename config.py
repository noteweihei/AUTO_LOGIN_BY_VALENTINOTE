# config.py

from selenium.webdriver.common.by import By

# สร้าง Dictionary เพื่อเก็บการตั้งค่าของแต่ละเว็บไซต์

WEBSITE_CONFIGS = {
# config.py (คัดลอกส่วนของ SBOBET นี้ไปวางทับของเดิม)

    "SBOBET": {
        # --- ส่วนล็อกอินหลัก ---
        "url": "https://www.cuisez.com/th-TH/betting.aspx",
        "user_locator": (By.ID, 'username'),
        "pass_locator": (By.ID, 'password'),
        "login_locator": (By.XPATH, '//*[@id="account-links"]/ul[1]/li[1]'),

        # --- Locator สำหรับปุ่มยอมรับข้อตกลง ---
        "tnc_accept_button_locator": (By.ID, 'submitBtn'),

        # --- ส่วนของหน้าบังคับเปลี่ยนรหัสผ่าน ---
        "change_pass_url": "https://sportsbook.cuisez.com/",
        "old_pass_locator": (By.ID, 'txtOldPwd'),
        "new_pass_locator": (By.ID, 'txtNewPwd1'),
        "confirm_pass_locator": (By.ID, 'txtNewPwd2'),
        "submit_change_pass_locator": (By.ID, 'submitBtn'),
        
        # --- Locator สำหรับปุ่ม Pop-up (รองรับ TH/EN) ---
        "change_pass_popup_button_locator": (By.XPATH, "//div[contains(@class, 'modal-footer')]//button[contains(text(), 'ทำรายการต่อ') or contains(text(), 'Continue')]"),

        # --- ตัวชี้วัดว่าเข้าสู่หน้าเว็บหลักสำเร็จแล้ว ---
        "login_success_indicator_locator": (By.ID, 'main-content') 
    },
}