#!/data/data/com.termux/files/usr/bin/bash
# BootKahoot Termux Kurulum Scripti
# Samsung M52'de çalıştır

echo "🚀 BootKahoot Termux Kurulumu"
echo "=============================="

# Paketleri kur
pkg update -y
pkg install -y python android-tools

# Python paketlerini kur
pip install requests pillow

# Termux:API erişimi
echo ""
echo "⚠️  YAPMAN GEREKENLER:"
echo "1. F-Droid'den 'Termux:API' uygulamasını kur"
echo "2. Ayarlar → Geliştirici Seçenekleri → Kablosuz Hata Ayıklama → AÇ"
echo "3. 'Eşleştirme kodu ile cihaz eşleştir' e bas"
echo "4. Port ve kodu not al, sonra şunu çalıştır:"
echo "   adb pair localhost:PORT KOD"
echo "5. Sonra bağlan:"
echo "   adb connect localhost:PORT"
echo "6. Test et:"
echo "   adb shell input tap 540 1200"
echo ""
echo "Kurulum tamam! Şimdi çalıştır:"
echo "   python kahoot_termux.py"
