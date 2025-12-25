"""AWS Lambda handler for Spotify data ingestion."""

import os

from spotify_client import SpotifyClient
from utils import (
    get_latest_timestamp,
    load_state_from_s3,
    save_state_to_s3,
    save_tracks_to_s3,
)

BUCKET_NAME = os.environ.get("S3_BUCKET", "spotify-pipeline-ivan-1766559048")


def lambda_handler(event, context):
    """Lambda entry point."""
    print("Starting Spotify data ingestion...")

    try:
        print("Authenticating with Spotify...")
        client = SpotifyClient()
        client.authenticate()

        print(f"Checking S3 for previous state: {BUCKET_NAME}")
        last_timestamp = load_state_from_s3(BUCKET_NAME)

        if last_timestamp:
            print(f"Incremental fetch since: {last_timestamp}")
            tracks = client.get_recent_plays_since(last_timestamp)
        else:
            print("First run - fetching last 50 plays")
            tracks = client.get_recently_played(limit=50)

        if not tracks:
            print("No new tracks found")
            return {"statusCode": 200, "body": "No new tracks"}

        print(f"Fetched {len(tracks)} tracks")

        s3_key = save_tracks_to_s3(tracks, BUCKET_NAME)
        print(f"Saved to: s3://{BUCKET_NAME}/{s3_key}")

        latest_timestamp = get_latest_timestamp(tracks)
        save_state_to_s3(latest_timestamp, BUCKET_NAME)
        print(f"State updated: {latest_timestamp}")

        return {"statusCode": 200, "body": f"Processed {len(tracks)} tracks"}

    except Exception as e:
        print(f"Error: {str(e)}")
        raise
