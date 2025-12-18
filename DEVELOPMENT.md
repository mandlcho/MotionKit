# xMobu Development Guide

## Architecture Overview

xMobu is designed with a modular, DCC-agnostic architecture that allows easy extension to multiple applications.

### Directory Structure

```
xMobu/
├── core/                   # DCC-agnostic core functionality
│   ├── logger.py          # Centralized logging
│   ├── config.py          # Configuration management
│   └── utils.py           # Utility functions
├── mobu/                   # MotionBuilder-specific code
│   ├── startup.py         # Entry point for MotionBuilder
│   ├── menu_builder.py    # Menu system
│   └── tools/             # Tool implementations
├── maya/                   # Future Maya integration
├── max/                    # Future 3ds Max integration
└── config/                 # Configuration files
```

## Adding New Tools

### 1. Create Tool File

Create a new Python file in the appropriate category folder:
- Animation: `mobu/tools/animation/`
- Rigging: `mobu/tools/rigging/`
- Pipeline: `mobu/tools/pipeline/`
- Unreal: `mobu/tools/unreal/`

### 2. Implement Tool Structure

Every tool must follow this structure:

```python
from pyfbsdk import FBMessageBox
from core.logger import logger

# Required: Tool name that appears in menu
TOOL_NAME = "My Awesome Tool"


# Required: Execute function called when menu item is clicked
def execute(control, event):
    """Main execution function"""
    logger.info("My Awesome Tool executed")

    try:
        # Your tool logic here
        FBMessageBox("My Tool", "Hello from my tool!", "OK")

    except Exception as e:
        logger.error(f"Tool error: {str(e)}")
        FBMessageBox("Error", f"An error occurred: {str(e)}", "OK")
```

### 3. Tool Discovery

Tools are automatically discovered by the menu system. The `menu_builder.py` scans tool folders and looks for:
- `TOOL_NAME` constant (string): Display name in menu
- `execute` function (callable): Function called on menu click

No registration needed - just create the file and restart MotionBuilder!

## Creating Custom UIs

For tools that need custom interfaces, use MotionBuilder's UI system:

```python
from pyfbsdk import (
    FBTool, FBLayout, FBButton,
    FBAddTool, FBAttachType
)

TOOL_NAME = "Advanced Tool"


class MyToolUI(FBTool):
    def __init__(self, name):
        FBTool.__init__(self, name)
        self.BuildUI()

    def BuildUI(self):
        x = FBAddRegionParam(0, FBAttachType.kFBAttachLeft, "")
        y = FBAddRegionParam(0, FBAttachType.kFBAttachTop, "")
        w = FBAddRegionParam(0, FBAttachType.kFBAttachRight, "")
        h = FBAddRegionParam(0, FBAttachType.kFBAttachBottom, "")

        main = FBLayout()
        self.AddRegion("main", "main", x, y, w, h)
        self.SetControl("main", main)

        # Add UI elements to main layout
        # ...


def execute(control, event):
    """Show the tool UI"""
    tool = MyToolUI("My Advanced Tool")
    tool.StartSizeX = 400
    tool.StartSizeY = 300
    ShowTool(tool)
```

## Configuration

### Modifying Config

Edit `config/config.json` to customize:

```json
{
    "mobu": {
        "menu_name": "xMobu",
        "tool_categories": [
            {"name": "Animation", "enabled": true},
            {"name": "Custom Category", "enabled": true}
        ]
    }
}
```

### Accessing Config in Tools

```python
from core.config import config

# Get config value
unreal_path = config.get('unreal.default_project_path', '/default/path')

# Set config value
config.set('unreal.default_project_path', 'C:/MyProject')
config.save()
```

## Logging

Use the centralized logger in all tools:

```python
from core.logger import logger

logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

## Best Practices

1. **Error Handling**: Always wrap tool logic in try/except blocks
2. **User Feedback**: Provide clear feedback via message boxes or logging
3. **Selection Validation**: Check user selection before operating
4. **Undo Support**: Use MotionBuilder's undo system when modifying scene
5. **Performance**: Log performance-critical operations
6. **Documentation**: Add docstrings to functions and classes

## Testing

Test your tools by:

1. Making changes to tool files
2. In MotionBuilder, use xMobu > Reload xMobu menu
3. Test the tool functionality
4. Check the console for log output

## Future DCC Integration

When adding Maya or Max support:

1. Create similar structure in `maya/` or `max/` folder
2. Implement DCC-specific menu builder
3. Reuse core functionality from `core/` module
4. Tools can share logic through core utilities

### Example Maya Integration

```python
# maya/menu_builder.py
import maya.cmds as cmds
from core.config import config

def build_menu():
    menu_name = config.get('maya.menu_name', 'xMobu')
    if cmds.menu(menu_name, exists=True):
        cmds.deleteUI(menu_name)

    menu = cmds.menu(menu_name, parent='MayaWindow', label=menu_name)
    # Build submenus...
```

## Troubleshooting

### Tools Not Appearing

1. Check file naming (no underscores at start)
2. Verify `TOOL_NAME` constant exists
3. Verify `execute(control, event)` function exists
4. Check console for import errors
5. Use "Reload xMobu" from menu

### Import Errors

1. Ensure xMobu root is in Python path
2. Check for syntax errors in tool files
3. Verify all required imports are available
4. Check MotionBuilder Python version compatibility

## Contributing

When contributing tools:

1. Follow the tool structure template
2. Add appropriate error handling
3. Include docstrings
4. Test thoroughly
5. Update this documentation if needed
