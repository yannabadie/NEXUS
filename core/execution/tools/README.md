# Tool Manager Package

V10.2 modular split of `tool_manager.py` (63.6KB, 1848 lines).

## Structure

```
tools/
├── __init__.py        # Re-exports ToolManager, ToolResult
├── file_helpers.py    # read/write/edit helpers (180 lines)
├── bash_helpers.py    # bash command helpers (140 lines)
├── search_helpers.py  # glob/grep helpers (150 lines)
├── web_helpers.py     # web_search/fetch helpers (160 lines)
└── README.md          # This file
```

## Module Contents

| Module | Functions |
|--------|-----------|
| `file_helpers` | `safe_read_file`, `safe_write_file`, `format_directory_listing` |
| `bash_helpers` | `parse_bash_command`, `is_simple_command`, `format_bash_output` |
| `search_helpers` | `format_glob_results`, `format_grep_results`, `compile_pattern` |
| `web_helpers` | `validate_url`, `format_web_content`, `strip_html_tags` |

## Usage

```python
# Main imports
from core.execution.tools import ToolManager, ToolResult

# Helpers
from core.execution.tools.file_helpers import safe_read_file
from core.execution.tools.bash_helpers import is_simple_command
```
