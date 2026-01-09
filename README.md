# KeyMapper – Çoklu Klavye ve Fare Tuş Eşleme Aracı

KeyMapper, birden fazla klavye ve fare cihazından gelen girdileri  
Windows uygulamaları, medya kontrolleri veya yürütülebilir dosyalar ile eşleştirmenizi sağlayan modern ve kullanımı kolay bir tuş eşleme aracıdır.

---

## 🚀 Özellikler

### ✅ Çoklu Klavye Desteği
- Her klavye **benzersiz olarak tanımlanır**
  - HID klavyeler: `VID/PID`
  - ACPI klavyeler: `ACPI hash`
- Aynı tuş, **farklı klavyelerde farklı işlemler** tetikleyebilir
- Windows **Raw Input API** kullanır
- Sistem genelinde **düşük gecikmeli** tuş yakalama

---

### 🖱️ Fare Desteği
- Fare butonları:
  - Sol Tuş
  - Sağ Tuş
  - Orta Tuş
- Fare tekerleği:
  - Yukarı
  - Aşağı
- **Debounce sistemi** ile yanlış tetiklemeler engellenir

---

### 🎯 Tetikleyici Seçenekleri

#### 🔑 Tuş Yakalama
- Klavye veya fareden gelen herhangi bir tuş dinlenebilir
- Cihaza özel tuş eşleme yapılabilir

#### 🪟 Windows Uygulamaları
- Başlat menüsündeki uygulamalar listelenir
- Arama kutusu ile hızlı seçim yapılır

#### 📁 Manuel Dosya Çalıştırma
- `.exe` veya herhangi bir dosya seçilebilir
- Seçilen dosya tetikleyici ile çalıştırılır

#### 🎵 Medya Kontrolleri
- 🔊 Ses Aç (Volume Up)
- 🔉 Ses Kıs (Volume Down)
- 🔇 Sessiz (Mute)
- ▶️ Oynat / ⏸️ Duraklat
- ⏭️ Sonraki Parça
- ⏮️ Önceki Parça

---

## 📦 Kurulum

### Gereksinimler
- Windows 10 / Windows 11
- Python 3.8 veya üzeri
- `klavye.dll` dosyası

---

\### 🔧 Adım Adım Kurulum

\#### 1️⃣ Python Paketlerini Kur

\`\`\`bash

pip install PyQt6 pynput pillow pystray

2️⃣ DLL Dosyasını Hazırla

klvye123\_dll.cpp dosyasını derleyerek klavye.dll oluşturun

veya

Hazır klavye.dll dosyasını proje dizinine kopyalayın

3️⃣ Uygulamayı Çalıştır

bash

Kodu kopyala

python keymapper.py

🖥️ Arayüz Kullanımı

Sol Panel – Ayarlar

Tetikleyici Tuş

“Tuş Yakalamayı Başlat” butonu ile klavye/fare tuşu seçilir

Windows Uygulaması Seç

Arama yaparak uygulama bulunur

Manuel Dosya / Medya

.exe dosyası seçilebilir

veya medya kontrolü atanabilir

Eşlemeyi Sisteme Ekle

Ayar kaydedilir

Sağ Panel – Aktif Atamalar

Tüm aktif tuş eşlemeleri listelenir

Bir eşlemeyi silmek için çift tıklayın

Tümünü Sil ile bütün atamalar temizlenir

🔧 Teknik Detaylar

DLL Yapısı

cpp

Kodu kopyala

// Ana fonksiyonlar

Initialize(KeyCallback cb); // Callback fonksiyonunu ayarlar

StartListener(); // Tuş dinleyiciyi başlatır

StopListener(); // Tuş dinleyiciyi durdurur

Tuş Tanımlama Sistemi

HID Klavyeler

vid\_XXXX&pid\_YYYY

ACPI Klavyeler

ACPI\_DEVICE\_XXXX (hash)

Fare Olayları

Mouse\_Left

Mouse\_Right

Mouse\_Middle

Mouse\_Wheel\_Up

Mouse\_Wheel\_Down

💾 Veri Depolama

Tüm ayarlar keymap\_gui.json dosyasında saklanır

JSON içeriği:

Cihaz ID

Tuş kodu

Hedef eylem (uygulama / dosya / medya)

⚙️ Yapılandırma

Debounce Süreleri

python

Kodu kopyala

DEBOUNCE\_SEC = 0.4 # Normal tuşlar

MOUSE\_WHEEL\_SEC = 0.12 # Fare tekerleği

Medya Tuş Kodları

python

Kodu kopyala

VK\_VOLUME\_UP = 0xAF

VK\_VOLUME\_DOWN = 0xAE

VK\_VOLUME\_MUTE = 0xAD

VK\_MEDIA\_PLAY\_PAUSE = 0xB3

VK\_MEDIA\_NEXT\_TRACK = 0xB0

VK\_MEDIA\_PREV\_TRACK = 0xB1

📌 Notlar

Uygulama sistem genelinde çalışır

Yönetici izni gerekebilir

DLL ve Python dosyaları aynı dizinde olmalıdır
