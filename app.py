import os
import sys
import json
import urllib.request
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from PIL import Image, ImageTk
import psycopg2

# ==========================================
#  ตั้งค่า SUPABASE CLOUD (แก้ไขเป็นค่า Pooler)
# ==========================================
DB_HOST = "aws-0-ap-south-1.pooler.supabase.com"      # 🟢 แก้ไขตรงนี้ (เปลี่ยนจาก db... เป็น pooler)
DB_NAME = "postgres"
DB_USER = "postgres.kilcjpzlbiddeqludncp"             # 🟢 แก้ไขตรงนี้ (เพิ่ม .kilcjpzlbiddeqludncp ต่อท้าย postgres)
DB_PASS = "0934522462spk"
DB_PORT = "6543"

class CarBookingApp:
    def __init__(self, root):
        self.root = root
        # ... (โค้ดสร้าง GUI เดิมของคุณ) ...

        # 🟢 เพิ่มการสั่งเช็กอัปเดตหลังเปิดโปรแกรมขึ้นมา 1 วินาที
        self.root.after(1000, self.check_for_updates)

        # Palette สี Modern Dashboard
        self.COLOR_BG = "#F8FAFC"
        self.COLOR_SURFACE = "#FFFFFF"
        self.COLOR_TEXT = "#0F172A"
        self.COLOR_TEXT_MUTED = "#64748B"
        self.COLOR_PRIMARY = "#2563EB"
        self.COLOR_SUCCESS = "#10B981"
        self.COLOR_WARNING = "#F59E0B"
        self.COLOR_DANGER = "#EF4444"
        self.COLOR_BORDER = "#E2E8F0"

        self.root.configure(bg=self.COLOR_BG)

        self.set_app_icon()
        
        # เชื่อมต่อ Database และสร้างตาราง
        try:
            self.init_db()
        except Exception as e:
            messagebox.showerror("เชื่อมต่อออนไลน์ล้มเหลว", f"ไม่สามารถเชื่อมต่อฐานข้อมูล Supabase ได้:\n{e}")

        self.setup_styles()
        self.create_header()
        self.create_dashboard()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tab_booking = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_in_use = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_available = ttk.Frame(self.notebook, style="Card.TFrame")
        self.tab_manage = ttk.Frame(self.notebook, style="Card.TFrame")

        self.notebook.add(self.tab_booking, text=" 📝 เบิก-คืนรถ ")
        self.notebook.add(self.tab_in_use, text=" 🔴 รถที่ถูกเบิกอยู่ ")
        self.notebook.add(self.tab_available, text=" 🟢 รถพร้อมใช้งาน ")
        self.notebook.add(self.tab_manage, text=" ⚙️ จัดการยานพาหนะ ")

        self.create_booking_tab()
        self.create_in_use_tab()
        self.create_available_tab()
        self.create_manage_tab()

        self.refresh_all_data()

        # เรียกเช็กอัปเดตออนไลน์หลังจากเปิดโปรแกรม 1.5 วินาที
        self.root.after(1500, self.check_for_updates)

    def check_for_updates(self):
        try:
            req = urllib.request.Request(UPDATE_CHECK_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("version")
                download_url = data.get("download_url")
                changelog = data.get("changelog", "")

            if latest_version and latest_version > CURRENT_VERSION:
                confirm = messagebox.askyesno(
                    "พบอัปเดตใหม่เวอร์ชัน " + latest_version,
                    f"ระบบมีเวอร์ชันใหม่พร้อมใช้งาน!\nเวอร์ชันปัจจุบัน: {CURRENT_VERSION}\nเวอร์ชันใหม่: {latest_version}\n\nรายการปรับปรุง:\n{changelog}\n\nคุณต้องการอัปเดตโปรแกรมตอนนี้เลยหรือไม่?"
                )
                if confirm:
                    self.apply_update(download_url)
        except Exception:
            pass  # ข้ามเงียบๆ หากไม่มีเน็ตหรือไฟล์ไม่พบ

    def apply_update(self, download_url):
        try:
            current_exe = sys.executable
            temp_exe = os.path.join(os.environ["TEMP"], "carbooking_new.exe")
            bat_script = os.path.join(os.environ["TEMP"], "update_installer.bat")

            messagebox.showinfo("กำลังดาวน์โหลด", "กำลังดาวน์โหลดไฟล์อัปเดตใหม่ กรุณารอสักครู่...")
            urllib.request.urlretrieve(download_url, temp_exe)

            bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
copy /y "{temp_exe}" "{current_exe}"
del "{temp_exe}"
start "" "{current_exe}"
del "%~f0"
"""
            with open(bat_script, "w", encoding="utf-8") as f:
                f.write(bat_content)

            subprocess.Popen([bat_script], shell=True)
            self.root.destroy()
            sys.exit()
        except Exception as e:
            messagebox.showerror("อัปเดตล้มเหลว", f"เกิดข้อผิดพลาดในการติดตั้งอัปเดต: {e}")

    def get_db_connection(self):
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )

    def get_base_dir(self):
        if getattr(sys, 'frozen', False):
            return sys._MEIPASS
        return os.path.dirname(os.path.abspath(__file__))

    def set_app_icon(self):
        try:
            base_dir = self.get_base_dir()
            icon_path = os.path.join(base_dir, "logo.ico")

            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            elif os.path.exists("logo.ico"):
                self.root.iconbitmap("logo.ico")
        except Exception:
            pass

    def init_db(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id SERIAL PRIMARY KEY,
            plate_number VARCHAR(50) UNIQUE NOT NULL,
            model VARCHAR(100) NOT NULL,
            vehicle_type VARCHAR(50) DEFAULT 'รถยนต์',
            status VARCHAR(50) DEFAULT 'AVAILABLE'
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            vehicle_id INTEGER NOT NULL,
            borrower_name VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            borrow_date VARCHAR(100) NOT NULL,
            status VARCHAR(50) DEFAULT 'ACTIVE'
        )
        """)

        cursor.execute("SELECT COUNT(*) FROM vehicles")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO vehicles (plate_number, model, vehicle_type) VALUES (%s, %s, %s)",
                [
                    ("กข-1234", "Toyota Camry", "รถยนต์"),
                    ("ขก-5678", "Isuzu D-Max", "รถยนต์"),
                    ("คง-9999", "Honda Wave 110i", "รถจักรยานยนต์")
                ]
            )
        conn.commit()
        cursor.close()
        conn.close()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        font_family = "Tahoma"

        style.configure("Main.TFrame", background=self.COLOR_BG)
        style.configure("Card.TFrame", background=self.COLOR_SURFACE, relief="flat")
        style.configure("Header.TFrame", background=self.COLOR_PRIMARY)

        style.configure("HeaderTitle.TLabel", background=self.COLOR_PRIMARY, foreground="#FFFFFF", font=(font_family, 16, "bold"))
        style.configure("HeaderSub.TLabel", background=self.COLOR_PRIMARY, foreground="#93C5FD", font=(font_family, 9))
        
        style.configure("CardTitle.TLabel", background=self.COLOR_SURFACE, foreground=self.COLOR_TEXT_MUTED, font=(font_family, 10))
        style.configure("CardValue.TLabel", background=self.COLOR_SURFACE, font=(font_family, 18, "bold"))

        style.configure("FormLabel.TLabel", background=self.COLOR_SURFACE, foreground=self.COLOR_TEXT, font=(font_family, 10))
        style.configure("SectionTitle.TLabel", background=self.COLOR_SURFACE, foreground=self.COLOR_TEXT, font=(font_family, 12, "bold"))

        style.configure("TEntry", padding=6, relief="flat", fieldbackground="#F1F5F9", foreground=self.COLOR_TEXT)
        style.configure("TCombobox", padding=6, relief="flat", fieldbackground="#F1F5F9", foreground=self.COLOR_TEXT)

        style.configure("Primary.TButton", font=(font_family, 10, "bold"), background=self.COLOR_PRIMARY, foreground="#FFFFFF", borderwidth=0, padding=(12, 8))
        style.map("Primary.TButton", background=[("active", "#1D4ED8")])

        style.configure("Success.TButton", font=(font_family, 10, "bold"), background=self.COLOR_SUCCESS, foreground="#FFFFFF", borderwidth=0, padding=(12, 8))
        style.map("Success.TButton", background=[("active", "#059669")])

        style.configure("Warning.TButton", font=(font_family, 10, "bold"), background=self.COLOR_WARNING, foreground="#FFFFFF", borderwidth=0, padding=(12, 8))
        style.map("Warning.TButton", background=[("active", "#D97706")])

        style.configure("Danger.TButton", font=(font_family, 10, "bold"), background=self.COLOR_DANGER, foreground="#FFFFFF", borderwidth=0, padding=(12, 8))
        style.map("Danger.TButton", background=[("active", "#DC2626")])

        style.configure("TNotebook", background=self.COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=(font_family, 10), padding=(16, 10), background="#E2E8F0", foreground=self.COLOR_TEXT_MUTED, borderwidth=0)
        style.map("TNotebook.Tab", 
                  background=[("selected", self.COLOR_SURFACE)], 
                  foreground=[("selected", self.COLOR_PRIMARY)],
                  font=[("selected", (font_family, 10, "bold"))])

        style.configure("Treeview", 
                        background=self.COLOR_SURFACE, 
                        foreground=self.COLOR_TEXT, 
                        rowheight=32, 
                        fieldbackground=self.COLOR_SURFACE,
                        font=(font_family, 9),
                        borderwidth=0)
        style.configure("Treeview.Heading", 
                        background="#F1F5F9", 
                        foreground=self.COLOR_TEXT, 
                        font=(font_family, 10, "bold"),
                        relief="flat",
                        padding=6)
        style.map("Treeview", background=[("selected", "#EFF6FF")], foreground=[("selected", self.COLOR_PRIMARY)])

    def create_header(self):
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 12))
        header.pack(fill="x")

        base_dir = self.get_base_dir()
        search_dirs = [base_dir, os.getcwd()]
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.ico')
        
        img_path = None
        for d in search_dirs:
            if not os.path.exists(d):
                continue
            for f in os.listdir(d):
                if f.lower().startswith('logo_header') or (f.lower().startswith('logo') and not f.lower().endswith('.ico')):
                    if f.lower().endswith(valid_extensions):
                        img_path = os.path.join(d, f)
                        break
            if img_path:
                break

        if img_path and os.path.exists(img_path):
            try:
                raw_img = Image.open(img_path)
                raw_img = raw_img.resize((50, 50), Image.Resampling.LANCZOS)
                self.header_logo = ImageTk.PhotoImage(raw_img)
                lbl_img = tk.Label(header, image=self.header_logo, bg=self.COLOR_PRIMARY)
                lbl_img.pack(side="left", padx=(0, 12))
            except Exception:
                pass

        title_frame = ttk.Frame(header, style="Header.TFrame")
        title_frame.pack(side="left", anchor="w")

        ttk.Label(title_frame, text="ระบบบริหารจัดการรถราชการ สภ.นาข่า (Online)", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(title_frame, text="Na Kha Police Station - Official Vehicle Reservation & Fleet Management System", style="HeaderSub.TLabel").pack(anchor="w", pady=(2, 0))

    def create_dashboard(self):
        frame_dash = tk.Frame(self.root, bg=self.COLOR_BG)
        frame_dash.pack(fill="x", padx=20, pady=15)

        c1 = self.create_card(frame_dash, "รถทั้งหมดในระบบ", "0 คัน", self.COLOR_PRIMARY)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.lbl_total = c1.winfo_children()[1]

        c2 = self.create_card(frame_dash, "ถูกเบิกใช้งานอยู่", "0 คัน", self.COLOR_WARNING)
        c2.pack(side="left", fill="both", expand=True, padx=5)
        self.lbl_in_use = c2.winfo_children()[1]

        c3 = self.create_card(frame_dash, "คงเหลือพร้อมใช้งาน", "0 คัน", self.COLOR_SUCCESS)
        c3.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.lbl_avail = c3.winfo_children()[1]

    def create_card(self, parent, title, default_val, text_color):
        card = tk.Frame(parent, bg=self.COLOR_SURFACE, highlightbackground=self.COLOR_BORDER, highlightthickness=1, padx=20, pady=12)
        
        lbl_t = ttk.Label(card, text=title, style="CardTitle.TLabel")
        lbl_t.pack(anchor="w")

        lbl_v = tk.Label(card, text=default_val, font=("Tahoma", 18, "bold"), bg=self.COLOR_SURFACE, fg=text_color)
        lbl_v.pack(anchor="w", pady=(4, 0))

        return card

    def create_booking_tab(self):
        container = ttk.Frame(self.tab_booking, style="Card.TFrame", padding=25)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="ฟอร์มลงทะเบียนเบิกรถราชการ สภ.นาข่า", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        ttk.Label(container, text="เลือกรถที่ว่าง:", style="FormLabel.TLabel").grid(row=1, column=0, sticky="w", pady=10)
        self.combo_cars = ttk.Combobox(container, state="readonly", width=38)
        self.combo_cars.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=10)

        ttk.Label(container, text="ชื่อผู้เบิก:", style="FormLabel.TLabel").grid(row=2, column=0, sticky="w", pady=10)
        self.ent_borrower = ttk.Entry(container, width=40)
        self.ent_borrower.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=10)

        ttk.Label(container, text="หน่วยงาน / งาน / สายงาน:", style="FormLabel.TLabel").grid(row=3, column=0, sticky="w", pady=10)
        self.ent_dept = ttk.Entry(container, width=40)
        self.ent_dept.grid(row=3, column=1, sticky="w", padx=(10, 0), pady=10)

        ttk.Label(container, text="วันที่เบิก (กำหนดได้):", style="FormLabel.TLabel").grid(row=4, column=0, sticky="w", pady=10)
        self.ent_borrow_date = ttk.Entry(container, width=40)
        self.ent_borrow_date.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=10)
        self.ent_borrow_date.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        btn_borrow = ttk.Button(container, text="📌 บันทึกการเบิกรถ", style="Primary.TButton", command=self.borrow_car)
        btn_borrow.grid(row=5, column=1, sticky="e", padx=(10, 0), pady=(20, 0))

    def create_in_use_tab(self):
        container = ttk.Frame(self.tab_in_use, style="Card.TFrame", padding=15)
        container.pack(fill="both", expand=True)

        self.nb_in_use = ttk.Notebook(container)
        self.nb_in_use.pack(fill="both", expand=True)

        self.tab_car_in_use = ttk.Frame(self.nb_in_use, style="Card.TFrame")
        self.tab_moto_in_use = ttk.Frame(self.nb_in_use, style="Card.TFrame")
        self.nb_in_use.add(self.tab_car_in_use, text=" 🚗 รถยนต์ ")
        self.nb_in_use.add(self.tab_moto_in_use, text=" 🛵 รถจักรยานยนต์ ")

        cols_in_use = ("booking_id", "plate", "model", "borrower", "dept", "date")
        self.tree_car_booking = ttk.Treeview(self.tab_car_in_use, columns=cols_in_use, show="headings")
        self.setup_booking_treeview(self.tree_car_booking)

        self.tree_moto_booking = ttk.Treeview(self.tab_moto_in_use, columns=cols_in_use, show="headings")
        self.setup_booking_treeview(self.tree_moto_booking)

        frame_action = ttk.Frame(container, style="Card.TFrame")
        frame_action.pack(fill="x", pady=(10, 0))

        btn_edit_date = ttk.Button(frame_action, text="✏️ แก้ไขวันที่เบิก", style="Warning.TButton", command=self.edit_borrow_date)
        btn_edit_date.pack(side="left")

        btn_return = ttk.Button(frame_action, text="🔄 รับคืนรถคันที่เลือก", style="Success.TButton", command=self.return_car)
        btn_return.pack(side="right")

    def create_available_tab(self):
        container = ttk.Frame(self.tab_available, style="Card.TFrame", padding=15)
        container.pack(fill="both", expand=True)

        self.nb_avail = ttk.Notebook(container)
        self.nb_avail.pack(fill="both", expand=True)

        self.tab_car_avail = ttk.Frame(self.nb_avail, style="Card.TFrame")
        self.tab_moto_avail = ttk.Frame(self.nb_avail, style="Card.TFrame")
        self.nb_avail.add(self.tab_car_avail, text=" 🚗 รถยนต์ ")
        self.nb_avail.add(self.tab_moto_avail, text=" 🛵 รถจักรยานยนต์ ")

        cols_avail = ("plate", "model", "status")
        self.tree_car_avail = ttk.Treeview(self.tab_car_avail, columns=cols_avail, show="headings")
        self.setup_avail_treeview(self.tree_car_avail)

        self.tree_moto_avail = ttk.Treeview(self.tab_moto_avail, columns=cols_avail, show="headings")
        self.setup_avail_treeview(self.tree_moto_avail)

    def setup_booking_treeview(self, tree):
        tree.heading("booking_id", text="ID เบิก")
        tree.heading("plate", text="เลขทะเบียน")
        tree.heading("model", text="รุ่นรถ")
        tree.heading("borrower", text="ผู้เบิก")
        tree.heading("dept", text="หน่วยงาน/งาน/สายงาน")
        tree.heading("date", text="วัน-เวลาที่เบิก")

        tree.column("booking_id", width=70, anchor="center")
        tree.column("plate", width=130, anchor="center")
        tree.column("model", width=180)
        tree.column("borrower", width=180)
        tree.column("dept", width=160)
        tree.column("date", width=180, anchor="center")

        tree.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_avail_treeview(self, tree):
        tree.heading("plate", text="เลขทะเบียน")
        tree.heading("model", text="รุ่น / ยี่ห้อรถ")
        tree.heading("status", text="สถานะ")

        tree.column("plate", width=200, anchor="center")
        tree.column("model", width=400)
        tree.column("status", width=200, anchor="center")

        tree.pack(fill="both", expand=True, padx=5, pady=5)

    def create_manage_tab(self):
        container = ttk.Frame(self.tab_manage, style="Card.TFrame", padding=20)
        container.pack(fill="both", expand=True)

        frame_add = ttk.Frame(container, style="Card.TFrame")
        frame_add.pack(fill="x", pady=(0, 15))

        ttk.Label(frame_add, text="เพิ่ม / จัดการยานพาหนะ สภ.นาข่า", style="SectionTitle.TLabel").grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 10))

        ttk.Label(frame_add, text="ประเภท:", style="FormLabel.TLabel").grid(row=1, column=0, sticky="w")
        self.combo_type = ttk.Combobox(frame_add, values=["รถยนต์", "รถจักรยานยนต์"], state="readonly", width=14)
        self.combo_type.current(0)
        self.combo_type.grid(row=1, column=1, padx=(5, 12), sticky="w")

        ttk.Label(frame_add, text="เลขทะเบียน:", style="FormLabel.TLabel").grid(row=1, column=2, sticky="w")
        self.ent_new_plate = ttk.Entry(frame_add, width=16)
        self.ent_new_plate.grid(row=1, column=3, padx=(5, 12), sticky="w")

        ttk.Label(frame_add, text="รุ่น/ยี่ห้อรถ:", style="FormLabel.TLabel").grid(row=1, column=4, sticky="w")
        self.ent_new_model = ttk.Entry(frame_add, width=20)
        self.ent_new_model.grid(row=1, column=5, padx=(5, 12), sticky="w")

        btn_add_car = ttk.Button(frame_add, text="➕ เพิ่มรถ", style="Primary.TButton", command=self.add_car)
        btn_add_car.grid(row=1, column=6, padx=(5, 8))

        btn_delete_car = ttk.Button(frame_add, text="🗑 ลบรถที่เลือก", style="Danger.TButton", command=self.delete_car)
        btn_delete_car.grid(row=1, column=7, padx=(0, 5))

        frame_table = ttk.Frame(container, style="Card.TFrame")
        frame_table.pack(fill="both", expand=True, pady=(10, 0))

        columns = ("id", "type", "plate", "model", "status")
        self.tree_cars = ttk.Treeview(frame_table, columns=columns, show="headings")

        self.tree_cars.heading("id", text="ID")
        self.tree_cars.heading("type", text="ประเภท")
        self.tree_cars.heading("plate", text="เลขทะเบียน")
        self.tree_cars.heading("model", text="รุ่นรถ")
        self.tree_cars.heading("status", text="สถานะ")

        self.tree_cars.column("id", width=60, anchor="center")
        self.tree_cars.column("type", width=140, anchor="center")
        self.tree_cars.column("plate", width=160, anchor="center")
        self.tree_cars.column("model", width=280)
        self.tree_cars.column("status", width=150, anchor="center")

        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree_cars.yview)
        self.tree_cars.configure(yscrollcommand=scrollbar.set)

        self.tree_cars.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh_all_data(self):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM vehicles")
            total_cars = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'IN_USE'")
            in_use_cars = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'AVAILABLE'")
            avail_cars = cursor.fetchone()[0]

            self.lbl_total.config(text=f"{total_cars} คัน")
            self.lbl_in_use.config(text=f"{in_use_cars} คัน")
            self.lbl_avail.config(text=f"{avail_cars} คัน")

            cursor.execute("SELECT plate_number, model, vehicle_type FROM vehicles WHERE status = 'AVAILABLE'")
            cars = [f"[{row[2]}] {row[0]} - {row[1]}" for row in cursor.fetchall()]
            self.combo_cars['values'] = cars
            if cars:
                self.combo_cars.current(0)
            else:
                self.combo_cars.set('--- ไม่มีรถว่างในระบบ ---')

            self.ent_borrow_date.delete(0, tk.END)
            self.ent_borrow_date.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            for item in self.tree_car_booking.get_children():
                self.tree_car_booking.delete(item)
            for item in self.tree_moto_booking.get_children():
                self.tree_moto_booking.delete(item)

            cursor.execute("""
            SELECT b.id, v.plate_number, v.model, b.borrower_name, b.department, b.borrow_date
            FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.status = 'ACTIVE' AND v.vehicle_type = 'รถยนต์'
            """)
            for row in cursor.fetchall():
                self.tree_car_booking.insert("", "end", values=row)

            cursor.execute("""
            SELECT b.id, v.plate_number, v.model, b.borrower_name, b.department, b.borrow_date
            FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id
            WHERE b.status = 'ACTIVE' AND v.vehicle_type = 'รถจักรยานยนต์'
            """)
            for row in cursor.fetchall():
                self.tree_moto_booking.insert("", "end", values=row)

            for item in self.tree_car_avail.get_children():
                self.tree_car_avail.delete(item)
            for item in self.tree_moto_avail.get_children():
                self.tree_moto_avail.delete(item)

            cursor.execute("SELECT plate_number, model FROM vehicles WHERE status = 'AVAILABLE' AND vehicle_type = 'รถยนต์'")
            for row in cursor.fetchall():
                self.tree_car_avail.insert("", "end", values=(row[0], row[1], "🟢 พร้อมใช้งาน"))

            cursor.execute("SELECT plate_number, model FROM vehicles WHERE status = 'AVAILABLE' AND vehicle_type = 'รถจักรยานยนต์'")
            for row in cursor.fetchall():
                self.tree_moto_avail.insert("", "end", values=(row[0], row[1], "🟢 พร้อมใช้งาน"))

            for item in self.tree_cars.get_children():
                self.tree_cars.delete(item)

            cursor.execute("SELECT id, vehicle_type, plate_number, model, status FROM vehicles ORDER BY id DESC")
            status_map = {"AVAILABLE": "🟢 พร้อมใช้งาน", "IN_USE": "🔴 ถูกเบิกใช้งาน"}
            
            for row in cursor.fetchall():
                formatted_row = (row[0], row[1], row[2], row[3], status_map.get(row[4], row[4]))
                self.tree_cars.insert("", "end", values=formatted_row)

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error refreshing data: {e}")

    def borrow_car(self):
        selected = self.combo_cars.get()
        borrower = self.ent_borrower.get().strip()
        dept = self.ent_dept.get().strip()
        borrow_date = self.ent_borrow_date.get().strip()

        if not selected or selected == '--- ไม่มีรถว่างในระบบ ---' or not borrower or not dept or not borrow_date:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกข้อมูลให้ครบถ้วนทุกช่อง")
            return

        plate = selected.split("] ")[1].split(" - ")[0]
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM vehicles WHERE plate_number = %s", (plate,))
        v_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO bookings (vehicle_id, borrower_name, department, borrow_date) VALUES (%s, %s, %s, %s)",
                       (v_id, borrower, dept, borrow_date))
        cursor.execute("UPDATE vehicles SET status = 'IN_USE' WHERE id = %s", (v_id,))
        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("สำเร็จ", f"บันทึกการเบิกรถทะเบียน {plate} เรียบร้อยแล้ว")
        self.ent_borrower.delete(0, tk.END)
        self.ent_dept.delete(0, tk.END)
        self.refresh_all_data()

    def edit_borrow_date(self):
        selected_car = self.tree_car_booking.selection()
        selected_moto = self.tree_moto_booking.selection()

        if not selected_car and not selected_moto:
            messagebox.showwarning("แจ้งเตือน", "กรุณาคลิกเลือกรายการเบิกที่ต้องการแก้ไขจากตารางก่อน")
            return

        if selected_car:
            item_values = self.tree_car_booking.item(selected_car[0], 'values')
        else:
            item_values = self.tree_moto_booking.item(selected_moto[0], 'values')

        booking_id = item_values[0]
        plate = item_values[1]
        old_date = item_values[5]

        new_date = simpledialog.askstring("แก้ไขวันที่เบิก", f"ทะเบียน: {plate}\nวันที่เบิกเดิม: {old_date}\n\nระบุวัน-เวลาเบิกใหม่:", initialvalue=old_date)

        if new_date and new_date.strip():
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE bookings SET borrow_date = %s WHERE id = %s", (new_date.strip(), booking_id))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("สำเร็จ", "แก้ไขวันที่เบิกเรียบร้อยแล้ว")
            self.refresh_all_data()

    def return_car(self):
        selected_car = self.tree_car_booking.selection()
        selected_moto = self.tree_moto_booking.selection()

        if not selected_car and not selected_moto:
            messagebox.showwarning("แจ้งเตือน", "กรุณาคลิกเลือกรายการรถที่ต้องการคืนจากตารางก่อน")
            return

        if selected_car:
            item_values = self.tree_car_booking.item(selected_car[0], 'values')
        else:
            item_values = self.tree_moto_booking.item(selected_moto[0], 'values')

        plate = item_values[1]

        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM vehicles WHERE plate_number = %s", (plate,))
        v_id = cursor.fetchone()[0]

        cursor.execute("UPDATE bookings SET status = 'RETURNED' WHERE vehicle_id = %s AND status = 'ACTIVE'", (v_id,))
        cursor.execute("UPDATE vehicles SET status = 'AVAILABLE' WHERE id = %s", (v_id,))
        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("สำเร็จ", f"ทำรายการคืนรถทะเบียน {plate} เรียบร้อยแล้ว")
        self.refresh_all_data()

    def add_car(self):
        v_type = self.combo_type.get().strip()
        plate = self.ent_new_plate.get().strip()
        model = self.ent_new_model.get().strip()

        if not plate or not model:
            messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกเลขทะเบียนและรุ่นรถให้ครบถ้วน")
            return

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO vehicles (plate_number, model, vehicle_type) VALUES (%s, %s, %s)", (plate, model, v_type))
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("สำเร็จ", f"เพิ่ม{v_type} ทะเบียน {plate} เข้าสู่ระบบเรียบร้อยแล้ว")
            self.ent_new_plate.delete(0, tk.END)
            self.ent_new_model.delete(0, tk.END)
            self.refresh_all_data()

        except psycopg2.IntegrityError:
            messagebox.showerror("ข้อผิดพลาด", f"เลขทะเบียน {plate} มีอยู่ในระบบแล้ว")

    def delete_car(self):
        selected_item = self.tree_cars.selection()
        if not selected_item:
            messagebox.showwarning("แจ้งเตือน", "กรุณาคลิกเลือกรายการรถที่ต้องการลบจากตารางก่อน")
            return

        item_values = self.tree_cars.item(selected_item[0], 'values')
        car_id = item_values[0]
        plate = item_values[2]
        status = item_values[4]

        if "ถูกเบิกใช้งาน" in status:
            messagebox.showerror("ไม่สามารถลบได้", f"รถทะเบียน {plate} กำลังถูกเบิกใช้งานอยู่ กรุณาทำรายการรับคืนรถก่อนลบออกจากระบบ")
            return

        confirm = messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบรถทะเบียน {plate} ออกจากระบบใช่หรือไม่?")
        if confirm:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vehicles WHERE id = %s", (car_id,))
            cursor.execute("DELETE FROM bookings WHERE vehicle_id = %s", (car_id,))
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("สำเร็จ", f"ลบรถทะเบียน {plate} เรียบร้อยแล้ว")
            self.refresh_all_data()

if __name__ == "__main__":
    root = tk.Tk()
    app = CarBookingApp(root)
    root.mainloop()
    def refresh_all_data(self):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # --- (โค้ดดึงข้อมูลเดิมทั้งหมดของคุณ) ---
            # เช่น ดึงข้อมูลตารางรถ, ประวัติการเบิก-คืน ฯลฯ

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error refreshing data: {e}")

        # 🟢 เพิ่มบรรทัดนี้ไว้บรรทัดสุดท้ายของฟังก์ชัน refresh_all_data
        # สั่งให้โปรแกรมดึงข้อมูลใหม่จาก Cloud มาอัปเดตหน้าจอทุกๆ 5,000 มิลลิวินาที (5 วินาที)
        self.root.after(5000, self.refresh_all_data)
        import sys
import subprocess
import os
import requests
from tkinter import messagebox

CURRENT_VERSION = "1.0.0"  # 📌 กำหนดเวอร์ชันปัจจุบันของไฟล์ .exe นี้

def check_for_updates(self):
    try:
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # ดึงข้อมูลเวอร์ชันล่าสุดจาก Supabase
        cursor.execute("SELECT version, download_url FROM app_version ORDER BY id DESC LIMIT 1;")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if result:
            latest_version, download_url = result
            if latest_version != CURRENT_VERSION:
                answer = messagebox.askyesno(
                    "พบอัปเดตใหม่", 
                    f"พบโปรแกรมเวอร์ชันใหม่ ({latest_version})\nคุณต้องการอัปเดตทันทีหรือไม่?"
                )
                if answer:
                    self.download_and_update(download_url)

    except Exception as e:
        print(f"Error checking version update: {e}")

def download_and_update(self, url):
    try:
        # ดาวน์โหลดไฟล์ .exe เวอร์ชันใหม่ลงเครื่อง
        new_exe_name = "app_update.exe"
        response = requests.get(url, stream=True)
        with open(new_exe_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        current_exe = sys.argv[0]
        
        # เขียน Batch Script ช่วยแทนที่ไฟล์ .exe เดิมแบบอัตโนมัติ
        bat_content = f"""
        @echo off
        timeout /t 2 /nobreak > nul
        move /y "{new_exe_name}" "{current_exe}"
        start "" "{current_exe}"
        del "%~f0"
        """
        
        with open("updater.bat", "w") as bat_file:
            bat_file.write(bat_content)

        # รัน updater.bat และปิดโปรแกรมปัจจุบัน
        subprocess.Popen(["updater.bat"], shell=True)
        self.root.destroy()
        sys.exit()

    except Exception as e:
        messagebox.showerror("อัปเดตล้มเหลว", f"เกิดข้อผิดพลาดในการดาวน์โหลด: {e}")
        import tkinter as tk
from PIL import Image, ImageTk
import os
import sys

def resource_path(relative_path):
    """ฟังก์ชันจัดการ Path ไฟล์สำหรับ PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)  # ซ่อนแถบหัวหน้าต่าง (Close/Min/Max)

    # โหลดและแสดงรูปภาพ Splash
    splash_img_path = resource_path("splash.png")  # 📌 เปลี่ยนชื่อไฟล์ภาพตามของคุณ
    
    if os.path.exists(splash_img_path):
        img = Image.open(splash_img_path)
        
        # ปรับขนาดภาพตามต้องการ (เช่น 500x300 Pixels)
        width, height = 500, 300
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        splash_photo = ImageTk.PhotoImage(img)

        # จัดให้อยู่กลางหน้าจอ
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        splash.geometry(f"{width}x{height}+{x}+{y}")

        label = tk.Label(splash, image=splash_photo, bg="white")
        label.image = splash_photo  # ป้องกัน Image ถูก Garbage Collection ลบ
        label.pack(fill="both", expand=True)
    else:
        # กรณีหาไฟล์รูปไม่พบ
        splash.geometry("400x200")
        label = tk.Label(splash, text="กำลังโหลดระบบ...", font=("TH Sarabun New", 18, "bold"))
        label.pack(expand=True)

    splash.update()
    return splash