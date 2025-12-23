"""
Local test of the full ingestion pipeline.
This simulates what will run in Lambda.
"""
import os
import sys
from dotenv import load_dotenv

# Add lambda functions to path
sys.path.insert(0, 'lambda-functions/spotify-ingestion/src')

from spotify_client import SpotifyClient
from utils import save_tracks_to_json, get_latest_timestamp, get_oldest_timestamp

# Load environment variables
load_dotenv()


def main():
    """Run the ingestion pipeline locally."""
    print("=" * 80)
    print("SPOTIFY DATA INGESTION - LOCAL TEST")
    print("=" * 80)
    
    try:
        # Initialize client
        print("\n1. Initializing Spotify client...")
        client = SpotifyClient()
        client.authenticate()
        
        # Fetch all available history
        print("\n2. Fetching all available listening history...")
        tracks = client.get_all_recent_history()
        
        if not tracks:
            print("⚠️  No tracks found!")
            return
        
        # Show summary
        print(f"\n3. Summary:")
        print(f"   Total plays: {len(tracks)}")
        print(f"   Unique tracks: {len(set(t['track_id'] for t in tracks))}")
        print(f"   Unique artists: {len(set(t['artist_id'] for t in tracks))}")
        print(f"   Date range: {tracks[0]['played_at']} to {tracks[-1]['played_at']}")
        
        # Save to file
        print("\n4. Saving to local file...")
        filepath = save_tracks_to_json(tracks, output_dir="data")
        
        print(f"\n✅ SUCCESS! Data saved to: {filepath}")
        print("\nNext steps:")
        print("- Tomorrow: Run this again to test incremental fetch")
        print("- Week 2: Deploy to Lambda and save to S3")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise


if __name__ == "__main__":
    main()