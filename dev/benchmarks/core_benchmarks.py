#!/usr/bin/env python3
"""
Core Component Benchmarks

This module implements specific benchmarks for core DeepSeek Engineer components
to track performance against our success metrics:
- Response time < 100ms
- Memory usage < 500MB
- Resource efficiency

Implementation Notes:
- Measures both cold and warm start times
- Tracks memory usage patterns
- Monitors resource utilization
- Generates detailed performance reports
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List

from benchmark_framework import benchmark, BenchmarkTracker
from deepseek_engineer.core.file_manager import FileManager
from deepseek_engineer.core.conversation_manager import ConversationManager
from deepseek_engineer.core.security_manager import SecurityManager
from deepseek_engineer.mcp.manager import MCPManager

class CoreBenchmarks:
    """Benchmarks for core system components."""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(Path(self.temp_dir))
        self.conversation_manager = ConversationManager()
        self.security_manager = SecurityManager()
        self.results: Dict[str, List[float]] = {}

    @benchmark("file_operations")
    def benchmark_file_operations(self, file_count: int = 100) -> None:
        """Benchmark file operations performance."""
        files: List[str] = []
        
        # Write operations
        for i in range(file_count):
            path = f"test_file_{i}.txt"
            content = f"Test content for file {i}\n" * 10
            self.file_manager.write_file(path, content)
            files.append(path)

        # Read operations
        for path in files:
            self.file_manager.read_file(path)

        # Search operations
        self.file_manager.search_files("test", "*.txt")

        # Cleanup
        for path in files:
            self.file_manager.delete_file(path)

    @benchmark("conversation_management")
    def benchmark_conversation(self, message_count: int = 100) -> None:
        """Benchmark conversation management performance."""
        # Add messages
        for i in range(message_count):
            self.conversation_manager.add_message({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Test message {i}\n" * 5
            })

        # Get context
        self.conversation_manager.get_context()

        # Clear context
        self.conversation_manager.clear_context()

    @benchmark("security_validation")
    def benchmark_security(self, operation_count: int = 1000) -> None:
        """Benchmark security validation performance."""
        paths = [f"/test/path/{i}" for i in range(operation_count)]
        
        # Path validation
        for path in paths:
            self.security_manager.validate_path(path)

        # Content validation
        content = "Test content\n" * 100
        self.security_manager.validate_content(content)

        # Token validation
        token = "test_token"
        for _ in range(operation_count):
            self.security_manager.validate_token(token)

    @benchmark("mcp_operations")
    async def benchmark_mcp(self, plugin_count: int = 10) -> None:
        """Benchmark MCP system performance."""
        mcp_manager = MCPManager()
        
        # Plugin registration
        for i in range(plugin_count):
            await mcp_manager.register_plugin(f"test_plugin_{i}")

        # Tool execution
        for i in range(plugin_count):
            await mcp_manager.execute_tool(f"test_plugin_{i}", "test_tool", {})

        # Resource access
        for i in range(plugin_count):
            await mcp_manager.get_resource(f"test_plugin_{i}", "test_resource")

        # Cleanup
        await mcp_manager.shutdown()

def run_benchmarks():
    """Run all core benchmarks."""
    benchmarks = CoreBenchmarks()
    
    print("Running File Operations Benchmark...")
    benchmarks.benchmark_file_operations()
    
    print("Running Conversation Management Benchmark...")
    benchmarks.benchmark_conversation()
    
    print("Running Security Validation Benchmark...")
    benchmarks.benchmark_security()
    
    print("Running MCP Operations Benchmark...")
    asyncio.run(benchmarks.benchmark_mcp())
    
    # Save results
    tracker = benchmarks.benchmark_file_operations.tracker
    tracker.save_results()

if __name__ == "__main__":
    run_benchmarks()