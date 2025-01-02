"""Plugin configuration management system."""

import os
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import jsonschema
from jsonschema import validate, ValidationError
import yaml
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

@dataclass
class PluginConfigSchema:
    """Schema for plugin configuration."""
    type: str = "object"
    properties: Dict[str, Dict[str, Any]] = None
    required: List[str] = None
    additionalProperties: bool = False
    
    def __post_init__(self):
        """Initialize with defaults if needed."""
        if self.properties is None:
            self.properties = {}
        if self.required is None:
            self.required = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary format."""
        schema = {
            "type": self.type,
            "properties": self.properties,
            "additionalProperties": self.additionalProperties
        }
        if self.required:
            schema["required"] = self.required
        return schema
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfigSchema':
        """Create schema from dictionary format."""
        return cls(
            type=data.get("type", "object"),
            properties=data.get("properties", {}),
            required=data.get("required", []),
            additionalProperties=data.get("additionalProperties", False)
        )

class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass

class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass

class ConfigurationManager:
    """Manages plugin configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Optional directory for configuration files
        """
        self.config_dir = config_dir or Path.home() / ".deepseek" / "plugins"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._schemas: Dict[str, PluginConfigSchema] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._env_prefix = "DEEPSEEK_PLUGIN_"
    
    def register_schema(self, plugin_name: str, schema: PluginConfigSchema):
        """
        Register configuration schema for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            schema: Configuration schema
        """
        self._schemas[plugin_name] = schema
        
        # Load existing configuration if available
        self.load_config(plugin_name)
    
    def set_config(self, plugin_name: str, config: Dict[str, Any]):
        """
        Set and validate configuration for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            config: Configuration data
            
        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if plugin_name not in self._schemas:
            raise ConfigError(f"No schema registered for plugin {plugin_name}")
        
        # Validate configuration
        try:
            validate(
                instance=config,
                schema=self._schemas[plugin_name].to_dict()
            )
        except ValidationError as e:
            raise ConfigValidationError(f"Invalid configuration: {str(e)}")
        
        self._configs[plugin_name] = deepcopy(config)
        
        # Save configuration
        self.save_config(plugin_name)
    
    def get_config(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get configuration for a plugin.
        
        Args:
            plugin_name: Name of the plugin
            
        Returns:
            Plugin configuration
        """
        if plugin_name not in self._configs:
            self.load_config(plugin_name)
        return deepcopy(self._configs.get(plugin_name, {}))
    
    def load_config(self, plugin_name: str):
        """
        Load configuration from file and environment.
        
        Args:
            plugin_name: Name of the plugin
        """
        config = {}
        
        # Load from file
        config_file = self._get_config_path(plugin_name)
        if config_file.exists():
            try:
                if config_file.suffix == '.yaml':
                    with open(config_file) as f:
                        config = yaml.safe_load(f)
                else:
                    with open(config_file) as f:
                        config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading config for {plugin_name}: {str(e)}")
        
        # Override with environment variables
        config = self._apply_env_overrides(plugin_name, config)
        
        # Validate if schema exists
        if plugin_name in self._schemas:
            try:
                validate(
                    instance=config,
                    schema=self._schemas[plugin_name].to_dict()
                )
            except ValidationError as e:
                logger.error(f"Invalid configuration for {plugin_name}: {str(e)}")
                config = {}
        
        self._configs[plugin_name] = config
    
    def save_config(self, plugin_name: str):
        """
        Save configuration to file.
        
        Args:
            plugin_name: Name of the plugin
        """
        if plugin_name not in self._configs:
            return
            
        config_file = self._get_config_path(plugin_name)
        try:
            if config_file.suffix == '.yaml':
                with open(config_file, 'w') as f:
                    yaml.safe_dump(self._configs[plugin_name], f)
            else:
                with open(config_file, 'w') as f:
                    json.dump(self._configs[plugin_name], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config for {plugin_name}: {str(e)}")
    
    def _get_config_path(self, plugin_name: str) -> Path:
        """Get path for plugin configuration file."""
        return self.config_dir / f"{plugin_name}.yaml"
    
    def _apply_env_overrides(
        self,
        plugin_name: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            plugin_name: Name of the plugin
            config: Current configuration
            
        Returns:
            Updated configuration
        """
        prefix = f"{self._env_prefix}{plugin_name.upper()}_"
        result = deepcopy(config)
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                
                # Handle nested keys (e.g., PLUGIN_DB_HOST -> db.host)
                parts = config_key.split('_')
                current = result
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Try to parse as JSON, fallback to string
                try:
                    current[parts[-1]] = json.loads(value)
                except json.JSONDecodeError:
                    current[parts[-1]] = value
        
        return result
    
    def get_schema(self, plugin_name: str) -> Optional[PluginConfigSchema]:
        """Get configuration schema for a plugin."""
        return self._schemas.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """Get list of plugins with registered schemas."""
        return list(self._schemas.keys())
    
    def clear_config(self, plugin_name: str):
        """Clear configuration for a plugin."""
        if plugin_name in self._configs:
            del self._configs[plugin_name]
            
        config_file = self._get_config_path(plugin_name)
        if config_file.exists():
            config_file.unlink()
    
    def clear_all_configs(self):
        """Clear all plugin configurations."""
        self._configs.clear()
        for config_file in self.config_dir.glob("*.yaml"):
            config_file.unlink()