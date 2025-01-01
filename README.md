# DeepSeek Engineer 🐋

## Overview

This repository contains a powerful coding assistant application that integrates with the DeepSeek API to process user conversations and generate structured JSON responses. Through an intuitive command-line interface, it can read local file contents, create new files, and apply diff edits to existing files in real time. The system is extended through the Model Context Protocol (MCP), providing access to a wide range of tools and services.

## Key Features

1. DeepSeek Client Configuration
   - Automatically configures an API client to use the DeepSeek service with a valid DEEPSEEK_API_KEY. 
   - Connects to the DeepSeek endpoint specified in the environment variable to stream GPT-like completions. 

2. Data Models
   - Leverages Pydantic for type-safe handling of file operations, including:
     • FileToCreate – describes files to be created or updated.  
     • FileToEdit – describes specific snippet replacements in an existing file.  
     • AssistantResponse – structures chat responses and potential file operations.  

3. System Prompt
   - A comprehensive system prompt (system_PROMPT) guides conversation, ensuring all replies strictly adhere to JSON output with optional file creations or edits.  

4. Helper Functions
   - read_local_file: Reads a target filesystem path and returns its content as a string.  
   - create_file: Creates or overwrites a file with provided content.  
   - show_diff_table: Presents proposed file changes in a rich, multi-line table.  
   - apply_diff_edit: Applies snippet-level modifications to existing files.  

5. "/add" Command
   - Users can type "/add path/to/file" to quickly read a file's content and insert it into the conversation as a system message.  
   - This allows the assistant to reference the file contents for further discussion, code generation, or diff proposals.  

6. Conversation Flow
   - Maintains a conversation_history list to track messages between user and assistant.  
   - Streams the assistant's replies via the DeepSeek API, parsing them as JSON to preserve both the textual response and the instructions for file modifications.  

7. Interactive Session
   - Run the script (for example: "python3 main.py") to start an interactive loop at your terminal.  
   - Enter your requests or code questions. Enter "/add path/to/file" to add file contents to the conversation.  
   - When the assistant suggests new or edited files, you can confirm changes directly in your local environment.  
   - Type "exit" or "quit" to end the session.  

8. MCP Server Integration
   - Extends functionality through the Model Context Protocol (MCP)
   - Provides access to various server types:
     • System Integration (Filesystem, Git, Time)
     • Database (SQLite, PostgreSQL)
     • Search & Knowledge (Brave Search, AWS KB Retrieval)
     • AI/ML Integration (Sequential Thinking, EverArt)
     • External API Integration (Google Maps, Slack, GitHub/GitLab)
     • Monitoring (Sentry)
   - Implements both TypeScript and Python servers
   - Features comprehensive security and rate limiting
   - Supports caching and resource management

## Getting Started

1. Prepare a .env file with your DeepSeek API key:
   DEEPSEEK_API_KEY=your_api_key_here

2. Install dependencies and run (choose one method):

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
   - Set up desired MCP servers from the mcp-servers directory
   - Configure server settings in ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
   - Add any required API keys or credentials to the server configurations

4. Enjoy multi-line streaming responses, file read-ins with "/add path/to/file", precise file edits when approved, and extended functionality through MCP servers.

## MCP Server Documentation

For detailed information about MCP servers, refer to the documentation in dev/docs:
- [MCP Specification](dev/docs/mcp-specification.md) - Protocol details and architecture
- [MCP Implementation](dev/docs/mcp-implementation.md) - Implementation guide and examples
- [MCP Best Practices](dev/docs/mcp-best-practices.md) - Guidelines and patterns

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

> **Note**: This is an experimental project developed by Skirano to test the new DeepSeek v3 API capabilities. It was developed as a rapid prototype and should be used accordingly.
