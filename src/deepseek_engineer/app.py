"""Main application class for DeepSeek Engineer."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from .core.file_manager import FileManager
from .core.api_client import DeepSeekClient
from .core.conversation_manager import ConversationManager
from .core.security_manager import SecurityManager
from .core.monitoring import MonitoringSystem

@dataclass
class AppConfig:
    """Application configuration."""
    api_key: str
    base_path: Path
    max_tokens: int = 8000
    conversation_persist_path: Optional[Path] = None
    security_config_path: Optional[Path] = None
    log_path: Optional[Path] = None

class DeepSeekEngineer:
    """Main application class integrating all components."""
    
    def __init__(self, config: AppConfig):
        """Initialize DeepSeek Engineer application."""
        self.config = config
        self.base_path = config.base_path
        
        # Initialize monitoring first to track component initialization
        self.monitoring = MonitoringSystem(log_path=config.log_path)
        
        with self.monitoring.measure_time("app_initialization"):
            try:
                # Initialize core components
                self.security = SecurityManager(config_path=config.security_config_path)
                self.file_manager = FileManager(base_path=config.base_path)
                self.api_client = DeepSeekClient(api_key=config.api_key)
                self.conversation = ConversationManager(
                    max_tokens=config.max_tokens,
                    persist_path=config.conversation_persist_path
                )
                
                # Record successful initialization
                self.monitoring.record_event(
                    "app_initialized",
                    {"base_path": str(config.base_path)}
                )
                
            except Exception as e:
                self.monitoring.record_error(
                    "Initialization failed",
                    error=e,
                    config=str(config)
                )
                raise
    
    @classmethod
    def from_env(cls, base_path: Optional[Path] = None) -> 'DeepSeekEngineer':
        """Create instance from environment variables."""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
        
        config = AppConfig(
            api_key=api_key,
            base_path=base_path or Path.cwd(),
            conversation_persist_path=Path(os.getenv(
                "DEEPSEEK_CONVERSATION_PATH",
                "~/.deepseek/conversation.json"
            )).expanduser(),
            security_config_path=Path(os.getenv(
                "DEEPSEEK_SECURITY_CONFIG",
                "~/.deepseek/security.json"
            )).expanduser(),
            log_path=Path(os.getenv(
                "DEEPSEEK_LOG_PATH",
                "~/.deepseek/deepseek.log"
            )).expanduser()
        )
        
        return cls(config)
    
    def process_request(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user request with security and monitoring.
        
        Args:
            message: User's request message
            context: Optional additional context
            auth_token: Optional authentication token
            
        Returns:
            Response dictionary containing results and any file changes
        """
        with self.monitoring.measure_time("request_processing"):
            try:
                # Validate authentication
                self.security.validate_auth_token(auth_token)
                
                # Add context to conversation
                if context:
                    self.conversation.add_message(
                        "system",
                        str(context)
                    )
                
                # Add user message
                self.conversation.add_message(
                    "user",
                    message
                )
                
                # Get conversation context
                chat_context = self.conversation.get_context()
                
                # Get API response
                response = self.api_client.structured_chat(
                    messages=chat_context,
                    response_schema={
                        "type": "object",
                        "properties": {
                            "response": {"type": "string"},
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "content": {"type": "string"},
                                        "operation": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                )
                
                # Process any file operations
                file_changes = []
                for file_op in response.get("files", []):
                    path = file_op["path"]
                    content = file_op["content"]
                    operation = file_op["operation"]
                    
                    # Validate path and content
                    self.security.validate_path(Path(path))
                    self.security.validate_content(content)
                    
                    # Perform operation
                    if operation == "write":
                        self.file_manager.write_file(path, content)
                    elif operation == "append":
                        current = self.file_manager.read_file(path)
                        self.file_manager.write_file(path, current + content)
                    elif operation == "modify":
                        self.file_manager.apply_diff(
                            path,
                            file_op.get("original", ""),
                            content
                        )
                    
                    file_changes.append({
                        "path": path,
                        "operation": operation,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Add assistant response to conversation
                self.conversation.add_message(
                    "assistant",
                    response["response"]
                )
                
                result = {
                    "response": response["response"],
                    "file_changes": file_changes
                }
                
                # Record successful request
                self.monitoring.record_event(
                    "request_completed",
                    {
                        "message_length": len(message),
                        "response_length": len(response["response"]),
                        "file_changes": len(file_changes)
                    }
                )
                
                return result
                
            except Exception as e:
                self.monitoring.record_error(
                    "Request processing failed",
                    error=e,
                    message=message
                )
                raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "system_status": self.monitoring.get_system_status(),
            "conversation_summary": self.conversation.get_conversation_summary(),
            "security_status": {
                "auth_required": self.security.config.require_auth,
                "rate_limit_config": {
                    "window": self.security.config.rate_limit_window,
                    "max_requests": self.security.config.rate_limit_max_requests
                }
            }
        }
    
    def export_metrics(self, path: Path):
        """Export monitoring metrics to file."""
        self.monitoring.export_metrics(path)
    
    def export_events(self, path: Path):
        """Export monitoring events to file."""
        self.monitoring.export_events(path)
    
    def clear_conversation(self, keep_system: bool = True):
        """Clear conversation history."""
        self.conversation.clear_context(keep_system=keep_system)
    
    def generate_auth_token(self) -> str:
        """Generate new authentication token."""
        return self.security.generate_auth_token()
    
    def revoke_auth_token(self, token: str):
        """Revoke an authentication token."""
        self.security.revoke_auth_token(token)