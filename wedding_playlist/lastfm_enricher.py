"""Last.fm metadata enricher for enhanced track analysis."""

import os
import time
from typing import List, Dict, Any, Optional
import pylast
from rich.console import Console
from rich.progress import Progress

# Ensure environment variables are loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, assume env vars are set manually

console = Console()


class LastFMEnricher:
    """Enriches track metadata using Last.fm API."""
    
    def __init__(self):
        """Initialize the Last.fm enricher."""
        # Get Last.fm API credentials
        api_key = os.getenv('LASTFM_API_KEY')
        if not api_key:
            console.print("⚠️ LASTFM_API_KEY not found - Last.fm enrichment will be skipped")
            self.network = None
            return
        
        try:
            # Initialize Last.fm network (read-only, no authentication needed)
            self.network = pylast.LastFMNetwork(api_key=api_key)
            console.print("✅ Last.fm API initialized successfully")
        except Exception as e:
            console.print(f"❌ Failed to initialize Last.fm API: {e}")
            self.network = None
    
    def enrich_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich tracks with Last.fm metadata.
        
        Args:
            tracks: List of track dictionaries from Spotify
            
        Returns:
            List of tracks enriched with Last.fm metadata
        """
        if not self.network:
            console.print("⚠️ Last.fm API not available - skipping enrichment")
            return tracks
        
        console.print(f"🎵 Enriching {len(tracks)} tracks with Last.fm metadata...")
        
        enriched_tracks = []
        
        with Progress() as progress:
            task = progress.add_task("Enriching with Last.fm...", total=len(tracks))
            
            for track in tracks:
                enriched_track = track.copy()
                lastfm_data = self._get_lastfm_metadata(track['name'], track['artist'])
                
                if lastfm_data:
                    enriched_track['lastfm'] = lastfm_data
                else:
                    enriched_track['lastfm'] = {}
                
                enriched_tracks.append(enriched_track)
                progress.update(task, advance=1)
                
                # Rate limiting - Last.fm allows 5 requests per second
                time.sleep(0.2)
        
        console.print(f"✅ Enriched {len(enriched_tracks)} tracks with Last.fm data")
        return enriched_tracks
    
    def _get_lastfm_metadata(self, track_name: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a single track from Last.fm.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            Dictionary with Last.fm metadata or None if not found
        """
        try:
            # Get track object from Last.fm
            track = self.network.get_track(artist_name, track_name)
            
            # Collect metadata
            metadata = {}
            
            # Get basic track info
            try:
                track_info = track.get_info()
                if track_info:
                    metadata['playcount'] = getattr(track_info, 'playcount', 0)
                    metadata['listeners'] = getattr(track_info, 'listeners', 0)
                    
                    # Get track duration if available
                    duration = getattr(track_info, 'duration', None)
                    if duration:
                        metadata['duration_seconds'] = int(duration) / 1000
            except Exception:
                pass
            
            # Get top tags (genres)
            try:
                tags = track.get_top_tags(limit=10)
                if tags:
                    metadata['tags'] = [
                        {
                            'name': tag.item.name,
                            'weight': tag.weight
                        }
                        for tag in tags
                    ]
                    # Extract main genres
                    metadata['genres'] = [tag.item.name for tag in tags[:5]]
            except Exception:
                metadata['tags'] = []
                metadata['genres'] = []
            
            # Get similar tracks
            try:
                similar = track.get_similar(limit=5)
                if similar:
                    metadata['similar_tracks'] = [
                        {
                            'artist': sim.item.artist.name,
                            'track': sim.item.title,
                            'match': sim.match
                        }
                        for sim in similar
                    ]
            except Exception:
                metadata['similar_tracks'] = []
            
            # Get artist info
            try:
                artist = track.artist
                artist_info = artist.get_info()
                if artist_info:
                    metadata['artist_info'] = {
                        'playcount': getattr(artist_info, 'playcount', 0),
                        'listeners': getattr(artist_info, 'listeners', 0)
                    }
                
                # Get artist tags
                artist_tags = artist.get_top_tags(limit=5)
                if artist_tags:
                    metadata['artist_tags'] = [tag.item.name for tag in artist_tags]
                
                # Get similar artists
                similar_artists = artist.get_similar(limit=3)
                if similar_artists:
                    metadata['similar_artists'] = [
                        {
                            'name': sim.item.name,
                            'match': sim.match
                        }
                        for sim in similar_artists
                    ]
            except Exception:
                metadata['artist_info'] = {}
                metadata['artist_tags'] = []
                metadata['similar_artists'] = []
            
            return metadata if metadata else None
            
        except pylast.WSError as e:
            # Track not found or API error
            console.print(f"⚠️ Last.fm error for '{track_name}' by '{artist_name}': {e}", style="dim")
            return None
        except Exception as e:
            console.print(f"⚠️ Unexpected error for '{track_name}' by '{artist_name}': {e}", style="dim")
            return None
    
    def format_lastfm_data_for_ai(self, track: Dict[str, Any]) -> str:
        """
        Format Last.fm metadata for AI consumption.
        
        Args:
            track: Track dictionary with Last.fm metadata
            
        Returns:
            Formatted string with Last.fm data for AI analysis
        """
        lastfm = track.get('lastfm', {})
        if not lastfm:
            return ""
        
        parts = []
        
        # Add popularity metrics
        if 'playcount' in lastfm and lastfm['playcount'] > 0:
            parts.append(f"Last.fm plays: {lastfm['playcount']:,}")
        
        if 'listeners' in lastfm and lastfm['listeners'] > 0:
            parts.append(f"Listeners: {lastfm['listeners']:,}")
        
        # Add genres/tags
        if 'genres' in lastfm and lastfm['genres']:
            genres_str = ', '.join(lastfm['genres'][:3])  # Top 3 genres
            parts.append(f"Genres: {genres_str}")
        
        # Add artist popularity
        artist_info = lastfm.get('artist_info', {})
        if 'listeners' in artist_info and artist_info['listeners'] > 0:
            parts.append(f"Artist listeners: {artist_info['listeners']:,}")
        
        # Add artist tags for style context
        if 'artist_tags' in lastfm and lastfm['artist_tags']:
            artist_tags_str = ', '.join(lastfm['artist_tags'][:2])  # Top 2 artist tags
            parts.append(f"Artist style: {artist_tags_str}")
        
        return " | ".join(parts) if parts else ""
    
    def get_genre_summary(self, tracks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get a summary of genres from enriched tracks.
        
        Args:
            tracks: List of tracks with Last.fm metadata
            
        Returns:
            Dictionary with genre counts
        """
        genre_counts = {}
        
        for track in tracks:
            lastfm = track.get('lastfm', {})
            genres = lastfm.get('genres', [])
            
            for genre in genres[:3]:  # Count top 3 genres per track
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort by frequency
        return dict(sorted(genre_counts.items(), key=lambda x: x[1], reverse=True))
    
    def analyze_danceability_from_tags(self, track: Dict[str, Any]) -> float:
        """
        Estimate danceability from Last.fm tags.
        
        Args:
            track: Track dictionary with Last.fm metadata
            
        Returns:
            Estimated danceability score (0.0 - 1.0)
        """
        lastfm = track.get('lastfm', {})
        tags = lastfm.get('tags', [])
        
        # Define tag weights for danceability
        dance_tags = {
            'dance': 0.9, 'electronic': 0.8, 'house': 0.9, 'techno': 0.8,
            'disco': 0.9, 'funk': 0.8, 'pop': 0.7, 'club': 0.9,
            'edm': 0.9, 'trance': 0.8, 'dubstep': 0.7, 'hip hop': 0.7,
            'hip-hop': 0.7, 'rap': 0.6, 'r&b': 0.7, 'rnb': 0.7,
            'latin': 0.8, 'reggaeton': 0.9, 'afrobeat': 0.8,
            'upbeat': 0.8, 'energetic': 0.7, 'party': 0.8
        }
        
        chill_tags = {
            'ambient': 0.1, 'chill': 0.2, 'relaxing': 0.1, 'mellow': 0.2,
            'folk': 0.3, 'acoustic': 0.3, 'jazz': 0.4, 'classical': 0.1,
            'instrumental': 0.2, 'ballad': 0.2, 'sad': 0.1, 'melancholy': 0.1
        }
        
        score = 0.5  # Default neutral score
        weight_sum = 0
        
        for tag_info in tags:
            tag_name = tag_info['name'].lower()
            tag_weight = tag_info.get('weight', 1)
            
            if tag_name in dance_tags:
                score += dance_tags[tag_name] * tag_weight
                weight_sum += tag_weight
            elif tag_name in chill_tags:
                score += chill_tags[tag_name] * tag_weight
                weight_sum += tag_weight
        
        # Normalize if we found relevant tags
        if weight_sum > 0:
            score = score / (weight_sum + 1)  # +1 to account for default score
        
        return max(0.0, min(1.0, score))  # Clamp to 0-1 range 