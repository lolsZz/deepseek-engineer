# Model Configuration Guide

## Overview

RAWDOG's MCP servers can leverage detailed model configurations through litellm. Each provider (AWS Bedrock, Jina AI, Deepseek) has specific configuration parameters that can be customized for optimal performance.

## Provider-Specific Configurations

### 1. Amazon Titan Configuration

```python
class TitanConfig:
    """
    Configuration for Amazon Titan models.
    
    Parameters:
    - maxTokenCount (int): Maximum tokens to generate
    - stopSequences (list): List of stop sequence strings
    - temperature (float): Temperature for sampling
    - topP (int): Top P for nucleus sampling
    """
    def __init__(self):
        self.maxTokenCount = None
        self.stopSequences = None
        self.temperature = None
        self.topP = None
```

### 2. Anthropic Configuration

```python
class AnthropicConfig:
    """
    Configuration for Anthropic Claude models.
    
    Parameters:
    - max_tokens_to_sample (int): Maximum tokens to generate
    - temperature (float): Model temperature
    - top_k (int): Top K for sampling
    - top_p (int): Top P for sampling
    - stop_sequences (list): List of stop sequences
    - anthropic_version (str): Anthropic API version
    """
    def __init__(self):
        self.max_tokens_to_sample = None
        self.temperature = None
        self.top_k = None
        self.top_p = None
        self.stop_sequences = None
        self.anthropic_version = None
```

### 3. Cohere Configuration

```python
class CohereConfig:
    """
    Configuration for Cohere models.
    
    Parameters:
    - max_tokens (int): Maximum tokens to generate
    - temperature (float): Model temperature
    - return_likelihood (str): Likelihood return option
    """
    def __init__(self):
        self.max_tokens = None
        self.temperature = None
        self.return_likelihood = None
```

## Implementation

### 1. Configuration Manager

```typescript
// server/src/config/model-config.ts
interface ModelConfig {
    provider: string;
    parameters: Record<string, any>;
}

class ConfigurationManager {
    private configs: Map<string, ModelConfig>;

    constructor() {
        this.configs = new Map();
        this.initializeConfigs();
    }

    private initializeConfigs() {
        // Amazon Titan
        this.configs.set('amazon.titan', {
            provider: 'amazon',
            parameters: {
                maxTokenCount: 4096,
                temperature: 0.7,
                topP: 0.9
            }
        });

        // Anthropic Claude
        this.configs.set('anthropic.claude', {
            provider: 'anthropic',
            parameters: {
                max_tokens_to_sample: 4096,
                temperature: 0.7,
                top_p: 0.9,
                anthropic_version: 'bedrock-2023-05-31'
            }
        });
    }

    getConfig(model: string): ModelConfig {
        return this.configs.get(model);
    }
}
```

### 2. Parameter Validation

```typescript
// server/src/config/parameter-validator.ts
class ParameterValidator {
    static validateTitanParams(params: any) {
        if (params.maxTokenCount && 
            (params.maxTokenCount < 1 || params.maxTokenCount > 8192)) {
            throw new Error('maxTokenCount must be between 1 and 8192');
        }

        if (params.temperature && 
            (params.temperature < 0 || params.temperature > 1)) {
            throw new Error('temperature must be between 0 and 1');
        }
    }

    static validateAnthropicParams(params: any) {
        if (params.max_tokens_to_sample && 
            (params.max_tokens_to_sample < 1 || 
             params.max_tokens_to_sample > 4096)) {
            throw new Error('max_tokens_to_sample must be between 1 and 4096');
        }
    }
}
```

### 3. Request Builder

```typescript
// server/src/config/request-builder.ts
class RequestBuilder {
    static buildTitanRequest(prompt: string, config: any) {
        return {
            inputText: prompt,
            textGenerationConfig: {
                maxTokenCount: config.maxTokenCount,
                temperature: config.temperature,
                topP: config.topP
            }
        };
    }

    static buildAnthropicRequest(prompt: string, config: any) {
        return {
            prompt: prompt,
            max_tokens_to_sample: config.max_tokens_to_sample,
            temperature: config.temperature,
            top_p: config.top_p,
            stop_sequences: config.stop_sequences
        };
    }
}
```

## Usage Examples

### 1. Basic Configuration

```typescript
// Example of configuring a model
const config = new ConfigurationManager();
const titanConfig = config.getConfig('amazon.titan');

const response = await completion({
    model: 'amazon.titan',
    messages: [{ role: 'user', content: prompt }],
    ...titanConfig.parameters
});
```

### 2. Dynamic Configuration

```typescript
// Dynamically adjust configuration based on task
class TaskOptimizer {
    static getOptimalConfig(task: string, baseConfig: any) {
        switch (task) {
            case 'creative':
                return {
                    ...baseConfig,
                    temperature: 0.9,
                    top_p: 0.95
                };
            case 'analytical':
                return {
                    ...baseConfig,
                    temperature: 0.2,
                    top_p: 0.8
                };
            default:
                return baseConfig;
        }
    }
}
```

## Best Practices

### 1. Parameter Selection

```typescript
class ParameterSelector {
    static getParameters(task: string, model: string) {
        const baseParams = {
            temperature: 0.7,
            top_p: 0.9
        };

        switch (task) {
            case 'code_generation':
                return {
                    ...baseParams,
                    temperature: 0.2,
                    stop_sequences: ['\n\n']
                };
            case 'creative_writing':
                return {
                    ...baseParams,
                    temperature: 0.9
                };
            default:
                return baseParams;
        }
    }
}
```

### 2. Error Handling

```typescript
class ConfigurationError extends Error {
    constructor(message: string, public parameter: string) {
        super(message);
        this.name = 'ConfigurationError';
    }
}

class ErrorHandler {
    static validateConfiguration(config: any) {
        if (config.temperature < 0 || config.temperature > 1) {
            throw new ConfigurationError(
                'Temperature must be between 0 and 1',
                'temperature'
            );
        }
    }
}
```

### 3. Monitoring

```typescript
class ConfigurationMonitor {
    static logConfiguration(config: any, result: any) {
        const metrics = {
            timestamp: new Date().toISOString(),
            model: config.model,
            parameters: config,
            success: result.success,
            latency: result.latency
        };
        
        // Log to monitoring system
    }
}
```

## Future Considerations

1. **Enhanced Configuration**
   - Dynamic parameter adjustment
   - A/B testing support
   - Performance tracking

2. **Provider Updates**
   - New model support
   - Parameter validation
   - Version management

3. **Optimization**
   - Parameter tuning
   - Cost optimization
   - Performance metrics