# 🚀 BootKahoot — AI-Powered Kahoot Bot

> **DAÜ Yapay Zeka Zirvesi '26** için geliştirilmiş, Gemini destekli tam otomatik Kahoot yanıtlama sistemi.

---

## 🎯 Amaç

2 Mayıs 2026'da **Doğu Akdeniz Üniversitesi (DAÜ) Yapay Zeka Zirvesi**'nde düzenlenecek Kahoot yarışmalarında en yüksek sıralamayı elde etmek için tasarlanmıştır.

| Yarışma | Sponsor | Ödül | Kota |
|---------|---------|------|------|
| Kahoot #1 | **KoopBank** | Staj İmkanı | İlk **5** kişi |
| Kahoot #2 | **Turkcell KKTC** | Staj İmkanı | İlk **2** kişi |

Bot, ekran görüntüsünü (veya kamera feed'ini) Gemini'ye gönderir, doğru cevabın rengini belirler ve otomatik olarak tıklar — tüm süreç **~3-4 saniye** içinde tamamlanır.

---

## ⚡ Özellikler

### Çekirdek
- **Gemini Vision Entegrasyonu** — Ekran görüntüsünü veya kamera karesini Gemini'ye gönderip renk bazlı cevap alır
- **Tam Otomatik Mod (Turbo)** — Ekran değişikliğini algılar, şıkların yüklenmesini bekler, soruyu gönderir ve otomatik tıklar
- **Manuel Mod** — `K` tuşuyla tek seferde soru gönderme

### Hız & Güvenilirlik
- **Multi-Key Rotasyon** — Birden fazla API key ile round-robin rotasyon; rate-limit'i bypass eder
- **Pre-warm Bağlantı** — Model bağlantısı önceden ısıtılarak ilk soruda gecikme önlenir
- **Thinking Budget = 0** — Gemini'nin düşünme aşaması devre dışı bırakılarak minimum gecikme sağlanır
- **Görüntü Optimizasyonu** — Yüksek çözünürlüklü ekran yakalama max 768px'e küçültülür, JPEG %85 kalitede sıkıştırılır

### Algılama
- **2 Aşamalı Ekran Değişikliği Algılama** — İlk değişiklik (soru geldi) sonrası ikinci değişiklik (şıklar yüklendi) beklenir
- **Pixel-Level Diff** — 64×64 küçültülmüş görüntüler üzerinden ortalama fark hesaplanır (eşik: `15.0`)
- **False-Positive Koruması** — `YOK` yanıtı ile soru olmayan ekranlar otomatik atlanır
- **Cooldown Mekanizması** — Her cevaptan sonra 6 saniye bekleme ile çift tetikleme önlenir

### Giriş Kaynakları
- **Ekran Yakalama** — Belirlenen alan (bbox) üzerinden `ImageGrab`
- **Kamera (DroidCam)** — Telefonu projektöre çevirip `cv2.VideoCapture` ile kamera feed'i

### Arayüz
- **Tkinter Dark-Mode GUI** — Kompakt, always-on-top pencere
- **Canlı İstatistikler** — Cevaplanan soru sayısı, ortalama süre, son süre
- **Renkli Log Konsolu** — Her adım gerçek zamanlı loglanır
- **Kalibrasyon Araçları** — Ekran alanı ve buton koordinatları görsel olarak belirlenir

---

## 🛠 Kurulum

### Gereksinimler
- Python 3.10+
- Windows (Yönetici olarak çalıştırılmalı)
- En az 1 adet [Google AI Studio](https://aistudio.google.com/) API key'i

### Bağımlılıklar

```bash
pip install google-genai pyautogui keyboard pillow opencv-python
```

### Çalıştırma

```bash
# Yönetici (Administrator) olarak PowerShell/CMD aç
python KahootBotGUI.py
```

---

## 📖 Kullanım Kılavuzu

### 1. Bağlantı
1. API key'leri gir (birden fazla key virgülle ayrılır → rate-limit bypass)
2. Model seç (varsayılan: `gemini-2.5-flash`)
3. **⚡ BAĞLAN** butonuna tıkla
4. Pre-warm tamamlanana kadar bekle

### 2. Görüntü Kaynağı
- **Ekran Yakalama** — Kahoot ekranının olduğu monitörü seç
- **Kamera (DroidCam)** — Telefonu webcam olarak kullanmak için kamera numarasını ayarla

### 3. Kalibrasyon
1. **Alan Belirle** — Kahoot ekranının tamamını kapsayan dikdörtgeni seç
2. **Butonları Eşleştir** — Sırasıyla tıkla: 🔴 Kırmızı → 🔵 Mavi → 🟡 Sarı → 🟢 Yeşil

### 4. Yarışma
| Mod | Tetikleme | Kullanım |
|-----|-----------|----------|
| **Manuel** | `K` tuşu | Her soru için elle tetikle |
| **Turbo (Oto)** | Otomatik | Ekran değişikliğini algılar ve otomatik çalışır |

> 💡 **İpucu:** Turbo mod için `OTO-MOD` butonunu aç ve arkana yaslan.

---

## ⚙️ Teknik Parametreler

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `POLL_INTERVAL_MS` | 500ms | Ekran kontrol aralığı |
| `CHANGE_THRESHOLD` | 15.0 | Pixel fark eşiği |
| `AUTO_COOLDOWN_S` | 6.0s | Cevap sonrası bekleme |
| `IMG_MAX_WIDTH` | 768px | Gönderilen görüntü max genişliği |
| `OPTION_POLL_MS` | 400ms | Şık yükleme kontrol aralığı |
| `OPTION_TIMEOUT_S` | 8.0s | Şık bekleme zaman aşımı |
| `MIN_REQUEST_INTERVAL_S` | 2s | API istekleri arası minimum süre |
| `temperature` | 0.0 | Deterministik çıktı |
| `thinking_budget` | 0 | Düşünme süresi yok |

---

## 📁 Dosya Yapısı

```
kahoot/
├── KahootBotGUI.py      # Masaüstü uygulama (Tkinter GUI + bot)
├── kahoot_config.json    # Kalibrasyon ve API ayarları (otomatik kaydedilir)
├── docs/                 # 📱 Mobil PWA (GitHub Pages)
│   ├── index.html        # Tek dosyalık tam PWA
│   ├── manifest.json     # PWA manifest
│   └── sw.js             # Service Worker (offline + kurulum)
└── README.md             # Bu dosya
```

---

## 🔑 API Key Stratejisi

Bot, rate-limit sorunlarını aşmak için **multi-key round-robin rotasyon** kullanır:

```
Key1 → Key2 → Key3 → Key4 → Key5 → Key6 → Key1 → ...
```

Her istek farklı bir key üzerinden gider. Bu sayede tek key'e düşen yük azalır ve dakikadaki istek limiti pratikte `N × limit` olur.

> ⚠️ `kahoot_config.json` dosyasındaki API key'leri commit etmeden önce temizle!

---

## 🏗 Mimari

```
┌─────────────────────────────────────────────┐
│                  GUI (Tkinter)               │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Bağlantı │  │Kalibrasyon│  │ Turbo Mod │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │              │        │
│  ┌────▼──────────────▼──────────────▼────┐   │
│  │          Olay Döngüsü (Poll)          │   │
│  │  1. Ekran değişikliği algıla          │   │
│  │  2. Şıkların yüklenmesini bekle       │   │
│  │  3. Görüntüyü optimize et             │   │
│  │  4. Gemini'ye gönder (key rotasyon)   │   │
│  │  5. Renk çıktısını parse et           │   │
│  │  6. pyautogui ile otomatik tıkla      │   │
│  └───────────────────────────────────────┘   │
│                                              │
│  Kaynaklar: ImageGrab | cv2.VideoCapture     │
│  AI Motor:  google-genai (Gemini Vision)     │
└─────────────────────────────────────────────┘
```

---

## ⏱ Performans

| Metrik | Değer |
|--------|-------|
| Gemini yanıt süresi | ~2-4 saniye |
| Otomatik tıklama | <10ms |
| Toplam gecikme (algılama → tıklama) | ~3-5 saniye |
| Başarı oranı (doğru renk) | ~%85-95 |

---

## 📱 Mobil Versiyon (PWA)

Bilgisayar yerine **sadece telefonla** yarışmak için mobil PWA versiyonu `docs/` klasöründedir.

### Özellikler
- 📷 **Arka kamera** ile projektör/ekrandaki soruyu yakalar
- 🤖 **Gemini Vision API** ile cevabı analiz eder
- 🎨 **Tam ekran renk gösterimi** — cevap rengi ekranı kaplar
- 📳 **Titreşim geri bildirimi** — cevap geldiğinde telefon titrer
- 🔄 **Oto-Mod** — ekran değişikliğini algılayıp otomatik analiz eder
- 🔑 **Multi-key rotasyon** — masaüstü versiyondaki gibi round-robin
- 📱 **Split-screen uyumlu** — Samsung'da üstte bot, altta Kahoot

### Kullanım (Split-Screen)
1. Telefona Kahoot'u aç (Chrome)
2. PWA'yı aç (Samsung Internet veya başka tarayıcı)
3. Samsung split-screen: **bot üstte, Kahoot altta**
4. Telefonu projektöre çevir
5. **📸 butona bas** veya **Oto-Mod aç**
6. Cevap rengi üst yarıda görünür → alttan Kahoot'ta bas

### Deploy (GitHub Pages)
```bash
git add docs/
git commit -m "Add mobile PWA"
git push origin main
```
GitHub → **Settings** → **Pages** → Source: `main` / `/docs` → **Save**

Birkaç dakika sonra erişim: `https://ruzorin.github.io/BootKahoot/`

> 💡 Telefonda bu URL'yi aç → **Ana Ekrana Ekle** ile PWA olarak kur

---

## ⚠️ Sorumluluk Reddi

Bu proje **eğitim ve araştırma amaçlıdır**. Kahoot kullanım koşullarına ve yarışma kurallarına uygunluk kullanıcının sorumluluğundadır. Yazarlar herhangi bir olumsuz sonuçtan sorumlu tutulamaz.

---

## 📜 Lisans

MIT License — Detaylar için `LICENSE` dosyasına bakın.

---

<p align="center">
  <b>🤖 BootKahoot — DAÜ AI Summit '26</b><br>
  <i>Staj fırsatını yakala, yapay zeka seni tıklasın.</i>
</p>
