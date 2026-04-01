import os
import requests
from bs4 import BeautifulSoup
import hashlib
import time
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "seen_jobs.txt")

def load_seen_jobs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_jobs(job_ids):
    if not job_ids: return
    with open(DB_FILE, "a") as f:
        for job_id in job_ids:
            f.write(f"{job_id}\n")

def escape_markdown(text):
    """Helper to escape special characters for Telegram MarkdownV2"""
    # Characters that need escaping in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": "true"
    }
    requests.post(url, data=payload)

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_job_ids = []

    sources = [
        {"name": "Sarkari Result", "url": "https://www.sarkariresult.com/latestjob/", "selector": ".post ul li a"},
        {"name": "Free Job Alert", "url": "https://www.freejobalert.com/latest-notifications/", "selector": "table.listing tr td a"},
        {"name": "Sarkari-FJA", "url": "https://sarkariresult.freejobalert.com/", "selector": ".post-content ul li a, .entry-content ul li a"}
    ]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for src in sources:
        try:
            print(f"🔍 Scraping {src['name']}...")
            res = requests.get(src['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select(src['selector'])

            for link in links[:15]:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                if not href or len(title) < 10: continue

                job_id = hashlib.md5(href.encode()).hexdigest()

                if job_id not in seen_jobs:
                    # Minimalist formatting: Title is the clickable link
                    # Source name is bold and small.
                    clean_title = escape_markdown(title)
                    source_name = escape_markdown(src['name'])
                    
                    # Minimal UI Format: "● [Title](URL) | [Source]"
                    msg = f"• [{clean_title}]({href}) \| *{source_name}*"
                    
                    send_telegram(msg)
                    new_job_ids.append(job_id)
                    seen_jobs.add(job_id)
                    time.sleep(1)

        except Exception as e:
            print(f"⚠️ Error on {src['name']}: {e}")

    save_seen_jobs(new_job_ids)

if __name__ == "__main__":
    scrape_jobs()
