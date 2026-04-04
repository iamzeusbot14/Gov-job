import os
import requests
from bs4 import BeautifulSoup
import hashlib
import time

# storage configuration
db_file = "seen_jobs.txt"

def load_seen_jobs():
    """loads all historical job hashes into a set for o(1) lookup."""
    if os.path.exists(db_file):
        with open(db_file, "r") as f:
            # filters for valid 32-character md5 hashes
            return set(line.strip() for line in f if len(line.strip()) == 32)
    return set()

def save_seen_jobs(updated_set):
    """saves the growing database, sorted alphabetically for clean git history."""
    if not updated_set:
        return
    # sorting ensures that the git diff only shows exactly what was added
    sorted_hashes = sorted(list(updated_set))
    with open(db_file, "w") as f:
        f.write("\n".join(sorted_hashes) + "\n")

def send_telegram(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "markdown",
        "disable_web_page_preview": True
    }
    try:
        requests.post(url, data=payload, timeout=15)
    except Exception as e:
        print(f"telegram error: {e}")

def scrape_website():
    """fetches from sarkari result website"""
    jobs = []
    url = "https://sarkariresult.com.cm/category/latest-job/"
    headers = {'user-agent': 'mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.select('h2.entry-title a') or soup.select('.post-content ul li a')
        for link in links[:15]:
            title = link.get_text(strip=True).lower()
            href = link.get('href', '')
            if href and len(title) > 8:
                jobs.append({"title": title, "url": href})
    except: pass
    return jobs

def scrape_telegram():
    """fetches from sarkariexam_info channel via web preview"""
    jobs = []
    url = "https://t.me/s/SarkariExam_info"
    try:
        res = requests.get(url, timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        messages = soup.find_all("div", class_="tgme_widget_message_text")
        for msg in messages[-10:]:
            link_tag = msg.find("a")
            href = link_tag.get("href") if link_tag else None
            text = msg.get_text(separator=" ", strip=True).lower()
            # clean title extraction
            title = text.split('।')[0].split('\n')[0][:70]
            if href and len(title) > 5:
                jobs.append({"title": title, "url": href})
    except: pass
    return jobs

def main():
    # 1. load historical memory
    history_set = load_seen_jobs()
    
    # 2. gather data from all sources
    raw_found = scrape_website() + scrape_telegram()
    
    new_jobs_to_report = []
    
    # 3. cross-source deduplication logic
    for job in raw_found:
        # unique fingerprint based on the url
        job_hash = hashlib.md5(job['url'].encode()).hexdigest()
        
        # only proceed if this link has never been seen before across any source
        if job_hash not in history_set:
            new_jobs_to_report.append(job)
            history_set.add(job_hash)

    # 4. output report
    if new_jobs_to_report:
        report = f"🚀 new updates ({len(new_jobs_to_report)})\n"
        report += "━━━━━━━━━━━━━━━━━━\n\n"
        
        for job in new_jobs_to_report:
            line = f"• [{job['title']}]({job['url']})\n\n"
            if len(report) + len(line) > 4000:
                send_telegram(report)
                report = ""
            report += line
        
        if report:
            send_telegram(report)
        
        # 5. sync the updated memory back to the file
        save_seen_jobs(history_set)
    else:
        print("logs: all jobs are already in history.")

if __name__ == "__main__":
    main()
