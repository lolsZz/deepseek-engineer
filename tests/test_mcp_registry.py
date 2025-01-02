"""Tests for the MCP plugin registry."""

import pytest
import asyncio
from pathlib import Path
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, call

from deepseek_engineer.mcp.registry import (
    PluginRegistry,
    PluginState,
    PluginInfo,
    PluginError
)
from deepseek_engineer.mcp.base import (
    MCPPlugin,
    ResourceProvider,
    ToolProvider,
    PluginMetadata,
    create_plugin_metadata
)
from deepseek_engineer.mcp.loader import LoadedPlugin

# Test Plugin Implementations
class TestPlugin(MCPPlugin):
    """Basic test plugin."""
    def _validate_config(self): pass
    async def initialize(self): pass
    async def shutdown(self): pass
    def get_capabilities(self): return {"test": True}

class TestResourcePlugin(ResourceProvider):
    """Test resource provider."""
    def _validate_config(self): pass
    async def initialize(self): pass
    async def shutdown(self): pass
    def get_capabilities(self): return {"resources": True}
    async def get_resource(self, uri): return {"uri": uri}
    def list_resources(self): return [{"name": "test"}]
    def get_resource_schema(self, type): return {}

class TestToolPlugin(ToolProvider):
    """Test tool provider."""
    def _validate_config(self): pass
    async def initialize(self): pass
    async def shutdown(self): pass
    def get_capabilities(self): return {"tools": True}
    async def execute_tool(self, name, args): return {"result": "success"}
    def list_tools(self): return [{"name": "test"}]
    def get_tool_schema(self, name): return {}

@pytest.fixture
def registry():
    """Create a plugin registry for testing."""
    return PluginRegistry()

@pytest.fixture
def test_plugin():
    """Create a test plugin instance."""
    metadata = create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test Plugin",
        author="Test"
    )
    return LoadedPlugin(
        metadata=metadata,
        instance=TestPlugin(metadata),
        path=Path("/test"),
        dependencies=set()
    )

@pytest.fixture
def resource_plugin():
    """Create a test resource plugin instance."""
    metadata = create_plugin_metadata(
        name="resource",
        version="1.0.0",
        description="Resource Plugin",
        author="Test"
    )
    return LoadedPlugin(
        metadata=metadata,
        instance=TestResourcePlugin(metadata),
        path=Path("/test"),
        dependencies=set()
    )

@pytest.fixture
def tool_plugin():
    """Create a test tool plugin instance."""
    metadata = create_plugin_metadata(
        name="tool",
        version="1.0.0",
        description="Tool Plugin",
        author="Test"
    )
    return LoadedPlugin(
        metadata=metadata,
        instance=TestToolPlugin(metadata),
        path=Path("/test"),
        dependencies=set()
    )

@pytest.mark.asyncio
async def test_plugin_registration(registry, test_plugin):
    """Test basic plugin registration."""
    await registry.register_plugin(test_plugin)
    
    assert test_plugin.metadata.name in registry.plugins
    info = registry.get_plugin_info(test_plugin.metadata.name)
    assert info.state == PluginState.ACTIVE
    assert info.error is None

@pytest.mark.asyncio
async def test_plugin_state_transitions(registry, test_plugin):
    """Test plugin state transitions."""
    # Mock initialize to track states
    states = []
    
    def state_listener(name, state, error):
        states.append(state)
    
    registry.add_state_listener(test_plugin.metadata.name, state_listener)
    await registry.register_plugin(test_plugin)
    
    assert states == [
        PluginState.REGISTERED,
        PluginState.INITIALIZING,
        PluginState.ACTIVE
    ]
    
    await registry.unregister_plugin(test_plugin.metadata.name)
    assert states[-1] == PluginState.STOPPING

@pytest.mark.asyncio
async def test_plugin_initialization_error(registry):
    """Test handling of plugin initialization errors."""
    metadata = create_plugin_metadata(
        name="error",
        version="1.0.0",
        description="Error Plugin",
        author="Test"
    )
    
    class ErrorPlugin(TestPlugin):
        async def initialize(self):
            raise Exception("Init error")
    
    error_plugin = LoadedPlugin(
        metadata=metadata,
        instance=ErrorPlugin(metadata),
        path=Path("/test"),
        dependencies=set()
    )
    
    with pytest.raises(Exception):
        await registry.register_plugin(error_plugin)
    
    info = registry.get_plugin_info("error")
    assert info.state == PluginState.ERROR
    assert "Init error" in info.error

@pytest.mark.asyncio
async def test_resource_provider(registry, resource_plugin):
    """Test resource provider functionality."""
    await registry.register_plugin(resource_plugin)
    
    # Test resource listing
    resources = registry.get_resources()
    assert "resource" in resources
    assert len(resources["resource"]) == 1
    
    # Test resource retrieval
    result = await registry.get_resource("resource", "test://uri")
    assert result["uri"] == "test://uri"

@pytest.mark.asyncio
async def test_tool_provider(registry, tool_plugin):
    """Test tool provider functionality."""
    await registry.register_plugin(tool_plugin)
    
    # Test tool listing
    tools = registry.get_tools()
    assert "tool" in tools
    assert len(tools["tool"]) == 1
    
    # Test tool execution
    result = await registry.execute_tool("tool", "test", {})
    assert result["result"] == "success"

@pytest.mark.asyncio
async def test_plugin_discovery(registry, tmp_path):
    """Test plugin discovery and loading."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    
    # Create test plugin
    test_dir = plugin_dir / "test"
    test_dir.mkdir()
    
    with open(test_dir / "plugin.json", "w") as f:
        json.dump({
            "name": "test",
            "version": "1.0.0",
            "description": "Test Plugin",
            "author": "Test"
        }, f)
    
    registry.add_plugin_directory(plugin_dir)
    
    with patch("deepseek_engineer.mcp.loader.PluginLoader._load_plugin_module") as mock_load:
        mock_load.return_value = TestPlugin
        await registry.discover_and_load()
    
    assert "test" in registry.plugins
    assert registry.get_plugin_state("test") == PluginState.ACTIVE

@pytest.mark.asyncio
async def test_plugin_dependencies(registry, test_plugin, tool_plugin):
    """Test plugin dependency handling."""
    # Register dependency first
    await registry.register_plugin(test_plugin)
    
    # Add dependency to tool plugin
    tool_plugin.dependencies.add(test_plugin.metadata.name)
    await registry.register_plugin(tool_plugin)
    
    # Unregistering dependency should fail while dependent is active
    with pytest.raises(Exception):
        await registry.unregister_plugin(test_plugin.metadata.name)

@pytest.mark.asyncio
async def test_registry_shutdown(registry, test_plugin, tool_plugin):
    """Test registry shutdown."""
    await registry.register_plugin(test_plugin)
    await registry.register_plugin(tool_plugin)
    
    await registry.shutdown()
    
    assert len(registry.plugins) == 0
    assert len(registry.get_active_plugins()) == 0

def test_plugin_info():
    """Test PluginInfo creation and state tracking."""
    metadata = create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test",
        author="Test"
    )
    plugin = LoadedPlugin(
        metadata=metadata,
        instance=TestPlugin(metadata),
        path=Path("/test"),
        dependencies=set()
    )
    
    info = PluginInfo(
        loaded=plugin,
        state=PluginState.REGISTERED
    )
    
    assert info.state == PluginState.REGISTERED
    assert info.error is None
    assert isinstance(info.last_state_change, datetime)

@pytest.mark.asyncio
async def test_capability_caching(registry, resource_plugin, tool_plugin):
    """Test capability caching behavior."""
    await registry.register_plugin(resource_plugin)
    
    # First call should cache
    resources1 = registry.get_resources()
    resources2 = registry.get_resources()
    assert resources1 is resources2
    
    # Registration should clear cache
    await registry.register_plugin(tool_plugin)
    tools = registry.get_tools()
    assert "tool" in tools

@pytest.mark.asyncio
async def test_error_handling(registry):
    """Test error handling in various operations."""
    # Test invalid plugin name
    with pytest.raises(PluginError):
        await registry.execute_tool("nonexistent", "test", {})
    
    with pytest.raises(PluginError):
        await registry.get_resource("nonexistent", "test://uri")
    
    # Test duplicate registration
    metadata = create_plugin_metadata(
        name="duplicate",
        version="1.0.0",
        description="Test",
        author="Test"
    )
    plugin = LoadedPlugin(
        metadata=metadata,
        instance=TestPlugin(metadata),
        path=Path("/test"),
        dependencies=set()
    )
    
    await registry.register_plugin(plugin)
    with pytest.raises(PluginError):
        await registry.register_plugin(plugin)