# MCP Best Practices Guide 🎯

## Core Principles

### 1. Language Selection

#### TypeScript/JavaScript
Best suited for:
- Web API integrations
- Real-time data processing
- Event-driven servers
- Browser automation

```typescript
// Example: Brave Search Server
class BraveSearchServer extends Server {
    private api: AxiosInstance;

    constructor() {
        super({
            name: "brave-search",
            version: "1.0.0"
        });
        
        this.api = axios.create({
            baseURL: "https://api.search.brave.com/",
            headers: {
                "X-Subscription-Token": process.env.BRAVE_API_KEY
            }
        });
    }
}
```

#### Python
Best suited for:
- Data processing
- Machine learning integration
- System operations
- Database operations

```python
# Example: Git Server
class GitServer:
    def __init__(self):
        self.server = Server(
            name="git-server",
            version="1.0.0"
        )
        
    async def execute_git_command(self, command: List[str]) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                "git", *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return stdout.decode()
        except Exception as e:
            raise McpError("INTERNAL_ERROR", f"Git command failed: {str(e)}")
```

### 2. Tool Design Principles

#### Clear and Focused Tools
```typescript
// Good
{
    name: "search_web",
    description: "Search the web using Brave Search API",
    inputSchema: {
        type: "object",
        properties: {
            query: { type: "string" },
            country: { type: "string", pattern: "^[A-Z]{2}$" },
            language: { type: "string", pattern: "^[a-z]{2}$" }
        },
        required: ["query"]
    }
}

// Avoid
{
    name: "search",
    description: "General search operations",
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
            type: typeof result === 'object' ? 'json' : 'text',
            text: typeof result === 'object' ? JSON.stringify(result) : String(result)
        }]
    };
}
```

### 3. Resource Management

#### Resource Lifecycle
```typescript
class ResourceManager {
    private resources: Map<string, any>;
    private cleanupHandlers: Map<string, () => Promise<void>>;

    async initialize(): Promise<void> {
        // Setup resources
    }

    async cleanup(): Promise<void> {
        for (const [id, handler] of this.cleanupHandlers) {
            try {
                await handler();
            } catch (error) {
                console.error(`Cleanup failed for ${id}:`, error);
            }
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

### 4. Error Handling

#### Error Types
```typescript
enum ErrorCode {
    InvalidRequest = "INVALID_REQUEST",
    InternalError = "INTERNAL_ERROR",
    ExternalServiceError = "EXTERNAL_SERVICE_ERROR",
    ResourceNotFound = "RESOURCE_NOT_FOUND",
    Unauthorized = "UNAUTHORIZED",
    RateLimitExceeded = "RATE_LIMIT_EXCEEDED"
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

### 5. Security Implementation

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
    private rateLimiter: RateLimiter;

    constructor() {
        this.rateLimiter = new RateLimiter();
    }

    validateToken(token: string): boolean {
        // Validate token
        return true;
    }

    checkPermission(resource: string, action: string): boolean {
        // Check permissions
        return true;
    }

    checkRateLimit(key: string): boolean {
        return this.rateLimiter.checkLimit(key, 100, 60000); // 100 requests per minute
    }

    auditAccess(resource: string, action: string): void {
        // Log access
        console.log(`Access: ${action} on ${resource}`);
    }
}
```

## Implementation Patterns

### 1. API Integration Pattern
```typescript
class ApiIntegrationServer extends CustomMcpServer {
    private api: AxiosInstance;
    private cache: CacheManager;
    private rateLimiter: RateLimiter;

    constructor() {
        super();
        this.setupApi();
        this.cache = new CacheManager();
        this.rateLimiter = new RateLimiter();
    }

    private setupApi() {
        this.api = axios.create({
            baseURL: process.env.API_BASE_URL,
            headers: {
                Authorization: `Bearer ${process.env.API_KEY}`
            }
        });

        // Add response caching
        this.api.interceptors.response.use(async (response) => {
            const cacheKey = this.getCacheKey(response.config);
            await this.cache.set(cacheKey, response.data);
            return response;
        });
    }

    protected async makeApiCall(endpoint: string, params: any): Promise<any> {
        const cacheKey = this.getCacheKey({ url: endpoint, params });
        const cachedData = await this.cache.get(cacheKey);
        if (cachedData) return cachedData;

        if (!this.rateLimiter.checkLimit(endpoint, 60, 60000)) {
            throw new McpError(ErrorCode.RateLimitExceeded, "Rate limit exceeded");
        }

        try {
            const response = await this.api.get(endpoint, { params });
            return response.data;
        } catch (error) {
            throw new McpError(
                ErrorCode.ExternalServiceError,
                `API call failed: ${error.message}`
            );
        }
    }
}
```

### 2. Database Integration Pattern
```typescript
class DatabaseServer extends CustomMcpServer {
    private pool: Pool;
    private queryCache: CacheManager;

    constructor() {
        super();
        this.setupDatabase();
        this.queryCache = new CacheManager();
    }

    private async setupDatabase() {
        this.pool = new Pool({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME,
            max: 20,
            idleTimeoutMillis: 30000
        });
    }

    protected async query(sql: string, params: any[]): Promise<any> {
        const cacheKey = this.getQueryCacheKey(sql, params);
        const cachedResult = await this.queryCache.get(cacheKey);
        if (cachedResult) return cachedResult;

        const client = await this.pool.connect();
        try {
            const result = await client.query(sql, params);
            await this.queryCache.set(cacheKey, result.rows);
            return result.rows;
        } finally {
            client.release();
        }
    }
}
```

## Best Practices Checklist

### 1. Server Implementation
- [ ] Choose appropriate language (TypeScript/Python) based on use case
- [ ] Implement proper initialization and cleanup
- [ ] Use dependency injection for better testability
- [ ] Follow single responsibility principle
- [ ] Implement proper logging and monitoring

### 2. Tool Design
- [ ] Use clear, descriptive names
- [ ] Implement comprehensive input validation
- [ ] Return structured responses
- [ ] Handle errors gracefully
- [ ] Document usage and parameters

### 3. Resource Management
- [ ] Implement proper resource lifecycle
- [ ] Use caching where appropriate
- [ ] Handle concurrent access
- [ ] Cleanup resources properly
- [ ] Validate resource access

### 4. Error Handling
- [ ] Use appropriate error codes
- [ ] Provide detailed error messages
- [ ] Implement proper cleanup on errors
- [ ] Log errors for debugging
- [ ] Handle timeouts gracefully

### 5. Security
- [ ] Validate all inputs
- [ ] Implement access control
- [ ] Handle sensitive data properly
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting

### 6. Performance
- [ ] Use caching effectively
- [ ] Implement connection pooling
- [ ] Handle concurrent requests
- [ ] Monitor resource usage
- [ ] Optimize response times

### 7. Testing
- [ ] Write comprehensive unit tests
- [ ] Implement integration tests
- [ ] Test error scenarios
- [ ] Test performance under load
- [ ] Test security measures

## Testing Guidelines

### 1. Unit Testing
```typescript
describe('Tool', () => {
    let tool: Tool;
    let mockApi: jest.Mock;

    beforeEach(() => {
        mockApi = jest.fn();
        tool = new Tool('test', mockApi);
    });

    it('should validate input', async () => {
        await expect(tool.execute({})).rejects.toThrow(McpError);
    });

    it('should handle successful execution', async () => {
        mockApi.mockResolvedValue({ data: 'test' });
        const result = await tool.execute({ param: 'test' });
        expect(result.content[0].text).toBe('{"data":"test"}');
    });
});
```

### 2. Integration Testing
```typescript
describe('Server', () => {
    let server: CustomMcpServer;
    let mockDb: jest.Mock;

    beforeEach(async () => {
        mockDb = jest.fn();
        server = new CustomMcpServer(mockDb);
        await server.initialize();
    });

    afterEach(async () => {
        await server.cleanup();
    });

    it('should handle database queries', async () => {
        mockDb.mockResolvedValue([{ id: 1 }]);
        const response = await server.handleRequest({
            type: 'tool',
            name: 'query',
            params: { sql: 'SELECT * FROM test' }
        });
        expect(response.content[0].text).toContain('"id":1');
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