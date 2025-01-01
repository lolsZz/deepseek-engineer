# DeepSeek Integration Implementation 🔌

## Overview

DeepSeek Engineer implements direct integration with DeepSeek's API, focusing on structured outputs and efficient file operations. This document details our specific implementation choices and patterns.

## Core Implementation

### 1. Direct API Integration
```python
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
```

Unlike rawdog's litellm-based approach, we use direct API integration for:
- Simplified dependency chain
- Direct control over API interactions
- Streamlined error handling

### 2. Structured Output Model
```python
class FileToCreate(BaseModel):
    path: str
    content: str

class FileToEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str

class AssistantResponse(BaseModel):
    assistant_reply: str
    files_to_create: Optional[List[FileToCreate]] = None
    files_to_edit: Optional[List[FileToEdit]] = None
```

Key differences from rawdog:
- Focused model structure for file operations
- Simplified response format
- Direct file operation support

### 3. Stream Processing Implementation
```python
def stream_openai_response(user_message: str):
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=conversation_history,
        response_format={"type": "json_object"},
        max_completion_tokens=8000,
        stream=True
    )

    full_content = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content_chunk = chunk.choices[0].delta.content
            full_content += content_chunk
            console.print(content_chunk, end="")
```

Benefits:
- Real-time response display
- Efficient memory usage
- Improved user experience

## File Operation Integration

### 1. Context-Aware File Operations
```python
def ensure_file_in_context(file_path: str) -> bool:
    """Ensures file content is in conversation context."""
    try:
        normalized_path = normalize_path(file_path)
        content = read_local_file(normalized_path)
        file_marker = f"Content of file '{normalized_path}'"
        if not any(file_marker in msg["content"] for msg in conversation_history):
            conversation_history.append({
                "role": "system",
                "content": f"{file_marker}:\n\n{content}"
            })
        return True
    except OSError:
        return False
```

Features:
- Automatic context management
- Path normalization
- Duplicate prevention
- Error handling

### 2. Diff-Based File Editing
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

    for edit in files_to_edit:
        table.add_row(edit.path, edit.original_snippet, edit.new_snippet)
```

Advantages:
- Visual diff preview
- User confirmation
- Safe code modifications
- Context preservation

## System Prompt Integration

Our system prompt is designed to work specifically with DeepSeek's capabilities:

```python
system_PROMPT = dedent("""\
    You are an elite software engineer called DeepSeek Engineer with decades of experience...
    
    Core capabilities:
    1. Code Analysis & Discussion
    2. File Operations
       a) Read existing files
       b) Create new files
       c) Edit existing files
    
    Output Format:
    {
      "assistant_reply": "Your main explanation or response",
      "files_to_create": [
        {
          "path": "path/to/new/file",
          "content": "complete file content"
        }
      ],
      "files_to_edit": [
        {
          "path": "path/to/existing/file",
          "original_snippet": "exact code to be replaced",
          "new_snippet": "new code to insert"
        }
      ]
    }
""")
```

Key aspects:
- Structured JSON output
- Clear file operation specifications
- Comprehensive capability description

## Error Handling

### 1. API Error Management
```python
try:
    stream = client.chat.completions.create(...)
except Exception as e:
    error_msg = f"DeepSeek API error: {str(e)}"
    return AssistantResponse(
        assistant_reply=error_msg,
        files_to_create=[]
    )
```

### 2. File Operation Errors
```python
try:
    content = read_local_file(path)
    if original_snippet in content:
        updated_content = content.replace(original_snippet, new_snippet, 1)
        create_file(path, updated_content)
    else:
        console.print(f"[yellow]⚠[/yellow] Original snippet not found")
except FileNotFoundError:
    console.print(f"[red]✗[/red] File not found: '{path}'")
```

## Best Practices

1. **API Usage**
   - Stream responses for better UX
   - Maintain conversation context
   - Handle rate limits gracefully
   - Validate responses

2. **File Operations**
   - Always normalize paths
   - Preview changes before applying
   - Maintain file context
   - Handle encoding properly

3. **Error Management**
   - Provide clear error messages
   - Implement graceful fallbacks
   - Log errors for debugging
   - Handle edge cases

4. **Performance**
   - Efficient context management
   - Smart file handling
   - Response streaming
   - Memory optimization

## Future Enhancements

1. **API Integration**
   - Support for more DeepSeek models
   - Enhanced streaming capabilities
   - Better error recovery
   - Rate limit handling

2. **File Operations**
   - Batch operations
   - Undo/redo support
   - Better diff visualization
   - File backup system

3. **User Experience**
   - Progress indicators
   - Enhanced error messages
   - Interactive confirmations
   - Operation logging

4. **Performance**
   - Response caching
   - Optimized file handling
   - Smart context pruning
   - Memory management