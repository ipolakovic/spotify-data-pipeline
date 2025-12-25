"""
Spotify Artist API client for fetching artist details.
Extends SpotifyClient functionality for artist-specific operations.
"""
import os
import logging
from typing import Dict, List, Set
from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyOAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpotifyArtistClient:
    """Handle Spotify Artist API operations."""
    
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None
    ):
        """Initialize artist client."""
        self.client_id = client_id or os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = redirect_uri or os.getenv('SPOTIFY_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing Spotify credentials")
        
        self.sp = None
        logger.info("SpotifyArtistClient initialized")
    
    def authenticate(self) -> None:
        """Authenticate with Spotify (reuses token from ingestion Lambda)."""
        is_lambda = 'AWS_EXECUTION_ENV' in os.environ
        
        if is_lambda:
            cache_path = '/tmp/.spotify_cache'
            try:
                import boto3
                s3 = boto3.client('s3')
                bucket = os.getenv('S3_BUCKET')
                s3.download_file(bucket, 'secrets/spotify_token', cache_path)
                logger.info("Downloaded Spotify token from S3")
            except Exception as e:
                logger.error(f"Failed to download token: {str(e)}")
                raise
            open_browser = False
        else:
            cache_path = ".spotify_cache"
            open_browser = True
        
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-read-recently-played",
                cache_path=cache_path,
                open_browser=open_browser
            )
            
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            user = self.sp.current_user()
            logger.info(f"Authenticated as: {user['display_name']}")
            
            # Upload refreshed token if in Lambda
            if is_lambda:
                try:
                    s3.upload_file(cache_path, bucket, 'secrets/spotify_token')
                    logger.info("Uploaded refreshed token to S3")
                except Exception as e:
                    logger.error(f"Failed to upload token: {str(e)}")
        
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def get_artists(self, artist_ids: List[str]) -> List[Dict]:
        """
        Fetch artist details in batches.
        
        Spotify allows max 50 artists per request.
        
        Args:
            artist_ids: List of Spotify artist IDs
            
        Returns:
            List of artist detail dictionaries
        """
        if not self.sp:
            raise ValueError("Not authenticated")
        
        all_artists = []
        batch_size = 50
        
        for i in range(0, len(artist_ids), batch_size):
            batch = artist_ids[i:i + batch_size]
            logger.info(f"Fetching artists batch {i//batch_size + 1}: {len(batch)} artists")
            
            try:
                results = self.sp.artists(batch)
                
                for artist in results['artists']:
                    if artist:  # API can return None for invalid IDs
                        artist_data = {
                            'artist_id': artist['id'],
                            'artist_name': artist['name'],
                            'genres': artist.get('genres', []),
                            'followers': artist['followers']['total'],
                            'popularity': artist['popularity'],
                            'image_url': artist['images'][0]['url'] if artist['images'] else None,
                            'fetched_at': datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        }
                        all_artists.append(artist_data)
                
            except Exception as e:
                logger.error(f"Failed to fetch batch: {str(e)}")
                # Continue with other batches even if one fails
                continue
        
        logger.info(f"Fetched details for {len(all_artists)} artists")
        return all_artists
