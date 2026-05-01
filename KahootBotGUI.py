# UYARI: Windows'ta Yönetici (Administrator) olarak çalıştırılmalıdır.

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from google import genai
from google.genai import types
import pyautogui
import keyboard
import threading
import time
import json
import os
import io
import cv2
from PIL import ImageGrab, ImageChops, ImageStat, Image

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

CONFIG_FILE = "kahoot_config.json"
DEFAULT_MODEL = "gemini-2.5-flash"
POLL_INTERVAL_MS = 500
CHANGE_THRESHOLD = 15.0
AUTO_COOLDOWN_S = 6.0
IMG_MAX_WIDTH = 768
OPTION_POLL_MS = 400          # Şık kontrol aralığı (ms)
OPTION_TIMEOUT_S = 8.0        # Max bekleme süresi
MIN_REQUEST_INTERVAL_S = 2    # Key rotasyonu sayesinde düşük tutabiliriz

PROMPT_TR = (
    "Ekrandaki Kahoot sorusunu ve şıklarını dikkatlice oku. "
    "ÖNEMLİ KURAL: Eğer ekranda henüz renkli cevap şıkları (kutu/butonlar) "
    "BELİRMEMİŞSE, sadece ve sadece 'BEKLE' yaz. "
    "Eğer renkli şıklar ekrandaysa doğru cevabı bul. "
    "Soru 4 seçenekliyse SADECE şu kelimelerden BİRİNİ dön: KIRMIZI, MAVI, SARI, YESIL. "
    "Eğer soru Doğru/Yanlış (True/False) sorusuysa ve sadece 2 şık varsa, "
    "'Doğru' cevap için MAVI, 'Yanlış' cevap için KIRMIZI dön. "
    "Asla açıklama yapma."
)

COL_BG = "#121212"
COL_FRAME = "#1E1E1E"
COL_TEXT = "#E0E0E0"
COL_ACCENT = "#BB86FC"
COL_SUCCESS = "#03DAC6"
COL_WARN = "#CF6679"
COL_INPUT = "#2C2C2C"
COL_TURBO = "#FF6D00"


class KahootBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kahoot Bot — AI Summit '26 Turbo")
        self.root.geometry("450x850")
        self.root.attributes('-topmost', True)
        self.root.configure(bg=COL_BG)

        self.api_key = tk.StringVar()
        self.selected_model_name = tk.StringVar(value=DEFAULT_MODEL)
        self.capture_area = None
        self.button_coords = {"rojo": None, "azul": None, "amarillo": None, "verde": None}
        self.clients = []         # Birden fazla API key için client listesi
        self.client_index = 0     # Sıradaki client
        self.client = None        # Aktif client
        self.model_name = None
        self.is_running = False
        self.is_waiting = False   # Çift tetiklemeyi önle

        self.use_camera = tk.BooleanVar(value=False)
        self.camera_index = tk.IntVar(value=0)
        self.camera_cap = None

        self.auto_mode = False
        self.last_screenshot = None
        self.last_answer_time = 0
        self.last_request_time = 0
        self.stats = {"answered": 0, "times": []}

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=COL_INPUT, background=COL_FRAME,
                        foreground=COL_TEXT, arrowcolor="white")

        self.create_header()
        self.create_source_section()
        self.create_calibration_section()
        self.create_turbo_section()
        self.create_control_section()

        self.load_config()
        keyboard.add_hotkey('k', self.on_hotkey_pressed)
        self.update_ui_status()

    def create_header(self):
        f = tk.LabelFrame(self.root, text=" 1. BAĞLANTI ", bg=COL_BG, fg=COL_SUCCESS,
                          font=("Consolas", 10, "bold"), bd=2, relief="groove")
        f.pack(fill="x", padx=15, pady=10)
        tk.Label(f, text="API Key (birden fazla = virgülle ayır):", bg=COL_BG, fg=COL_TEXT).pack(anchor="w", padx=5)
        tk.Entry(f, textvariable=self.api_key, show="", bg=COL_INPUT, fg="white",
                 insertbackground="white", relief="flat").pack(fill="x", padx=5, pady=5, ipady=3)
        tk.Button(f, text="↻ Modelleri Bul", command=self.fetch_models,
                  bg="#3700B3", fg="white", relief="flat", cursor="hand2").pack(fill="x", padx=5, pady=2)
        tk.Label(f, text="Model:", bg=COL_BG, fg=COL_TEXT).pack(anchor="w", padx=5)
        self.combo_models = ttk.Combobox(f, textvariable=self.selected_model_name, state="normal")
        self.combo_models.pack(fill="x", padx=5, pady=2)
        tk.Button(f, text="⚡ BAĞLAN", command=self.manual_connect,
                  bg=COL_SUCCESS, fg="black", font=("Arial", 9, "bold"), cursor="hand2"
                  ).pack(fill="x", padx=5, pady=8)

    def create_source_section(self):
        f = tk.LabelFrame(self.root, text=" 2. GÖRÜNTÜ KAYNAĞI ", bg=COL_BG, fg="#00BCD4",
                          font=("Consolas", 10, "bold"), bd=2, relief="groove")
        f.pack(fill="x", padx=15, pady=5)
        row = tk.Frame(f, bg=COL_BG)
        row.pack(fill="x", padx=5, pady=5)
        tk.Radiobutton(row, text="Ekran Yakalama", variable=self.use_camera, value=False,
                       bg=COL_BG, fg=COL_TEXT, selectcolor=COL_INPUT, activebackground=COL_BG,
                       command=self._on_source_change).pack(side="left", padx=5)
        tk.Radiobutton(row, text="Kamera (DroidCam)", variable=self.use_camera, value=True,
                       bg=COL_BG, fg=COL_TEXT, selectcolor=COL_INPUT, activebackground=COL_BG,
                       command=self._on_source_change).pack(side="left", padx=5)
        self.cam_frame = tk.Frame(f, bg=COL_BG)
        self.cam_frame.pack(fill="x", padx=5, pady=2)
        tk.Label(self.cam_frame, text="Kamera No:", bg=COL_BG, fg=COL_TEXT).pack(side="left")
        tk.Spinbox(self.cam_frame, from_=0, to=5, textvariable=self.camera_index, width=3,
                   bg=COL_INPUT, fg="white").pack(side="left", padx=5)
        tk.Button(self.cam_frame, text="📷 Test Et", command=self.test_camera,
                  bg=COL_FRAME, fg="white", cursor="hand2").pack(side="left", padx=5)
        self.lbl_cam = tk.Label(self.cam_frame, text="", bg=COL_BG, fg=COL_WARN, font=("Arial", 8))
        self.lbl_cam.pack(side="left", padx=5)
        tk.Label(f, text="💡 DroidCam ile telefonu projektöre çevir, kamera no'yu seç",
                 bg=COL_BG, fg="gray", font=("Arial", 7)).pack(pady=(0, 3))

    def _on_source_change(self):
        if not self.use_camera.get() and self.camera_cap:
            self.camera_cap.release()
            self.camera_cap = None

    def test_camera(self):
        idx = self.camera_index.get()
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                Image.fromarray(frame_rgb).show(title=f"Kamera {idx} Testi")
                self.lbl_cam.config(text=f"✔ Kamera {idx} OK", fg=COL_SUCCESS)
            cap.release()
        else:
            self.lbl_cam.config(text=f"✘ Kamera {idx} bulunamadı", fg=COL_WARN)

    def _grab_camera_frame(self):
        if self.camera_cap is None or not self.camera_cap.isOpened():
            self.camera_cap = cv2.VideoCapture(self.camera_index.get())
        ret, frame = self.camera_cap.read()
        if not ret:
            return None
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def create_calibration_section(self):
        f = tk.LabelFrame(self.root, text=" 3. KALİBRASYON ", bg=COL_BG, fg=COL_ACCENT,
                          font=("Consolas", 10, "bold"), bd=2, relief="groove")
        f.pack(fill="x", padx=15, pady=5)
        tk.Button(f, text="[ A ] ALAN BELİRLE", command=self.start_area_selection,
                  bg=COL_FRAME, fg="white", relief="raised").pack(fill="x", padx=5, pady=2)
        self.lbl_area = tk.Label(f, text="⚠ Alan Belirlenmedi", bg=COL_BG, fg=COL_WARN, font=("Arial", 8))
        self.lbl_area.pack()
        tk.Button(f, text="[ B ] BUTONLARI EŞLEŞTİR", command=self.start_button_calibration,
                  bg=COL_FRAME, fg="white", relief="raised").pack(fill="x", padx=5, pady=2)
        self.lbl_buttons = tk.Label(f, text="⚠ Butonlar Eşleştirilmedi", bg=COL_BG, fg=COL_WARN, font=("Arial", 8))
        self.lbl_buttons.pack(pady=(0, 5))

    def create_turbo_section(self):
        f = tk.LabelFrame(self.root, text=" 4. TURBO MOD ⚡ ", bg=COL_BG, fg=COL_TURBO,
                          font=("Consolas", 10, "bold"), bd=2, relief="groove")
        f.pack(fill="x", padx=15, pady=5)
        self.btn_auto = tk.Button(f, text="🚀 OTO-MOD: KAPALI", command=self.toggle_auto_mode,
                                  bg=COL_FRAME, fg="white", font=("Arial", 10, "bold"),
                                  activebackground=COL_TURBO, cursor="hand2")
        self.btn_auto.pack(fill="x", padx=5, pady=5)
        sf = tk.Frame(f, bg=COL_BG)
        sf.pack(fill="x", padx=5, pady=(0, 5))
        self.lbl_stats = tk.Label(sf, text="📊 0 soru | ⏱ --", bg=COL_BG, fg=COL_TEXT, font=("Consolas", 9))
        self.lbl_stats.pack(side="left")
        self.lbl_speed = tk.Label(sf, text="", bg=COL_BG, fg=COL_SUCCESS, font=("Consolas", 9, "bold"))
        self.lbl_speed.pack(side="right")

    def create_control_section(self):
        f = tk.LabelFrame(self.root, text=" 5. OYUN ", bg=COL_BG, fg="#FF0266",
                          font=("Consolas", 10, "bold"), bd=2, relief="groove")
        f.pack(fill="both", expand=True, padx=15, pady=10)
        self.lbl_status = tk.Label(f, text="ÇEVRİMDIŞI", bg=COL_BG, fg="#555555", font=("Impact", 24))
        self.lbl_status.pack(pady=10)
        tb = tk.Frame(f, bg=COL_BG)
        tb.pack(fill="x", padx=5)
        tk.Label(tb, text="Gemini Logu:", bg=COL_BG, fg="gray", font=("Arial", 8)).pack(side="left")
        tk.Button(tb, text="🗑 Temizle", command=self.clear_log,
                  bg=COL_BG, fg=COL_WARN, font=("Arial", 8, "bold"), bd=0, cursor="hand2").pack(side="right")
        self.log_box = scrolledtext.ScrolledText(f, height=6, font=("Consolas", 9),
                                                 bg="#000000", fg="#00FF00", state='normal')
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)
        tk.Label(f, text="'K' = Manuel  |  Oto-Mod = Tam otomatik", bg=COL_BG, fg=COL_ACCENT).pack(pady=5)

    # === YARDIMCI ===
    def clear_log(self):
        self.log_box.delete('1.0', tk.END)

    def log(self, text):
        self.log_box.insert(tk.END, f"> {text}\n")
        self.log_box.see(tk.END)
        print(f"LOG: {text}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.api_key.set(data.get("api_key", ""))
                    self.capture_area = data.get("capture_area")
                    self.button_coords = data.get("button_coords", self.button_coords)
                    saved_model = data.get("model_name", "")
                    if saved_model:
                        self.selected_model_name.set(saved_model)
                    self.use_camera.set(data.get("use_camera", False))
                    self.camera_index.set(data.get("camera_index", 0))
            except:
                pass

    def save_config(self):
        data = {
            "api_key": self.api_key.get(),
            "capture_area": self.capture_area,
            "button_coords": self.button_coords,
            "model_name": self.selected_model_name.get(),
            "use_camera": self.use_camera.get(),
            "camera_index": self.camera_index.get()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)

    def update_ui_status(self):
        if self.capture_area:
            self.lbl_area.config(text="✔ Alan OK", fg=COL_SUCCESS)
        if all(self.button_coords.values()):
            self.lbl_buttons.config(text="✔ Butonlar OK", fg=COL_SUCCESS)
        source_ok = self.use_camera.get() or self.capture_area
        if self.client and source_ok and all(self.button_coords.values()):
            self.lbl_status.config(text="HAZIR (K)", fg=COL_SUCCESS)
        else:
            self.lbl_status.config(text="YAPILANDIR", fg="orange")

    def update_stats_ui(self):
        n = self.stats["answered"]
        if self.stats["times"]:
            avg = sum(self.stats["times"]) / len(self.stats["times"])
            last = self.stats["times"][-1]
            self.lbl_stats.config(text=f"📊 {n} soru | ⏱ ort: {avg:.1f}s")
            self.lbl_speed.config(text=f"Son: {last:.1f}s")

    def optimize_image(self, img):
        w, h = img.size
        if w > IMG_MAX_WIDTH:
            ratio = IMG_MAX_WIDTH / w
            img = img.resize((IMG_MAX_WIDTH, int(h * ratio)))
        return img

    def pil_to_bytes(self, img):
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return buf.read()

    # === MODEL ===
    def fetch_models(self):
        key = self.api_key.get().strip()
        if not key:
            return messagebox.showerror("Hata", "Önce API Key gir")
        self.log("Modeller aranıyor...")
        try:
            client = genai.Client(api_key=key)
            models = [m.name for m in client.models.list()]
            self.combo_models['values'] = models
            if models:
                self.combo_models.set(models[0])
                self.log(f"Bulunan: {len(models)} model")
        except Exception as e:
            self.log(f"API Hatası: {e}")

    def manual_connect(self):
        name = self.selected_model_name.get().strip()
        if not name:
            return messagebox.showerror("Hata", "Bir model yaz veya seç")
        self.connect_model(name)

    def connect_model(self, model_name):
        try:
            keys = [k.strip() for k in self.api_key.get().split(",") if k.strip()]
            if not keys:
                self.log("Hata: API key girilmedi")
                return
            self.clients = [genai.Client(api_key=k) for k in keys]
            self.client_index = 0
            self.client = self.clients[0]
            self.model_name = model_name
            self.log(f"Bağlanıldı: {model_name} ({len(keys)} key)")
            self.save_config()
            self.update_ui_status()
            self.log("⏳ Bağlantı ısıtılıyor...")
            threading.Thread(target=self._prewarm, daemon=True).start()
        except Exception as e:
            self.log(f"Bağlantı hatası: {e}")

    def _next_client(self):
        """Sıradaki API key'e geç (round-robin)."""
        if len(self.clients) > 1:
            self.client_index = (self.client_index + 1) % len(self.clients)
            self.client = self.clients[self.client_index]

    def _prewarm(self):
        try:
            t0 = time.time()
            self.client.models.generate_content(
                model=self.model_name,
                contents="test",
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            dt = time.time() - t0
            self.root.after(0, lambda: self.log(f"✔ Hazır! Pre-warm: {dt:.1f}s"))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda m=err: self.log(f"⚠ Pre-warm: {m}"))

    # === KALİBRASYON ===
    def start_area_selection(self):
        self.root.iconify()
        self.sel_win = tk.Toplevel(self.root)
        self.sel_win.attributes('-fullscreen', True, '-alpha', 0.3, '-topmost', True)
        self.sel_win.config(bg='black')
        self.sel_win.bind('<Button-1>', self.on_click_start)
        self.sel_win.bind('<B1-Motion>', self.on_drag)
        self.sel_win.bind('<ButtonRelease-1>', self.on_click_end)
        self.canvas = tk.Canvas(self.sel_win, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def on_click_start(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline=COL_SUCCESS, width=3)

    def on_drag(self, e):
        self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def on_click_end(self, e):
        x1, y1 = min(self.start_x, e.x), min(self.start_y, e.y)
        x2, y2 = max(self.start_x, e.x), max(self.start_y, e.y)
        self.capture_area = (x1, y1, x2, y2)
        self.save_config()
        self.update_ui_status()
        self.sel_win.destroy()
        self.root.deiconify()

    def start_button_calibration(self):
        messagebox.showinfo("Sıralama", "Sırayla tıkla: KIRMIZI -> MAVİ -> SARI -> YEŞİL")
        self.root.iconify()
        self.cal_win = tk.Toplevel(self.root)
        self.cal_win.attributes('-fullscreen', True, '-alpha', 0.01, '-topmost', True)
        self.cal_win.bind('<Button-1>', self.cal_click)
        self.cal_step = 0
        self.colors = ["rojo", "azul", "amarillo", "verde"]

    def cal_click(self, e):
        if self.cal_step < 4:
            self.button_coords[self.colors[self.cal_step]] = (e.x, e.y)
            self.cal_step += 1
            if self.cal_step == 4:
                self.cal_win.destroy()
                self.root.deiconify()
                self.save_config()
                self.update_ui_status()

    # === TURBO OTO-MOD ===
    def toggle_auto_mode(self):
        source_ok = self.use_camera.get() or self.capture_area
        if not self.client or not source_ok or not all(self.button_coords.values()):
            messagebox.showwarning("Uyarı", "Önce model bağla, kaynak ayarla ve butonları eşleştir!")
            return
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.btn_auto.config(text="🔥 OTO-MOD: AÇIK", bg=COL_TURBO, fg="black")
            self.last_screenshot = None
            self.log("🚀 OTO-MOD AÇILDI")
            self._auto_poll()
        else:
            self.btn_auto.config(text="🚀 OTO-MOD: KAPALI", bg=COL_FRAME, fg="white")
            self.log("⏹ OTO-MOD KAPATILDI")

    def _auto_poll(self):
        if not self.auto_mode:
            return
        if time.time() - self.last_answer_time < AUTO_COOLDOWN_S or self.is_running or self.is_waiting:
            self.root.after(POLL_INTERVAL_MS, self._auto_poll)
            return
        try:
            img = self._grab_image()
            if img and self._detect_change(img):
                self.is_waiting = True  # Çift tetiklemeyi önle
                self.log("🔍 Ekran değişti — şıklar bekleniyor...")
                self.last_screenshot = img
                threading.Thread(target=self._wait_and_process, daemon=True).start()
            elif img and self.last_screenshot is None:
                self.last_screenshot = img
        except:
            pass
        self.root.after(POLL_INTERVAL_MS, self._auto_poll)

    def _grab_image(self):
        if self.use_camera.get():
            return self._grab_camera_frame()
        elif self.capture_area:
            return ImageGrab.grab(bbox=self.capture_area)
        return None

    def _detect_change(self, new_img):
        if self.last_screenshot is None:
            return False
        try:
            size = (64, 64)
            old_s = self.last_screenshot.resize(size)
            new_s = new_img.resize(size)
            diff = ImageChops.difference(old_s, new_s)
            stat = ImageStat.Stat(diff)
            return sum(stat.mean) / len(stat.mean) > CHANGE_THRESHOLD
        except:
            return False

    # === ANA İŞLEM ===
    def on_hotkey_pressed(self):
        if self.is_running or not self.client:
            return
        threading.Thread(target=self._capture_and_process, daemon=True).start()

    def _capture_and_process(self):
        img = self._grab_image()
        if img:
            self._process_image(img)

    def _wait_and_process(self):
        """2 aşamalı algılama: Soru geldi → şıkları bekle → gönder."""
        # Aşama 1: Soru geldi, şımdi şıkların gelmesini bekle
        # Şıklar gelince ekran tekrar değişecek
        base_img = self._grab_image()
        start = time.time()
        
        while time.time() - start < OPTION_TIMEOUT_S:
            time.sleep(OPTION_POLL_MS / 1000)
            new_img = self._grab_image()
            if new_img and base_img:
                try:
                    size = (64, 64)
                    old_s = base_img.resize(size)
                    new_s = new_img.resize(size)
                    diff = ImageChops.difference(old_s, new_s)
                    stat = ImageStat.Stat(diff)
                    mean_diff = sum(stat.mean) / len(stat.mean)
                    if mean_diff > CHANGE_THRESHOLD:
                        # 2. değişiklik algılandı = şıklar geldi!
                        self.root.after(0, lambda: self.log("✅ Şıklar yüklendi!"))
                        time.sleep(0.5)  # Kısa bekleme, her şey oturmuş olsun
                        final_img = self._grab_image()
                        if final_img:
                            self.last_screenshot = final_img
                            self._process_image(final_img)
                        return
                except:
                    pass
                base_img = new_img
        
        # Timeout: şıklar ayrı gelmemiş olabilir, ne varsa gönder
        self.root.after(0, lambda: self.log("⏰ Timeout — mevcut ekranla devam"))
        img = self._grab_image()
        if img:
            self.last_screenshot = img
            self._process_image(img)
        else:
            self.is_waiting = False

    def _process_image(self, img):
        # Rate limit kontrolü
        elapsed = time.time() - self.last_request_time
        if elapsed < MIN_REQUEST_INTERVAL_S:
            wait = MIN_REQUEST_INTERVAL_S - elapsed
            self.root.after(0, lambda w=wait: self.log(f"⏳ Rate limit bekleniyor ({w:.0f}s)"))
            time.sleep(wait)

        self.is_running = True
        self.last_request_time = time.time()
        self.root.after(0, lambda: self.lbl_status.config(text="⌛ DÜŞÜNÜYOR...", fg=COL_TURBO))
        try:
            self._next_client()  # API key rotasyonu
            img = self.optimize_image(img)
            img_bytes = self.pil_to_bytes(img)

            t0 = time.time()
            res = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(parts=[
                        types.Part.from_text(text=PROMPT_TR),
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    ])
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            txt = res.text.strip().upper()
            dt = time.time() - t0

            self.root.after(0, lambda dt=dt, txt=txt: self.log(f"🤖 ({dt:.2f}s): {txt}"))

            # Şıklar henüz yüklenmemiş — tıklama, oto-mod tekrar deneyecek
            if "BEKLE" in txt:
                self.root.after(0, lambda: self.log("⏳ Şıklar bekleniyor... tekrar denenecek"))
                self.root.after(0, lambda: self.lbl_status.config(text="⏳ ŞIKLAR BEKLENİYOR", fg=COL_TURBO))
                self.is_running = False
                self.is_waiting = False
                self.last_screenshot = None  # Bir sonraki poll'da tekrar tetiklensin
                return

            # Soru yoksa atla
            if "YOK" in txt:
                self.root.after(0, lambda: self.log("⏭ Soru/şık yok, atlandı"))
                self.is_running = False
                self.is_waiting = False
                return

            detected = None
            if "KIRMIZI" in txt: detected = "rojo"
            elif "MAVI" in txt: detected = "azul"
            elif "SARI" in txt: detected = "amarillo"
            elif "YESIL" in txt: detected = "verde"

            if detected and self.button_coords[detected]:
                color_tr = {"rojo": "KIRMIZI", "azul": "MAVİ", "amarillo": "SARI", "verde": "YEŞİL"}
                label = color_tr.get(detected, detected)
                self.root.after(0, lambda l=label, d=dt: self.lbl_status.config(
                    text=f"✔ {l} ({d:.1f}s)", fg=COL_SUCCESS))
                pyautogui.click(self.button_coords[detected])
                self.stats["answered"] += 1
                self.stats["times"].append(dt)
                self.last_answer_time = time.time()
                self.root.after(0, self.update_stats_ui)
            else:
                self.root.after(0, lambda: self.lbl_status.config(text="? RENK BULUNAMADI", fg=COL_WARN))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda m=err_msg: self.log(f"Hata: {m}"))
        finally:
            self.is_running = False
            self.is_waiting = False
            if self.client and not self.auto_mode:
                self.root.after(500, lambda: self.lbl_status.config(text="HAZIR (K)", fg=COL_SUCCESS))


if __name__ == "__main__":
    root = tk.Tk()
    app = KahootBotApp(root)
    root.mainloop()