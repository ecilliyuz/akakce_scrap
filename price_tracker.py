import requests
from lxml import html
import time
import json
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def setup_session():
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    )
    return session


def scrape_price(session, url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        element = tree.xpath('//*[@id="pd_v8"]/div[3]/span[1]/span')
        if element:
            return element[0].text_content().strip()
        else:
            print(f"Fiyat bulunamadı: {url}")
            return None
    except Exception as e:
        print(f"Hata oluştu {url} için: {e}")
        return None


def load_data():
    try:
        with open("price_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open("price_data.json", "w") as f:
        json.dump(data, f, indent=2)


def check_prices(urls):
    session = setup_session()
    data = load_data()

    for url in urls:
        current_price = scrape_price(session, url)
        if current_price:
            if url not in data:
                data[url] = {"price": current_price, "last_updated": str(datetime.now())}
                print(f"Yeni ürün eklendi: {url} - Fiyat: {current_price}")
            elif data[url]["price"] != current_price:
                print(f"Fiyat değişti: {url}")
                print(f"Eski fiyat: {data[url]['price']}, Yeni fiyat: {current_price}")
                data[url] = {"price": current_price, "last_updated": str(datetime.now())}
            else:
                data[url]["last_updated"] = str(datetime.now())

    save_data(data)


def main():
    urls = [
        "https://www.akakce.com/mouse/en-ucuz-razer-deathadder-essential-optik-kablolu-oyuncu-mouse-fiyati,335153583.html",
        "https://www.akakce.com/mouse/en-ucuz-razer-cobra-rz01-04650100-r3m1-optik-kablolu-fiyati,223063350.html",
        # Diğer URL'leri buraya ekleyin
    ]

    while True:
        print("Fiyatlar kontrol ediliyor...")
        check_prices(urls)
        print("Kontrol tamamlandı. 5 dakika bekleniyor...")
        time.sleep(300)  # 5 dakika bekle


if __name__ == "__main__":
    main()
