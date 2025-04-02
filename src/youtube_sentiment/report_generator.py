"""Module for generating reports and visualizations from sentiment analysis results."""

import os
import json
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class ReportGenerator:
    """Class for generating reports from sentiment analysis results."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize the Report Generator.
        
        Args:
            output_dir: Directory to save reports and visualizations.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _comments_to_dataframe(self, video_results: Dict) -> pd.DataFrame:
        """
        Convert comments with sentiment analysis to a DataFrame.
        
        Args:
            video_results: Dictionary with video info and analyzed comments.
            
        Returns:
            DataFrame with comment data.
        """
        comments = video_results["comments"]
        
        # Extract relevant fields from each comment
        data = []
        for comment in comments:
            if "sentiment_analysis" not in comment:
                continue
                
            row = {
                "comment_id": comment["id"],
                "text": comment["text"],
                "author": comment["author"],
                "published_at": comment["published_at"],
                "like_count": comment["like_count"],
                "sentiment": comment["sentiment_analysis"].get("sentiment", "unknown"),
                "score": comment["sentiment_analysis"].get("score", 0.0)
            }
            
            # Add topics and emotional tone if available
            if "topics" in comment["sentiment_analysis"]:
                row["topics"] = ", ".join(comment["sentiment_analysis"]["topics"])
            
            if "emotional_tone" in comment["sentiment_analysis"]:
                row["emotional_tone"] = ", ".join(comment["sentiment_analysis"]["emotional_tone"])
                
            data.append(row)
            
        return pd.DataFrame(data)
    
    def generate_summary_visualizations(self, video_results: Dict, video_id: str) -> Dict[str, str]:
        """
        Generate summary visualizations for a video's sentiment analysis.
        
        Args:
            video_results: Dictionary with video info and analyzed comments.
            video_id: ID of the video.
            
        Returns:
            Dictionary mapping visualization names to file paths.
        """
        # Convert to DataFrame
        df = self._comments_to_dataframe(video_results)
        
        if df.empty:
            return {}
            
        # Create output paths
        sentiment_dist_path = os.path.join(self.output_dir, f"{video_id}_sentiment_distribution.png")
        sentiment_score_path = os.path.join(self.output_dir, f"{video_id}_sentiment_scores.png")
        
        # Set up the style
        sns.set(style="whitegrid")
        
        # 1. Sentiment Distribution
        plt.figure(figsize=(10, 6))
        sentiment_counts = df["sentiment"].value_counts()
        ax = sentiment_counts.plot(kind="bar", color=["green", "red", "gray"])
        plt.title(f"Sentiment Distribution for Video {video_id}")
        plt.xlabel("Sentiment")
        plt.ylabel("Number of Comments")
        plt.tight_layout()
        plt.savefig(sentiment_dist_path)
        plt.close()
        
        # 2. Sentiment Score Distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(df["score"], bins=20, kde=True)
        plt.title(f"Sentiment Score Distribution for Video {video_id}")
        plt.xlabel("Sentiment Score (-1.0 to 1.0)")
        plt.ylabel("Number of Comments")
        plt.axvline(x=0, color='r', linestyle='--')
        plt.tight_layout()
        plt.savefig(sentiment_score_path)
        plt.close()
        
        return {
            "sentiment_distribution": sentiment_dist_path,
            "sentiment_scores": sentiment_score_path
        }
    
    def export_to_csv(self, video_results: Dict, video_id: str) -> str:
        """
        Export sentiment analysis results to CSV.
        
        Args:
            video_results: Dictionary with video info and analyzed comments.
            video_id: ID of the video.
            
        Returns:
            Path to the exported CSV file.
        """
        df = self._comments_to_dataframe(video_results)
        
        if df.empty:
            return ""
            
        # Create output path
        csv_path = os.path.join(self.output_dir, f"{video_id}_sentiment_analysis.csv")
        
        # Export to CSV
        df.to_csv(csv_path, index=False)
        
        return csv_path
    
    def export_to_json(self, video_results: Dict, video_id: str) -> str:
        """
        Export sentiment analysis results to JSON.
        
        Args:
            video_results: Dictionary with video info and analyzed comments.
            video_id: ID of the video.
            
        Returns:
            Path to the exported JSON file.
        """
        # Create output path
        json_path = os.path.join(self.output_dir, f"{video_id}_sentiment_analysis.json")
        
        # Export to JSON
        with open(json_path, "w") as f:
            json.dump(video_results, f, indent=2)
            
        return json_path
    
    def generate_full_report(self, video_results: Dict, video_id: str) -> Dict[str, str]:
        """
        Generate a full report including visualizations and data exports.
        
        Args:
            video_results: Dictionary with video info and analyzed comments.
            video_id: ID of the video.
            
        Returns:
            Dictionary mapping output types to file paths.
        """
        results = {}
        
        # Generate visualizations
        viz_paths = self.generate_summary_visualizations(video_results, video_id)
        results.update(viz_paths)
        
        # Export data
        csv_path = self.export_to_csv(video_results, video_id)
        if csv_path:
            results["csv_export"] = csv_path
            
        json_path = self.export_to_json(video_results, video_id)
        if json_path:
            results["json_export"] = json_path
            
        return results
