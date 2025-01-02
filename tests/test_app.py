"""Tests for the DeepSeek Engineer application class."""

import pytest
from pathlib import Path
import os
from unittest.mock import Mock, patch, ANY
from datetime import datetime

from deepseek_engineer.app import DeepSeekEngineer, AppConfig
from deepseek_engineer.core.security_manager import AccessDenied

@pytest.fixture
def mock_components():
    """Mock all core components."""
    with patch('deepseek_engineer.app.FileManager') as mock_file_manager, \
         patch('deepseek_engineer.app.DeepSeekClient') as mock_api_client, \
         patch('deepseek_engineer.app.ConversationManager') as mock_conversation, \
         patch('deepseek_engineer.app.SecurityManager') as mock_security, \
         patch('deepseek_engineer.app.MonitoringSystem') as mock_monitoring:
        yield {
            'file_manager': mock_file_manager,
            'api_client': mock_api_client,
            'conversation': mock_conversation,
            'security': mock_security,
            'monitoring': mock_monitoring
        }

@pytest.fixture
def app_config(tmp_path):
    """Create test application configuration."""
    return AppConfig(
        api_key="test_key",
        base_path=tmp_path,
        conversation_persist_path=tmp_path / "conversation.json",
        security_config_path=tmp_path / "security.json",
        log_path=tmp_path / "app.log"
    )

@pytest.fixture
def app(app_config, mock_components):
    """Create test application instance."""
    return DeepSeekEngineer(app_config)

def test_initialization(app_config, mock_components):
    """Test application initialization."""
    app = DeepSeekEngineer(app_config)
    
    # Verify all components were initialized
    mock_components['file_manager'].assert_called_once_with(base_path=app_config.base_path)
    mock_components['api_client'].assert_called_once_with(api_key=app_config.api_key)
    mock_components['conversation'].assert_called_once()
    mock_components['security'].assert_called_once()
    mock_components['monitoring'].assert_called_once()

def test_from_env():
    """Test creating application from environment variables."""
    with patch.dict(os.environ, {
        'DEEPSEEK_API_KEY': 'test_key',
        'DEEPSEEK_CONVERSATION_PATH': '/tmp/conv.json',
        'DEEPSEEK_SECURITY_CONFIG': '/tmp/security.json',
        'DEEPSEEK_LOG_PATH': '/tmp/app.log'
    }):
        app = DeepSeekEngineer.from_env()
        assert app.config.api_key == 'test_key'

def test_process_request(app, mock_components):
    """Test processing a user request."""
    # Setup mock responses
    mock_components['security'].return_value.validate_auth_token.return_value = True
    mock_components['conversation'].return_value.get_context.return_value = [
        {"role": "user", "content": "test message"}
    ]
    mock_components['api_client'].return_value.structured_chat.return_value = {
        "response": "Test response",
        "files": [{
            "path": "test.txt",
            "content": "test content",
            "operation": "write"
        }]
    }
    
    # Process request
    result = app.process_request(
        message="test message",
        context={"test": "context"},
        auth_token="test_token"
    )
    
    # Verify response
    assert result["response"] == "Test response"
    assert len(result["file_changes"]) == 1
    assert result["file_changes"][0]["path"] == "test.txt"
    
    # Verify component interactions
    mock_components['security'].return_value.validate_auth_token.assert_called_once_with("test_token")
    mock_components['conversation'].return_value.add_message.assert_called()
    mock_components['api_client'].return_value.structured_chat.assert_called_once()
    mock_components['file_manager'].return_value.write_file.assert_called_once()

def test_process_request_auth_failure(app, mock_components):
    """Test request processing with authentication failure."""
    mock_components['security'].return_value.validate_auth_token.side_effect = AccessDenied("Invalid token")
    
    with pytest.raises(AccessDenied):
        app.process_request("test", auth_token="invalid_token")

def test_process_request_with_file_operations(app, mock_components):
    """Test request processing with different file operations."""
    mock_components['security'].return_value.validate_auth_token.return_value = True
    mock_components['api_client'].return_value.structured_chat.return_value = {
        "response": "Test response",
        "files": [
            {
                "path": "test1.txt",
                "content": "new content",
                "operation": "write"
            },
            {
                "path": "test2.txt",
                "content": "appended content",
                "operation": "append"
            },
            {
                "path": "test3.txt",
                "content": "modified content",
                "operation": "modify",
                "original": "original content"
            }
        ]
    }
    
    # Mock file manager methods
    mock_file_manager = mock_components['file_manager'].return_value
    mock_file_manager.read_file.return_value = "existing content"
    
    result = app.process_request("test message")
    
    # Verify file operations
    assert len(result["file_changes"]) == 3
    mock_file_manager.write_file.assert_called()
    mock_file_manager.apply_diff.assert_called()

def test_get_status(app, mock_components):
    """Test getting system status."""
    # Setup mock responses
    mock_components['monitoring'].return_value.get_system_status.return_value = {
        "system_metrics": {"cpu": 50}
    }
    mock_components['conversation'].return_value.get_conversation_summary.return_value = {
        "message_count": 10
    }
    mock_components['security'].return_value.config.require_auth = True
    mock_components['security'].return_value.config.rate_limit_window = 60
    mock_components['security'].return_value.config.rate_limit_max_requests = 100
    
    status = app.get_status()
    
    assert "system_status" in status
    assert "conversation_summary" in status
    assert "security_status" in status
    assert status["security_status"]["auth_required"] is True

def test_export_functions(app, mock_components):
    """Test metric and event export functions."""
    export_path = Path("test_export.json")
    
    app.export_metrics(export_path)
    mock_components['monitoring'].return_value.export_metrics.assert_called_once_with(export_path)
    
    app.export_events(export_path)
    mock_components['monitoring'].return_value.export_events.assert_called_once_with(export_path)

def test_conversation_management(app, mock_components):
    """Test conversation management functions."""
    app.clear_conversation(keep_system=True)
    mock_components['conversation'].return_value.clear_context.assert_called_once_with(keep_system=True)

def test_auth_token_management(app, mock_components):
    """Test authentication token management."""
    mock_components['security'].return_value.generate_auth_token.return_value = "new_token"
    
    token = app.generate_auth_token()
    assert token == "new_token"
    
    app.revoke_auth_token(token)
    mock_components['security'].return_value.revoke_auth_token.assert_called_once_with(token)

def test_error_handling(app, mock_components):
    """Test error handling in request processing."""
    # Mock API error
    mock_components['api_client'].return_value.structured_chat.side_effect = Exception("API Error")
    
    with pytest.raises(Exception):
        app.process_request("test message")
    
    # Verify error was recorded
    mock_components['monitoring'].return_value.record_error.assert_called_once()

def test_monitoring_integration(app, mock_components):
    """Test monitoring integration during request processing."""
    mock_monitoring = mock_components['monitoring'].return_value
    
    # Process request
    app.process_request("test message")
    
    # Verify monitoring calls
    assert mock_monitoring.measure_time.called
    assert mock_monitoring.record_event.called

def test_security_validation(app, mock_components):
    """Test security validations during request processing."""
    mock_security = mock_components['security'].return_value
    mock_components['api_client'].return_value.structured_chat.return_value = {
        "response": "Test",
        "files": [{
            "path": "test.txt",
            "content": "content",
            "operation": "write"
        }]
    }
    
    app.process_request("test message")
    
    # Verify security checks
    assert mock_security.validate_path.called
    assert mock_security.validate_content.called