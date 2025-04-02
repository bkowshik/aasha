#!/usr/bin/env python3
"""
Example: Analyze YouTube comments from a specific channel.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from youtube_sentiment import YouTubeAPI, SentimentAnalyzer, ReportGenerator

# Load environment variables from .env file
load_dotenv()

def main():
    """Run the example."""
    # Replace with your desired channel
    channel_name = "MKBHD"  # Marques Brownlee's tech channel
    
    print(f"Analyzing comments from channel: {channel_name}")
    
    # Initialize our components
    youtube_api = YouTubeAPI()
    sentiment_analyzer = SentimentAnalyzer()
    report_generator = ReportGenerator(output_dir="reports")
    
    try:
        # Get the channel ID
        channel_id = youtube_api.get_channel_id(channel_name)
        print(f"Found channel ID: {channel_id}")
        
        # Get videos and comments (limit to 3 videos and 50 comments per video for this example)
        video_comments = youtube_api.get_comments_from_channel(
            channel_id, 
            max_videos=3, 
            max_comments_per_video=50
        )
        
        print(f"Retrieved comments from {len(video_comments)} videos")
        
        # Save raw data
        os.makedirs("data", exist_ok=True)
        with open(f"data/{channel_name}_raw.json", "w") as f:
            json.dump(video_comments, f, indent=2)
        
        # Process each video
        for video_id, data in video_comments.items():
            video_title = data["video_info"]["title"]
            comment_count = len(data["comments"])
            
            print(f"\nAnalyzing {comment_count} comments for video: {video_title} ({video_id})")
            
            # Analyze sentiment
            video_results = sentiment_analyzer.analyze_video_comments(data)
            
            # Generate reports
            report_paths = report_generator.generate_full_report(video_results, video_id)
            
            # Print summary
            sentiment_summary = video_results["sentiment_summary"]
            print(f"Sentiment summary for {video_id}:")
            print(f"  - Total comments analyzed: {sentiment_summary['total_comments']}")
            print(f"  - Overall sentiment: {sentiment_summary['overall_sentiment']}")
            print(f"  - Positive comments: {sentiment_summary['counts']['positive']}")
            print(f"  - Negative comments: {sentiment_summary['counts']['negative']}")
            print(f"  - Neutral comments: {sentiment_summary['counts']['neutral']}")
            
            # Print report locations
            print("\nGenerated reports:")
            for report_type, path in report_paths.items():
                print(f"  - {report_type}: {path}")
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
