"""Test top artists all-time."""

import json
import os

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

scope = "user-top-read"
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=scope,
        cache_path=".spotify_cache",
    )
)

print("Fetching your all-time top artists...\n")
results = sp.current_user_top_artists(time_range="long_term", limit=50)

print(f"Total artists returned: {len(results['items'])}\n")
print("Your Top 20 All-Time Artists:")
print("=" * 80)

for i, artist in enumerate(results["items"][:20], 1):
    genres = ", ".join(artist["genres"][:3]) if artist["genres"] else "No genres listed"
    print(f"{i}. {artist['name']}")
    print(f"   Genres: {genres}")
    print(f"   Popularity: {artist['popularity']}")
    print(f"   Followers: {artist['followers']['total']:,}")
    print()

# Save full results
with open("top_artists_sample.json", "w") as f:
    json.dump(results, f, indent=2)

print("Full data saved to: top_artists_sample.json")
