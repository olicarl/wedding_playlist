# 🎵 AI-Powered Wedding Playlist Generator

An intelligent wedding playlist generator that extracts your favorite music from Spotify, enriches it with Last.fm metadata, clusters tracks by music style, and uses DeepSeek AI to validate tracks for party suitability.

## ✨ Features

- **🎧 Spotify Integration**: Extract your top tracks and saved songs
- **🎵 Last.fm Enrichment**: Add detailed genre tags, similar tracks, and popularity metrics
- **🧠 AI-Powered Analysis**: Uses DeepSeek AI to evaluate party suitability
- **📊 Music Clustering**: Groups tracks by musical style using machine learning
- **📁 Multiple Output Formats**: TXT, JSON, and detailed analysis reports
- **🎉 Spotify Playlist Creation**: Automatically create playlists on your Spotify account
- **📝 Comprehensive Logging**: Detailed logs of AI analysis for review

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- UV package manager
- Spotify Developer Account
- DeepSeek API Account
- Last.fm API Account (optional, for enhanced metadata)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/wedding_playlist.git
cd wedding_playlist

# Install dependencies using UV
uv sync
```

### 3. Setup API Credentials

#### Spotify API Setup
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add redirect URI: `https://127.0.0.1:8888/callback`
4. Copy Client ID and Client Secret

#### DeepSeek API Setup
1. Visit [DeepSeek Platform](https://platform.deepseek.com)
2. Create an account and get your API key

#### Last.fm API Setup (Optional)
1. Go to [Last.fm API](https://www.last.fm/api/account/create)
2. Create an API account
3. Get your API key

#### Environment Configuration
Copy the example environment file and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your API credentials:

```env
# Spotify API credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_REDIRECT_URI=https://127.0.0.1:8888/callback

# DeepSeek API credentials
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Last.fm API credentials (optional - for enhanced metadata)
LASTFM_API_KEY=your_lastfm_api_key_here
```

### 4. First Run

Set up Spotify authentication:

```bash
uv run python main.py setup
```

## 📖 Usage

### Generate Complete Wedding Playlist

```bash
# Generate playlist with 50 tracks, 5 clusters, minimum AI score of 6.0
uv run python main.py generate --tracks 50 --clusters 5 --min-score 6.0

# Create playlist directly on Spotify
uv run python main.py generate --tracks 30 --create-spotify-playlist

# Skip Last.fm enrichment for faster processing
uv run python main.py generate --tracks 20 --skip-lastfm
```

### Quick Music Analysis

```bash
# Analyze your music collection without generating playlists
uv run python main.py analyze --tracks 30 --clusters 4

# Skip Last.fm for faster analysis
uv run python main.py analyze --tracks 20 --skip-lastfm
```

### Test API Connections

```bash
# Test all API connections
uv run python main.py test

# Debug environment variables
uv run python main.py debug
```

## 🔧 Command Line Options

### `generate` - Generate Wedding Playlist
- `--tracks`: Number of tracks to analyze (default: 50)
- `--clusters`: Number of music style clusters (default: 5)
- `--min-score`: Minimum AI score for party tracks (default: 6.0)
- `--create-spotify-playlist`: Create playlist on Spotify
- `--skip-lastfm`: Skip Last.fm metadata enrichment

### `analyze` - Music Collection Analysis
- `--tracks`: Number of tracks to analyze (default: 20)
- `--clusters`: Number of clusters (default: 3)
- `--skip-lastfm`: Skip Last.fm metadata enrichment

### `setup` - Configure Spotify Authentication
- Interactive setup for Spotify OAuth

### `test` - Test API Connections
- Validates all API credentials and connections

### `debug` - Debug Environment
- Shows environment variable status

## 📊 Output Files

The generator creates several output files in the `output/` directory:

### Playlist Files
- `wedding_party_playlist_YYYYMMDD_HHMMSS.txt` - Simple track list
- `wedding_party_playlist_YYYYMMDD_HHMMSS.json` - Detailed track data

### Analysis Reports
- `playlist_analysis_report_YYYYMMDD_HHMMSS.txt` - Comprehensive analysis
- `music_clusters_YYYYMMDD_HHMMSS.json` - Clustering analysis

### AI Logs (for review)
- `output/ai_logs/ai_validation_YYYYMMDD_HHMMSS.log` - Human-readable AI analysis
- `output/ai_logs/ai_detailed_YYYYMMDD_HHMMSS.json` - Structured AI data

## 🎯 How It Works

1. **🎵 Music Extraction**: Fetches your top tracks and saved songs from Spotify
2. **🔍 Metadata Enrichment**: Adds Last.fm data including genres, similar tracks, and popularity
3. **🧮 Style Clustering**: Uses K-means clustering to group tracks by musical characteristics
4. **🤖 AI Validation**: DeepSeek AI analyzes each track for party suitability
5. **📊 Analysis & Filtering**: Generates detailed reports and filters tracks by AI scores
6. **🎉 Playlist Creation**: Creates final playlist files and optionally Spotify playlists

## 🎨 Example Output

```
🎵 AI-Powered Wedding Playlist Generator 🎵

📥 Extracting 50 favorite tracks from Spotify...
📊 Deduplicated to 47 unique tracks

🎵 Enriching tracks with Last.fm metadata...
📊 Top genres found:
  • pop: 12 tracks
  • rock: 8 tracks
  • electronic: 6 tracks

🧮 Clustering 47 tracks into 5 style groups...
🤖 Starting AI validation with DeepSeek...
🎉 Selected 23 tracks for the party playlist!

📄 Generating outputs...
✅ Created: wedding_party_playlist_20240617_143022.txt
✅ Created: wedding_party_playlist_20240617_143022.json
✅ Created: playlist_analysis_report_20240617_143022.txt
```

## 🔍 AI Analysis Details

The AI logs provide complete transparency into the decision-making process:

- **Full prompts** sent to the AI
- **Complete responses** from DeepSeek
- **Detailed reasoning** for each track
- **Party suitability scores** (1-10)
- **Recommendations** (yes/no/maybe)

## 🛠️ Troubleshooting

### Common Issues

1. **"INVALID_CLIENT: Invalid redirect URI"**
   - Ensure redirect URI in Spotify app settings matches: `https://127.0.0.1:8888/callback`

2. **"DEEPSEEK_API_KEY not found"**
   - Check your `.env` file has the correct API key
   - Verify the key is valid on DeepSeek platform

3. **"Last.fm enrichment failed"**
   - Last.fm API key may be invalid or missing
   - Use `--skip-lastfm` flag to bypass Last.fm enrichment

4. **Rate limiting errors**
   - The tool includes automatic rate limiting and retries
   - For persistent issues, reduce batch sizes or add delays

### Debug Commands

```bash
# Check environment variables
uv run python main.py debug

# Test individual API connections
uv run python main.py test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Spotify** for the comprehensive music API
- **Last.fm** for detailed music metadata and genre information
- **DeepSeek** for AI-powered music analysis
- **scikit-learn** for machine learning clustering algorithms

---

*Perfect for weddings, parties, and any celebration where you want AI-curated music that gets people dancing! 🎉* 