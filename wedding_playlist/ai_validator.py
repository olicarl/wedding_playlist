"""AI-powered track validation for party playlists."""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, TaskID

# Ensure environment variables are loaded
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, assume env vars are set manually

console = Console()


class AIValidator:
    """Uses AI to validate tracks for party playlist suitability."""
    
    def __init__(self):
        """Initialize the AI validator."""
        # Initialize OpenAI client (DeepSeek API)
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            console.print("⚠️ DEEPSEEK_API_KEY not found - AI validation will be skipped")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
        
        # Create logs directory
        self.logs_dir = "output/ai_logs"
        os.makedirs(self.logs_dir, exist_ok=True)
    
    def validate_tracks_for_party(self, tracks: List[Dict[str, Any]], batch_size: int = 5) -> List[Dict[str, Any]]:
        """Validate tracks for party playlist suitability using AI."""
        
        if not self.client:
            console.print("⚠️ AI validation skipped - no API key")
            # Return tracks with default scores
            for track in tracks:
                track.update({
                    'ai_party_score': 5,
                    'ai_reasoning': 'AI validation unavailable',
                    'ai_recommendation': 'maybe'
                })
            return tracks
        
        console.print(f"🤖 Validating {len(tracks)} tracks with AI...")
        
        validated_tracks = []
        
        with Progress() as progress:
            task = progress.add_task("Validating tracks...", total=len(tracks))
            
            for i in range(0, len(tracks), batch_size):
                batch_number = (i // batch_size) + 1
                batch = tracks[i:i + batch_size]
                batch_results = self._validate_batch(batch, batch_number)
                validated_tracks.extend(batch_results)
                progress.update(task, advance=len(batch))
        
        return validated_tracks
    
    def _validate_batch(self, tracks: List[Dict[str, Any]], batch_number: int) -> List[Dict[str, Any]]:
        """Validate a batch of tracks using DeepSeek API."""
        
        try:
            # Prepare track information for AI analysis (metadata only)
            track_info = []
            for track in tracks:
                # Just pass the track as-is since we now use metadata
                track_info.append(track)
            
            # Create prompt for AI
            prompt = self._create_validation_prompt(track_info)
            
            # Call DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a music expert specializing in party and wedding playlists."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse AI response and update tracks
            validation_results = self._parse_ai_response(ai_response, tracks)
            
            # Log the validation batch
            self.log_validation_batch(batch_number, tracks, prompt, ai_response, validation_results)
            
            return validation_results
            
        except Exception as e:
            console.print(f"⚠️ Error in AI validation: {e}")
            # Return tracks with default AI scores
            error_results = []
            for track in tracks:
                error_result = {
                    'ai_party_score': 5,
                    'ai_reasoning': f'API Error: {str(e)}',
                    'ai_recommendation': 'maybe'
                }
                track.update(error_result)
                error_results.append(track)
            
            # Log the error
            self.log_validation_batch(batch_number, tracks, "ERROR", str(e), error_results)
            
            return error_results
    
    def _create_validation_prompt(self, track_info: List[Dict[str, Any]]) -> str:
        """Create a prompt for the AI to validate party suitability."""
        prompt = """Analyze the following tracks for their suitability in a wedding/party playlist. 
Consider factors like danceability, energy, mood, and overall party atmosphere.

For each track, provide:
1. party_score (1-10): How suitable is this track for a party? (1=terrible, 10=perfect)
2. reasoning: Brief explanation of why it fits or doesn't fit
3. recommendation: "yes", "no", or "maybe"

Tracks to analyze:
"""
        
        for i, track in enumerate(track_info, 1):
            track_description = self._format_track_for_ai(track)
            prompt += f"\n{i}. {track_description}"
        
        prompt += """

Please respond in JSON format with an array of objects, each containing:
{
  "track_number": number,
  "party_score": number,
  "reasoning": "string",
  "recommendation": "yes/no/maybe"
}
"""
        
        return prompt
    
    def _format_track_for_ai(self, track: Dict[str, Any]) -> str:
        """Format track information for AI analysis (metadata-based with Last.fm enrichment)."""
        
        # Basic track info
        track_info = f"Track: {track.get('name', 'Unknown')} by {track.get('artist', 'Unknown Artist')}"
        
        # Add available Spotify metadata
        metadata_parts = []
        
        if 'popularity' in track:
            metadata_parts.append(f"Spotify popularity: {track['popularity']}/100")
        
        if 'release_year' in track:
            metadata_parts.append(f"Year: {track['release_year']}")
        
        if 'duration_ms' in track:
            duration_min = track['duration_ms'] / (1000 * 60)
            metadata_parts.append(f"Duration: {duration_min:.1f}min")
        
        # Add estimated energy from track name analysis
        name_energy = self._estimate_energy_from_name(track.get('name', ''))
        if name_energy:
            metadata_parts.append(f"Estimated energy: {name_energy}")
        
        # Add album info if available
        if 'album' in track and isinstance(track['album'], dict):
            album_name = track['album'].get('name', '')
            if album_name:
                metadata_parts.append(f"Album: {album_name}")
        
        # Add Last.fm metadata if available
        lastfm_data = track.get('lastfm', {})
        if lastfm_data:
            # Add Last.fm popularity metrics
            if 'playcount' in lastfm_data and lastfm_data['playcount'] > 0:
                metadata_parts.append(f"Last.fm plays: {lastfm_data['playcount']:,}")
            
            if 'listeners' in lastfm_data and lastfm_data['listeners'] > 0:
                metadata_parts.append(f"Last.fm listeners: {lastfm_data['listeners']:,}")
            
            # Add genres/tags from Last.fm
            if 'genres' in lastfm_data and lastfm_data['genres']:
                genres_str = ', '.join(lastfm_data['genres'][:3])  # Top 3 genres
                metadata_parts.append(f"Genres: {genres_str}")
            
            # Add artist popularity from Last.fm
            artist_info = lastfm_data.get('artist_info', {})
            if 'listeners' in artist_info and artist_info['listeners'] > 0:
                metadata_parts.append(f"Artist listeners: {artist_info['listeners']:,}")
            
            # Add artist style tags
            if 'artist_tags' in lastfm_data and lastfm_data['artist_tags']:
                artist_tags_str = ', '.join(lastfm_data['artist_tags'][:2])  # Top 2 artist tags
                metadata_parts.append(f"Artist style: {artist_tags_str}")
            
            # Add similar tracks for context
            if 'similar_tracks' in lastfm_data and lastfm_data['similar_tracks']:
                similar = lastfm_data['similar_tracks'][:2]  # Top 2 similar tracks
                similar_str = ', '.join([f"{s['artist']} - {s['track']}" for s in similar])
                metadata_parts.append(f"Similar to: {similar_str}")
        
        # Combine all metadata
        if metadata_parts:
            track_info += " | " + " | ".join(metadata_parts)
        
        return track_info

    def _estimate_energy_from_name(self, track_name: str) -> str:
        """Estimate energy level from track name keywords."""
        if not track_name:
            return ""
        
        track_lower = track_name.lower()
        
        # High energy keywords
        high_energy_words = ['party', 'dance', 'pump', 'energy', 'wild', 'crazy', 'fire', 'hype', 'upbeat', 'bounce']
        # Low energy keywords  
        low_energy_words = ['slow', 'ballad', 'sad', 'melancholy', 'quiet', 'soft', 'gentle', 'calm', 'peaceful']
        
        high_count = sum(1 for word in high_energy_words if word in track_lower)
        low_count = sum(1 for word in low_energy_words if word in track_lower)
        
        if high_count > low_count:
            return "High"
        elif low_count > high_count:
            return "Low"
        else:
            return "Medium"
    
    def _parse_ai_response(self, ai_response: str, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse AI response and update track information."""
        
        try:
            # Try to extract JSON from the response
            json_start = ai_response.find('[')
            json_end = ai_response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                ai_results = json.loads(json_str)
                
                # Update tracks with AI results
                for i, result in enumerate(ai_results):
                    if i < len(tracks):
                        tracks[i].update({
                            'ai_party_score': result.get('party_score', 5),
                            'ai_reasoning': result.get('reasoning', 'No reasoning provided'),
                            'ai_recommendation': result.get('recommendation', 'maybe')
                        })
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            console.print(f"⚠️ Error parsing AI response: {e}")
            # Fallback: assign default scores
            for track in tracks:
                track.update({
                    'ai_party_score': 5,
                    'ai_reasoning': f'Parsing error: {str(e)}',
                    'ai_recommendation': 'maybe'
                })
        
        return tracks
    
    def log_validation_batch(self, batch_number: int, tracks: List[Dict[str, Any]], 
                           prompt: str, ai_response: str, results: List[Dict[str, Any]]):
        """Log the complete AI validation process for review."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create human-readable log
        log_filename = f"ai_validation_{timestamp}.log"
        log_path = os.path.join(self.logs_dir, log_filename)
        
        # Create detailed JSON log
        json_filename = f"ai_detailed_{timestamp}.json"
        json_path = os.path.join(self.logs_dir, json_filename)
        
        # Write human-readable log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"BATCH {batch_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n\n")
            
            f.write("TRACKS BEING ANALYZED:\n")
            f.write("-" * 40 + "\n")
            for i, track in enumerate(tracks, 1):
                f.write(f"{i}. {track.get('name', 'Unknown')} by {track.get('artist', 'Unknown')}\n")
            
            f.write(f"\nAI PROMPT SENT:\n")
            f.write("-" * 40 + "\n")
            f.write(prompt + "\n")
            
            f.write(f"\nAI RESPONSE RECEIVED:\n")
            f.write("-" * 40 + "\n")
            f.write(ai_response + "\n")
            
            f.write(f"\nPARSED RESULTS:\n")
            f.write("-" * 40 + "\n")
            for track in results:
                f.write(f"• {track.get('name', 'Unknown')} by {track.get('artist', 'Unknown')}\n")
                f.write(f"  Score: {track.get('ai_party_score', 'N/A')}/10\n")
                f.write(f"  Recommendation: {track.get('ai_recommendation', 'N/A')}\n")
                f.write(f"  Reasoning: {track.get('ai_reasoning', 'N/A')}\n\n")
        
        # Write detailed JSON log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "batch_number": batch_number,
            "tracks": tracks,
            "prompt": prompt,
            "ai_response": ai_response,
            "results": results
        }
        
        # Read existing log or create new
        json_data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            except:
                json_data = []
        
        json_data.append(log_entry)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"📝 Logged batch {batch_number} to {log_filename} and {json_filename}")
    
    def display_validation_summary(self, tracks: List[Dict[str, Any]]):
        """Display a summary of AI validation results."""
        
        # Calculate statistics
        scores = [track.get('ai_party_score', 0) for track in tracks]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        recommendations = {}
        for track in tracks:
            rec = track.get('ai_recommendation', 'unknown')
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        # Display summary
        console.print("\n🤖 AI Validation Summary:")
        console.print(f"   Average party score: {avg_score:.1f}/10")
        console.print(f"   Recommendations:")
        for rec, count in recommendations.items():
            console.print(f"     • {rec}: {count} tracks")
    
    def filter_party_tracks(self, tracks: List[Dict[str, Any]], min_score: float = 6.0) -> List[Dict[str, Any]]:
        """Filter tracks that are suitable for parties based on AI scores."""
        
        party_tracks = [
            track for track in tracks 
            if track.get('ai_party_score', 0) >= min_score
        ]
        
        # Sort by AI score (highest first)
        party_tracks.sort(key=lambda x: x.get('ai_party_score', 0), reverse=True)
        
        return party_tracks 