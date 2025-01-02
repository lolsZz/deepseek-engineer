# DeepSeek Integration Guide 🔌

## Overview

DeepSeek Engineer implements a robust integration with DeepSeek's API, leveraging both direct API access and LiteLLM for multi-provider support. This document details our implementation patterns and best practices.

## Core Implementation

### 1. API Integration Options

#### Direct API Access
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)
```

#### LiteLLM Integration
```python
from litellm import completion

response = completion(
    model="deepseek/deepseek-coder",
    messages=[{"role": "user", "content": "Write a Python function"}]
)
```

### 2. Data Models
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class FileOperation(BaseModel):
    """Base class for file operations."""
    path: str = Field(..., description="Path to the target file")

class FileToCreate(FileOperation):
    """Model for file creation operations."""
    content: str = Field(..., description="Complete content of the file")

class FileToEdit(FileOperation):
    """Model for file editing operations."""
    original_snippet: str = Field(..., description="Exact content to be replaced")
    new_snippet: str = Field(..., description="New content to insert")

class AssistantResponse(BaseModel):
    """Model for structured assistant responses."""
    assistant_reply: str = Field(..., description="Main response text")
    files_to_create: Optional[List[FileToCreate]] = Field(default=None)
    files_to_edit: Optional[List[FileToEdit]] = Field(default=None)
```

### 3. Stream Processing
```python
async def stream_response(messages: List[dict], **kwargs) -> AsyncGenerator[str, None]:
    """
    Stream responses from DeepSeek API with proper error handling.
    
    Args:
        messages: List of conversation messages
        **kwargs: Additional API parameters
    
    Yields:
        Chunks of the response text
    """
    try:
        stream = await client.chat.completions.create(
            model="deepseek-coder",
            messages=messages,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        raise StreamError(f"Failed to stream response: {str(e)}")
```

## File Operations

### 1. Context Management
```python
class FileContextManager:
    """Manages file content in conversation context."""
    
    def __init__(self, max_context_size: int = 8192):
        self.max_context_size = max_context_size
        self.context_files: Dict[str, str] = {}
    
    async def add_file(self, path: str) -> bool:
        """
        Add file content to conversation context.
        
        Args:
            path: Path to the file
            
        Returns:
            bool: True if file was added successfully
        """
        try:
            content = await read_file_async(path)
            if self._will_fit_in_context(content):
                self.context_files[path] = content
                return True
            return False
        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            return False
    
    def _will_fit_in_context(self, content: str) -> bool:
        """Check if new content will fit in context budget."""
        current_size = sum(len(c) for c in self.context_files.values())
        return current_size + len(content) <= self.max_context_size
```

### 2. Diff Management
```python
class DiffManager:
    """Manages code modifications with safety checks."""
    
    def preview_changes(self, files_to_edit: List[FileToEdit]) -> Table:
        """Generate rich diff preview table."""
        table = Table(
            title="Proposed Changes",
            show_header=True,
            header_style="bold magenta"
        )
        table.add_column("File", style="cyan")
        table.add_column("Original", style="red")
        table.add_column("New", style="green")
        
        for edit in files_to_edit:
            table.add_row(
                edit.path,
                Syntax(edit.original_snippet, "python", theme="monokai"),
                Syntax(edit.new_snippet, "python", theme="monokai")
            )
        
        return table
    
    async def apply_changes(self, files_to_edit: List[FileToEdit]) -> List[str]:
        """
        Apply changes with validation and backup.
        
        Returns:
            List of modified file paths
        """
        modified_files = []
        
        for edit in files_to_edit:
            try:
                await self._backup_file(edit.path)
                content = await read_file_async(edit.path)
                
                if edit.original_snippet not in content:
                    raise DiffError(f"Original content not found in {edit.path}")
                
                new_content = content.replace(
                    edit.original_snippet,
                    edit.new_snippet,
                    1
                )
                
                await write_file_async(edit.path, new_content)
                modified_files.append(edit.path)
                
            except Exception as e:
                logger.error(f"Failed to apply changes to {edit.path}: {str(e)}")
                await self._restore_backup(edit.path)
                raise
        
        return modified_files
```

## Error Handling

### 1. Custom Exceptions
```python
class DeepSeekError(Exception):
    """Base exception for DeepSeek-related errors."""
    pass

class APIError(DeepSeekError):
    """Raised when API requests fail."""
    pass

class StreamError(DeepSeekError):
    """Raised when streaming fails."""
    pass

class DiffError(DeepSeekError):
    """Raised when diff operations fail."""
    pass
```

### 2. Error Management
```python
class ErrorManager:
    """Manages error handling and recovery."""
    
    def handle_api_error(self, error: Exception) -> AssistantResponse:
        """Convert API errors to user-friendly responses."""
        error_msg = str(error)
        
        if isinstance(error, RateLimitError):
            return AssistantResponse(
                assistant_reply="Rate limit exceeded. Please try again later.",
                files_to_create=None,
                files_to_edit=None
            )
            
        if isinstance(error, AuthenticationError):
            return AssistantResponse(
                assistant_reply="Authentication failed. Please check your API key.",
                files_to_create=None,
                files_to_edit=None
            )
            
        return AssistantResponse(
            assistant_reply=f"An error occurred: {error_msg}",
            files_to_create=None,
            files_to_edit=None
        )
```

## Best Practices

### 1. API Usage
- Use streaming for better user experience
- Implement proper rate limiting
- Handle API errors gracefully
- Validate responses against schemas
- Monitor API usage and costs

### 2. File Operations
- Always create backups before modifications
- Validate file contents before changes
- Use atomic operations where possible
- Implement proper error recovery
- Maintain audit trail of changes

### 3. Performance
- Optimize context management
- Implement caching where appropriate
- Use async operations for I/O
- Monitor memory usage
- Profile critical paths

### 4. Security
- Secure API key management
- Validate all file paths
- Implement proper access controls
- Monitor for suspicious patterns
- Regular security audits

## Future Enhancements

### 1. API Features
- Support for newer model versions
- Enhanced streaming capabilities
- Better error recovery mechanisms
- Advanced rate limiting strategies

### 2. File Operations
- Multi-file atomic changes
- Enhanced diff visualization
- Automatic code formatting
- Syntax-aware modifications

### 3. Performance
- Improved caching strategies
- Better memory management
- Response optimization
- Parallel operations support

### 4. Monitoring
- Enhanced error tracking
- Usage analytics
- Performance metrics
- Cost optimization tools

## Troubleshooting

### Common Issues

1. **API Connection**
   - Verify API key validity
   - Check network connectivity
   - Confirm rate limits
   - Validate request format

2. **File Operations**
   - Check file permissions
   - Verify file existence
   - Validate content format
   - Check available space

3. **Performance**
   - Monitor response times
   - Check memory usage
   - Verify cache operation
   - Profile slow operations

### Debug Tools

```python
class DebugTools:
    """Collection of debugging utilities."""
    
    @staticmethod
    def log_api_request(messages: List[dict], **kwargs):
        """Log API request details."""
        logger.debug(f"API Request: {json.dumps(messages, indent=2)}")
        logger.debug(f"Parameters: {json.dumps(kwargs, indent=2)}")
    
    @staticmethod
    def analyze_response(response: dict):
        """Analyze API response for issues."""
        logger.debug(f"Response: {json.dumps(response, indent=2)}")
        
    @staticmethod
    async def verify_file_operation(path: str):
        """Verify file operation results."""
        try:
            content = await read_file_async(path)
            logger.debug(f"File content: {content[:100]}...")
        except Exception as e:
            logger.error(f"File verification failed: {str(e)}")