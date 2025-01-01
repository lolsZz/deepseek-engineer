# MCP Best Practices Guide 🎯

## Core Principles

### 1. Tool Design Principles

#### Clear and Focused Tools
```typescript
// Good
{
    name: "fetch_weather",
    description: "Get weather for a specific location",
    inputSchema: {
        type: "object",
        properties: {
            location: { type: "string" },
            units: { type: "string", enum: ["metric", "imperial"] }
        },
        required: ["location"]
    }
}

// Avoid
{
    name: "weather_tool",
    description: "Weather related operations",
    inputSchema: {
        type: "object",
        properties: {
            action: { type: "string" },
            data: { type: "object" }
        }
    }
}
```

#### Consistent Response Format
```typescript
interface ToolResponse {
    content: Array<{
        type: string;  // "text", "json", "error"
        text: string;
    }>;
    isError?: boolean;
}

// Example implementation
function createResponse(result: any): ToolResponse {
    return {
        content: [{
            type: "text",
            text: JSON.stringify(result)
        }]
    };
}
```

### 2. Resource Management

#### Resource Lifecycle
```typescript
class ResourceManager {
    private resources: Map<string, any>;

    async initialize(): Promise<void> {
        // Setup resources
    }

    async cleanup(): Promise<void> {
        // Cleanup resources
        for (const [_, resource] of this.resources) {
            await resource.close();
        }
    }

    async validateAccess(uri: string): Promise<boolean> {
        // Validate resource access
        return true;
    }
}
```

#### Caching Implementation
```typescript
class CacheManager {
    private cache: Map<string, {
        value: any;
        timestamp: number;
        ttl: number;
    }>;

    async get(key: string): Promise<any> {
        const entry = this.cache.get(key);
        if (!entry) return null;

        if (Date.now() - entry.timestamp > entry.ttl) {
            this.cache.delete(key);
            return null;
        }

        return entry.value;
    }

    async set(key: string, value: any, ttl: number = 300000): Promise<void> {
        this.cache.set(key, {
            value,
            timestamp: Date.now(),
            ttl
        });
    }
}
```

### 3. Error Handling

#### Error Types
```typescript
enum ErrorCode {
    InvalidRequest = "INVALID_REQUEST",
    InternalError = "INTERNAL_ERROR",
    ExternalServiceError = "EXTERNAL_SERVICE_ERROR",
    ResourceNotFound = "RESOURCE_NOT_FOUND",
    Unauthorized = "UNAUTHORIZED"
}

class McpError extends Error {
    constructor(
        public code: ErrorCode,
        message: string
    ) {
        super(message);
    }
}
```

#### Error Handling Pattern
```typescript
async function handleToolExecution(params: any): Promise<ToolResponse> {
    try {
        // Validate input
        validateInput(params);

        // Execute operation
        const result = await executeOperation(params);

        return createResponse(result);
    } catch (error) {
        if (error instanceof McpError) {
            throw error;
        }

        throw new McpError(
            ErrorCode.InternalError,
            `Operation failed: ${error.message}`
        );
    }
}
```

### 4. Security Implementation

#### Input Validation
```typescript
function validateInput(input: any, schema: JSONSchema): void {
    const validator = new JSONSchemaValidator();
    if (!validator.validate(input, schema)) {
        throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid input: ${validator.errors.join(", ")}`
        );
    }
}
```

#### Access Control
```typescript
class AccessManager {
    validateToken(token: string): boolean {
        // Validate token
        return true;
    }

    checkPermission(resource: string, action: string): boolean {
        // Check permissions
        return true;
    }

    auditAccess(resource: string, action: string): void {
        // Log access
        console.log(`Access: ${action} on ${resource}`);
    }
}
```

## Implementation Patterns

### 1. Server Setup
```typescript
class CustomMcpServer {
    private server: Server;
    private resources: ResourceManager;
    private cache: CacheManager;
    private access: AccessManager;

    constructor() {
        this.server = new Server({
            name: "custom-server",
            version: "1.0.0"
        });

        this.resources = new ResourceManager();
        this.cache = new CacheManager();
        this.access = new AccessManager();

        this.setupHandlers();
    }

    private setupHandlers(): void {
        this.setupToolHandlers();
        this.setupResourceHandlers();
    }
}
```

### 2. Tool Implementation
```typescript
class Tool {
    constructor(
        private name: string,
        private handler: (params: any) => Promise<any>
    ) {}

    async execute(params: any): Promise<ToolResponse> {
        try {
            const result = await this.handler(params);
            return createResponse(result);
        } catch (error) {
            throw new McpError(
                ErrorCode.InternalError,
                `Tool execution failed: ${error.message}`
            );
        }
    }
}
```

### 3. Resource Implementation
```typescript
class Resource {
    constructor(
        private uri: string,
        private fetcher: () => Promise<any>
    ) {}

    async fetch(): Promise<any> {
        try {
            return await this.fetcher();
        } catch (error) {
            throw new McpError(
                ErrorCode.ResourceNotFound,
                `Resource fetch failed: ${error.message}`
            );
        }
    }
}
```

## Best Practices Checklist

### 1. Tool Design
- [ ] Use clear, descriptive names
- [ ] Implement comprehensive input validation
- [ ] Return structured responses
- [ ] Handle errors gracefully
- [ ] Document usage and parameters

### 2. Resource Management
- [ ] Implement proper resource lifecycle
- [ ] Use caching where appropriate
- [ ] Handle concurrent access
- [ ] Cleanup resources properly
- [ ] Validate resource access

### 3. Error Handling
- [ ] Use appropriate error codes
- [ ] Provide detailed error messages
- [ ] Implement proper cleanup on errors
- [ ] Log errors for debugging
- [ ] Handle timeouts gracefully

### 4. Security
- [ ] Validate all inputs
- [ ] Implement access control
- [ ] Handle sensitive data properly
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting

### 5. Performance
- [ ] Use caching effectively
- [ ] Implement connection pooling
- [ ] Handle concurrent requests
- [ ] Monitor resource usage
- [ ] Optimize response times

### 6. Monitoring
- [ ] Implement logging
- [ ] Track metrics
- [ ] Set up health checks
- [ ] Monitor error rates
- [ ] Track resource usage

## Testing Guidelines

### 1. Unit Testing
```typescript
describe('Tool', () => {
    it('should validate input', () => {
        const tool = new Tool('test', async () => {});
        expect(() => tool.execute({})).to.throw(McpError);
    });
});
```

### 2. Integration Testing
```typescript
describe('Server', () => {
    it('should handle tool requests', async () => {
        const server = new CustomMcpServer();
        const response = await server.handleRequest({
            type: 'tool',
            name: 'test',
            params: {}
        });
        expect(response).to.exist;
    });
});
```

## Future Considerations

1. **Enhanced Security**
   - OAuth integration
   - Request signing
   - Advanced rate limiting
   - Audit logging

2. **Performance Optimization**
   - Response caching
   - Connection pooling
   - Request batching
   - Load balancing

3. **Monitoring Improvements**
   - Detailed metrics
   - Performance tracking
   - Error analysis
   - Usage analytics

4. **Feature Extensions**
   - Streaming support
   - Binary data handling
   - Batch operations
   - Plugin system