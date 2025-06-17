"""AI validation using DeepSeek API to assess party playlist suitability."""

import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


class AIValidator:
    """Uses DeepSeek AI to validate party playlist suitability."""
    
    def __init__(self):
        """Initialize the AI validator with DeepSeek API."""
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Please set DEEPSEEK_API_KEY environment variable.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def validate_tracks_for_party(self, tracks: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Validate a list of tracks for party suitability using DeepSeek AI.
        
        Args:
            tracks: List of track dictionaries with name, artist, and audio features
            batch_size: Number of tracks to validate in each API call
        
        Returns:
            List of tracks with AI validation results
        """
        console.print(f"🤖 Validating {len(tracks)} tracks with DeepSeek AI...")
        
        validated_tracks = []
        
        with Progress() as progress:
            task = progress.add_task("Validating tracks...", total=len(tracks))
            
            for i in range(0, len(tracks), batch_size):
                batch = tracks[i:i + batch_size]
                batch_results = self._validate_batch(batch)
                validated_tracks.extend(batch_results)
                progress.update(task, advance=len(batch))
        
        console.print(f"✅ Completed AI validation for {len(validated_tracks)} tracks")
        return validated_tracks
    
    def _validate_batch(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a batch of tracks using DeepSeek API."""
        try:
            # Prepare track information for AI analysis
            track_info = []
            for track in tracks:
                info = {
                    "name": track['name'],
                    "artist": track['artist'],
                    "audio_features": {
                        "danceability": track.get('danceability', 0),
                        "energy": track.get('energy', 0),
                        "valence": track.get('valence', 0),
                        "tempo": track.get('tempo', 0),
                        "popularity": track.get('popularity', 0)
                    }
                }
                track_info.append(info)
            
            # Create prompt for AI validation
            prompt = self._create_validation_prompt(track_info)
            
            # Call DeepSeek API
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a music expert specializing in party and wedding playlists. Analyze tracks for their suitability in creating an energetic, fun party atmosphere."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content
            validation_results = self._parse_ai_response(ai_response)
            
            # Combine results with original tracks
            for i, track in enumerate(tracks):
                if i < len(validation_results):
                    track.update(validation_results[i])
                else:
                    # Default values if AI response is incomplete
                    track.update({
                        'ai_party_score': 5,
                        'ai_reasoning': 'Unable to analyze',
                        'ai_recommendation': 'maybe'
                    })
            
            return tracks
            
        except Exception as e:
            console.print(f"⚠️ Error in AI validation: {e}")
            # Return tracks with default AI scores
            for track in tracks:
                track.update({
                    'ai_party_score': 5,
                    'ai_reasoning': f'API Error: {str(e)}',
                    'ai_recommendation': 'maybe'
                })
            return tracks
    
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
            features = track['audio_features']
            prompt += f"""
{i}. "{track['name']}" by {track['artist']}
   - Danceability: {features['danceability']:.2f}
   - Energy: {features['energy']:.2f}
   - Valence (positivity): {features['valence']:.2f}
   - Tempo: {features['tempo']:.0f} BPM
   - Popularity: {features['popularity']}/100
"""
        
        prompt += """
Please respond in JSON format:
[
  {
    "track_number": 1,
    "party_score": 8,
    "reasoning": "High energy and danceability make this perfect for dancing",
    "recommendation": "yes"
  },
  ...
]"""
        
        return prompt
    
    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the AI response and extract validation results."""
        try:
            # Try to find JSON in the response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                results = json.loads(json_str)
                
                # Convert to expected format
                parsed_results = []
                for result in results:
                    parsed_results.append({
                        'ai_party_score': result.get('party_score', 5),
                        'ai_reasoning': result.get('reasoning', 'No reasoning provided'),
                        'ai_recommendation': result.get('recommendation', 'maybe').lower()
                    })
                
                return parsed_results
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            console.print(f"⚠️ Error parsing AI response: {e}")
            return []
    
    def filter_party_tracks(self, validated_tracks: List[Dict[str, Any]], min_score: float = 6.0) -> List[Dict[str, Any]]:
        """
        Filter tracks based on AI validation scores.
        
        Args:
            validated_tracks: Tracks with AI validation results
            min_score: Minimum AI party score to include
        
        Returns:
            Filtered list of party-suitable tracks
        """
        party_tracks = []
        
        for track in validated_tracks:
            ai_score = track.get('ai_party_score', 0)
            ai_recommendation = track.get('ai_recommendation', 'no')
            
            if ai_score >= min_score or ai_recommendation == 'yes':
                party_tracks.append(track)
        
        console.print(f"🎉 Selected {len(party_tracks)} tracks out of {len(validated_tracks)} for party playlist")
        return party_tracks
    
    def display_validation_summary(self, validated_tracks: List[Dict[str, Any]]) -> None:
        """Display a summary of AI validation results."""
        from rich.table import Table
        
        table = Table(title="🤖 AI Validation Summary")
        table.add_column("Track", style="cyan")
        table.add_column("Artist", style="magenta")
        table.add_column("AI Score", style="green")
        table.add_column("Recommendation", style="yellow")
        table.add_column("Reasoning", style="white")
        
        # Sort by AI score (descending)
        sorted_tracks = sorted(validated_tracks, key=lambda x: x.get('ai_party_score', 0), reverse=True)
        
        for track in sorted_tracks[:15]:  # Show top 15
            score = track.get('ai_party_score', 0)
            recommendation = track.get('ai_recommendation', 'unknown')
            reasoning = track.get('ai_reasoning', 'No reasoning')
            
            # Color code recommendation
            rec_color = {
                'yes': '✅ YES',
                'maybe': '🤔 MAYBE',
                'no': '❌ NO'
            }.get(recommendation, recommendation)
            
            table.add_row(
                track['name'][:30] + "..." if len(track['name']) > 30 else track['name'],
                track['artist'][:20] + "..." if len(track['artist']) > 20 else track['artist'],
                f"{score}/10",
                rec_color,
                reasoning[:50] + "..." if len(reasoning) > 50 else reasoning
            )
        
        console.print(table) 