# 1. Base image olarak Python 3.9 kullanıyoruz
FROM python:3.9-slim

# 2. Çalışma dizinini ayarla
WORKDIR /app

# 3. Gerekli bağımlılıkları yüklemek için requirements.txt dosyasını kopyala
COPY requirements.txt .

# 4. Bağımlılıkları yükle
RUN pip install --no-cache-dir -r requirements.txt

# 5. Uygulama dosyalarını kopyala
COPY . .

# 6. Uygulamanın Flask ortam değişkenini belirle
ENV FLASK_APP=app.py

# 7. Uygulamanın çalışacağı portu belirt
EXPOSE 5005

# 8. Uygulamanın Docker container başlatıldığında nasıl çalışacağını tanımla
CMD ["python", "app.py"]
