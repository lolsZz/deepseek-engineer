"""Base classes and interfaces for MCP plugins."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

@dataclass
class PluginMetadata:
    """Metadata for an MCP plugin."""
    name: str
    version: str
    description: str
    author: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: str = "MIT"
    created: datetime = None
    updated: datetime = None

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created is None:
            self.created = datetime.now()
        if self.updated is None:
            self.updated = self.created

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "homepage": self.homepage,
            "repository": self.repository,
            "license": self.license,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create metadata from dictionary format."""
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            homepage=data.get("homepage"),
            repository=data.get("repository"),
            license=data.get("license", "MIT"),
            created=datetime.fromisoformat(data["created"]) if "created" in data else None,
            updated=datetime.fromisoformat(data["updated"]) if "updated" in data else None
        )

class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass

class PluginInitError(PluginError):
    """Raised when plugin initialization fails."""
    pass

class PluginConfigError(PluginError):
    """Raised when plugin configuration is invalid."""
    pass

class MCPPlugin(ABC):
    """Abstract base class for MCP plugins."""
    
    def __init__(self, metadata: PluginMetadata, config: Optional[Dict[str, Any]] = None):
        """Initialize plugin with metadata and optional configuration."""
        self.metadata = metadata
        self.config = config or {}
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self):
        """Validate plugin configuration."""
        pass
    
    @abstractmethod
    async def initialize(self):
        """Initialize plugin resources."""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Clean up plugin resources."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get plugin capabilities."""
        pass

class ResourceProvider(MCPPlugin):
    """Base class for plugins that provide resources."""
    
    @abstractmethod
    async def get_resource(self, uri: str) -> Any:
        """Get resource by URI."""
        pass
    
    @abstractmethod
    def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        pass
    
    @abstractmethod
    def get_resource_schema(self, resource_type: str) -> Dict[str, Any]:
        """Get JSON schema for resource type."""
        pass

class ToolProvider(MCPPlugin):
    """Base class for plugins that provide tools."""
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments."""
        pass
    
    @abstractmethod
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        pass
    
    @abstractmethod
    def get_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get JSON schema for tool arguments."""
        pass

class HybridPlugin(ResourceProvider, ToolProvider):
    """Plugin that provides both resources and tools."""
    pass

def load_plugin_metadata(path: Path) -> PluginMetadata:
    """Load plugin metadata from a file."""
    try:
        with open(path / "plugin.json") as f:
            data = json.load(f)
        return PluginMetadata.from_dict(data)
    except Exception as e:
        raise PluginError(f"Failed to load plugin metadata: {str(e)}")

def create_plugin_metadata(
    name: str,
    version: str,
    description: str,
    author: str,
    **kwargs
) -> PluginMetadata:
    """Create new plugin metadata."""
    return PluginMetadata(
        name=name,
        version=version,
        description=description,
        author=author,
        **kwargs
    )