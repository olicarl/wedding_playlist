# 🎵 AI-Powered Wedding Playlist Generator

An intelligent Python application that analyzes your Spotify music, clusters tracks by style, and uses DeepSeek AI to create the perfect wedding party playlist.

## ✨ Features

- **🎯 Smart Music Extraction**: Pulls your favorite tracks from Spotify (top tracks + saved songs)
- **🔬 Audio Analysis**: Uses Spotify's audio features to analyze danceability, energy, mood, and tempo
- **🎪 Style Clustering**: Groups your music into distinct style clusters using machine learning
- **🤖 AI Validation**: DeepSeek AI evaluates each track's party suitability with detailed reasoning
- **📊 Rich Analytics**: Beautiful terminal displays and comprehensive analysis reports
- **📝 Multiple Outputs**: Generates text files, JSON data, and analysis reports
- **🎵 Spotify Integration**: Automatically creates playlists in your Spotify account

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/olicarl/wedding_playlist.git
cd wedding_playlist

# Install dependencies with UV
uv sync
```

### 2. Setup API Credentials

Run the interactive setup:

```bash
uv run python main.py setup
```

Or manually create a `.env` file:

```bash
cp env.example .env
# Edit .env with your credentials
```

**Required APIs:**
- **Spotify**: Get credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- **DeepSeek**: Get API key from [DeepSeek Platform](https://platform.deepseek.com)

### 3. Generate Your Playlist

```bash
# Basic generation
uv run python main.py generate

# Advanced options
uv run python main.py generate --tracks 150 --clusters 7 --ai-score 7.0 --create-spotify
```

## 🛠️ Commands

### `generate` - Create AI-curated playlist
```bash
uv run python main.py generate [OPTIONS]

Options:
  -t, --tracks INTEGER     Number of tracks to analyze (default: 100)
  -c, --clusters INTEGER   Number of music style clusters (default: 5)
  -s, --ai-score FLOAT     Minimum AI party score (default: 6.0)
  --create-spotify         Create Spotify playlist
  -o, --output-dir TEXT    Output directory for files
```

### `analyze` - Music analysis only
```bash
uv run python main.py analyze
```

### `setup` - Configure API credentials
```bash
uv run python main.py setup
```

### `test` - Test API connections
```bash
uv run python main.py test
```

## 📊 How It Works

### 1. **Music Extraction**
- Fetches your top tracks from Spotify
- Retrieves your saved/liked songs
- Combines and deduplicates the collection

### 2. **Audio Analysis**
- Extracts Spotify's audio features for each track:
  - **Danceability**: How suitable for dancing (0.0 - 1.0)
  - **Energy**: Intensity and power (0.0 - 1.0)
  - **Valence**: Musical positivity/mood (0.0 - 1.0)
  - **Tempo**: BPM of the track
  - **Acousticness**: Acoustic vs. electronic (0.0 - 1.0)

### 3. **Style Clustering**
- Uses K-means clustering with PCA dimensionality reduction
- Groups tracks into distinct musical styles
- Analyzes each cluster's characteristics
- Provides style descriptions (e.g., "High-energy dance upbeat")

### 4. **AI Validation**
- Sends batches of tracks to DeepSeek AI
- AI evaluates party suitability (1-10 score)
- Provides reasoning for each recommendation
- Considers factors like energy, danceability, and mood

### 5. **Playlist Generation**
- Filters tracks based on AI scores
- Generates multiple output formats
- Creates Spotify playlists automatically

## 📁 Output Files

The application generates several files in the `output/` directory:

- **`wedding_party_playlist_*.txt`**: Human-readable playlist with track details
- **`wedding_party_playlist_*.json`**: Machine-readable data with full metadata
- **`playlist_analysis_report_*.txt`**: Comprehensive analysis report

## 🎯 Example Workflow

```bash
# Setup (first time only)
uv run python main.py setup

# Test connections
uv run python main.py test

# Generate playlist
uv run python main.py generate --tracks 100 --create-spotify
```

## 🔧 Configuration

### Audio Feature Thresholds for Party Music
The application uses these criteria for party-suitable tracks:
- **Danceability**: 0.6 - 1.0 (high)
- **Energy**: 0.5 - 1.0 (medium to high)
- **Valence**: 0.4 - 1.0 (positive mood)
- **Tempo**: 100 - 180 BPM
- **Acousticness**: 0.0 - 0.4 (prefer electronic)

### Clustering Algorithm
- **Algorithm**: K-means with PCA preprocessing
- **Features**: 9 audio features normalized with StandardScaler
- **Dimensionality**: Reduced to 5 components via PCA
- **Clusters**: Configurable (default: 5)

## 🤖 AI Integration

The DeepSeek AI validator:
- Analyzes tracks in batches for efficiency
- Considers audio features + track metadata
- Provides 1-10 party suitability scores
- Gives detailed reasoning for each decision
- Recommends "yes", "maybe", or "no" for inclusion

## 🎵 Spotify Integration

### Required Permissions
- `user-library-read`: Access saved tracks
- `user-top-read`: Access top tracks
- `playlist-modify-public`: Create public playlists
- `playlist-modify-private`: Create private playlists

### Playlist Creation
- Automatically creates private playlists
- Includes AI-generated description with statistics
- Handles large playlists (100+ tracks)

## 🐛 Troubleshooting

### Common Issues

**Spotify Authentication Error**
- Ensure redirect URI is set to `http://localhost:8888/callback`
- Check client ID and secret are correct
- Run `uv run python main.py test` to verify

**DeepSeek API Error**
- Verify API key is valid
- Check rate limits and quotas
- Ensure you have credits in your DeepSeek account

**No Tracks Found**
- Make sure you have liked songs or listening history on Spotify
- Try reducing the number of tracks requested
- Check your Spotify account has sufficient data

## 🔗 Dependencies

- **spotipy**: Spotify Web API integration
- **scikit-learn**: Machine learning for clustering
- **pandas/numpy**: Data manipulation and analysis
- **openai**: DeepSeek AI API client
- **click**: Command-line interface
- **rich**: Beautiful terminal output
- **python-dotenv**: Environment variable management

## 🤝 Contributing

Feel free to contribute to this project! Areas for improvement:
- Additional music streaming services
- More sophisticated clustering algorithms
- Integration with other AI models
- Advanced audio feature analysis

## 📄 License

This project is open source. Feel free to use and modify as needed.

---

**Happy playlist generating! 🎉** 