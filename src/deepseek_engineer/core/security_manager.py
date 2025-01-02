"""Security management and access control."""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Set, Pattern
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
import hashlib
import secrets
from functools import wraps

@dataclass
class SecurityConfig:
    """Security configuration settings."""
    allowed_paths: List[Path]
    blocked_paths: List[Path]
    allowed_extensions: Set[str]
    blocked_extensions: Set[str]
    max_file_size: int  # in bytes
    rate_limit_window: int  # in seconds
    rate_limit_max_requests: int
    require_auth: bool
    auth_token_expiry: int  # in seconds

class SecurityViolation(Exception):
    """Base exception for security violations."""
    pass

class AccessDenied(SecurityViolation):
    """Raised when access to a resource is denied."""
    pass

class RateLimitExceeded(SecurityViolation):
    """Raised when rate limit is exceeded."""
    pass

class InvalidInput(SecurityViolation):
    """Raised when input validation fails."""
    pass

class SecurityManager:
    """Manages security and access control."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize security manager with optional config path."""
        self.config = self._load_config(config_path)
        self._rate_limit_tracker: Dict[str, List[datetime]] = {}
        self._active_tokens: Dict[str, datetime] = {}
        self._dangerous_patterns: List[Pattern] = self._compile_dangerous_patterns()
    
    def _load_config(self, config_path: Optional[Path]) -> SecurityConfig:
        """Load security configuration from file or use defaults."""
        defaults = {
            "allowed_paths": [os.getcwd()],
            "blocked_paths": ["/etc", "/sys", "/dev"],
            "allowed_extensions": {".py", ".js", ".html", ".css", ".json", ".md", ".txt"},
            "blocked_extensions": {".exe", ".dll", ".so", ".dylib", ".sh", ".bash"},
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "rate_limit_window": 60,  # 1 minute
            "rate_limit_max_requests": 100,
            "require_auth": True,
            "auth_token_expiry": 3600  # 1 hour
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                defaults.update(custom_config)
            except Exception as e:
                print(f"Warning: Failed to load security config: {e}")
        
        return SecurityConfig(
            allowed_paths=[Path(p) for p in defaults["allowed_paths"]],
            blocked_paths=[Path(p) for p in defaults["blocked_paths"]],
            allowed_extensions=set(defaults["allowed_extensions"]),
            blocked_extensions=set(defaults["blocked_extensions"]),
            max_file_size=defaults["max_file_size"],
            rate_limit_window=defaults["rate_limit_window"],
            rate_limit_max_requests=defaults["rate_limit_max_requests"],
            require_auth=defaults["require_auth"],
            auth_token_expiry=defaults["auth_token_expiry"]
        )
    
    def _compile_dangerous_patterns(self) -> List[Pattern]:
        """Compile regex patterns for dangerous content."""
        patterns = [
            r"rm\s+-rf",  # Dangerous shell commands
            r"sudo",
            r"chmod\s+777",
            r"eval\(",  # Dangerous code patterns
            r"exec\(",
            r"os\.system",
            r"subprocess\.call",
            r"__import__",
            r"input\(",  # Potential security risks
            r"open\([^)]*w",  # Write file operations
        ]
        return [re.compile(pattern) for pattern in patterns]
    
    def validate_path(self, path: Path) -> bool:
        """
        Validate if a path is allowed.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path is allowed
            
        Raises:
            AccessDenied: If path access is not allowed
        """
        try:
            resolved_path = path.resolve()
            
            # Check blocked paths
            for blocked in self.config.blocked_paths:
                if str(resolved_path).startswith(str(blocked)):
                    raise AccessDenied(f"Access to path {path} is blocked")
            
            # Check allowed paths
            allowed = any(
                str(resolved_path).startswith(str(allowed))
                for allowed in self.config.allowed_paths
            )
            if not allowed:
                raise AccessDenied(f"Path {path} is outside allowed directories")
            
            # Check extensions
            if path.suffix:
                if path.suffix in self.config.blocked_extensions:
                    raise AccessDenied(f"File extension {path.suffix} is blocked")
                if self.config.allowed_extensions and path.suffix not in self.config.allowed_extensions:
                    raise AccessDenied(f"File extension {path.suffix} is not allowed")
            
            return True
            
        except Exception as e:
            if not isinstance(e, AccessDenied):
                raise AccessDenied(f"Path validation error: {str(e)}")
            raise
    
    def validate_content(self, content: str) -> bool:
        """
        Validate if content is safe.
        
        Args:
            content: Content to validate
            
        Returns:
            bool: True if content is safe
            
        Raises:
            InvalidInput: If content contains dangerous patterns
        """
        # Check for dangerous patterns
        for pattern in self._dangerous_patterns:
            if pattern.search(content):
                raise InvalidInput(f"Content contains dangerous pattern: {pattern.pattern}")
        
        # Check content length
        if len(content.encode('utf-8')) > self.config.max_file_size:
            raise InvalidInput(f"Content exceeds maximum size of {self.config.max_file_size} bytes")
        
        return True
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier for rate limiting (e.g., IP address)
            
        Returns:
            bool: True if request is allowed
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.config.rate_limit_window)
        
        # Clean old requests
        if identifier in self._rate_limit_tracker:
            self._rate_limit_tracker[identifier] = [
                t for t in self._rate_limit_tracker[identifier]
                if t > window_start
            ]
        else:
            self._rate_limit_tracker[identifier] = []
        
        # Check limit
        if len(self._rate_limit_tracker[identifier]) >= self.config.rate_limit_max_requests:
            raise RateLimitExceeded(
                f"Rate limit of {self.config.rate_limit_max_requests} "
                f"requests per {self.config.rate_limit_window} seconds exceeded"
            )
        
        # Add new request
        self._rate_limit_tracker[identifier].append(now)
        return True
    
    def generate_auth_token(self) -> str:
        """Generate a new authentication token."""
        token = secrets.token_urlsafe(32)
        self._active_tokens[token] = datetime.now() + timedelta(
            seconds=self.config.auth_token_expiry
        )
        return token
    
    def validate_auth_token(self, token: str) -> bool:
        """
        Validate an authentication token.
        
        Args:
            token: Token to validate
            
        Returns:
            bool: True if token is valid
            
        Raises:
            AccessDenied: If token is invalid or expired
        """
        if not self.config.require_auth:
            return True
            
        if token not in self._active_tokens:
            raise AccessDenied("Invalid authentication token")
            
        if datetime.now() > self._active_tokens[token]:
            del self._active_tokens[token]
            raise AccessDenied("Authentication token expired")
            
        return True
    
    def revoke_auth_token(self, token: str):
        """Revoke an authentication token."""
        if token in self._active_tokens:
            del self._active_tokens[token]
    
    def clean_expired_tokens(self):
        """Remove expired authentication tokens."""
        now = datetime.now()
        expired = [
            token for token, expiry in self._active_tokens.items()
            if now > expiry
        ]
        for token in expired:
            del self._active_tokens[token]
    
    @staticmethod
    def hash_content(content: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def require_auth(self, func):
        """Decorator to require authentication for a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = kwargs.pop('auth_token', None)
            self.validate_auth_token(token)
            return func(*args, **kwargs)
        return wrapper
    
    def secure_operation(self, func):
        """Decorator to apply security checks to an operation."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract identifier for rate limiting (could be from kwargs)
            identifier = kwargs.get('identifier', 'default')
            
            # Perform security checks
            self.check_rate_limit(identifier)
            
            # Clean expired tokens periodically
            self.clean_expired_tokens()
            
            return func(*args, **kwargs)
        return wrapper