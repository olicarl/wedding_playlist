"""Music analysis and clustering functionality."""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table

console = Console()


class MusicAnalyzer:
    """Analyzes and clusters music based on audio features."""
    
    def __init__(self):
        """Initialize the music analyzer."""
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=5)
        self.kmeans = None
        self.feature_columns = [
            'danceability', 'energy', 'loudness', 'speechiness',
            'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo'
        ]
    
    def prepare_data(self, tracks: List[Dict[str, Any]], audio_features: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Combine track info with audio features into a pandas DataFrame.
        
        Args:
            tracks: List of track dictionaries
            audio_features: List of audio feature dictionaries
        
        Returns:
            DataFrame with combined track and audio feature data
        """
        console.print("📊 Preparing music data for analysis...")
        
        # Create track lookup by ID
        track_lookup = {track['id']: track for track in tracks}
        
        # Combine data
        combined_data = []
        for features in audio_features:
            if features and features['id'] in track_lookup:
                track = track_lookup[features['id']]
                combined_row = {
                    **track,
                    **features
                }
                combined_data.append(combined_row)
        
        df = pd.DataFrame(combined_data)
        console.print(f"✅ Prepared data for {len(df)} tracks")
        return df
    
    def cluster_tracks(self, df: pd.DataFrame, n_clusters: int = 5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Cluster tracks based on audio features.
        
        Args:
            df: DataFrame with track and audio feature data
            n_clusters: Number of clusters to create
        
        Returns:
            Tuple of (DataFrame with cluster labels, cluster analysis)
        """
        console.print(f"🎯 Clustering tracks into {n_clusters} music styles...")
        
        # Select and clean feature columns
        feature_data = df[self.feature_columns].copy()
        feature_data = feature_data.dropna()
        
        if len(feature_data) == 0:
            raise ValueError("No valid audio features found for clustering")
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(feature_data)
        
        # Apply PCA for dimensionality reduction
        features_pca = self.pca.fit_transform(features_scaled)
        
        # Perform K-means clustering
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(features_pca)
        
        # Add cluster labels to dataframe
        df_clustered = df.loc[feature_data.index].copy()
        df_clustered['cluster'] = cluster_labels
        
        # Analyze clusters
        cluster_analysis = self._analyze_clusters(df_clustered)
        
        console.print(f"✅ Successfully clustered {len(df_clustered)} tracks into {n_clusters} styles")
        return df_clustered, cluster_analysis
    
    def _analyze_clusters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the characteristics of each cluster."""
        console.print("📈 Analyzing cluster characteristics...")
        
        analysis = {}
        
        for cluster_id in sorted(df['cluster'].unique()):
            cluster_data = df[df['cluster'] == cluster_id]
            
            # Calculate mean audio features for this cluster
            feature_means = cluster_data[self.feature_columns].mean()
            
            # Get style description based on audio features
            style_desc = self._describe_music_style(feature_means)
            
            analysis[cluster_id] = {
                'size': len(cluster_data),
                'style_description': style_desc,
                'avg_features': feature_means.to_dict(),
                'sample_tracks': cluster_data[['name', 'artist']].head(3).to_dict('records'),
                'avg_popularity': cluster_data['popularity'].mean(),
                'total_duration_min': cluster_data['duration_ms'].sum() / (1000 * 60)
            }
        
        return analysis
    
    def _describe_music_style(self, features: pd.Series) -> str:
        """Generate a description of music style based on audio features."""
        style_elements = []
        
        # Energy and danceability
        if features['energy'] > 0.7 and features['danceability'] > 0.7:
            style_elements.append("High-energy dance")
        elif features['energy'] > 0.6:
            style_elements.append("Energetic")
        elif features['energy'] < 0.4:
            style_elements.append("Mellow")
        
        # Valence (mood)
        if features['valence'] > 0.7:
            style_elements.append("upbeat")
        elif features['valence'] < 0.4:
            style_elements.append("melancholic")
        
        # Acousticness
        if features['acousticness'] > 0.6:
            style_elements.append("acoustic")
        
        # Instrumentalness
        if features['instrumentalness'] > 0.5:
            style_elements.append("instrumental")
        
        # Tempo
        if features['tempo'] > 140:
            style_elements.append("fast-paced")
        elif features['tempo'] < 90:
            style_elements.append("slow-tempo")
        
        return " ".join(style_elements) if style_elements else "Mixed style"
    
    def display_cluster_overview(self, cluster_analysis: Dict[str, Any]) -> None:
        """Display a rich table overview of clusters."""
        table = Table(title="🎵 Music Style Clusters Analysis")
        table.add_column("Cluster", style="cyan", no_wrap=True)
        table.add_column("Style", style="magenta")
        table.add_column("Tracks", style="green")
        table.add_column("Avg Popularity", style="yellow")
        table.add_column("Duration (min)", style="blue")
        table.add_column("Sample Tracks", style="white")
        
        for cluster_id, data in cluster_analysis.items():
            sample_tracks = ", ".join([f"{t['name']} - {t['artist']}" for t in data['sample_tracks']])
            
            table.add_row(
                f"Cluster {cluster_id}",
                data['style_description'],
                str(data['size']),
                f"{data['avg_popularity']:.1f}",
                f"{data['total_duration_min']:.1f}",
                sample_tracks[:60] + "..." if len(sample_tracks) > 60 else sample_tracks
            )
        
        console.print(table)
    
    def get_party_suitable_features(self) -> Dict[str, Tuple[float, float]]:
        """Get audio feature ranges that are suitable for party music."""
        return {
            'danceability': (0.6, 1.0),  # High danceability
            'energy': (0.5, 1.0),        # Medium to high energy
            'valence': (0.4, 1.0),       # Positive to very positive mood
            'tempo': (100, 180),         # Moderate to fast tempo
            'loudness': (-10, 0),        # Not too quiet
            'acousticness': (0.0, 0.4)   # Prefer less acoustic songs
        } 