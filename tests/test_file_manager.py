"""Tests for the FileManager class."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from deepseek_engineer.core.file_manager import FileManager, FileOperationError, FileMetadata

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def file_manager(temp_dir):
    """Create a FileManager instance with a temporary directory."""
    return FileManager(base_path=temp_dir)

def test_init_default():
    """Test FileManager initialization with default parameters."""
    fm = FileManager()
    assert fm.base_path == Path.cwd()

def test_init_with_path(temp_dir):
    """Test FileManager initialization with custom path."""
    fm = FileManager(base_path=temp_dir)
    assert fm.base_path == temp_dir

def test_read_write_file(file_manager, temp_dir):
    """Test basic file read/write operations."""
    test_file = temp_dir / "test.txt"
    content = "Hello, World!"
    
    file_manager.write_file(test_file, content)
    assert test_file.exists()
    
    read_content = file_manager.read_file(test_file)
    assert read_content == content

def test_write_file_creates_directories(file_manager, temp_dir):
    """Test that write_file creates necessary directories."""
    nested_file = temp_dir / "deep" / "nested" / "test.txt"
    content = "Nested content"
    
    file_manager.write_file(nested_file, content)
    assert nested_file.exists()
    assert nested_file.read_text() == content

def test_apply_diff(file_manager, temp_dir):
    """Test applying diffs to files."""
    test_file = temp_dir / "diff_test.txt"
    original_content = "Hello\nWorld\nTest"
    file_manager.write_file(test_file, original_content)
    
    file_manager.apply_diff(test_file, "World", "Modified")
    modified_content = file_manager.read_file(test_file)
    assert modified_content == "Hello\nModified\nTest"

def test_apply_diff_not_found(file_manager, temp_dir):
    """Test applying diff when original content not found."""
    test_file = temp_dir / "diff_error.txt"
    file_manager.write_file(test_file, "Different content")
    
    with pytest.raises(FileOperationError):
        file_manager.apply_diff(test_file, "NonexistentContent", "New")

def test_list_files(file_manager, temp_dir):
    """Test listing files with different patterns."""
    # Create test files
    (temp_dir / "test1.txt").touch()
    (temp_dir / "test2.txt").touch()
    (temp_dir / "other.dat").touch()
    nested_dir = temp_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "nested.txt").touch()
    
    # Test non-recursive listing
    txt_files = file_manager.list_files(temp_dir, "*.txt", recursive=False)
    assert len(txt_files) == 2
    assert all(f.suffix == ".txt" for f in txt_files)
    
    # Test recursive listing
    all_txt_files = file_manager.list_files(temp_dir, "*.txt", recursive=True)
    assert len(all_txt_files) == 3

def test_copy_file(file_manager, temp_dir):
    """Test file copying functionality."""
    source = temp_dir / "source.txt"
    dest = temp_dir / "dest.txt"
    content = "Test content"
    
    file_manager.write_file(source, content)
    file_manager.copy_file(source, dest)
    
    assert dest.exists()
    assert file_manager.read_file(dest) == content

def test_copy_file_no_overwrite(file_manager, temp_dir):
    """Test copy file with overwrite protection."""
    source = temp_dir / "source.txt"
    dest = temp_dir / "dest.txt"
    
    file_manager.write_file(source, "Source content")
    file_manager.write_file(dest, "Dest content")
    
    with pytest.raises(FileOperationError):
        file_manager.copy_file(source, dest, overwrite=False)

def test_move_file(file_manager, temp_dir):
    """Test file moving functionality."""
    source = temp_dir / "source.txt"
    dest = temp_dir / "dest.txt"
    content = "Move test"
    
    file_manager.write_file(source, content)
    file_manager.move_file(source, dest)
    
    assert not source.exists()
    assert dest.exists()
    assert file_manager.read_file(dest) == content

def test_delete_file(file_manager, temp_dir):
    """Test file deletion."""
    test_file = temp_dir / "delete_test.txt"
    file_manager.write_file(test_file, "Delete me")
    
    assert test_file.exists()
    file_manager.delete_file(test_file)
    assert not test_file.exists()

def test_get_file_info(file_manager, temp_dir):
    """Test getting file metadata."""
    test_file = temp_dir / "info_test.txt"
    content = "Test content"
    file_manager.write_file(test_file, content)
    
    info = file_manager.get_file_info(test_file)
    assert isinstance(info, FileMetadata)
    assert info.path == test_file
    assert info.size == len(content)
    assert isinstance(info.modified_time, datetime)
    assert info.content_type == "text/plain"

def test_metadata_caching(file_manager, temp_dir):
    """Test that metadata is cached and cache can be cleared."""
    test_file = temp_dir / "cache_test.txt"
    file_manager.write_file(test_file, "Cache test")
    
    # Get info twice - second should use cache
    info1 = file_manager.get_file_info(test_file)
    info2 = file_manager.get_file_info(test_file)
    assert info1 == info2
    
    # Clear cache and get new info
    file_manager.clear_cache()
    info3 = file_manager.get_file_info(test_file)
    assert info3.hash == info1.hash  # Content hasn't changed

def test_error_handling(file_manager):
    """Test error handling for various operations."""
    with pytest.raises(FileOperationError):
        file_manager.read_file("nonexistent.txt")
    
    with pytest.raises(FileOperationError):
        file_manager.delete_file("nonexistent.txt")
    
    with pytest.raises(FileOperationError):
        file_manager.get_file_info("nonexistent.txt")