# DeepSeek Engineer 🐋

## Overview

This repository contains a powerful coding assistant application that integrates with multiple LLM providers through LiteLLM, with DeepSeek as the primary implementation. Through an intuitive command-line interface, it can read local file contents, create new files, and apply diff edits to existing files in real time. The system is extended through the Model Context Protocol (MCP), providing access to a wide range of tools and services.

## Key Features

1. Multi-Provider LLM Support
   - Primary integration with DeepSeek API
   - Support for Cerebras models
   - AWS Bedrock integration
   - Unified interface through LiteLLM
   - Configurable fallback strategies

2. Data Models
   - Leverages Pydantic for type-safe handling of file operations:
     • FileToCreate – describes files to be created or updated
     • FileToEdit – describes specific snippet replacements in an existing file
     • AssistantResponse – structures chat responses and potential file operations

3. System Prompt
   - A comprehensive system prompt guides conversation
   - Ensures structured JSON output
   - Supports file operations and tool usage

4. File Operations
   - read_local_file: Reads target filesystem paths
   - create_file: Creates or overwrites files
   - show_diff_table: Visual diff previews
   - apply_diff_edit: Precise code modifications

5. "/add" Command
   - Quick file content insertion with "/add path/to/file"
   - Adds context for code generation and modifications
   - Supports conversation history management

6. Conversation Flow
   - Maintains conversation history
   - Streams responses from LLM providers
   - Parses structured JSON outputs
   - Handles file modifications

7. Interactive Session
   - Terminal-based interface
   - File content integration
   - Change confirmation system
   - Streaming responses

8. MCP Server Integration
   - Model Context Protocol support
   - Various server types:
     • System Integration (Filesystem, Git, Time)
     • Database (SQLite, PostgreSQL)
     • Search & Knowledge (Brave Search, AWS KB Retrieval)
     • AI/ML Integration (Sequential Thinking, EverArt)
     • External API Integration (Google Maps, Slack, GitHub/GitLab)
     • Monitoring (Sentry)
   - TypeScript and Python implementations
   - Security and rate limiting
   - Caching and resource management

9. Logging and Monitoring
   - Comprehensive logging system
   - Performance monitoring
   - Error tracking
   - Usage analytics

## Getting Started

1. Prepare environment variables:
   ```bash
   # .env file
   DEEPSEEK_API_KEY=your_deepseek_key
   CEREBRAS_API_KEY=your_cerebras_key  # Optional
   AWS_ACCESS_KEY_ID=your_aws_key      # Optional
   AWS_SECRET_ACCESS_KEY=your_aws_secret  # Optional
   AWS_REGION_NAME=your_aws_region     # Optional
   ```

2. Install dependencies (choose one method):

   ### Using pip
   ```bash
   pip install -r requirements.txt
   python3 main.py
   ```

   ### Using uv (faster alternative)
   ```bash
   uv venv
   uv run main.py
   ```

3. Configure MCP Servers:
   - Set up desired MCP servers from mcp-servers directory
   - Configure in ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
   - Add required API keys and credentials

4. Start using the system:
   - Run interactive sessions
   - Use "/add path/to/file" for file operations
   - Leverage MCP servers for extended functionality

## Documentation

### Core Documentation
- [Architecture](dev/docs/architecture.md) - System design and components
- [API Integration](dev/docs/api-integration.md) - API interaction details
- [File Operations](dev/docs/file-operations.md) - File handling guide
- [Components](dev/docs/components.md) - Component breakdown

### LLM Integration
- [DeepSeek Integration](dev/docs/deepseek-integration.md) - Primary LLM implementation
- [LiteLLM Integration](dev/docs/litellm-integration.md) - Multi-provider support
- [LLM Configuration](dev/docs/llm-configuration.md) - LLM setup guide
- [Advanced LLM Features](dev/docs/advanced-llm-features.md) - Advanced capabilities

### MCP Documentation
- [MCP Specification](dev/docs/mcp-specification.md) - Protocol details
- [MCP Implementation](dev/docs/mcp-implementation.md) - Implementation guide
- [MCP Best Practices](dev/docs/mcp-best-practices.md) - Guidelines and patterns

### System Documentation
- [Development Guide](dev/docs/development-guide.md) - Development workflow
- [Logging and Monitoring](dev/docs/logging-and-monitoring.md) - Observability guide

## Available MCP Servers

1. System Integration
   - filesystem: File system operations
   - git: Version control operations
   - time: Time management and scheduling

2. Database
   - sqlite: SQLite database operations
   - postgres: PostgreSQL database operations
   - memory: In-memory storage

3. Search & Knowledge
   - brave-search: Web search capabilities
   - aws-kb-retrieval: AWS knowledge base integration
   - everything: Local file search

4. AI/ML Integration
   - sequentialthinking: Advanced reasoning capabilities
   - everart: Art generation

5. External APIs
   - google-maps: Location and mapping services
   - slack: Slack messaging integration
   - github/gitlab: Repository management

6. Monitoring
   - sentry: Error tracking and monitoring

## Contributing

See the [Development Guide](dev/docs/development-guide.md) for information on contributing to the project.

## License

This project is licensed under the terms specified in the project root.

---

> **Note**: This is an experimental project developed to test advanced LLM capabilities through a unified interface. It was developed as a rapid prototype and should be used accordingly.
