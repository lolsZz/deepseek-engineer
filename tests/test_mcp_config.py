"""Tests for the MCP configuration system."""

import pytest
import os
from pathlib import Path
import json
import yaml
from unittest.mock import patch

from deepseek_engineer.mcp.config import (
    ConfigurationManager,
    PluginConfigSchema,
    ConfigError,
    ConfigValidationError
)

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary configuration directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def config_manager(temp_config_dir):
    """Create a configuration manager with test directory."""
    return ConfigurationManager(config_dir=temp_config_dir)

@pytest.fixture
def test_schema():
    """Create a test configuration schema."""
    return PluginConfigSchema(
        type="object",
        properties={
            "host": {"type": "string"},
            "port": {"type": "integer"},
            "debug": {"type": "boolean"},
            "settings": {
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer"},
                    "retries": {"type": "integer"}
                }
            }
        },
        required=["host", "port"]
    )

def test_schema_creation():
    """Test configuration schema creation and serialization."""
    schema = PluginConfigSchema(
        type="object",
        properties={"test": {"type": "string"}},
        required=["test"]
    )
    
    # Test conversion to dict
    schema_dict = schema.to_dict()
    assert schema_dict["type"] == "object"
    assert "test" in schema_dict["properties"]
    assert schema_dict["required"] == ["test"]
    
    # Test creation from dict
    new_schema = PluginConfigSchema.from_dict(schema_dict)
    assert new_schema.type == schema.type
    assert new_schema.properties == schema.properties
    assert new_schema.required == schema.required

def test_config_validation(config_manager, test_schema):
    """Test configuration validation against schema."""
    config_manager.register_schema("test", test_schema)
    
    # Valid configuration
    valid_config = {
        "host": "localhost",
        "port": 8080,
        "debug": True,
        "settings": {
            "timeout": 30,
            "retries": 3
        }
    }
    config_manager.set_config("test", valid_config)
    
    # Invalid configuration (missing required field)
    invalid_config = {
        "host": "localhost",
        "debug": True
    }
    with pytest.raises(ConfigValidationError):
        config_manager.set_config("test", invalid_config)
    
    # Invalid configuration (wrong type)
    invalid_config = {
        "host": "localhost",
        "port": "8080"  # Should be integer
    }
    with pytest.raises(ConfigValidationError):
        config_manager.set_config("test", invalid_config)

def test_config_persistence(config_manager, test_schema):
    """Test configuration persistence to file."""
    config_manager.register_schema("test", test_schema)
    
    test_config = {
        "host": "localhost",
        "port": 8080
    }
    
    # Save configuration
    config_manager.set_config("test", test_config)
    
    # Create new manager and load config
    new_manager = ConfigurationManager(config_dir=config_manager.config_dir)
    new_manager.register_schema("test", test_schema)
    loaded_config = new_manager.get_config("test")
    
    assert loaded_config == test_config

def test_yaml_config(config_manager, test_schema):
    """Test YAML configuration handling."""
    config_manager.register_schema("test", test_schema)
    
    # Create YAML config file
    config_path = config_manager.config_dir / "test.yaml"
    test_config = {
        "host": "localhost",
        "port": 8080
    }
    
    with open(config_path, "w") as f:
        yaml.safe_dump(test_config, f)
    
    # Load configuration
    loaded_config = config_manager.get_config("test")
    assert loaded_config == test_config

def test_environment_overrides(config_manager, test_schema):
    """Test environment variable configuration overrides."""
    config_manager.register_schema("test", test_schema)
    
    base_config = {
        "host": "localhost",
        "port": 8080
    }
    config_manager.set_config("test", base_config)
    
    # Override with environment variables
    with patch.dict(os.environ, {
        "DEEPSEEK_PLUGIN_TEST_HOST": "example.com",
        "DEEPSEEK_PLUGIN_TEST_PORT": "9090",
        "DEEPSEEK_PLUGIN_TEST_SETTINGS_TIMEOUT": "60"
    }):
        config = config_manager.get_config("test")
        assert config["host"] == "example.com"
        assert config["port"] == 9090
        assert config["settings"]["timeout"] == 60

def test_nested_config(config_manager):
    """Test handling of nested configuration structures."""
    schema = PluginConfigSchema(
        type="object",
        properties={
            "database": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "credentials": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string"},
                            "password": {"type": "string"}
                        }
                    }
                }
            }
        }
    )
    
    config_manager.register_schema("nested", schema)
    
    config = {
        "database": {
            "host": "localhost",
            "credentials": {
                "username": "user",
                "password": "pass"
            }
        }
    }
    
    config_manager.set_config("nested", config)
    loaded = config_manager.get_config("nested")
    assert loaded == config

def test_config_updates(config_manager, test_schema):
    """Test configuration updates."""
    config_manager.register_schema("test", test_schema)
    
    # Initial config
    config1 = {
        "host": "localhost",
        "port": 8080
    }
    config_manager.set_config("test", config1)
    
    # Update config
    config2 = {
        "host": "example.com",
        "port": 9090
    }
    config_manager.set_config("test", config2)
    
    loaded = config_manager.get_config("test")
    assert loaded == config2

def test_config_clearing(config_manager, test_schema):
    """Test configuration clearing."""
    config_manager.register_schema("test", test_schema)
    
    config = {
        "host": "localhost",
        "port": 8080
    }
    config_manager.set_config("test", config)
    
    # Clear single config
    config_manager.clear_config("test")
    assert config_manager.get_config("test") == {}
    
    # Clear all configs
    config_manager.set_config("test", config)
    config_manager.clear_all_configs()
    assert config_manager.get_config("test") == {}

def test_error_handling(config_manager):
    """Test configuration error handling."""
    # Test unregistered schema
    with pytest.raises(ConfigError):
        config_manager.set_config("unknown", {})
    
    # Test invalid config file
    config_path = config_manager.config_dir / "invalid.yaml"
    with open(config_path, "w") as f:
        f.write("invalid: yaml: content")
    
    # Should not raise exception but log error
    config_manager.register_schema("invalid", PluginConfigSchema())
    config = config_manager.get_config("invalid")
    assert config == {}

def test_schema_listing(config_manager, test_schema):
    """Test listing of registered schemas."""
    config_manager.register_schema("test1", test_schema)
    config_manager.register_schema("test2", test_schema)
    
    plugins = config_manager.list_plugins()
    assert "test1" in plugins
    assert "test2" in plugins

def test_config_isolation(config_manager, test_schema):
    """Test configuration isolation between plugins."""
    config_manager.register_schema("plugin1", test_schema)
    config_manager.register_schema("plugin2", test_schema)
    
    config1 = {
        "host": "host1",
        "port": 8081
    }
    config2 = {
        "host": "host2",
        "port": 8082
    }
    
    config_manager.set_config("plugin1", config1)
    config_manager.set_config("plugin2", config2)
    
    assert config_manager.get_config("plugin1") == config1
    assert config_manager.get_config("plugin2") == config2