# MCP Server Discovery and Loading

## Overview

RAWDOG can implement an automatic MCP server discovery system that monitors a designated `servers/` directory for MCP server implementations. This allows for a plugin-style architecture where new MCP servers can be added by simply dropping them into the servers directory.

## Directory Structure

```
rawdog/
├── servers/              # Main MCP servers directory
│   ├── time/            # Time server implementation
│   │   ├── index.ts     # Server implementation
│   │   ├── package.json # Server dependencies
│   │   └── tsconfig.json
│   ├── weather/         # Weather server implementation
│   │   ├── index.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   └── ...
```

## Server Discovery Mechanism

### 1. Directory Monitoring

```python
class MCPServerDiscovery:
    def __init__(self, servers_dir: Path):
        self.servers_dir = servers_dir
        self.active_servers = {}
    
    def scan_servers(self):
        """Scan servers directory for MCP server implementations"""
        for server_dir in self.servers_dir.iterdir():
            if server_dir.is_dir():
                self.load_server(server_dir)
    
    def load_server(self, server_dir: Path):
        """Load individual MCP server"""
        if self._is_valid_server(server_dir):
            server_name = server_dir.name
            config = self._load_server_config(server_dir)
            self.active_servers[server_name] = config
```

### 2. Server Validation

```python
def _is_valid_server(self, server_dir: Path) -> bool:
    """Validate MCP server structure"""
    required_files = [
        'index.ts',      # Main server implementation
        'package.json',  # Dependencies
        'tsconfig.json'  # TypeScript configuration
    ]
    
    return all(
        (server_dir / file).exists()
        for file in required_files
    )
```

### 3. Configuration Generation

```python
def _load_server_config(self, server_dir: Path) -> dict:
    """Generate server configuration"""
    package_json = json.loads(
        (server_dir / 'package.json').read_text()
    )
    
    return {
        'command': 'node',
        'args': [str(server_dir / 'build' / 'index.js')],
        'env': self._get_server_env(server_dir),
        'name': package_json.get('name', server_dir.name)
    }
```

## Integration with RAWDOG

### 1. Configuration Management

```python
class MCPConfiguration:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.discovery = MCPServerDiscovery(
            rawdog_dir / 'servers'
        )
    
    def update_config(self):
        """Update RAWDOG config with discovered servers"""
        config = self._read_config()
        
        # Scan for new servers
        self.discovery.scan_servers()
        
        # Update MCP servers configuration
        config['mcpServers'] = {
            **config.get('mcpServers', {}),
            **self.discovery.active_servers
        }
        
        self._write_config(config)
```

### 2. Server Lifecycle Management

```python
class MCPServerManager:
    def __init__(self):
        self.servers = {}
        self.config = MCPConfiguration(config_path)
    
    async def start_servers(self):
        """Start all discovered MCP servers"""
        for name, config in self.config.get_servers().items():
            await self.start_server(name, config)
    
    async def start_server(self, name: str, config: dict):
        """Start individual MCP server"""
        process = await asyncio.create_subprocess_exec(
            config['command'],
            *config['args'],
            env=config['env']
        )
        self.servers[name] = process
```

## Server Implementation Requirements

### 1. Required Files

- `index.ts`: Main server implementation
- `package.json`: Server dependencies and metadata
- `tsconfig.json`: TypeScript configuration

### 2. Server Implementation Template

```typescript
// index.ts
import { Server } from '@modelcontextprotocol/sdk/server';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio';

class CustomServer {
    private server: Server;
    
    constructor() {
        this.server = new Server({
            name: 'custom-server',
            version: '1.0.0'
        });
        
        this.setupHandlers();
    }
    
    private setupHandlers() {
        // Implement server capabilities
    }
    
    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
    }
}

// Start server
const server = new CustomServer();
server.run().catch(console.error);
```

### 3. Package Configuration

```json
{
    "name": "custom-server",
    "version": "1.0.0",
    "type": "module",
    "scripts": {
        "build": "tsc",
        "start": "node build/index.js"
    },
    "dependencies": {
        "@modelcontextprotocol/sdk": "^1.0.0"
    }
}
```

## Adding New Servers

1. Create new directory in `servers/`
2. Implement required files
3. Build server
4. RAWDOG will automatically discover and load the server

## Security Considerations

### 1. Server Validation

```python
def validate_server(server_dir: Path) -> bool:
    """Validate server security requirements"""
    # Check package.json for allowed dependencies
    # Verify server doesn't access sensitive paths
    # Ensure proper permission settings
    return True
```

### 2. Resource Isolation

```python
def create_server_env(server_dir: Path) -> dict:
    """Create isolated environment for server"""
    return {
        'NODE_ENV': 'production',
        'SERVER_DIR': str(server_dir),
        'TEMP_DIR': str(server_dir / 'temp'),
        # Add other environment restrictions
    }
```

## Error Handling

### 1. Server Failures

```python
async def handle_server_failure(self, name: str):
    """Handle MCP server failures"""
    if name in self.servers:
        # Log failure
        logger.error(f"Server {name} failed")
        
        # Attempt restart
        config = self.config.get_server_config(name)
        await self.start_server(name, config)
```

### 2. Discovery Errors

```python
def handle_discovery_error(self, server_dir: Path, error: Exception):
    """Handle server discovery errors"""
    logger.error(
        f"Failed to load server from {server_dir}: {error}"
    )
    # Implement recovery strategy
```

## Best Practices

1. **Server Implementation**
   - Follow MCP protocol specification
   - Implement proper error handling
   - Use TypeScript for type safety
   - Include comprehensive tests

2. **Security**
   - Validate all server implementations
   - Isolate server processes
   - Implement proper access controls
   - Monitor server behavior

3. **Maintenance**
   - Regular server updates
   - Version compatibility checks
   - Performance monitoring
   - Resource cleanup

4. **Documentation**
   - Clear server documentation
   - API specifications
   - Usage examples
   - Troubleshooting guides