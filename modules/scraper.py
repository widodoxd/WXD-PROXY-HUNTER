import requests
import re
from fake_useragent import UserAgent

def get_proxies(country_code="ALL"):
    proxies = []
    print(f"[*] Mining Global Data... (Target Filter: {country_code})")
    
    try: ua = UserAgent()
    except: ua = None

    # --- SUMBER 1: GITHUB (Raw Text) ---
    github_sources = [
        ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "HTTP"),
        ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", "SOCKS5"),
        ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt", "HTTP"),
        ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt", "SOCKS5"),
        ("https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt", "HTTP"),
        ("https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt", "SOCKS5"),
        ("https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt", "HTTP"),
        ("https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt", "SOCKS5"),
        # Sumber Tambahan Kualitas Bagus
        ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt", "HTTP"),
        ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt", "SOCKS5"),
        ("https://spys.me/proxy.txt", "HTTP"), # Legendaris
        ("https://spys.me/socks.txt", "SOCKS5")
    ]
    
    print("[*] Mengambil data dari GitHub & Spys...")
    for url, p_type in github_sources:
        try:
            current_ua = ua.random if ua else 'Mozilla/5.0'
            r = requests.get(url, headers={'User-Agent': current_ua}, timeout=10)
            if r.status_code == 200:
                lines = r.text.splitlines()
                # Ambil lebih banyak sampel (max 3000 per file)
                for line in lines[:3000]: 
                    if ":" in line and not line.startswith("#"): # Hindari komentar
                        proxies.append({"ip": line.strip(), "type": p_type, "anon": "UNKNOWN", "region": "ALL"})
        except: pass

    # --- SUMBER 2: PROXYSCRAPE API (High Volume) ---
    print("[*] Mengambil data API ProxyScrape (Sakti)...")
    scrape_configs = [
        ("http", "HTTP"),
        ("socks5", "SOCKS5")
    ]
    for proto_api, proto_label in scrape_configs:
        try:
            # Mengambil proxy yang statusnya 'alive' menurut proxyscrape
            api_url = f"https://api.proxyscrape.com/v2/?request=getproxies&protocol={proto_api}&timeout=10000&country=all&ssl=all&anonymity=all"
            current_ua = ua.random if ua else 'Mozilla/5.0'
            r = requests.get(api_url, headers={'User-Agent': current_ua}, timeout=15)
            if r.status_code == 200:
                lines = r.text.splitlines()
                for line in lines:
                    if ":" in line:
                        proxies.append({"ip": line.strip(), "type": proto_label, "anon": "UNKNOWN", "region": "ALL"})
        except: pass

    # --- DEDUPLICATE & CLEANING ---
    unique_proxies = []
    seen_ips = set()
    for p in proxies:
        clean_ip = p['ip'].strip()
        # Regex Validasi IP:PORT
        if clean_ip not in seen_ips and re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$", clean_ip):
            p['ip'] = clean_ip
            unique_proxies.append(p)
            seen_ips.add(clean_ip)
            
    print(f"[*] Total Kandidat Super Scraper: {len(unique_proxies)}")
    return unique_proxies
