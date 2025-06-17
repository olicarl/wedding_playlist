#!/usr/bin/env python3
"""Main entry point for the AI-powered wedding playlist generator."""

import os
import click
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
from rich.text import Text
from rich.progress import Progress

# Load environment variables first, before importing our modules
from dotenv import load_dotenv
load_dotenv()  # Load .env file from current directory

from .spotify_client import SpotifyClient
from .music_analyzer import MusicAnalyzer
from .ai_validator import AIValidator
from .playlist_generator import PlaylistGenerator
from .lastfm_enricher import LastFMEnricher

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
@click.option('--skip-lastfm', is_flag=True, help='Skip Last.fm metadata enrichment')
def generate(tracks, clusters, ai_score, create_spotify, output_dir, skip_lastfm):
    """🎉 Generate AI-curated wedding party playlist from your Spotify favorites."""
    
    console.print(Panel.fit(
        "🎵 AI-Powered Wedding Playlist Generator 🎵\n\n"
        "This will:\n"
        "• Extract your favorite music from Spotify\n"
        "• Enrich with Last.fm metadata\n"
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
        
        # Initialize Last.fm enricher (optional)
        lastfm_enricher = None
        if not skip_lastfm:
            lastfm_enricher = LastFMEnricher()
        
        # Step 2: Extract music from Spotify
        console.print(f"\n📥 Extracting {tracks} favorite tracks from Spotify...")
        
        # Get both top tracks and saved tracks
        top_tracks = spotify_client.get_user_top_tracks(limit=min(50, tracks//2))
        saved_tracks = spotify_client.get_saved_tracks(limit=min(50, tracks//2))
        
        # Remove duplicates and get the final list
        all_tracks = top_tracks + saved_tracks
        # Improved deduplication with debug info
        unique_tracks = list({track['id']: track for track in all_tracks if track.get('id')}.values())[:tracks]
        console.print(f"📊 Deduplicated to {len(unique_tracks)} unique tracks")
        
        # Step 3: Enrich with Last.fm metadata (optional)
        if lastfm_enricher and lastfm_enricher.network:
            console.print("\n🎵 Enriching tracks with Last.fm metadata...")
            unique_tracks = lastfm_enricher.enrich_tracks(unique_tracks)
            
            # Display genre summary
            genre_summary = lastfm_enricher.get_genre_summary(unique_tracks)
            if genre_summary:
                console.print("\n📊 Top genres found:")
                for genre, count in list(genre_summary.items())[:10]:
                    console.print(f"  • {genre}: {count} tracks")
        else:
            console.print("⚠️ Note: Using metadata-based clustering (Spotify audio features deprecated)")
        
        # Step 4: Prepare data and cluster (no audio features needed)
        df = analyzer.prepare_data(unique_tracks)
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
    console.print("3. Add redirect URI: https://127.0.0.1:8888/callback")
    
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
        f.write(f"SPOTIFY_REDIRECT_URI=https://127.0.0.1:8888/callback\n")
        f.write(f"DEEPSEEK_API_KEY={deepseek_key}\n")
    
    console.print(f"✅ Credentials saved to {env_file}")
    console.print("💡 Run 'uv run python main.py generate' to start generating playlists!")


@main.command()
@click.option('--tracks', '-t', default=20, help='Number of tracks to analyze (default: 20)')
@click.option('--clusters', '-c', default=3, help='Number of music style clusters (default: 3)')
@click.option('--skip-lastfm', is_flag=True, help='Skip Last.fm metadata enrichment')
def analyze(tracks, clusters, skip_lastfm):
    """📊 Analyze your Spotify music without generating playlists."""
    
    try:
        spotify_client = SpotifyClient()
        analyzer = MusicAnalyzer()
        lastfm_enricher = LastFMEnricher() if not skip_lastfm else None
        
        console.print(f"\n📥 Extracting {tracks} tracks...")
        top_tracks = spotify_client.get_user_top_tracks(limit=min(50, tracks//2))
        saved_tracks = spotify_client.get_saved_tracks(limit=min(50, tracks//2))
        
        all_tracks = top_tracks + saved_tracks
        # Improved deduplication with debug info
        unique_tracks = list({track['id']: track for track in all_tracks if track.get('id')}.values())[:tracks]
        console.print(f"📊 Deduplicated to {len(unique_tracks)} unique tracks")
        
        # Enrich with Last.fm metadata if enabled
        if lastfm_enricher and not skip_lastfm:
            unique_tracks = lastfm_enricher.enrich_tracks(unique_tracks)
            
            # Display genre summary
            genre_summary = lastfm_enricher.get_genre_summary(unique_tracks)
            if genre_summary:
                console.print("📊 Top genres found:")
                for genre, count in list(genre_summary.items())[:5]:
                    console.print(f"  • {genre}: {count} tracks")
        else:
            console.print("⚠️ Skipping Last.fm enrichment")
        
        console.print("⚠️ Note: Using metadata-based clustering (Spotify audio features deprecated)")
        
        # Step 3: Prepare data and cluster (no audio features needed)
        df = analyzer.prepare_data(unique_tracks)
        df_clustered, cluster_analysis = analyzer.cluster_tracks(df, n_clusters=clusters)
        
        # Display cluster overview
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
        
        # Test audio features specifically
        if test_tracks:
            track_id = test_tracks[0]['id']
            console.print(f"🔊 Testing audio features for track: {track_id}")
            features = spotify_client.sp.audio_features([track_id])
            if features and features[0]:
                console.print("✅ Spotify Audio Features: Working correctly")
            else:
                console.print("⚠️ Spotify Audio Features: No data returned")
        
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


@main.command()
def debug():
    """🔍 Debug environment variables and configuration."""
    
    console.print("🔍 Environment Variables Debug\n")
    
    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        console.print(f"✅ Found .env file: {os.path.abspath(env_file)}")
        
        # Show file size (not contents for security)
        file_size = os.path.getsize(env_file)
        console.print(f"📏 .env file size: {file_size} bytes")
    else:
        console.print(f"❌ No .env file found at: {os.path.abspath(env_file)}")
        console.print("💡 Run 'uv run python main.py setup' to create one")
    
    # Check environment variables (show only if they exist, not values)
    env_vars = {
        'SPOTIFY_CLIENT_ID': os.getenv('SPOTIFY_CLIENT_ID'),
        'SPOTIFY_CLIENT_SECRET': os.getenv('SPOTIFY_CLIENT_SECRET'),
        'SPOTIFY_REDIRECT_URI': os.getenv('SPOTIFY_REDIRECT_URI'),
        'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY')
    }
    
    console.print("\n🔑 Environment Variables Status:")
    for var, value in env_vars.items():
        if value:
            console.print(f"✅ {var}: Set (length: {len(value)})")
        else:
            console.print(f"❌ {var}: Not found")
    
    # Show current working directory
    console.print(f"\n📁 Current working directory: {os.getcwd()}")
    
    # Try to manually load .env again
    if os.path.exists(env_file):
        console.print(f"\n🔄 Manually reloading {env_file}...")
        from dotenv import load_dotenv
        success = load_dotenv(env_file, verbose=True)
        console.print(f"Load result: {success}")


@main.command()
@click.option('--playlist-file', '-f', required=True, help='Path to wedding playlist JSON file')
@click.option('--playlist-name', '-n', help='Custom name for the Spotify playlist')
@click.option('--public', is_flag=True, help='Make the playlist public (default: private)')
@click.option('--description', '-d', help='Custom description for the playlist')
def create_playlist(playlist_file, playlist_name, public, description):
    """🎵 Create a Spotify playlist from an existing wedding playlist JSON file."""
    
    try:
        # Check if file exists
        if not os.path.exists(playlist_file):
            console.print(f"❌ File not found: {playlist_file}")
            console.print("💡 Use a file generated by the 'generate' command")
            raise click.Abort()
        
        # Load the JSON playlist
        console.print(f"📂 Loading playlist from: {playlist_file}")
        
        import json
        with open(playlist_file, 'r', encoding='utf-8') as f:
            playlist_data = json.load(f)
        
        # Validate JSON structure
        if 'tracks' not in playlist_data:
            console.print("❌ Invalid playlist file: missing 'tracks' field")
            raise click.Abort()
        
        tracks = playlist_data['tracks']
        metadata = playlist_data.get('metadata', {})
        
        console.print(f"✅ Loaded {len(tracks)} tracks from playlist file")
        
        # Initialize Spotify client
        console.print("🔧 Connecting to Spotify...")
        spotify_client = SpotifyClient()
        
        # Generate playlist name if not provided
        if not playlist_name:
            original_name = metadata.get('name', 'Wedding Party Playlist')
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            playlist_name = f"{original_name} - {timestamp}"
        
        # Generate description if not provided
        if not description:
            total_tracks = len(tracks)
            total_duration = sum(track.get('duration_ms', 0) for track in tracks) / (1000 * 60)
            avg_score = sum(track.get('ai_party_score', 0) for track in tracks) / len(tracks) if tracks else 0
            
            description = (
                f"AI-curated wedding playlist with {total_tracks} tracks "
                f"({total_duration:.1f} min total). "
                f"Average party score: {avg_score:.1f}/10. "
                f"Generated by AI Wedding Playlist Generator."
            )
        
        # Extract track IDs
        track_ids = []
        invalid_tracks = []
        
        for track in tracks:
            track_id = track.get('id')
            if track_id:
                track_ids.append(track_id)
            else:
                invalid_tracks.append(track.get('name', 'Unknown'))
        
        if invalid_tracks:
            console.print(f"⚠️ Warning: {len(invalid_tracks)} tracks missing Spotify IDs")
            for track_name in invalid_tracks[:3]:  # Show first 3
                console.print(f"  • {track_name}")
            if len(invalid_tracks) > 3:
                console.print(f"  • ... and {len(invalid_tracks) - 3} more")
        
        if not track_ids:
            console.print("❌ No valid Spotify track IDs found in playlist")
            raise click.Abort()
        
        console.print(f"🎵 Creating Spotify playlist with {len(track_ids)} tracks...")
        
        # Create the playlist
        user_id = spotify_client.sp.current_user()['id']
        
        # Create playlist
        playlist = spotify_client.sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=public,
            description=description
        )
        
        playlist_id = playlist['id']
        console.print(f"✅ Created playlist: {playlist_name}")
        
        # Add tracks in batches (Spotify limit is 100 tracks per request)
        batch_size = 100
        added_count = 0
        
        with Progress() as progress:
            task = progress.add_task("Adding tracks...", total=len(track_ids))
            
            for i in range(0, len(track_ids), batch_size):
                batch = track_ids[i:i + batch_size]
                
                try:
                    spotify_client.sp.playlist_add_items(playlist_id, batch)
                    added_count += len(batch)
                    progress.update(task, advance=len(batch))
                except Exception as e:
                    console.print(f"⚠️ Error adding batch {i//batch_size + 1}: {e}")
                    # Continue with next batch
                    progress.update(task, advance=len(batch))
        
        # Display results
        playlist_url = playlist['external_urls']['spotify']
        
        console.print(Panel.fit(
            f"🎉 Spotify Playlist Created Successfully! 🎉\n\n"
            f"📊 Playlist Details:\n"
            f"• Name: {playlist_name}\n"
            f"• Tracks added: {added_count}/{len(track_ids)}\n"
            f"• Visibility: {'Public' if public else 'Private'}\n"
            f"• URL: {playlist_url}\n\n"
            f"🎵 Ready to party! Open the playlist in Spotify to start listening.",
            title="Success",
            style="bold green"
        ))
        
        # Show track details
        if len(tracks) <= 10:  # Show details for small playlists
            console.print("\n🎵 Playlist Tracks:")
            for i, track in enumerate(tracks, 1):
                score = track.get('ai_party_score', 'N/A')
                console.print(f"  {i:2d}. {track.get('name', 'Unknown')} - {track.get('artist', 'Unknown')} (Score: {score}/10)")
        else:
            console.print(f"\n🎵 Playlist contains {len(tracks)} tracks. Check Spotify for full list!")
        
    except json.JSONDecodeError:
        console.print("❌ Invalid JSON file format")
        raise click.Abort()
    except Exception as e:
        console.print(Panel.fit(
            f"❌ Error creating playlist: {str(e)}\n\n"
            "Please check your Spotify connection and try again.",
            title="Error",
            style="bold red"
        ))
        raise click.Abort()


if __name__ == "__main__":
    main() 