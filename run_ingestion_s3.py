"""
Spotify data ingestion pipeline with S3 storage.
Saves data and state to S3 instead of local files.
"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timezone

# Add lambda functions to path
sys.path.insert(0, 'lambda-functions/spotify-ingestion/src')

from spotify_client import SpotifyClient
from utils import (
    save_tracks_to_s3,
    get_latest_timestamp,
    save_state_to_s3,
    load_state_from_s3
)

load_dotenv()

# S3 bucket name
BUCKET_NAME = "spotify-pipeline-ivan-1766559048"


def main():
    """Run the ingestion pipeline with S3 storage."""
    print("=" * 80)
    print("SPOTIFY DATA INGESTION → S3")
    print("=" * 80)
    
    try:
        # Initialize and authenticate
        print("\n1. Authenticating with Spotify...")
        client = SpotifyClient()
        client.authenticate()
        
        # Load last processed timestamp from S3
        print(f"\n2. Checking S3 for previous state...")
        print(f"   Bucket: {BUCKET_NAME}")
        last_timestamp = load_state_from_s3(BUCKET_NAME)
        
        if last_timestamp:
            from datetime import datetime
            readable_time = datetime.fromtimestamp(last_timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"   Found previous state: {readable_time}")
            print(f"\n3. Fetching new plays since last run...")
            tracks = client.get_recent_plays_since(last_timestamp)
        else:
            print(f"   No previous state found")
            print(f"\n3. First run - fetching last 50 plays...")
            tracks = client.get_recently_played(limit=50)
        
        if not tracks:
            print("\n⚠️  No new tracks found!")
            print("   (Listen to more music and run again)")
            return
        
        # Summary
        print(f"\n4. Fetched {len(tracks)} plays")
        print(f"   Unique tracks: {len(set(t['track_id'] for t in tracks))}")
        print(f"   Unique artists: {len(set(t['artist_id'] for t in tracks))}")
        
        # tracks[0] = oldest, tracks[-1] = newest (list is sorted)
        oldest = min(tracks, key=lambda x: x['played_at_timestamp'])
        newest = max(tracks, key=lambda x: x['played_at_timestamp'])
        print(f"   Range: {oldest['played_at']} → {newest['played_at']}")
        
        # Save to S3
        print(f"\n5. Saving to S3...")
        s3_key = save_tracks_to_s3(tracks, BUCKET_NAME)
        print(f"   Data saved to: s3://{BUCKET_NAME}/{s3_key}")
        
        # Update state in S3
        latest_timestamp = get_latest_timestamp(tracks)
        save_state_to_s3(latest_timestamp, BUCKET_NAME)
        print(f"   State updated in S3: {latest_timestamp}")
        
        print(f"\n✅ SUCCESS!")
        print(f"   Check S3: https://s3.console.aws.amazon.com/s3/buckets/{BUCKET_NAME}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
