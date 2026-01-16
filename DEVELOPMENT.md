# MotionKit Development Guide

## Architecture Overview

MotionKit is designed with a modular, DCC-agnostic architecture that allows easy extension to multiple applications.

### Directory Structure

```
MotionKit/
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

## Fast Development Workflow (No Reinstall Required!)

### Method 1: Use the Menu (Easiest)

1. Make changes to your Python files
2. In MotionBuilder: **MotionKit > Reload MotionKit**
3. Test your changes immediately

This reloads all modules and rebuilds the menu without restarting MotionBuilder.

### Method 2: Python Console (Fastest)

For rapid iteration, use the Python Console (View > Python Console):

**First time setup:**
```python
exec(open(r'C:\Users\elementa\projects\MotionKit\quick_reload.py').read())
```

**Subsequent reloads (after first run):**
```python
reload_motionkit()
```

This reloads all MotionKit modules in seconds!

### Method 3: Keyboard Shortcut (Advanced)

1. Open MotionBuilder's Keyboard Editor
2. Create a shortcut (e.g., Ctrl+Shift+R)
3. Assign it to run: `exec(open(r'C:\Users\elementa\projects\MotionKit\quick_reload.py').read())`

Now press your shortcut to reload instantly!

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

### 3. Test Your Tool

**No installation needed!** Just:
1. Save your new tool file
2. Run `reload_motionkit()` in Python Console (or use MotionKit > Reload MotionKit)
3. Your tool appears in the menu automatically

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
        "menu_name": "MotionKit",
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

Console output is prefixed with `[MotionKit]` for easy filtering.

## Best Practices

1. **Error Handling**: Always wrap tool logic in try/except blocks
2. **User Feedback**: Provide clear feedback via message boxes or logging
3. **Selection Validation**: Check user selection before operating
4. **Undo Support**: Use MotionBuilder's undo system when modifying scene
5. **Performance**: Log performance-critical operations
6. **Documentation**: Add docstrings to functions and classes
7. **Iterative Testing**: Use `reload_motionkit()` frequently during development

## Debugging Tips

### Check Console Output

All MotionKit messages start with `[MotionKit]`:
```
[MotionKit] Initialization completed successfully!
[MotionKit] Building category: Animation
[MotionKit]   Found 1 tool(s) in Animation
```

### Test Tool Directly

You can test tool functions directly in the console:
```python
from mobu.tools.animation.keyframe_tools import execute
execute(None, None)  # Test the tool
```

### Reload Specific Module

For targeted testing:
```python
import importlib
import mobu.tools.animation.keyframe_tools
importlib.reload(mobu.tools.animation.keyframe_tools)
```

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
    menu_name = config.get('maya.menu_name', 'MotionKit')
    if cmds.menu(menu_name, exists=True):
        cmds.deleteUI(menu_name)

    menu = cmds.menu(menu_name, parent='MayaWindow', label=menu_name)
    # Build submenus...
```

## Troubleshooting

### Tools Not Appearing After Reload

1. Check file naming (no underscores at start)
2. Verify `TOOL_NAME` constant exists
3. Verify `execute(control, event)` function exists
4. Check console for import errors
5. Look for Python syntax errors

### Reload Fails

1. Check console for full traceback
2. Look for syntax errors in your code
3. Ensure all imports are available
4. Try restarting MotionBuilder if modules are corrupted

### Import Errors

1. Ensure MotionKit root is in Python path (check console on startup)
2. Check for syntax errors in tool files
3. Verify all required imports are available in MotionBuilder
4. Check MotionBuilder Python version compatibility (3.7+)

## Contributing

When contributing tools:

1. Follow the tool structure template
2. Add appropriate error handling
3. Include docstrings
4. Test with `reload_motionkit()` during development
5. Test with fresh MotionBuilder startup
6. Update this documentation if needed

## Performance Tips

- **Lazy imports**: Import heavy modules inside functions when possible
- **Cache data**: Store expensive computations in class variables
- **Profile**: Use Python's `time` module to identify bottlenecks
- **Batch operations**: Process multiple items in one pass when possible

## Common Patterns

### Getting Selected Objects

```python
from pyfbsdk import FBModelList, FBGetSelectedModels

selected = FBModelList()
FBGetSelectedModels(selected)

if len(selected) == 0:
    FBMessageBox("Error", "Please select objects", "OK")
    return

for model in selected:
    print(model.Name)
```

### Working with Animation

```python
from pyfbsdk import FBPlayerControl, FBTime

player = FBPlayerControl()
current_frame = player.GetEditCurrentTime().GetFrame()

# Set keyframe
model.Translation.SetAnimated(True)
model.Translation.GetAnimationNode().KeyAdd(FBTime(0, 0, 0, current_frame))
```

### Scene File Operations

```python
from pyfbsdk import FBApplication

app = FBApplication()
current_file = app.FBXFileName

# Save
app.FileSave()

# Open
app.FileOpen("path/to/file.fbx")
```

---

**Happy Development!** Remember: Use `reload_motionkit()` for instant testing - no MotionBuilder restart needed!
