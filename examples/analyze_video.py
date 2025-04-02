#!/usr/bin/env python3
"""
Example: Analyze YouTube comments from a specific video.
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
    # Replace with your desired video ID
    video_id = "dQw4w9WgXcQ"  # A popular YouTube video
    
    print(f"Analyzing comments from video ID: {video_id}")
    
    # Initialize our components
    youtube_api = YouTubeAPI()
    sentiment_analyzer = SentimentAnalyzer()
    report_generator = ReportGenerator(output_dir="reports")
    
    try:
        # Get comments for the video (limit to 100 comments for this example)
        comments = youtube_api.get_video_comments(video_id, max_results=100)
        
        print(f"Retrieved {len(comments)} comments")
        
        # Create a video_comments structure
        video_comments = {
            "video_info": {"id": video_id, "title": f"Video {video_id}"},
            "comments": comments
        }
        
        # Save raw data
        os.makedirs("data", exist_ok=True)
        with open(f"data/video_{video_id}_raw.json", "w") as f:
            json.dump(video_comments, f, indent=2)
        
        # Analyze sentiment
        print("\nAnalyzing sentiment...")
        video_results = sentiment_analyzer.analyze_video_comments(video_comments)
        
        # Generate reports
        print("\nGenerating reports...")
        report_paths = report_generator.generate_full_report(video_results, video_id)
        
        # Print summary
        sentiment_summary = video_results["sentiment_summary"]
        print(f"\nSentiment summary for video {video_id}:")
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
