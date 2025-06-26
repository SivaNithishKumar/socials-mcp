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
from twitter import TwitterAPI

load_dotenv()

class TwitterRateLimitedAPI(TwitterAPI):
    """
    Twitter API client for rate-limited endpoints with proper retry and backoff logic
    Inherits from the main TwitterAPI class for OAuth functionality
    """
    
    def __init__(self):
        super().__init__()
        self.rate_limits = {}
        
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
    
    def _check_rate_limit(self, endpoint: str, response_headers: Dict[str, str]) -> None:
        """Store rate limit information from headers without printing to stdout."""
        info: Dict[str, int] = {}
        for hdr, key in [
            ('x-rate-limit-limit', 'limit'),
            ('x-rate-limit-remaining', 'remaining'),
            ('x-rate-limit-reset', 'reset'),
            ('x-user-limit-24hour', 'user_limit_24hour'),
            ('x-user-limit-24hour-remaining', 'user_limit_24hour_remaining'),
        ]:
            if hdr in response_headers:
                info[key] = int(response_headers[hdr])
        self.rate_limits[endpoint] = info
    
    def _wait_for_rate_limit(self, endpoint: str) -> bool:
        """Wait for rate limit to reset if needed"""
        if endpoint not in self.rate_limits:
            return True
            
        rate_info = self.rate_limits[endpoint]
        
        # Check if we have remaining requests
        if rate_info.get('remaining', 1) > 0:
            return True
            
        # Check if we need to wait for reset
        if 'reset' in rate_info:
            reset_time = rate_info['reset']
            current_time = int(time.time())
            wait_time = reset_time - current_time
            
            if wait_time > 0:
                time.sleep(wait_time + 1)
                
        return True
    
    def _handle_rate_limited_request(self, method: str, url: str, endpoint_name: str, 
                                   headers: Dict[str, str], **kwargs) -> Dict[str, Any]:
        """Handle requests for rate-limited endpoints with retry logic"""
        max_retries = 3
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Wait for rate limit if needed
                self._wait_for_rate_limit(endpoint_name)
                
                # Make the request
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, **kwargs)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=headers, **kwargs)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=headers, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Store rate limit info (silent)
                self._check_rate_limit(endpoint_name, dict(response.headers))
                
                # Handle different response codes
                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception:
                        return {"error": "Invalid JSON", "status_code": response.status_code, "text": response.text}
                
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    return {"error": "Rate limit exceeded", "status_code": 429}
                
                else:
                    return {"error": f"HTTP {response.status_code}", "text": response.text}
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                else:
                    return {"error": str(e)}
        
        return {"error": "Max retries exceeded"}
    
    def search_tweets(self, query: str, max_results: int = 10, tweet_fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for recent tweets (RATE LIMITED)
        
        Args:
            query: Search query
            max_results: Maximum number of tweets to return
            tweet_fields: Comma-separated list of tweet fields to include
            
        Returns:
            Dict containing search results
        """
        url = f"{self.base_url}/2/tweets/search/recent"
        params = {'query': query, 'max_results': str(max_results)}
        if tweet_fields:
            params['tweet.fields'] = tweet_fields
        headers = {'Authorization': self._generate_oauth_header('GET', url, params)}
        return self._handle_rate_limited_request('GET', url, 'search_tweets', headers, params=params)
    
    def get_list_tweets(self, list_id: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Get tweets from a specific list (RATE LIMITED)
        
        Args:
            list_id: ID of the list
            max_results: Maximum number of tweets to return
            
        Returns:
            Dict containing list tweets
        """
        url = f"{self.base_url}/2/lists/{list_id}/tweets"
        params = {'max_results': str(max_results)}
        headers = {'Authorization': self._generate_oauth_header('GET', url, params)}
        return self._handle_rate_limited_request('GET', url, f'list_tweets_{list_id}', headers, params=params)
    
    def get_user_by_username(self, username: str, user_fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information by username (RATE LIMITED)
        
        Args:
            username: Twitter username (without @)
            user_fields: Comma-separated user fields to include
            
        Returns:
            Dict containing user information
        """
        url = f"{self.base_url}/2/users/by/username/{username}"
        params: Dict[str, str] = {}
        if user_fields:
            params['user.fields'] = user_fields
        headers = {'Authorization': self._generate_oauth_header('GET', url, params)}
        return self._handle_rate_limited_request('GET', url, 'user_by_username', headers, params=params)
    
    def get_users_by_usernames(self, usernames: List[str], user_fields: Optional[str] = None) -> Dict[str, Any]:
        """
        Get multiple users by their usernames (RATE LIMITED)
        
        Args:
            usernames: List of Twitter usernames (without @)
            user_fields: Comma-separated user fields to include
            
        Returns:
            Dict containing users information
        """
        url = f"{self.base_url}/2/users/by"
        params = {'usernames': ','.join(usernames)}
        if user_fields:
            params['user.fields'] = user_fields
        headers = {'Authorization': self._generate_oauth_header('GET', url, params)}
        return self._handle_rate_limited_request('GET', url, 'users_by_usernames', headers, params=params)
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status for all tracked endpoints"""
        return {
            "rate_limits": self.rate_limits,
            "current_time": int(time.time()),
            "current_time_str": time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

    def get_tweet_analytics(self, tweet_ids: List[str], start_time: str, end_time: str,
                            analytics_fields: Optional[str] = None, granularity: str = 'day') -> Dict[str, Any]:
        url = "https://api.twitter.com/2/tweets/analytics"
        params = {
            'ids': ','.join(tweet_ids),
            'start_time': start_time,
            'end_time': end_time,
            'granularity': granularity
        }
        if analytics_fields:
            params['analytics.fields'] = analytics_fields
        headers = {'Authorization': self._generate_oauth_header('GET', url, params)}
        return self._handle_rate_limited_request('GET', url, 'tweet_analytics', headers, params=params)

    def get_media_analytics(self, media_keys: List[str], start_time: str, end_time: str,
                            media_analytics_fields: Optional[str] = None, granularity: str = 'day') -> Dict[str, Any]:
        url = "https://api.twitter.com/2/media/analytics"
        params = {
            'media_keys': ','.join(media_keys),
            'start_time': start_time,
            'end_time': end_time,
            'granularity': granularity
        }
        if media_analytics_fields:
            params['media_analytics.fields'] = media_analytics_fields
        headers = {'Authorization': self._generate_oauth_header('GET', url, params)}
        return self._handle_rate_limited_request('GET', url, 'media_analytics', headers, params=params)

# Example usage
def example_rate_limited_usage():
    """
    Example usage of the TwitterRateLimitedAPI class
    """
    try:
        # Initialize the rate-limited API client
        twitter_rl = TwitterRateLimitedAPI()
        
        # Search for tweets (with rate limiting)
        print("Testing rate-limited search...")
        search_results = twitter_rl.search_tweets("python programming", max_results=5)
        print("Search results:", search_results)
        
        # Get user information (with rate limiting)
        print("\nTesting rate-limited user lookup...")
        user_info = twitter_rl.get_user_by_username("github")
        print("User info:", user_info)
        
        # Get multiple users (with rate limiting)
        print("\nTesting rate-limited multiple user lookup...")
        users_info = twitter_rl.get_users_by_usernames(["github", "python"])
        print("Multiple users info:", users_info)
        
        # Check rate limit status
        print("\nCurrent rate limit status:")
        rate_status = twitter_rl.get_rate_limit_status()
        print(json.dumps(rate_status, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    example_rate_limited_usage() 