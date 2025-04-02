#!/usr/bin/env python3
"""
YouTube Sentiment Analysis Tool

This script analyzes sentiment in YouTube comments using the Gemini API.
"""

import os
import argparse
import json
from dotenv import load_dotenv
from youtube_sentiment import YouTubeAPI, SentimentAnalyzer, ReportGenerator

# Load environment variables
load_dotenv()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="YouTube Comment Sentiment Analysis Tool")
    
    # Required arguments
    parser.add_argument("--channel", type=str, help="YouTube channel name or ID")
    parser.add_argument("--video", type=str, help="YouTube video ID")
    
    # Optional arguments
    parser.add_argument("--max-videos", type=int, default=5, 
                        help="Maximum number of videos to analyze from channel")
    parser.add_argument("--max-comments", type=int, default=100, 
                        help="Maximum number of comments to analyze per video")
    parser.add_argument("--output-dir", type=str, default="reports", 
                        help="Directory to save reports")
    parser.add_argument("--save-raw", action="store_true", 
                        help="Save raw comments data before analysis")
    
    return parser.parse_args()

def main():
    """Main function to run the sentiment analysis."""
    args = parse_args()
    
    if not args.channel and not args.video:
        print("Error: Either --channel or --video must be specified")
        return
    
    try:
        # Initialize the YouTube API client
        youtube_api = YouTubeAPI()
        
        # Initialize the Sentiment Analyzer
        sentiment_analyzer = SentimentAnalyzer()
        
        # Initialize the Report Generator
        report_generator = ReportGenerator(output_dir=args.output_dir)
        
        # Get comments based on input type
        if args.video:
            print(f"Fetching comments for video: {args.video}")
            comments = youtube_api.get_video_comments(args.video, max_results=args.max_comments)
            video_info = {"id": args.video, "title": "Video " + args.video}
            video_comments = {
                args.video: {
                    "video_info": video_info,
                    "comments": comments
                }
            }
        else:
            print(f"Fetching videos from channel: {args.channel}")
            video_comments = youtube_api.get_comments_from_channel(
                args.channel, 
                max_videos=args.max_videos, 
                max_comments_per_video=args.max_comments
            )
        
        # Save raw comments if requested
        if args.save_raw:
            os.makedirs("data", exist_ok=True)
            raw_file = f"data/{'video_' + args.video if args.video else 'channel_' + args.channel.replace(' ', '_')}_raw.json"
            with open(raw_file, "w") as f:
                json.dump(video_comments, f, indent=2)
            print(f"Raw comments saved to {raw_file}")
        
        # Analyze sentiment for each video
        results = {}
        for video_id, data in video_comments.items():
            print(f"Analyzing sentiment for video: {video_id}")
            video_results = sentiment_analyzer.analyze_video_comments(data)
            results[video_id] = video_results
            
            # Generate report for this video
            print(f"Generating report for video: {video_id}")
            report_paths = report_generator.generate_full_report(video_results, video_id)
            
            # Print report locations
            print(f"Reports for video {video_id}:")
            for report_type, path in report_paths.items():
                print(f"  - {report_type}: {path}")
        
        print("Sentiment analysis complete!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
