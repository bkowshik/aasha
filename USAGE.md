# YouTube Sentiment Analysis Tool - Usage Guide

This guide explains how to set up and use the YouTube Sentiment Analysis tool to analyze comments from YouTube videos or channels using the Gemini API.

## Setup

1. **Clone the repository**:
   ```
   git clone https://github.com/bkowshik/aasha.git
   cd aasha
   ```

2. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

3. **Set up API keys**:
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Edit the `.env` file and add your API keys:
     - YouTube Data API key: Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
     - Gemini API key: Get from [Google AI Studio](https://ai.google.dev/)

## Usage

### Command Line Interface

The main script provides a command-line interface for analyzing YouTube comments:

```bash
# Analyze comments from a specific channel
python src/main.py --channel "MKBHD" --max-videos 3 --max-comments 100

# Analyze comments from a specific video
python src/main.py --video "dQw4w9WgXcQ" --max-comments 200

# Save raw comments data before analysis
python src/main.py --channel "MKBHD" --save-raw

# Specify a custom output directory
python src/main.py --video "dQw4w9WgXcQ" --output-dir "my_reports"
```

### Using the Examples

The `examples` directory contains ready-to-use scripts:

1. **Analyze a channel**:
   ```bash
   python examples/analyze_channel.py
   ```
   Edit the script to change the channel name.

2. **Analyze a specific video**:
   ```bash
   python examples/analyze_video.py
   ```
   Edit the script to change the video ID.

## Output

The tool generates several outputs:

1. **CSV Export**: Tabular data with comments and sentiment analysis
2. **JSON Export**: Complete data including video info, comments, and sentiment analysis
3. **Visualizations**:
   - Sentiment distribution (positive/negative/neutral)
   - Sentiment score distribution

All outputs are saved to the `reports` directory by default.

## Using as a Library

You can also use the components as a library in your own Python code:

```python
from youtube_sentiment import YouTubeAPI, SentimentAnalyzer, ReportGenerator

# Initialize components
youtube_api = YouTubeAPI()
sentiment_analyzer = SentimentAnalyzer()
report_generator = ReportGenerator()

# Get comments from a channel
video_comments = youtube_api.get_comments_from_channel("ChannelName", max_videos=3)

# Analyze sentiment
results = sentiment_analyzer.analyze_video_comments(video_comments["video_id"])

# Generate reports
report_generator.generate_full_report(results, "video_id")
```

## Troubleshooting

- **API Quota Limits**: The YouTube Data API has quota limits. If you hit these limits, try reducing the number of videos or comments you're analyzing.
- **Rate Limiting**: The Gemini API may have rate limits. The tool includes delays between requests to avoid this, but you may need to adjust the `rate_limit_delay` parameter.
- **Missing Comments**: Some videos may have comments disabled or restricted, resulting in fewer comments than expected.
