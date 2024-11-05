from flask import Flask, render_template, request, jsonify
import requests
from lxml import html
import json
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import threading
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

app = Flask(__name__)

# .env dosyasını yükle
load_dotenv()
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Log dosyasını ve formatını ayarlayın
log_file_path = "logs/app.log"  # Log dosyasının yolu

# File Handler
file_handler = RotatingFileHandler(log_file_path, maxBytes=100000, backupCount=10)
file_handler.setLevel(logging.INFO)  # Log seviyesini ayarlayın
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console Handler
console_handler = logging.StreamHandler()  # Konsola yazmak için
console_handler.setLevel(logging.INFO)  # Log seviyesini ayarlayın
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# Logger'ı ayarlayın
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Tüm logları almak için seviyeyi ayarlayın
logger.addHandler(file_handler)  # Dosya handler'ını ekleyin
logger.addHandler(console_handler)  # Konsol handler'ını ekleyin

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def setup_session():
    logger.info("Oturum kurulmaya başlanıyor")
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    )
    logger.info("Oturum başarıyla kuruldu")
    return session


def send_telegram_message(message):
    logger.info(f"Telegram mesajı gönderiliyor: {message}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        logger.error(f"Telegram mesajı gönderilirken hata oluştu: {response.text}")
    else:
        logger.info("Telegram mesajı başarıyla gönderildi.")


def scrape_price(session, url):
    logger.info(f"Fiyat çekiliyor: {url}")
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        element = tree.xpath('//*[@id="pd_v8"]/div[3]/span[1]/span')
        if element:
            price = element[0].text_content().strip()
            logger.info(f"Fiyat başarıyla çekildi: {url} - {price}")
            return price
        else:
            logger.warning(f"Fiyat bulunamadı: {url}")
            return None
    except Exception as e:
        logger.error(f"Hata oluştu {url} için: {e}")
        return None


def load_data():
    logger.info("Fiyat verileri yükleniyor")
    try:
        with open("price_data.json", "r") as f:
            data = json.load(f)
            logger.info(f"{len(data)} ürün verisi başarıyla yüklendi")
            return data
    except FileNotFoundError:
        logger.warning("price_data.json dosyası bulunamadı, boş sözlük döndürülüyor")
        return {}


def save_data(data):
    logger.info(f"{len(data)} ürün verisi kaydediliyor")
    with open("price_data.json", "w") as f:
        json.dump(data, f, indent=2)
    logger.info("Fiyat verileri başarıyla kaydedildi")


def check_prices():
    logger.info("Fiyat kontrol döngüsü başlatılıyor")
    while True:
        urls = load_urls()  # Assuming this returns a list of dicts with 'url' and 'website'
        data = load_data()

        for entry in urls:
            url = entry["url"]
            website = entry["website"]  # Get the associated website
            session = setup_session()
            current_price = scrape_price(session, url)

            if current_price:
                pure_price = current_price  # Adjust parsing if necessary
                current_price = current_price.split(",")[0]  # Adjust parsing if necessary
                current_price = current_price.replace(".", "")
                print(current_price)
                if url not in data:
                    data[url] = {"website": website, "price": current_price, "last_updated": str(datetime.now())}
                    logger.info(f"Yeni ürün eklendi: {url} - Fiyat: {current_price}")
                    send_telegram_message(f"Yeni ürün eklendi: {url} - Fiyat: {pure_price}")
                elif data[url]["price"] > current_price:
                    logger.info(f"Fiyat değişti: {url}")
                    logger.info(f"Eski fiyat: {data[url]['price']}, Yeni fiyat: {pure_price}")
                    send_telegram_message(f"Fiyat değişti: {url}\nEski fiyat: {data[url]['price']}, Yeni fiyat: {pure_price}")
                    data[url]["price"] = current_price  # Update the price
                    data[url]["last_updated"] = str(datetime.now())  # Update timestamp
                # else:
                #     logger.info(f"Fiyat aynı veya yüksek: {current_price}")
                # data[url]["price"] = current_price
                # data[url]["last_updated"] = str(datetime.now())  # Update the last checked time
            else:
                logger.warning(f"Fiyat alınamadı: {url}")

        save_data(data)
        logger.info("Fiyat kontrol döngüsü tamamlandı. 5 dakika bekleniyor.")
        time.sleep(300)  # 5 dakika bekle


@app.route("/")
def index():
    logger.info("Ana sayfa isteği alındı")
    urls = load_urls()
    with open("price_data.json", "r") as f:
        pricedata = json.load(f)
    print(pricedata)
    return render_template("index.html", urls=urls, pricedata=pricedata)


def load_urls():
    try:
        with open("urls.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


@app.route("/add_url", methods=["POST"])
def add_url():
    url = request.form["url"]
    website = request.form["website"]  # Get the website from the form data
    logger.info(f"Yeni URL ekleme isteği: {url} ({website})")

    urls = load_urls()

    # Check if the URL already exists
    if url not in [item["url"] for item in urls]:
        new_entry = {"website": website, "url": url}
        urls.append(new_entry)
        save_urls(urls)
        logger.info(f"Yeni URL eklendi: {new_entry}")
    else:
        logger.info(f"URL zaten mevcut: {url}")

    return jsonify(success=True, urls=urls)


def save_urls(urls):
    logger.info(f"{len(urls)} URL kaydediliyor")
    with open("urls.json", "w") as f:
        json.dump(urls, f, indent=2)
    logger.info("URL'ler başarıyla kaydedildi")


@app.route("/remove_url", methods=["POST"])
def remove_url():
    url_to_remove = request.form["url"]
    print(url_to_remove)
    logger.info(f"URL silme isteği: {url_to_remove}")

    # Load the current list of URLs
    urls = load_urls()

    # Log the current URLs before removal
    logger.info(f"Mevcut URL'ler: {urls}")

    # Remove the URL from the list
    updated_urls = [entry for entry in urls if entry["url"] != url_to_remove]

    # Log the URLs after attempted removal
    logger.info(f"Güncellenmiş URL'ler: {updated_urls}")

    # Save the updated list of URLs
    save_urls(updated_urls)

    return jsonify(success=True, urls=updated_urls)


if __name__ == "__main__":
    logger.info("Uygulama başlatılıyor")
    threading.Thread(target=check_prices, daemon=True).start()
    app.run(debug=True, host="0.0.0.0", port=5005)
