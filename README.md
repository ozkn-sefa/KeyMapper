# Klavye & Fare Tuş Eşleştirici (KeyMapper)

Klavyeden veya fareden herhangi bir tuş/fare hareketini yakalayıp  
Windows uygulamalarını açabilen, medya tuşlarını simüle edebilen **hafif** bir araç.

**Özellikler**
- Birden fazla klavye/fare cihazını ayrı ayrı tanır  
- Store uygulamaları + klasik .exe dosyaları + medya kontrolleri  
- Sistem tepsisinde (tray) çalışır, arka planda kalır  
- Debounce (çift basım önleme) özelliği  
- Basit, modern, karanlık tema arayüzü


## Nasıl Kullanılır?

1. "TUŞ YAKALAMAYI BAŞLAT" butonuna basın
2. Klavyeden veya fareden kullanmak istediğiniz tuşa basın
3. Aşağıdaki 3 seçenekten birini seçin:
   - Microsoft Store uygulaması
   - Herhangi bir .exe dosyası
   - Medya kontrolü (ses aç/kapa, sonraki/önceki, çalma/durdur)
4. **EŞLEMEYİ SİSTEME EKLE** butonuna basın

Artık seçtiğiniz tuşa her bastığınızda ilgili işlem gerçekleşecek.
## DLL
Normalde Windows, bilgisayara takılı 5 farklı klavye de olsa hepsini tek bir giriş gibi görür. Bu kodun asıl amacı, gelen tuş vuruşunun fiziksel olarak hangi cihazdan (VID/PID kimliğiyle) geldiğini tespit etmektir.

Benzersiz Cihaz Kimliği (GetDeviceUniqueId): Kodun en büyük parçası, klavyenin donanım kimliğini (Vendor ID ve Product ID) okumaya ayrılmıştır. Bu sayede "Klavye A" ile "Klavye B" birbirinden ayırt edilebilir.

JSON Veri Yapısı: Yakalanan tuş ve cihaz bilgisi, modern yazılımların (örneğin bir oyun motoru veya bir otomasyon aracı) kolayca okuyabileceği { "device": "...", "vkey": ... } formatına dönüştürülür.

Arka Plan Dinleyicisi: Kod, kullanıcıyı engellemeden veya bilgisayarı yavaşlatmadan mesajları izleyen gizli bir pencere (HWND_MESSAGE) üzerinden çalışır.

Neden Bir Keylogger Değildir?
Bu kod, kötü niyetli bir yazılımın sahip olması gereken karakteristik özelliklerin hiçbirini taşımamaktadır:

Veri Depolama ve İletim Yok: Kodda yakalanan tuşları bir dosyaya kaydetme (log tutma) veya internet üzerinden uzak bir sunucuya gönderme fonksiyonu bulunmamaktadır. Veri sadece o an çalışan ana uygulamaya (callback aracılığıyla) anlık olarak iletilir.

Sistem Geneli Gizlilik Yok: Kod, kendini sistemden gizlemeye çalışmaz. Standart Windows API'lerini kullanır.

Sınırlı Veri Takibi: Kod sadece tuşa basılma anını (keydown) yakalar. Şifre çalmak için gereken karmaşık mantık dizilerine (shift/alt kombinasyonları, büyük-küçük harf ayrımı vb.) sahip değildir.

Kontrollü Çalışma: StartListener ve StopListener fonksiyonları ile sadece kullanıcı veya ana yazılım istediği zaman aktif olur.

## Kısayollar & Medya Tuşları

| Eylem               | Kısaltma   |
|---------------------|------------|
| Ses açma            | VOL_UP     |
| Ses kısma           | VOL_DOWN   |
| Sessize alma/açma   | MUTE       |
| Çalma/Durdur        | PLAY_PAUSE |
| Sonraki parça       | NEXT       |
| Önceki parça        | PREV       |

## Derleme (Kaynak Kodundan)

```bash
# Gereksinimler
pip install pyqt6 pynput pillow pystray
