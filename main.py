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
from bs4 import BeautifulSoup
import random

file_path = "user-agents.txt"


def setup_session():
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["HEAD", "GET", "OPTIONS"])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {"User-Agent": getUA()}
        # {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    )
    return session


def getUA():
    random_line_number = random.randint(1, 1000)

    with open(file_path, "r") as file:
        lines = file.readlines()
        user_agent = lines[random_line_number - 1].strip()  # \n karakterini temizlemek için strip() kullanıyoruz
        print(user_agent)
        return user_agent  # Satırdaki \n ve boşluk karakterlerini kaldırarak döndürüyoruz


session = setup_session()

url = "https://www.instacart.com/store/foodsco-delivery-now/collections/2605-berries-citrus"

response = session.get(url, timeout=10)
response.raise_for_status()

soup = BeautifulSoup(response.content, "html.parser")

titles = soup.find_all("span", {"class": "e-1qkvt8e"})
for i in titles:
    print(i.text)
