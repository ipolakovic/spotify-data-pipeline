"""
Spotify API client for fetching listening history.
Production-ready code that works locally and in AWS Lambda.
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpotifyClient:
    """
    Handle Spotify API authentication and data fetching.
    
    Designed to be environment-agnostic (works locally and in Lambda).
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ):
        """
        Initialize Spotify client.
        
        Args:
            client_id: Spotify app client ID (defaults to env var)
            client_secret: Spotify app client secret (defaults to env var)
            redirect_uri: OAuth redirect URI (defaults to env var)
            
        Raises:
            ValueError: If credentials are missing
        """
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('SPOTIFY_REDIRECT_URI')
        
        # Validate credentials
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError(
                "Missing Spotify credentials. Set SPOTIFY_CLIENT_ID, "
                "SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI"
            )
        
        self.sp = None
        logger.info("SpotifyClient initialized")


    def authenticate(self) -> None:
        """
        Authenticate with Spotify API using OAuth.
        
        In Lambda: Uses cached token from S3, uploads refreshed token back
        Locally: Uses browser-based OAuth flow
        """
        scope = "user-read-recently-played"
        
        # Check if running in Lambda (AWS_EXECUTION_ENV exists)
        is_lambda = 'AWS_EXECUTION_ENV' in os.environ
        
        if is_lambda:
            # Lambda: Download cached token from S3
            cache_path = '/tmp/.spotify_cache'
            try:
                import boto3
                s3 = boto3.client('s3')
                bucket = os.environ.get('S3_BUCKET')
                s3.download_file(bucket, 'secrets/spotify_token', cache_path)
                logger.info("Downloaded Spotify token from S3")
            except Exception as e:
                logger.error(f"Failed to download token from S3: {str(e)}")
                raise
            
            open_browser = False
        else:
            # Local: Use current directory
            cache_path = ".spotify_cache"
            open_browser = True
        
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                cache_path=cache_path,
                open_browser=open_browser
            )
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            # Test authentication (this triggers token refresh if needed)
            user = self.sp.current_user()
            logger.info(f"Authenticated as: {user['display_name']} ({user['id']})")
            
            # CRITICAL FIX: If in Lambda, upload refreshed token back to S3
            if is_lambda:
                try:
                    s3.upload_file(cache_path, bucket, 'secrets/spotify_token')
                    logger.info("Uploaded refreshed token to S3")
                except Exception as e:
                    logger.error(f"Failed to upload refreshed token to S3: {str(e)}")
                    # Don't raise - authentication already worked
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    def get_recently_played(
        self, 
        limit: int = 50,
        after: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch recently played tracks from Spotify.
        
        Args:
            limit: Number of tracks to fetch (max 50)
            after: Unix timestamp (ms). Only fetch plays after this time.
            
        Returns:
            List of simplified track dictionaries with play metadata
            
        Raises:
            ValueError: If not authenticated
            spotipy.SpotifyException: If API request fails
        """
        if not self.sp:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        if limit > 50:
            logger.warning(f"Limit {limit} exceeds max 50, using 50")
            limit = 50
        
        try:
            # Build request parameters
            params = {'limit': limit}
            if after:
                params['after'] = after
            
            logger.info(f"Fetching recently played: limit={limit}, after={after}")
            results = self.sp.current_user_recently_played(**params)
            
            # Transform to simpler structure
            tracks = []
            for item in results['items']:
                track_data = {
                    'played_at': item['played_at'],
                    'played_at_timestamp': self._parse_timestamp(item['played_at']),
                    'track_id': item['track']['id'],
                    'track_name': item['track']['name'],
                    'artist_id': item['track']['artists'][0]['id'],
                    'artist_name': item['track']['artists'][0]['name'],
                    'album_id': item['track']['album']['id'],
                    'album_name': item['track']['album']['name'],
                    'release_date': item['track']['album']['release_date'],
                    'duration_ms': item['track']['duration_ms'],
                    'popularity': item['track']['popularity'],
                }
                tracks.append(track_data)
            
            logger.info(f"Fetched {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to fetch recently played: {str(e)}")
            raise
    
    @staticmethod
    def _parse_timestamp(iso_string: str) -> int:
        """
        Convert ISO timestamp to Unix milliseconds.
        
        Args:
            iso_string: ISO 8601 timestamp (e.g., '2024-12-23T10:15:00Z')
            
        Returns:
            Unix timestamp in milliseconds
        """
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    


    def get_all_recent_history(self) -> List[Dict]:
        """
        Fetch all available recently played tracks by paginating through API.
        
        Spotify's "recently played" typically stores ~2 weeks of history.
        This method paginates backward in time until no more tracks are available.
        
        Returns:
            List of all available track play events, ordered oldest to newest
            
        Raises:
            ValueError: If not authenticated
        """
        if not self.sp:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        all_tracks = []
        before_timestamp = None  # Start with most recent
        page = 1
        
        logger.info("Starting full history fetch (paginating backward through time)")
        
        while True:
            try:
                # Build parameters
                params = {'limit': 50}
                if before_timestamp:
                    params['before'] = before_timestamp
                
                # Fetch batch
                logger.info(f"Fetching page {page}: before={before_timestamp}")
                results = self.sp.current_user_recently_played(**params)
                tracks_data = results.get('items', [])
                
                if not tracks_data:
                    logger.info("No more tracks available")
                    break
                
                # Transform tracks
                tracks = []
                for item in tracks_data:
                    track_data = {
                        'played_at': item['played_at'],
                        'played_at_timestamp': self._parse_timestamp(item['played_at']),
                        'track_id': item['track']['id'],
                        'track_name': item['track']['name'],
                        'artist_id': item['track']['artists'][0]['id'],
                        'artist_name': item['track']['artists'][0]['name'],
                        'album_id': item['track']['album']['id'],
                        'album_name': item['track']['album']['name'],
                        'release_date': item['track']['album']['release_date'],
                        'duration_ms': item['track']['duration_ms'],
                        'popularity': item['track']['popularity'],
                    }
                    tracks.append(track_data)
                
                all_tracks.extend(tracks)
                logger.info(f"Page {page}: Fetched {len(tracks)} tracks. Total so far: {len(all_tracks)}")
                
                # Check if we got less than 50 (indicates end of available history)
                if len(tracks) < 50:
                    logger.info("Received fewer than 50 tracks, reached end of history")
                    break
                
                # Update before_timestamp for next iteration
                # Use the OLDEST track's timestamp from this batch
                before_timestamp = tracks[-1]['played_at_timestamp']
                
                page += 1
                
                # Safety check: prevent infinite loops
                if page > 100:
                    logger.warning("Reached 100 pages, stopping to prevent infinite loop")
                    break
                    
            except Exception as e:
                logger.error(f"Error on page {page}: {str(e)}")
                # Don't lose data we already fetched
                if all_tracks:
                    logger.info(f"Returning {len(all_tracks)} tracks fetched before error")
                    break
                else:
                    raise
        
        # Sort by timestamp (oldest first)
        all_tracks.sort(key=lambda x: x['played_at_timestamp'])
        
        logger.info(f"Completed history fetch: {len(all_tracks)} total tracks")
        
        if all_tracks:
            oldest = all_tracks[0]['played_at']
            newest = all_tracks[-1]['played_at']
            logger.info(f"Date range: {oldest} to {newest}")
        
        return all_tracks
    

    def get_recent_plays_since(self, after_timestamp: int) -> List[Dict]:
        """
        Fetch recently played tracks after a specific timestamp.
        
        This is used for incremental fetches - only get new plays since last run.
        
        Args:
            after_timestamp: Unix timestamp in milliseconds. Fetch plays after this time.
            
        Returns:
            List of new track play events since the timestamp
            
        Raises:
            ValueError: If not authenticated
        """
        if not self.sp:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        logger.info(f"Fetching plays after timestamp: {after_timestamp}")
        
        all_new_tracks = []
        current_after = after_timestamp
        page = 1
        
        while True:
            try:
                # Fetch batch using 'after' parameter
                params = {'limit': 50, 'after': current_after}
                
                logger.info(f"Incremental fetch page {page}: after={current_after}")
                results = self.sp.current_user_recently_played(**params)
                tracks_data = results.get('items', [])
                
                if not tracks_data:
                    logger.info("No new tracks found")
                    break
                
                # Transform tracks
                tracks = []
                for item in tracks_data:
                    track_data = {
                        'played_at': item['played_at'],
                        'played_at_timestamp': self._parse_timestamp(item['played_at']),
                        'track_id': item['track']['id'],
                        'track_name': item['track']['name'],
                        'artist_id': item['track']['artists'][0]['id'],
                        'artist_name': item['track']['artists'][0]['name'],
                        'album_id': item['track']['album']['id'],
                        'album_name': item['track']['album']['name'],
                        'release_date': item['track']['album']['release_date'],
                        'duration_ms': item['track']['duration_ms'],
                        'popularity': item['track']['popularity'],
                    }
                    tracks.append(track_data)
                
                all_new_tracks.extend(tracks)
                logger.info(f"Page {page}: Fetched {len(tracks)} new tracks. Total: {len(all_new_tracks)}")
                
                # If we got less than 50, we've fetched everything new
                if len(tracks) < 50:
                    logger.info("Fetched all new tracks")
                    break
                
                # Update timestamp for next page (use newest track from this batch)
                current_after = tracks[0]['played_at_timestamp']
                page += 1
                
                # Safety check
                if page > 10:
                    logger.warning("Reached 10 pages of new data, stopping")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching incremental data on page {page}: {str(e)}")
                if all_new_tracks:
                    logger.info(f"Returning {len(all_new_tracks)} tracks fetched before error")
                    break
                else:
                    raise
        
        # Sort chronologically (oldest first)
        all_new_tracks.sort(key=lambda x: x['played_at_timestamp'])
        
        logger.info(f"Incremental fetch complete: {len(all_new_tracks)} new tracks")
        return all_new_tracks

if __name__ == "__main__":
    """
    Local testing - run this file directly to test Spotify client.
    Usage: python spotify_client.py
    """
    from dotenv import load_dotenv
    
    # Load environment variables from .env
    load_dotenv()
    
    print("=" * 80)
    print("SPOTIFY CLIENT TEST")
    print("=" * 80)
    
    try:
        # Initialize and authenticate
        client = SpotifyClient()
        client.authenticate()
        
        print("\n" + "=" * 80)
        print("TEST 1: Fetch last 10 plays")
        print("=" * 80)
        recent = client.get_recently_played(limit=10)
        for i, track in enumerate(recent, 1):
            print(f"{i}. {track['track_name']} - {track['artist_name']}")
            print(f"   Played at: {track['played_at']}")
        
        print("\n" + "=" * 80)
        print("TEST 2: Fetch ALL available history")
        print("=" * 80)
        all_history = client.get_all_recent_history()
        
        print(f"\nTotal tracks fetched: {len(all_history)}")
        if all_history:
            print(f"Oldest: {all_history[0]['played_at']}")
            print(f"Newest: {all_history[-1]['played_at']}")
            
            # Show some stats
            unique_tracks = len(set(t['track_id'] for t in all_history))
            unique_artists = len(set(t['artist_id'] for t in all_history))
            print(f"\nUnique tracks: {unique_tracks}")
            print(f"Unique artists: {unique_artists}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise

