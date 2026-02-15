import sqlite3
import time

DB_NAME = "proxies.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # --- OPTIMASI PERFORMANCE (WAL MODE) ---
    # Mengaktifkan Write-Ahead Logging agar database ngebut & anti-locked
    c.execute("PRAGMA journal_mode=WAL;")
    
    # Membuat tabel
    c.execute('''CREATE TABLE IF NOT EXISTS proxies
                 (ip TEXT PRIMARY KEY, type TEXT, region TEXT, anon TEXT, last_checked REAL, isp TEXT, category TEXT)''')
    
    # Vacuum untuk membersihkan sampah data
    c.execute("VACUUM")
    
    conn.commit()
    conn.close()

def save_proxy_to_db(p):
    try:
        # Timeout ditingkatkan ke 20 detik agar lebih sabar menunggu antrian
        conn = sqlite3.connect(DB_NAME, timeout=20)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO proxies VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (p['ip'], p['type'], p['region'], p['anon'], time.time(), p.get('isp', 'Unknown'), p.get('category', 'UNKNOWN')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] DB Save Error: {e}")

def get_all_db_proxies():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=20)
        c = conn.cursor()
        c.execute("SELECT * FROM proxies")
        rows = c.fetchall()
        conn.close()
        
        proxies = []
        for r in rows:
            proxies.append({
                "ip": r[0], "type": r[1], "region": r[2], "anon": r[3], "isp": r[5], "category": r[6]
            })
        return proxies
    except: return []

def remove_proxy_from_db(ip):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=20)
        c = conn.cursor()
        c.execute("DELETE FROM proxies WHERE ip=?", (ip,))
        conn.commit()
        conn.close()
    except: pass

def get_db_stats():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=20)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM proxies")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM proxies WHERE category='RESIDENTIAL'")
        res = c.fetchone()[0]
        conn.close()
        return f"{total} (Res: {res})"
    except: return "0"
