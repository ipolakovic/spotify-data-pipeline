"""
Spotify data ingestion pipeline with incremental fetch.
Fetches new plays since last run (or last 50 if first run).
"""
import os
import sys
from dotenv import load_dotenv

# Add lambda functions to path
sys.path.insert(0, 'lambda-functions/spotify-ingestion/src')

from spotify_client import SpotifyClient
from utils import save_tracks_to_json, get_latest_timestamp, save_state, load_state

load_dotenv()


def main():
    """Run the ingestion pipeline."""
    print("=" * 80)
    print("SPOTIFY DATA INGESTION")
    print("=" * 80)
    
    try:
        # Initialize and authenticate
        print("\n1. Authenticating with Spotify...")
        client = SpotifyClient()
        client.authenticate()
        
        # Load last processed timestamp (None if first run)
        last_timestamp = load_state()
        
        if last_timestamp:
            print(f"\n2. Fetching new plays since last run...")
            print(f"   Last timestamp: {last_timestamp}")
            tracks = client.get_recent_plays_since(last_timestamp)
        else:
            print(f"\n2. First run - fetching last 50 plays (Spotify API limit)...")
            # For first run, fetch without 'after' parameter
            tracks = client.get_recently_played(limit=50)
        
        if not tracks:
            print("\n⚠️  No new tracks found!")
            print("   (Listen to more music and run again)")
            return
        
        # Summary
        print(f"\n3. Fetched {len(tracks)} plays")
        print(f"   Unique tracks: {len(set(t['track_id'] for t in tracks))}")
        print(f"   Unique artists: {len(set(t['artist_id'] for t in tracks))}")
        print(f"   Range: {tracks[-1]['played_at']} → {tracks[0]['played_at']}")
        
        # Save data
        print("\n4. Saving data...")
        filepath = save_tracks_to_json(tracks)
        
        # Update state
        latest_timestamp = get_latest_timestamp(tracks)
        save_state(latest_timestamp)
        
        print(f"\n✅ SUCCESS!")
        print(f"   Data: {filepath}")
        print(f"   State updated: {latest_timestamp}")
        
        print("\n💡 Note: Spotify API limited to 50 plays.")
        print("   Run every 12-24 hours to avoid data loss.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise


if __name__ == "__main__":
    main()