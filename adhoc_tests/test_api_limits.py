"""Test to understand Spotify API history limits."""
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime

load_dotenv()

scope = "user-read-recently-played"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
    scope=scope,
    cache_path=".spotify_cache"
))

print("Fetching page 1...")
page1 = sp.current_user_recently_played(limit=50)
print(f"Page 1: {len(page1['items'])} tracks")

if page1['items']:
    oldest_p1 = page1['items'][-1]
    print(f"Oldest from page 1: {oldest_p1['played_at']}")
    
    # Get timestamp
    oldest_ts = int(datetime.fromisoformat(oldest_p1['played_at'].replace('Z', '+00:00')).timestamp() * 1000)
    
    print(f"\nFetching page 2 (after timestamp {oldest_ts})...")
    page2 = sp.current_user_recently_played(limit=50, after=oldest_ts)
    print(f"Page 2: {len(page2['items'])} tracks")
    
    if page2['items']:
        oldest_p2 = page2['items'][-1]
        print(f"Oldest from page 2: {oldest_p2['played_at']}")
        
        # Check if there's overlap
        p1_ids = [t['played_at'] for t in page1['items']]
        p2_ids = [t['played_at'] for t in page2['items']]
        overlap = set(p1_ids) & set(p2_ids)
        print(f"\nOverlap between pages: {len(overlap)} tracks")
    else:
        print("No tracks in page 2")

print("\nCHECK: Go to https://www.spotify.com/account/privacy/")
print("Request your data - it will show ALL your listening history")
