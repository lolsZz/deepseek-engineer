# Logging and Monitoring Guide

## Overview

RAWDOG integrates with Langfuse for comprehensive LLM logging and monitoring. This enables teams to debug, analyze, and iterate on their LLM applications effectively.

## Langfuse Integration

### 1. Setup

```python
# server/src/logging/langfuse_setup.py
import os
import litellm
from litellm import completion

class LangfuseLogger:
    def __init__(self):
        # Set up Langfuse credentials
        os.environ["LANGFUSE_PUBLIC_KEY"] = "your-public-key"
        os.environ["LANGFUSE_SECRET_KEY"] = "your-secret-key"
        
        # Enable Langfuse callbacks
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
```

### 2. Basic Usage

```python
class LLMLogger:
    def __init__(self):
        self.logger = LangfuseLogger()
    
    async def log_completion(self, prompt: str, model: str):
        response = await completion(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            metadata={
                "generation_name": "rawdog-completion",
                "project": "rawdog-mcp"
            }
        )
        return response
```

## Advanced Logging Features

### 1. Trace Management

```python
class TraceManager:
    def __init__(self):
        self.current_trace_id = None
    
    async def start_trace(self, metadata: dict):
        response = await completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Starting trace"}],
            metadata={
                "trace_id": "trace-123",
                "trace_user_id": metadata.get("user_id"),
                "trace_metadata": metadata,
                "trace_version": "v1.0",
                "tags": ["rawdog", "mcp"]
            }
        )
        self.current_trace_id = "trace-123"
        return response
```

### 2. Session Tracking

```python
class SessionTracker:
    def __init__(self):
        self.session_id = None
    
    async def track_session(self, user_id: str):
        response = await completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Session start"}],
            metadata={
                "trace_user_id": user_id,
                "session_id": "session-123",
                "tags": ["session-start"]
            }
        )
        self.session_id = "session-123"
        return response
```

## Privacy and Data Protection

### 1. Content Redaction

```python
class ContentRedactor:
    @staticmethod
    def redact_message(message: dict):
        return completion(
            model="gpt-4",
            messages=[message],
            metadata={
                "mask_input": True,  # Redact input content
                "mask_output": True  # Redact output content
            }
        )
```

### 2. Selective Logging

```python
class SelectiveLogger:
    @staticmethod
    def log_with_filters(message: dict, log_level: str):
        if log_level == "none":
            return completion(
                messages=[message],
                model="gpt-4",
                **{"no-log": True}  # Disable logging for this call
            )
        return completion(messages=[message], model="gpt-4")
```

## Integration with MCP Servers

### 1. Server Logging

```typescript
// server/src/logging/mcp-logger.ts
class MCPServerLogger {
    private trace: any;
    
    constructor(serverName: string) {
        this.setupLogging(serverName);
    }
    
    private setupLogging(serverName: string) {
        // Configure logging for specific server
        const metadata = {
            generation_name: `${serverName}-gen`,
            trace_name: serverName,
            tags: ["mcp-server", serverName]
        };
        
        return metadata;
    }
    
    async logOperation(operation: string, input: any) {
        return await completion({
            model: "gpt-4",
            messages: [{ role: "user", content: input }],
            metadata: {
                ...this.metadata,
                operation_type: operation
            }
        });
    }
}
```

### 2. Provider-Specific Logging

```typescript
// server/src/logging/provider-logger.ts
class ProviderLogger {
    constructor(provider: string) {
        this.provider = provider;
    }
    
    async logModelUsage(model: string, tokens: number) {
        return await completion({
            model: "gpt-4",
            messages: [{
                role: "system",
                content: "Logging model usage"
            }],
            metadata: {
                provider: this.provider,
                model,
                tokens,
                timestamp: new Date().toISOString()
            }
        });
    }
}
```

## Monitoring and Analytics

### 1. Usage Tracking

```typescript
class UsageMonitor {
    private metrics: Map<string, number>;
    
    constructor() {
        this.metrics = new Map();
    }
    
    async trackUsage(provider: string, tokens: number) {
        this.metrics.set(
            provider, 
            (this.metrics.get(provider) || 0) + tokens
        );
        
        await this.logMetrics();
    }
    
    private async logMetrics() {
        return await completion({
            model: "gpt-4",
            messages: [{
                role: "system",
                content: "Logging metrics"
            }],
            metadata: {
                metrics: Object.fromEntries(this.metrics),
                timestamp: new Date().toISOString()
            }
        });
    }
}
```

### 2. Performance Monitoring

```typescript
class PerformanceMonitor {
    async trackLatency(operation: string, duration: number) {
        return await completion({
            model: "gpt-4",
            messages: [{
                role: "system",
                content: "Logging performance"
            }],
            metadata: {
                operation,
                duration,
                timestamp: new Date().toISOString()
            }
        });
    }
}
```

## Best Practices

1. **Logging Strategy**
   - Log appropriate detail level
   - Implement content redaction
   - Track relevant metadata
   - Monitor performance metrics

2. **Privacy Considerations**
   - Redact sensitive information
   - Implement data retention
   - Follow compliance requirements
   - Handle user consent

3. **Performance Impact**
   - Optimize logging calls
   - Implement batching
   - Handle failures gracefully
   - Monitor resource usage

## Future Considerations

1. **Enhanced Analytics**
   - Advanced metrics
   - Custom dashboards
   - Trend analysis
   - Cost optimization

2. **Integration Improvements**
   - Additional providers
   - Custom metrics
   - Real-time monitoring
   - Alert systems