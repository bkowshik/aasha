"""Module for interacting with the YouTube Data API."""

import os
from typing import Dict, List, Optional, Union
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeAPI:
    """Class for interacting with the YouTube Data API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the YouTube API client.
        
        Args:
            api_key: YouTube Data API key. If None, will try to load from environment variable.
        """
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            raise ValueError("YouTube API key is required. Set it as YOUTUBE_API_KEY environment variable or pass it directly.")
        
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=self.api_key
        )
    
    def get_channel_id(self, channel_name: str) -> str:
        """
        Get the channel ID for a given channel name.
        
        Args:
            channel_name: The name of the YouTube channel.
            
        Returns:
            The channel ID.
            
        Raises:
            ValueError: If the channel is not found.
        """
        try:
            search_response = self.youtube.search().list(
                q=channel_name,
                type="channel",
                part="id",
                maxResults=1
            ).execute()
            
            if not search_response.get("items"):
                raise ValueError(f"Channel '{channel_name}' not found.")
                
            return search_response["items"][0]["id"]["channelId"]
        except HttpError as e:
            raise ValueError(f"Error fetching channel ID: {e}")
    
    def get_videos_from_channel(self, channel_id: str, max_results: int = 10) -> List[Dict]:
        """
        Get videos from a channel.
        
        Args:
            channel_id: The ID of the YouTube channel.
            max_results: Maximum number of videos to return.
            
        Returns:
            List of video information dictionaries.
        """
        try:
            search_response = self.youtube.search().list(
                channelId=channel_id,
                type="video",
                part="id,snippet",
                maxResults=max_results,
                order="date"  # Get most recent videos
            ).execute()
            
            videos = []
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                video_title = item["snippet"]["title"]
                video_description = item["snippet"]["description"]
                published_at = item["snippet"]["publishedAt"]
                
                videos.append({
                    "id": video_id,
                    "title": video_title,
                    "description": video_description,
                    "published_at": published_at
                })
                
            return videos
        except HttpError as e:
            raise ValueError(f"Error fetching videos: {e}")
    
    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """
        Get comments for a specific video.
        
        Args:
            video_id: The ID of the YouTube video.
            max_results: Maximum number of comments to return.
            
        Returns:
            List of comment dictionaries.
        """
        try:
            comments = []
            next_page_token = None
            
            while len(comments) < max_results:
                # Get comments for the video
                response = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    pageToken=next_page_token
                ).execute()
                
                # Extract comment information
                for item in response.get("items", []):
                    comment = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "id": item["id"],
                        "text": comment["textDisplay"],
                        "author": comment["authorDisplayName"],
                        "published_at": comment["publishedAt"],
                        "like_count": comment["likeCount"]
                    })
                
                # Check if there are more comments to fetch
                next_page_token = response.get("nextPageToken")
                if not next_page_token or len(comments) >= max_results:
                    break
            
            return comments[:max_results]
        except HttpError as e:
            if "commentsDisabled" in str(e):
                return []
            raise ValueError(f"Error fetching comments: {e}")
    
    def get_comments_from_channel(self, 
                                 channel_id_or_name: str, 
                                 max_videos: int = 5, 
                                 max_comments_per_video: int = 100) -> Dict[str, List[Dict]]:
        """
        Get comments from multiple videos in a channel.
        
        Args:
            channel_id_or_name: Channel ID or name.
            max_videos: Maximum number of videos to fetch.
            max_comments_per_video: Maximum comments per video.
            
        Returns:
            Dictionary mapping video IDs to lists of comments.
        """
        # Determine if input is a channel ID or name
        if not channel_id_or_name.startswith("UC"):
            channel_id = self.get_channel_id(channel_id_or_name)
        else:
            channel_id = channel_id_or_name
            
        # Get videos from the channel
        videos = self.get_videos_from_channel(channel_id, max_results=max_videos)
        
        # Get comments for each video
        video_comments = {}
        for video in videos:
            video_id = video["id"]
            comments = self.get_video_comments(video_id, max_results=max_comments_per_video)
            video_comments[video_id] = {
                "video_info": video,
                "comments": comments
            }
            
        return video_comments
