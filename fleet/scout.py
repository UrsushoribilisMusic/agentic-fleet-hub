#!/usr/bin/env python3
"""
Scout script — daily YouTube API pull to PocketBase

Fetches daily YouTube metrics for The Classical Remix catalog and updates
the PocketBase songs collection.

Dependencies:
- requests
- google-auth, google-auth-oauthlib, google-auth-httplib2
- google-api-python-client

Environment:
- TCR_PB_TOKEN: PocketBase admin token for songs collection write access
- TCR_YT_API_KEY: YouTube Data API v3 key
- TCR_YT_CHANNEL_ID: The Classical Remix channel ID
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

import requests
from googleapiclient.discovery import build

# --- Configuration ---
PB_URL = "http://localhost:8090"
PB_COLLECTION = "songs"

# --- PocketBase Client ---
class PocketBaseClient:
    def __init__(self, base_url, collection, token):
        self.base_url = base_url.rstrip('/')
        self.collection = collection
        self.token = token

    def get_songs(self):
        url = f"{self.base_url}/api/collections/{self.collection}/records"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json().get('items', [])

    def update_song(self, record_id, data):
        url = f"{self.base_url}/api/collections/{self.collection}/records/{record_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.patch(url, headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()

# --- YouTube Client ---
class YouTubeClient:
    def __init__(self, api_key):
        self.service = build('youtube', 'v3', developerKey=api_key)

    def get_video_metrics(self, video_id):
        parts = [
            'snippet', 'statistics', 'contentDetails',
            'status', 'recordingDetails', 'topicDetails'
        ]
        request = self.service.videos().list(
            part=','.join(parts),
            id=video_id
        )
        response = request.execute()
        if not response.get('items'):
            return None
        return response['items'][0]

# --- Scout Logic ---

def fetch_and_update(pb_client, yt_client):
    songs = pb_client.get_songs()
    updated = 0
    for song in songs:
        video_id = song.get('video_id')
        if not video_id:
            continue
        metrics = yt_client.get_video_metrics(video_id)
        if not metrics:
            continue

        stats = metrics.get('statistics', {})
        snippet = metrics.get('snippet', {})

        update_data = {
            'views': int(stats.get('viewCount', 0)),
            'likes': int(stats.get('likeCount', 0)),
            'comments': int(stats.get('commentCount', 0)),
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'published_at': snippet.get('publishedAt', ''),
        }

        pb_client.update_song(song['id'], update_data)
        updated += 1

    return updated

# --- Main ---

def main():
    # Load tokens
    pb_token = os.environ.get('TCR_PB_TOKEN')
    yt_api_key = os.environ.get('TCR_YT_API_KEY')

    if not pb_token:
        print("ERROR: TCR_PB_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    if not yt_api_key:
        print("ERROR: TCR_YT_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    pb = PocketBaseClient(PB_URL, PB_COLLECTION, pb_token)
    yt = YouTubeClient(yt_api_key)

    print(f"[{datetime.utcnow().isoformat()}] Starting scout run...")
    updated = fetch_and_update(pb, yt)
    print(f"[{datetime.utcnow().isoformat()}] Updated {updated} songs.")

if __name__ == '__main__':
    main()