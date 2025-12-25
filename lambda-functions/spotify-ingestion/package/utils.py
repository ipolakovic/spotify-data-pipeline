"""
Utility functions for data persistence and state management.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone
import logging
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


def save_tracks_to_json(
    tracks: List[Dict],
    output_dir: str = "data",
    filename: Optional[str] = None
) -> str:
    """
    Save tracks to a JSON file.
    
    Args:
        tracks: List of track dictionaries
        output_dir: Directory to save file (created if doesn't exist)
        filename: Optional custom filename. If None, uses timestamp.
        
    Returns:
        Path to saved file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp once
    now = datetime.now(timezone.utc)
    
    # Generate filename with timestamp if not provided
    if filename is None:
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"spotify_plays_{timestamp}.json"
    
    filepath = os.path.join(output_dir, filename)
    
    # Prepare data with metadata
    data = {
        "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "track_count": len(tracks),
        "tracks": tracks
    }
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(tracks)} tracks to {filepath}")
    return filepath


def load_tracks_from_json(filepath: str) -> List[Dict]:
    """
    Load tracks from a JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of track dictionaries
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tracks = data.get('tracks', [])
    logger.info(f"Loaded {len(tracks)} tracks from {filepath}")
    return tracks


def get_latest_timestamp(tracks: List[Dict]) -> Optional[int]:
    """
    Get the most recent timestamp from a list of tracks.
    
    Args:
        tracks: List of track dictionaries
        
    Returns:
        Most recent played_at_timestamp, or None if no tracks
    """
    if not tracks:
        return None
    
    return max(track['played_at_timestamp'] for track in tracks)


def get_oldest_timestamp(tracks: List[Dict]) -> Optional[int]:
    """
    Get the oldest timestamp from a list of tracks.
    
    Args:
        tracks: List of track dictionaries
        
    Returns:
        Oldest played_at_timestamp, or None if no tracks
    """
    if not tracks:
        return None
    
    return min(track['played_at_timestamp'] for track in tracks)



def save_state(last_timestamp: int, state_dir: str = "data") -> str:
    """
    Save the last processed timestamp to a state file.
    
    This enables incremental fetches - we only fetch plays after this timestamp.
    
    Args:
        last_timestamp: Unix timestamp in milliseconds of the last processed play
        state_dir: Directory to save state file
        
    Returns:
        Path to state file
    """
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    
    state_file = os.path.join(state_dir, "last_run_state.json")
    
    state = {
        "last_processed_timestamp": last_timestamp,
        "last_processed_at": datetime.fromtimestamp(last_timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    
    logger.info(f"Saved state: last_timestamp={last_timestamp}")
    return state_file


def load_state(state_dir: str = "data") -> Optional[int]:
    """
    Load the last processed timestamp from state file.
    
    Args:
        state_dir: Directory where state file is stored
        
    Returns:
        Last processed timestamp in milliseconds, or None if no state exists
    """
    state_file = os.path.join(state_dir, "last_run_state.json")
    
    if not os.path.exists(state_file):
        logger.info("No previous state found - this is the first run")
        return None
    
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    last_timestamp = state.get('last_processed_timestamp')
    logger.info(f"Loaded state: last_timestamp={last_timestamp}")
    return last_timestamp


def is_first_run(state_dir: str = "data") -> bool:
    """
    Check if this is the first run (no state file exists).
    
    Args:
        state_dir: Directory where state file would be stored
        
    Returns:
        True if first run, False otherwise
    """
    state_file = os.path.join(state_dir, "last_run_state.json")
    return not os.path.exists(state_file)


def save_tracks_to_s3(
    tracks: List[Dict],
    bucket_name: str,
    prefix: str = "raw"
) -> str:
    """
    Save tracks to S3 with date partitioning.
    
    Args:
        tracks: List of track dictionaries
        bucket_name: S3 bucket name
        prefix: S3 key prefix (e.g., 'raw', 'processed')
        
    Returns:
        S3 key where data was saved
    """
    if not tracks:
        logger.warning("No tracks to save")
        return ""
    
    # Create S3 client
    s3 = boto3.client('s3')
    
    # Generate timestamp once
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    s3_key = f"{prefix}/year={now.year}/month={now.month:02d}/day={now.day:02d}/spotify_plays_{timestamp}.json"
    
    # Prepare data with metadata
    data = {
        "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "track_count": len(tracks),
        "tracks": tracks
    }
    
    # Upload to S3
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json.dumps(data, indent=2, ensure_ascii=False),
        ContentType='application/json'
    )
    
    logger.info(f"Saved {len(tracks)} tracks to s3://{bucket_name}/{s3_key}")
    return s3_key

def save_state_to_s3(
    last_timestamp: int,
    bucket_name: str,
    key: str = "state/last_run_state.json"
) -> None:
    """
    Save pipeline state to S3.
    
    Args:
        last_timestamp: Unix timestamp in milliseconds of last processed play
        bucket_name: S3 bucket name
        key: S3 key for state file
    """
    s3 = boto3.client('s3')
    
    state = {
        "last_processed_timestamp": last_timestamp,
        "last_processed_at": datetime.fromtimestamp(last_timestamp / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(state, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Saved state to s3://{bucket_name}/{key}: last_timestamp={last_timestamp}")

def load_state_from_s3(
    bucket_name: str,
    key: str = "state/last_run_state.json"
) -> Optional[int]:
    """
    Load pipeline state from S3.
    
    Args:
        bucket_name: S3 bucket name
        key: S3 key for state file
        
    Returns:
        Last processed timestamp in milliseconds, or None if no state exists
    """
    s3 = boto3.client('s3')
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=key)
        state = json.loads(response['Body'].read())
        last_timestamp = state.get('last_processed_timestamp')
        logger.info(f"Loaded state from S3: last_timestamp={last_timestamp}")
        return last_timestamp
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info("No previous state found in S3 - this is the first run")
            return None
        raise  # Re-raise other errors