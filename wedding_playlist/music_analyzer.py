"""Music analysis and clustering functionality."""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table
import re

console = Console()


class MusicAnalyzer:
    """Analyzes and clusters music based on track metadata (audio features deprecated by Spotify)."""
    
    def __init__(self):
        """Initialize the music analyzer."""
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=3)
        self.kmeans = None
        # Use available metadata features instead of audio features
        self.feature_columns = [
            'popularity', 'duration_ms', 'release_year', 'artist_popularity'
        ]
    
    def prepare_data(self, tracks: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Prepare track data using available metadata (no audio features needed).
        
        Args:
            tracks: List of track dictionaries with metadata
        
        Returns:
            DataFrame with track metadata
        """
        console.print("📊 Preparing music data for analysis (using metadata only)...")
        
        # Extract useful features from track metadata
        enhanced_tracks = []
        for track in tracks:
            enhanced_track = track.copy()
            
            # Extract release year from album release date if available
            try:
                if 'album' in track and 'release_date' in track['album']:
                    release_date = track['album']['release_date']
                    enhanced_track['release_year'] = int(release_date[:4])
                else:
                    enhanced_track['release_year'] = 2020  # Default
            except:
                enhanced_track['release_year'] = 2020
            
            # Add artist popularity (use track popularity as proxy)
            enhanced_track['artist_popularity'] = track.get('popularity', 50)
            
            # Estimate genre diversity based on artist name patterns
            enhanced_track['name_energy'] = self._estimate_energy_from_name(track.get('name', ''))
            
            enhanced_tracks.append(enhanced_track)
        
        df = pd.DataFrame(enhanced_tracks)
        console.print(f"✅ Prepared metadata for {len(df)} tracks")
        return df
    
    def _estimate_energy_from_name(self, track_name: str) -> float:
        """Estimate energy level from track name patterns."""
        track_name = track_name.lower()
        
        high_energy_keywords = ['dance', 'party', 'electric', 'beat', 'club', 'remix', 'uptempo', 'energy', 'pump', 'groove']
        low_energy_keywords = ['ballad', 'acoustic', 'slow', 'quiet', 'piano', 'soft', 'gentle', 'lullaby', 'ambient']
        
        energy_score = 0.5  # baseline
        
        for keyword in high_energy_keywords:
            if keyword in track_name:
                energy_score += 0.1
        
        for keyword in low_energy_keywords:
            if keyword in track_name:
                energy_score -= 0.1
        
        return max(0.0, min(1.0, energy_score))
    
    def cluster_tracks(self, df: pd.DataFrame, n_clusters: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cluster tracks based on available metadata.
        
        Args:
            df: DataFrame with track metadata
            n_clusters: Number of clusters to create
        
        Returns:
            Tuple of (DataFrame with cluster labels, cluster analysis)
        """
        console.print(f"🎯 Clustering tracks into {n_clusters} music styles (using metadata)...")
        
        # Add estimated features
        df['name_energy'] = df['name'].apply(self._estimate_energy_from_name)
        
        # Select and clean feature columns
        available_features = [col for col in self.feature_columns if col in df.columns]
        available_features.append('name_energy')
        
        feature_data = df[available_features].copy()
        feature_data = feature_data.dropna()
        
        if len(feature_data) == 0:
            raise ValueError("No valid metadata found for clustering")
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(feature_data)
        
        # Apply PCA for dimensionality reduction (adjust components based on data size)
        n_components = min(3, len(feature_data), len(available_features))
        if n_components < 1:
            n_components = 1
        
        self.pca = PCA(n_components=n_components)
        features_pca = self.pca.fit_transform(features_scaled)
        
        # Perform K-means clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(features_pca)
        
        # Add cluster labels to dataframe
        df_clustered = df.loc[feature_data.index].copy()
        df_clustered['cluster'] = cluster_labels
        
        # Analyze clusters
        cluster_analysis = self._analyze_clusters(df_clustered, available_features)
        
        console.print(f"✅ Successfully clustered {len(df_clustered)} tracks into {n_clusters} styles")
        return df_clustered, cluster_analysis
    
    def _analyze_clusters(self, df: pd.DataFrame, feature_columns: List[str]) -> Dict[str, Any]:
        """Analyze the characteristics of each cluster using available metadata."""
        console.print("📈 Analyzing cluster characteristics...")
        
        analysis = {}
        
        for cluster_id in sorted(df['cluster'].unique()):
            cluster_data = df[df['cluster'] == cluster_id]
            
            # Calculate mean features for this cluster
            numeric_features = [col for col in feature_columns if col in cluster_data.columns and cluster_data[col].dtype in ['int64', 'float64']]
            if numeric_features:
                feature_means = cluster_data[numeric_features].mean()
            else:
                feature_means = pd.Series()
            
            # Get style description based on available features
            style_desc = self._describe_music_style_from_metadata(cluster_data)
            
            analysis[cluster_id] = {
                'size': len(cluster_data),
                'style_description': style_desc,
                'avg_features': feature_means.to_dict() if not feature_means.empty else {},
                'sample_tracks': cluster_data[['name', 'artist']].head(3).to_dict('records'),
                'avg_popularity': cluster_data['popularity'].mean() if 'popularity' in cluster_data.columns else 0,
                'total_duration_min': cluster_data['duration_ms'].sum() / (1000 * 60) if 'duration_ms' in cluster_data.columns else 0,
                'release_year_range': f"{cluster_data['release_year'].min()}-{cluster_data['release_year'].max()}" if 'release_year' in cluster_data.columns else "Unknown"
            }
        
        return analysis
    
    def _describe_music_style_from_metadata(self, cluster_data: pd.DataFrame) -> str:
        """Generate a description of music style based on available metadata."""
        style_elements = []
        
        # Popularity-based classification
        avg_popularity = cluster_data['popularity'].mean() if 'popularity' in cluster_data.columns else 50
        if avg_popularity > 70:
            style_elements.append("Popular hits")
        elif avg_popularity < 30:
            style_elements.append("Deep cuts")
        
        # Era-based classification
        if 'release_year' in cluster_data.columns:
            avg_year = cluster_data['release_year'].mean()
            if avg_year < 1980:
                style_elements.append("Classic oldies")
            elif avg_year < 1990:
                style_elements.append("80s")
            elif avg_year < 2000:
                style_elements.append("90s")
            elif avg_year < 2010:
                style_elements.append("2000s")
            elif avg_year < 2020:
                style_elements.append("2010s")
            else:
                style_elements.append("Recent releases")
        
        # Energy estimation from track names
        if 'name_energy' in cluster_data.columns:
            avg_energy = cluster_data['name_energy'].mean()
            if avg_energy > 0.6:
                style_elements.append("High-energy")
            elif avg_energy < 0.4:
                style_elements.append("Mellow")
        
        # Duration-based classification
        if 'duration_ms' in cluster_data.columns:
            avg_duration = cluster_data['duration_ms'].mean() / 1000  # Convert to seconds
            if avg_duration > 300:  # 5 minutes
                style_elements.append("Extended tracks")
            elif avg_duration < 180:  # 3 minutes
                style_elements.append("Radio-friendly")
        
        return " ".join(style_elements) if style_elements else "Mixed style"
    
    def display_cluster_overview(self, cluster_analysis: Dict[str, Any]) -> None:
        """Display a rich table overview of clusters."""
        table = Table(title="🎵 Music Style Clusters Analysis (Metadata-Based)")
        table.add_column("Cluster", style="cyan", no_wrap=True)
        table.add_column("Style", style="magenta")
        table.add_column("Tracks", style="green")
        table.add_column("Avg Popularity", style="yellow")
        table.add_column("Duration (min)", style="blue")
        table.add_column("Era", style="purple")
        table.add_column("Sample Tracks", style="white")
        
        for cluster_id, data in cluster_analysis.items():
            sample_tracks = ", ".join([f"{t['name']} - {t['artist']}" for t in data['sample_tracks']])
            
            table.add_row(
                f"Cluster {cluster_id}",
                data['style_description'],
                str(data['size']),
                f"{data['avg_popularity']:.1f}",
                f"{data['total_duration_min']:.1f}",
                data.get('release_year_range', 'Unknown'),
                sample_tracks[:50] + "..." if len(sample_tracks) > 50 else sample_tracks
            )
        
        console.print(table)
    
    def get_party_suitable_features(self) -> Dict[str, Tuple[float, float]]:
        """Get metadata ranges that suggest party-suitable music."""
        return {
            'popularity': (40, 100),      # Prefer well-known tracks
            'name_energy': (0.5, 1.0),   # Prefer tracks with energetic names
            'release_year': (1980, 2024), # Modern enough for parties
            'duration_ms': (120000, 360000)  # 2-6 minutes (good for dancing)
        } 