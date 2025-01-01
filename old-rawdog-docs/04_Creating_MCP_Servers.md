# Creating New MCP Servers for RAWDOG

## Overview

This guide provides a practical walkthrough for creating new MCP servers to extend RAWDOG's capabilities. It covers server implementation, tool creation, and integration best practices.

## Server Types

### 1. API Integration Servers
- Connect to external APIs
- Handle authentication
- Manage rate limiting
- Cache responses

### 2. System Integration Servers
- Interact with OS
- Manage processes
- Handle file operations
- Monitor system resources

### 3. Database Servers
- Database connections
- Query execution
- Data transformation
- Connection pooling

## Implementation Guide

### 1. Server Structure

```typescript
// index.ts
import { Server } from "@modelcontextprotocol/sdk/server";

class CustomServer {
  private server: Server;
  
  constructor() {
    this.server = new Server({
      name: "custom-server",
      version: "1.0.0"
    });
    
    this.initializeServer();
  }
  
  private async initializeServer() {
    // Setup tools and resources
    this.registerTools();
    this.registerResources();
    
    // Initialize connections
    await this.setupConnections();
  }
}
```

### 2. Tool Implementation

```typescript
interface Tool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, any>;
    required: string[];
  };
}

private registerTools() {
  this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
      {
        name: "example_tool",
        description: "Tool description",
        inputSchema: {
          type: "object",
          properties: {
            param1: { type: "string" }
          },
          required: ["param1"]
        }
      }
    ]
  }));
}
```

### 3. Resource Implementation

```typescript
interface Resource {
  uri: string;
  name: string;
  mimeType?: string;
  description?: string;
}

private registerResources() {
  this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
    resources: [
      {
        uri: "custom://resource",
        name: "Example Resource",
        mimeType: "application/json"
      }
    ]
  }));
}
```

## Integration Patterns

### 1. API Integration

```typescript
class ApiServer extends CustomServer {
  private api: ApiClient;
  
  protected async setupConnections() {
    this.api = new ApiClient({
      baseUrl: process.env.API_URL,
      apiKey: process.env.API_KEY
    });
  }
  
  protected async callApi(endpoint: string, params: any) {
    try {
      return await this.api.call(endpoint, params);
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `API call failed: ${error.message}`
      );
    }
  }
}
```

### 2. Database Integration

```typescript
class DatabaseServer extends CustomServer {
  private db: Database;
  
  protected async setupConnections() {
    this.db = await createConnection({
      host: process.env.DB_HOST,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD
    });
  }
  
  protected async query(sql: string, params: any[]) {
    try {
      return await this.db.query(sql, params);
    } catch (error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Query failed: ${error.message}`
      );
    }
  }
}
```

## Security Considerations

1. **Input Validation**
```typescript
private validateInput(input: any, schema: JSONSchema) {
  const validator = new JSONSchemaValidator();
  const valid = validator.validate(input, schema);
  if (!valid) {
    throw new McpError(
      ErrorCode.InvalidParams,
      `Invalid input: ${validator.errors.join(", ")}`
    );
  }
}
```

2. **Authentication**
```typescript
private async authenticate(request: Request) {
  const token = request.headers.authorization;
  if (!token) {
    throw new McpError(
      ErrorCode.Unauthorized,
      "Authentication required"
    );
  }
  // Verify token
}
```

3. **Rate Limiting**
```typescript
class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  
  checkLimit(key: string, limit: number, window: number): boolean {
    const now = Date.now();
    const times = this.requests.get(key) || [];
    const recentTimes = times.filter(time => time > now - window);
    
    if (recentTimes.length >= limit) {
      return false;
    }
    
    recentTimes.push(now);
    this.requests.set(key, recentTimes);
    return true;
  }
}
```

## Testing

```typescript
import { expect } from 'chai';
import { CustomServer } from './server';

describe('CustomServer', () => {
  let server: CustomServer;
  
  beforeEach(() => {
    server = new CustomServer();
  });
  
  it('should handle tool requests', async () => {
    const result = await server.handleToolCall({
      name: 'example_tool',
      arguments: { param1: 'test' }
    });
    
    expect(result).to.exist;
  });
  
  it('should handle errors gracefully', async () => {
    try {
      await server.handleToolCall({
        name: 'invalid_tool',
        arguments: {}
      });
    } catch (error) {
      expect(error).to.be.instanceOf(McpError);
      expect(error.code).to.equal(ErrorCode.MethodNotFound);
    }
  });
});
```

## Deployment

1. **Build Configuration**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "outDir": "./build",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
```

2. **Package Scripts**
```json
{
  "scripts": {
    "build": "tsc",
    "start": "node build/index.js",
    "test": "mocha -r ts-node/register tests/**/*.test.ts",
    "lint": "eslint src/**/*.ts"
  }
}
```

3. **Environment Setup**
```bash
# .env
API_KEY=your-api-key
DB_HOST=localhost
DB_USER=user
DB_PASSWORD=password
```

## Best Practices

1. **Error Handling**
- Use appropriate error codes
- Provide detailed error messages
- Implement proper cleanup
- Log errors appropriately

2. **Performance**
- Implement caching
- Use connection pooling
- Handle memory efficiently
- Implement timeouts

3. **Maintenance**
- Use clear documentation
- Implement logging
- Monitor server health
- Regular updates

4. **Code Quality**
- Use TypeScript
- Implement tests
- Use linting
- Regular code review