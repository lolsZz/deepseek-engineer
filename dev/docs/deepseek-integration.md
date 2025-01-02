# DeepSeek Integration Guide 🔌

## Overview

DeepSeek Engineer implements a robust integration with DeepSeek's API, leveraging both direct API access and LiteLLM for multi-provider support. This document details our implementation patterns, real-world examples, and production-ready best practices.

## Core Implementation

### 1. API Integration Options

#### Direct API Access
```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# Pro Tip: Use connection pooling for better performance
from openai import OpenAI
import httpx

# Create a persistent HTTP client with connection pooling
http_client = httpx.Client(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    transport=httpx.HTTPTransport(retries=3)
)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    http_client=http_client
)
```

#### LiteLLM Integration
```python
from litellm import completion
import asyncio
from typing import AsyncGenerator

# Pro Tip: Use async for better performance
async def get_completion(prompt: str) -> AsyncGenerator[str, None]:
    """
    Async generator for streaming responses with proper error handling.
    
    Real-world Example:
    ```python
    async for chunk in get_completion("Write a Python function"):
        print(chunk, end="", flush=True)
    ```
    """
    try:
        response = await completion(
            model="deepseek/deepseek-coder",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            timeout=30,  # Practical timeout for production
            max_retries=3
        )
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"Completion error: {str(e)}", exc_info=True)
        raise
```

### 2. Production-Ready Data Models

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib

class FileOperation(BaseModel):
    """Base class for file operations with enhanced validation."""
    path: str = Field(..., description="Path to the target file")
    operation_id: str = Field(default_factory=lambda: hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:8])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('path')
    def validate_path(cls, v):
        """Prevent path traversal attacks."""
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid path: Must be relative and cannot contain '..'")
        return v

class FileToCreate(FileOperation):
    """Model for file creation with content validation."""
    content: str = Field(..., description="Complete content of the file")
    backup_path: Optional[str] = None
    
    @validator('content')
    def validate_content(cls, v):
        """Basic content validation."""
        if len(v.encode('utf-8')) > 10_000_000:  # 10MB limit
            raise ValueError("File content exceeds maximum size")
        return v

class FileToEdit(FileOperation):
    """Model for file editing with diff tracking."""
    original_snippet: str = Field(..., description="Exact content to be replaced")
    new_snippet: str = Field(..., description="New content to insert")
    line_number: Optional[int] = Field(None, description="Starting line number for context")
    
    @validator('original_snippet', 'new_snippet')
    def validate_snippets(cls, v):
        if not v.strip():
            raise ValueError("Snippet cannot be empty")
        return v

class AssistantResponse(BaseModel):
    """Enhanced model for structured assistant responses."""
    assistant_reply: str = Field(..., description="Main response text")
    files_to_create: Optional[List[FileToCreate]] = Field(default=None)
    files_to_edit: Optional[List[FileToEdit]] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_affected_files(self) -> List[str]:
        """Get list of all files that will be modified."""
        files = []
        if self.files_to_create:
            files.extend(f.path for f in self.files_to_create)
        if self.files_to_edit:
            files.extend(f.path for f in self.files_to_edit)
        return list(set(files))  # Remove duplicates
```

### 3. Production Stream Processing

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import backoff
import aiohttp
import asyncio

class StreamProcessor:
    """Production-ready stream processing with retry logic and monitoring."""
    
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
        self._metrics = {
            'requests': 0,
            'errors': 0,
            'tokens_processed': 0
        }
    
    @asynccontextmanager
    async def get_session(self):
        """Managed session context with connection pooling."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=aiohttp.TCPConnector(
                    limit=100,  # Connection pool size
                    ttl_dns_cache=300,  # DNS cache TTL
                    ssl=False  # Disable for internal services
                )
            )
        try:
            yield self.session
        finally:
            if self.session and self.session.closed:
                await self.session.close()
                self.session = None

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=30
    )
    async def stream_response(
        self,
        messages: List[dict],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Production-ready streaming with error handling and monitoring.
        
        Real-world Example:
        ```python
        processor = StreamProcessor(api_key="your-key")
        async for chunk in processor.stream_response(messages):
            print(chunk, end="", flush=True)
        print(f"Metrics: {processor.get_metrics()}")
        ```
        """
        self._metrics['requests'] += 1
        
        try:
            async with self.get_session() as session:
                async with session.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    json={
                        "model": "deepseek-coder",
                        "messages": messages,
                        "stream": True,
                        **kwargs
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8').strip('data: '))
                                if chunk.choices[0].delta.content:
                                    content = chunk.choices[0].delta.content
                                    self._metrics['tokens_processed'] += len(content.split())
                                    yield content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode chunk: {line}")
                                continue
                                
        except Exception as e:
            self._metrics['errors'] += 1
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            raise StreamError(f"Failed to stream response: {str(e)}")
    
    def get_metrics(self) -> dict:
        """Get current metrics for monitoring."""
        return self._metrics.copy()
```

## Real-World File Operations

### 1. Context Management with Memory Optimization

```python
from typing import Dict, Optional
import weakref
import psutil
import os

class FileContextManager:
    """Production-ready file context management with memory optimization."""
    
    def __init__(
        self,
        max_context_size: int = 8192,
        max_memory_percent: float = 75.0
    ):
        self.max_context_size = max_context_size
        self.max_memory_percent = max_memory_percent
        self.context_files: Dict[str, weakref.ref[str]] = {}
        self._memory = psutil.Process(os.getpid())
    
    def _check_memory_usage(self) -> bool:
        """Monitor memory usage to prevent OOM."""
        memory_percent = self._memory.memory_percent()
        return memory_percent < self.max_memory_percent
    
    async def add_file(self, path: str, priority: int = 1) -> bool:
        """
        Add file to context with memory management and prioritization.
        
        Real-world Example:
        ```python
        ctx = FileContextManager(max_context_size=8192)
        
        # Add high-priority files first
        await ctx.add_file("core/config.py", priority=2)
        await ctx.add_file("utils/helpers.py", priority=1)
        
        # Get optimized context
        context = ctx.get_optimized_context()
        ```
        """
        try:
            if not self._check_memory_usage():
                logger.warning("Memory usage too high, clearing low-priority context")
                self._clear_low_priority_files()
            
            content = await read_file_async(path)
            if self._will_fit_in_context(content):
                # Use weak reference to allow garbage collection
                self.context_files[path] = {
                    'content': weakref.ref(content),
                    'priority': priority,
                    'size': len(content)
                }
                return True
            return False
            
        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            return False
        except Exception as e:
            logger.error(f"Error adding file {path}: {str(e)}")
            return False
    
    def _clear_low_priority_files(self):
        """Remove low-priority files when memory constrained."""
        sorted_files = sorted(
            self.context_files.items(),
            key=lambda x: (x[1]['priority'], -x[1]['size'])
        )
        
        for path, _ in sorted_files:
            if self._check_memory_usage():
                break
            del self.context_files[path]
    
    def get_optimized_context(self) -> Dict[str, str]:
        """Get optimized context, cleaning up unused references."""
        optimized = {}
        for path, file_data in self.context_files.items():
            content = file_data['content']()
            if content is not None:
                optimized[path] = content
            else:
                # Reference was garbage collected
                del self.context_files[path]
        return optimized
```

### 2. Enhanced Diff Management

```python
from dataclasses import dataclass
from typing import List, Optional
import difflib
import asyncio
import hashlib

@dataclass
class DiffResult:
    """Structured diff result with metadata."""
    path: str
    original: str
    modified: str
    unified_diff: str
    hash: str
    line_changes: Dict[str, int]  # added, deleted, modified

class DiffManager:
    """Production-ready diff management with safety checks and visualization."""
    
    def __init__(self):
        self._backup_dir = ".backups"
        self._lock = asyncio.Lock()
        self._pending_changes: Dict[str, DiffResult] = {}
    
    def _compute_file_hash(self, content: str) -> str:
        """Compute content hash for verification."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_diff_stats(
        self,
        original: str,
        modified: str
    ) -> Dict[str, int]:
        """Generate detailed diff statistics."""
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        stats = {'added': 0, 'deleted': 0, 'modified': 0}
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                stats['added'] += j2 - j1
            elif tag == 'delete':
                stats['deleted'] += i2 - i1
            elif tag == 'replace':
                stats['modified'] += max(i2 - i1, j2 - j1)
                
        return stats
    
    async def preview_changes(
        self,
        files_to_edit: List[FileToEdit],
        syntax_highlight: bool = True
    ) -> Table:
        """Generate rich diff preview with syntax highlighting."""
        table = Table(
            title="Proposed Changes",
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("File", style="cyan", width=30)
        table.add_column("Changes", style="yellow", width=15)
        table.add_column("Original", style="red")
        table.add_column("Modified", style="green")
        
        for edit in files_to_edit:
            try:
                current_content = await read_file_async(edit.path)
                modified_content = current_content.replace(
                    edit.original_snippet,
                    edit.new_snippet,
                    1
                )
                
                # Generate diff statistics
                stats = self._generate_diff_stats(
                    edit.original_snippet,
                    edit.new_snippet
                )
                
                changes = (
                    f"+{stats['added']} "
                    f"-{stats['deleted']} "
                    f"~{stats['modified']}"
                )
                
                if syntax_highlight:
                    original = Syntax(
                        edit.original_snippet,
                        "python",
                        theme="monokai",
                        line_numbers=True
                    )
                    modified = Syntax(
                        edit.new_snippet,
                        "python",
                        theme="monokai",
                        line_numbers=True
                    )
                else:
                    original = edit.original_snippet
                    modified = edit.new_snippet
                
                table.add_row(
                    edit.path,
                    changes,
                    original,
                    modified
                )
                
                # Store pending change
                self._pending_changes[edit.path] = DiffResult(
                    path=edit.path,
                    original=current_content,
                    modified=modified_content,
                    unified_diff='\n'.join(difflib.unified_diff(
                        current_content.splitlines(),
                        modified_content.splitlines(),
                        fromfile=f'a/{edit.path}',
                        tofile=f'b/{edit.path}'
                    )),
                    hash=self._compute_file_hash(current_content),
                    line_changes=stats
                )
                
            except Exception as e:
                logger.error(f"Failed to generate diff for {edit.path}: {str(e)}")
                table.add_row(
                    edit.path,
                    "ERROR",
                    str(e),
                    "",
                )
        
        return table
    
    async def apply_changes(
        self,
        files_to_edit: List[FileToEdit]
    ) -> List[str]:
        """Apply changes with atomic operations and verification."""
        modified_files = []
        
        async with self._lock:  # Ensure thread-safety
            try:
                # Verify all files before making any changes
                for edit in files_to_edit:
                    if edit.path not in self._pending_changes:
                        raise DiffError(f"No pending changes for {edit.path}")
                    
                    current_content = await read_file_async(edit.path)
                    current_hash = self._compute_file_hash(current_content)
                    
                    if current_hash != self._pending_changes[edit.path].hash:
                        raise DiffError(
                            f"File {edit.path} has been modified since diff generation"
                        )
                
                # Apply all changes atomically
                for edit in files_to_edit:
                    diff_result = self._pending_changes[edit.path]
                    
                    # Create backup
                    backup_path = os.path.join(
                        self._backup_dir,
                        f"{edit.path}.{int(time.time())}.bak"
                    )
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    await write_file_async(backup_path, diff_result.original)
                    
                    # Apply change
                    await write_file_async(edit.path, diff_result.modified)
                    modified_files.append(edit.path)
                    
                    # Log change for audit
                    logger.info(
                        f"Applied changes to {edit.path}",
                        extra={
                            'diff': diff_result.unified_diff,
                            'backup': backup_path,
                            'changes': diff_result.line_changes
                        }
                    )
                
                # Clear pending changes
                for path in modified_files:
                    del self._pending_changes[path]
                
                return modified_files
                
            except Exception as e:
                logger.error(f"Failed to apply changes: {str(e)}")
                # Attempt to restore from backups
                await self._restore_backups(modified_files)
                raise
```

## Production Error Handling

### 1. Enhanced Exception Hierarchy

```python
class DeepSeekError(Exception):
    """Base exception with error tracking."""
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.timestamp = datetime.utcnow()
        
        # Log error with context
        logger.error(
            f"DeepSeek Error: {message}",
            extra={
                'error_code': code,
                'timestamp': self.timestamp,
                'traceback': traceback.format_exc()
            }
        )

class APIError(DeepSeekError):
    """API-specific errors with retry guidance."""
    def __init__(self, message: str, status_code: int, response: dict):
        super().__init__(
            f"API Error ({status_code}): {message}",
            code=f"API_{status_code}"
        )
        self.status_code = status_code
        self.response = response
        self.is_retryable = status_code in {408, 429, 500, 502, 503, 504}

class StreamError(DeepSeekError):
    """Streaming-specific errors with recovery options."""
    def __init__(self, message: str, chunk_index: Optional[int] = None):
        super().__init__(
            f"Stream Error at chunk {chunk_index}: {message}",
            code="STREAM_ERROR"
        )
        self.chunk_index = chunk_index
        self.partial_response = []

class DiffError(DeepSeekError):
    """Diff operation errors with detailed context."""
    def __init__(self, message: str, file_path: str, operation: str):
        super().__init__(
            f"Diff Error in {file_path} during {operation}: {message}",
            code="DIFF_ERROR"
        )
        self.file_path = file_path
        self.operation = operation
```

### 2. Production Error Management

```python
from typing import Optional, Dict, Any
import sentry_sdk
from datetime import datetime, timedelta

class ErrorManager:
    """Production-ready error management with rate limiting and monitoring."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, datetime] = {}
        self.rate_limit_window = timedelta(minutes=5)
        self.rate_limit_threshold = 10
    
    def _should_alert(self, error_code: str) -> bool:
        """Implement rate limiting for alerts."""
        now = datetime.utcnow()
        
        if error_code not in self.error_counts:
            self.error_counts[error_code] = 0
            self.error_timestamps[error_code] = now
            return True
        
        # Reset counts if outside window
        if now - self.error_timestamps[error_code] > self.rate_limit_window:
            self.error_counts[error_code] = 0
            self.error_timestamps[error_code] = now
            return True
        
        self.error_counts[error_code] += 1
        return self.error_counts[error_code] <= self.rate_limit_threshold
    
    def handle_api_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> AssistantResponse:
        """Convert API errors to user-friendly responses with proper logging."""
        error_msg = str(error)
        error_code = getattr(error, 'code', 'UNKNOWN')
        
        # Enhance error context
        error_context = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error.__class__.__name__,
            'error_code': error_code,
            **(context or {})
        }
        
        # Handle specific error types
        if isinstance(error, RateLimitError):
            logger.warning(
                "Rate limit exceeded",
                extra={
                    **error_context,
                    'retry_after': error.retry_after
                }
            )
            
            return AssistantResponse(
                assistant_reply=(
                    "Rate limit exceeded. Please try again in "
                    f"{error.retry_after} seconds."
                ),
                metadata={'retry_after': error.retry_after}
            )
            
        if isinstance(error, AuthenticationError):
            logger.error(
                "Authentication failed",
                extra=error_context
            )
            
            if self._should_alert('AUTH_ERROR'):
                # Alert operations team
                self._send_alert(
                    "Authentication failure detected",
                    error_context
                )
            
            return AssistantResponse(
                assistant_reply=(
                    "Authentication failed. Please check your API key or "
                    "contact support."
                ),
                metadata={'auth_error': True}
            )
        
        # Handle unexpected errors
        logger.error(
            f"Unexpected error: {error_msg}",
            extra=error_context,
            exc_info=True
        )
        
        # Report to error tracking
        sentry_sdk.capture_exception(
            error,
            extra=error_context
        )
        
        return AssistantResponse(
            assistant_reply=(
                "An unexpected error occurred. Our team has been notified. "
                "Please try again later."
            ),
            metadata={
                'error': str(error),
                'error_code': error_code
            }
        )
    
    def _send_alert(
        self,
        message: str,
        context: Dict[str, Any]
    ):
        """Send alerts to operations team."""
        try:
            # Implementation depends on your alert system
            # Example: Send to Slack
            slack_client.chat_postMessage(
                channel="#ops-alerts",
                text=f"🚨 {message}",
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{message}*"}
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{json.dumps(context, indent=2)}```"
                        }
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
```

## Production Best Practices

### 1. API Usage

#### Rate Limiting
```python
class RateLimiter:
    """Thread-safe rate limiter with token bucket algorithm."""
    
    def __init__(
        self,
        rate: float,
        burst: int = 1
    ):
        self.rate = rate  # tokens per second
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens with proper rate limiting."""
        with self._lock:
            now = time.time()
            # Add new tokens based on time passed
            self.tokens = min(
                self.burst,
                self.tokens + (now - self.last_update) * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# Usage
rate_limiter = RateLimiter(rate=10.0, burst=20)  # 10 requests/second
if rate_limiter.acquire():
    # Make API request
    pass
else:
    # Handle rate limit
    pass
```

#### Response Validation
```python
from pydantic import BaseModel, validator
from typing import List, Optional

class APIResponse(BaseModel):
    """Validated API response structure."""
    content: str
    tokens_used: int
    model: str
    finish_reason: Optional[str]
    
    @validator('tokens_used')
    def validate_tokens(cls, v):
        if v < 0:
            raise ValueError("Token count cannot be negative")
        return v
    
    @validator('finish_reason')
    def validate_finish(cls, v):
        valid_reasons = {'stop', 'length', 'content_filter', None}
        if v not in valid_reasons:
            raise ValueError(f"Invalid finish reason: {v}")
        return v

def validate_response(raw_response: dict) -> APIResponse:
    """Validate API response with proper error handling."""
    try:
        return APIResponse(**raw_response)
    except Exception as e:
        logger.error(f"Response validation failed: {str(e)}")
        raise ValueError(f"Invalid API response: {str(e)}")
```

### 2. File Operations

#### Atomic File Updates
```python
import tempfile
import shutil
import os

async def atomic_write(path: str, content: str):
    """Atomic file write with backup."""
    # Create temporary file
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=os.path.dirname(os.path.abspath(path))
    )
    
    try:
        # Write to temporary file
        with os.fdopen(tmp_fd, 'w') as tmp_file:
            tmp_file.write(content)
        
        # Create backup of existing file
        if os.path.exists(path):
            backup_path = f"{path}.bak"
            shutil.copy2(path, backup_path)
        
        # Atomic rename
        os.replace(tmp_path, path)
        
    except Exception as e:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise FileOperationError(f"Failed to write file: {str(e)}")
```

#### Safe File Operations
```python
import os
from typing import Optional
import hashlib

class SafeFileOps:
    """Thread-safe file operations with validation."""
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    async def safe_read(
        path: str,
        encoding: str = 'utf-8'
    ) -> tuple[str, str]:
        """
        Safely read file with hash verification.
        Returns (content, hash)
        """
        try:
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                content = await f.read()
                return content, SafeFileOps.compute_hash(content)
        except Exception as e:
            logger.error(f"Failed to read {path}: {str(e)}")
            raise
    
    @staticmethod
    async def safe_write(
        path: str,
        content: str,
        original_hash: Optional[str] = None
    ) -> str:
        """
        Safely write file with hash verification.
        Returns new content hash.
        """
        if original_hash:
            current_content, current_hash = await SafeFileOps.safe_read(path)
            if current_hash != original_hash:
                raise FileConflictError(
                    f"File {path} has been modified"
                )
        
        await atomic_write(path, content)
        return SafeFileOps.compute_hash(content)
```

### 3. Performance Optimization

#### Response Streaming
```python
class OptimizedStreamer:
    """Memory-efficient response streaming."""
    
    def __init__(self, chunk_size: int = 1024):
        self.chunk_size = chunk_size
        self.buffer = []
        self.buffer_size = 0
    
    async def process_chunk(
        self,
        chunk: str,
        callback: Optional[Callable[[str], None]] = None
    ):
        """Process chunk with memory optimization."""
        self.buffer.append(chunk)
        self.buffer_size += len(chunk)
        
        if self.buffer_size >= self.chunk_size:
            content = ''.join(self.buffer)
            self.buffer = []
            self.buffer_size = 0
            
            if callback:
                callback(content)
            return content
        return None
    
    async def finish(
        self,
        callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """Flush remaining buffer."""
        if self.buffer:
            content = ''.join(self.buffer)
            self.buffer = []
            self.buffer_size = 0
            
            if callback:
                callback(content)
            return content
        return None
```

#### Connection Pooling
```python
import aiohttp
from typing import Optional

class ConnectionPool:
    """Managed connection pool for API requests."""
    
    def __init__(
        self,
        pool_size: int = 100,
        keepalive_timeout: int = 30,
        timeout: int = 30
    ):
        self.session: Optional[aiohttp.ClientSession] = None
        self.pool_size = pool_size
        self.keepalive_timeout = keepalive_timeout
        self.timeout = timeout
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create session with connection pooling."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    limit=self.pool_size,
                    keepalive_timeout=self.keepalive_timeout
                ),
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
