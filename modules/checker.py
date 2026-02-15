import asyncio
import time
import aiohttp
from aiohttp_socks import ProxyConnector
from fake_useragent import UserAgent

TEST_URL = "http://www.google.com" 
TIMEOUT = 10 

try: ua_gen = UserAgent()
except: ua_gen = None

# KEYWORDS DATACENTER
DATACENTER_KEYWORDS = [
    "GOOGLE", "AMAZON", "AWS", "MICROSOFT", "AZURE", "DIGITALOCEAN", 
    "ALIBABA", "ORACLE", "LINODE", "VULTR", "HETZNER", "OVH", 
    "CHOOPA", "M247", "DATACAMP", "HOST", "SERVER", "VPS", "CLOUD", 
    "DEDICATED", "COLOCATION", "LEASEWEB", "CONTABO", "IPXO", 
    "PONYNET", "FRANTECH", "BUYVM", "ONLINE S.A.S.", "SCALEWAY",
    "TRANSIT", "DATA CENTER", "DATACENTER", "CDN", "TELECOM ITALIA SPARKLE",
    "GSL NETWORKS", "CLOUDFLARE", "AKAMAI", "FASTLY", "EDGECAST",
    "QUASINETWORKS", "PACKET", "HOSTING", "LAYERIP", "SERVERIAN",
    "SELECTEL", "TERA-SWITCH", "ZENLAYER", "CDNETWORKS", "NOCTION",
    "DATACOMM", "FIBER"
]

def get_proxy_category(isp_name, org_name):
    full_text = (str(isp_name) + " " + str(org_name)).upper()
    for keyword in DATACENTER_KEYWORDS:
        if keyword in full_text: return "DATACENTER"
    return "RESIDENTIAL"

async def check_single_proxy(session, proxy_data, on_found_callback):
    proxy_ip = proxy_data['ip']
    proxy_type = proxy_data['type'].lower()
    proxy_url = f"{proxy_type}://{proxy_ip}"
    
    random_ua = ua_gen.random if ua_gen else "Mozilla/5.0"
    headers = {"User-Agent": random_ua}
    
    start_time = time.time()
    try:
        connector = None
        if "socks" in proxy_type:
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector) as specific_session:
                async with specific_session.get(TEST_URL, headers=headers, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        await _handle_success(proxy_data, start_time, on_found_callback)
        else:
            async with session.get(TEST_URL, proxy=proxy_url, headers=headers, timeout=TIMEOUT) as response:
                if response.status == 200:
                    await _handle_success(proxy_data, start_time, on_found_callback)
    except: pass

async def _check_hia_async(ip, p_type):
    """
    Cek Anonymity secara ASYNC agar tidak memblokir loop utama.
    """
    try:
        proxy_url = f"{p_type.lower()}://{ip}"
        # Khusus SOCKS butuh connector
        connector = ProxyConnector.from_url(proxy_url) if "socks" in p_type.lower() else None
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Gunakan httpbin untuk cek header
            # Kita set timeout pendek (10s) agar tidak menunggu lama
            async with session.get("http://httpbin.org/get", proxy=proxy_url if not connector else None, timeout=10) as r:
                if r.status == 200:
                    js = await r.json()
                    headers = js.get("headers", {})
                    leak_headers = ["X-Forwarded-For", "Via", "X-Real-Ip", "Forwarded"]
                    is_leaking = any(h in headers for h in leak_headers)
                    
                    if not is_leaking: return "HIA (Elite)"
                    else: return "Anonymous"
    except: 
        pass
    return "Transparent/Unknown"

async def _handle_success(data, start_time, callback):
    latency = round(time.time() - start_time, 2)
    
    # 1. SMART RECHECK ISP
    current_isp = data.get('isp', 'Unknown')
    current_cat = data.get('category', 'UNKNOWN')

    if current_isp == "Unknown" or current_cat == "UNKNOWN":
        isp_name, org_name = "Unknown", "Unknown"
        try:
            await asyncio.sleep(0.3) # Rate limit protection
            ip_only = data['ip'].split(":")[0]
            async with aiohttp.ClientSession() as sess:
                async with sess.get(f"http://ip-api.com/json/{ip_only}?fields=isp,org", timeout=5) as r:
                    if r.status == 200:
                        js = await r.json()
                        isp_name = js.get('isp', 'Unknown')
                        org_name = js.get('org', 'Unknown')
        except: pass
        
        data['isp'] = isp_name if isp_name != "Unknown" else org_name
        data['category'] = get_proxy_category(isp_name, org_name)

    # 2. CHECK ANONYMITY (HIA) - SEKARANG ASYNC!
    # Kita cek HIA jika statusnya masih UNKNOWN atau kita mau re-verify
    # Agar hemat waktu, kita cek HIA hanya jika data baru
    if "HIA" not in data.get('anon', '') and "Anonymous" not in data.get('anon', ''):
         data['anon'] = await _check_hia_async(data['ip'], data['type'])

    result = {'data': data, 'latency': latency}
    if callback: callback(result)

async def check_proxies_async(proxies, on_found_callback):
    tasks = []
    semaphore = asyncio.Semaphore(200) 

    async def sem_task(session, p):
        async with semaphore:
            await check_single_proxy(session, p, on_found_callback)

    async with aiohttp.ClientSession() as session:
        for p in proxies:
            task = asyncio.create_task(sem_task(session, p))
            tasks.append(task)
        await asyncio.gather(*tasks)
