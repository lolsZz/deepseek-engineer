# Advanced LLM Features with AWS Bedrock

## Overview

RAWDOG's MCP servers can leverage advanced AWS Bedrock features through litellm, including function calling, vision capabilities, streaming, and more. This document details how to implement these features in your MCP servers.

## Function Calling

### Implementation
```typescript
// server/src/function-calling.ts
import { completion } from 'litellm';

interface WeatherFunction {
    name: string;
    description: string;
    parameters: {
        type: string;
        properties: {
            location: {
                type: string;
                description: string;
            };
            unit: {
                type: string;
                enum: string[];
            };
        };
        required: string[];
    };
}

class FunctionCallingHandler {
    private tools: WeatherFunction[] = [{
        type: "function",
        function: {
            name: "get_current_weather",
            description: "Get the current weather in a given location",
            parameters: {
                type: "object",
                properties: {
                    location: {
                        type: "string",
                        description: "The city and state, e.g. San Francisco, CA",
                    },
                    unit: { type: "string", enum: ["celsius", "fahrenheit"] },
                },
                required: ["location"],
            },
        },
    }];

    async process(userQuery: string) {
        return await completion({
            model: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
            messages: [{ role: "user", content: userQuery }],
            tools: this.tools,
            tool_choice: "auto"
        });
    }
}
```

## Vision Capabilities

### Image Processing
```typescript
// server/src/vision-handler.ts
import { completion } from 'litellm';
import { encode_image } from './utils';

class VisionHandler {
    async analyzeImage(imagePath: string, query: string) {
        const base64Image = await encode_image(imagePath);
        
        return await completion({
            model: "bedrock/anthropic.claude-3-sonnet-20240229-v1:0",
            messages: [{
                role: "user",
                content: [
                    { type: "text", text: query },
                    {
                        type: "image_url",
                        image_url: {
                            url: `data:image/jpeg;base64,${base64Image}`
                        }
                    }
                ]
            }]
        });
    }
}
```

## Streaming Responses

### Implementation
```typescript
// server/src/streaming.ts
class StreamHandler {
    async streamResponse(prompt: string) {
        const response = await completion({
            model: "bedrock/anthropic.claude-instant-v1",
            messages: [{ content: prompt, role: "user" }],
            stream: true
        });

        for await (const chunk of response) {
            // Process streaming chunks
            console.log(chunk.choices[0].delta.content);
        }
    }
}
```

## PDF/Document Understanding

### Document Processing
```typescript
// server/src/document-handler.ts
import { supports_pdf_input } from 'litellm/utils';

class DocumentHandler {
    async analyzePDF(pdfUrl: string, query: string) {
        const model = "bedrock/anthropic.claude-3-sonnet-20240229-v1:0";
        
        if (!supports_pdf_input(model, null)) {
            throw new Error("Model does not support PDF input");
        }

        return await completion({
            model,
            messages: [{
                role: "user",
                content: [
                    { type: "text", text: query },
                    {
                        type: "image_url",
                        image_url: { url: pdfUrl }
                    }
                ]
            }]
        });
    }
}
```

## Advanced Configuration Options

### 1. Model-Specific Parameters
```typescript
interface ModelParams {
    temperature?: number;
    top_p?: number;
    top_k?: number;  // Provider-specific parameter
}

class AdvancedConfig {
    static getModelParams(taskType: string): ModelParams {
        switch (taskType) {
            case 'creative':
                return {
                    temperature: 0.8,
                    top_p: 0.95
                };
            case 'analytical':
                return {
                    temperature: 0.2,
                    top_p: 1.0
                };
            default:
                return {
                    temperature: 0.7,
                    top_p: 1.0
                };
        }
    }
}
```

### 2. System Messages
```typescript
class SystemMessageHandler {
    static getSystemPrompt(serverType: string): string {
        const prompts = {
            search: "You are a focused search assistant.",
            analysis: "You are a detailed analytical assistant.",
            creative: "You are a creative writing assistant."
        };
        
        return prompts[serverType] || "You are a helpful assistant.";
    }

    async processWithSystem(query: string, serverType: string) {
        return await completion({
            model: "bedrock/anthropic.claude-v2:1",
            messages: [
                { role: "system", content: this.getSystemPrompt(serverType) },
                { role: "user", content: query }
            ]
        });
    }
}
```

## Cross-Region Support

### Region Configuration
```typescript
class RegionHandler {
    private regions = {
        'us-east-1': 'bedrock/us.anthropic.claude-3-haiku-20240307-v1:0',
        'us-west-2': 'bedrock/us.anthropic.claude-3-sonnet-20240229-v1:0'
    };

    async routeRequest(query: string, region: string) {
        const model = this.regions[region];
        if (!model) {
            throw new Error(`Unsupported region: ${region}`);
        }

        return await completion({
            model,
            messages: [{ role: "user", content: query }],
            max_tokens: 10,
            temperature: 0.1
        });
    }
}
```

## Error Handling and Retries

### Robust Error Handler
```typescript
class ErrorHandler {
    private maxRetries = 3;
    private retryDelay = 1000; // ms

    async withRetry(operation: () => Promise<any>) {
        let lastError;
        
        for (let i = 0; i < this.maxRetries; i++) {
            try {
                return await operation();
            } catch (error) {
                lastError = error;
                if (this.isRetryable(error)) {
                    await this.delay(this.retryDelay * Math.pow(2, i));
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

    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

## Best Practices

1. **Model Selection**
   - Use appropriate models for specific tasks
   - Consider cost vs. capability tradeoffs
   - Implement fallback strategies

2. **Performance Optimization**
   - Implement caching where appropriate
   - Use streaming for long responses
   - Consider cross-region routing

3. **Error Handling**
   - Implement robust retry mechanisms
   - Handle rate limits gracefully
   - Log errors for debugging

4. **Security**
   - Validate all inputs
   - Implement proper access controls
   - Handle credentials securely

## Future Considerations

1. **Enhanced Capabilities**
   - Support for new model versions
   - Additional vision features
   - Improved document processing

2. **Performance Improvements**
   - Better caching strategies
   - Optimized streaming
   - Enhanced error recovery

3. **Integration Enhancements**
   - Support for new AWS services
   - Additional model providers
   - Enhanced monitoring tools