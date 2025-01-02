"""Model Context Protocol (MCP) system."""

from .base import (
    MCPPlugin,
    ResourceProvider,
    ToolProvider,
    HybridPlugin,
    PluginMetadata,
    PluginError,
    PluginInitError,
    create_plugin_metadata
)
from .loader import PluginLoader, LoadedPlugin
from .registry import PluginRegistry, PluginState, PluginInfo
from .config import (
    ConfigurationManager,
    PluginConfigSchema,
    ConfigError,
    ConfigValidationError
)
from .manager import MCPManager

__all__ = [
    # Base
    'MCPPlugin',
    'ResourceProvider',
    'ToolProvider',
    'HybridPlugin',
    'PluginMetadata',
    'PluginError',
    'PluginInitError',
    'create_plugin_metadata',
    
    # Loader
    'PluginLoader',
    'LoadedPlugin',
    
    # Registry
    'PluginRegistry',
    'PluginState',
    'PluginInfo',
    
    # Config
    'ConfigurationManager',
    'PluginConfigSchema',
    'ConfigError',
    'ConfigValidationError',
    
    # Manager
    'MCPManager'
]