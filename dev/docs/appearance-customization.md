# Appearance Customization Guide 🎨

## Overview

DeepSeek Engineer supports extensive customization of its appearance through themes, styles, and custom components. This guide covers all aspects of visual customization and theming.

## Theme System

### 1. Built-in Themes

```python
from rich.theme import Theme

DEFAULT_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "code": "blue",
    "prompt": "magenta",
    "system": "grey70",
})
```

### 2. Custom Theme Creation

```python
custom_theme = Theme({
    "info": "blue",
    "warning": "orange1",
    "error": "red1 bold",
    "success": "green4",
    "code": "cyan2",
    "prompt": "purple4",
    "system": "grey74",
})

console = Console(theme=custom_theme)
```

### 3. Theme Configuration File

Create `~/.config/deepseek-engineer/theme.json`:
```json
{
    "colors": {
        "info": "#00FFFF",
        "warning": "#FFD700",
        "error": "#FF0000",
        "success": "#00FF00",
        "code": "#0000FF",
        "prompt": "#FF00FF",
        "system": "#808080"
    },
    "styles": {
        "code_block": {
            "background": "#1E1E1E",
            "foreground": "#D4D4D4"
        },
        "diff": {
            "added": "#28A745",
            "removed": "#DC3545"
        }
    }
}
```

## Console Customization

### 1. Output Formatting

```python
class OutputFormatter:
    """Handles console output formatting."""
    
    def format_code(self, code: str) -> None:
        """Format code blocks with syntax highlighting."""
        console.print(Syntax(code, "python", theme="monokai"))
    
    def format_diff(self, original: str, new: str) -> None:
        """Display code differences."""
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_row(
            Panel(Syntax(original, "python", theme="monokai"), 
                  title="Original", 
                  border_style="red"),
            Panel(Syntax(new, "python", theme="monokai"), 
                  title="New", 
                  border_style="green")
        )
        console.print(table)
    
    def format_error(self, message: str) -> None:
        """Format error messages."""
        console.print(f"[error]✗ Error:[/error] {message}")
    
    def format_success(self, message: str) -> None:
        """Format success messages."""
        console.print(f"[success]✓ Success:[/success] {message}")
```

### 2. Progress Indicators

```python
class ProgressManager:
    """Manages progress indicators and spinners."""
    
    def file_operation_progress(self, operation: str) -> Progress:
        """Create progress bar for file operations."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn()
        )
    
    def api_call_spinner(self, message: str) -> Status:
        """Create spinner for API calls."""
        return Status(message, spinner="dots")
```

## Component Styling

### 1. File Operation Display

```python
class FileOperationDisplay:
    """Handles display of file operations."""
    
    def show_file_tree(self, path: str) -> None:
        """Display file tree with custom styling."""
        tree = Tree(
            f":open_file_folder: {path}",
            guide_style="bold bright_blue"
        )
        self._build_tree(path, tree)
        console.print(tree)
    
    def show_diff_preview(self, diff: Dict[str, str]) -> None:
        """Display diff preview with syntax highlighting."""
        table = Table(
            title="File Changes Preview",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
            box=box.DOUBLE
        )
        # Table implementation...
```

### 2. Response Formatting

```python
class ResponseFormatter:
    """Formats AI responses with styling."""
    
    def format_response(self, response: str) -> None:
        """Format AI response with custom styling."""
        panel = Panel(
            response,
            title="AI Response",
            border_style="bright_blue",
            padding=(1, 2)
        )
        console.print(panel)
    
    def format_code_suggestion(self, code: str) -> None:
        """Format code suggestions with syntax highlighting."""
        panel = Panel(
            Syntax(code, "python", theme="monokai"),
            title="Suggested Code",
            border_style="green"
        )
        console.print(panel)
```

## Custom Components

### 1. Creating Custom Components

```python
class CustomComponent:
    """Base class for custom UI components."""
    
    def __init__(self, style: Dict[str, str]):
        self.style = style
    
    def render(self) -> None:
        """Render the component."""
        raise NotImplementedError
```

### 2. Example Implementation

```python
class CodePreview(CustomComponent):
    """Custom component for code preview."""
    
    def render(self, code: str) -> None:
        """Render code preview with custom styling."""
        panel = Panel(
            Syntax(code, "python", theme="monokai"),
            title="Code Preview",
            border_style=self.style.get("border", "bright_blue"),
            padding=self.style.get("padding", (1, 2))
        )
        console.print(panel)
```

## Configuration

### 1. User Configuration

Create `~/.config/deepseek-engineer/appearance.json`:
```json
{
    "theme": "dark",
    "syntax_theme": "monokai",
    "font_size": 12,
    "components": {
        "code_preview": {
            "border_style": "bright_blue",
            "padding": [1, 2]
        },
        "diff_view": {
            "border_style": "magenta",
            "show_line_numbers": true
        }
    }
}
```

### 2. Loading Configuration

```python
class AppearanceConfig:
    """Manages appearance configuration."""
    
    def __init__(self):
        self.config_path = Path.home() / ".config" / "deepseek-engineer" / "appearance.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return self._default_config()
```

## Best Practices

1. **Theme Consistency**
   - Use consistent color schemes
   - Maintain readable contrast ratios
   - Follow accessibility guidelines

2. **Performance**
   - Cache rendered components
   - Optimize rendering for large outputs
   - Use appropriate update intervals

3. **Accessibility**
   - Support high contrast modes
   - Provide configurable font sizes
   - Include screen reader support

4. **Customization**
   - Allow user overrides
   - Support multiple themes
   - Enable component-level styling

## Future Enhancements

1. **Theme System**
   - Additional built-in themes
   - Theme hot-reloading
   - Custom theme sharing

2. **Components**
   - More interactive elements
   - Enhanced visualizations
   - Improved animations

3. **Accessibility**
   - Enhanced screen reader support
   - Keyboard navigation
   - Color blind modes