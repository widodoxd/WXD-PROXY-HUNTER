FROM python:3.10-slim

# Install wget
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Requirements & Install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download Database GeoIP
RUN wget -O /app/GeoLite2-Country.mmdb "https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb"

# Copy SELURUH isi folder (termasuk modules)
COPY . .

# Jalankan main.py
CMD ["python", "main.py"]
