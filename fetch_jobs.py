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
    headers = {'User-Agent': 'Mozilla/5.0'} # Pretend to be a browser
    
    seen_jobs = load_seen_jobs()
    new_job_ids = []
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # SarkariResult lists jobs inside a div with id='post' or within <ul> tags
        # We look for all links within the main content area
        job_links = soup.select("#post ul li a")
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        for link in job_links[:20]: # Check the latest 20 items
            title = link.text.strip()
            href = link.get('href')
            
            # Create a unique ID based on the URL
            job_id = hashlib.md5(href.encode()).hexdigest()
            
            if job_id not in seen_jobs:
                # Some links are relative, fix them if necessary
                full_link = href if href.startswith('http') else f"https://www.sarkariresult.com{href}"
                
                message = f"🆕 *Sarkari Result Update*\n\n🔹 *{title}*\n🔗 [Apply / Details]({full_link})"
                
                # Send to Telegram
                tel_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(tel_url, data={
                    "chat_id": chat_id, 
                    "text": message, 
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": "true"
                })
                
                new_job_ids.append(job_id)

        if new_job_ids:
            save_seen_jobs(new_job_ids)
            print(f"Sent {len(new_job_ids)} new jobs.")
        else:
            print("No new updates found.")

    except Exception as e:
        print(f"Error fetching Sarkari Result: {e}")

if __name__ == "__main__":
    fetch_sarkari_jobs()
