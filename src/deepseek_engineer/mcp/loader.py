"""Plugin discovery and loading system."""

import os
import sys
import importlib.util
import inspect
from typing import Dict, List, Type, Optional, Set
from pathlib import Path
import asyncio
import logging
from dataclasses import dataclass

from .base import (
    MCPPlugin,
    PluginMetadata,
    PluginError,
    PluginInitError,
    load_plugin_metadata
)

logger = logging.getLogger(__name__)

@dataclass
class LoadedPlugin:
    """Information about a loaded plugin."""
    metadata: PluginMetadata
    instance: MCPPlugin
    path: Path
    dependencies: Set[str]

class PluginLoader:
    """Handles plugin discovery, loading, and lifecycle management."""
    
    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """Initialize plugin loader with optional plugin directories."""
        self.plugin_dirs = plugin_dirs or []
        self.loaded_plugins: Dict[str, LoadedPlugin] = {}
        self._loading: Set[str] = set()  # For circular dependency detection
    
    def add_plugin_dir(self, path: Path):
        """Add a directory to search for plugins."""
        if path not in self.plugin_dirs:
            self.plugin_dirs.append(path)
    
    def discover_plugins(self) -> List[Path]:
        """
        Discover plugin directories in configured plugin paths.
        
        Returns:
            List of paths to discovered plugin directories
        """
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue
                
            # Look for plugin.json files
            for path in plugin_dir.glob("*/plugin.json"):
                plugin_path = path.parent
                discovered.append(plugin_path)
                
        return discovered
    
    def _load_plugin_module(self, path: Path) -> Optional[Type[MCPPlugin]]:
        """
        Load plugin module and return plugin class.
        
        Args:
            path: Path to plugin directory
            
        Returns:
            Plugin class if found, None otherwise
        """
        # Look for plugin.py or __init__.py
        module_file = None
        for filename in ["plugin.py", "__init__.py"]:
            potential_file = path / filename
            if potential_file.exists():
                module_file = potential_file
                break
        
        if not module_file:
            raise PluginError(f"No plugin module found in {path}")
        
        try:
            # Import module
            module_name = f"mcp_plugin_{path.name}"
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if not spec or not spec.loader:
                raise PluginError(f"Failed to create module spec for {module_file}")
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Find plugin class
            for item_name, item in inspect.getmembers(module):
                if (inspect.isclass(item) and 
                    issubclass(item, MCPPlugin) and 
                    item != MCPPlugin):
                    return item
            
            raise PluginError(f"No plugin class found in {module_file}")
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin module: {str(e)}")
    
    async def load_plugin(
        self,
        path: Path,
        config: Optional[Dict] = None,
        _loading_chain: Optional[Set[str]] = None
    ) -> LoadedPlugin:
        """
        Load a plugin from a directory.
        
        Args:
            path: Path to plugin directory
            config: Optional plugin configuration
            _loading_chain: Internal set for circular dependency detection
            
        Returns:
            LoadedPlugin instance
            
        Raises:
            PluginError: If plugin loading fails
        """
        try:
            # Load metadata
            metadata = load_plugin_metadata(path)
            
            # Check for circular dependencies
            if _loading_chain is None:
                _loading_chain = set()
            
            if metadata.name in _loading_chain:
                chain = " -> ".join(_loading_chain)
                raise PluginError(
                    f"Circular dependency detected: {chain} -> {metadata.name}"
                )
            
            # Check if already loaded
            if metadata.name in self.loaded_plugins:
                return self.loaded_plugins[metadata.name]
            
            # Track loading state
            _loading_chain.add(metadata.name)
            
            # Load dependencies first
            dependencies = set()
            if config and "dependencies" in config:
                for dep_name, dep_config in config["dependencies"].items():
                    dep_path = Path(dep_config["path"])
                    dep_plugin = await self.load_plugin(
                        dep_path,
                        dep_config.get("config"),
                        _loading_chain
                    )
                    dependencies.add(dep_name)
            
            # Load plugin class
            plugin_class = self._load_plugin_module(path)
            if not plugin_class:
                raise PluginError(f"No plugin class found in {path}")
            
            # Instantiate plugin
            plugin = plugin_class(metadata, config)
            
            # Initialize plugin
            try:
                await plugin.initialize()
            except Exception as e:
                raise PluginInitError(f"Plugin initialization failed: {str(e)}")
            
            # Register loaded plugin
            loaded = LoadedPlugin(
                metadata=metadata,
                instance=plugin,
                path=path,
                dependencies=dependencies
            )
            self.loaded_plugins[metadata.name] = loaded
            
            # Remove from loading chain
            _loading_chain.remove(metadata.name)
            
            return loaded
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin from {path}: {str(e)}")
    
    async def load_all_plugins(self, configs: Optional[Dict[str, Dict]] = None):
        """
        Discover and load all plugins.
        
        Args:
            configs: Optional dict mapping plugin names to configurations
        """
        discovered = self.discover_plugins()
        
        for path in discovered:
            try:
                metadata = load_plugin_metadata(path)
                config = configs.get(metadata.name) if configs else None
                await self.load_plugin(path, config)
            except Exception as e:
                logger.error(f"Failed to load plugin {path}: {str(e)}")
    
    def get_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """Get a loaded plugin by name."""
        return self.loaded_plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """Get metadata for all loaded plugins."""
        return [p.metadata for p in self.loaded_plugins.values()]
    
    async def unload_plugin(self, name: str):
        """
        Unload a plugin and its dependencies.
        
        Args:
            name: Name of plugin to unload
        """
        if name not in self.loaded_plugins:
            return
            
        plugin = self.loaded_plugins[name]
        
        # Unload plugins that depend on this one
        dependents = [
            p_name for p_name, p in self.loaded_plugins.items()
            if name in p.dependencies
        ]
        
        for dep in dependents:
            await self.unload_plugin(dep)
        
        # Shutdown plugin
        try:
            await plugin.instance.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down plugin {name}: {str(e)}")
        
        # Remove from loaded plugins
        del self.loaded_plugins[name]
    
    async def reload_plugin(self, name: str):
        """
        Reload a plugin and its dependents.
        
        Args:
            name: Name of plugin to reload
        """
        if name not in self.loaded_plugins:
            raise PluginError(f"Plugin {name} not loaded")
            
        plugin = self.loaded_plugins[name]
        path = plugin.path
        config = plugin.instance.config
        
        # Unload plugin and dependents
        await self.unload_plugin(name)
        
        # Reload plugin
        await self.load_plugin(path, config)
    
    async def shutdown(self):
        """Shutdown all plugins."""
        # Shutdown in reverse dependency order
        plugin_names = list(self.loaded_plugins.keys())
        for name in reversed(plugin_names):
            await self.unload_plugin(name)