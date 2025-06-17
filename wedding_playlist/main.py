#!/usr/bin/env python3
"""Main entry point for the AI-powered wedding playlist generator."""

import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt

from .spotify_client import SpotifyClient
from .music_analyzer import MusicAnalyzer
from .ai_validator import AIValidator
from .playlist_generator import PlaylistGenerator

console = Console()


@click.group()
@click.version_option()
def main():
    """🎵 AI-Powered Wedding Playlist Generator
    
    Extract your favorite music from Spotify, analyze and cluster it by style,
    validate tracks with DeepSeek AI, and generate the perfect party playlist!
    """
    pass


@main.command()
@click.option('--tracks', '-t', default=100, help='Number of tracks to analyze (default: 100)')
@click.option('--clusters', '-c', default=5, help='Number of music style clusters (default: 5)')
@click.option('--ai-score', '-s', default=6.0, help='Minimum AI party score (default: 6.0)')
@click.option('--create-spotify', '-sp', is_flag=True, help='Create Spotify playlist')
@click.option('--output-dir', '-o', default='output', help='Output directory for files')
def generate(tracks, clusters, ai_score, create_spotify, output_dir):
    """🎉 Generate AI-curated wedding party playlist from your Spotify favorites."""
    
    console.print(Panel.fit(
        "🎵 AI-Powered Wedding Playlist Generator 🎵\n\n"
        "This will:\n"
        "• Extract your favorite music from Spotify\n"
        "• Cluster tracks by music style\n"
        "• Validate with DeepSeek AI for party suitability\n"
        "• Generate playlists and analysis reports",
        title="Welcome",
        style="bold cyan"
    ))
    
    try:
        # Step 1: Initialize clients
        console.print("\n🔧 Initializing clients...")
        spotify_client = SpotifyClient()
        analyzer = MusicAnalyzer()
        ai_validator = AIValidator()
        generator = PlaylistGenerator()
        
        # Step 2: Extract music from Spotify
        console.print(f"\n📥 Extracting {tracks} favorite tracks from Spotify...")
        
        # Get both top tracks and saved tracks
        top_tracks = spotify_client.get_user_top_tracks(limit=min(50, tracks//2))
        saved_tracks = spotify_client.get_saved_tracks(limit=min(50, tracks//2))
        
        # Combine and deduplicate
        all_tracks = top_tracks + saved_tracks
        seen_ids = set()
        unique_tracks = []
        for track in all_tracks:
            if track['id'] not in seen_ids:
                unique_tracks.append(track)
                seen_ids.add(track['id'])
        
        # Limit to requested number
        final_tracks = unique_tracks[:tracks]
        console.print(f"✅ Found {len(final_tracks)} unique tracks")
        
        # Step 3: Get audio features
        track_ids = [track['id'] for track in final_tracks]
        audio_features = spotify_client.get_audio_features(track_ids)
        
        # Step 4: Prepare data and cluster
        df = analyzer.prepare_data(final_tracks, audio_features)
        df_clustered, cluster_analysis = analyzer.cluster_tracks(df, n_clusters=clusters)
        
        # Display cluster overview
        analyzer.display_cluster_overview(cluster_analysis)
        
        # Step 5: AI validation
        console.print(f"\n🤖 Starting AI validation with DeepSeek...")
        tracks_list = df_clustered.to_dict('records')
        validated_tracks = ai_validator.validate_tracks_for_party(tracks_list)
        
        # Display AI validation summary
        ai_validator.display_validation_summary(validated_tracks)
        
        # Step 6: Filter party-suitable tracks
        party_tracks = ai_validator.filter_party_tracks(validated_tracks, min_score=ai_score)
        
        console.print(f"\n🎉 Selected {len(party_tracks)} tracks for the party playlist!")
        
        # Step 7: Generate outputs
        console.print("\n📄 Generating outputs...")
        
        # Text playlist
        txt_file = generator.generate_txt_playlist(party_tracks)
        
        # JSON playlist
        json_file = generator.generate_json_playlist(party_tracks)
        
        # Analysis report
        report_file = generator.generate_analysis_report(validated_tracks, cluster_analysis)
        
        # Spotify playlist (optional)
        if create_spotify:
            if Confirm.ask("\n🎵 Create Spotify playlist?"):
                try:
                    playlist = generator.create_spotify_playlist(spotify_client, party_tracks)
                    console.print(f"✅ Spotify playlist created: {playlist['external_urls']['spotify']}")
                except Exception as e:
                    console.print(f"❌ Error creating Spotify playlist: {e}")
        
        # Summary
        console.print(Panel.fit(
            f"🎉 Wedding Playlist Generation Complete! 🎉\n\n"
            f"📊 Analysis:\n"
            f"• Total tracks analyzed: {len(validated_tracks)}\n"
            f"• Party-suitable tracks: {len(party_tracks)}\n"
            f"• Music style clusters: {clusters}\n"
            f"• Average AI score: {sum(t.get('ai_party_score', 0) for t in party_tracks) / len(party_tracks):.1f}/10\n\n"
            f"📁 Generated files:\n"
            f"• Text playlist: {txt_file}\n"
            f"• JSON data: {json_file}\n"
            f"• Analysis report: {report_file}",
            title="Success",
            style="bold green"
        ))
        
    except Exception as e:
        console.print(Panel.fit(
            f"❌ Error: {str(e)}\n\n"
            "Please check your credentials and try again.",
            title="Error",
            style="bold red"
        ))
        raise click.Abort()


@main.command()
def setup():
    """🔧 Set up API credentials and configuration."""
    
    console.print(Panel.fit(
        "🔧 API Credentials Setup 🔧\n\n"
        "You'll need:\n"
        "• Spotify Client ID & Secret\n"
        "• DeepSeek API Key",
        title="Setup",
        style="bold yellow"
    ))
    
    # Check for .env file
    env_file = ".env"
    if os.path.exists(env_file):
        console.print(f"📁 Found existing {env_file} file")
        if not Confirm.ask("Update existing credentials?"):
            return
    
    # Spotify credentials
    console.print("\n🎵 Spotify API Setup:")
    console.print("1. Go to https://developer.spotify.com/dashboard")
    console.print("2. Create a new app")
    console.print("3. Add redirect URI: http://localhost:8888/callback")
    
    spotify_id = click.prompt("Enter Spotify Client ID")
    spotify_secret = click.prompt("Enter Spotify Client Secret", hide_input=True)
    
    # DeepSeek credentials
    console.print("\n🤖 DeepSeek API Setup:")
    console.print("1. Go to https://platform.deepseek.com")
    console.print("2. Create an account and get API key")
    
    deepseek_key = click.prompt("Enter DeepSeek API Key", hide_input=True)
    
    # Write to .env file
    with open(env_file, 'w') as f:
        f.write(f"SPOTIFY_CLIENT_ID={spotify_id}\n")
        f.write(f"SPOTIFY_CLIENT_SECRET={spotify_secret}\n")
        f.write(f"SPOTIFY_REDIRECT_URI=http://localhost:8888/callback\n")
        f.write(f"DEEPSEEK_API_KEY={deepseek_key}\n")
    
    console.print(f"✅ Credentials saved to {env_file}")
    console.print("💡 Run 'uv run python main.py generate' to start generating playlists!")


@main.command()
def analyze():
    """📊 Analyze your Spotify music without generating playlists."""
    
    try:
        spotify_client = SpotifyClient()
        analyzer = MusicAnalyzer()
        
        tracks_count = IntPrompt.ask("How many tracks to analyze?", default=50)
        clusters_count = IntPrompt.ask("Number of style clusters?", default=5)
        
        console.print(f"\n📥 Extracting {tracks_count} tracks...")
        top_tracks = spotify_client.get_user_top_tracks(limit=min(50, tracks_count//2))
        saved_tracks = spotify_client.get_saved_tracks(limit=min(50, tracks_count//2))
        
        all_tracks = top_tracks + saved_tracks
        unique_tracks = list({track['id']: track for track in all_tracks}.values())[:tracks_count]
        
        track_ids = [track['id'] for track in unique_tracks]
        audio_features = spotify_client.get_audio_features(track_ids)
        
        df = analyzer.prepare_data(unique_tracks, audio_features)
        df_clustered, cluster_analysis = analyzer.cluster_tracks(df, n_clusters=clusters_count)
        
        analyzer.display_cluster_overview(cluster_analysis)
        
        # Generate analysis report
        generator = PlaylistGenerator()
        tracks_list = df_clustered.to_dict('records')
        report_file = generator.generate_analysis_report(tracks_list, cluster_analysis)
        
        console.print(f"\n✅ Analysis complete! Report saved to: {report_file}")
        
    except Exception as e:
        console.print(f"❌ Error: {e}")
        raise click.Abort()


@main.command()
def test():
    """🧪 Test API connections and credentials."""
    
    console.print("🧪 Testing API connections...\n")
    
    # Test Spotify
    try:
        spotify_client = SpotifyClient()
        test_tracks = spotify_client.get_user_top_tracks(limit=1)
        console.print("✅ Spotify API: Connected successfully")
    except Exception as e:
        console.print(f"❌ Spotify API: {e}")
    
    # Test DeepSeek
    try:
        ai_validator = AIValidator()
        # Create a minimal test
        test_track = [{
            'name': 'Test Song',
            'artist': 'Test Artist',
            'danceability': 0.8,
            'energy': 0.7,
            'valence': 0.6,
            'tempo': 120,
            'popularity': 80
        }]
        validated = ai_validator.validate_tracks_for_party(test_track)
        console.print("✅ DeepSeek AI API: Connected successfully")
    except Exception as e:
        console.print(f"❌ DeepSeek AI API: {e}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main() 