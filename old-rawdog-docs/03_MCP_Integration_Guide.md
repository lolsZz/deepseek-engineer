# MCP (Model Context Protocol) Integration with RAWDOG

## Overview

The Model Context Protocol (MCP) provides a powerful extension mechanism for RAWDOG, allowing it to interact with external tools and services through a standardized interface. This document details how to integrate MCP servers with RAWDOG.

## Architecture

### 1. Core Components

```
RAWDOG
  └── MCP Integration
      ├── Server Communication
      │   ├── StdioServerTransport
      │   └── Server Connection Management
      ├── Tool Management
      │   ├── Tool Registration
      │   └── Tool Execution
      └── Resource Management
          ├── Resource Access
          └── Resource Templates
```

### 2. Server Implementation

MCP servers in RAWDOG follow a standard structure:

```typescript
import { Server } from "@modelcontextprotocol/sdk/server";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";

const server = new Server({
  name: "custom-server",
  version: "1.0.0"
});

// Tool definitions
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "tool_name",
      description: "Tool description",
      inputSchema: {
        // JSON Schema for tool parameters
      }
    }
  ]
}));

// Tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Tool implementation
});
```

## Integration Steps

1. **Server Setup**
   - Create a new directory in `/servers/src/`
   - Initialize TypeScript configuration
   - Install MCP SDK dependencies

2. **Tool Definition**
   ```typescript
   interface Tool {
     name: string;
     description: string;
     inputSchema: JSONSchema;
   }
   ```

3. **Resource Implementation**
   ```typescript
   interface Resource {
     uri: string;
     name: string;
     mimeType?: string;
     description?: string;
   }
   ```

4. **Error Handling**
   ```typescript
   try {
     // Tool/resource implementation
   } catch (error) {
     throw new McpError(ErrorCode.InternalError, error.message);
   }
   ```

## Best Practices

1. **Tool Design**
   - Keep tools focused and single-purpose
   - Use clear, descriptive names
   - Provide comprehensive input validation
   - Return structured responses

2. **Resource Management**
   - Use URI templates for dynamic resources
   - Implement proper cleanup
   - Handle concurrent access
   - Cache when appropriate

3. **Error Handling**
   - Use appropriate error codes
   - Provide detailed error messages
   - Implement proper cleanup on errors
   - Handle timeouts gracefully

4. **Security**
   - Validate all inputs
   - Sanitize file paths
   - Implement proper access controls
   - Handle sensitive data appropriately

## Example Implementation

Here's a minimal example of an MCP server:

```typescript
#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio";

class CustomServer {
  private server: Server;

  constructor() {
    this.server = new Server({
      name: "custom-server",
      version: "1.0.0"
    });

    this.setupTools();
  }

  private setupTools() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "example_tool",
          description: "Example tool implementation",
          inputSchema: {
            type: "object",
            properties: {
              input: { type: "string" }
            },
            required: ["input"]
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      switch (name) {
        case "example_tool":
          return {
            content: [{
              type: "text",
              text: `Processed: ${args.input}`
            }]
          };
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Custom MCP server running");
  }
}

const server = new CustomServer();
server.run().catch(console.error);
```

## Configuration

MCP servers are configured in RAWDOG's configuration file:

```yaml
mcpServers:
  custom-server:
    command: "node"
    args: ["path/to/server/build/index.js"]
    env:
      KEY: "value"
```

## Testing

1. Build the server:
```bash
npm run build
```

2. Test tool execution:
```bash
node build/index.js
```

3. Verify in RAWDOG:
```python
# Your tool will be available through RAWDOG's MCP integration
```

## Common Issues

1. **Connection Errors**
   - Check server process is running
   - Verify stdio transport
   - Check configuration paths

2. **Tool Execution Failures**
   - Validate input schema
   - Check error handling
   - Verify tool implementation

3. **Resource Access Issues**
   - Check URI format
   - Verify resource exists
   - Check permissions