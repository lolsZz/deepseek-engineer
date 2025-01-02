"""MCP manager for coordinating plugin system components."""

import asyncio
from typing import Dict, List, Any, Optional, Set, Callable
from pathlib import Path
import logging
from datetime import datetime

from .base import (
    MCPPlugin,
    PluginMetadata,
    ResourceProvider,
    ToolProvider,
    PluginError
)
from .loader import PluginLoader, LoadedPlugin
from .registry import PluginRegistry, PluginState, PluginInfo
from .config import ConfigurationManager, PluginConfigSchema

logger = logging.getLogger(__name__)

class MCPManager:
    """Coordinates MCP plugin system components."""
    
    def __init__(
        self,
        plugin_dirs: Optional[List[Path]] = None,
        config_dir: Optional[Path] = None
    ):
        """
        Initialize MCP manager.
        
        Args:
            plugin_dirs: Optional list of plugin directories
            config_dir: Optional configuration directory
        """
        self.registry = PluginRegistry()
        self.config_manager = ConfigurationManager(config_dir)
        
        # Add plugin directories
        if plugin_dirs:
            for path in plugin_dirs:
                self.add_plugin_directory(path)
    
    def add_plugin_directory(self, path: Path):
        """Add a directory to search for plugins."""
        self.registry.add_plugin_directory(path)
    
    async def initialize(self):
        """Initialize plugin system and discover plugins."""
        try:
            # Discover and load plugins
            await self.registry.discover_and_load()
            
            logger.info(
                f"Initialized {len(self.registry.get_active_plugins())} plugins"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin system: {str(e)}")
            raise
    
    async def shutdown(self):
        """Shutdown plugin system and cleanup."""
        try:
            await self.registry.shutdown()
            logger.info("Plugin system shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during plugin system shutdown: {str(e)}")
            raise
    
    def register_plugin_schema(
        self,
        plugin_name: str,
        schema: PluginConfigSchema
    ):
        """
        Register configuration schema for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            schema: Configuration schema
        """
        self.config_manager.register_schema(plugin_name, schema)
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]):
        """
        Configure a plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: Plugin configuration
        """
        self.config_manager.set_config(plugin_name, config)
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get plugin configuration.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration
        """
        return self.config_manager.get_config(plugin_name)
    
    def get_plugin_schema(self, plugin_name: str) -> Optional[PluginConfigSchema]:
        """
        Get plugin configuration schema.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration schema if registered
        """
        return self.config_manager.get_schema(plugin_name)
    
    def get_plugin_state(self, plugin_name: str) -> Optional[PluginState]:
        """
        Get current state of a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin state if plugin exists
        """
        return self.registry.get_plugin_state(plugin_name)
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        Get detailed plugin information.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin information if plugin exists
        """
        return self.registry.get_plugin_info(plugin_name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """
        Get list of all registered plugins.
        
        Returns:
            List of plugin metadata
        """
        return self.registry.list_plugins()
    
    def get_active_plugins(self) -> List[str]:
        """
        Get list of active plugin names.
        
        Returns:
            List of active plugin names
        """
        return self.registry.get_active_plugins()
    
    def get_available_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available resources from plugins.
        
        Returns:
            Dictionary mapping plugin names to their resources
        """
        return self.registry.get_resources()
    
    def get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available tools from plugins.
        
        Returns:
            Dictionary mapping plugin names to their tools
        """
        return self.registry.get_tools()
    
    async def execute_tool(
        self,
        plugin_name: str,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Any:
        """
        Execute a plugin tool.
        
        Args:
            plugin_name: Name of the plugin
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        return await self.registry.execute_tool(plugin_name, tool_name, args)
    
    async def get_resource(self, plugin_name: str, uri: str) -> Any:
        """
        Get a plugin resource.
        
        Args:
            plugin_name: Name of the plugin
            uri: Resource URI
            
        Returns:
            Resource data
        """
        return await self.registry.get_resource(plugin_name, uri)
    
    def add_plugin_state_listener(
        self,
        plugin_name: str,
        callback: Callable[[str, PluginState, Optional[str]], None]
    ):
        """
        Add listener for plugin state changes.
        
        Args:
            plugin_name: Name of the plugin
            callback: Callback function for state changes
        """
        self.registry.add_state_listener(plugin_name, callback)
    
    def remove_plugin_state_listener(
        self,
        plugin_name: str,
        callback: Callable[[str, PluginState, Optional[str]], None]
    ):
        """
        Remove plugin state change listener.
        
        Args:
            plugin_name: Name of the plugin
            callback: Callback function to remove
        """
        self.registry.remove_state_listener(plugin_name, callback)
    
    async def reload_plugin(self, plugin_name: str):
        """
        Reload a plugin.
        
        Args:
            plugin_name: Name of the plugin to reload
        """
        await self.registry.reload_plugin(plugin_name)
    
    def clear_plugin_config(self, plugin_name: str):
        """
        Clear plugin configuration.
        
        Args:
            plugin_name: Name of the plugin
        """
        self.config_manager.clear_config(plugin_name)