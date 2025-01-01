# RAWDOG MCP Integration Guide

## Overview

RAWDOG (Run Any Workflow, Described Only Generally) integrates with MCP (Model Context Protocol) servers to extend its capabilities beyond basic Python script execution. This document details how RAWDOG and MCP servers work together.

## Integration Architecture

### 1. Script Generation Layer
```python
# RAWDOG generates Python scripts that can:
- Execute system commands
- Handle file operations
- Process data
- Interact with MCP servers
```

### 2. MCP Server Communication

RAWDOG interacts with MCP servers through:
1. Configuration management
2. Script execution
3. Tool/resource access

## Server Integration Points

### 1. Server Configuration
```yaml
# ~/.rawdog/config.yaml
mcpServers:
  custom-server:
    command: "node"
    args: ["path/to/server.js"]
    env:
      API_KEY: "your-key"
```

### 2. Server Discovery
- Automatic server detection
- Capability registration
- Tool/resource enumeration

### 3. Tool Execution Flow
```
User Request -> RAWDOG Script -> MCP Tool Call -> Result Processing
```

## Implementation Details

### 1. Server Setup

```python
# Example RAWDOG script using MCP server
import subprocess
import json

def call_mcp_tool(server_name, tool_name, args):
    # Format MCP tool request
    request = {
        "jsonrpc": "2.0",
        "method": "call_tool",
        "params": {
            "name": tool_name,
            "arguments": args
        }
    }
    
    # Execute MCP server request
    result = subprocess.run(
        ["mcp-client", server_name],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)
```

### 2. Resource Access

```python
def access_mcp_resource(server_name, uri):
    # Format resource request
    request = {
        "jsonrpc": "2.0",
        "method": "read_resource",
        "params": {
            "uri": uri
        }
    }
    
    # Execute resource request
    result = subprocess.run(
        ["mcp-client", server_name],
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)
```

## Best Practices

### 1. Error Handling

```python
try:
    result = call_mcp_tool(server_name, tool_name, args)
    if "error" in result:
        print(f"MCP tool error: {result['error']}")
        # Handle error appropriately
except Exception as e:
    print(f"Failed to call MCP tool: {e}")
    # Implement recovery strategy
```

### 2. Resource Management

```python
def with_mcp_resource(server_name, uri):
    resource = None
    try:
        resource = access_mcp_resource(server_name, uri)
        # Use resource
    finally:
        if resource:
            # Cleanup if needed
            pass
```

### 3. Performance Optimization

```python
# Cache MCP results when appropriate
cached_results = {}

def get_cached_mcp_result(server_name, tool_name, args, ttl=300):
    cache_key = f"{server_name}:{tool_name}:{json.dumps(args)}"
    if cache_key in cached_results:
        result, timestamp = cached_results[cache_key]
        if time.time() - timestamp < ttl:
            return result
    
    result = call_mcp_tool(server_name, tool_name, args)
    cached_results[cache_key] = (result, time.time())
    return result
```

## Security Considerations

### 1. Input Validation

```python
def validate_mcp_input(args):
    # Validate input parameters
    if not isinstance(args, dict):
        raise ValueError("Arguments must be a dictionary")
    
    # Check required fields
    required_fields = ["param1", "param2"]
    for field in required_fields:
        if field not in args:
            raise ValueError(f"Missing required field: {field}")
```

### 2. Access Control

```python
def check_mcp_permissions(server_name, tool_name):
    # Check if tool access is allowed
    allowed_tools = get_allowed_tools(server_name)
    if tool_name not in allowed_tools:
        raise PermissionError(f"Access to tool {tool_name} not allowed")
```

## Testing

### 1. Unit Tests

```python
def test_mcp_tool_call():
    result = call_mcp_tool(
        "test-server",
        "example-tool",
        {"param": "value"}
    )
    assert "error" not in result
    assert "result" in result
```

### 2. Integration Tests

```python
def test_mcp_workflow():
    # Test complete workflow
    tool_result = call_mcp_tool(...)
    resource = access_mcp_resource(...)
    # Verify results
```

## Troubleshooting

1. Server Connection Issues
   - Check server process
   - Verify configuration
   - Check environment variables

2. Tool Execution Failures
   - Validate input
   - Check permissions
   - Review error messages

3. Resource Access Problems
   - Verify URI format
   - Check resource exists
   - Validate access rights

## Common Patterns

### 1. Tool Chaining

```python
def chain_mcp_tools(steps):
    results = []
    for step in steps:
        server_name, tool_name, args = step
        result = call_mcp_tool(server_name, tool_name, args)
        results.append(result)
        if "error" in result:
            break
    return results
```

### 2. Resource Processing

```python
def process_mcp_resources(resources):
    results = []
    for server_name, uri in resources:
        content = access_mcp_resource(server_name, uri)
        processed = process_content(content)
        results.append(processed)
    return results
```

## Future Considerations

1. Enhanced Caching
   - Implement smarter caching
   - Add cache invalidation
   - Support distributed caching

2. Better Error Recovery
   - Implement retry strategies
   - Add circuit breakers
   - Enhance error reporting

3. Performance Improvements
   - Batch operations
   - Connection pooling
   - Request optimization