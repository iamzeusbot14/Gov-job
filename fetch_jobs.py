import os
import requests
from bs4 import BeautifulSoup
import hashlib
import time

# --- SETUP PATHS ---
# This ensures the bot finds seen_jobs.txt in the same folder as the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "seen_jobs.txt")

def load_seen_jobs():
    """Reads the database file and returns a set of job hashes."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            # Use splitlines to avoid issues with hidden characters
            data = set(line.strip() for line in f if line.strip())
            print(f"✅ Loaded {len(data)} existing jobs from database.")
            return data
    print("ℹ️ No database found. Starting fresh.")
    return set()

def save_seen_jobs(job_ids):
    """Appends new job hashes to the database file."""
    if not job_ids:
        return
    with open(DB_FILE, "a") as f:
        for job_id in job_ids:
            f.write(f"{job_id}\n")
    print(f"💾 Saved {len(job_ids)} new jobs to database.")

def send_telegram(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("❌ Error: Telegram credentials missing!")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": "true"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ Telegram Error: {e}")

def scrape_jobs():
    seen_jobs = load_seen_jobs()
    new_job_ids = []
    
    # Trusted Sources
    sources = [
        {"name": "Sarkari Result", "url": "https://www.sarkariresult.com/latestjob/", "selector": "#post ul li a", "base": "https://www.sarkariresult.com"},
        {"name": "Free Job Alert", "url": "https://www.freejobalert.com/latest-notifications/", "selector": "table.listing tr td a", "base": ""},
    ]

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for src in sources:
        try:
            print(f"🔍 Checking {src['name']}...")
            res = requests.get(src['url'], headers=headers, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.select(src['selector'])

            for link in links[:25]: # Look at top 25 links
                title = link.get_text(strip=True)
                href = link.get('href', '')
                if not href or len(title) < 10: continue

                full_link = href if href.startswith('http') else f"{src['base']}{href}"
                
                # Create a unique ID for this job
                job_id = hashlib.md5(full_link.encode()).hexdigest()

                # --- THE DUPLICATE CHECK ---
                if job_id not in seen_jobs:
                    emoji = "🚨" if any(k in title.upper() for k in ["SSC", "UPSC", "RAILWAY", "BANK", "POLICE"]) else "🆕"
                    msg = f"{emoji} *[{src['name']}] Update*\n\n🔹 *{title}*\n🔗 [Apply / Details]({full_link})"
                    
                    send_telegram(msg)
                    new_job_ids.append(job_id)
                    seen_jobs.add(job_id) # Add to temporary set to avoid duplicates in same run
                    time.sleep(1) 

        except Exception as e:
            print(f"⚠️ Error on {src['name']}: {e}")

    # Save the new jobs back to the file
    save_seen_jobs(new_job_ids)

if __name__ == "__main__":
    scrape_jobs()
