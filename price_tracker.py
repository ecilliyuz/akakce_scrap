from flask import Flask, render_template, request, jsonify
import requests
from lxml import html
import json
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import threading

app = Flask(__name__)


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


def load_urls():
    try:
        with open("urls.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_urls(urls):
    with open("urls.json", "w") as f:
        json.dump(urls, f, indent=2)


def load_data():
    try:
        with open("price_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open("price_data.json", "w") as f:
        json.dump(data, f, indent=2)


def check_prices():
    while True:
        session = setup_session()
        urls = load_urls()
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
            else:
                print(f"Fiyat alınamadı: {url}")

        save_data(data)
        time.sleep(300)  # 5 dakika bekle


@app.route("/")
def index():
    urls = load_urls()
    return render_template("index.html", urls=urls)


@app.route("/add_url", methods=["POST"])
def add_url():
    url = request.form["url"]
    urls = load_urls()
    if url not in urls:
        urls.append(url)
        save_urls(urls)
    return jsonify(success=True, urls=urls)


@app.route("/remove_url", methods=["POST"])
def remove_url():
    url = request.form["url"]
    urls = load_urls()
    if url in urls:
        urls.remove(url)
        save_urls(urls)
    return jsonify(success=True, urls=urls)


if __name__ == "__main__":
    threading.Thread(target=check_prices, daemon=True).start()
    app.run(debug=True)
