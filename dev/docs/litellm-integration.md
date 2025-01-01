# LiteLLM Integration Guide 🔄

## Overview

DeepSeek Engineer uses LiteLLM to provide a unified interface for multiple LLM providers. This allows for easy switching between different models and providers while maintaining consistent interfaces and functionality.

## Installation

```bash
pip install litellm
```

## Core Integration

### 1. LiteLLM Client Setup
```python
from litellm import completion

class LiteLLMClient:
    def __init__(self, config: dict):
        self.config = {
            "model": config.get("model", "deepseek-chat"),
            "api_key": config.get("api_key"),
            "base_url": config.get("base_url", "https://api.deepseek.com"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 4000)
        }

    async def complete(self, messages: list) -> dict:
        try:
            response = await completion(
                model=self.config["model"],
                messages=messages,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                api_key=self.config["api_key"],
                api_base=self.config["base_url"]
            )
            return response
        except Exception as e:
            raise self._handle_error(e)

    def _handle_error(self, error: Exception) -> Exception:
        # Error handling implementation
        pass
```

### 2. Model Configuration
```python
class ModelConfig:
    PROVIDER_CONFIGS = {
        "deepseek": {
            "chat": {
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com"
            },
            "code": {
                "model": "deepseek-coder",
                "base_url": "https://api.deepseek.com"
            }
        },
        "anthropic": {
            "chat": {
                "model": "claude-3-opus-20240229",
                "base_url": "https://api.anthropic.com"
            }
        },
        "openai": {
            "chat": {
                "model": "gpt-4-turbo-preview",
                "base_url": "https://api.openai.com/v1"
            }
        }
    }

    @classmethod
    def get_config(cls, provider: str, type: str = "chat") -> dict:
        if provider not in cls.PROVIDER_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}")
        if type not in cls.PROVIDER_CONFIGS[provider]:
            raise ValueError(f"Unsupported type for provider {provider}: {type}")
        return cls.PROVIDER_CONFIGS[provider][type]
```

## Provider Integration

### 1. DeepSeek Integration
```python
class DeepSeekProvider:
    def __init__(self, api_key: str):
        self.client = LiteLLMClient({
            **ModelConfig.get_config("deepseek"),
            "api_key": api_key
        })

    async def chat_completion(self, messages: list) -> dict:
        return await self.client.complete(messages)

    async def code_completion(self, messages: list) -> dict:
        code_client = LiteLLMClient({
            **ModelConfig.get_config("deepseek", "code"),
            "api_key": self.api_key
        })
        return await code_client.complete(messages)
```

### 2. Alternative Provider Support
```python
class ProviderFactory:
    @staticmethod
    def create_provider(provider: str, api_key: str) -> Any:
        providers = {
            "deepseek": DeepSeekProvider,
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider
        }
        if provider not in providers:
            raise ValueError(f"Unsupported provider: {provider}")
        return providers[provider](api_key)
```

## Advanced Features

### 1. Streaming Support
```python
class StreamingLLMClient:
    async def stream_complete(self, messages: list):
        try:
            stream = await completion(
                model=self.config["model"],
                messages=messages,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"],
                api_key=self.config["api_key"],
                api_base=self.config["base_url"],
                stream=True
            )

            async for chunk in stream:
                yield chunk
        except Exception as e:
            raise self._handle_error(e)
```

### 2. Function Calling
```python
class FunctionCallingClient:
    async def complete_with_functions(self, messages: list, functions: list):
        try:
            response = await completion(
                model=self.config["model"],
                messages=messages,
                functions=functions,
                function_call="auto",
                **self.config
            )
            return response
        except Exception as e:
            raise self._handle_error(e)
```

### 3. Vision Support
```python
class VisionClient:
    async def analyze_image(self, image_data: str, prompt: str):
        try:
            response = await completion(
                model=self.config["model"],
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }],
                **self.config
            )
            return response
        except Exception as e:
            raise self._handle_error(e)
```

## Error Handling

### 1. Provider-Specific Errors
```python
class LLMError(Exception):
    def __init__(self, provider: str, message: str, code: str = None):
        self.provider = provider
        self.code = code
        super().__init__(f"{provider} error: {message}")

class ErrorHandler:
    @staticmethod
    def handle_provider_error(provider: str, error: Exception) -> LLMError:
        error_mappings = {
            "deepseek": {
                "InvalidRequestError": "invalid_request",
                "AuthenticationError": "auth_error",
                "RateLimitError": "rate_limit"
            }
        }
        
        provider_mappings = error_mappings.get(provider, {})
        error_code = provider_mappings.get(error.__class__.__name__, "unknown_error")
        
        return LLMError(provider, str(error), error_code)
```

## Configuration Management

### 1. Environment Setup
```python
# .env
DEEPSEEK_API_KEY=your-deepseek-key
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
```

### 2. Provider Configuration
```python
class ProviderConfig:
    def __init__(self):
        self.configs = {}
        self._load_configs()

    def _load_configs(self):
        self.configs = {
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            }
        }
```

## Best Practices

### 1. Provider Selection
- Choose appropriate providers for specific tasks
- Implement fallback strategies
- Consider cost and performance tradeoffs
- Monitor provider status

### 2. Error Management
- Implement proper retry logic
- Handle rate limits gracefully
- Log provider-specific errors
- Maintain error consistency

### 3. Performance
- Use streaming for long responses
- Implement response caching
- Monitor token usage
- Handle timeouts appropriately

### 4. Security
- Secure API key management
- Validate provider responses
- Implement rate limiting
- Monitor usage patterns

## Future Considerations

1. **Enhanced Provider Support**
   - Additional LLM providers
   - New model versions
   - Custom provider implementations
   - Provider-specific optimizations

2. **Feature Extensions**
   - Advanced function calling
   - Enhanced streaming
   - Improved error handling
   - Better monitoring

3. **Performance Improvements**
   - Response caching
   - Request batching
   - Connection pooling
   - Load balancing

4. **Security Enhancements**
   - API key rotation
   - Usage monitoring
   - Access control
   - Audit logging