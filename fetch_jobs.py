import requests
import os

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

def fetch_and_notify():
    api_url = "https://jobful-api.vercel.app/freejobalert"
    seen_jobs = load_seen_jobs()
    new_job_ids = []
    
    try:
        response = requests.get(api_url)
        jobs = response.json()
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        for job in jobs[:15]: # Check the latest 15
            # Create a unique ID (title + link works if API has no ID)
            job_id = str(hash(job['link'])) 
            
            if job_id not in seen_jobs:
                message = f"🆕 *NEW GOVT JOB*\n\n🔹 *{job['title']}*\n🔗 [View Details]({job['link']})"
                
                # Send to Telegram
                tel_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(tel_url, data={
                    "chat_id": chat_id, 
                    "text": message, 
                    "parse_mode": "Markdown"
                })
                
                new_job_ids.append(job_id)

        if new_job_ids:
            save_seen_jobs(new_job_ids)
            print(f"Sent {len(new_job_ids)} new jobs.")
        else:
            print("No new jobs found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_notify()
  
