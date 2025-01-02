"""Conversation management and context handling."""

import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import tiktoken
from pathlib import Path

@dataclass
class Message:
    """A single message in the conversation."""
    role: str
    content: str
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary format."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )

class TokenCounter:
    """Handles token counting for different models."""
    
    def __init__(self, model: str = "gpt-4"):
        """Initialize with specific model encoding."""
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.encoding.encode(text))
    
    def count_message_tokens(self, message: Message) -> int:
        """Count tokens in a message including role."""
        return self.count_tokens(message.role) + self.count_tokens(message.content)

class ConversationManager:
    """Manages conversation history and context."""
    
    def __init__(
        self,
        max_tokens: int = 8000,
        persist_path: Optional[Path] = None,
        model: str = "gpt-4"
    ):
        """
        Initialize conversation manager.
        
        Args:
            max_tokens: Maximum tokens to maintain in context
            persist_path: Optional path to persist conversations
            model: Model name for token counting
        """
        self.max_tokens = max_tokens
        self.persist_path = Path(persist_path) if persist_path else None
        self.token_counter = TokenCounter(model)
        self.messages: List[Message] = []
        self.system_message: Optional[Message] = None
        
        # Load persisted conversation if available
        if self.persist_path and self.persist_path.exists():
            self.load_conversation()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """
        Add a new message to the conversation.
        
        Args:
            role: Message role (system/user/assistant)
            content: Message content
            metadata: Optional metadata dictionary
            
        Returns:
            The created Message object
        """
        message = Message(role=role, content=content, metadata=metadata)
        
        if role == "system":
            self.system_message = message
        else:
            self.messages.append(message)
            
        # Trim context if needed
        self._trim_context()
        
        # Persist if enabled
        if self.persist_path:
            self.save_conversation()
            
        return message
    
    def get_context(self, max_tokens: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get current conversation context within token limit.
        
        Args:
            max_tokens: Optional override for max tokens
            
        Returns:
            List of messages in API format
        """
        limit = max_tokens or self.max_tokens
        context: List[Dict[str, str]] = []
        token_count = 0
        
        # Always include system message if present
        if self.system_message:
            system_tokens = self.token_counter.count_message_tokens(self.system_message)
            if system_tokens <= limit:
                context.append({
                    "role": self.system_message.role,
                    "content": self.system_message.content
                })
                token_count += system_tokens
        
        # Add remaining messages up to token limit
        for message in reversed(self.messages):
            msg_tokens = self.token_counter.count_message_tokens(message)
            if token_count + msg_tokens <= limit:
                context.insert(1, {
                    "role": message.role,
                    "content": message.content
                })
                token_count += msg_tokens
            else:
                break
        
        return context
    
    def _trim_context(self):
        """Remove oldest messages if context exceeds token limit."""
        while self.get_total_tokens() > self.max_tokens and self.messages:
            self.messages.pop(0)  # Remove oldest message
    
    def get_total_tokens(self) -> int:
        """Get total tokens in current conversation."""
        total = 0
        if self.system_message:
            total += self.token_counter.count_message_tokens(self.system_message)
        for message in self.messages:
            total += self.token_counter.count_message_tokens(message)
        return total
    
    def clear_context(self, keep_system: bool = True):
        """
        Clear conversation context.
        
        Args:
            keep_system: Whether to keep system message
        """
        if not keep_system:
            self.system_message = None
        self.messages.clear()
        
        if self.persist_path:
            self.save_conversation()
    
    def save_conversation(self):
        """Save conversation to disk if persist_path is set."""
        if not self.persist_path:
            return
            
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "system_message": self.system_message.to_dict() if self.system_message else None,
            "messages": [msg.to_dict() for msg in self.messages]
        }
        
        with open(self.persist_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_conversation(self):
        """Load conversation from disk if persist_path exists."""
        if not self.persist_path or not self.persist_path.exists():
            return
            
        with open(self.persist_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if data.get("system_message"):
            self.system_message = Message.from_dict(data["system_message"])
            
        self.messages = [
            Message.from_dict(msg_data)
            for msg_data in data.get("messages", [])
        ]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the conversation."""
        return {
            "message_count": len(self.messages),
            "total_tokens": self.get_total_tokens(),
            "has_system_message": self.system_message is not None,
            "oldest_message": self.messages[0].timestamp if self.messages else None,
            "newest_message": self.messages[-1].timestamp if self.messages else None
        }