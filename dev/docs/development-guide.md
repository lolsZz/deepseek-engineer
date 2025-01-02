# Development Guide 🛠️

## Getting Started

### Prerequisites
- Python 3.12 or higher (for enhanced typing support)
- DeepSeek API key
- pip or uv package manager
- Git for version control

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
├── tests/              # Test suite directory
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
└── dev/               # Development documentation
    └── docs/          # Detailed documentation files
```

## Development Workflow

### 1. Code Organization

The main application logic is organized into several key sections:

1. **Client Configuration**
   - API client setup
   - Environment variable management
   - MCP server configuration

2. **Data Models**
   - Pydantic models for type safety
   - Request/response structures
   - MCP protocol types

3. **File Operations**
   - File reading/writing utilities
   - Diff editing functionality
   - Path normalization

4. **Conversation Management**
   - Message history tracking
   - Context management
   - Token optimization

5. **UI/UX Components**
   - Rich console output
   - User interaction handlers
   - Progress indicators

### 2. Adding New Features

When adding new features:

1. **Plan the Feature**
   - Define the feature scope
   - Design the API/interface
   - Consider error cases
   - Plan for testing

2. **Implement Models**
   ```python
   from pydantic import BaseModel, Field
   
   class NewFeatureModel(BaseModel):
       field1: str = Field(..., description="Field description")
       field2: Optional[int] = Field(None, description="Optional field")
   ```

3. **Add Helper Functions**
   ```python
   def new_feature_helper(param: str) -> Result:
       """
       Implement new functionality with proper typing.

       Args:
           param: Description of parameter

       Returns:
           Result: Description of return value

       Raises:
           FeatureError: When something goes wrong
       """
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

The project uses pytest for testing. Run tests with:
```bash
pytest tests/
```

1. **Unit Tests**
   ```python
   import pytest
   from unittest.mock import Mock

   def test_file_operations():
       # Arrange
       test_file = "test.txt"
       test_content = "test content"
       
       # Act
       result = create_file(test_file, test_content)
       
       # Assert
       assert result.success
       assert file_exists(test_file)
   ```

2. **Integration Tests**
   ```python
   @pytest.mark.integration
   def test_api_integration():
       # Test API connection
       client = create_client()
       response = client.chat.completions.create(...)
       assert response.status == 200
   ```

3. **Mocking External Services**
   ```python
   @pytest.fixture
   def mock_api():
       with patch('deepseek.api.client') as mock:
           yield mock
   ```

### 4. Error Handling

Follow these principles for error handling:

1. **Custom Exceptions**
   ```python
   class FeatureError(Exception):
       """Base exception for feature-specific errors."""
       pass

   class ValidationError(FeatureError):
       """Raised when validation fails."""
       pass
   ```

2. **Error Handling Pattern**
   ```python
   try:
       result = perform_operation()
   except ValidationError as e:
       console.print(f"[red]✗[/red] Validation failed: {str(e)}")
       logger.error(f"Validation error: {str(e)}")
   except FeatureError as e:
       console.print(f"[red]✗[/red] Operation failed: {str(e)}")
       logger.error(f"Feature error: {str(e)}")
   except Exception as e:
       console.print(f"[red]✗[/red] Unexpected error: {str(e)}")
       logger.exception("Unexpected error occurred")
   ```

3. **Logging**
   ```python
   import logging

   logger = logging.getLogger(__name__)
   logger.setLevel(logging.INFO)

   handler = logging.FileHandler('app.log')
   handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
   logger.addHandler(handler)
   ```

## Best Practices

### 1. Code Style

Follow these guidelines:

1. **Type Hints**
   ```python
   from typing import Optional, List, Dict

   def process_data(items: List[str], config: Optional[Dict[str, any]] = None) -> bool:
       return all(isinstance(item, str) for item in items)
   ```

2. **Documentation**
   ```python
   def complex_operation(param: str) -> Result:
       """
       Perform a complex operation with detailed documentation.
       
       Args:
           param: Detailed parameter description
       
       Returns:
           Result object containing operation output
       
       Raises:
           ValueError: When param is invalid
           OperationError: When operation fails
       
       Example:
           >>> result = complex_operation("test")
           >>> print(result.status)
           'success'
       """
   ```

3. **Code Formatting**
   - Use black for consistent formatting
   - Use isort for import sorting
   - Use flake8 for linting
   - Use mypy for type checking

### 2. Git Workflow

1. **Branch Naming**
   ```bash
   feature/add-new-capability
   bugfix/fix-error-handling
   docs/update-api-docs
   ```

2. **Commit Messages**
   ```
   feat: Add new feature X
   fix: Resolve issue with Y
   docs: Update documentation for Z
   test: Add tests for feature X
   ```

3. **Pull Request Process**
   - Create detailed PR description
   - Include test coverage
   - Update documentation
   - Add changelog entry

### 3. Documentation

1. **Code Comments**
   ```python
   # Algorithm complexity: O(n log n)
   # Note: This assumes sorted input
   def binary_search(items: List[int], target: int) -> int:
       """
       Perform binary search with detailed implementation notes.
       """
   ```

2. **API Documentation**
   ```python
   class APIClient:
       """
       Client for interacting with external APIs.

       Attributes:
           base_url: The base URL for API requests
           timeout: Request timeout in seconds

       Example:
           >>> client = APIClient("https://api.example.com")
           >>> response = client.get_data()
       """
   ```

3. **README Updates**
   - Keep installation steps current
   - Document new features
   - Update troubleshooting guides
   - Include example usage

## Troubleshooting

### Common Issues

1. **API Connection**
   - Check API key validity
   - Verify network connection
   - Confirm base URL
   - Check rate limits

2. **File Operations**
   - Check file permissions
   - Verify path existence
   - Validate file content
   - Check disk space

3. **Dependencies**
   - Verify Python version
   - Check package versions
   - Update dependencies
   - Clear cache if needed

### Debug Tools

1. **Rich Console**
   ```python
   from rich.console import Console
   console = Console()

   console.print("[red]Debug:[/red]", obj, style="bold")
   console.print_json(data)
   ```

2. **Environment Checks**
   ```python
   import sys
   import os
   
   console.print(f"Python: {sys.version}")
   console.print(f"Working Dir: {os.getcwd()}")
   console.print(f"Environment: {os.environ.get('ENV', 'development')}")
   ```

## Future Development

### Planned Enhancements

1. **Code Quality**
   - Expand test coverage
   - Add performance benchmarks
   - Implement comprehensive logging
   - Add static analysis tools

2. **Features**
   - Enhanced MCP server support
   - Improved file operations
   - Project templates
   - Plugin system

3. **Documentation**
   - Interactive API documentation
   - Video tutorials
   - Contributing guidelines
   - Architecture diagrams

### Contributing

1. **Setup Development Environment**
   ```bash
   git clone <repo>
   cd deepseek-engineer
   uv venv
   uv pip install -r requirements.txt
   pre-commit install
   ```

2. **Development Process**
   - Follow style guide
   - Write tests
   - Update documentation
   - Run CI checks locally

3. **Submit Changes**
   - Create feature branch
   - Make atomic commits
   - Write clear PR description
   - Address review feedback