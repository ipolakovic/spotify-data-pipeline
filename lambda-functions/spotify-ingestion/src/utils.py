"""
Utility functions for data persistence and state management.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

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
    
    # Generate filename with timestamp if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"spotify_plays_{timestamp}.json"
    
    filepath = os.path.join(output_dir, filename)
    
    # Prepare data with metadata
    data = {
        "fetched_at": datetime.now().isoformat(),
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