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
        "last_processed_at": datetime.fromtimestamp(last_timestamp / 1000).isoformat(),
        "updated_at": datetime.now().isoformat()
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