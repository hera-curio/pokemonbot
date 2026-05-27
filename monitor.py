import requests
import schedule
import time
import logging
from datetime import datetime
import pytz

# ── CONFIG ──────────────────────────────────────────────
TELEGRAM_TOKEN   = "8896256671:AAES5CXCf8vCEaGGs393vS50FQX7z2tVnSg"
TELEGRAM_CHAT_ID = "8762116992"

TARGET_TEXTS = [
    "7月22日",
    "July 22",
    "7/22",
    "07/22",
]

RESERVATION_URL = "https://reserve.pokemon-cafe.jp/"

JST = pytz.timezone("Asia/Tokyo")
EST = pytz.timezone("America/New_York")

check_count = 0
already_alerted = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── TELEGRAM ─────────────────────────────────────────────
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info(f"Telegram sent: {message[:60]}")
    except Exception as e:
        log.error(f"Telegram failed: {e}")

# ── FETCH PAGE ────────────────────────────────────────────
def fetch_page():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        r = requests.get(RESERVATION_URL, headers=headers, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log.warning(f"Fetch failed: {e}")
        return None

# ── CHECK ─────────────────────────────────────────────────
def check():
    global check_count, already_alerted

    if already_alerted:
        return

    check_count += 1
    now_jst = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    now_est = datetime.now(EST).strftime("%Y-%m-%d %H:%M:%S EST")
    log.info(f"Check #{check_count} — {now_est}")

    html = fetch_page()

    if html is None:
        log.warning("Could not fetch page — will retry")
        return

    # ── DETECTED ─────────────────────────────────────────
    found = any(t in html for t in TARGET_TEXTS)

    if found:
        already_alerted = True
        message = (
            "🚨🚨🚨 <b>JULY 22 IS OPEN</b> 🚨🚨🚨\n\n"
            "Pokémon Cafe July 22 reservations are NOW available!\n\n"
            "👉 <b>Book immediately:</b>\n"
            f"https://reserve.pokemon-cafe.jp/\n\n"
            f"🕐 Detected at: {now_est}\n"
            f"🇯🇵 Japan time: {now_jst}\n\n"
            "Steps:\n"
            "1. Open the link above\n"
            "2. Scroll down and click agree\n"
            "3. Solve the captcha\n"
            "4. Select July 22\n"
            "5. Complete booking\n\n"
            "⚡ GO NOW — slots sell out in minutes!"
        )
        send_telegram(message)
        # Send 3 times so you definitely see it
        time.sleep(2)
        send_telegram("🚨 POKEMON CAFE JULY 22 OPEN — BOOK NOW 🚨\nhttps://reserve.pokemon-cafe.jp/")
        time.sleep(2)
        send_telegram("🚨 POKEMON CAFE JULY 22 OPEN — BOOK NOW 🚨\nhttps://reserve.pokemon-cafe.jp/")
        log.info("SLOT FOUND — alerts sent 3x")

    else:
        log.info(f"Not available yet. Total checks: {check_count}")

# ── HOURLY HEARTBEAT ──────────────────────────────────────
def heartbeat():
    if already_alerted:
        return
    now_est = datetime.now(EST).strftime("%H:%M EST")
    now_jst = datetime.now(JST).strftime("%H:%M JST")
    message = (
        f"✅ <b>Pokemon Cafe Monitor — Still Running</b>\n\n"
        f"No July 22 slots yet.\n"
        f"Total checks so far: <b>{check_count}</b>\n"
        f"Current time: {now_est} / {now_jst}\n\n"
        f"Checking every 30 seconds normally.\n"
        f"Checking every 10 seconds during 5–9am EST "
        f"(6–10pm JST — likely release window).\n\n"
        f"You'll get 3 alerts the moment July 22 appears. 🔔"
    )
    send_telegram(message)

# ── DAILY SUMMARY ─────────────────────────────────────────
def daily_summary():
    if already_alerted:
        return
    now_est = datetime.now(EST).strftime("%Y-%m-%d %H:%M EST")
    message = (
        f"📊 <b>Daily Summary</b>\n\n"
        f"Still monitoring for Pokémon Cafe July 22.\n"
        f"Total checks: <b>{check_count}</b>\n"
        f"Time: {now_est}\n\n"
        f"No slots found yet. Monitoring continues. 👀"
    )
    send_telegram(message)

# ── SMART INTERVAL ────────────────────────────────────────
def get_interval():
    """
    Check every 10 seconds during 5am-9am EST
    (= 6pm-10pm JST, the most likely release window
    based on the May 17 6pm JST precedent).
    Otherwise every 30 seconds.
    """
    hour_est = datetime.now(EST).hour
    if 5 <= hour_est <= 9:
        return 10
    return 30

# ── MAIN ──────────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("Pokémon Cafe July 22 Monitor Starting")
    log.info("=" * 50)

    # Startup message
    send_telegram(
        "🟢 <b>Pokémon Cafe Monitor Started</b>\n\n"
        "Watching for July 22 reservation slots.\n"
        "You'll receive:\n"
        "• Hourly heartbeat (still running)\n"
        "• Daily summary at 9am EST\n"
        "• 3x instant alerts when July 22 opens\n\n"
        "Monitoring: https://reserve.pokemon-cafe.jp/\n"
        "Bot is running on Railway ☁️"
    )

    # Schedule heartbeat and daily summary
    schedule.every(1).hours.do(heartbeat)
    schedule.every().day.at("09:00").do(daily_summary)

    # Main loop with smart interval
    last_check = 0
    while True:
        now = time.time()
        interval = get_interval()

        if now - last_check >= interval:
            check()
            last_check = now

        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
