"""Tests for the DeepSeek API client."""

import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta
from openai.types.chat import ChatCompletion, ChatCompletionMessage, Choice
from deepseek_engineer.core.api_client import (
    DeepSeekClient,
    APIError,
    RateLimitError,
    AuthenticationError,
    RateLimitConfig,
    RequestTracker
)

@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch('deepseek_engineer.core.api_client.OpenAI') as mock:
        yield mock

@pytest.fixture
def client(mock_openai):
    """Create a DeepSeekClient instance with mocked OpenAI."""
    return DeepSeekClient(api_key="test_key")

def create_mock_completion(content: str) -> ChatCompletion:
    """Create a mock ChatCompletion object."""
    message = ChatCompletionMessage(role="assistant", content=content)
    choice = Choice(message=message, index=0, finish_reason="stop")
    return ChatCompletion(id="test", choices=[choice], created=1234, model="test", object="chat.completion")

def test_init_with_key():
    """Test client initialization with API key."""
    client = DeepSeekClient(api_key="test_key")
    assert client.api_key == "test_key"

def test_init_without_key():
    """Test client initialization fails without API key."""
    with pytest.raises(AuthenticationError):
        DeepSeekClient(api_key=None)

def test_chat_completion_success(client, mock_openai):
    """Test successful chat completion request."""
    expected_response = create_mock_completion("Test response")
    mock_openai.return_value.chat.completions.create.return_value = expected_response
    
    messages = [{"role": "user", "content": "Hello"}]
    response = client.chat_completion(messages)
    
    assert response.choices[0].message.content == "Test response"
    mock_openai.return_value.chat.completions.create.assert_called_once()

def test_chat_completion_authentication_error(client, mock_openai):
    """Test chat completion with authentication error."""
    mock_openai.return_value.chat.completions.create.side_effect = Exception("authentication failed")
    
    with pytest.raises(AuthenticationError):
        client.chat_completion([{"role": "user", "content": "Hello"}])

def test_chat_completion_rate_limit_error(client, mock_openai):
    """Test chat completion with rate limit error."""
    mock_openai.return_value.chat.completions.create.side_effect = Exception("rate limit exceeded")
    
    with pytest.raises(RateLimitError):
        client.chat_completion([{"role": "user", "content": "Hello"}])

def test_chat_completion_streaming(client, mock_openai):
    """Test streaming chat completion."""
    chunks = [
        create_mock_completion("Hello"),
        create_mock_completion("World")
    ]
    mock_openai.return_value.chat.completions.create.return_value = chunks
    
    messages = [{"role": "user", "content": "Hello"}]
    stream = client.chat_completion(messages, stream=True)
    
    # Convert generator to list to test contents
    responses = list(stream)
    assert len(responses) == 2
    assert responses[0].choices[0].message.content == "Hello"
    assert responses[1].choices[0].message.content == "World"

def test_structured_chat_success(client, mock_openai):
    """Test structured chat with JSON response."""
    json_response = {"key": "value"}
    mock_completion = create_mock_completion(json.dumps(json_response))
    mock_openai.return_value.chat.completions.create.return_value = mock_completion
    
    messages = [{"role": "user", "content": "Hello"}]
    response = client.structured_chat(messages, {})
    
    assert response == json_response

def test_structured_chat_invalid_json(client, mock_openai):
    """Test structured chat with invalid JSON response."""
    mock_completion = create_mock_completion("invalid json")
    mock_openai.return_value.chat.completions.create.return_value = mock_completion
    
    messages = [{"role": "user", "content": "Hello"}]
    with pytest.raises(APIError, match="Failed to parse JSON response"):
        client.structured_chat(messages, {})

def test_request_tracker():
    """Test request tracking and rate limiting."""
    tracker = RequestTracker(window_size=60)
    config = RateLimitConfig(requests_per_minute=2, tokens_per_minute=100)
    
    # First request should be allowed
    assert tracker.can_make_request(config) is True
    tracker.add_request(50)  # 50 tokens
    
    # Second request should be allowed
    assert tracker.can_make_request(config) is True
    tracker.add_request(40)  # +40 tokens = 90 total
    
    # Third request should be denied (request limit)
    assert tracker.can_make_request(config) is False
    
    # Test token limit
    tracker = RequestTracker(window_size=60)
    tracker.add_request(90)  # 90 tokens
    assert tracker.can_make_request(config) is True
    tracker.add_request(20)  # Would exceed token limit
    assert tracker.can_make_request(config) is False

def test_request_tracker_window():
    """Test request tracker window expiration."""
    tracker = RequestTracker(window_size=1)  # 1 second window
    config = RateLimitConfig(requests_per_minute=1)
    
    tracker.add_request()
    assert tracker.can_make_request(config) is False
    
    # Wait for window to expire
    import time
    time.sleep(1.1)
    
    # Should be allowed after window expiration
    assert tracker.can_make_request(config) is True

def test_rate_limit_wait(client):
    """Test rate limit waiting behavior."""
    config = RateLimitConfig(
        requests_per_minute=1,
        max_retries=2,
        retry_delay=0.1
    )
    client.rate_limit_config = config
    
    # Make initial request
    client.request_tracker.add_request()
    
    # Next request should trigger waiting
    with pytest.raises(RateLimitError):
        client._wait_for_rate_limit()

def test_custom_rate_limit_config():
    """Test custom rate limit configuration."""
    config = RateLimitConfig(
        requests_per_minute=100,
        tokens_per_minute=150000,
        max_retries=5,
        retry_delay=0.5
    )
    client = DeepSeekClient(api_key="test_key", rate_limit_config=config)
    
    assert client.rate_limit_config.requests_per_minute == 100
    assert client.rate_limit_config.tokens_per_minute == 150000
    assert client.rate_limit_config.max_retries == 5
    assert client.rate_limit_config.retry_delay == 0.5