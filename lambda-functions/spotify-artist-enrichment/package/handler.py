"""
AWS Lambda handler for Spotify artist enrichment.
Fetches artist details for all unique artists found in plays data.
"""
import os
import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

from artist_client import SpotifyArtistClient

BUCKET_NAME = os.environ.get('S3_BUCKET', 'spotify-pipeline-ivan-1766559048')


def lambda_handler(event, context):
    """Lambda entry point."""
    print("Starting artist enrichment...")
    
    try:
        s3 = boto3.client('s3')
        spotify = SpotifyArtistClient()
        spotify.authenticate()
        
        print("Extracting unique artists from plays data...")
        artist_ids = get_unique_artists_from_s3(s3, BUCKET_NAME)
        
        if not artist_ids:
            print("No artists found in plays data")
            return {'statusCode': 200, 'body': 'No artists to process'}
        
        print(f"Found {len(artist_ids)} unique artists")
        
        print("Fetching artist details from Spotify API...")
        artists = spotify.get_artists(list(artist_ids))
        
        if not artists:
            print("No artist data fetched")
            return {'statusCode': 200, 'body': 'No artist data retrieved'}
        
        print(f"Fetched details for {len(artists)} artists")
        
        print("Saving artist data to S3...")
        s3_key = save_artists_to_s3(s3, BUCKET_NAME, artists)
        
        print(f"✅ Successfully saved to: s3://{BUCKET_NAME}/{s3_key}")
        
        return {'statusCode': 200, 'body': f'Processed {len(artists)} artists'}
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise


def get_unique_artists_from_s3(s3, bucket: str) -> set:
    """Extract unique artist IDs from all plays files."""
    artist_ids = set()
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix='raw/')
        
        file_count = 0
        for page in pages:
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                
                if not key.endswith('.json'):
                    continue
                
                try:
                    response = s3.get_object(Bucket=bucket, Key=key)
                    data = json.loads(response['Body'].read())
                    
                    for track in data.get('tracks', []):
                        artist_id = track.get('artist_id')
                        if artist_id:
                            artist_ids.add(artist_id)
                    
                    file_count += 1
                    
                except Exception as e:
                    print(f"Warning: Failed to process {key}: {str(e)}")
                    continue
        
        print(f"Scanned {file_count} play files")
        
    except ClientError as e:
        print(f"Error reading from S3: {str(e)}")
        raise
    
    return artist_ids


def save_artists_to_s3(s3, bucket: str, artists: list) -> str:
    """Save artist data to S3 with date partitioning."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    s3_key = f"artists/year={now.year}/month={now.month:02d}/day={now.day:02d}/artist_data_{timestamp}.json"
    
    data = {
        "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "artist_count": len(artists),
        "artists": artists
    }
    
    try:
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=json.dumps(data, indent=2, ensure_ascii=False),
            ContentType='application/json'
        )
        print(f"Saved {len(artists)} artists to s3://{bucket}/{s3_key}")
        
    except ClientError as e:
        print(f"Error saving to S3: {str(e)}")
        raise
    
    return s3_key
