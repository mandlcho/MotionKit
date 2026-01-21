# DCCKit Installer

Simple, compact Python installer for DCCKit with multi-language support!

## Quick Start

### Double-Click Method
1. Double-click **`run_installer.bat`**
2. Done!

### Command Line
```bash
python dcckit_installer.py
```

## Requirements

- **Python 3.7+** (that's it!)
- tkinter (comes with Python by default)

## Features

✅ **Multi-Language Support** - English, Chinese (中文), Korean (한국어)
✅ **Auto DCC Detection** - Finds MotionBuilder & 3ds Max automatically
✅ **Selective Installation** - Choose which DCC versions to install to
✅ **Three Installation Profiles** (via dropdown):
- **Artist** - Essential tools only
- **Animator** - Full suite (recommended)
- **Expert** - Everything + debug tools

✅ **Compact UI** - Small window footprint (500x450)
✅ **Dark Theme** - Matches DCC environments
✅ **Progress Tracking** - See installation progress
✅ **No Dependencies** - Uses built-in tkinter

## Files

- **`dcckit_installer.py`** - Main installer script
- **`run_installer.bat`** - Easy launcher (double-click this!)
- **`INSTALLER.md`** - This file

## Using the Installer

### Language Switcher
1. Click the language dropdown in the top-right
2. Select: **EN** (English) / **CN** (中文) / **KR** (한국어)
3. All text updates instantly!

### DCC Selection
- **Checkboxes** appear for each detected DCC version
- **Check/Uncheck** to select which ones to install to
- All detected versions are **selected by default**
- You can install to multiple versions at once

### Installation Profile
- Use the **dropdown** to select your profile:
  - **Artist**: Animation, Character Mapping, Scene Manager
  - **Animator**: Full suite with Unreal integration
  - **Expert**: Everything + Debug + Experimental features

## Customization

### Colors
All colors are in the `DCCKitInstaller` class:
- `self.bg_color` - Background color (#2b2b2b)
- `self.accent_color` - Accent/brand color (#0d7377)
- `self.success_color` - Success messages (#4CAF50)
- `self.error_color` - Error messages (#f44336)

### Translations
Add more languages in the `TRANSLATIONS` dictionary:
```python
TRANSLATIONS = {
    'EN': {...},
    'CN': {...},
    'KR': {...},
    'JP': {...}  # Add Japanese, etc.
}
```

### Window Size
Change in `__init__`:
```python
self.root.geometry("500x450")  # width x height
```

## Installation Logic

The actual installation logic is in the `run_installation()` method. Currently it's a placeholder - replace it with your actual installation code:

```python
def run_installation(self, profile):
    # Your installation code here
    # - Copy files
    # - Configure startup scripts
    # - Update config files
    pass
```

## That's It!

Clean, simple, no complications. Just Python + tkinter.
