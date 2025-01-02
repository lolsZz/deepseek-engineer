"""DeepSeek API client implementation."""

import os
from typing import List, Dict, Any, Optional, Generator
from datetime import datetime, timedelta
import time
import json
from dataclasses import dataclass
from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, Field

class APIError(Exception):
    """Base exception for API-related errors."""
    pass

class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    pass

class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass

@dataclass
class RateLimitConfig:
    """Configuration for API rate limiting."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000
    max_retries: int = 3
    retry_delay: float = 1.0

class RequestTracker:
    """Tracks API request metrics for rate limiting."""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size  # in seconds
        self.requests: List[datetime] = []
        self.tokens: List[tuple[datetime, int]] = []
    
    def can_make_request(self, config: RateLimitConfig) -> bool:
        """Check if a new request is allowed under rate limits."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_size)
        
        # Clean old data
        self.requests = [t for t in self.requests if t > cutoff]
        self.tokens = [(t, n) for t, n in self.tokens if t > cutoff]
        
        # Check limits
        if len(self.requests) >= config.requests_per_minute:
            return False
            
        total_tokens = sum(n for _, n in self.tokens)
        if total_tokens >= config.tokens_per_minute:
            return False
            
        return True
    
    def add_request(self, token_count: Optional[int] = None):
        """Record a new request and its token usage."""
        now = datetime.now()
        self.requests.append(now)
        if token_count is not None:
            self.tokens.append((now, token_count))

class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: str
    content: str

class DeepSeekClient:
    """Client for interacting with the DeepSeek API."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com",
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        """Initialize the DeepSeek API client."""
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise AuthenticationError("No API key provided")
            
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url
        )
        
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.request_tracker = RequestTracker()
        
    def _wait_for_rate_limit(self):
        """Wait until rate limit allows next request."""
        retries = 0
        while not self.request_tracker.can_make_request(self.rate_limit_config):
            retries += 1
            if retries > self.rate_limit_config.max_retries:
                raise RateLimitError("Rate limit exceeded and max retries reached")
            time.sleep(self.rate_limit_config.retry_delay)
    
    def _count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages. Implement proper token counting here."""
        # TODO: Implement proper token counting using tiktoken
        # For now, use a rough estimate
        return sum(len(msg["content"]) // 4 for msg in messages)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> Generator[ChatCompletion, None, None] if stream else ChatCompletion:
        """
        Send a chat completion request to the DeepSeek API.
        
        Args:
            messages: List of conversation messages
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            response_format: Optional response format specification
            stream: Whether to stream the response
            
        Returns:
            Generator yielding completion chunks if streaming,
            otherwise complete completion response
        """
        try:
            # Check rate limits
            self._wait_for_rate_limit()
            
            # Track token usage
            token_count = self._count_tokens(messages)
            self.request_tracker.add_request(token_count)
            
            # Make API request
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                stream=stream
            )
            
            if stream:
                # For streaming, wrap response in generator
                def response_generator():
                    try:
                        for chunk in response:
                            yield chunk
                    except Exception as e:
                        raise APIError(f"Stream error: {str(e)}")
                        
                return response_generator()
            
            return response
            
        except Exception as e:
            if "authentication" in str(e).lower():
                raise AuthenticationError(f"Authentication failed: {str(e)}")
            elif "rate limit" in str(e).lower():
                raise RateLimitError(f"Rate limit exceeded: {str(e)}")
            else:
                raise APIError(f"API request failed: {str(e)}")
    
    def structured_chat(
        self,
        messages: List[Dict[str, str]],
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request expecting a structured JSON response.
        
        Args:
            messages: List of conversation messages
            response_schema: JSON schema for expected response
            **kwargs: Additional arguments for chat_completion
            
        Returns:
            Parsed JSON response matching schema
        """
        response = self.chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
            **kwargs
        )
        
        try:
            if hasattr(response.choices[0].message, 'content'):
                content = response.choices[0].message.content
                return json.loads(content)
            raise APIError("No content in response")
            
        except json.JSONDecodeError as e:
            raise APIError(f"Failed to parse JSON response: {str(e)}")