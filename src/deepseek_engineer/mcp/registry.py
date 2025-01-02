"""Plugin registry for managing MCP plugins."""

import asyncio
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from enum import Enum

from .base import (
    MCPPlugin,
    PluginMetadata,
    ResourceProvider,
    ToolProvider,
    PluginError
)
from .loader import PluginLoader, LoadedPlugin

logger = logging.getLogger(__name__)

class PluginState(Enum):
    """Plugin states in the registry."""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class PluginInfo:
    """Extended information about a registered plugin."""
    loaded: LoadedPlugin
    state: PluginState
    error: Optional[str] = None
    last_state_change: datetime = None

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.last_state_change is None:
            self.last_state_change = datetime.now()

class PluginRegistry:
    """Central registry for MCP plugins."""
    
    def __init__(self):
        """Initialize plugin registry."""
        self.loader = PluginLoader()
        self.plugins: Dict[str, PluginInfo] = {}
        self._state_listeners: Dict[str, List[Callable]] = {}
        self._capability_cache: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    def add_plugin_directory(self, path: Path):
        """Add a directory to search for plugins."""
        self.loader.add_plugin_dir(path)
    
    async def discover_and_load(self, configs: Optional[Dict[str, Dict]] = None):
        """
        Discover and load all plugins in registered directories.
        
        Args:
            configs: Optional configurations for plugins
        """
        async with self._lock:
            discovered = self.loader.discover_plugins()
            
            for path in discovered:
                try:
                    plugin = await self.loader.load_plugin(path, configs.get(path.name) if configs else None)
                    await self.register_plugin(plugin)
                except Exception as e:
                    logger.error(f"Failed to load plugin from {path}: {str(e)}")
    
    async def register_plugin(self, loaded_plugin: LoadedPlugin):
        """
        Register a loaded plugin.
        
        Args:
            loaded_plugin: LoadedPlugin instance to register
        """
        async with self._lock:
            name = loaded_plugin.metadata.name
            
            if name in self.plugins:
                raise PluginError(f"Plugin {name} already registered")
            
            info = PluginInfo(
                loaded=loaded_plugin,
                state=PluginState.REGISTERED
            )
            self.plugins[name] = info
            
            # Clear capability cache
            self._capability_cache.clear()
            
            # Notify listeners
            await self._notify_state_change(name, PluginState.REGISTERED)
            
            # Initialize plugin
            await self._set_plugin_state(name, PluginState.INITIALIZING)
            try:
                await loaded_plugin.instance.initialize()
                await self._set_plugin_state(name, PluginState.ACTIVE)
            except Exception as e:
                error = f"Plugin initialization failed: {str(e)}"
                await self._set_plugin_state(name, PluginState.ERROR, error)
                raise
    
    async def unregister_plugin(self, name: str):
        """
        Unregister and stop a plugin.
        
        Args:
            name: Name of plugin to unregister
        """
        async with self._lock:
            if name not in self.plugins:
                return
            
            info = self.plugins[name]
            
            # Stop plugin
            await self._set_plugin_state(name, PluginState.STOPPING)
            try:
                await info.loaded.instance.shutdown()
            except Exception as e:
                logger.error(f"Error stopping plugin {name}: {str(e)}")
            
            # Unload plugin and dependents
            await self.loader.unload_plugin(name)
            
            # Remove from registry
            del self.plugins[name]
            self._capability_cache.clear()
            
            # Notify listeners
            await self._notify_state_change(name, PluginState.STOPPED)
    
    def get_plugin(self, name: str) -> Optional[MCPPlugin]:
        """Get plugin instance by name."""
        info = self.plugins.get(name)
        return info.loaded.instance if info else None
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Get plugin information by name."""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """Get metadata for all registered plugins."""
        return [info.loaded.metadata for info in self.plugins.values()]
    
    def get_plugin_state(self, name: str) -> Optional[PluginState]:
        """Get current state of a plugin."""
        info = self.plugins.get(name)
        return info.state if info else None
    
    def get_active_plugins(self) -> List[str]:
        """Get names of all active plugins."""
        return [
            name for name, info in self.plugins.items()
            if info.state == PluginState.ACTIVE
        ]
    
    def get_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available resources from resource providers."""
        if "resources" not in self._capability_cache:
            resources = {}
            for name, info in self.plugins.items():
                if (isinstance(info.loaded.instance, ResourceProvider) and 
                    info.state == PluginState.ACTIVE):
                    try:
                        resources[name] = info.loaded.instance.list_resources()
                    except Exception as e:
                        logger.error(f"Error listing resources for {name}: {str(e)}")
            self._capability_cache["resources"] = resources
        return self._capability_cache["resources"]
    
    def get_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available tools from tool providers."""
        if "tools" not in self._capability_cache:
            tools = {}
            for name, info in self.plugins.items():
                if (isinstance(info.loaded.instance, ToolProvider) and 
                    info.state == PluginState.ACTIVE):
                    try:
                        tools[name] = info.loaded.instance.list_tools()
                    except Exception as e:
                        logger.error(f"Error listing tools for {name}: {str(e)}")
            self._capability_cache["tools"] = tools
        return self._capability_cache["tools"]
    
    async def execute_tool(
        self,
        plugin_name: str,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Any:
        """
        Execute a tool from a specific plugin.
        
        Args:
            plugin_name: Name of plugin providing the tool
            tool_name: Name of tool to execute
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin or not isinstance(plugin, ToolProvider):
            raise PluginError(f"No tool provider plugin named {plugin_name}")
        
        if self.get_plugin_state(plugin_name) != PluginState.ACTIVE:
            raise PluginError(f"Plugin {plugin_name} is not active")
        
        return await plugin.execute_tool(tool_name, args)
    
    async def get_resource(self, plugin_name: str, uri: str) -> Any:
        """
        Get a resource from a specific plugin.
        
        Args:
            plugin_name: Name of plugin providing the resource
            uri: Resource URI
            
        Returns:
            Resource data
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin or not isinstance(plugin, ResourceProvider):
            raise PluginError(f"No resource provider plugin named {plugin_name}")
        
        if self.get_plugin_state(plugin_name) != PluginState.ACTIVE:
            raise PluginError(f"Plugin {plugin_name} is not active")
        
        return await plugin.get_resource(uri)
    
    def add_state_listener(
        self,
        plugin_name: str,
        callback: Callable[[str, PluginState, Optional[str]], None]
    ):
        """Add listener for plugin state changes."""
        if plugin_name not in self._state_listeners:
            self._state_listeners[plugin_name] = []
        self._state_listeners[plugin_name].append(callback)
    
    def remove_state_listener(
        self,
        plugin_name: str,
        callback: Callable[[str, PluginState, Optional[str]], None]
    ):
        """Remove state change listener."""
        if plugin_name in self._state_listeners:
            try:
                self._state_listeners[plugin_name].remove(callback)
            except ValueError:
                pass
    
    async def _set_plugin_state(
        self,
        name: str,
        state: PluginState,
        error: Optional[str] = None
    ):
        """Update plugin state and notify listeners."""
        if name in self.plugins:
            info = self.plugins[name]
            info.state = state
            info.error = error
            info.last_state_change = datetime.now()
            await self._notify_state_change(name, state, error)
    
    async def _notify_state_change(
        self,
        name: str,
        state: PluginState,
        error: Optional[str] = None
    ):
        """Notify listeners of state change."""
        if name in self._state_listeners:
            for callback in self._state_listeners[name]:
                try:
                    callback(name, state, error)
                except Exception as e:
                    logger.error(f"Error in state listener: {str(e)}")
    
    async def shutdown(self):
        """Shutdown all plugins and clear registry."""
        plugin_names = list(self.plugins.keys())
        for name in reversed(plugin_names):
            await self.unregister_plugin(name)