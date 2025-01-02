# DeepSeek Engineer

An advanced software development assistant powered by DeepSeek's language models. This tool provides intelligent code analysis, generation, and modification capabilities with robust security, monitoring, and conversation management.

## Features

- 🧠 Intelligent code understanding and generation
- 🔒 Built-in security and access control
- 📊 Comprehensive monitoring and telemetry
- 💬 Persistent conversation management
- 🔄 Smart file operations with diff support
- 📝 Structured output handling
- 🚀 MCP (Model Context Protocol) integration

## Installation

### From PyPI

```bash
pip install deepseek-engineer
```

### From Source

```bash
git clone https://github.com/deepseek/deepseek-engineer.git
cd deepseek-engineer
pip install -e ".[dev,test]"
```

## Configuration

DeepSeek Engineer can be configured through environment variables or command-line arguments:

```bash
# Required
export DEEPSEEK_API_KEY="your-api-key"

# Optional
export DEEPSEEK_CONVERSATION_PATH="~/.deepseek/conversation.json"
export DEEPSEEK_SECURITY_CONFIG="~/.deepseek/security.json"
export DEEPSEEK_LOG_PATH="~/.deepseek/deepseek.log"
```

## Usage

### Command Line Interface

```bash
# Basic usage
deepseek

# With custom configuration
deepseek --base-path /path/to/project \
         --max-tokens 4000 \
         --conversation-path ./conversation.json

# Export metrics/events
deepseek --export-metrics metrics.json
deepseek --export-events events.json
```

### Python API

```python
from deepseek_engineer import DeepSeekEngineer, AppConfig

# Initialize with configuration
config = AppConfig(
    api_key="your-api-key",
    base_path=Path("./project"),
    max_tokens=8000
)
app = DeepSeekEngineer(config)

# Process a request
result = app.process_request(
    message="Create a Python function that sorts a list of dictionaries by a key",
    context={"language": "python", "style": "functional"}
)

# Access response and file changes
print(result["response"])
for change in result["file_changes"]:
    print(f"Modified {change['path']}: {change['operation']}")

# Get system status
status = app.get_status()
print(f"System CPU: {status['system_status']['system_metrics']['cpu_percent']}%")
```

## Security

DeepSeek Engineer includes comprehensive security features:

- Path validation and sandboxing
- Content validation
- Rate limiting
- Authentication tokens
- Input sanitization
- Secure file operations

Configure security settings in `security.json`:

```json
{
    "allowed_paths": ["/path/to/project"],
    "blocked_paths": ["/etc", "/sys"],
    "allowed_extensions": [".py", ".js", ".html", ".css", ".json"],
    "blocked_extensions": [".exe", ".sh"],
    "max_file_size": 10485760,
    "rate_limit_window": 60,
    "rate_limit_max_requests": 100,
    "require_auth": true,
    "auth_token_expiry": 3600
}
```

## Monitoring

The system includes built-in monitoring capabilities:

- System metrics (CPU, memory, disk usage)
- Request/response metrics
- Error tracking
- Performance monitoring
- Event logging

Access monitoring data through the API or export it:

```python
# Export metrics
app.export_metrics("metrics.json")

# Export events
app.export_events("events.json")

# Get current status
status = app.get_status()
```

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=deepseek_engineer

# Run specific test file
pytest tests/test_app.py
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- mypy for type checking
- ruff for linting

```bash
# Format code
black src tests
isort src tests

# Type checking
mypy src

# Linting
ruff src tests
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- DeepSeek for their powerful language models
- The open source community for various tools and libraries used in this project

## Support

For support, please:
1. Check the [documentation](https://docs.deepseek.ai/engineer)
2. Search [existing issues](https://github.com/deepseek/deepseek-engineer/issues)
3. Create a new issue if needed

## Roadmap

- [ ] Enhanced code generation capabilities
- [ ] Improved context management
- [ ] Additional language support
- [ ] IDE integrations
- [ ] Collaborative features
- [ ] Performance optimizations
