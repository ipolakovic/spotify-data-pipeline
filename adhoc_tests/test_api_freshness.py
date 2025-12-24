import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
    scope="user-read-recently-played",
    cache_path=".spotify_cache"
))

result = sp.current_user_recently_played(limit=1)

if result['items']:
    track = result['items'][0]
    played_at = track['played_at']
    track_name = track['track']['name']
    artist = track['track']['artists'][0]['name']
    
    # Parse timestamp
    dt = datetime.fromisoformat(played_at.replace('Z', '+00:00'))
    minutes_ago = (datetime.now(dt.tzinfo) - dt).total_seconds() / 60
    
    print(f"Most recent play:")
    print(f"  Track: {track_name} - {artist}")
    print(f"  Played at: {played_at}")
    print(f"  That was {minutes_ago:.1f} minutes ago")
    
    if minutes_ago < 5:
        print("\n✅ API is VERY fresh (< 5 minutes delay)")
    elif minutes_ago < 15:
        print("\n⚠️  API has some delay (5-15 minutes)")
    else:
        print("\n❌ API is delayed (> 15 minutes)")
else:
    print("No plays found!")
