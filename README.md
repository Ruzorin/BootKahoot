# 🚀 BootKahoot — AI-Powered Kahoot Bot

> Gemini Vision destekli, tam otomatik Kahoot yanıtlama sistemi. Masaüstü ve **mobil (PWA)** desteğiyle her yerden kullanılabilir.

---

## ⚡ Özellikler

### Çekirdek
- **Gemini Vision AI** — Ekran görüntüsünü veya kamera karesini analiz ederek doğru cevabın rengini belirler
- **Tam Otomatik Mod (Turbo)** — Ekran değişikliğini algılar, şıkları bekler, cevabı verir
- **Manuel Mod** — `K` tuşuyla tek seferde tetikleme
- **📱 Mobil PWA** — Telefon kamerasıyla projektöre/ekrana bakarak çalışır, split-screen uyumlu

### Hız & Güvenilirlik
- **Multi-Key Rotasyon** — Birden fazla API key ile round-robin; rate-limit bypass
- **Pre-warm Bağlantı** — İlk soruda gecikme olmaz
- **Thinking Budget = 0** — Gemini düşünme aşaması kapalı, minimum gecikme
- **Görüntü Optimizasyonu** — Max 768px, JPEG %85 sıkıştırma

### Algılama
- **2 Aşamalı Değişiklik Algılama** — Soru geldi → şıklar yüklendi → gönder
- **Pixel-Level Diff** — 64×64 küçültülmüş kareler üzerinden fark hesabı
- **False-Positive Koruması** — Soru olmayan ekranlar otomatik atlanır
- **Cooldown** — Çift tetikleme önlenir

### Giriş Kaynakları
- **Ekran Yakalama** — Belirlenen alan üzerinden `ImageGrab`
- **Kamera (DroidCam)** — Telefonu webcam olarak kullan
- **📱 Mobil Kamera** — Arka kamera ile projektörü/ekranı tara

---

## 🛠 Kurulum

### Masaüstü (Windows)

```bash
pip install google-genai pyautogui keyboard pillow opencv-python
```

```bash
# Yönetici (Administrator) olarak çalıştır
python KahootBotGUI.py
```

### 📱 Mobil (PWA)

Tarayıcıdan aç → **Ana Ekrana Ekle** ile kur:

🔗 **https://ruzorin.github.io/BootKahoot/**

> Kurulum gerekmez. HTTPS üzerinden kamera erişimi otomatik sağlanır.

---

## 📖 Kullanım

### Masaüstü

1. **API key** gir (virgülle ayırarak birden fazla key ekle)
2. **Model** seç → `gemini-2.5-flash` önerilir
3. **⚡ BAĞLAN**
4. **Alan Belirle** — Kahoot ekranını kapsayan dikdörtgeni çiz
5. **Butonları Eşleştir** — Sırayla tıkla: 🔴 → 🔵 → 🟡 → 🟢
6. `K` ile manuel veya **Turbo Mod** ile tam otomatik çalıştır

### 📱 Mobil

1. PWA'yı aç → API key gir → **BAĞLAN & BAŞLA**
2. Kamerayı Kahoot ekranına/projektöre çevir
3. **📸** ile manuel tara veya **Oto-Mod** aç
4. Cevap rengi tüm ekranı kaplar + telefon titrer

> 💡 **Split-Screen:** Samsung'da bot üstte, Kahoot altta. Cevap gelince alttan bas.

---

## ⚙️ Parametreler

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `POLL_INTERVAL_MS` | 500ms | Ekran kontrol aralığı |
| `CHANGE_THRESHOLD` | 15.0 | Pixel fark eşiği |
| `AUTO_COOLDOWN_S` | 6.0s | Cevap sonrası bekleme |
| `IMG_MAX_WIDTH` | 768px | Gönderilen görüntü max genişliği |
| `OPTION_TIMEOUT_S` | 8.0s | Şık bekleme zaman aşımı |
| `temperature` | 0.0 | Deterministik çıktı |
| `thinking_budget` | 0 | Düşünme süresi yok |

---

## 📁 Dosya Yapısı

```
kahoot/
├── KahootBotGUI.py      # Masaüstü uygulama (Tkinter GUI)
├── kahoot_config.json    # Ayarlar (otomatik kaydedilir)
├── docs/                 # 📱 Mobil PWA
│   ├── index.html        # Tek dosyalık tam PWA
│   ├── manifest.json     # PWA manifest
│   └── sw.js             # Service Worker
└── README.md
```

---

## 🔑 API Key Stratejisi

Birden fazla Gemini API key'i virgülle ayrılarak girilir. Bot, round-robin ile her istekte farklı key kullanır:

```
Key1 → Key2 → Key3 → ... → Key1 → ...
```

Rate-limit pratikte `N × limit` olur. Key'ler [Google AI Studio](https://aistudio.google.com/)'dan ücretsiz alınabilir.

---

## 🏗 Mimari

```
┌──────────────────────────────────────────┐
│          Masaüstü (Tkinter GUI)          │
│  Ekran Yakalama / DroidCam → Gemini →   │
│  Renk Parse → pyautogui ile otomatik tık │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│          Mobil PWA (Tarayıcı)            │
│  Arka Kamera → Gemini REST API →        │
│  Tam ekran renk gösterimi + titreşim     │
└──────────────────────────────────────────┘
```

---

## ⏱ Performans

| Metrik | Değer |
|--------|-------|
| Gemini yanıt süresi | ~2-4 saniye |
| Otomatik tıklama (masaüstü) | <10ms |
| Toplam gecikme | ~3-5 saniye |

---

## 📜 Lisans

MIT License

---

<p align="center">
  <b>🤖 BootKahoot</b><br>
  <i>Yapay zeka seni tıklasın.</i>
</p>
