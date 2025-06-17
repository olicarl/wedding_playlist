"""Playlist generation and export functionality."""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from rich.console import Console

console = Console()


class PlaylistGenerator:
    """Generates and exports party playlists."""
    
    def __init__(self):
        """Initialize the playlist generator."""
        self.output_dir = "output"
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Ensure the output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            console.print(f"📁 Created output directory: {self.output_dir}")
    
    def generate_txt_playlist(self, tracks: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Generate a text file playlist.
        
        Args:
            tracks: List of track dictionaries
            filename: Optional filename, auto-generated if not provided
        
        Returns:
            Path to the generated file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wedding_party_playlist_{timestamp}.txt"
        
        filepath = os.path.join(self.output_dir, filename)
        
        console.print(f"📝 Creating text playlist: {filename}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("🎵 AI-Generated Wedding Party Playlist 🎵\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total tracks: {len(tracks)}\n")
            f.write(f"Total duration: {self._calculate_total_duration(tracks):.1f} minutes\n")
            f.write("=" * 50 + "\n\n")
            
            for i, track in enumerate(tracks, 1):
                f.write(f"{i:2d}. {track['name']}\n")
                f.write(f"    Artist: {track['artist']}\n")
                f.write(f"    Album: {track.get('album', 'Unknown')}\n")
                
                if 'ai_party_score' in track:
                    f.write(f"    AI Party Score: {track['ai_party_score']}/10\n")
                    f.write(f"    AI Reasoning: {track['ai_reasoning']}\n")
                
                if 'cluster' in track:
                    f.write(f"    Music Style: Cluster {track['cluster']}\n")
                
                # Audio features
                features = []
                if 'danceability' in track:
                    features.append(f"Danceability: {track['danceability']:.2f}")
                if 'energy' in track:
                    features.append(f"Energy: {track['energy']:.2f}")
                if 'valence' in track:
                    features.append(f"Mood: {track['valence']:.2f}")
                
                if features:
                    f.write(f"    Features: {', '.join(features)}\n")
                
                if 'external_urls' in track and 'spotify' in track['external_urls']:
                    f.write(f"    Spotify: {track['external_urls']['spotify']}\n")
                
                f.write("\n")
        
        console.print(f"✅ Text playlist saved to: {filepath}")
        return filepath
    
    def generate_json_playlist(self, tracks: List[Dict[str, Any]], filename: str = None) -> str:
        """
        Generate a JSON file with detailed track information.
        
        Args:
            tracks: List of track dictionaries
            filename: Optional filename, auto-generated if not provided
        
        Returns:
            Path to the generated file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wedding_party_playlist_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        console.print(f"💾 Creating JSON playlist: {filename}")
        
        playlist_data = {
            "metadata": {
                "name": "AI-Generated Wedding Party Playlist",
                "generated_on": datetime.now().isoformat(),
                "total_tracks": len(tracks),
                "total_duration_minutes": self._calculate_total_duration(tracks)
            },
            "tracks": tracks
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(playlist_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"✅ JSON playlist saved to: {filepath}")
        return filepath
    
    def create_spotify_playlist(self, spotify_client, tracks: List[Dict[str, Any]], 
                              name: str = None, description: str = None) -> Dict[str, Any]:
        """
        Create a Spotify playlist with the given tracks.
        
        Args:
            spotify_client: SpotifyClient instance
            tracks: List of track dictionaries
            name: Playlist name
            description: Playlist description
        
        Returns:
            Playlist information
        """
        if not name:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            name = f"🎉 Wedding Party Playlist ({timestamp})"
        
        if not description:
            ai_count = sum(1 for t in tracks if t.get('ai_party_score', 0) >= 6)
            description = (f"AI-curated wedding party playlist with {len(tracks)} tracks. "
                         f"{ai_count} tracks validated by AI for optimal party atmosphere. "
                         f"Generated on {datetime.now().strftime('%Y-%m-%d')}")
        
        # Extract track URIs
        track_uris = []
        for track in tracks:
            if 'id' in track:
                track_uris.append(f"spotify:track:{track['id']}")
        
        if not track_uris:
            raise ValueError("No valid Spotify track IDs found")
        
        # Create the playlist
        playlist = spotify_client.create_playlist(name, description, track_uris)
        return playlist
    
    def _calculate_total_duration(self, tracks: List[Dict[str, Any]]) -> float:
        """Calculate total duration of tracks in minutes."""
        total_ms = sum(track.get('duration_ms', 0) for track in tracks)
        return total_ms / (1000 * 60)  # Convert to minutes
    
    def generate_analysis_report(self, tracks: List[Dict[str, Any]], 
                               cluster_analysis: Dict[str, Any] = None) -> str:
        """
        Generate a detailed analysis report.
        
        Args:
            tracks: List of track dictionaries
            cluster_analysis: Optional cluster analysis data
        
        Returns:
            Path to the generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"playlist_analysis_report_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        console.print(f"📊 Creating analysis report: {filename}")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("🎵 Wedding Playlist Analysis Report 🎵\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall statistics
            f.write("📈 OVERALL STATISTICS\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total tracks analyzed: {len(tracks)}\n")
            f.write(f"Total duration: {self._calculate_total_duration(tracks):.1f} minutes\n")
            
            if any('ai_party_score' in track for track in tracks):
                ai_scores = [track.get('ai_party_score', 0) for track in tracks if 'ai_party_score' in track]
                avg_ai_score = sum(ai_scores) / len(ai_scores) if ai_scores else 0
                high_score_count = sum(1 for score in ai_scores if score >= 7)
                
                f.write(f"Average AI party score: {avg_ai_score:.1f}/10\n")
                f.write(f"High-scoring tracks (7+): {high_score_count}\n")
                
                # AI recommendations breakdown
                recommendations = {}
                for track in tracks:
                    rec = track.get('ai_recommendation', 'unknown')
                    recommendations[rec] = recommendations.get(rec, 0) + 1
                
                f.write("\nAI Recommendations breakdown:\n")
                for rec, count in recommendations.items():
                    f.write(f"  {rec.upper()}: {count} tracks\n")
            
            # Audio features analysis
            if any('danceability' in track for track in tracks):
                f.write("\n🎶 AUDIO FEATURES ANALYSIS\n")
                f.write("-" * 30 + "\n")
                
                features = ['danceability', 'energy', 'valence', 'tempo', 'acousticness']
                for feature in features:
                    values = [track.get(feature, 0) for track in tracks if feature in track]
                    if values:
                        avg_value = sum(values) / len(values)
                        if feature == 'tempo':
                            f.write(f"Average {feature}: {avg_value:.0f} BPM\n")
                        else:
                            f.write(f"Average {feature}: {avg_value:.2f}\n")
            
            # Cluster analysis
            if cluster_analysis:
                f.write("\n🎯 MUSIC STYLE CLUSTERS\n")
                f.write("-" * 30 + "\n")
                
                for cluster_id, data in cluster_analysis.items():
                    f.write(f"\nCluster {cluster_id}: {data['style_description']}\n")
                    f.write(f"  Tracks: {data['size']}\n")
                    f.write(f"  Duration: {data['total_duration_min']:.1f} minutes\n")
                    f.write(f"  Avg Popularity: {data['avg_popularity']:.1f}/100\n")
                    f.write("  Sample tracks:\n")
                    for track in data['sample_tracks']:
                        f.write(f"    - {track['name']} by {track['artist']}\n")
            
            # Top recommended tracks
            if any('ai_party_score' in track for track in tracks):
                f.write("\n🏆 TOP AI-RECOMMENDED TRACKS\n")
                f.write("-" * 30 + "\n")
                
                top_tracks = sorted(tracks, key=lambda x: x.get('ai_party_score', 0), reverse=True)[:10]
                for i, track in enumerate(top_tracks, 1):
                    score = track.get('ai_party_score', 0)
                    f.write(f"{i:2d}. {track['name']} - {track['artist']} (Score: {score}/10)\n")
        
        console.print(f"✅ Analysis report saved to: {filepath}")
        return filepath 