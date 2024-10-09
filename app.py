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
from dotenv import load_dotenv

app = Flask(__name__)

# .env dosyasını yükle
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def setup_session():
    logging.info("Oturum kurulmaya başlanıyor")
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    )
    logging.info("Oturum başarıyla kuruldu")
    return session


def send_telegram_message(message):
    logging.info(f"Telegram mesajı gönderiliyor: {message}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        logging.error(f"Telegram mesajı gönderilirken hata oluştu: {response.text}")
    else:
        logging.info("Telegram mesajı başarıyla gönderildi.")


def scrape_price(session, url):
    logging.info(f"Fiyat çekiliyor: {url}")
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        tree = html.fromstring(response.content)
        element = tree.xpath('//*[@id="pd_v8"]/div[3]/span[1]/span')
        if element:
            price = element[0].text_content().strip()
            logging.info(f"Fiyat başarıyla çekildi: {url} - {price}")
            return price
        else:
            logging.warning(f"Fiyat bulunamadı: {url}")
            return None
    except Exception as e:
        logging.error(f"Hata oluştu {url} için: {e}")
        return None


def load_urls():
    logging.info("URL'ler yükleniyor")
    try:
        with open("urls.json", "r") as f:
            urls = json.load(f)
            logging.info(f"{len(urls)} URL başarıyla yüklendi")
            return urls
    except FileNotFoundError:
        logging.warning("urls.json dosyası bulunamadı, boş liste döndürülüyor")
        return []


def save_urls(urls):
    logging.info(f"{len(urls)} URL kaydediliyor")
    with open("urls.json", "w") as f:
        json.dump(urls, f, indent=2)
    logging.info("URL'ler başarıyla kaydedildi")


def load_data():
    logging.info("Fiyat verileri yükleniyor")
    try:
        with open("price_data.json", "r") as f:
            data = json.load(f)
            logging.info(f"{len(data)} ürün verisi başarıyla yüklendi")
            return data
    except FileNotFoundError:
        logging.warning("price_data.json dosyası bulunamadı, boş sözlük döndürülüyor")
        return {}


def save_data(data):
    logging.info(f"{len(data)} ürün verisi kaydediliyor")
    with open("price_data.json", "w") as f:
        json.dump(data, f, indent=2)
    logging.info("Fiyat verileri başarıyla kaydedildi")


def check_prices():
    logging.info("Fiyat kontrol döngüsü başlatılıyor")
    while True:
        session = setup_session()
        urls = load_urls()
        data = load_data()

        for url in urls:
            current_price = scrape_price(session, url)
            if current_price:
                if url not in data:
                    data[url] = {"price": current_price, "last_updated": str(datetime.now())}
                    logging.info(f"Yeni ürün eklendi: {url} - Fiyat: {current_price}")
                    send_telegram_message(f"Yeni ürün eklendi: {url} - Fiyat: {current_price}")
                elif data[url]["price"] != current_price:
                    logging.info(f"Fiyat değişti: {url}")
                    logging.info(f"Eski fiyat: {data[url]['price']}, Yeni fiyat: {current_price}")
                    send_telegram_message(f"Fiyat değişti: {url}\nEski fiyat: {data[url]['price']}, Yeni fiyat: {current_price}")
                    data[url] = {"price": current_price, "last_updated": str(datetime.now())}
                else:
                    data[url]["last_updated"] = str(datetime.now())
            else:
                logging.warning(f"Fiyat alınamadı: {url}")

        save_data(data)
        logging.info("Fiyat kontrol döngüsü tamamlandı. 5 dakika bekleniyor.")
        time.sleep(300)  # 5 dakika bekle


@app.route("/")
def index():
    logging.info("Ana sayfa isteği alındı")
    urls = load_urls()
    return render_template("index.html", urls=urls)


@app.route("/add_url", methods=["POST"])
def add_url():
    url = request.form["url"]
    logging.info(f"Yeni URL ekleme isteği: {url}")
    urls = load_urls()
    if url not in urls:
        urls.append(url)
        save_urls(urls)
        logging.info(f"Yeni URL eklendi: {url}")
    else:
        logging.info(f"URL zaten mevcut: {url}")
    return jsonify(success=True, urls=urls)


@app.route("/remove_url", methods=["POST"])
def remove_url():
    url = request.form["url"]
    logging.info(f"URL kaldırma isteği: {url}")
    urls = load_urls()
    if url in urls:
        urls.remove(url)
        save_urls(urls)
        logging.info(f"URL kaldırıldı: {url}")
    else:
        logging.warning(f"Kaldırılmak istenen URL bulunamadı: {url}")
    return jsonify(success=True, urls=urls)


if __name__ == "__main__":
    logging.info("Uygulama başlatılıyor")
    threading.Thread(target=check_prices, daemon=True).start()
    app.run(debug=True, host="0.0.0.0", port=5005)
