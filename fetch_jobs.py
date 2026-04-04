import os
import requests
from bs4 import BeautifulSoup
import hashlib
import time

# 1. Database Management
DB_FILE = "seen_jobs.txt"

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

def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send to Telegram: {e}")

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_jobs_list = []
    new_job_ids = []

    # Targeted URL
    target_url = "https://sarkariresult.com.cm/category/latest-job/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        res = requests.get(target_url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Selectors for sarkariresult.com.cm links
        links = soup.select('h2.entry-title a') or soup.select('.post-content ul li a')

        for link in links[:20]: # Check top 20 latest
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not href or len(title) < 10: continue
            
            # Use URL hash as unique ID
            job_id = hashlib.md5(href.encode()).hexdigest()

            if job_id not in seen_jobs:
                new_jobs_list.append({"title": title, "url": href})
                new_job_ids.append(job_id)
                seen_jobs.add(job_id)

    except Exception as e:
        print(f"Scraper encountered an error: {e}")

    # 2. Professional Report UI Logic
    if new_jobs_list:
        report = f"🚀 **New Updates ({len(new_jobs_list)})**\n"
        report += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for job in new_jobs_list:
            # Clean "Clickable Title" format
            line = f"• [{job['title']}]({job['url']})\n\n"
            
            # Split if message exceeds Telegram limit
            if len(report) + len(line) > 4000:
                send_telegram(report)
                report = ""
            report += line
        
        if report:
            send_telegram(report)
        
        # Only save to history if we found and processed new jobs
        save_seen_jobs(new_job_ids)
    else:
        print("No new jobs to report.")

if __name__ == "__main__":
    scrape_jobs()
