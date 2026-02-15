import logging
import time
import os

def setup_logging():
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    # Silent loggers yang berisik
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

def save_formatted_proxies(proxy_list_dicts):
    """
    Menyimpan 3 tipe file:
    1. proxy_active.txt (SEMUA IP:PORT)
    2. type_proxy_active.txt (SEMUA PROTOCOL://IP:PORT)
    3. proxy_residential.txt (HANYA RESIDENTIAL) -> YANG KITA TAMBAHKAN
    """
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M')
        
        # --- FILE 1: ALL IP:PORT ---
        with open("proxy_active.txt", "w") as f1:
            f1.write(f"=== ALL PROXY LIST ({timestamp}) ===\n")
            f1.write(f"Total: {len(proxy_list_dicts)}\n\n")
            for p in proxy_list_dicts:
                f1.write(f"{p['ip']}\n")
        
        # --- FILE 2: ALL URI ---
        with open("type_proxy_active.txt", "w") as f2:
            f2.write(f"=== ALL PROXY URI ({timestamp}) ===\n")
            f2.write(f"Total: {len(proxy_list_dicts)}\n\n")
            for p in proxy_list_dicts:
                proto = p['type'].lower()
                f2.write(f"{proto}://{p['ip']}\n")
        
        # --- FILE 3: RESIDENTIAL ONLY (PREMIUM) ---
        # Filter: Hanya ambil yang category-nya RESIDENTIAL
        res_proxies = [p for p in proxy_list_dicts if p.get('category') == 'RESIDENTIAL']
        
        with open("proxy_residential.txt", "w") as f3:
            f3.write(f"=== WXD RESIDENTIAL LIST ({timestamp}) ===\n")
            f3.write(f"Count: {len(res_proxies)}\n")
            f3.write("Format: IP:PORT | TYPE | REGION | ISP\n\n")
            
            if res_proxies:
                for p in res_proxies:
                    # Kita kasih detail ISP biar kelihatan premiumnya
                    line = f"{p['ip']} | {p['type'].upper()} | {p['region']} | {p.get('isp', 'Unknown')}\n"
                    f3.write(line)
            else:
                f3.write("Belum ada proxy residential ditemukan pada scan terakhir.\n")
                
        return True
    except Exception as e:
        print(f"[!] Gagal save file TXT: {e}")
        return False
