"""Tests for the DeepSeek Engineer CLI interface."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
import argparse
import os
from io import StringIO

from deepseek_engineer.main import (
    create_arg_parser,
    display_status,
    handle_file_changes,
    main
)
from deepseek_engineer.app import DeepSeekEngineer
from deepseek_engineer.core.security_manager import SecurityViolation

@pytest.fixture
def mock_console():
    """Mock rich console output."""
    with patch('deepseek_engineer.main.console') as mock:
        yield mock

@pytest.fixture
def mock_app():
    """Create mock DeepSeekEngineer instance."""
    with patch('deepseek_engineer.main.DeepSeekEngineer') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield mock_instance

def test_argument_parser():
    """Test command line argument parsing."""
    parser = create_arg_parser()
    
    # Test with all arguments
    args = parser.parse_args([
        '--base-path', '/test/path',
        '--api-key', 'test_key',
        '--conversation-path', '/test/conversation.json',
        '--security-config', '/test/security.json',
        '--log-path', '/test/app.log',
        '--max-tokens', '1000',
        '--export-metrics', '/test/metrics.json',
        '--export-events', '/test/events.json'
    ])
    
    assert args.base_path == Path('/test/path')
    assert args.api_key == 'test_key'
    assert args.conversation_path == Path('/test/conversation.json')
    assert args.security_config == Path('/test/security.json')
    assert args.log_path == Path('/test/app.log')
    assert args.max_tokens == 1000
    assert args.export_metrics == Path('/test/metrics.json')
    assert args.export_events == Path('/test/events.json')

def test_display_status(mock_console):
    """Test status display formatting."""
    mock_app = Mock()
    mock_app.get_status.return_value = {
        "system_status": {
            "system_metrics": {
                "cpu_percent": 50.0,
                "memory_percent": 60.0
            }
        },
        "conversation_summary": {
            "message_count": 10,
            "total_tokens": 1000
        },
        "security_status": {
            "auth_required": True,
            "rate_limit_config": {
                "window": 60,
                "max_requests": 100
            }
        }
    }
    
    display_status(mock_app)
    
    # Verify console output calls
    assert mock_console.print.called
    calls = mock_console.print.call_args_list
    assert any("System Metrics" in str(call)) 
    assert any("Conversation Summary" in str(call))
    assert any("Security Status" in str(call))

def test_handle_file_changes(mock_console):
    """Test file changes display formatting."""
    changes = [
        {
            "path": "test.py",
            "operation": "write",
            "timestamp": "2025-01-02T16:20:00"
        },
        {
            "path": "config.json",
            "operation": "modify",
            "timestamp": "2025-01-02T16:21:00"
        }
    ]
    
    handle_file_changes(changes)
    
    # Verify table was printed
    assert mock_console.print.called
    table_call = mock_console.print.call_args[0][0]
    assert "File Changes" in str(table_call)
    assert "test.py" in str(table_call)
    assert "config.json" in str(table_call)

@patch('deepseek_engineer.main.Prompt')
def test_main_interaction_loop(mock_prompt, mock_app, mock_console):
    """Test main interaction loop."""
    # Mock user inputs
    mock_prompt.ask.side_effect = [
        "test command",  # Normal command
        "status",        # Status command
        "clear",         # Clear command
        "exit"          # Exit command
    ]
    
    # Mock app responses
    mock_app.process_request.return_value = {
        "response": "Test response",
        "file_changes": []
    }
    mock_app.security.config.require_auth = True
    mock_app.generate_auth_token.return_value = "test_token"
    
    # Run main
    with patch('deepseek_engineer.main.DeepSeekEngineer', return_value=mock_app):
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            main()
    
    # Verify interactions
    assert mock_app.process_request.called
    assert mock_app.get_status.called
    assert mock_app.clear_conversation.called

@patch('deepseek_engineer.main.Prompt')
def test_main_error_handling(mock_prompt, mock_app, mock_console):
    """Test error handling in main loop."""
    # Mock user inputs
    mock_prompt.ask.side_effect = [
        "test command",  # Raises SecurityViolation
        "bad command",   # Raises general Exception
        "exit"
    ]
    
    # Mock app responses
    mock_app.process_request.side_effect = [
        SecurityViolation("Access denied"),
        Exception("General error")
    ]
    mock_app.security.config.require_auth = False
    
    # Run main
    with patch('deepseek_engineer.main.DeepSeekEngineer', return_value=mock_app):
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            main()
    
    # Verify error messages
    error_messages = [
        call_args[0][0] for call_args in mock_console.print.call_args_list
        if "Error" in str(call_args[0][0])
    ]
    assert any("Security Error" in str(msg) for msg in error_messages)
    assert any("Error: General error" in str(msg) for msg in error_messages)

def test_main_export_commands(mock_app, mock_console):
    """Test metric and event export commands."""
    # Test metrics export
    with patch('sys.argv', ['deepseek', '--export-metrics', '/test/metrics.json']):
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            main()
    mock_app.export_metrics.assert_called_once()
    
    # Reset mock
    mock_app.reset_mock()
    
    # Test events export
    with patch('sys.argv', ['deepseek', '--export-events', '/test/events.json']):
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            main()
    mock_app.export_events.assert_called_once()

def test_main_keyboard_interrupt(mock_app, mock_console):
    """Test handling of keyboard interrupt."""
    with patch('deepseek_engineer.main.Prompt.ask', side_effect=KeyboardInterrupt):
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test_key'}):
            main()
    
    # Verify graceful exit message
    assert any(
        "Interrupted" in str(call_args[0][0])
        for call_args in mock_console.print.call_args_list
    )

def test_main_missing_api_key(mock_console):
    """Test handling of missing API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit):
            main()
    
    # Verify error message
    error_calls = [
        call_args[0][0] for call_args in mock_console.print.call_args_list
        if "Error" in str(call_args[0][0])
    ]
    assert any("API key" in str(msg) for msg in error_calls)