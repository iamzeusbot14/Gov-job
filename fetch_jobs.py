import os
import requests
from bs4 import BeautifulSoup
import hashlib
import time

# 1. History Management
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
    requests.post(url, data=payload)

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_jobs_list = []
    new_job_ids = []

    # Targeting the specific domain requested
    target_url = "https://sarkariresult.com.cm/category/latest-job/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        res = requests.get(target_url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Pulling the latest 15 links from the container
        links = soup.select('h2.entry-title a') or soup.select('.post-content ul li a')

        for link in links[:15]:
            title = link.get_text(strip=True)
            href = link.get('href', '')
            
            if not href or len(title) < 8: continue
            
            job_id = hashlib.md5(href.encode()).hexdigest()

            if job_id not in seen_jobs:
                new_jobs_list.append({"title": title, "url": href})
                new_job_ids.append(job_id)
                seen_jobs.add(job_id)

    except Exception as e:
        print(f"Error: {e}")

    # 2. Ultra-Minimalist Report UI
    if new_jobs_list:
        # Clean Header with dynamic count
        report = f"🚀 *New Opportunities ({len(new_jobs_list)})*\n"
        report += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for job in new_jobs_list:
            # Format: • [Job Title](URL)
            line = f"• [{job['title']}]({job['url']})\n\n"
            
            # Message splitting for safety
            if len(report) + len(line) > 4000:
                send_telegram(report)
                report = ""
            report += line
        
        # Sending the final report (No source/footer text)
        if report:
            send_telegram(report)
        
        save_seen_jobs(new_job_ids)
    else:
        print("No new updates found.")

if __name__ == "__main__":
    scrape_jobs()
