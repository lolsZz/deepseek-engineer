"""Tests for the MCP manager."""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, call
import asyncio

from deepseek_engineer.mcp.manager import MCPManager
from deepseek_engineer.mcp.base import (
    MCPPlugin,
    ResourceProvider,
    ToolProvider,
    PluginMetadata,
    create_plugin_metadata
)
from deepseek_engineer.mcp.config import PluginConfigSchema
from deepseek_engineer.mcp.registry import PluginState

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
def temp_plugin_dir(tmp_path):
    """Create a temporary plugin directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    return plugin_dir

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
async def mcp_manager(temp_plugin_dir, temp_config_dir):
    """Create an MCP manager instance."""
    manager = MCPManager(
        plugin_dirs=[temp_plugin_dir],
        config_dir=temp_config_dir
    )
    yield manager
    await manager.shutdown()

@pytest.fixture
def test_plugin_metadata():
    """Create test plugin metadata."""
    return create_plugin_metadata(
        name="test",
        version="1.0.0",
        description="Test Plugin",
        author="Test"
    )

@pytest.fixture
def test_plugin_schema():
    """Create test plugin schema."""
    return PluginConfigSchema(
        type="object",
        properties={
            "setting": {"type": "string"}
        }
    )

@pytest.mark.asyncio
async def test_initialization(mcp_manager, temp_plugin_dir):
    """Test plugin system initialization."""
    # Create test plugin
    plugin_dir = temp_plugin_dir / "test"
    plugin_dir.mkdir()
    
    with patch("deepseek_engineer.mcp.loader.PluginLoader._load_plugin_module") as mock_load:
        mock_load.return_value = TestPlugin
        await mcp_manager.initialize()
    
    assert len(mcp_manager.get_active_plugins()) >= 0

@pytest.mark.asyncio
async def test_plugin_configuration(mcp_manager, test_plugin_metadata, test_plugin_schema):
    """Test plugin configuration management."""
    # Register schema
    mcp_manager.register_plugin_schema("test", test_plugin_schema)
    
    # Set configuration
    config = {"setting": "value"}
    mcp_manager.configure_plugin("test", config)
    
    # Get configuration
    loaded_config = mcp_manager.get_plugin_config("test")
    assert loaded_config == config
    
    # Get schema
    schema = mcp_manager.get_plugin_schema("test")
    assert schema == test_plugin_schema

@pytest.mark.asyncio
async def test_resource_handling(mcp_manager):
    """Test resource provider functionality."""
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.get_resources") as mock_resources:
        mock_resources.return_value = {
            "test": [{"name": "test_resource"}]
        }
        
        resources = mcp_manager.get_available_resources()
        assert "test" in resources
        assert resources["test"][0]["name"] == "test_resource"

@pytest.mark.asyncio
async def test_tool_handling(mcp_manager):
    """Test tool provider functionality."""
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.get_tools") as mock_tools:
        mock_tools.return_value = {
            "test": [{"name": "test_tool"}]
        }
        
        tools = mcp_manager.get_available_tools()
        assert "test" in tools
        assert tools["test"][0]["name"] == "test_tool"

@pytest.mark.asyncio
async def test_plugin_state_management(mcp_manager):
    """Test plugin state management."""
    # Mock state changes
    states = []
    
    def state_listener(name, state, error):
        states.append((name, state))
    
    mcp_manager.add_plugin_state_listener("test", state_listener)
    
    # Simulate state changes through registry
    await mcp_manager.registry._set_plugin_state("test", PluginState.INITIALIZING)
    await mcp_manager.registry._set_plugin_state("test", PluginState.ACTIVE)
    
    assert ("test", PluginState.INITIALIZING) in states
    assert ("test", PluginState.ACTIVE) in states
    
    # Remove listener
    mcp_manager.remove_plugin_state_listener("test", state_listener)
    await mcp_manager.registry._set_plugin_state("test", PluginState.STOPPED)
    assert len(states) == 2  # No new states added

@pytest.mark.asyncio
async def test_tool_execution(mcp_manager):
    """Test tool execution."""
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.execute_tool") as mock_execute:
        mock_execute.return_value = {"result": "success"}
        
        result = await mcp_manager.execute_tool(
            "test",
            "test_tool",
            {"arg": "value"}
        )
        assert result["result"] == "success"

@pytest.mark.asyncio
async def test_resource_access(mcp_manager):
    """Test resource access."""
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.get_resource") as mock_get:
        mock_get.return_value = {"data": "test"}
        
        result = await mcp_manager.get_resource("test", "test://uri")
        assert result["data"] == "test"

@pytest.mark.asyncio
async def test_plugin_reload(mcp_manager):
    """Test plugin reloading."""
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.reload_plugin") as mock_reload:
        await mcp_manager.reload_plugin("test")
        mock_reload.assert_called_once_with("test")

def test_plugin_config_clearing(mcp_manager):
    """Test configuration clearing."""
    with patch("deepseek_engineer.mcp.config.ConfigurationManager.clear_config") as mock_clear:
        mcp_manager.clear_plugin_config("test")
        mock_clear.assert_called_once_with("test")

@pytest.mark.asyncio
async def test_error_handling(mcp_manager):
    """Test error handling in manager operations."""
    # Test initialization error
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.discover_and_load",
              side_effect=Exception("Init error")):
        with pytest.raises(Exception):
            await mcp_manager.initialize()
    
    # Test shutdown error
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.shutdown",
              side_effect=Exception("Shutdown error")):
        with pytest.raises(Exception):
            await mcp_manager.shutdown()

@pytest.mark.asyncio
async def test_plugin_directory_management(mcp_manager):
    """Test plugin directory management."""
    new_dir = Path("/test/plugins")
    mcp_manager.add_plugin_directory(new_dir)
    
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.discover_and_load") as mock_discover:
        await mcp_manager.initialize()
        mock_discover.assert_called_once()

@pytest.mark.asyncio
async def test_plugin_listing(mcp_manager):
    """Test plugin listing functionality."""
    with patch("deepseek_engineer.mcp.registry.PluginRegistry.list_plugins") as mock_list:
        mock_list.return_value = [
            create_plugin_metadata(
                name="test1",
                version="1.0.0",
                description="Test 1",
                author="Test"
            ),
            create_plugin_metadata(
                name="test2",
                version="1.0.0",
                description="Test 2",
                author="Test"
            )
        ]
        
        plugins = mcp_manager.list_plugins()
        assert len(plugins) == 2
        assert plugins[0].name == "test1"
        assert plugins[1].name == "test2"