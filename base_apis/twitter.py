import os
import requests
import json
import hashlib
import hmac
import base64
import time
import urllib.parse
from typing import Optional, Dict, Any, List
import secrets
import string
from dotenv import load_dotenv

load_dotenv()

class TwitterAPI:
    def __init__(self):
        """
        Initialize Twitter API client with OAuth 1.0 credentials from environment variables
        """
        self.consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        self.consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Missing required Twitter API credentials in environment variables")
        
        self.base_url = "https://api.x.com"
        
    def _generate_nonce(self, length: int = 32) -> str:
        """Generate a random nonce for OAuth"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    
    def _generate_timestamp(self) -> str:
        """Generate current timestamp for OAuth"""
        return str(int(time.time()))
    
    def _percent_encode(self, text: str) -> str:
        """Percent encode text for OAuth"""
        return urllib.parse.quote(str(text), safe='')
    
    def _generate_signature_base_string(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate signature base string for OAuth"""
        # Sort parameters
        sorted_params = sorted(params.items())
        param_string = '&'.join([f"{self._percent_encode(k)}={self._percent_encode(v)}" for k, v in sorted_params])
        
        return f"{method.upper()}&{self._percent_encode(url)}&{self._percent_encode(param_string)}"
    
    def _generate_signing_key(self) -> str:
        """Generate signing key for OAuth"""
        return f"{self._percent_encode(self.consumer_secret)}&{self._percent_encode(self.access_token_secret)}"
    
    def _generate_signature(self, signature_base_string: str, signing_key: str) -> str:
        """Generate OAuth signature"""
        signature = hmac.new(
            signing_key.encode('utf-8'),
            signature_base_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _generate_oauth_header(self, method: str, url: str, params: Optional[Dict[str, str]] = None) -> str:
        """Generate OAuth 1.0 authorization header"""
        if params is None:
            params = {}
            
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_token': self.access_token,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': self._generate_timestamp(),
            'oauth_nonce': self._generate_nonce(),
            'oauth_version': '1.0'
        }
        
        # Combine OAuth params with request params for signature
        all_params = {**oauth_params, **params}
        
        # Generate signature
        signature_base_string = self._generate_signature_base_string(method, url, all_params)
        signing_key = self._generate_signing_key()
        oauth_signature = self._generate_signature(signature_base_string, signing_key)
        
        oauth_params['oauth_signature'] = oauth_signature
        
        # Build authorization header
        auth_header_params = []
        for key, value in oauth_params.items():
            auth_header_params.append(f'{self._percent_encode(key)}="{self._percent_encode(value)}"')
        
        return f"OAuth {','.join(auth_header_params)}"
    
    def create_tweet(self, text: str, media_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new tweet (optionally with media)."""
        url = f"{self.base_url}/2/tweets"
        payload: Dict[str, Any] = {"text": text}
        if media_ids:
            payload["media"] = {"media_ids": media_ids}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': self._generate_oauth_header('POST', url)
        }
        response = requests.post(url, headers=headers, json=payload)
        try:
            return response.json()
        except Exception:
            return {"error": "Invalid JSON", "status_code": response.status_code, "text": response.text}
    
    def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Delete a tweet by ID."""
        url = f"{self.base_url}/2/tweets/{tweet_id}"
        headers = {'Authorization': self._generate_oauth_header('DELETE', url)}
        response = requests.delete(url, headers=headers)
        try:
            return response.json()
        except Exception:
            return {"error": "Invalid JSON", "status_code": response.status_code, "text": response.text}
    
    def upload_media_simple(self, media_path: str, media_type: str) -> Dict[str, Any]:
        """Upload a small media file to Twitter and return the API response."""
        url = "https://upload.twitter.com/1.1/media/upload.json"
        headers = {'Authorization': self._generate_oauth_header('POST', url)}
        try:
            with open(media_path, 'rb') as media_file:
                files = {'media': media_file}
                response = requests.post(url, headers=headers, files=files)
                return response.json() if response.ok else {
                    'error': f'HTTP {response.status_code}', 'text': response.text
                }
        except Exception as exc:
            return {'error': str(exc)}
    
    def upload_media_chunked(self, media_path: str, media_type: str) -> Optional[str]:
        """Chunked upload for large files. Returns the media ID or None on failure."""
        import os
        try:
            media_size = os.path.getsize(media_path)
            init = self.upload_media_init(media_size, media_type)
            media_id = init.get('media_id')
            if not media_id:
                return None
            chunk_size = 1024 * 1024  # 1 MB
            with open(media_path, 'rb') as f:
                segment = 0
                while chunk := f.read(chunk_size):
                    if 'error' in self.upload_media_append(media_id, chunk, segment):
                        return None
                    segment += 1
            finalize = self.upload_media_finalize(media_id)
            return media_id if 'error' not in finalize else None
        except Exception:
            return None
    
    def upload_media_init(self, total_bytes: int, media_type: str) -> Dict[str, Any]:
        """Initialize chunked media upload"""
        url = "https://upload.twitter.com/1.1/media/upload.json"
        params = {
            'command': 'INIT',
            'total_bytes': str(total_bytes),
            'media_type': media_type
        }
        
        headers = {
            'Authorization': self._generate_oauth_header('POST', url, params)
        }
        
        response = requests.post(url, headers=headers, data=params)
        return response.json()
    
    def upload_media_append(self, media_id: str, chunk: bytes, segment_index: int) -> Dict[str, Any]:
        """Append chunk to media upload"""
        url = "https://upload.twitter.com/1.1/media/upload.json"
        data = {
            'command': 'APPEND',
            'media_id': media_id,
            'segment_index': str(segment_index)
        }
        
        headers = {
            'Authorization': self._generate_oauth_header('POST', url, data)
        }
        
        files = {'media': chunk}
        
        response = requests.post(url, headers=headers, data=data, files=files)
        try:
            return response.json()
        except:
            # APPEND command might not return JSON, just return success indicator
            return {'status': 'success'} if response.status_code == 200 else {'error': 'append_failed'}
    
    def upload_media_finalize(self, media_id: str) -> Dict[str, Any]:
        """Finalize chunked media upload"""
        url = "https://upload.twitter.com/1.1/media/upload.json"
        data = {
            'command': 'FINALIZE',
            'media_id': media_id
        }
        
        headers = {
            'Authorization': self._generate_oauth_header('POST', url, data)
        }
        
        response = requests.post(url, headers=headers, data=data)
        return response.json()
    
    def create_tweet_with_media(self, text: str, media_path: str, media_type: str) -> Dict[str, Any]:
        """
        Create a tweet with media attachment
        
        Args:
            text: Tweet content
            media_path: Path to media file
            media_type: Type of media
            
        Returns:
            Dict containing the created tweet data
        """
        # Try simple upload first (for smaller files)
        try:
            media_response = self.upload_media_simple(media_path, media_type)
            if 'media_id' in media_response or 'media_id_string' in media_response:
                media_id = media_response.get('media_id_string', media_response.get('media_id'))
                return self.create_tweet(text, [str(media_id)])
        except Exception:
            # simple upload failed silently; fallback to chunked
            pass
        
        # Fall back to chunked upload
        media_id = self.upload_media_chunked(media_path, media_type)
        
        if media_id:
            return self.create_tweet(text, [media_id])
        else:
            raise Exception("Failed to upload media")

# Example usage and helper functions
def example_usage():
    """
    Example usage of the TwitterAPI class (Non-rate-limited endpoints only)
    """
    try:
        # Initialize the API client
        twitter = TwitterAPI()
        
        # Create a simple tweet
        tweet_response = twitter.create_tweet("Hello World from Python! 🐍")
        print("Tweet created:", tweet_response)
        
        # Upload media
        media_response = twitter.upload_media_simple("Base APIs/media/pcm 3.jpg", "image/jpeg")
        print("Media upload:", media_response)
        
        # Create tweet with media
        if 'media_id' in media_response or 'media_id_string' in media_response:
            media_id = media_response.get('media_id_string', media_response.get('media_id'))
            tweet_with_media = twitter.create_tweet("Tweet with media!", [str(media_id)])
            print("Tweet with media:", tweet_with_media)
        
        # Note: Rate-limited endpoints (search_tweets, get_user_by_username, etc.) 
        # are now in the TwitterRateLimitedAPI class in twitter_rate_limits.py
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    example_usage()
