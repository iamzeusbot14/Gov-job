import requests
from bs4 import BeautifulSoup
import os
import hashlib
import time

DB_FILE = "seen_jobs.txt"

def load_seen_jobs():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def save_seen_jobs(job_ids):
    with open(DB_FILE, "a") as f:
        for job_id in job_ids:
            f.write(f"{job_id}\n")

def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": "true"
        }, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_job_ids = []
    
    # List of sources with their specific HTML structures
    sources = [
        {
            "name": "Sarkari Result",
            "url": "https://www.sarkariresult.com/latestjob/",
            "selector": "#post ul li a",
            "base_url": "https://www.sarkariresult.com"
        },
        {
            "name": "Free Job Alert",
            "url": "https://www.freejobalert.com/latest-notifications/",
            "selector": "table.listing tr td a",
            "base_url": "" 
        },
        {
            "name": "Jagran Josh",
            "url": "https://www.jagranjosh.com/articles/government-jobs-india-1303386128-1",
            "selector": ".ListingBox ul li a",
            "base_url": "https://www.jagranjosh.com"
        }
    ]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for src in sources:
        try:
            print(f"🔍 Checking {src['name']}...")
            response = requests.get(src['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(src['selector'])

            for link in links[:20]: # Check the top 20 latest links per site
                title = link.get_text().strip()
                href = link.get('href', '')
                
                if not href or len(title) < 8 or "javascript" in href:
                    continue
                
                full_link = href if href.startswith('http') else f"{src['base_url']}{href}"
                job_id = hashlib.md5(full_link.encode()).hexdigest()

                if job_id not in seen_jobs:
                    # Highlight high-priority keywords
                    priority_keys = ["UPSC", "SSC", "RAILWAY", "BANK", "POLICE", "ARMY", "TEACHER"]
                    is_priority = any(k in title.upper() for k in priority_keys)
                    emoji = "🚨" if is_priority else "🆕"
                    
                    msg = f"{emoji} *[{src['name']}] Update*\n\n🔹 *{title}*\n🔗 [Apply / Details]({full_link})"
                    
                    send_telegram(msg)
                    new_job_ids.append(job_id)
                    time.sleep(1.5) # Prevent Telegram flood/ban

        except Exception as e:
            print(f"⚠️ Error on {src['name']}: {e}")

    if new_job_ids:
        save_seen_jobs(new_job_ids)
        print(f"✅ Sent {len(new_job_ids)} new job updates.")
    else:
        print("📭 No new updates found this time.")

if __name__ == "__main__":
    scrape_jobs()
