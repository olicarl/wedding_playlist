"""Spotify API client for extracting user's favorite music."""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Any
from rich.console import Console

console = Console()


class SpotifyClient:
    """Client for interacting with Spotify Web API."""
    
    def __init__(self):
        """Initialize Spotify client with OAuth."""
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")
        
        scope = "user-library-read playlist-modify-public playlist-modify-private user-top-read"
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=scope
        ))
    
    def get_user_top_tracks(self, limit: int = 50, time_range: str = 'medium_term') -> List[Dict[str, Any]]:
        """
        Get user's top tracks.
        
        Args:
            limit: Number of tracks to retrieve (max 50)
            time_range: 'short_term', 'medium_term', or 'long_term'
        """
        console.print(f"🎵 Fetching top {limit} tracks from Spotify...")
        
        results = self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
        tracks = []
        
        for item in results['items']:
            track_info = {
                'id': item['id'],
                'name': item['name'],
                'artist': ', '.join([artist['name'] for artist in item['artists']]),
                'album': item['album']['name'],
                'popularity': item['popularity'],
                'preview_url': item['preview_url'],
                'external_urls': item['external_urls'],
                'duration_ms': item['duration_ms']
            }
            tracks.append(track_info)
        
        console.print(f"✅ Successfully fetched {len(tracks)} tracks")
        return tracks
    
    def get_audio_features(self, track_ids: List[str]) -> List[Dict[str, Any]]:
        """Get audio features for a list of track IDs."""
        console.print(f"🔊 Analyzing audio features for {len(track_ids)} tracks...")
        
        # Spotify API allows max 100 tracks per request
        all_features = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            features = self.sp.audio_features(batch)
            all_features.extend([f for f in features if f is not None])
        
        console.print(f"✅ Retrieved audio features for {len(all_features)} tracks")
        return all_features
    
    def get_saved_tracks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's saved tracks (liked songs)."""
        console.print(f"💚 Fetching {limit} saved tracks...")
        
        tracks = []
        offset = 0
        
        while len(tracks) < limit:
            batch_size = min(50, limit - len(tracks))
            results = self.sp.current_user_saved_tracks(limit=batch_size, offset=offset)
            
            if not results['items']:
                break
            
            for item in results['items']:
                track = item['track']
                track_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'popularity': track['popularity'],
                    'preview_url': track['preview_url'],
                    'external_urls': track['external_urls'],
                    'duration_ms': track['duration_ms']
                }
                tracks.append(track_info)
            
            offset += batch_size
        
        console.print(f"✅ Successfully fetched {len(tracks)} saved tracks")
        return tracks
    
    def create_playlist(self, name: str, description: str, track_uris: List[str]) -> Dict[str, Any]:
        """Create a new playlist with the given tracks."""
        console.print(f"🎵 Creating playlist '{name}' with {len(track_uris)} tracks...")
        
        # Get current user
        user = self.sp.current_user()
        user_id = user['id']
        
        # Create playlist
        playlist = self.sp.user_playlist_create(
            user=user_id,
            name=name,
            public=False,
            description=description
        )
        
        # Add tracks to playlist (max 100 per request)
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            self.sp.playlist_add_items(playlist['id'], batch)
        
        console.print(f"✅ Created playlist: {playlist['external_urls']['spotify']}")
        return playlist 