# LiteLLM Integration Guide 🔄

## Overview

DeepSeek Engineer uses LiteLLM to provide a unified interface for multiple LLM providers. This allows for easy switching between different models and providers while maintaining consistent interfaces and functionality.

## Installation

```bash
# Core installation
pip install litellm

# For AWS Bedrock support
pip install boto3>=1.28.57
```

## Core Configuration

### 1. Basic Settings
```python
litellm_settings = {
    # Logging/Callback settings
    "success_callback": ["langfuse"],
    "failure_callback": ["sentry"],
    "callbacks": ["otel"],
    "service_callbacks": ["datadog", "prometheus"],
    
    # Networking settings
    "request_timeout": 10,  # timeout in seconds
    "force_ipv4": True,    # force IPv4 for all requests
    
    # Debug settings
    "set_verbose": False,  # verbose debug logs
    "json_logs": True      # format logs as JSON
}
```

## Provider Support

### 1. DeepSeek Models
```python
# Set API Key
os.environ['DEEPSEEK_API_KEY'] = "your-api-key"

# Chat Model
response = completion(
    model="deepseek/deepseek-chat",
    messages=[
        {"role": "user", "content": "Hello from DeepSeek!"}
    ]
)

# Coder Model
response = completion(
    model="deepseek/deepseek-coder",
    messages=[
        {"role": "user", "content": "Write a Python function"}
    ]
)

# Streaming Support
response = completion(
    model="deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)
for chunk in response:
    print(chunk)
```

### 2. Cerebras Models
```python
# Set API Key
os.environ['CEREBRAS_API_KEY'] = "your-api-key"

# Basic Usage
response = completion(
    model="cerebras/meta/llama3-70b-instruct",
    messages=[
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=10,
    response_format={"type": "json_object"},
    seed=123,
    temperature=0.2,
    top_p=0.9
)

# Streaming Support
response = completion(
    model="cerebras/meta/llama3-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
    max_tokens=10
)
for chunk in response:
    print(chunk)

# Function Calling
response = completion(
    model="cerebras/meta/llama3-70b-instruct",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tool_choice="auto",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }]
)
```

### 3. AWS Bedrock Models
```python
# Set AWS Credentials
os.environ["AWS_ACCESS_KEY_ID"] = "your-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your-secret"
os.environ["AWS_REGION_NAME"] = "your-region"

# Basic Usage
response = completion(
    model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Cross-Region Support
response = completion(
    model="bedrock/us.anthropic.claude-3-haiku-20240307-v1:0",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Vision Support
def encode_image(image_path):
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

response = completion(
    model="bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image('image.jpg')}"
                }
            }
        ]
    }]
)
```

## Proxy Server Configuration

### 1. Config File Setup
```yaml
# config.yaml
model_list:
  - model_name: my-deepseek
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: your-api-key

  - model_name: my-cerebras
    litellm_params:
      model: cerebras/meta/llama3-70b-instruct
      api_key: your-api-key

  - model_name: my-bedrock
    litellm_params:
      model: bedrock/anthropic.claude-3-sonnet-20240229-v1:0
      aws_access_key_id: your-key
      aws_secret_access_key: your-secret
      aws_region_name: your-region
```

### 2. Starting the Proxy
```bash
litellm --config /path/to/config.yaml
```

### 3. Client Usage
```python
import openai

client = openai.OpenAI(
    api_key="your-key",
    base_url="http://0.0.0.0:4000"
)

# DeepSeek request
response = client.chat.completions.create(
    model="my-deepseek",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Cerebras request
response = client.chat.completions.create(
    model="my-cerebras",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Bedrock request
response = client.chat.completions.create(
    model="my-bedrock",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Advanced Features

### 1. Caching
```python
cache_config = {
    "type": "redis",
    "host": "localhost",
    "port": 6379,
    "password": "your-password",
    "namespace": "litellm.cache"
}

# Enable caching
litellm.cache = True
litellm.cache_params = cache_config
```

### 2. Fallback Strategies
```python
fallback_config = {
    "default_fallbacks": ["claude-3"],
    "content_policy_fallbacks": [{
        "gpt-3.5": ["claude-3"]
    }],
    "context_window_fallbacks": [{
        "gpt-3.5": ["gpt-4", "claude-3"]
    }]
}
```

### 3. Monitoring
```python
class MetricsCollector:
    def setup_monitoring(self):
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["sentry"]
        litellm.callbacks = ["otel"]
        litellm.service_callbacks = ["datadog", "prometheus"]
```

## Best Practices

### 1. Error Handling
- Implement proper retry mechanisms
- Use appropriate fallback strategies
- Log errors comprehensively
- Monitor rate limits

### 2. Performance
- Enable streaming for long responses
- Implement proper timeout handling
- Use connection pooling
- Monitor response times

### 3. Security
- Secure API key management
- Implement proper redaction
- Monitor usage patterns
- Control access to models

## Future Considerations

1. **Enhanced Provider Support**
   - Additional model providers
   - New model versions
   - Custom provider implementations
   - Provider-specific optimizations

2. **Performance Improvements**
   - Response caching
   - Request batching
   - Connection pooling
   - Load balancing

3. **Security Enhancements**
   - Advanced key rotation
   - Usage quotas
   - Access control
   - Audit logging

4. **Monitoring Improvements**
   - Custom metrics
   - Performance tracking
   - Cost optimization
   - Usage analytics