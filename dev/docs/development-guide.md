# Development Guide 🛠️

## Getting Started

### Prerequisites
- Python 3.11 or higher
- DeepSeek API key
- pip or uv package manager

### Initial Setup

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd deepseek-engineer
   ```

2. **Environment Setup**
   Create a `.env` file in the project root:
   ```bash
   DEEPSEEK_API_KEY=your_api_key_here
   ```

3. **Installation**
   Choose one of these methods:

   Using pip:
   ```bash
   pip install -r requirements.txt
   ```

   Using uv (recommended for faster installation):
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

### Project Structure
```
deepseek-engineer/
├── main.py              # Main application entry point
├── pyproject.toml       # Project metadata and dependencies
├── requirements.txt     # Pinned dependencies
├── .gitignore          # Git ignore rules
├── README.md           # Project documentation
└── dev/                # Development documentation
    └── docs/           # Detailed documentation files
```

## Development Workflow

### 1. Code Organization

The main application logic is organized into several key sections:

1. **Client Configuration**
   - API client setup
   - Environment variable management

2. **Data Models**
   - Pydantic models for type safety
   - Request/response structures

3. **File Operations**
   - File reading/writing utilities
   - Diff editing functionality

4. **Conversation Management**
   - Message history tracking
   - Context management

5. **UI/UX Components**
   - Rich console output
   - User interaction handlers

### 2. Adding New Features

When adding new features:

1. **Plan the Feature**
   - Define the feature scope
   - Design the API/interface
   - Consider error cases

2. **Implement Models**
   ```python
   from pydantic import BaseModel
   
   class NewFeatureModel(BaseModel):
       field1: str
       field2: Optional[int] = None
   ```

3. **Add Helper Functions**
   ```python
   def new_feature_helper():
       """Document the purpose and usage."""
       # Implementation
   ```

4. **Update Main Loop**
   ```python
   def main():
       # Add new command handling
       if new_feature_condition:
           handle_new_feature()
   ```

### 3. Testing

Currently, the project needs a formal testing framework. When implementing tests:

1. **Unit Tests**
   ```python
   def test_file_operations():
       # Test file creation
       # Test file reading
       # Test diff editing
   ```

2. **Integration Tests**
   ```python
   def test_api_integration():
       # Test API connection
       # Test response handling
       # Test error cases
   ```

3. **Manual Testing**
   - Test file operations
   - Verify API responses
   - Check error handling

### 4. Error Handling

Follow these principles for error handling:

1. **Use Try-Except Blocks**
   ```python
   try:
       # Operation
   except SpecificError as e:
       # Handle specific error
   except Exception as e:
       # Handle unexpected errors
   ```

2. **Provide Clear Feedback**
   ```python
   console.print(f"[red]✗[/red] Error: {str(e)}", style="red")
   ```

3. **Log Errors**
   ```python
   # Future enhancement: Add proper logging
   logger.error(f"Operation failed: {str(e)}")
   ```

## Best Practices

### 1. Code Style

Follow these guidelines:

1. **Type Hints**
   ```python
   def function_name(param: str) -> bool:
       return isinstance(param, str)
   ```

2. **Documentation**
   ```python
   def complex_operation():
       """
       Detailed description of the operation.
       
       Returns:
           Operation result
       Raises:
           SpecificError: When something goes wrong
       """
   ```

3. **Consistent Formatting**
   - Use 4 spaces for indentation
   - Follow PEP 8 guidelines
   - Use meaningful variable names

### 2. Git Workflow

1. **Branch Management**
   ```bash
   git checkout -b feature/new-feature
   git checkout -b bugfix/issue-description
   ```

2. **Commit Messages**
   ```
   feat: Add new feature X
   fix: Resolve issue with Y
   docs: Update documentation for Z
   ```

3. **Pull Requests**
   - Provide clear descriptions
   - Reference issues
   - Include test cases

### 3. Documentation

1. **Code Comments**
   ```python
   # Explain complex algorithms
   # Document assumptions
   # Note potential issues
   ```

2. **Function Documentation**
   ```python
   def function_name():
       """
       Short description.

       Longer description with examples:
       >>> function_name()
       Expected output

       Args:
           None

       Returns:
           Description of return value
       """
   ```

3. **README Updates**
   - Keep installation steps current
   - Document new features
   - Update troubleshooting guides

## Troubleshooting

### Common Issues

1. **API Connection**
   - Check API key validity
   - Verify network connection
   - Confirm base URL

2. **File Operations**
   - Check file permissions
   - Verify path existence
   - Validate file content

3. **Dependencies**
   - Verify Python version
   - Check package versions
   - Update dependencies

### Debug Tools

1. **Rich Console**
   ```python
   console.print("[red]Debug:[/red]", obj, style="bold")
   ```

2. **Environment Checks**
   ```python
   console.print(f"Python: {sys.version}")
   console.print(f"Working Dir: {os.getcwd()}")
   ```

## Future Development

### Planned Enhancements

1. **Code Quality**
   - Add test suite
   - Implement logging
   - Add type checking

2. **Features**
   - Multiple model support
   - Enhanced file operations
   - Project templates

3. **Documentation**
   - API documentation
   - User guides
   - Contributing guidelines

### Contributing

1. **Setup Development Environment**
   ```bash
   git clone <repo>
   cd deepseek-engineer
   uv venv
   uv pip install -r requirements.txt
   ```

2. **Make Changes**
   - Follow style guide
   - Add tests
   - Update docs

3. **Submit PR**
   - Clear description
   - Test coverage
   - Documentation updates