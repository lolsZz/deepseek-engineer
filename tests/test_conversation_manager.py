"""Tests for the ConversationManager class."""

import pytest
from pathlib import Path
import json
from datetime import datetime, timedelta
from deepseek_engineer.core.conversation_manager import (
    ConversationManager,
    Message,
    TokenCounter
)

@pytest.fixture
def temp_persist_file(tmp_path):
    """Create a temporary file for conversation persistence."""
    return tmp_path / "conversation.json"

@pytest.fixture
def conversation_manager(temp_persist_file):
    """Create a ConversationManager instance with test configuration."""
    return ConversationManager(
        max_tokens=100,
        persist_path=temp_persist_file,
        model="gpt-4"
    )

def test_message_creation():
    """Test Message object creation and serialization."""
    # Create message with minimal args
    msg = Message(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert isinstance(msg.timestamp, datetime)
    assert msg.metadata == {}
    
    # Create message with full args
    timestamp = datetime.now()
    metadata = {"key": "value"}
    msg = Message(
        role="assistant",
        content="Hi",
        timestamp=timestamp,
        metadata=metadata
    )
    assert msg.timestamp == timestamp
    assert msg.metadata == metadata
    
    # Test serialization
    msg_dict = msg.to_dict()
    assert msg_dict["role"] == "assistant"
    assert msg_dict["content"] == "Hi"
    assert msg_dict["timestamp"] == timestamp.isoformat()
    assert msg_dict["metadata"] == metadata
    
    # Test deserialization
    new_msg = Message.from_dict(msg_dict)
    assert new_msg.role == msg.role
    assert new_msg.content == msg.content
    assert new_msg.timestamp == msg.timestamp
    assert new_msg.metadata == msg.metadata

def test_add_message(conversation_manager):
    """Test adding messages to conversation."""
    # Add system message
    system_msg = conversation_manager.add_message(
        "system",
        "System prompt",
        {"type": "initialization"}
    )
    assert conversation_manager.system_message == system_msg
    assert len(conversation_manager.messages) == 0
    
    # Add user message
    user_msg = conversation_manager.add_message(
        "user",
        "Hello",
        {"type": "greeting"}
    )
    assert len(conversation_manager.messages) == 1
    assert conversation_manager.messages[0] == user_msg
    
    # Add assistant message
    assistant_msg = conversation_manager.add_message(
        "assistant",
        "Hi there!",
        {"type": "response"}
    )
    assert len(conversation_manager.messages) == 2
    assert conversation_manager.messages[1] == assistant_msg

def test_context_management(conversation_manager):
    """Test context management and token limiting."""
    # Mock token counter to return predictable values
    conversation_manager.token_counter.count_tokens = lambda x: len(x)
    conversation_manager.token_counter.count_message_tokens = lambda x: len(x.content)
    
    # Add messages up to token limit
    conversation_manager.add_message("system", "S" * 20)
    conversation_manager.add_message("user", "A" * 30)
    conversation_manager.add_message("assistant", "B" * 30)
    conversation_manager.add_message("user", "C" * 40)
    
    # This should trigger context trimming
    conversation_manager.add_message("assistant", "D" * 20)
    
    # Check that oldest messages were removed to stay under limit
    context = conversation_manager.get_context()
    total_tokens = sum(len(msg["content"]) for msg in context)
    assert total_tokens <= conversation_manager.max_tokens

def test_conversation_persistence(temp_persist_file):
    """Test saving and loading conversations."""
    # Create manager and add messages
    manager1 = ConversationManager(persist_path=temp_persist_file)
    manager1.add_message("system", "System prompt")
    manager1.add_message("user", "Hello")
    manager1.add_message("assistant", "Hi there!")
    
    # Save should happen automatically, but we can force it
    manager1.save_conversation()
    
    # Create new manager and load conversation
    manager2 = ConversationManager(persist_path=temp_persist_file)
    assert manager2.system_message.content == "System prompt"
    assert len(manager2.messages) == 2
    assert manager2.messages[0].content == "Hello"
    assert manager2.messages[1].content == "Hi there!"

def test_clear_context(conversation_manager):
    """Test clearing conversation context."""
    # Add some messages
    conversation_manager.add_message("system", "System prompt")
    conversation_manager.add_message("user", "Hello")
    conversation_manager.add_message("assistant", "Hi")
    
    # Clear keeping system message
    conversation_manager.clear_context(keep_system=True)
    assert conversation_manager.system_message is not None
    assert len(conversation_manager.messages) == 0
    
    # Add more messages and clear everything
    conversation_manager.add_message("user", "Test")
    conversation_manager.clear_context(keep_system=False)
    assert conversation_manager.system_message is None
    assert len(conversation_manager.messages) == 0

def test_get_conversation_summary(conversation_manager):
    """Test getting conversation summary statistics."""
    # Add messages with known timestamps
    now = datetime.now()
    conversation_manager.add_message("system", "System")
    conversation_manager.add_message("user", "First", {"timestamp": now - timedelta(hours=1)})
    conversation_manager.add_message("assistant", "Last", {"timestamp": now})
    
    summary = conversation_manager.get_conversation_summary()
    assert summary["message_count"] == 2  # Not counting system message
    assert summary["has_system_message"] is True
    assert summary["total_tokens"] > 0
    
    # Check message timestamps
    assert summary["oldest_message"] <= summary["newest_message"]

def test_token_counter():
    """Test token counting functionality."""
    counter = TokenCounter()
    
    # Test basic token counting
    assert counter.count_tokens("Hello, world!") > 0
    
    # Test message token counting
    msg = Message("user", "Test message")
    tokens = counter.count_message_tokens(msg)
    assert tokens > 0
    assert tokens > counter.count_tokens("Test message")  # Should include role tokens

def test_get_context_with_limit(conversation_manager):
    """Test getting context with specific token limit."""
    conversation_manager.add_message("system", "S" * 20)
    conversation_manager.add_message("user", "A" * 30)
    conversation_manager.add_message("assistant", "B" * 30)
    
    # Get context with custom limit
    context = conversation_manager.get_context(max_tokens=50)
    total_tokens = conversation_manager.token_counter.count_tokens(
        "".join(msg["content"] for msg in context)
    )
    assert total_tokens <= 50

def test_invalid_persistence_path():
    """Test handling of invalid persistence path."""
    # Try to create manager with invalid path
    invalid_path = Path("/nonexistent/path/conversation.json")
    manager = ConversationManager(persist_path=invalid_path)
    
    # Should not raise error on initialization
    assert manager.persist_path == invalid_path
    
    # Should handle save gracefully
    manager.add_message("system", "Test")
    # No exception should be raised