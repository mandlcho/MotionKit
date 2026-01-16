# MotionKit - DCC Pipeline Toolset

A comprehensive, easy-to-deploy pipeline toolset for Autodesk MotionBuilder with future integration support for Maya and 3ds Max.

## Features

- **Easy Installation**: One-click batch installer automatically configures MotionBuilder
- **Menu Integration**: Access all tools from the MotionKit menu in MotionBuilder
- **Organized Tools**: Tools categorized into Animation, Rigging, Pipeline, and Unreal Engine integration
- **Extensible Architecture**: DCC-agnostic core designed for future Maya and Max integration
- **Python 3**: Compatible with MotionBuilder 2020+

## Installation

1. Clone or download this repository
2. Run `install.bat`
3. Follow the prompts to configure your MotionBuilder installation
4. Restart MotionBuilder

The installer will automatically:
- Detect your MotionBuilder installation
- Configure the Python startup path
- Set up the MotionKit menu system

## Uninstallation

To remove MotionKit from MotionBuilder:

1. Run `uninstall.bat`
2. Choose which MotionBuilder versions to uninstall from
3. Restart MotionBuilder

The uninstaller removes only the startup integration. The MotionKit files remain in your directory for easy reinstallation.

## Usage

After installation, launch MotionBuilder and you'll find the **MotionKit** menu in the menu bar with the following categories:

- **Animation**: Tools for keyframe manipulation, retargeting, and mocap cleanup
- **Rigging**: Character setup and rig utilities
- **Pipeline**: File management, batch processing, and asset publishing
- **Unreal Engine**: Direct integration with Unreal Engine's content browser

## Project Structure

```
MotionKit/
├── install.bat              # Automatic installer
├── uninstall.bat            # Automatic uninstaller
├── core/                    # DCC-agnostic core framework
├── mobu/                    # MotionBuilder integration
│   ├── startup.py          # MotionBuilder startup script
│   ├── menu_builder.py     # Menu system
│   └── tools/              # Tool implementations
├── config/                  # Configuration files
└── resources/              # Icons and UI resources
```

## Configuration

Edit `config/config.json` to customize:
- Menu layout
- Tool categories
- Unreal Engine project paths
- Custom tool paths

## Development

### Adding New Tools

1. Create a new Python file in the appropriate category folder (e.g., `mobu/tools/animation/`)
2. Implement your tool class
3. Register it in the category's `__init__.py`
4. The menu system will automatically detect and add it

### Future DCC Support

The core framework is designed to be DCC-agnostic. Maya and Max integrations follow the same pattern as the `mobu/` directory.

## Requirements

- MotionBuilder 2020 or newer
- Python 3.7+
- Windows (installer currently Windows-only, manual setup possible on other platforms)

## License

[Your License Here]
