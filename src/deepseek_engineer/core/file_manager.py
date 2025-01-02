"""FileManager class for handling all file system operations."""

import os
from pathlib import Path
from typing import List, Optional, Union, Dict
from dataclasses import dataclass
import hashlib
import shutil
from datetime import datetime

@dataclass
class FileMetadata:
    """Metadata for a file in the system."""
    path: Path
    size: int
    modified_time: datetime
    hash: str
    content_type: str

class FileOperationError(Exception):
    """Base exception for file operations."""
    pass

class FileManager:
    """Manages all file system operations with enhanced capabilities."""
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """Initialize FileManager with optional base path."""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self._file_cache: Dict[str, FileMetadata] = {}

    def _normalize_path(self, path: Union[str, Path]) -> Path:
        """Convert path to absolute Path object relative to base_path."""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            path_obj = self.base_path / path_obj
        return path_obj.resolve()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file contents."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_content_type(self, file_path: Path) -> str:
        """Determine content type based on file extension."""
        extension = file_path.suffix.lower()
        content_types = {
            '.py': 'text/python',
            '.js': 'text/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.md': 'text/markdown',
            '.txt': 'text/plain'
        }
        return content_types.get(extension, 'application/octet-stream')

    def _get_metadata(self, file_path: Path) -> FileMetadata:
        """Get metadata for a file, using cache if available."""
        path_str = str(file_path)
        if path_str in self._file_cache:
            return self._file_cache[path_str]

        if not file_path.exists():
            raise FileOperationError(f"File not found: {file_path}")

        metadata = FileMetadata(
            path=file_path,
            size=file_path.stat().st_size,
            modified_time=datetime.fromtimestamp(file_path.stat().st_mtime),
            hash=self._calculate_file_hash(file_path),
            content_type=self._get_content_type(file_path)
        )
        self._file_cache[path_str] = metadata
        return metadata

    def read_file(self, path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read and return the contents of a file."""
        try:
            file_path = self._normalize_path(path)
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(f"Error reading file {path}: {str(e)}")

    def write_file(self, path: Union[str, Path], content: str, encoding: str = 'utf-8') -> None:
        """Write content to a file, creating directories if needed."""
        try:
            file_path = self._normalize_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Invalidate cache for this file
            if str(file_path) in self._file_cache:
                del self._file_cache[str(file_path)]
                
        except Exception as e:
            raise FileOperationError(f"Error writing to file {path}: {str(e)}")

    def apply_diff(self, path: Union[str, Path], original: str, new: str) -> None:
        """Apply a diff to a file, replacing original content with new content."""
        try:
            file_path = self._normalize_path(path)
            content = self.read_file(file_path)
            
            if original not in content:
                raise FileOperationError(
                    f"Original content not found in {path}. "
                    "File may have been modified."
                )
            
            updated_content = content.replace(original, new, 1)
            self.write_file(file_path, updated_content)
            
        except Exception as e:
            raise FileOperationError(f"Error applying diff to {path}: {str(e)}")

    def list_files(self, 
                   directory: Union[str, Path], 
                   pattern: str = "*", 
                   recursive: bool = False) -> List[Path]:
        """List files in directory matching pattern."""
        try:
            dir_path = self._normalize_path(directory)
            if not dir_path.is_dir():
                raise FileOperationError(f"Not a directory: {directory}")

            if recursive:
                return list(dir_path.rglob(pattern))
            return list(dir_path.glob(pattern))
            
        except Exception as e:
            raise FileOperationError(f"Error listing files in {directory}: {str(e)}")

    def copy_file(self, 
                  source: Union[str, Path], 
                  destination: Union[str, Path], 
                  overwrite: bool = False) -> None:
        """Copy a file from source to destination."""
        try:
            src_path = self._normalize_path(source)
            dst_path = self._normalize_path(destination)

            if not overwrite and dst_path.exists():
                raise FileOperationError(f"Destination file exists: {destination}")

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)

            # Invalidate cache for destination file
            if str(dst_path) in self._file_cache:
                del self._file_cache[str(dst_path)]
                
        except Exception as e:
            raise FileOperationError(f"Error copying {source} to {destination}: {str(e)}")

    def move_file(self, 
                  source: Union[str, Path], 
                  destination: Union[str, Path], 
                  overwrite: bool = False) -> None:
        """Move a file from source to destination."""
        try:
            src_path = self._normalize_path(source)
            dst_path = self._normalize_path(destination)

            if not overwrite and dst_path.exists():
                raise FileOperationError(f"Destination file exists: {destination}")

            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))

            # Update cache
            if str(src_path) in self._file_cache:
                del self._file_cache[str(src_path)]
            if str(dst_path) in self._file_cache:
                del self._file_cache[str(dst_path)]
                
        except Exception as e:
            raise FileOperationError(f"Error moving {source} to {destination}: {str(e)}")

    def delete_file(self, path: Union[str, Path]) -> None:
        """Delete a file."""
        try:
            file_path = self._normalize_path(path)
            file_path.unlink()

            # Remove from cache
            if str(file_path) in self._file_cache:
                del self._file_cache[str(file_path)]
                
        except Exception as e:
            raise FileOperationError(f"Error deleting {path}: {str(e)}")

    def get_file_info(self, path: Union[str, Path]) -> FileMetadata:
        """Get metadata about a file."""
        try:
            file_path = self._normalize_path(path)
            return self._get_metadata(file_path)
        except Exception as e:
            raise FileOperationError(f"Error getting info for {path}: {str(e)}")

    def clear_cache(self) -> None:
        """Clear the metadata cache."""
        self._file_cache.clear()