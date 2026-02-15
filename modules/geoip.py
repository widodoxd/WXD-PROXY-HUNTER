import geoip2.database
import os

# Lokasi absolut di dalam Docker
DB_PATH = "/app/GeoLite2-Country.mmdb"

def get_geoip_data(ip_address):
    """
    Menerima IP (bisa format ip:port atau ip saja)
    Mengembalikan Bendera, Nama Negara, Kode Negara
    """
    try:
        # PENTING: Bersihkan Port jika ada (1.1.1.1:80 -> 1.1.1.1)
        clean_ip = ip_address.split(':')[0]

        if not os.path.exists(DB_PATH):
            print(f"[!] GeoIP Error: Database file not found at {DB_PATH}")
            return "🏳️", "Unknown Region", "ALL"

        with geoip2.database.Reader(DB_PATH) as reader:
            response = reader.country(clean_ip) # Gunakan IP bersih
            country_code = response.country.iso_code
            country_name = response.country.name
            
            if not country_code:
                return "🏳️", "Unknown Region", "ALL"

            # Bikin Bendera
            flag = "".join([chr(ord(c) + 127397) for c in country_code.upper()])
            
            # Shorten names (Biar tidak kepanjangan di chat)
            if country_name == "United Kingdom": country_name = "UK"
            if country_name == "United States": country_name = "USA"
            if country_name == "Russian Federation": country_name = "Russia"
            
            return flag, country_name, country_code.upper()

    except Exception as e:
        # Uncomment baris bawah ini jika ingin melihat error detail di terminal
        # print(f"[!] GeoIP Lookup Error ({ip_address}): {e}")
        return "🏳️", "Unknown Region", "ALL"
