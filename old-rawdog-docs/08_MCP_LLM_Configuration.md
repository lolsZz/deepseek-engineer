# MCP Server LLM Configuration with AWS Bedrock

## Overview

RAWDOG uses litellm for LLM integration, which enables configuring different AWS Bedrock models for different MCP servers. This allows for optimizing token usage by matching the model capability to the server's needs.

## AWS Bedrock Integration

### 1. Prerequisites
```bash
# Install required dependency for AWS Bedrock
pip install boto3>=1.28.57
```

### 2. Core Configuration
```yaml
# ~/.rawdog/config.yaml
llm_api_key: null  # Not needed for AWS Bedrock
llm_base_url: null
llm_model: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
llm_custom_provider: "bedrock"
llm_temperature: 1.0

# AWS Credentials
aws_access_key_id: "your-access-key"
aws_secret_access_key: "your-secret-key"
aws_region_name: "your-region"
```

### 3. MCP Server Configuration
```yaml
# ~/.rawdog/config.yaml
mcpServers:
  search-server:
    command: "node"
    args: ["path/to/server.js"]
    env:
      AWS_ACCESS_KEY_ID: "${aws_access_key_id}"
      AWS_SECRET_ACCESS_KEY: "${aws_secret_access_key}"
      AWS_REGION_NAME: "${aws_region_name}"
      LLM_MODEL: "bedrock/anthropic.claude-instant-v1"
      LLM_TEMPERATURE: "0.7"
  
  analysis-server:
    command: "node"
    args: ["path/to/server.js"]
    env:
      AWS_ACCESS_KEY_ID: "${aws_access_key_id}"
      AWS_SECRET_ACCESS_KEY: "${aws_secret_access_key}"
      AWS_REGION_NAME: "${aws_region_name}"
      LLM_MODEL: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
      LLM_TEMPERATURE: "0.2"
```

## Implementation Guide

### 1. Server-Specific LLM Client

```typescript
// server/src/llm-client.ts
import { completion } from 'litellm';

class LLMClient {
    private config: {
        model: string;
        temperature: number;
        aws_access_key_id: string;
        aws_secret_access_key: string;
        aws_region_name: string;
    };

    constructor() {
        this.config = {
            model: process.env.LLM_MODEL || 'bedrock/anthropic.claude-instant-v1',
            temperature: parseFloat(process.env.LLM_TEMPERATURE || '0.7'),
            aws_access_key_id: process.env.AWS_ACCESS_KEY_ID,
            aws_secret_access_key: process.env.AWS_SECRET_ACCESS_KEY,
            aws_region_name: process.env.AWS_REGION_NAME
        };
    }

    async complete(messages: any[]) {
        return await completion({
            model: this.config.model,
            messages,
            temperature: this.config.temperature,
            aws_access_key_id: this.config.aws_access_key_id,
            aws_secret_access_key: this.config.aws_secret_access_key,
            aws_region_name: this.config.aws_region_name
        });
    }
}
```

## Model Selection Guidelines

### 1. Available AWS Bedrock Models

| Model | Best For | Use Case |
|-------|----------|-----------|
| anthropic.claude-instant-v1 | Quick responses, basic tasks | Search, classification |
| anthropic.claude-3-sonnet | Complex reasoning, analysis | Detailed analysis, code generation |
| anthropic.claude-3-haiku | Efficient, balanced performance | General purpose tasks |

### 2. Server-Specific Model Selection

```typescript
// server/src/model-selector.ts
class ModelSelector {
    static getModelForTask(taskType: string): string {
        switch (taskType) {
            case 'search':
                return 'bedrock/anthropic.claude-instant-v1';
            case 'analysis':
                return 'bedrock/anthropic.claude-3-sonnet-20240229-v1:0';
            default:
                return process.env.LLM_MODEL;
        }
    }
}
```

## Authentication Options

AWS Bedrock supports multiple authentication methods through boto3:

```typescript
interface AWSAuth {
    // Required for direct API key authentication
    aws_access_key_id?: string;
    aws_secret_access_key?: string;
    aws_region_name?: string;

    // Optional additional authentication methods
    aws_session_token?: string;
    aws_session_name?: string;
    aws_profile_name?: string;
    aws_role_name?: string;
    aws_web_identity_token?: string;
}
```

## Configuration Examples

### 1. Basic Search Server
```yaml
search-server:
  command: "node"
  args: ["servers/search/build/index.js"]
  env:
    AWS_ACCESS_KEY_ID: "${aws_access_key_id}"
    AWS_SECRET_ACCESS_KEY: "${aws_secret_access_key}"
    AWS_REGION_NAME: "${aws_region_name}"
    LLM_MODEL: "bedrock/anthropic.claude-instant-v1"
    LLM_TEMPERATURE: "0.7"
```

### 2. Advanced Analysis Server
```yaml
analysis-server:
  command: "node"
  args: ["servers/analysis/build/index.js"]
  env:
    AWS_ACCESS_KEY_ID: "${aws_access_key_id}"
    AWS_SECRET_ACCESS_KEY: "${aws_secret_access_key}"
    AWS_REGION_NAME: "${aws_region_name}"
    LLM_MODEL: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
    LLM_TEMPERATURE: "0.2"
```

## Error Handling

```typescript
class BedrockErrorHandler {
    async withRetry(operation: () => Promise<any>): Promise<any> {
        const maxRetries = 3;
        let lastError;

        for (let i = 0; i < maxRetries; i++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error;
                if (this.isRetryable(error)) {
                    await this.wait(Math.pow(2, i) * 1000);
                    continue;
                }
                throw error;
            }
        }
        throw lastError;
    }

    private isRetryable(error: any): boolean {
        return [
            'ThrottlingException',
            'RequestLimitExceeded',
            'ServiceUnavailable'
        ].includes(error.code);
    }

    private wait(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

## Monitoring and Logging

```typescript
class BedrockMonitor {
    logRequest(model: string, tokens: number) {
        const entry = {
            timestamp: new Date().toISOString(),
            model,
            tokens,
            service: 'bedrock',
            region: process.env.AWS_REGION_NAME
        };
        
        // Log to RAWDOG's logging system
        appendToLog('bedrock-usage.log', JSON.stringify(entry));
    }
}
```

## Best Practices

1. **Authentication**
   - Use environment variables for AWS credentials
   - Implement proper credential rotation
   - Use minimum required permissions

2. **Model Selection**
   - Use claude-instant for simple tasks
   - Reserve claude-3-sonnet for complex analysis
   - Consider cost vs. performance tradeoffs

3. **Error Handling**
   - Implement proper retries
   - Handle rate limits gracefully
   - Log errors for debugging

4. **Monitoring**
   - Track usage and costs
   - Monitor performance
   - Set up alerts for issues

## Future Considerations

1. **Model Updates**
   - Stay updated with new Bedrock models
   - Test performance improvements
   - Update model selection strategies

2. **Cost Optimization**
   - Implement caching where appropriate
   - Batch similar requests
   - Monitor and optimize token usage

3. **Integration Improvements**
   - Support for more AWS services
   - Enhanced error handling
   - Better monitoring tools