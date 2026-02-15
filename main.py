import sys
import traceback
import os
import asyncio
import time
import logging

# --- IMPORT MODULES ---
from config import BOT_TOKEN, ALLOWED_USER_ID, LOOP_DELAY
from modules.utils import setup_logging, save_formatted_proxies
from modules.database import init_db, save_proxy_to_db, get_all_db_proxies, remove_proxy_from_db, get_db_stats
from modules.geoip import get_geoip_data
from modules.scraper import get_proxies
from modules.checker import check_proxies_async

# Import Telegram (Try-Except tidak diperlukan di import level, tapi di inisialisasi)
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, Application
from telegram.request import HTTPXRequest 
from telegram.error import InvalidToken, Unauthorized

setup_logging()

# Global Vars
current_task = None
is_running = False
live_status_log = "⏳ Menunggu..."
active_region = "ALL"
active_anon = "HIA"

def set_status(text: str):
    global live_status_log
    timestamp = time.strftime("%H:%M:%S")
    live_status_log = f"🕒 **Last Update: {timestamp}**\n{text}"
    # Print ke console agar terlihat di log VPS (Mode CLI)
    print(f"[*] {text}", flush=True)

# --- KEYBOARDS (Hanya dipakai jika Telegram Aktif) ---
def get_main_menu():
    try: db_stats = get_db_stats()
    except: db_stats = "0"
    icon_anon = "🛡️" if active_anon == "HIA" else ("🔓" if active_anon == "ALL" else "🕵️")
    lbl_region = f"🏳️ SET REGION: {active_region}" 
    lbl_anon = f"⚙️ SET ANON: {active_anon}"
    keyboard = [
        [KeyboardButton(f"💾 DB: {db_stats}"), KeyboardButton("📄 LOG")],
        [KeyboardButton("📥 ALL (IP:PORT)"), KeyboardButton("📥 ALL (URI)")],
        [KeyboardButton("📥 RESIDENTIAL ONLY (Premium) 🏠")],
        [KeyboardButton(lbl_region), KeyboardButton(lbl_anon)],
        [KeyboardButton("▶️ START SCAN"), KeyboardButton("🛑 STOP")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_region_menu():
    codes = ["ALL", "US", "ID", "SG", "PH", "CN", "DE", "AR", "BR", "RU", "JP", "GB"]
    buttons = []
    row = []
    for code in codes:
        flag_map = {"ALL":"🌍", "US":"🇺🇸", "ID":"🇮🇩", "SG":"🇸🇬", "PH":"🇵🇭", "CN":"🇨🇳", "DE":"🇩🇪", "AR":"🇦🇷", "BR":"🇧🇷", "RU":"🇷🇺", "JP":"🇯🇵", "GB":"🇬🇧"}
        flag = flag_map.get(code, "🏳️")
        row.append(KeyboardButton(f"SET: {flag} {code}"))
        if len(row) == 3: 
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    buttons.append([KeyboardButton("🔙 KEMBALI")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_anon_menu():
    buttons = [[KeyboardButton("FILTER: 🛡️ HIA")], [KeyboardButton("FILTER: 🕵️ ANM")], [KeyboardButton("FILTER: 🔓 ALL")], [KeyboardButton("🔙 KEMBALI")]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- CORE LOGIC (HYBRID) ---
# Parameter bot_instance dan chat_id dibuat OPTIONAL (None)
async def background_scan_task(bot_instance: Bot = None, chat_id: int = None):
    global is_running
    is_running = True
    
    # Init DB saat task mulai
    init_db()
    
    print("🚀 PROXY HUNTER STARTED...", flush=True)
    if not bot_instance:
        print("⚠️  RUNNING IN HEADLESS MODE (NO TELEGRAM) ⚠️", flush=True)

    while is_running:
        try:
            cycle_region = active_region
            cycle_anon = active_anon
            cycle_proxies_data = [] 
            checked_ips_in_db = set()

            # --- FASE 1: DB Check ---
            db_proxies = get_all_db_proxies()
            if db_proxies:
                set_status(f"💾 **Fase 1: Cek Gold List** ({len(db_proxies)} proxy)...")
                gold_alive = []
                
                def on_gold_found(result):
                    p = result['data']
                    gold_alive.append(p['ip'])
                    save_proxy_to_db(p)
                    cycle_proxies_data.append(p)
                    # Log CLI
                    print(f"[+] GOLD ALIVE: {p['ip']}", flush=True)

                await check_proxies_async(db_proxies, on_gold_found)
                
                for p in db_proxies: checked_ips_in_db.add(p['ip'])

                all_db_ips = [p['ip'] for p in db_proxies]
                dead_ips = set(all_db_ips) - set(gold_alive)
                for dead in dead_ips: remove_proxy_from_db(dead)

            # --- FASE 2: Mining ---
            set_status(f"⛏️ **Fase 2: Mining Global** (Filter: {cycle_region})...")
            raw_proxies = await asyncio.get_running_loop().run_in_executor(None, get_proxies, cycle_region)
            
            filtered_proxies = []
            if raw_proxies:
                for p in raw_proxies:
                    if p['ip'] not in checked_ips_in_db:
                        filtered_proxies.append(p)
                
                ignored = len(raw_proxies) - len(filtered_proxies)
                set_status(f"🔎 Kandidat: {len(raw_proxies)} | Skip DB: {ignored} | Cek: {len(filtered_proxies)}")
            else: filtered_proxies = []

            if filtered_proxies:
                new_found_count = 0
                
                # Wrapper untuk kirim pesan Telegram AMAN
                async def send_telegram_msg(txt, use_markup=False):
                    if bot_instance and chat_id:
                        try: 
                            markup = get_main_menu() if use_markup else None
                            await bot_instance.send_message(chat_id, txt, parse_mode='Markdown', reply_markup=markup)
                        except Exception as e: print(f"[!] Tele Send Err: {e}")

                def on_found(result):
                    if not is_running: return
                    p = result['data']
                    
                    flag, name, code = get_geoip_data(p['ip'])
                    if cycle_region != "ALL" and code != cycle_region: return 

                    final_anon = p.get('anon', 'Unknown')
                    if cycle_anon == "HIA" and "HIA" not in final_anon: return
                    elif cycle_anon == "ANM" and "Anonymous" not in final_anon and "HIA" not in final_anon: return

                    nonlocal new_found_count
                    new_found_count += 1
                    
                    isp_info = p.get('isp', 'Unknown ISP')
                    category = p.get('category', 'UNKNOWN')
                    cat_icon = "🏠" if category == "RESIDENTIAL" else "🏢"
                    
                    # LOG CLI (Selalu print)
                    print(f"[+] NEW: {p['ip']} -> {name} ({category}) | {isp_info}", flush=True)
                    
                    save_proxy_to_db(p)
                    cycle_proxies_data.append(p)

                    # NOTIF TELEGRAM (Hanya jika bot ada)
                    type_icon = "🛡️" if "SOCKS" in p['type'].upper() else "🌐"
                    msg = (
                        f"🚀 **LIVE PROXY!**\n\n"
                        f"{flag} Region: **{name}**\n"
                        f"📡 IP: `{p['ip']}`\n"
                        f"{type_icon} Type: **{p['type'].upper()}**\n"
                        f"🏢 ISP: **{isp_info}**\n" 
                        f"{cat_icon} Cat: **{category}**\n"
                        f"🕵️ Anon: **{final_anon}**\n"
                        f"⚡ Latency: **{result['latency']}s**"
                    )
                    asyncio.create_task(send_telegram_msg(msg))

                await check_proxies_async(filtered_proxies, on_found)
                
                total = len(cycle_proxies_data)
                db_stats = get_db_stats()
                save_formatted_proxies(cycle_proxies_data)
                
                status_msg = ""
                if total > 0:
                    status_msg = f"✅ **Siklus Selesai**\nAktif: {total} (Baru: {new_found_count})\n💾 Database: {db_stats}"
                    set_status(status_msg)
                    if new_found_count > 0:
                        asyncio.create_task(send_telegram_msg(status_msg, use_markup=True))
                else:
                    status_msg = f"⚠️ **ZONK** Siklus ini kosong.\n💾 Database: {db_stats}"
                    set_status(status_msg)
            else:
                set_status("⚠️ **ZONK** Tidak ada kandidat baru.")

            if is_running: await asyncio.sleep(LOOP_DELAY)

        except asyncio.CancelledError: break
        except Exception as e:
            set_status(f"❌ Error Loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)

# --- TELEGRAM HANDLERS ---
async def post_init(application: Application):
    global current_task
    # Cek apakah task sudah jalan (dari main), kalau belum, jalankan via Telegram
    if current_task is None or current_task.done():
        current_task = asyncio.create_task(background_scan_task(application.bot, ALLOWED_USER_ID))
    
    try: await application.bot.send_message(ALLOWED_USER_ID, f"🚀 **BOT READY**\nMode: Telegram Connected ✅", reply_markup=get_main_menu())
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID: return
    await context.bot.send_message(update.effective_chat.id, "🤖 **PANEL**", reply_markup=get_main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID: return
    text = update.message.text
    chat_id = update.effective_chat.id
    global is_running, active_region, active_anon, current_task

    try:
        if text.startswith("SET:"):
            active_region = text.split(" ")[-1]
            await context.bot.send_message(chat_id, f"✅ Target: **{active_region}**", reply_markup=get_main_menu(), parse_mode='Markdown'); return
        if "REGION" in text: await context.bot.send_message(chat_id, "🏳️ **PILIH NEGARA:**", reply_markup=get_region_menu()); return

        if text.startswith("FILTER:"):
            if "HIA" in text: active_anon = "HIA"
            elif "ANM" in text: active_anon = "ANM"
            else: active_anon = "ALL"
            await context.bot.send_message(chat_id, f"✅ Filter: **{active_anon}**", reply_markup=get_main_menu(), parse_mode='Markdown'); return
        if "ANON" in text: await context.bot.send_message(chat_id, "🛡️ **PILIH LEVEL:**", reply_markup=get_anon_menu()); return

        if text == "🔙 KEMBALI": await context.bot.send_message(chat_id, "🔙 Menu", reply_markup=get_main_menu()); return

        if text == "📥 ALL (IP:PORT)":
            if os.path.exists("proxy_active.txt"):
                await context.bot.send_document(chat_id, open("proxy_active.txt", "rb"), caption="📄 **Semua Proxy (IP:PORT)**", parse_mode='Markdown')
            else: await context.bot.send_message(chat_id, "⚠️ File belum siap.")
            return

        if text == "📥 ALL (URI)":
            if os.path.exists("type_proxy_active.txt"):
                await context.bot.send_document(chat_id, open("type_proxy_active.txt", "rb"), caption="🔗 **Semua Proxy (URI)**", parse_mode='Markdown')
            else: await context.bot.send_message(chat_id, "⚠️ File belum siap.")
            return
            
        if "RESIDENTIAL" in text:
            if os.path.exists("proxy_residential.txt"):
                await context.
