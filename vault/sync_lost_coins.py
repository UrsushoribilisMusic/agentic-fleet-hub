import json
import sqlite3
import os
import subprocess
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG ---
DB_PATH = "/opt/crm-api/data/crm.db"
SHEET_ID = "1axs3rNozxIsjsLDYcENWpKHhwfX3LZ6fXHbgRYUyUKs"

def get_vault_secret(name):
    try:
        res = subprocess.run(
            ["infisical", "secrets", "get", name, "--domain=https://eu.infisical.com/api", "--env=dev", "--plain"],
            capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"Vault error: {e}")
        return None

def sync():
    # 1. Auth with Google
    print("Reading credentials from file...")
    try:
        with open("/opt/crm-api/service_account.json", "r") as f:
            sa_json = f.read()
    except:
        print("Error: /opt/crm-api/service_account.json not found")
        return
    
    creds = Credentials.from_service_account_info(
        json.loads(sa_json),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet("Shorts")
    data = worksheet.get_all_records()
    
    # 2. Connect to local DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("Clearing old demo data...")
    # Optional: Clear demo data first? For now we just append/update.
    
    # 3. Create Contacts if missing
    platforms = ["YouTube Shorts", "TikTok", "Instagram"]
    platform_ids = {}
    for p in platforms:
        cur.execute("INSERT OR IGNORE INTO contacts (name, type) VALUES (?, 'Platform')", (p,))
        cur.execute("SELECT id FROM contacts WHERE name = ?", (p,))
        platform_ids[p] = cur.fetchone()[0]
    
    # 4. Process Spreadsheet Rows
    print(f"Processing {len(data)} rows...")
    for row in data:
        theme = row.get("Video Theme", "")
        if "Lost Coins" not in theme: continue
        
        # Extract Chapter Number (e.g., "Chapter 1")
        title = row.get("Title", "")
        chapter_num = 0
        if "Chapter" in title:
            try: chapter_num = int(title.split("Chapter")[1].split()[0])
            except: pass
        
        if chapter_num == 0: continue
        
        # Create/Update Task (Deal)
        task_name = f"The Lost Coins: Chapter {chapter_num}"
        status = "Won" if chapter_num <= 12 else "Active"
        
        cur.execute("INSERT OR IGNORE INTO deals (name, status, value) VALUES (?, ?, ?)", 
                    (task_name, status, 0))
        cur.execute("SELECT id FROM deals WHERE name = ?", (task_name,))
        deal_id = cur.fetchone()[0]
        
        # Add Activities (Views/Likes)
        post_date = row.get("Date Posted", "")
        if post_date:
            try:
                # Format: YYYY-MM-DD
                dt = datetime.strptime(post_date, "%Y-%m-%d")
                
                # Activity for each platform
                metrics = {
                    "YouTube Shorts": (row.get("YT Views", 0), row.get("YT Likes", 0)),
                    "TikTok": (row.get("TikTok Views", 0), row.get("TikTok Likes", 0)),
                    "Instagram": (row.get("Insta Views", 0), row.get("Insta Likes", 0))
                }
                
                for platform, (views, likes) in metrics.items():
                    if views and views != '':
                        note = f"Stats: {views} views, {likes} likes."
                        cur.execute("""
                            INSERT OR IGNORE INTO activities (deal_id, contact_id, type, note, date) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (deal_id, platform_ids[platform], 'Social Post', note, post_date))
                        
                        # Also add to Calendar (Tasks table in CRM acts as calendar)
                        cur.execute("""
                            INSERT OR IGNORE INTO tasks (deal_id, title, due_date, status)
                            VALUES (?, ?, ?, 'Completed')
                        """, (deal_id, f"Published to {platform}", post_date, 'Completed'))
            except Exception as e:
                print(f"Error parsing date {post_date}: {e}")

    conn.commit()
    conn.close()
    print("Sync complete!")

if __name__ == "__main__":
    sync()
