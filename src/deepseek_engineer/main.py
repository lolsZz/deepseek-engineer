#!/usr/bin/env python3
"""DeepSeek Engineer CLI application."""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
import json

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.style import Style
from rich.traceback import install as install_rich_traceback

from .app import DeepSeekEngineer, AppConfig
from .core.security_manager import SecurityViolation

# Install rich traceback handler
install_rich_traceback(show_locals=True)

# Initialize Rich console
console = Console()

def create_arg_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="DeepSeek Engineer - Advanced software development assistant"
    )
    
    parser.add_argument(
        "--base-path",
        type=Path,
        help="Base path for file operations (default: current directory)"
    )
    
    parser.add_argument(
        "--api-key",
        help="DeepSeek API key (can also use DEEPSEEK_API_KEY env var)"
    )
    
    parser.add_argument(
        "--conversation-path",
        type=Path,
        help="Path to persist conversation history"
    )
    
    parser.add_argument(
        "--security-config",
        type=Path,
        help="Path to security configuration file"
    )
    
    parser.add_argument(
        "--log-path",
        type=Path,
        help="Path to log file"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8000,
        help="Maximum tokens for conversation context"
    )
    
    parser.add_argument(
        "--export-metrics",
        type=Path,
        help="Export metrics to specified file"
    )
    
    parser.add_argument(
        "--export-events",
        type=Path,
        help="Export events to specified file"
    )
    
    return parser

def display_status(app: DeepSeekEngineer):
    """Display current system status."""
    status = app.get_status()
    
    # System metrics
    metrics_table = Table(title="System Metrics", show_header=True)
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", style="green")
    
    for name, value in status["system_status"]["system_metrics"].items():
        metrics_table.add_row(name, f"{value}")
    
    console.print(metrics_table)
    
    # Conversation summary
    conv_summary = status["conversation_summary"]
    console.print("\n[bold]Conversation Summary[/bold]")
    console.print(f"Messages: {conv_summary['message_count']}")
    console.print(f"Total Tokens: {conv_summary['total_tokens']}")
    
    # Security status
    security = status["security_status"]
    console.print("\n[bold]Security Status[/bold]")
    console.print(f"Auth Required: {security['auth_required']}")
    console.print(
        f"Rate Limit: {security['rate_limit_config']['max_requests']} "
        f"requests per {security['rate_limit_config']['window']} seconds"
    )

def handle_file_changes(changes: list):
    """Display file changes in a table."""
    if not changes:
        return
        
    table = Table(title="File Changes", show_header=True)
    table.add_column("Path", style="cyan")
    table.add_column("Operation", style="green")
    table.add_column("Timestamp", style="blue")
    
    for change in changes:
        table.add_row(
            change["path"],
            change["operation"],
            change["timestamp"]
        )
    
    console.print(table)

def main():
    """Main CLI entry point."""
    parser = create_arg_parser()
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = AppConfig(
            api_key=args.api_key or os.getenv("DEEPSEEK_API_KEY"),
            base_path=args.base_path or Path.cwd(),
            max_tokens=args.max_tokens,
            conversation_persist_path=args.conversation_path,
            security_config_path=args.security_config,
            log_path=args.log_path
        )
        
        # Initialize application
        app = DeepSeekEngineer(config)
        
        # Handle export commands if specified
        if args.export_metrics:
            app.export_metrics(args.export_metrics)
            console.print(f"[green]Metrics exported to {args.export_metrics}[/green]")
            return
            
        if args.export_events:
            app.export_events(args.export_events)
            console.print(f"[green]Events exported to {args.export_events}[/green]")
            return
        
        # Display welcome message
        console.print(Panel.fit(
            "[bold blue]Welcome to DeepSeek Engineer[/bold blue] 🚀\n"
            "Your advanced software development assistant",
            border_style="blue"
        ))
        
        # Generate auth token if needed
        auth_token = None
        if app.security.config.require_auth:
            auth_token = app.generate_auth_token()
            console.print(f"[green]Auth Token: {auth_token}[/green]")
        
        # Main interaction loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You>[/bold green] ")
                
                # Handle special commands
                if user_input.lower() in ["exit", "quit"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                    
                if user_input.lower() == "status":
                    display_status(app)
                    continue
                    
                if user_input.lower() == "clear":
                    app.clear_conversation()
                    console.print("[green]Conversation cleared[/green]")
                    continue
                
                # Process normal request
                result = app.process_request(
                    message=user_input,
                    auth_token=auth_token
                )
                
                # Display response
                console.print("\n[bold blue]Assistant>[/bold blue] ", end="")
                console.print(result["response"])
                
                # Display any file changes
                handle_file_changes(result["file_changes"])
                
            except SecurityViolation as e:
                console.print(f"[red]Security Error: {str(e)}[/red]")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break
                
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                console.print("[red]Use 'exit' to quit[/red]")
        
        console.print("[blue]Session finished.[/blue]")
        
    except Exception as e:
        console.print(f"[red]Fatal Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()