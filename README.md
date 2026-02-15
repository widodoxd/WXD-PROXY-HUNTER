**WXD Proxy Hunter** adalah bot Telegram *high-performance* berbasis Python yang dirancang untuk mencari, memvalidasi, dan mengklasifikasikan proxy secara otomatis.

Dibangun dengan arsitektur **Asynchronous (AsyncIO)** dan **SQLite WAL Mode**, bot ini mampu memproses ribuan proxy dalam hitungan detik dengan penggunaan sumber daya (CPU/RAM) yang sangat efisien. Bot ini juga memiliki fitur **Hybrid Mode**, yang memungkinkannya tetap berjalan di server (CLI) meskipun koneksi ke Telegram gagal.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)
![SQLite](https://img.shields.io/badge/SQLite-WAL%20Mode-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

---

## 🚀 Fitur Unggulan

### 🧠 1. Smart Classification (Residential vs Datacenter)
Fitur premium untuk memisahkan "Harta Karun" dari proxy pasaran.
- **Residential (🏠):** Proxy dari ISP rumahan (Indihome, Comcast, Verizon). Tahan blokir Netflix/Google. Disimpan terpisah di `proxy_residential.txt`.
- **Datacenter (🏢):** Proxy dari server cloud (Google Cloud, AWS, DigitalOcean). Cepat tapi mudah terdeteksi.

### 🤖 2. Hybrid & Headless Mode
Bot ini "Tahan Banting".
- **Telegram Mode:** Kontrol penuh via chat, notifikasi realtime, dan download file via tombol.
- **CLI / Headless Mode:** Jika Token Telegram salah/kosong atau API down, bot **TIDAK AKAN CRASH**. Bot otomatis beralih ke mode CLI (Command Line), tetap melakukan mining proxy, dan menyimpan hasilnya ke database & file lokal VPS.

### 🛡️ 3. Safety & Resource Limiting
Aman dijalankan berdampingan dengan aplikasi berat (seperti Freqtrade/Node Validator).
- **CPU/RAM Limit:** Dibatasi via Docker (Max 50% CPU & 4GB RAM).
- **Rate Limiting:** Delay cerdas saat mengecek API ISP untuk mencegah IP VPS terkena banned.
- **Bloatware Free:** Tidak menggunakan Selenium/Chrome, sangat ringan.

### ⚡ 4. Efisiensi Tinggi
- **Smart Deduplication:** Proxy yang sudah ada di database (Gold List) tidak akan dicek ulang ke API ISP (Hemat Kuota API).
- **Database Optimization:** Menggunakan SQLite dengan `WAL Mode` (Write-Ahead Logging) untuk mencegah database terkunci saat ribuan data masuk bersamaan.
- **Auto-Vacuum:** Otomatis membersihkan sampah database setiap restart.

---

## 🛠️ Instalasi & Cara Pakai

### Prasyarat
- VPS Linux (Ubuntu/Debian)
- Docker & Docker Compose

### 1. Clone & Setup
```bash
git clone [https://github.com/username-anda/wxd-proxy-hunter.git](https://github.com/username-anda/wxd-proxy-hunter.git)
cd wxd-proxy-hunter

2. Konfigurasi
Edit file config.py:
BOT_TOKEN = "123456:ABC-DEF..." # Kosongkan jika ingin mode CLI/Tanpa Telegram
ALLOWED_USER_ID = 123456789     # ID Telegram Anda

3. Jalankan (Docker)
Gunakan perintah ini untuk membangun dan menjalankan bot di background:
docker compose up -d --build

4. Cek Log
Untuk melihat aktivitas bot (terutama di mode Headless):
docker compose logs -f

🎮 Kontrol Telegram
Kirim /start ke bot Anda untuk memunculkan panel kontrol.
| Tombol | Fungsi |
|---|---|
| ▶️ START SCAN | Memulai siklus mining otomatis. |
| 🛑 STOP | Menghentikan proses mining. |
| 📄 LOG | Cek status terkini & refresh statistik database. |
| 📥 RESIDENTIAL ONLY | 💎 Download file khusus proxy ISP Rumahan (proxy_residential.txt). |
| 📥 ALL (IP:PORT) | Download semua proxy aktif (proxy_active.txt). |
| 📥 ALL (URI) | Download format socks5://1.1.1.1:80. |
| 🏳️ SET REGION | Filter pencarian negara tertentu (ID, US, SG, dll). |
📂 Struktur Project
.
├── docker-compose.yml      # Config Container (Volume & Resource Limit)
├── Dockerfile              # Setup Python Environment (Slim)
├── requirements.txt        # Dependensi (Requests, Aiohttp, dll)
├── config.py               # Token & User Settings
├── main.py                 # Logic Utama (Hybrid Mode Telegram/CLI)
├── modules/
│   ├── scraper.py          # Mining (GitHub, Spys.me, ProxyScrape)
│   ├── checker.py          # Validasi (Google, ISP Check, HIA)
│   ├── database.py         # SQLite Handler (WAL, Vacuum)
│   ├── geoip.py            # Deteksi Bendera Negara Offline
│   └── utils.py            # Formatter & File Saver (Residential)
└── output/                 # (Volume Mapped) File .txt & .db tersimpan di sini

⚠️ Output Files
Bot akan menghasilkan file berikut secara otomatis di folder VPS Anda:
 * proxy_residential.txt: List Premium (ISP Rumahan).
 * proxy_active.txt: Semua proxy aktif (Campur).
 * type_proxy_active.txt: Format Protocol URI.
 * proxies.db: Database SQLite utama.
Dev: WXD | License: MIT

