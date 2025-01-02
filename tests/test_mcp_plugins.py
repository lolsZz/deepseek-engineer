"""Tests for the MCP plugin system."""

import pytest
from pathlib import Path
import json
from datetime import datetime
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from deepseek_engineer.mcp.base import (
    PluginMetadata,
    MCPPlugin,
    ResourceProvider,
    ToolProvider,
    HybridPlugin,
    PluginError,
    PluginInitError,
    load_plugin_metadata,
    create_plugin_metadata
)
from deepseek_engineer.mcp.loader import PluginLoader, LoadedPlugin

# Test Plugin Implementations
class TestPlugin(MCPPlugin):
    """Test plugin implementation."""
    
    def _validate_config(self):
        if self.config.get("fail_validation"):
            raise PluginError("Validation failed")
    
    async def initialize(self):
        if self.config.get("fail_init"):
            raise PluginInitError("Initialization failed")
    
    async def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"test": True}

class TestResourcePlugin(ResourceProvider):
    """Test resource provider implementation."""
    
    def _validate_config(self):
        pass
    
    async def initialize(self):
        pass
    
    async def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"resources": ["test"]}
    
    async def get_resource(self, uri: str):
        return {"uri": uri}
    
    def list_resources(self):
        return [{"name": "test", "type": "test"}]
    
    def get_resource_schema(self, resource_type: str):
        return {"type": "object"}

class TestToolPlugin(ToolProvider):
    """Test tool provider implementation."""
    
    def _validate_config(self):
        pass
    
    async def initialize(self):
        pass
    
    async def shutdown(self):
        pass
    
    def get_capabilities(self):
        return {"tools": ["test"]}
    
    async def execute_tool(self, tool_name: str, args: dict):
        return {"result": "success"}
    
    def list_tools(self):
        return [{"name": "test", "description": "test"}]
    
    def get_tool_schema(self, tool_name: str):
        return {"type": "object"}

@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Create a temporary plugin directory with metadata."""
    plugin_dir = tmp_path / "test_plugin"
    plugin_dir.mkdir()
    
    # Create plugin.json
    metadata = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test plugin",
        "author": "Test Author"
    }
    with open(plugin_dir / "plugin.json", "w") as f:
        json.dump(metadata, f)
    
    # Create plugin.py
    plugin_code = """
from deepseek_engineer.mcp.base import MCPPlugin

class TestPlugin(MCPPlugin):
    def _validate_config(self):
        pass
        
    async def initialize(self):
        pass
        
    async def shutdown(self):
        pass
        
    def get_capabilities(self):
        return {"test": True}
"""
    with open(plugin_dir / "plugin.py", "w") as f:
        f.write(plugin_code)
    
    return plugin_dir

def test_plugin_metadata():
    """Test plugin metadata creation and serialization."""
    metadata = create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test plugin",
        author="Test Author",
        homepage="https://test.com"
    )
    
    assert metadata.name == "test"
    assert metadata.version == "1.0.0"
    assert metadata.homepage == "https://test.com"
    
    # Test serialization
    data = metadata.to_dict()
    loaded = PluginMetadata.from_dict(data)
    assert loaded.name == metadata.name
    assert loaded.version == metadata.version

def test_plugin_validation():
    """Test plugin configuration validation."""
    metadata = create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test",
        author="Test"
    )
    
    # Test successful validation
    plugin = TestPlugin(metadata, {})
    assert plugin.metadata == metadata
    
    # Test failed validation
    with pytest.raises(PluginError):
        TestPlugin(metadata, {"fail_validation": True})

@pytest.mark.asyncio
async def test_plugin_lifecycle():
    """Test plugin initialization and shutdown."""
    metadata = create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test",
        author="Test"
    )
    
    # Test successful initialization
    plugin = TestPlugin(metadata, {})
    await plugin.initialize()
    
    # Test failed initialization
    plugin_fail = TestPlugin(metadata, {"fail_init": True})
    with pytest.raises(PluginInitError):
        await plugin_fail.initialize()

def test_plugin_types():
    """Test different plugin type implementations."""
    metadata = create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test",
        author="Test"
    )
    
    # Test resource provider
    resource_plugin = TestResourcePlugin(metadata, {})
    assert "resources" in resource_plugin.get_capabilities()
    
    # Test tool provider
    tool_plugin = TestToolPlugin(metadata, {})
    assert "tools" in tool_plugin.get_capabilities()

@pytest.mark.asyncio
async def test_plugin_loader(temp_plugin_dir):
    """Test plugin loader functionality."""
    loader = PluginLoader([temp_plugin_dir.parent])
    
    # Test plugin discovery
    discovered = loader.discover_plugins()
    assert len(discovered) == 1
    assert discovered[0] == temp_plugin_dir
    
    # Test plugin loading
    plugin = await loader.load_plugin(temp_plugin_dir)
    assert isinstance(plugin, LoadedPlugin)
    assert plugin.metadata.name == "test_plugin"
    
    # Test plugin listing
    plugins = loader.list_plugins()
    assert len(plugins) == 1
    assert plugins[0].name == "test_plugin"
    
    # Test plugin unloading
    await loader.unload_plugin("test_plugin")
    assert "test_plugin" not in loader.loaded_plugins

@pytest.mark.asyncio
async def test_plugin_dependencies(tmp_path):
    """Test plugin dependency resolution."""
    # Create two plugins with a dependency relationship
    plugin1_dir = tmp_path / "plugin1"
    plugin1_dir.mkdir()
    with open(plugin1_dir / "plugin.json", "w") as f:
        json.dump({
            "name": "plugin1",
            "version": "1.0.0",
            "description": "Plugin 1",
            "author": "Test"
        }, f)
    
    plugin2_dir = tmp_path / "plugin2"
    plugin2_dir.mkdir()
    with open(plugin2_dir / "plugin.json", "w") as f:
        json.dump({
            "name": "plugin2",
            "version": "1.0.0",
            "description": "Plugin 2",
            "author": "Test"
        }, f)
    
    loader = PluginLoader([tmp_path])
    
    # Test loading with dependencies
    config = {
        "plugin2": {
            "dependencies": {
                "plugin1": {
                    "path": str(plugin1_dir),
                    "config": {}
                }
            }
        }
    }
    
    with patch("deepseek_engineer.mcp.loader.PluginLoader._load_plugin_module") as mock_load:
        mock_load.return_value = TestPlugin
        
        plugin2 = await loader.load_plugin(plugin2_dir, config["plugin2"])
        assert "plugin1" in plugin2.dependencies
        assert "plugin1" in loader.loaded_plugins

@pytest.mark.asyncio
async def test_plugin_reload(temp_plugin_dir):
    """Test plugin reloading."""
    loader = PluginLoader([temp_plugin_dir.parent])
    
    # Load plugin
    plugin = await loader.load_plugin(temp_plugin_dir)
    original_instance = plugin.instance
    
    # Reload plugin
    await loader.reload_plugin("test_plugin")
    reloaded = loader.get_plugin("test_plugin")
    
    assert reloaded is not None
    assert reloaded.instance is not original_instance

def test_error_handling(tmp_path):
    """Test error handling in plugin operations."""
    # Test invalid plugin.json
    bad_plugin_dir = tmp_path / "bad_plugin"
    bad_plugin_dir.mkdir()
    with open(bad_plugin_dir / "plugin.json", "w") as f:
        f.write("invalid json")
    
    with pytest.raises(PluginError):
        load_plugin_metadata(bad_plugin_dir)
    
    # Test missing plugin module
    loader = PluginLoader([tmp_path])
    with pytest.raises(PluginError):
        asyncio.run(loader.load_plugin(bad_plugin_dir))