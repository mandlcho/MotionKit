# xMobu Quick Start Guide

## Installation (5 minutes)

### Step 1: Get xMobu
```bash
git clone <repository-url> C:\xMobu
cd C:\xMobu
```

### Step 2: Run Installer
Double-click `install.bat` and follow the prompts:
- The installer will detect your MotionBuilder installations
- Choose which version(s) to configure
- Press any key to complete

### Step 3: Launch MotionBuilder
Start MotionBuilder and look for the **xMobu** menu in the menu bar!

## Uninstallation

To remove xMobu:

1. Double-click `uninstall.bat`
2. Choose which MotionBuilder version(s) to remove from
3. Restart MotionBuilder

The xMobu files remain in the directory for easy reinstallation.

## First Steps

### Accessing Tools

All tools are organized under the **xMobu** menu:

```
xMobu
├── Animation
│   └── Keyframe Tools
├── Rigging
│   └── Constraint Helper
├── Pipeline
│   └── Scene Manager
├── Unreal Engine
│   └── UE Content Browser
├── ───────────────
├── Settings...
├── Reload xMobu
├── ───────────────
└── About xMobu
```

### Configuration

Edit `config/config.json` to customize:

```json
{
    "unreal": {
        "default_project_path": "C:/UnrealProjects/MyProject/MyProject.uproject"
    }
}
```

Then use **xMobu > Reload xMobu** to apply changes.

## Creating Your First Tool

### 1. Create a new tool file

Create `mobu/tools/animation/my_tool.py`:

```python
from pyfbsdk import FBMessageBox
from core.logger import logger

TOOL_NAME = "My First Tool"

def execute(control, event):
    logger.info("Hello from my tool!")
    FBMessageBox("Success", "My first xMobu tool!", "OK")
```

### 2. Reload xMobu

In MotionBuilder: **xMobu > Reload xMobu**

### 3. Test it

Click **xMobu > Animation > My First Tool**

That's it! Your tool now appears in the menu automatically.

## Common Tasks

### Export Animation to Unreal

1. Select character/objects in MotionBuilder
2. **xMobu > Unreal Engine > UE Content Browser**
3. Configure export settings
4. Animation is automatically imported to Unreal

### Batch Processing

1. **xMobu > Pipeline > Scene Manager**
2. Select files to process
3. Choose operation
4. Run batch process

### Reload Tools During Development

After making changes to tool code:
- **xMobu > Reload xMobu** (or restart MotionBuilder)
- Changes take effect immediately

## Tips

- **Check the console**: Errors and info messages appear in MotionBuilder's Python console
- **Use the logger**: `logger.info("message")` for debugging
- **Tool templates**: Copy existing tools as starting templates
- **Config overrides**: Create `config/local_config.json` for personal settings (won't be committed to git)

## Troubleshooting

### Menu doesn't appear
- Check MotionBuilder console for errors
- Verify installation: Look for `xmobu_init.py` in `MotionBuilder/bin/config/PythonStartup/`
- Try manual initialization in Python console: `import mobu.startup`

### Tool doesn't show up
- Verify file is in correct category folder
- Check that `TOOL_NAME` and `execute` are defined
- Use **Reload xMobu** after adding new tools
- Check console for import errors

### Import errors
- Ensure MotionBuilder 2020+ (Python 3 required)
- Check file for syntax errors
- Verify all imports are available in MotionBuilder

## Next Steps

- Read [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide
- Explore example tools in `mobu/tools/`
- Customize configuration in `config/config.json`
- Create your own pipeline tools

## Getting Help

- Check the [README.md](README.md) for overview
- Read [DEVELOPMENT.md](DEVELOPMENT.md) for technical details
- Check console output for error messages
- Review example tools for patterns

---

**Happy Pipeline Building!** 🚀
