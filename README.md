# Fiyat Takip Scripti

Bu Python scripti, belirli ürünlerin fiyatlarını düzenli olarak takip etmek ve fiyat değişikliklerini raporlamak için tasarlanmıştır.

## Özellikler

- Birden fazla URL'den fiyat takibi
- Düzenli aralıklarla otomatik kontrol (varsayılan: 5 dakika)
- Fiyat değişikliklerini konsola raporlama
- Fiyat verilerini JSON dosyasında saklama

## Gereksinimler

Script'i çalıştırmak için aşağıdaki Python kütüphanelerine ihtiyacınız vardır:

- requests
- lxml

Bu kütüphaneleri şu komutla yükleyebilirsiniz:

```
pip install requests lxml
```

## Kullanım

1. Scripti bilgisayarınıza indirin (örneğin: `price_tracker.py` olarak kaydedin).

2. Script içindeki `urls` listesine takip etmek istediğiniz ürünlerin URL'lerini ekleyin:

   ```python
   urls = [
       "https://www.akakce.com/mouse/en-ucuz-razer-deathadder-essential-optik-kablolu-oyuncu-mouse-fiyati,335153583.html",
       # Diğer URL'leri buraya ekleyin
   ]
   ```

3. Terminali veya komut istemcisini açın ve scriptin bulunduğu dizine gidin.

4. Aşağıdaki komutu çalıştırarak scripti başlatın:

   ```
   python price_tracker.py
   ```

5. Script çalışmaya başlayacak ve her 5 dakikada bir fiyatları kontrol edecektir.

## Çıktılar

- Script, fiyat değişikliklerini konsola yazdıracaktır.
- Tüm fiyat verileri `price_data.json` dosyasında saklanacaktır.

## Önemli Notlar

- Script, siz manuel olarak durdurana kadar (Ctrl+C tuşları ile) çalışmaya devam edecektir.
- Çok sık istek göndermek, web sitesinin IP adresinizi engellemesine neden olabilir. Gerekirse kontrol aralığını artırın.
- Web sitesinin yapısı değişirse, script içindeki XPath'i güncellemeniz gerekebilir.

## Özelleştirme

- Kontrol aralığını değiştirmek için, `time.sleep(300)` satırındaki 300 değerini istediğiniz saniye cinsinden değerle değiştirin.
- Farklı bir XPath kullanmanız gerekiyorsa, `scrape_price` fonksiyonu içindeki XPath sorgusunu güncelleyin.

## Sorun Giderme

Eğer script çalışırken hatalarla karşılaşırsanız:

1. İnternet bağlantınızı kontrol edin.
2. Gerekli kütüphanelerin doğru şekilde yüklendiğinden emin olun.
3. URL'lerin doğru ve erişilebilir olduğundan emin olun.
4. Web sitesinin yapısının değişip değişmediğini kontrol edin ve gerekirse XPath'i güncelleyin.

Bu README dosyası, scriptin nasıl kullanılacağı ve özelleştirileceği konusunda temel bilgileri içermektedir. Herhangi bir sorunuz veya öneriniz varsa, lütfen iletişime geçmekten çekinmeyin.