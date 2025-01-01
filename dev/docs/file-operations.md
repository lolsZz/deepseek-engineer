# File Operations Guide 📁

## Overview

DeepSeek Engineer implements a robust file operations system that handles file creation, reading, and precise code modifications through diff editing. This document details the implementation and usage of these file operations.

## Core File Operation Components

### 1. File Reading
```python
def read_local_file(file_path: str) -> str:
    """Return the text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
```

Key features:
- UTF-8 encoding support
- Error handling for file access
- Path normalization

### 2. File Creation
```python
def create_file(path: str, content: str):
    """Create (or overwrite) a file with content."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
```

Capabilities:
- Automatic directory creation
- Path normalization
- Conversation context updates
- Success feedback

### 3. Diff Editing
```python
def apply_diff_edit(path: str, original_snippet: str, new_snippet: str):
    """Replace specific code snippets in existing files."""
    content = read_local_file(path)
    if original_snippet in content:
        updated_content = content.replace(original_snippet, new_snippet, 1)
        create_file(path, updated_content)
```

Features:
- Precise code replacement
- Context preservation
- Visual diff preview
- User confirmation

## Path Handling

### Path Normalization
```python
def normalize_path(path_str: str) -> str:
    """Return a canonical, absolute version of the path."""
    return str(Path(path_str).resolve())
```

Benefits:
- Consistent path formatting
- Security through absolute paths
- Cross-platform compatibility

### File Context Management
```python
def ensure_file_in_context(file_path: str) -> bool:
    """Ensures file content is in conversation context."""
    normalized_path = normalize_path(file_path)
    content = read_local_file(normalized_path)
    file_marker = f"Content of file '{normalized_path}'"
    # Add to context if not present
```

## Visual Feedback

### Diff Table Display
```python
def show_diff_table(files_to_edit: List[FileToEdit]):
    """Display proposed changes in a rich table."""
    table = Table(
        title="Proposed Edits",
        show_header=True,
        header_style="bold magenta",
        show_lines=True
    )
    table.add_column("File Path", style="cyan")
    table.add_column("Original", style="red")
    table.add_column("New", style="green")
```

Features:
- Side-by-side diff view
- Syntax highlighting
- Clear visual hierarchy

## File Operation Workflows

### 1. File Addition Workflow
```
User Input (/add command)
  ↓
Path Normalization
  ↓
File Reading
  ↓
Context Update
  ↓
Success Confirmation
```

### 2. File Creation Workflow
```
Assistant Response
  ↓
Path Validation
  ↓
Directory Creation
  ↓
Content Writing
  ↓
Context Update
  ↓
Success Feedback
```

### 3. Diff Edit Workflow
```
Assistant Suggestion
  ↓
Diff Preview
  ↓
User Confirmation
  ↓
Content Replacement
  ↓
Context Update
  ↓
Success Feedback
```

## Error Handling

### 1. File Access Errors
- FileNotFoundError handling
- Permission error management
- Path validation

### 2. Content Validation
- UTF-8 encoding verification
- Content size checks
- Format validation

### 3. Diff Application Errors
- Snippet matching verification
- Content replacement validation
- Backup mechanisms

## Best Practices

1. **Path Handling**
   - Always normalize paths
   - Use absolute paths internally
   - Validate paths before operations

2. **Content Management**
   - Use appropriate encoding
   - Handle large files efficiently
   - Maintain file context

3. **Error Recovery**
   - Implement rollback mechanisms
   - Provide clear error messages
   - Log operations for debugging

4. **User Interaction**
   - Confirm destructive operations
   - Show clear previews
   - Provide operation feedback

## Security Considerations

1. **Path Traversal Prevention**
   - Path normalization
   - Directory access validation
   - Symbolic link handling

2. **File Permission Management**
   - Check write permissions
   - Validate file ownership
   - Handle permission errors

3. **Content Validation**
   - Sanitize file content
   - Validate encodings
   - Check file sizes

## Future Enhancements

1. **Operation Features**
   - File backup system
   - Batch operations
   - Undo/redo support

2. **UI Improvements**
   - Enhanced diff visualization
   - Progress indicators
   - File tree navigation

3. **Security Enhancements**
   - File checksums
   - Operation logging
   - Access control lists