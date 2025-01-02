"""Tests for the SecurityManager class."""

import pytest
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from deepseek_engineer.core.security_manager import (
    SecurityManager,
    SecurityConfig,
    AccessDenied,
    RateLimitExceeded,
    InvalidInput
)

@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary security config file."""
    config = {
        "allowed_paths": [str(tmp_path)],
        "blocked_paths": ["/etc", "/sys"],
        "allowed_extensions": [".txt", ".py"],
        "blocked_extensions": [".exe", ".sh"],
        "max_file_size": 1024,  # 1KB for testing
        "rate_limit_window": 1,  # 1 second for faster testing
        "rate_limit_max_requests": 3,
        "require_auth": True,
        "auth_token_expiry": 1  # 1 second for faster testing
    }
    
    config_file = tmp_path / "security_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    
    return config_file

@pytest.fixture
def security_manager(temp_config_file):
    """Create a SecurityManager instance with test configuration."""
    return SecurityManager(config_path=temp_config_file)

def test_config_loading(temp_config_file):
    """Test security configuration loading."""
    manager = SecurityManager(config_path=temp_config_file)
    assert isinstance(manager.config, SecurityConfig)
    assert len(manager.config.allowed_paths) > 0
    assert len(manager.config.blocked_paths) > 0
    assert len(manager.config.allowed_extensions) > 0
    assert len(manager.config.blocked_extensions) > 0

def test_path_validation(security_manager, tmp_path):
    """Test path validation logic."""
    # Test allowed path
    test_file = tmp_path / "test.txt"
    assert security_manager.validate_path(test_file) is True
    
    # Test blocked path
    with pytest.raises(AccessDenied):
        security_manager.validate_path(Path("/etc/passwd"))
    
    # Test blocked extension
    with pytest.raises(AccessDenied):
        security_manager.validate_path(tmp_path / "test.exe")
    
    # Test path outside allowed directories
    with pytest.raises(AccessDenied):
        security_manager.validate_path(Path("/usr/local/test.txt"))

def test_content_validation(security_manager):
    """Test content validation logic."""
    # Test safe content
    assert security_manager.validate_content("Hello, world!") is True
    
    # Test dangerous patterns
    dangerous_contents = [
        "rm -rf /",
        "sudo apt-get install",
        "eval('code')",
        "os.system('command')",
        "subprocess.call(['rm', '-rf'])",
        "__import__('os').system",
        "open('file', 'w').write('data')"
    ]
    
    for content in dangerous_contents:
        with pytest.raises(InvalidInput):
            security_manager.validate_content(content)
    
    # Test content size limit
    large_content = "x" * (security_manager.config.max_file_size + 1)
    with pytest.raises(InvalidInput):
        security_manager.validate_content(large_content)

def test_rate_limiting(security_manager):
    """Test rate limiting functionality."""
    identifier = "test_user"
    
    # Make requests up to limit
    for _ in range(security_manager.config.rate_limit_max_requests):
        assert security_manager.check_rate_limit(identifier) is True
    
    # Next request should fail
    with pytest.raises(RateLimitExceeded):
        security_manager.check_rate_limit(identifier)
    
    # Wait for window to expire
    time.sleep(security_manager.config.rate_limit_window + 0.1)
    
    # Should be able to make requests again
    assert security_manager.check_rate_limit(identifier) is True

def test_authentication(security_manager):
    """Test authentication token management."""
    # Generate token
    token = security_manager.generate_auth_token()
    assert token is not None
    
    # Validate token
    assert security_manager.validate_auth_token(token) is True
    
    # Test invalid token
    with pytest.raises(AccessDenied):
        security_manager.validate_auth_token("invalid_token")
    
    # Test token expiration
    time.sleep(security_manager.config.auth_token_expiry + 0.1)
    with pytest.raises(AccessDenied):
        security_manager.validate_auth_token(token)

def test_token_revocation(security_manager):
    """Test token revocation."""
    token = security_manager.generate_auth_token()
    assert security_manager.validate_auth_token(token) is True
    
    security_manager.revoke_auth_token(token)
    with pytest.raises(AccessDenied):
        security_manager.validate_auth_token(token)

def test_expired_token_cleanup(security_manager):
    """Test cleanup of expired tokens."""
    # Generate multiple tokens
    tokens = [security_manager.generate_auth_token() for _ in range(3)]
    
    # Wait for expiration
    time.sleep(security_manager.config.auth_token_expiry + 0.1)
    
    # Clean expired tokens
    security_manager.clean_expired_tokens()
    
    # All tokens should be invalid
    for token in tokens:
        with pytest.raises(AccessDenied):
            security_manager.validate_auth_token(token)

def test_content_hashing(security_manager):
    """Test content hashing functionality."""
    content = "Test content"
    hash1 = security_manager.hash_content(content)
    hash2 = security_manager.hash_content(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64 character hex string

def test_security_decorators(security_manager):
    """Test security decorator functionality."""
    
    # Test function with auth requirement
    @security_manager.require_auth
    def protected_function():
        return "success"
    
    # Test function with security checks
    @security_manager.secure_operation
    def rate_limited_function():
        return "success"
    
    # Test auth decorator
    token = security_manager.generate_auth_token()
    assert protected_function(auth_token=token) == "success"
    
    with pytest.raises(AccessDenied):
        protected_function(auth_token="invalid_token")
    
    # Test security decorator
    for _ in range(security_manager.config.rate_limit_max_requests):
        assert rate_limited_function(identifier="test") == "success"
    
    with pytest.raises(RateLimitExceeded):
        rate_limited_function(identifier="test")

def test_multiple_security_managers(tmp_path):
    """Test multiple SecurityManager instances don't interfere."""
    config1 = tmp_path / "config1.json"
    config2 = tmp_path / "config2.json"
    
    # Create different configs
    for path, window in [(config1, 1), (config2, 2)]:
        with open(path, 'w') as f:
            json.dump({
                "allowed_paths": [str(tmp_path)],
                "rate_limit_window": window,
                "rate_limit_max_requests": 1
            }, f)
    
    manager1 = SecurityManager(config_path=config1)
    manager2 = SecurityManager(config_path=config2)
    
    # Test rate limits are independent
    manager1.check_rate_limit("test")
    manager2.check_rate_limit("test")
    
    with pytest.raises(RateLimitExceeded):
        manager1.check_rate_limit("test")
    
    # But manager2 should still work due to longer window
    assert manager2.check_rate_limit("test") is True