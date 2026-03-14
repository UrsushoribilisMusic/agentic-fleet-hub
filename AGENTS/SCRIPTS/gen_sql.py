import json
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1axs3rNozxIsjsLDYcENWpKHhwfX3LZ6fXHbgRYUyUKs"

def generate_sql():
    with open("local_sa.json", "r") as f:
        sa_json = json.load(f)
    
    creds = Credentials.from_service_account_info(
        sa_json,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet("Shorts")
    data = worksheet.get_all_records()
    
    sql = []
    # Contacts
    platforms = ["YouTube Shorts", "TikTok", "Instagram"]
    for p in platforms:
        sql.append(f"INSERT OR IGNORE INTO contacts (name, type) VALUES ('{p}', 'Platform');")
    
    # Process Rows
    for row in data:
        theme = row.get("Video Theme", "")
        if "Lost Coins" not in theme: continue
        
        title = row.get("Title", "")
        chapter_num = 0
        if "Chapter" in title:
            parts = title.split("Chapter")
            if len(parts) > 1:
                try: chapter_num = int(parts[1].strip().split()[0])
                except: pass
        
        if chapter_num == 0: continue
        
        task_name = f"The Lost Coins: Chapter {chapter_num}"
        status = "Won" if chapter_num <= 12 else "Active"
        sql.append(f"INSERT OR IGNORE INTO deals (name, status, value) VALUES ('{task_name}', '{status}', 0);")
        
        post_date = row.get("Date Posted", "")
        if post_date:
            metrics = [
                ("YouTube Shorts", row.get("YT Views", 0), row.get("YT Likes", 0)),
                ("TikTok", row.get("TikTok Views", 0), row.get("TikTok Likes", 0)),
                ("Instagram", row.get("Insta Views", 0), row.get("Insta Likes", 0))
            ]
            
            for platform, views, likes in metrics:
                if views and str(views).strip():
                    note = f"Stats: {views} views, {likes} likes."
                    # We use sub-selects to find IDs
                    sql.append(f"INSERT OR IGNORE INTO activities (deal_id, contact_id, type, note, date) SELECT d.id, c.id, 'Social Post', '{note}', '{post_date}' FROM deals d, contacts c WHERE d.name='{task_name}' AND c.name='{platform}';")
                    sql.append(f"INSERT OR IGNORE INTO tasks (deal_id, title, due_date, status) SELECT d.id, 'Published to {platform}', '{post_date}', 'Completed' FROM deals d WHERE d.name='{task_name}';")

    with open("lost_coins.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(sql))

if __name__ == "__main__":
    generate_sql()
