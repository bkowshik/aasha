"""Module for sentiment analysis using Google's Gemini API."""

import os
from typing import Dict, List, Optional, Union, Any
import json
import time
import random
from tqdm import tqdm
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SentimentAnalyzer:
    """Class for analyzing sentiment using Google's Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-pro"):
        """
        Initialize the Sentiment Analyzer.
        
        Args:
            api_key: Gemini API key. If None, will try to load from environment variable.
            model_name: Name of the Gemini model to use.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set it as GEMINI_API_KEY environment variable or pass it directly.")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Use the latest model version with safety settings
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40
        }
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(model_name=model_name, 
                                              generation_config=generation_config)
        except Exception as e:
            # Fallback to other available models if the specified one fails
            print(f"Error initializing model {model_name}: {e}")
            print("Attempting to list available models...")
            try:
                available_models = [m.name for m in genai.list_models()]
                print(f"Available models: {available_models}")
                
                # Try to find a suitable Gemini model
                gemini_models = [m for m in available_models if "gemini" in m.lower()]
                if gemini_models:
                    fallback_model = gemini_models[0]
                    print(f"Falling back to model: {fallback_model}")
                    self.model = genai.GenerativeModel(model_name=fallback_model,
                                                     generation_config=generation_config)
                else:
                    raise ValueError("No Gemini models available")
            except Exception as list_error:
                raise ValueError(f"Failed to initialize Gemini model: {e}. Additionally, could not list models: {list_error}")
    
    def analyze_comment(self, comment_text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of a single comment.
        
        Args:
            comment_text: The text of the comment to analyze.
            
        Returns:
            Dictionary containing sentiment analysis results.
        """
        # Truncate very long comments to avoid token limits
        if len(comment_text) > 1000:
            comment_text = comment_text[:997] + "..."
            
        prompt = f"""
        Task: Analyze the sentiment of the following YouTube comment.
        
        Comment: "{comment_text}"
        
        Provide a detailed sentiment analysis with the following information:
        - Overall sentiment classification (must be exactly one of: positive, negative, or neutral)
        - Sentiment score (a number from -1.0 to 1.0, where -1.0 is very negative, 0.0 is neutral, and 1.0 is very positive)
        - Key sentiment phrases from the comment
        - Topics mentioned in the comment
        - Emotional tone detected (e.g., excited, angry, sad, etc.)
        
        Format your response ONLY as a valid JSON object with this exact structure:
        {{
            "sentiment": "positive" or "negative" or "neutral",
            "score": number between -1.0 and 1.0,
            "key_phrases": [list of strings],
            "topics": [list of strings],
            "emotional_tone": [list of strings]
        }}
        
        Return ONLY the JSON object, nothing else.
        """
        
        try:
            # Attempt to generate content with the model
            response = self.model.generate_content(prompt)
            
            # Extract text from response
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'parts'):
                response_text = ''.join([part.text for part in response.parts])
            else:
                # Handle other response formats
                response_text = str(response)
            
            # Clean up the response text
            response_text = response_text.strip()
            
            # Remove markdown code block markers if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
                
            response_text = response_text.strip()
            
            # Find JSON content (handle potential text before/after JSON)
            try:
                # Try to parse the entire response as JSON first
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        # If JSON extraction still fails, create a basic result
                        print(f"Failed to parse JSON from: {json_str}")
                        result = self._create_default_result()
                else:
                    # If JSON extraction fails, create a basic result
                    print(f"No JSON found in response: {response_text[:100]}...")
                    result = self._create_default_result()
            
            # Validate the result has the expected fields
            required_fields = ["sentiment", "score", "key_phrases", "topics", "emotional_tone"]
            for field in required_fields:
                if field not in result:
                    result[field] = self._get_default_value(field)
            
            return result
        except Exception as e:
            print(f"Error analyzing comment: {e}")
            return {
                "sentiment": "error",
                "score": 0.0,
                "key_phrases": [],
                "topics": [],
                "emotional_tone": [],
                "error": str(e)
            }
    
    def _create_default_result(self) -> Dict[str, Any]:
        """Create a default result when JSON parsing fails."""
        return {
            "sentiment": "unknown",
            "score": 0.0,
            "key_phrases": [],
            "topics": [],
            "emotional_tone": []
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for a specific field."""
        defaults = {
            "sentiment": "unknown",
            "score": 0.0,
            "key_phrases": [],
            "topics": [],
            "emotional_tone": []
        }
        return defaults.get(field, None)
    
    def analyze_comments_batch(self, comments: List[Dict], 
                              batch_size: int = 10, 
                              rate_limit_delay: float = 2.0,
                              max_retries: int = 3) -> List[Dict]:
        """
        Analyze sentiment for a batch of comments.
        
        Args:
            comments: List of comment dictionaries.
            batch_size: Number of comments to process in each batch.
            rate_limit_delay: Delay between API calls to avoid rate limiting.
            max_retries: Maximum number of retries for failed API calls.
            
        Returns:
            List of comment dictionaries with sentiment analysis added.
        """
        results = []
        
        # Process comments in batches with progress bar
        for i in tqdm(range(0, len(comments), batch_size), desc="Analyzing comments"):
            batch = comments[i:i+batch_size]
            
            for comment in batch:
                # Skip if already analyzed
                if "sentiment_analysis" in comment:
                    results.append(comment)
                    continue
                
                # Analyze sentiment with retry logic
                retry_count = 0
                sentiment_result = None
                
                while retry_count < max_retries:
                    try:
                        # Add jitter to delay to avoid synchronized retries
                        jitter = random.uniform(0.5, 1.5)
                        current_delay = rate_limit_delay * jitter
                        
                        # Exponential backoff on retries
                        if retry_count > 0:
                            backoff_delay = current_delay * (2 ** retry_count)
                            print(f"Retry {retry_count}/{max_retries} after {backoff_delay:.2f}s delay")
                            time.sleep(backoff_delay)
                        
                        # Analyze sentiment
                        sentiment_result = self.analyze_comment(comment["text"])
                        
                        # If we get here without exception, break the retry loop
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        if "quota" in str(e).lower() or "429" in str(e):
                            # Handle quota exceeded errors with longer backoff
                            print(f"Quota limit reached. Waiting before retry {retry_count}/{max_retries}")
                            time.sleep(15 * retry_count)  # Longer delay for quota issues
                        elif retry_count >= max_retries:
                            print(f"Failed after {max_retries} retries: {e}")
                            # Create a default result for failed analysis
                            sentiment_result = self._create_default_result()
                            sentiment_result["error"] = str(e)
                        else:
                            print(f"Error (will retry): {e}")
                
                # If all retries failed and we don't have a result, create a default one
                if sentiment_result is None:
                    sentiment_result = self._create_default_result()
                    sentiment_result["error"] = "Max retries exceeded"
                
                # Add sentiment analysis to comment
                comment_with_sentiment = comment.copy()
                comment_with_sentiment["sentiment_analysis"] = sentiment_result
                results.append(comment_with_sentiment)
                
                # Delay to avoid rate limiting (only if not already delayed due to retry)
                if retry_count == 0:
                    time.sleep(rate_limit_delay)
        
        return results
    
    def analyze_video_comments(self, video_comments: Dict) -> Dict:
        """
        Analyze sentiment for all comments in a video.
        
        Args:
            video_comments: Dictionary with video info and comments.
            
        Returns:
            Dictionary with video info and comments with sentiment analysis.
        """
        result = {
            "video_info": video_comments["video_info"],
            "comments": self.analyze_comments_batch(video_comments["comments"])
        }
        
        # Add summary statistics
        sentiments = [c["sentiment_analysis"]["sentiment"] for c in result["comments"] 
                     if "sentiment_analysis" in c and "sentiment" in c["sentiment_analysis"]]
        
        sentiment_counts = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral"),
            "unknown": len(result["comments"]) - len(sentiments)
        }
        
        result["sentiment_summary"] = {
            "counts": sentiment_counts,
            "total_comments": len(result["comments"]),
            "overall_sentiment": max(sentiment_counts, key=sentiment_counts.get)
        }
        
        return result
