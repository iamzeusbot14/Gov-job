import requests
from bs4 import BeautifulSoup
import os
import hashlib

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

def fetch_sarkari_jobs():
    url = "https://www.sarkariresult.com/latestjob/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    seen_jobs = load_seen_jobs()
    new_job_ids = []
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the main 'Latest Jobs' list items
        job_links = soup.select("#post ul li a")
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not bot_token or not chat_id:
            print("Error: Missing Telegram credentials in Environment Variables.")
            return

        for link in job_links[:20]: # Check the latest 20 links
            title = link.get_text().strip()
            href = link.get('href', '')
            
            if not href or "sarkariresult" not in href and not href.startswith('/'):
                continue
                
            # Create unique ID for this specific job link
            job_id = hashlib.md5(href.encode()).hexdigest()
            
            if job_id not in seen_jobs:
                full_link = href if href.startswith('http') else f"https://www.sarkariresult.com{href}"
                
                message = f"🆕 *Sarkari Result Update*\n\n🔹 *{title}*\n🔗 [Apply / Details]({full_link})"
                
                # Send to Telegram
                tel_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id, 
                    "text": message, 
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": "true"
                }
                
                res = requests.post(tel_url, data=payload)
                if res.status_code == 200:
                    new_job_ids.append(job_id)
                else:
                    print(f"Failed to send Telegram message: {res.text}")

        if new_job_ids:
            save_seen_jobs(new_job_ids)
            print(f"Successfully processed {len(new_job_ids)} new jobs.")
        else:
            print("Everything up to date. No new jobs.")

    except Exception as e:
        print(f"Scraper Error: {e}")

if __name__ == "__main__":
    fetch_sarkari_jobs()
