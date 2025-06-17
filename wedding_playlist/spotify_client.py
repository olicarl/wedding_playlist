"""Spotify API client for extracting user's favorite music."""

import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Any
from rich.console import Console

# Ensure environment variables are loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, assume env vars are set manually

console = Console()


class SpotifyClient:
    """Client for interacting with Spotify Web API."""
    
    def __init__(self):
        """Initialize Spotify client with OAuth."""
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'https://127.0.0.1:8888/callback')
        
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Spotify credentials not found. Please ensure your .env file contains:\n"
                "SPOTIFY_CLIENT_ID=your_client_id\n"
                "SPOTIFY_CLIENT_SECRET=your_client_secret\n"
                "Or run: uv run python main.py setup"
            )
        
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
                'album': {
                    'name': item['album']['name'],
                    'release_date': item['album'].get('release_date', ''),
                    'total_tracks': item['album'].get('total_tracks', 0)
                },
                'popularity': item['popularity'],
                'preview_url': item['preview_url'],
                'external_urls': item['external_urls'],
                'duration_ms': item['duration_ms'],
                'explicit': item.get('explicit', False),
                'track_number': item.get('track_number', 0)
            }
            tracks.append(track_info)
        
        console.print(f"✅ Successfully fetched {len(tracks)} tracks")
        return tracks
    
    def get_audio_features(self, track_ids: List[str]) -> List[Dict[str, Any]]:
        """Get audio features for a list of track IDs."""
        console.print(f"🔊 Analyzing audio features for {len(track_ids)} tracks...")
        
        # Remove duplicates and filter out None/empty IDs
        unique_track_ids = list(dict.fromkeys([tid for tid in track_ids if tid and isinstance(tid, str) and len(tid) == 22]))
        console.print(f"📊 Processing {len(unique_track_ids)} unique valid track IDs...")
        
        if not unique_track_ids:
            console.print("⚠️ No valid track IDs to process")
            return []
        
        # Debug: show first few track IDs
        console.print(f"🔍 Sample track IDs: {unique_track_ids[:3]}")
        
        # Use smaller batch size to avoid URL length issues and rate limiting
        batch_size = 50
        all_features = []
        
        for i in range(0, len(unique_track_ids), batch_size):
            batch = unique_track_ids[i:i+batch_size]
            console.print(f"🔄 Processing batch {i//batch_size + 1}/{(len(unique_track_ids) + batch_size - 1)//batch_size} ({len(batch)} tracks)")
            
            try:
                features = self.sp.audio_features(batch)
                valid_features = [f for f in features if f is not None]
                all_features.extend(valid_features)
                console.print(f"✅ Retrieved {len(valid_features)} audio features from batch")
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                console.print(f"⚠️ Error processing batch: {e}")
                console.print(f"📝 Batch track IDs: {batch[:5]}{'...' if len(batch) > 5 else ''}")
                
                # Try processing tracks one by one to identify problematic ones
                console.print("🔧 Trying individual track processing...")
                for track_id in batch:
                    try:
                        feature = self.sp.audio_features([track_id])
                        if feature and feature[0]:
                            all_features.append(feature[0])
                            console.print(f"✅ Processed track: {track_id}")
                        else:
                            console.print(f"⚠️ No features for track: {track_id}")
                    except Exception as track_error:
                        console.print(f"❌ Failed track {track_id}: {track_error}")
                    
                    # Small delay between individual requests
                    time.sleep(0.05)
        
        console.print(f"✅ Retrieved audio features for {len(all_features)} tracks total")
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
                    'album': {
                        'name': track['album']['name'],
                        'release_date': track['album'].get('release_date', ''),
                        'total_tracks': track['album'].get('total_tracks', 0)
                    },
                    'popularity': track['popularity'],
                    'preview_url': track['preview_url'],
                    'external_urls': track['external_urls'],
                    'duration_ms': track['duration_ms'],
                    'explicit': track.get('explicit', False),
                    'track_number': track.get('track_number', 0)
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