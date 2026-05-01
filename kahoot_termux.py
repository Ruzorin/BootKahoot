#!/usr/bin/env python3
"""
BootKahoot Termux — Phone-Only Auto-Tapper
Kamerayla projektörü çeker, Gemini ile analiz eder,
ADB ile Kahoot'a otomatik tıklar. Laptop gerektirmez.
"""
import subprocess, requests, base64, time, json, os, sys, io

# ===== PROMPT =====
PROMPT = (
    "Ekrandaki Kahoot sorusunu ve şıklarını dikkatlice oku. "
    "ÖNEMLİ KURAL: Eğer ekranda henüz renkli cevap şıkları (kutu/butonlar) "
    "BELİRMEMİŞSE, sadece ve sadece 'BEKLE' yaz. "
    "Eğer renkli şıklar ekrandaysa doğru cevabı bul. "
    "Soru 4 seçenekliyse SADECE şu kelimelerden BİRİNİ dön: KIRMIZI, MAVI, SARI, YESIL. "
    "Eğer soru Doğru/Yanlış (True/False) sorusuysa ve sadece 2 şık varsa, "
    "'Doğru' cevap için MAVI, 'Yanlış' cevap için KIRMIZI dön. "
    "Asla açıklama yapma."
)

CONFIG_FILE = os.path.expanduser("~/.kahoot_adb.json")
PHOTO_PATH = os.path.expanduser("~/kahoot_cap.jpg")

# Samsung M52 (1080x2400) — Kahoot ALT YARISINDA (split-screen)
DEFAULT_COORDS = {
    "KIRMIZI": [270, 1650],
    "MAVI":    [810, 1650],
    "SARI":    [270, 1950],
    "YESIL":   [810, 1950],
}
COLOR_NAMES = {
    "KIRMIZI": "🔴 KIRMIZI",
    "MAVI":    "🔵 MAVİ",
    "SARI":    "🟡 SARI",
    "YESIL":   "🟢 YEŞİL",
}

# ===== YARDIMCILAR =====
def log(msg):
    t = time.strftime("%H:%M:%S")
    print(f"[{t}] {msg}")

def adb_tap(x, y):
    subprocess.run(["adb", "shell", "input", "tap", str(int(x)), str(int(y))],
                   capture_output=True, timeout=5)

def adb_ok():
    try:
        r = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        return any("device" in l and "List" not in l for l in r.stdout.split("\n"))
    except:
        return False

def take_photo():
    """Termux:API ile arka kameradan fotoğraf çek."""
    if os.path.exists(PHOTO_PATH):
        os.remove(PHOTO_PATH)
    subprocess.run(["termux-camera-photo", "-c", "0", PHOTO_PATH],
                   capture_output=True, timeout=15)
    return os.path.exists(PHOTO_PATH)

def photo_to_b64(max_w=768):
    """Fotoğrafı base64'e çevir, boyutu küçült."""
    try:
        from PIL import Image
        img = Image.open(PHOTO_PATH)
        w, h = img.size
        if w > max_w:
            r = max_w / w
            img = img.resize((max_w, int(h * r)))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        with open(PHOTO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()

def ask_gemini(keys, key_idx, model, b64):
    """Gemini REST API'ye gönder, cevap al."""
    key = keys[key_idx % len(keys)]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"parts": [
            {"text": PROMPT},
            {"inlineData": {"mimeType": "image/jpeg", "data": b64}}
        ]}],
        "generationConfig": {"temperature": 0}
    }
    r = requests.post(url, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip().upper()

def parse_color(txt):
    for c in ["KIRMIZI", "MAVI", "SARI", "YESIL"]:
        if c in txt:
            return c
    return None

# ===== CONFIG =====
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def setup_wizard():
    """İlk kurulum sihirbazı."""
    print("\n🚀 BootKahoot Termux — İlk Kurulum")
    print("=" * 40)

    cfg = load_config()

    # API Keys
    existing = cfg.get("api_keys", "")
    keys = input(f"Gemini API key(leri) (virgülle ayır)\n[{existing[:20]}...]: ").strip()
    if keys:
        cfg["api_keys"] = keys
    elif not existing:
        print("❌ API key gerekli!")
        sys.exit(1)

    # Model
    model = cfg.get("model", "gemini-2.5-flash")
    m = input(f"Model [{model}]: ").strip()
    if m:
        cfg["model"] = m

    # Koordinatlar
    print("\n📱 Kahoot Buton Koordinatları (split-screen alt yarı)")
    print("Varsayılan koordinatlar Samsung M52 (1080x2400) içindir.")
    use_default = input("Varsayılanları kullan? [E/h]: ").strip().lower()
    if use_default != "h":
        cfg["coords"] = DEFAULT_COORDS
    else:
        cfg["coords"] = {}
        for color in ["KIRMIZI", "MAVI", "SARI", "YESIL"]:
            xy = input(f"  {color} (x,y): ").strip().split(",")
            cfg["coords"][color] = [int(xy[0]), int(xy[1])]

    # Cooldown
    cfg["cooldown"] = int(input("Cooldown (sn) [6]: ").strip() or "6")
    cfg["poll_interval"] = float(input("Fotoğraf aralığı (sn) [2]: ").strip() or "2")

    save_config(cfg)
    print("\n✅ Ayarlar kaydedildi!")
    return cfg

def test_taps(cfg):
    """Her renk butonuna test tıklaması yap."""
    print("\n🧪 Test Tıklaması — Kahoot'u aç ve izle")
    coords = cfg.get("coords", DEFAULT_COORDS)
    for color in ["KIRMIZI", "MAVI", "SARI", "YESIL"]:
        xy = coords[color]
        input(f"  {COLOR_NAMES[color]} ({xy[0]},{xy[1]}) tıklanacak — Enter'a bas...")
        adb_tap(xy[0], xy[1])
        print(f"  ✅ Tıklandı!")
    print("Test tamamlandı. Koordinatları düzeltmek için --setup çalıştır.\n")

# ===== ANA DÖNGÜ =====
def run_bot(cfg):
    keys = [k.strip() for k in cfg["api_keys"].split(",") if k.strip()]
    model = cfg.get("model", "gemini-2.5-flash")
    coords = cfg.get("coords", DEFAULT_COORDS)
    cooldown = cfg.get("cooldown", 6)
    poll = cfg.get("poll_interval", 2)
    key_idx = 0
    last_answer = 0
    stats = {"count": 0, "times": []}

    print("\n" + "=" * 40)
    print("🚀 BootKahoot AKTIF — Oto-Tıklama AÇIK")
    print(f"📷 Kamera → Gemini ({model}) → ADB Tap")
    print(f"🔑 {len(keys)} API key | ⏱ {poll}s aralık | ❄️ {cooldown}s cooldown")
    print("Ctrl+C ile durdur")
    print("=" * 40 + "\n")

    while True:
        try:
            # Cooldown kontrolü
            if time.time() - last_answer < cooldown:
                remaining = cooldown - (time.time() - last_answer)
                sys.stdout.write(f"\r❄️ Cooldown: {remaining:.0f}s   ")
                sys.stdout.flush()
                time.sleep(1)
                continue

            # Fotoğraf çek
            sys.stdout.write(f"\r📷 Çekiliyor...          ")
            sys.stdout.flush()
            if not take_photo():
                log("⚠ Fotoğraf çekilemedi, tekrar deneniyor...")
                time.sleep(2)
                continue

            # Base64'e çevir
            b64 = photo_to_b64()

            # Gemini'ye sor
            sys.stdout.write(f"\r🤖 Gemini düşünüyor...   ")
            sys.stdout.flush()
            t0 = time.time()
            answer = ask_gemini(keys, key_idx, model, b64)
            dt = time.time() - t0
            key_idx += 1

            # BEKLE — şıklar henüz yüklenmemiş
            if "BEKLE" in answer:
                log(f"⏳ ({dt:.1f}s) Şıklar bekleniyor... tekrar çekilecek")
                time.sleep(1)
                continue

            # YOK — soru yok
            if "YOK" in answer:
                log(f"⏭ ({dt:.1f}s) Soru yok, bekleniyor...")
                time.sleep(poll)
                continue

            # Renk algıla
            color = parse_color(answer)
            if color and color in coords:
                x, y = coords[color]
                adb_tap(x, y)
                stats["count"] += 1
                stats["times"].append(dt)
                avg = sum(stats["times"]) / len(stats["times"])
                last_answer = time.time()
                log(f"✅ {COLOR_NAMES[color]} tıklandı! ({dt:.1f}s) | "
                    f"#{stats['count']} | ort: {avg:.1f}s")
            else:
                log(f"⚠ ({dt:.1f}s) Renk bulunamadı: {answer}")

            time.sleep(poll)

        except KeyboardInterrupt:
            print("\n\n⏹ Bot durduruldu.")
            if stats["count"]:
                avg = sum(stats["times"]) / len(stats["times"])
                print(f"📊 Toplam: {stats['count']} soru | Ortalama: {avg:.1f}s")
            break
        except Exception as e:
            log(f"❌ Hata: {e}")
            time.sleep(3)

# ===== MAIN =====
if __name__ == "__main__":
    # ADB kontrolü
    if not adb_ok():
        print("❌ ADB bağlantısı yok!")
        print("Kablosuz hata ayıklamayı aç ve bağlan:")
        print("  adb pair localhost:PORT KOD")
        print("  adb connect localhost:PORT")
        sys.exit(1)

    # Argümanlar
    if "--setup" in sys.argv:
        cfg = setup_wizard()
    elif "--test" in sys.argv:
        cfg = load_config()
        if not cfg:
            cfg = setup_wizard()
        test_taps(cfg)
    else:
        cfg = load_config()
        if not cfg.get("api_keys"):
            cfg = setup_wizard()
        run_bot(cfg)
