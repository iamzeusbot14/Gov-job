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
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true"
    })

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_job_ids = []
    
    # Define our sources and their specific HTML patterns
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
            "selector": ".featured-list li a",
            "base_url": "" # These are usually full links
        }
    ]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for src in sources:
        try:
            print(f"Checking {src['name']}...")
            response = requests.get(src['url'], headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(src['selector'])

            for link in links[:15]: # Top 15 from each site
                title = link.get_text().strip()
                href = link.get('href', '')
                
                if not href or len(title) < 5: continue
                
                full_link = href if href.startswith('http') else f"{src['base_url']}{href}"
                job_id = hashlib.md5(full_link.encode()).hexdigest()

                if job_id not in seen_jobs:
                    msg = f"🆕 *[{src['name']}] Update*\n\n🔹 *{title}*\n🔗 [Link]({full_link})"
                    send_telegram(msg)
                    new_job_ids.append(job_id)
                    time.sleep(1) # Prevent Telegram rate limits

        except Exception as e:
            print(f"Error scraping {src['name']}: {e}")

    if new_job_ids:
        save_seen_jobs(new_job_ids)
        print(f"Found {len(new_job_ids)} total new jobs.")

if __name__ == "__main__":
    scrape_jobs()
