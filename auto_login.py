import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font
import pandas as pd
import threading
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService  # <-- เพิ่มบรรทัดนี้
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager  # <-- เพิ่มบรรทัดนี้
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, NoSuchElementException, WebDriverException, ElementClickInterceptedException
import sys
import os

try:
    from config import WEBSITE_CONFIGS
except ImportError:
    WEBSITE_CONFIGS = {}
    messagebox.showerror("Error", "ไม่พบไฟล์ config.py!")

CURRENT_CONFIG = {}
STATUS_SUCCESS = "สำเร็จ"
STATUS_PASSWORD_CHANGED = "เปลี่ยนรหัสผ่านสำเร็จ"
STATUS_PENDING = "รอดำเนินการ"
STATUS_MISSING_NEW_PASS = "ไม่มีข้อมูลรหัสผ่านใหม่"
STATUS_INVALID_PASSWORD = "รหัสผ่านไม่ถูกต้อง"
STATUS_ACCESS_DENIED = "เข้าใช้งานถูกจำกัด"
STATUS_RETRY_FAILED = "Error (Retry Failed)"

RESTART_DRIVER_INTERVAL = 100
MAX_RETRIES = 2

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snake Game")
        self.root.resizable(False, False)

        self.GAME_WIDTH = 500
        self.GAME_HEIGHT = 500
        self.SPEED = 100
        self.SPACE_SIZE = 20
        self.BODY_PARTS = 3
        self.SNAKE_COLOR = "#00FF00"
        self.FOOD_COLOR = "#FF0000"
        self.BACKGROUND_COLOR = "#000000"

        self.score = 0
        self.direction = 'down'
        self.paused = False
        self.game_over_flag = False

        control_frame = tk.Frame(self.root, bg='gray20')
        control_frame.pack(fill=tk.X)

        self.score_label = tk.Label(control_frame, text=f"Score: {self.score}", font=('Kanit', 12, 'bold'), bg='gray20', fg='white')
        self.score_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.status_label = tk.Label(control_frame, text="", font=('Kanit', 12, 'bold'), bg='gray20', fg='yellow')
        self.status_label.pack(side=tk.LEFT, expand=True)

        self.start_button = tk.Button(control_frame, text="Start", command=self.start_game, font=('Kanit', 9))
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.pause_button = tk.Button(control_frame, text="Pause", command=self.toggle_pause, font=('Kanit', 9), state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.restart_button = tk.Button(control_frame, text="Restart", command=self.restart_game, font=('Kanit', 9))
        self.restart_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.canvas = tk.Canvas(self.root, bg=self.BACKGROUND_COLOR, height=self.GAME_HEIGHT, width=self.GAME_WIDTH)
        self.canvas.pack()

        self.root.update()
        
        self.root.bind('<Left>', lambda event: self.change_direction('left'))
        self.root.bind('<Right>', lambda event: self.change_direction('right'))
        self.root.bind('<Up>', lambda event: self.change_direction('up'))
        self.root.bind('<Down>', lambda event: self.change_direction('down'))

        self.setup_game()

    def setup_game(self):
        self.canvas.delete("all")
        self.direction = 'down'
        self.score = 0
        self.score_label.config(text=f"Score: {self.score}")
        self.status_label.config(text="")
        self.paused = False
        self.game_over_flag = True
        self.pause_button.config(text="Pause", state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)

        self.snake_coordinates = []
        self.squares = []

        for i in range(0, self.BODY_PARTS):
            self.snake_coordinates.append([0, 0])

        for x, y in self.snake_coordinates:
            square = self.canvas.create_rectangle(x, y, x + self.SPACE_SIZE, y + self.SPACE_SIZE, fill=self.SNAKE_COLOR, tag="snake")
            self.squares.append(square)
        
        self.new_food()
        
    def start_game(self):
        self.game_over_flag = False
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.status_label.config(text="")
        self.next_turn()

    def next_turn(self):
        if self.game_over_flag or self.paused:
            return

        x, y = self.snake_coordinates[0]

        if self.direction == "up": y -= self.SPACE_SIZE
        elif self.direction == "down": y += self.SPACE_SIZE
        elif self.direction == "left": x -= self.SPACE_SIZE
        elif self.direction == "right": x += self.SPACE_SIZE

        self.snake_coordinates.insert(0, [x, y])
        square = self.canvas.create_rectangle(x, y, x + self.SPACE_SIZE, y + self.SPACE_SIZE, fill=self.SNAKE_COLOR)
        self.squares.insert(0, square)

        if x == self.food_coordinates[0] and y == self.food_coordinates[1]:
            self.score += 1
            self.score_label.config(text=f"Score: {self.score}")
            self.canvas.delete("food")
            self.new_food()
        else:
            del self.snake_coordinates[-1]
            self.canvas.delete(self.squares[-1])
            del self.squares[-1]

        if self.check_collisions():
            self.game_over()
        else:
            self.root.after(self.SPEED, self.next_turn)

    def change_direction(self, new_direction):
        if new_direction == 'left' and self.direction != 'right': self.direction = new_direction
        elif new_direction == 'right' and self.direction != 'left': self.direction = new_direction
        elif new_direction == 'up' and self.direction != 'down': self.direction = new_direction
        elif new_direction == 'down' and self.direction != 'up': self.direction = new_direction

    def check_collisions(self):
        x, y = self.snake_coordinates[0]
        if x < 0 or x >= self.GAME_WIDTH or y < 0 or y >= self.GAME_HEIGHT:
            return True
        for body_part in self.snake_coordinates[1:]:
            if x == body_part[0] and y == body_part[1]:
                return True
        return False

    def new_food(self):
        x = random.randint(0, int(self.GAME_WIDTH / self.SPACE_SIZE) - 1) * self.SPACE_SIZE
        y = random.randint(0, int(self.GAME_HEIGHT / self.SPACE_SIZE) - 1) * self.SPACE_SIZE
        self.food_coordinates = [x, y]
        self.canvas.create_oval(x, y, x + self.SPACE_SIZE, y + self.SPACE_SIZE, fill=self.FOOD_COLOR, tag="food")

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.status_label.config(text="PAUSED")
            self.pause_button.config(text="Resume")
        else:
            self.status_label.config(text="")
            self.pause_button.config(text="Pause")
            self.next_turn()

    def restart_game(self):
        self.setup_game()

    def game_over(self):
        self.game_over_flag = True
        self.status_label.config(text="GAME OVER!")
        self.pause_button.config(state=tk.DISABLED)

class AutoLoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Login & Password Changer by Valentinote [V.4.5]")
        self.root.geometry("1200x750")
        
        self.BG_COLOR = '#2E2E2E'
        self.FRAME_COLOR = '#3C3C3C'
        self.TEXT_COLOR = '#EAEAEA'
        self.ACCENT_COLOR = '#007ACC'
        self.SUCCESS_BG = '#093d15'
        self.ERROR_BG = '#4a1919'
        
        self.root.config(bg=self.BG_COLOR)
        try:
            self.root.iconbitmap("img/icon.ico")
        except tk.TclError:
            print("ไม่พบไฟล์ icon.ico")

        self.default_font = font.Font(family='Kanit', size=10)
        self.heading_font = font.Font(family='Kanit', size=10, weight='bold')
        
        self._apply_dark_theme()

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.current_index = 0
        self.active_driver = None
        self.df = None
        self.excel_path = ""
        self.error_during_run = False
        self.user_stopped = False
        self.start_time = 0
        self.processed_count = 0
        self.headless_var = tk.BooleanVar(value=True)
        self.driver_path = None
        self.retry_counts = {}
        self.current_driver_is_headless = None
        self.force_driver_restart = False

        self.browser_var = tk.StringVar(value="Firefox")  # <-- เพิ่มบรรทัดนี้ (ค่าเริ่มต้นคือ Firefox)
        self.driver_path_browser = None  # <-- เพิ่มบรรทัดนี้

        self._create_widgets()

# auto_login.py (แก้ไขฟังก์ชัน _apply_dark_theme)

    def _apply_dark_theme(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        
        # --- การตั้งค่า Style หลัก (เหมือนเดิม) ---
        style.configure('.', background=self.BG_COLOR, foreground=self.TEXT_COLOR, fieldbackground=self.FRAME_COLOR, borderwidth=1, font=self.default_font)
        style.map('.', background=[('active', self.FRAME_COLOR)])
        style.configure('TFrame', background=self.BG_COLOR)
        style.configure('TLabel', background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=self.default_font)
        style.configure('TLabelframe', background=self.BG_COLOR, bordercolor=self.ACCENT_COLOR, relief='solid')
        style.configure('TLabelframe.Label', background=self.BG_COLOR, foreground=self.TEXT_COLOR, font=self.default_font)
        
        # --- Style ปุ่ม TButton พื้นฐาน (สีน้ำเงิน) ---
        style.configure('TButton', font=self.default_font, padding=5, relief='flat', borderwidth=0)
        style.map('TButton', 
                  background=[('!active', self.ACCENT_COLOR), ('pressed', self.FRAME_COLOR), ('active', '#0098ff')], 
                  foreground=[('!active', 'white')])
        
        # =====================================================================
        # ส่วนที่ปรับปรุง: เพิ่ม Style สีสำหรับปุ่มต่างๆ
        # =====================================================================
        # --- Style ปุ่มสีเขียว (Green.TButton) ---
        style.configure('Green.TButton', background='#28a745', foreground='white')
        style.map('Green.TButton', background=[('active', '#218838'), ('pressed', '#1e7e34')])

        # --- Style ปุ่มสีแดง (Red.TButton) ---
        style.configure('Red.TButton', background='#dc3545', foreground='white')
        style.map('Red.TButton', background=[('active', '#c82333'), ('pressed', '#bd2130')])
        
        # --- Style ปุ่มสีส้ม (Orange.TButton) ---
        style.configure('Orange.TButton', background='#ffc107', foreground='black')
        style.map('Orange.TButton', background=[('active', '#e0a800'), ('pressed', '#d39e00')])

        # --- Style ปุ่มสีเทา (Gray.TButton) ---
        style.configure('Gray.TButton', background='#6c757d', foreground='white')
        style.map('Gray.TButton', background=[('active', '#5a6268'), ('pressed', '#545b62')])
        # =====================================================================

        style.configure('TCheckbutton', background=self.BG_COLOR, indicatorbackground=self.FRAME_COLOR, font=self.default_font)
        style.map('TCheckbutton', indicatorbackground=[('pressed', self.FRAME_COLOR), ('selected', self.ACCENT_COLOR)])
        self.root.option_add('*TCombobox*Listbox*Background', self.FRAME_COLOR)
        self.root.option_add('*TCombobox*Listbox*Foreground', self.TEXT_COLOR)
        self.root.option_add('*TCombobox*Listbox*selectBackground', self.ACCENT_COLOR)
        style.map('TCombobox', fieldbackground=[('readonly', self.FRAME_COLOR)], foreground=[('readonly', self.TEXT_COLOR)])
        style.configure("Treeview", background=self.FRAME_COLOR, fieldbackground=self.FRAME_COLOR, foreground=self.TEXT_COLOR, rowheight=25)
        style.configure("Treeview.Heading", background=self.FRAME_COLOR, font=self.heading_font, padding=5)
        style.map("Treeview", background=[('selected', self.ACCENT_COLOR)])
        style.map('Treeview.Heading', background=[('active', self.BG_COLOR)])
        style.configure('TProgressbar', thickness=15, background=self.ACCENT_COLOR, troughcolor=self.FRAME_COLOR)

# auto_login.py (แก้ไขฟังก์ชัน _create_widgets ฉบับสมบูรณ์)

    def _create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- เฟรมหลักสำหรับปุ่มควบคุมทั้งหมด ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5, padx=5)

        # --- กลุ่ม 1: จัดการข้อมูล (ซ้าย) ---
        data_frame = ttk.LabelFrame(control_frame, text="ไฟล์ข้อมูล")
        data_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
        
        self.btn_load = ttk.Button(data_frame, text="เลือกไฟล์ Excel", command=self.load_excel_file, style='TButton')
        self.btn_load.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_clear = ttk.Button(data_frame, text="🧹 เคลียร์ข้อมูล", command=self.clear_data, style='Red.TButton')
        self.btn_clear.pack(side=tk.LEFT, padx=5, pady=5)

        # --- กลุ่ม 2: ตั้งค่าการทำงาน ---
        settings_frame = ttk.LabelFrame(control_frame, text="ตั้งค่า")
        settings_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        ttk.Label(settings_frame, text="เว็บไซต์:").pack(side=tk.LEFT, padx=(5, 2), pady=5)
        self.website_options = list(WEBSITE_CONFIGS.keys())
        self.website_var = tk.StringVar()
        self.website_dropdown = ttk.Combobox(settings_frame, textvariable=self.website_var, values=self.website_options, state="readonly", width=12)
        self.website_dropdown.pack(side=tk.LEFT, padx=2, pady=5)
        if self.website_options: self.website_dropdown.set(self.website_options[0])
        self.website_dropdown.bind("<<ComboboxSelected>>", self.on_website_select)
        self.on_website_select()

        browser_frame = ttk.Frame(settings_frame)
        browser_frame.pack(side=tk.LEFT, padx=5, pady=0)
        ttk.Radiobutton(browser_frame, text="Firefox", variable=self.browser_var, value="Firefox").pack(anchor=tk.W)
        ttk.Radiobutton(browser_frame, text="Chrome", variable=self.browser_var, value="Chrome").pack(anchor=tk.W)
        
        self.check_headless = ttk.Checkbutton(settings_frame, text="ทำงานเบื้องหลัง", variable=self.headless_var)
        self.check_headless.pack(side=tk.LEFT, padx=5, pady=5, expand=True)
        
        # --- กลุ่ม 3: ควบคุมการทำงาน ---
        self.control_action_frame = ttk.LabelFrame(control_frame, text="ควบคุมการทำงาน")
        self.control_action_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)
        
        self.btn_start = ttk.Button(self.control_action_frame, text="▶ เริ่มทำงาน", command=self.start_processing, style='Green.TButton')
        self.btn_pause = ttk.Button(self.control_action_frame, text="⏸️ หยุดชั่วคราว", command=self.pause_processing, style='Orange.TButton')
        self.btn_resume = ttk.Button(self.control_action_frame, text="⏯️ ทำงานต่อ", command=self.resume_processing, style='Green.TButton')
        self.btn_end = ttk.Button(self.control_action_frame, text="⏹️ จบการทำงาน", command=self.end_processing, style='Red.TButton')
        self.btn_export = ttk.Button(self.control_action_frame, text="📥 Export ผลลัพธ์", command=self.export_to_excel, style='TButton')
        
        # --- กลุ่ม 4: เครื่องมือ (ขวา) ---
        utils_frame = ttk.LabelFrame(control_frame, text="เครื่องมือ")
        utils_frame.pack(side=tk.RIGHT, padx=0, fill=tk.Y)

        self.btn_help = ttk.Button(utils_frame, text="📖 คู่มือใช้งาน", command=self.show_help_window)
        self.btn_help.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_game = ttk.Button(utils_frame, text="🐍 เกมงู", command=self.open_snake_game)
        self.btn_game.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_restart = ttk.Button(utils_frame, text="🔄 รีสตาร์ท", command=self.restart_program, style='Gray.TButton')
        self.btn_restart.pack(side=tk.LEFT, padx=5, pady=5)
        
        # --- Progress Bar ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        self.progress_text = tk.StringVar()
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_text, anchor='e')
        self.progress_label.pack(side=tk.RIGHT, padx=(5, 0))
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # =====================================================================
        # ส่วนที่หายไปและได้เพิ่มกลับเข้ามา
        # =====================================================================
        # --- ตาราง Treeview ---
        tree_frame = ttk.LabelFrame(main_frame, text="ข้อมูลจาก Excel")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
        self.tree = ttk.Treeview(tree_frame, columns=('ID', 'Username', 'Password', 'NewPassword', 'Status'), show='headings')
        self.tree.heading('ID', text='ลำดับ'); self.tree.heading('Username', text='Username'); self.tree.heading('Password', text='Password (ปัจจุบัน)'); self.tree.heading('NewPassword', text='New Password'); self.tree.heading('Status', text='สถานะ')
        self.tree.column('ID', width=50, anchor=tk.CENTER); self.tree.column('Username', width=150); self.tree.column('Password', width=150); self.tree.column('NewPassword', width=150); self.tree.column('Status', width=150, anchor=tk.CENTER)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.tag_configure('success', background=self.SUCCESS_BG, foreground=self.TEXT_COLOR)
        self.tree.tag_configure('error', background=self.ERROR_BG, foreground=self.TEXT_COLOR)
        self.tree.tag_configure('default', background=self.FRAME_COLOR, foreground=self.TEXT_COLOR)

        # --- Log Text ---
        log_frame = ttk.LabelFrame(main_frame, text="Log")
        log_frame.pack(fill=tk.X, pady=5, padx=10)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD, state='disabled', font=self.default_font, bg=self.FRAME_COLOR, fg=self.TEXT_COLOR, insertbackground='white', relief='flat')
        self.log_text.pack(fill=tk.BOTH, expand=True)
        # =====================================================================

        self._update_ui_for_state('idle')
        
    def open_snake_game(self):
        game_window = tk.Toplevel(self.root)
        game_app = SnakeGame(game_window)
        game_window.transient(self.root)
        game_window.grab_set()
        self.root.wait_window(game_window)

    def show_help_window(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("คู่มือการใช้งานโปรแกรม")
        help_win.geometry("800x650")
        help_win.resizable(False, False)
        help_win.configure(bg=self.BG_COLOR)
        try:
            help_win.iconbitmap("img/icon.ico")
        except tk.TclError: pass
        text_area = scrolledtext.ScrolledText(help_win, wrap=tk.WORD, font=("Kanit", 11), padx=10, pady=10, bg=self.FRAME_COLOR, fg=self.TEXT_COLOR, relief='flat')
        text_area.pack(expand=True, fill=tk.BOTH)
        header_font = font.Font(family="Kanit", size=14, weight="bold")
        sub_header_font = font.Font(family="Kanit", size=12, weight="bold")
        bold_font = font.Font(family="Kanit", size=11, weight="bold")
        note_font = font.Font(family="Kanit", size=10, slant="italic")
        text_area.tag_configure("header", font=header_font, spacing3=10, justify='center')
        text_area.tag_configure("subheader", font=sub_header_font, spacing3=8, spacing1=10)
        text_area.tag_configure("bold", font=bold_font)
        text_area.tag_configure("bullet", lmargin1=20, lmargin2=20, spacing1=5)
        text_area.tag_configure("note", font=note_font, lmargin1=25, lmargin2=25, spacing1=5, foreground="#b0b0b0")
        text_area.tag_configure("warning", foreground="#ff6b6b", lmargin1=20, lmargin2=20, spacing1=5, font=bold_font)
        help_content = [("คู่มือการใช้งานโปรแกรม Auto Login & Password Changer\n", "header"),("1. การเตรียมไฟล์ Excel (.xlsx)\n", "subheader"),("โปรแกรมต้องการไฟล์ Excel ที่มีคอลัมน์ตามโครงสร้างที่กำหนดไว้เท่านั้น\n", "bullet"),("คอลัมน์ที่ต้องมีในไฟล์ Excel ของคุณ:\n", "bullet"),("   • ", "bullet"), ("username", "bold"), (": ชื่อผู้ใช้สำหรับล็อกอิน\n", "bullet"),("   • ", "bullet"), ("password", "bold"), (": รหัสผ่านปัจจุบันสำหรับล็อกอิน\n", "bullet"),("   • ", "bullet"), ("new password", "bold"), (": รหัสผ่านใหม่ (หากไม่ต้องการเปลี่ยน ให้เว้นว่างไว้)\n", "bullet"),("   • ", "bullet"), ("status", "bold"), (": สำหรับบันทึกผลลัพธ์ (ควรเว้นว่างไว้)\n", "bullet"),("\nหมายเหตุ:\n", "bold"),("คอลัมน์ 'ลำดับที่'", "note"), (" ที่เห็นในโปรแกรม ", "note"), ("จะถูกสร้างขึ้นอัตโนมัติ", "bold"), (" ไม่จำเป็นต้องมีในไฟล์ Excel ครับ\n", "note"),("\nตัวอย่างเทมเพลต Excel:\n", "bold"),("| username | password | new password | status |\n", None),("| user01   | pass123  | newpass_A    |        |\n", None),("| user02   | pass456  |              |        |\n", None),("2. ขั้นตอนการใช้งานโปรแกรม\n", "subheader"),("1. ", "bullet"), ("เปิดโปรแกรม", "bold"), (": ดับเบิลคลิกไฟล์โปรแกรม\n", "bullet"),("2. ", "bullet"), ("เลือกไฟล์ Excel", "bold"), (": กดปุ่ม 'เลือกไฟล์ Excel' และเลือกไฟล์ที่เตรียมไว้\n", "bullet"),("3. ", "bullet"), ("ตรวจสอบข้อมูล", "bold"), (": ข้อมูลจะปรากฏในตาราง\n", "bullet"),("4. ", "bullet"), ("เลือกเว็บไซต์", "bold"), (": เลือก Config ของเว็บที่ต้องการจากเมนู Dropdown\n", "bullet"),("5. ", "bullet"), ("เลือกโหมดการทำงาน", "bold"), (": ติ๊ก 'ทำงานเบื้องหลัง' (แนะนำ) เพื่อซ่อนหน้าต่างเบราว์เซอร์\n", "bullet"),("6. ", "bullet"), ("เริ่มทำงาน", "bold"), (": กดปุ่ม '▶ เริ่มทำงาน' เพื่อเริ่มกระบวนการ\n", "bullet"),("3. การตีความสถานะ (Status)\n", "subheader"),("• ", "bullet"), ("สำเร็จ", "bold"), (": ล็อกอินเข้าสู่ระบบได้ตามปกติ\n", "bullet"),("• ", "bullet"), ("เปลี่ยนรหัสผ่านสำเร็จ", "bold"), (": ล็อกอินแล้วเจอหน้าเปลี่ยนรหัส และเปลี่ยนสำเร็จ\n", "bullet"),("• ", "bullet"), ("ไม่มีรหัสผ่านใหม่", "bold"), (": เจอหน้าเปลี่ยนรหัส แต่ช่อง new password ว่าง\n", "bullet"),("• ", "bullet"), ("รหัสผ่านไม่ถูกต้อง", "bold"), (": ไม่สามารถล็อกอินได้\n", "bullet"),("• ", "bullet"), ("Error: ...", "bold"), (": เกิดข้อผิดพลาดทางเทคนิค โปรแกรมจะพยายามทำงานซ้ำ\n", "bullet"),("4. ข้อควรระวัง\n", "subheader"),("!!! ห้ามเปิดไฟล์ Excel ทิ้งไว้ !!!", "warning"),("\nขณะที่โปรแกรมกำลังทำงาน ", "bullet"), ("ต้องปิดไฟล์ Excel", "bold"), (" ที่ใช้งานอยู่เสมอ มิฉะนั้นโปรแกรมจะไม่สามารถบันทึกผลลัพธ์ได้\n", "bullet"),]
        for text, tag in help_content: text_area.insert(tk.END, text, tag)
        text_area.config(state="disabled")
        help_win.transient(self.root); help_win.grab_set(); self.root.wait_window(help_win)
        
# auto_login.py (แก้ไขในฟังก์ชัน _update_ui_for_state)

    def _update_ui_for_state(self, state):
        # ล้างปุ่มทั้งหมดในเฟรมควบคุมก่อน
        for widget in self.control_action_frame.winfo_children():
            widget.pack_forget()

        has_data = self.df is not None
        
        if state == 'idle':
            self.btn_start.pack(side=tk.LEFT, padx=5, pady=5)
            self.btn_start['state'] = 'normal' if has_data else 'disabled'
            self.btn_load['state'] = 'normal'
            self.btn_clear['state'] = 'normal' if has_data else 'disabled'
        elif state == 'running' or state == 'paused':
            if state == 'running':
                self.btn_pause.pack(side=tk.LEFT, padx=5, pady=5)
            if state == 'paused':
                self.btn_resume.pack(side=tk.LEFT, padx=5, pady=5)
            self.btn_end.pack(side=tk.LEFT, padx=5, pady=5)
            self.btn_load['state'] = 'disabled'
            self.btn_clear['state'] = 'disabled'
        elif state == 'finished':
            self.btn_start.pack(side=tk.LEFT, padx=5, pady=5)
            self.btn_export.pack(side=tk.LEFT, padx=5, pady=5)
            self.btn_start['state'] = 'normal' if has_data else 'disabled'
            self.btn_clear['state'] = 'normal'
            self.btn_export['state'] = 'normal' if has_data else 'disabled'
            self.btn_load['state'] = 'normal'
    
    def log(self, message):
        def append_message():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
            self.log_text.config(state='disabled'); self.log_text.see(tk.END)
        self.root.after(0, append_message)

    def on_website_select(self, event=None):
        global CURRENT_CONFIG
        selected_website = self.website_var.get()
        CURRENT_CONFIG = WEBSITE_CONFIGS.get(selected_website, {})
        self.log(f"โหลดการตั้งค่าสำหรับ: {selected_website}")
        
# auto_login.py (ส่วนของฟังก์ชัน clear_data ที่ปรับปรุงให้รีเซ็ตค่าทั้งหมด)

    def clear_data(self):
        if self.df is not None and messagebox.askyesno("ยืนยัน", "คุณต้องการล้างข้อมูลและรีเซ็ตสถานะทั้งหมดใช่หรือไม่?"):
            self.log("...กำลังล้างข้อมูลและรีเซ็ตโปรแกรม...")
            
            # 1. ล้างข้อมูลในตาราง Treeview
            self.tree.delete(*self.tree.get_children())
            
            # 2. รีเซ็ตค่าตัวแปรหลัก
            self.df = None
            self.excel_path = ""
            self.current_index = 0
            self.processed_count = 0
            self.retry_counts.clear()
            self.error_during_run = False
            self.user_stopped = False

            # 3. รีเซ็ต Progress Bar และข้อความ
            self.update_progress(0, 0)
            
            # 4. อัปเดตสถานะของปุ่มต่างๆ
            self._update_ui_for_state('idle')
            
            self.log("ข้อมูลถูกล้างเรียบร้อยแล้ว, โปรแกรมพร้อมสำหรับข้อมูลชุดใหม่")
    
# auto_login.py (ส่วนของฟังก์ชัน load_excel_file ที่ปรับปรุงใหม่)

    def load_excel_file(self):
        path = filedialog.askopenfilename(title="เลือกไฟล์ Excel", filetypes=(("Excel Files", "*.xlsx"),))
        if not path: return
        try:
            self.excel_path = path
            self.df = pd.read_excel(self.excel_path)
            self.df.columns = [c.lower() for c in self.df.columns]
            required = {'username', 'password'}
            if not required.issubset(self.df.columns):
                messagebox.showerror("ผิดพลาด", f"ไม่พบคอลัมน์ที่จำเป็น: {required - set(self.df.columns)}")
                return

            if 'new password' not in self.df.columns:
                self.df['new password'] = ''

            # =====================================================================
            # ส่วนที่ปรับปรุง: ตั้งค่าคอลัมน์ status เป็น "รอดำเนินการ" ทั้งหมด
            # =====================================================================
            self.log("...กำลังรีเซ็ตสถานะทั้งหมดเป็น 'รอดำเนินการ'")
            self.df['status'] = STATUS_PENDING # STATUS_PENDING คือ "รอดำเนินการ"
            # =====================================================================
            
            self.update_treeview()
            self._update_ui_for_state('idle')
            self.log(f"โหลดไฟล์ '{os.path.basename(self.excel_path)}' สำเร็จ ({len(self.df)} รายการ)")
            self.update_progress(0, len(self.df))
        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถโหลดไฟล์ Excel ได้:\n{e}")

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        for i, row in self.df.iterrows():
            values = (i + 1, row['username'], row['password'], row.get('new password', ''), row.get('status', ''))
            self.tree.insert("", 'end', iid=str(i), values=values, tags=('default',))

    def start_processing(self):
        if self.df is None: messagebox.showwarning("คำเตือน", "กรุณาโหลดไฟล์ Excel ก่อน"); return
        if not all(CURRENT_CONFIG.get(key) for key in ["url", "user_locator", "pass_locator", "login_locator"]):
            messagebox.showwarning("คำเตือน", f"การตั้งค่าสำหรับเว็บ '{self.website_var.get()}' ยังไม่สมบูรณ์"); return
        # =====================================================================
        # ส่วนที่ปรับปรุง: ตรวจสอบและติดตั้ง Driver ตามเบราว์เซอร์ที่เลือก
        # =====================================================================
        selected_browser = self.browser_var.get()
        
        # ตรวจสอบว่าต้องติดตั้ง Driver ใหม่หรือไม่ (ถ้ายังไม่เคยติดตั้ง หรือมีการเปลี่ยนเบราว์เซอร์)
        if not self.driver_path or self.driver_path_browser != selected_browser:
            try:
                if selected_browser == "Chrome":
                    self.log(f"...กำลังติดตั้ง/ตรวจสอบไดรเวอร์สำหรับ {selected_browser}...")
                    self.driver_path = ChromeDriverManager().install()
                else: # ค่าเริ่มต้นคือ Firefox
                    self.log(f"...กำลังติดตั้ง/ตรวจสอบไดรเวอร์สำหรับ {selected_browser}...")
                    self.driver_path = GeckoDriverManager().install()
                
                self.driver_path_browser = selected_browser # บันทึกว่า path นี้เป็นของเบราว์เซอร์อะไร
            except Exception as e:
                messagebox.showerror("ผิดพลาด", f"ไม่สามารถติดตั้งไดรเวอร์สำหรับ {selected_browser} ได้: {e}"); return
        # =====================================================================
        
        self.progress['maximum'] = len(self.df)
        self.update_progress(0)
        
        self.retry_counts.clear(); self.stop_event.clear(); self.pause_event.set()
        self._update_ui_for_state('running'); self.start_time = time.monotonic()
        self.worker_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.worker_thread.start()
        self.log(f"เริ่มต้นกระบวนการสำหรับเว็บ {self.website_var.get()}...")
        
    def update_progress(self, value, maximum=None):
        if maximum is not None: self.progress['maximum'] = maximum
        self.progress['value'] = value
        max_val = self.progress['maximum']
        if max_val > 0:
            percent = (value / max_val) * 100
            self.progress_text.set(f"{value} / {max_val} ({percent:.0f}%)")
        else:
            self.progress_text.set("0 / 0 (0%)")
        self.root.update_idletasks()

    def pause_processing(self): self.pause_event.clear(); self._update_ui_for_state('paused'); self.log("...หยุดการทำงานชั่วคราว...")
    def resume_processing(self): self._update_ui_for_state('running'); self.log("...ทำงานต่อ..."); self.pause_event.set()
    def end_processing(self): self.user_stopped = True; self.stop_event.set(); self.pause_event.set(); self.log("...กำลังจบการทำงาน...")
    def restart_program(self):
        if messagebox.askyesno("ยืนยันการรีสตาร์ท", "คุณต้องการรีสตาร์ทโปรแกรมหรือไม่?"):
            self.stop_event.set(); self.pause_event.set(); time.sleep(0.1)
            self._quit_driver(self.active_driver)
            os.execl(sys.executable, sys.executable, *sys.argv)

    def update_status_and_save(self, status):
        if self.current_index < len(self.df):
            self.df.at[self.current_index, 'status'] = status
            tag_to_use = 'default'
            if any(s in status for s in ['สำเร็จ', 'Changed']): tag_to_use = 'success'
            elif any(s in status for s in ['Error', 'ไม่ถูกต้อง', 'จำกัด']): tag_to_use = 'error'
            def update_ui():
                self.tree.set(str(self.current_index), 'Status', status)
                self.tree.item(str(self.current_index), tags=(tag_to_use,))
            self.root.after(0, update_ui)
            try:
                self.df.to_excel(self.excel_path, index=False)
            except Exception as e: self.log(f"บันทึก Excel ไม่สำเร็จ: {e}")

    def export_to_excel(self):
        if self.df is None: return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if path:
            try:
                self.df.to_excel(path, index=False)
                messagebox.showinfo("สำเร็จ", f"บันทึกผลลัพธ์ไปยังไฟล์\n{path}\nเรียบร้อยแล้ว")
            except Exception as e: messagebox.showerror("ผิดพลาด", f"ไม่สามารถบันทึกไฟล์ได้:\n{e}")

# auto_login.py (แก้ไขในฟังก์ชัน _create_driver ทั้งหมด)

    def _create_driver(self, headless=True):
        selected_browser = self.browser_var.get()
        self.log(f"กำลังสร้างเบราว์เซอร์: {selected_browser} (Headless: {headless})")
        
        try:
            # --- กรณีเลือก Chrome ---
            if selected_browser == "Chrome":
                options = webdriver.ChromeOptions()
                if headless: 
                    options.add_argument("--headless")
                    options.add_argument("--disable-gpu") # แนะนำให้ใส่สำหรับ Chrome headless
                service = ChromeService(executable_path=self.driver_path)
                return webdriver.Chrome(service=service, options=options)
            
            # --- กรณีเลือก Firefox (เป็นค่าเริ่มต้น) ---
            else:
                options = webdriver.FirefoxOptions()
                if headless: 
                    options.add_argument("--headless")
                    options.set_preference("permissions.default.image", 2)
                    options.set_preference("dom.stylesheet.css.enabled", False)
                service = FirefoxService(executable_path=self.driver_path)
                return webdriver.Firefox(service=service, options=options)

        except Exception as e:
            self.log(f"!!! ไม่สามารถสร้างเบราว์เซอร์ {selected_browser} ได้: {e}"); self.error_during_run = True; self.stop_event.set(); return None

    def _quit_driver(self, driver):
        if driver:
            try: driver.quit()
            except Exception as e: self.log(f"เกิดข้อผิดพลาดขณะปิดเบราว์เซอร์: {e}")

    def _human_type(self, element, text):
        for char in str(text):
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

    def _processing_loop(self):
        self.current_driver_is_headless = self.headless_var.get()
        driver = self._create_driver(headless=self.current_driver_is_headless)
        if not driver: self.root.after(0, self.on_processing_finished); return
        try:
            while self.current_index < len(self.df):
                self.pause_event.wait()
                if self.stop_event.is_set(): break
                should_restart = (self.force_driver_restart or (self.headless_var.get() != self.current_driver_is_headless) or (self.processed_count > 0 and self.processed_count % RESTART_DRIVER_INTERVAL == 0))
                if should_restart:
                    self.log("...กำลังรีสตาร์ทเบราว์เซอร์...")
                    self._quit_driver(driver)
                    self.current_driver_is_headless = self.headless_var.get()
                    driver = self._create_driver(headless=self.current_driver_is_headless)
                    if not driver: break
                    self.force_driver_restart = False
                retries = self.retry_counts.get(self.current_index, 0)
                if retries >= MAX_RETRIES:
                    self.update_status_and_save(STATUS_RETRY_FAILED)
                else:
                    status, needs_retry = self._process_single_row(driver)
                    if needs_retry:
                        self.log(f"เกิดปัญหา, กำลังลองใหม่ (ครั้งที่ {retries + 1})...")
                        self.retry_counts[self.current_index] = retries + 1
                        self.force_driver_restart = True
                        self.root.after(0, self.update_progress, self.processed_count)
                        continue
                    self.update_status_and_save(status)
                
                self.processed_count += 1
                self.current_index += 1
                self.retry_counts.pop(self.current_index, None)
                self.root.after(0, self.update_progress, self.processed_count)

        except Exception as e:
            self.log(f"!!! เกิดข้อผิดพลาดร้ายแรงใน Loop หลัก: {e}"); self.error_during_run = True
        finally:
            self._quit_driver(driver)
            self.root.after(0, self.on_processing_finished)

    def _process_single_row(self, driver):
        row = self.df.iloc[self.current_index]
        username, password = str(row['username']), str(row['password'])
        self.log(f"[{self.processed_count + 1}/{len(self.df)}] เริ่ม: {username}")
        self.root.after(0, self.tree.see, str(self.current_index))
        try:
            self.log("...กำลังล้าง Cookies")
            driver.delete_all_cookies()
            self.log(f"...กำลังเปิด URL: {CURRENT_CONFIG['url']}")
            driver.get(CURRENT_CONFIG["url"])
            wait = WebDriverWait(driver, 15)
            self.log("...กำลังกรอก Username")
            user_field = wait.until(EC.visibility_of_element_located(CURRENT_CONFIG["user_locator"]))
            self._human_type(user_field, username)
            self.log("...กำลังกรอก Password")
            pass_field = driver.find_element(*CURRENT_CONFIG["pass_locator"])
            self._human_type(pass_field, password)
            self.log("...กำลังกดปุ่ม Login")
            driver.find_element(*CURRENT_CONFIG["login_locator"]).click()
            self.log("...ตรวจสอบสถานะหลัง Login")
            return self._check_login_status(driver)
        except WebDriverException as e: return f"Error: {type(e).__name__}", True
        except Exception as e: return f"Error: {type(e).__name__}", False

# auto_login.py

    def _check_login_status(self, driver):
        wait = WebDriverWait(driver, 15)
        time.sleep(2) # หน่วงเวลาสั้นๆ หลังกด Login

        self.log("...กำลังตรวจสอบ Alert Box")
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return (STATUS_ACCESS_DENIED if "จำกัด" in alert_text else f"Alert: {alert_text}"), False
        except NoAlertPresentException:
            pass

        self.log("...กำลังตรวจสอบข้อความ Error ในหน้าเว็บ")
        if any(msg in driver.page_source for msg in ["not valid", "ไม่ถูกต้อง", "Invalid"]):
             return STATUS_INVALID_PASSWORD, False
        
        # =====================================================================
        # ส่วนที่ปรับปรุง: ตรวจสอบ URL ก่อน แล้วค่อยจัดการเงื่อนไขภายใน
        # =====================================================================
        self.log("...กำลังตรวจสอบ URL ของหน้าปัจจุบัน")
        change_pass_url = CURRENT_CONFIG.get("change_pass_url")

        # 1. ตรวจสอบว่าเข้ามาใน URL สำหรับเปลี่ยนรหัสผ่านหรือไม่
        if change_pass_url and driver.current_url.startswith(change_pass_url):
            self.log(f"!!! ตรวจพบ URL หน้าเปลี่ยนรหัสผ่าน: {driver.current_url}")

            # 2. (ขั้นตอนเสริม) หน่วงเวลารอตรวจสอบปุ่มยอมรับ (ไทย หรือ อังกฤษ)
            self.log("...หน่วงเวลารอตรวจสอบปุ่มยอมรับ (TH/EN) (รอสูงสุด 7 วินาที)")
            try:
                # ใช้ WebDriverWait รอไม่นาน เพื่อหาปุ่ม T&C
                wait_short = WebDriverWait(driver, 7)
                
                # *** บรรทัดที่แก้ไข ***
                agree_button_xpath = "//*[@id='submitBtn' and (contains(text(),'ข้าพเจ้าตกลง') or contains(text(),'I agree'))]"
                
                agree_button = wait_short.until(EC.element_to_be_clickable((By.XPATH, agree_button_xpath)))

                self.log("!!! พบปุ่มยอมรับข้อตกลง -> ทำการกดปุ่ม")
                agree_button.click()
                self.log("...กดปุ่มยอมรับข้อตกลงสำเร็จ")

            except TimeoutException:
                # ถ้าไม่เจอปุ่มในเวลาที่กำหนด ก็ไม่เป็นไร แสดงว่าไม่มีหน้านี้
                self.log("...ไม่พบปุ่มยอมรับข้อตกลง, ดำเนินการต่อ")
                pass
            except Exception as e:
                self.log(f"!!! เกิดปัญหาตอนรอปุ่มยอมรับข้อตกลง: {e}")
                pass

            # 3. ไม่ว่าจะเจอ T&C หรือไม่ ให้เรียกฟังก์ชันสำหรับเปลี่ยนรหัสผ่านได้เลย
            self.log(f"...เริ่มต้นกระบวนการเปลี่ยนรหัสผ่านสำหรับ {self.df.iloc[self.current_index]['username']}")
            return self._handle_password_change(driver, wait)
        
        # =====================================================================
        # สิ้นสุดส่วนที่ปรับปรุง
        # =====================================================================

        self.log("...กำลังตรวจสอบว่าเข้าสู่หน้าเว็บหลักสำเร็จหรือไม่")
        try:
            wait.until(EC.visibility_of_element_located(CURRENT_CONFIG["login_success_indicator_locator"]))
            return STATUS_SUCCESS, False
        except TimeoutException:
            return "Error: Login Timeout", True

# auto_login.py (ส่วนของฟังก์ชัน _handle_password_change ที่ปรับปรุงให้เสถียรขึ้นสำหรับ Firefox)

    def _handle_password_change(self, driver, wait):
        row = self.df.iloc[self.current_index]
        old_pass, new_pass = str(row['password']), str(row['new password'])
        if pd.isna(new_pass) or not new_pass.strip():
            return STATUS_MISSING_NEW_PASS, False
        try:
            # =====================================================================
            # ส่วนที่ปรับปรุงใหม่: เพิ่มขั้นตอนการรอที่แน่นอนและเสถียรขึ้น
            # =====================================================================
            self.log("...กำลังรอให้ช่องกรอกรหัสผ่านเก่าปรากฏ (วิธีใหม่สำหรับ Firefox)...")
            old_pass_locator = CURRENT_CONFIG["old_pass_locator"]
            
            # 1. รอจนกว่า element จะ "มีอยู่" ในโค้ดของหน้าเว็บ (ไม่ต้องมองเห็นก็ได้)
            old_pass_field = wait.until(EC.presence_of_element_located(old_pass_locator))

            # 2. ใช้ JavaScript เพื่อ "เลื่อนหน้าจอ" ไปยังตำแหน่งของช่องกรอกรหัส
            self.log("...กำลังเลื่อนหน้าจอไปยังช่องกรอกรหัส...")
            driver.execute_script("arguments[0].scrollIntoView(true);", old_pass_field)
            
            # 3. รออีกครั้งเพื่อให้แน่ใจว่าช่องนั้น "พร้อมให้คลิก/กรอกข้อมูลได้"
            wait.until(EC.element_to_be_clickable(old_pass_locator))
            
            # 4. หน่วงเวลาสั้นๆ 1 วินาที เพื่อให้หน้าเว็บนิ่งสนิทจริงๆ
            time.sleep(1)
            # =====================================================================
            # สิ้นสุดส่วนที่ปรับปรุง
            # =====================================================================

            self.log("...กำลังกรอกรหัสผ่านปัจจุบัน")
            self._human_type(old_pass_field, old_pass)
            
            self.log("...กำลังกรอกรหัสผ่านใหม่")
            new_pass_field = driver.find_element(*CURRENT_CONFIG["new_pass_locator"])
            self._human_type(new_pass_field, new_pass)
            
            self.log("...กำลังยืนยันรหัสผ่านใหม่")
            confirm_pass_field = driver.find_element(*CURRENT_CONFIG["confirm_pass_locator"])
            self._human_type(confirm_pass_field, new_pass)

            self.log("...หน่วงเวลารอให้ปุ่ม 'ยืนยัน' พร้อมสำหรับการคลิก...")
            submit_locator = CURRENT_CONFIG["submit_change_pass_locator"]
            submit_button = wait.until(EC.element_to_be_clickable(submit_locator))
            time.sleep(1)

            self.log("...กำลังกดยืนยันการเปลี่ยนรหัสผ่าน (ใช้วิธีที่เสถียรขึ้น)")
            try:
                submit_button.click()
            except ElementClickInterceptedException:
                self.log("!!! คลิกปกติถูกขัดจังหวะ -> ลองใหม่โดยใช้ JavaScript")
                driver.execute_script("arguments[0].click();", submit_button)

            self.log("...รอ Pop-up ยืนยันการเปลี่ยนรหัสผ่าน...")
            popup_locator = CURRENT_CONFIG.get("change_pass_popup_button_locator")
            if popup_locator:
                popup_button = wait.until(EC.element_to_be_clickable(popup_locator))
                popup_button.click()
                self.log("...กดปุ่ม 'ทำรายการต่อ' ใน Pop-up สำเร็จ...")
            
            return STATUS_PASSWORD_CHANGED, False
        except TimeoutException:
            return "Error: Change Pass Timeout", True
        except Exception as e:
            return f"Error: Change Pass Fail ({type(e).__name__})", False

# auto_login.py (แก้ไขฟังก์ชัน on_processing_finished ทั้งหมด)

    def on_processing_finished(self):
        duration = time.monotonic() - self.start_time
        
        # =====================================================================
        # ส่วนที่ปรับปรุง: สร้างสรุปผลการทำงานแบบละเอียด
        # =====================================================================
        summary = ""
        if self.df is not None and self.processed_count > 0:
            # เตรียมตัวแปรสำหรับนับและเก็บข้อมูล
            success_items = []
            failed_items = {}  # เก็บ {username: status}
            error_items = {}   # เก็บ {username: status}
            
            # คำที่ใช้ระบุสถานะ "สำเร็จ"
            SUCCESS_KEYWORDS = [STATUS_SUCCESS, STATUS_PASSWORD_CHANGED]

            # วนลูปในข้อมูลที่ประมวลผลไปแล้วเพื่อเก็บรายละเอียด
            for index, row in self.df.iloc[:self.processed_count].iterrows():
                status = str(row.get('status', ''))
                username = str(row.get('username', ''))

                if any(s in status for s in SUCCESS_KEYWORDS):
                    success_items.append(username)
                elif status.startswith("Error"):
                    error_items[username] = status
                else: # ที่เหลือคือ "ไม่สำเร็จ"
                    failed_items[username] = status
            
            # สร้างข้อความสรุป
            total_items = len(self.df)
            processed_str = f"ประมวลผล: {self.processed_count} / {total_items} รายการ"
            time_str = f"ใช้เวลาทั้งหมด: {time.strftime('%M นาที %S วินาที', time.gmtime(duration))}"
            
            # ส่วนของ "สำเร็จ"
            success_str = f"✅ สำเร็จ: {len(success_items)} รายการ"

            # ส่วนของ "ไม่สำเร็จ"
            failed_str = f"❌ ไม่สำเร็จ: {len(failed_items)} รายการ"
            if failed_items:
                failed_details = "\n".join([f"  - {user}: {reason}" for user, reason in failed_items.items()])
                failed_str += f"\n{failed_details}"

            # ส่วนของ "Error"
            error_str = f"❗ Error: {len(error_items)} รายการ"
            if error_items:
                error_details = "\n".join([f"  - {user}: {reason}" for user, reason in error_items.items()])
                error_str += f"\n{error_details}"

            summary = (
                f"{processed_str}\n"
                f"{time_str}\n\n"
                f"--- สรุปผล ---\n"
                f"{success_str}\n\n"
                f"{failed_str}\n\n"
                f"{error_str}"
            )
        else:
            summary = (
                f"ประมวลผล: 0 รายการ\n"
                f"ใช้เวลาทั้งหมด: {time.strftime('%M นาที %S วินาที', time.gmtime(duration))}"
            )
        # =====================================================================
        # สิ้นสุดส่วนที่ปรับปรุง
        # =====================================================================

        if self.user_stopped:
            msg = "จบการทำงานตามคำสั่งผู้ใช้"
            title = "จบการทำงาน"
            messagebox.showinfo(title, f"{msg}\n\n{summary}")
        elif self.error_during_run and not self.user_stopped:
            msg = "หยุดทำงานเนื่องจากข้อผิดพลาดร้ายแรง"
            title = "เกิดข้อผิดพลาด"
            messagebox.showerror(title, f"{msg}\n\n{summary}")
        else:
            msg = "กระบวนการทั้งหมดเสร็จสิ้น"
            title = "เสร็จสิ้นสมบูรณ์"
            messagebox.showinfo(title, f"ความไวเป็นของปีศาจ 😈\n\n{msg}\n\n{summary}")
            
        self._update_ui_for_state('finished')
            
if __name__ == "__main__":
    app_root = tk.Tk()
    app = AutoLoginApp(app_root)
    app_root.mainloop()