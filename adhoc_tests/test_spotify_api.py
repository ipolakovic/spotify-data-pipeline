"""Quick test to explore Spotify API data."""

import json
import os

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# Load credentials
load_dotenv()

# Authenticate
scope = "user-top-read user-read-recently-played"
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=scope,
        cache_path=".spotify_cache",
    )
)

# Fetch top tracks (long term)
print("Fetching your all-time top tracks...\n")
results = sp.current_user_top_tracks(time_range="long_term", limit=50)

print(f"Total tracks returned: {len(results['items'])}\n")
print("Your Top 10 All-Time Tracks:")
print("=" * 60)

for i, track in enumerate(results["items"][:10], 1):
    print(f"{i}. {track['name']}")
    print(f"   Artist: {track['artists'][0]['name']}")
    print(f"   Album: {track['album']['name']}")
    print(f"   Release: {track['album']['release_date']}")
    print(f"   Popularity: {track['popularity']}")
    print()

# Save full results to see all fields
with open("top_tracks_sample.json", "w") as f:
    json.dump(results, f, indent=2)

print("Full data saved to: top_tracks_sample.json")
