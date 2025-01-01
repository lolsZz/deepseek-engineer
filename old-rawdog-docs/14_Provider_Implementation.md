# Provider Implementation Guide

## Overview

When implementing a new LLM provider in RAWDOG, follow this standardized directory structure to ensure consistent integration with the system. Each provider should implement specific endpoints that map to standard OpenAI-compatible interfaces.

## Directory Structure

```
providers/
└── provider_name/
    ├── completion/       # OpenAI /v1/completions equivalent
    │   ├── handler.py
    │   └── transformation.py
    ├── chat/            # OpenAI /v1/chat/completions equivalent
    │   ├── handler.py
    │   └── transformation.py
    ├── embed/           # OpenAI /v1/embeddings equivalent
    │   ├── handler.py
    │   └── transformation.py
    ├── audio_transcription/  # OpenAI /v1/audio/transcriptions equivalent
    │   ├── handler.py
    │   └── transformation.py
    └── rerank/          # Cohere /rerank equivalent
        ├── handler.py
        └── transformation.py
```

## Implementation Guide

### 1. Handler Implementation

```python
# provider_name/chat/handler.py
from typing import Dict, Any
from ...base_handler import BaseHandler

class ChatHandler(BaseHandler):
    """
    Handler for chat completion requests.
    Maps to OpenAI's /v1/chat/completions endpoint.
    """
    
    def __init__(self):
        super().__init__()
        self.supports_streaming = True
        self.supports_function_calls = True
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process chat completion request
        """
        try:
            # Transform request to provider format
            provider_request = self.transform_request(request)
            
            # Make API call
            response = await self.make_api_call(provider_request)
            
            # Transform response to OpenAI format
            return self.transform_response(response)
            
        except Exception as e:
            self.handle_error(e)
```

### 2. Transformation Implementation

```python
# provider_name/chat/transformation.py
from typing import Dict, Any
from ...base_transformer import BaseTransformer

class ChatTransformer(BaseTransformer):
    """
    Handles request/response transformations for chat endpoint
    """
    
    def transform_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform OpenAI-format request to provider format
        """
        return {
            "messages": self._transform_messages(request["messages"]),
            "temperature": request.get("temperature", 0.7),
            "max_tokens": request.get("max_tokens", 100),
            # Add provider-specific parameters
        }
    
    def transform_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform provider response to OpenAI format
        """
        return {
            "id": response["id"],
            "object": "chat.completion",
            "created": response["timestamp"],
            "choices": self._transform_choices(response["output"]),
            "usage": self._transform_usage(response["usage"])
        }
```

## Endpoint Implementations

### 1. Chat Completion

```python
# Example chat completion implementation
class ChatCompletion:
    async def process(self, messages: list, **params):
        """
        Process chat completion request
        """
        request = {
            "messages": messages,
            **params
        }
        
        response = await self.api_call("/v1/chat/completions", request)
        return self.format_response(response)
```

### 2. Text Completion

```python
# Example text completion implementation
class TextCompletion:
    async def process(self, prompt: str, **params):
        """
        Process text completion request
        """
        request = {
            "prompt": prompt,
            **params
        }
        
        response = await self.api_call("/v1/completions", request)
        return self.format_response(response)
```

### 3. Embeddings

```python
# Example embeddings implementation
class Embeddings:
    async def process(self, input: list, **params):
        """
        Process embedding request
        """
        request = {
            "input": input,
            **params
        }
        
        response = await self.api_call("/v1/embeddings", request)
        return self.format_response(response)
```

## Error Handling

```python
class ProviderError(Exception):
    def __init__(self, message: str, code: str, status: int):
        self.message = message
        self.code = code
        self.status = status
        super().__init__(self.message)

class ErrorHandler:
    def handle_error(self, error: Exception) -> None:
        """
        Handle provider-specific errors
        """
        if isinstance(error, ProviderError):
            # Handle provider error
            self.handle_provider_error(error)
        else:
            # Handle general error
            self.handle_general_error(error)
```

## Testing

```python
# Example test implementation
import pytest

class TestProviderImplementation:
    @pytest.fixture
    def handler(self):
        return ChatHandler()
    
    async def test_chat_completion(self, handler):
        request = {
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
        
        response = await handler.handle_request(request)
        assert "choices" in response
        assert len(response["choices"]) > 0
```

## Best Practices

1. **Request Handling**
   - Validate all inputs
   - Transform requests accurately
   - Handle rate limits
   - Implement retries

2. **Response Processing**
   - Maintain OpenAI compatibility
   - Handle streaming properly
   - Process errors consistently
   - Track usage metrics

3. **Error Management**
   - Implement proper error mapping
   - Provide detailed error messages
   - Handle rate limits gracefully
   - Log errors appropriately

## Future Considerations

1. **Provider Updates**
   - Monitor API changes
   - Update transformations
   - Maintain compatibility
   - Add new features

2. **Performance**
   - Optimize transformations
   - Implement caching
   - Monitor latency
   - Track usage

3. **Features**
   - Add new endpoints
   - Enhance compatibility
   - Improve error handling
   - Extend functionality