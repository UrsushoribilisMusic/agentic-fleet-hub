#!/usr/bin/env python3
"""
TCR Campaign Manager: Generates a daily analytics briefing for Telegram.
"""

import os
import json
import requests
from datetime import datetime

PB_URL = "http://localhost:8090/api"
ANALYTICS_URL = "https://api.robotross.art/tracker/analytics"
TASK_ID = "tn28lgsjjxl9v5x" # TCR-8 Task ID
MONTHLY_BUDGET_CAP = 150.0

def get_monthly_spend():
    """Calculate total CHF spent this month from ad_performance."""
    try:
        # Start of current month
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        r = requests.get(f"{PB_URL}/collections/ad_performance/records", 
                         params={"filter": f'created >= "{start_of_month}"', "perPage": 200},
                         timeout=10)
        items = r.json().get("items", [])
        return sum(float(i.get("spend_chf", 0)) for i in items)
    except:
        return 0.0

def get_budget():
    try:
        r = requests.get(f"{PB_URL}/collections/config/records?filter=key='music_daily_budget'", timeout=10)
        items = r.json().get("items", [])
        if items:
            return float(items[0]["value"])
    except:
        pass
    return 5.0 # Default changed to 5.0 to better fit 150/month

def get_songs():
    try:
        r = requests.get(f"{PB_URL}/collections/songs/records?perPage=200&sort=-combined_views", timeout=10)
        return r.json().get("items", [])
    except:
        return []

def get_recommendations():
    try:
        r = requests.get(ANALYTICS_URL, timeout=10)
        return r.json().get("recommendations", [])
    except:
        return []

def format_briefing():
    today = datetime.now().strftime("%Y-%m-%d")
    daily_budget = get_budget()
    monthly_spend = get_monthly_spend()
    songs = get_songs()
    recommendations = get_recommendations()
    
    # 1. Top performers (24h delta)
    # Using combined_views as delta is not yet populated by Scout
    top_performers = sorted(songs, key=lambda x: x.get("combined_views", 0), reverse=True)[:3]
    
    # 2. Ad-eligible videos (>500 views, not yet boosted)
    ad_eligible = [s for s in songs if s.get("ad_eligible") and "boosted" not in s.get("notes", "").lower()]
    
    # 3. Recommended boost
    top_rec = recommendations[0] if recommendations else None
    
    # Adjust budget if monthly cap is close
    remaining_monthly = MONTHLY_BUDGET_CAP - monthly_spend
    proposed_spend = min(daily_budget, remaining_monthly) if remaining_monthly > 0 else 0.0
    
    msg = f"🎵 TCR Daily Brief — {today}\n\n"
    
    msg += f"Monthly Status: CHF {monthly_spend:.2f} / {MONTHLY_BUDGET_CAP:.2f} spent.\n"
    msg += "Top performers (Lifetime Views):\n"
    for s in top_performers:
        msg += f"- {s['piece']} ({s['style']}): {s['combined_views']} views\n"
    
    msg += "\nAd-eligible videos (>500 views):\n"
    if ad_eligible:
        for s in ad_eligible[:5]:
            msg += f"- {s['piece']} ({s['style']}): {s['combined_views']} views\n"
    else:
        msg += "- None today\n"
        
    msg += "\nRecommended boost today:\n"
    if top_rec and proposed_spend > 0:
        msg += f"- {top_rec['piece']} ({top_rec['style']}) — Predicted avg: {top_rec['predicted_avg']}\n"
        msg += f"Proposed spend: CHF {proposed_spend:.2f}\n"
        msg += "Daily Split:\n"
        msg += f"  - CHF {proposed_spend * 0.6:.2f} Content targeting\n"
        msg += f"  - CHF {proposed_spend * 0.3:.2f} Custom intent\n"
        msg += f"  - CHF {proposed_spend * 0.1:.2f} Discovery\n"
    elif proposed_spend <= 0:
        msg += "- ⚠️ Monthly budget cap reached. No spend recommended.\n"
    else:
        msg += "- No recommendations available.\n"
        
    msg += "\nTo approve send: GO TCR\nReply SKIP to skip today."
    
    return msg

def main():
    briefing = format_briefing()
    print(briefing)
    
    # Post to PocketBase as task output comment
    try:
        r = requests.post(f"{PB_URL}/collections/comments/records", json={
            "task_id": TASK_ID,
            "agent": "gem",
            "content": briefing,
            "type": "output"
        })
        if r.status_code == 200:
            print("Successfully posted briefing to PocketBase.")
        else:
            print(f"Failed to post briefing: {r.text}")
    except Exception as e:
        print(f"Error posting briefing: {e}")

if __name__ == "__main__":
    main()
