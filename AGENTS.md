# MotionKit Agent Guidelines

This document provides guidelines for coding agents working on the MotionKit codebase. MotionKit is a multi-DCC pipeline toolset supporting MotionBuilder, 3ds Max, and Maya.

## Build/Lint/Test Commands

### Running Tests
```bash
# Run all tests
python -m unittest discover tests/

# Run specific test file
python -m unittest tests.test_foot_sync_presets

# Run specific test class
python -m unittest tests.test_foot_sync_presets.TestPresetValidation

# Run specific test method
python -m unittest tests.test_foot_sync_presets.TestPresetValidation.test_valid_preset

# Run with verbose output
python -m unittest discover tests/ -v
```

### Code Quality
```bash
# No formal linter configured - use Python best practices
# The codebase follows PEP 8 style guidelines manually
```

### Installation
```bash
# Install dependencies (if any)
pip install -r requirements.txt  # (none currently specified)

# Run installer for DCC integration
install.bat  # Windows only - configures MotionBuilder/Max
```

## Code Style Guidelines

### Imports
```python
# Standard library imports first
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Third-party imports second
import json

# Local imports last (relative imports)
from core.logger import logger
from core.config import config
from core.localization import t
```

### DCC-Specific Imports
```python
# Always wrap DCC imports in try/except
try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[ToolName] ERROR: pymxs not available")
    pymxs = None
    rt = None

try:
    from pyfbsdk import *
except ImportError:
    print("[ToolName] ERROR: pyfbsdk not available")
    # Define mock objects if needed for testing
```

### Naming Conventions

#### Files and Modules
- Use `snake_case.py` for module names
- Use `PascalCase.py` for main tool files
- `__init__.py` files should be minimal

#### Classes and Functions
```python
# Classes: PascalCase
class MyToolClass:
    pass

# Functions: snake_case
def my_utility_function():
    pass

# Private methods: _underscore_prefix
def _private_method(self):
    pass

# Constants: UPPER_CASE
TOOL_NAME = "My Tool"
MAX_VERSION = 2023
```

#### Variables
```python
# snake_case for all variables
my_variable = 42
config_data = {}
selected_objects = []
```

### Tool Structure Pattern
```python
"""
Tool description for MotionKit
Brief description of what the tool does
"""

# DCC imports (with try/except)
try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    pymxs = None
    rt = None

# Core imports
from core.logger import logger
from core.localization import t
from core.config import config

# Tool constant (required)
TOOL_NAME = "Tool Display Name"

def execute(control=None, event=None):
    """Main execution function called by menu system"""
    if not pymxs or not rt:
        print("[ToolName] ERROR: Not running in 3ds Max")
        return

    try:
        # Tool implementation
        dialog = MyToolDialog()
        dialog.show()
    except Exception as e:
        logger.error(f"Failed to open tool: {str(e)}")
        rt.messageBox(f"Failed to open tool: {str(e)}", title="MotionKit Error")

class MyToolDialog:
    """Dialog class for tool UI"""

    def show(self):
        """Show the dialog using MaxScript or Qt"""
        # Implementation
        pass
```

### Error Handling

#### Use try/except liberally
```python
try:
    result = some_dcc_operation()
    if result is None:
        raise ValueError("Operation failed")
except Exception as e:
    logger.error(f"Operation failed: {str(e)}")
    # Show user-friendly message if in DCC
    if rt:
        rt.messageBox(f"Error: {str(e)}", title="Tool Name Error")
    return False
```

#### Log errors with context
```python
try:
    # risky operation
    pass
except FileNotFoundError as e:
    logger.error(f"Config file not found: {config_path}")
    logger.error(f"Error details: {str(e)}")
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config: {str(e)}")
    logger.error(f"Line {e.lineno}: {e.msg}")
```

### Logging

#### Use the centralized logger
```python
from core.logger import logger

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning about potential issues")
logger.error("Error conditions")
```

#### Log levels:
- `debug`: Detailed technical information
- `info`: General user-facing information
- `warning`: Potential issues that don't break functionality
- `error`: Actual errors and exceptions

### Configuration

#### Use the config system
```python
from core.config import config

# Get values with defaults
setting_value = config.get('category.setting', 'default_value')
user_name = config.get('user.name', 'Unknown')

# Set values
config.set('category.setting', 'new_value')
```

#### Config hierarchy:
- `config/local_config.json` (user overrides, not in git)
- `config/config.json` (default config)
- Runtime overrides via config.set()

### Localization

#### Use the translation system
```python
from core.localization import t

# Get translated strings
title = t('tools.mytool.title')
button_text = t('common.ok')

# Fallback to English if translation missing
custom_text = t('my.custom.key', 'Default English Text')
```

#### Translation files:
- `localization/en.json`
- `localization/zh.json`
- `localization/ko.json`

### Type Hints

#### Use type hints where helpful
```python
from typing import Dict, List, Optional, Tuple, Union

def process_data(data: Dict[str, Union[str, int]]) -> Optional[List[str]]:
    """Process data and return results or None"""
    pass

class MyClass:
    def __init__(self, name: str, value: int = 0) -> None:
        self.name: str = name
        self.value: int = value
```

### File Structure

#### Maintain the established structure:
```
MotionKit/
├── core/                    # DCC-agnostic core modules
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging system
│   ├── localization.py     # Translation system
│   └── utils.py            # Utility functions
├── max/                     # 3ds Max integration
│   ├── tools/
│   │   ├── animation/      # Animation tools
│   │   ├── pipeline/       # Pipeline tools
│   │   └── unrealengine/   # UE integration
│   └── menu_builder.py     # Max menu system
├── mobu/                    # MotionBuilder integration
├── config/                  # Configuration files
│   ├── config.json         # Default config
│   ├── foot_sync_presets.json  # Character presets (gitignored)
│   └── foot_sync_presets.example.json  # Template
├── tests/                   # Unit tests
└── localization/           # Translation files
```

### Documentation

#### Docstrings required for:
- All public functions
- All classes
- Complex private methods

```python
def my_function(param1: str, param2: int = 0) -> bool:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)

    Returns:
        bool: True on success, False on failure

    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

#### Module docstrings:
```python
"""
Module description for MotionKit
Detailed explanation of the module's purpose and functionality
"""
```

### Testing

#### Unit test structure:
```python
import unittest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestMyFeature(unittest.TestCase):
    """Test cases for my feature"""

    def setUp(self):
        """Set up test fixtures"""
        pass

    def tearDown(self):
        """Clean up test fixtures"""
        pass

    def test_basic_functionality(self):
        """Test basic functionality"""
        result = my_function("test")
        self.assertEqual(result, "expected")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        with self.assertRaises(ValueError):
            my_function(None)
```

#### Mock DCC APIs for testing:
```python
# Mock pymxs for testing outside Max
try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    # Create mock objects for testing
    class MockRuntime:
        def messageBox(self, msg, title=""): pass
        def queryBox(self, msg, title=""): return True

    rt = MockRuntime()
    pymxs = None
```

### Git Workflow

#### Commit message format:
```
type: Brief description of changes

- Detailed change 1
- Detailed change 2
- Fixes issue #123
```

#### Protected files (don't commit):
- `config/foot_sync_presets.json` (character presets)
- `ANIMAX_EXTRACTED_FUNCTIONS.txt` (reverse-engineered code)
- `config/local_config.json` (user settings)

#### Branch naming:
- `feature/tool-name` for new tools
- `bugfix/issue-description` for bug fixes
- `refactor/component-name` for refactoring

### Performance Considerations

#### Avoid unnecessary DCC API calls:
```python
# Bad - calls API every time
def get_object_count():
    return len(rt.objects)

# Good - cache when possible
_object_count = None
def get_object_count():
    global _object_count
    if _object_count is None:
        _object_count = len(rt.objects)
    return _object_count
```

#### Use efficient data structures:
```python
# Prefer sets for membership testing
selected_names = {obj.name for obj in selection}

# Use list comprehensions over loops
valid_objects = [obj for obj in objects if is_valid(obj)]
```

### Security

#### Input validation:
```python
def process_file(file_path: str) -> bool:
    """Process a file safely"""
    if not isinstance(file_path, str):
        raise TypeError("file_path must be a string")

    # Prevent directory traversal
    if ".." in file_path or file_path.startswith("/"):
        raise ValueError("Invalid file path")

    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Implementation...
    pass
```

#### Avoid eval/exec:
```python
# Bad
user_code = input("Enter code: ")
eval(user_code)

# Good - use safe alternatives
allowed_values = {'option1', 'option2', 'option3'}
if user_input in allowed_values:
    process_option(user_input)
```

This document should be updated as the codebase evolves. Follow these guidelines to maintain consistency and quality across the MotionKit project.