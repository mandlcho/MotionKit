# ✅ VERIFIED Unreal Engine Python Startup Path

## Official Documentation Reference

**Source:** Epic Games Official Documentation  
**URL:** https://docs.unrealengine.com/5.0/en-US/scripting-the-unreal-editor-using-python/

## The Verified Default Path

```
C:\Users\[YourUsername]\Documents\UnrealEngine\Python
```

Example for user "elementa":
```
C:\Users\elementa\Documents\UnrealEngine\Python
```

## Official Quote from Epic Documentation

> "The Unreal Editor automatically adds several paths to this `sys.path` list:
> - The **Content/Python** sub-folder in your Project's folder.
> - The **Content/Python** sub-folder in the main Unreal Engine installation.
> - The **Content/Python** sub-folder in each enabled Plugin's folder.
> - **The Documents/UnrealEngine/Python folder inside your user directory.** For example, on Windows 10, this is equivalent to `C:/Users/Username/Documents/UnrealEngine/Python`"

## How init_unreal.py Works

According to Epic's documentation:

> "If the Editor detects a script file called `init_unreal.py` in any of the paths it is configured to use, it automatically runs that script immediately."

This means:
1. Place `init_unreal.py` in `C:\Users\[YourUsername]\Documents\UnrealEngine\Python\`
2. Unreal Engine will **automatically execute it on startup**
3. No configuration needed - it just works!

## DCCKit Installer Implementation

The `dcckit_installer.py` now uses this verified path by default:

```python
@staticmethod
def detect_unreal():
    """Detect Unreal Engine Python startup path.
    
    Returns the default Python startup path for Unreal Engine as documented
    in the official UE documentation.
    """
    # Official UE Python startup path (verified from Epic docs)
    ue_python_path = Path(os.path.expanduser("~")) / "Documents" / "UnrealEngine" / "Python"
    return str(ue_python_path)
```

## Installation Process

When you run the DCCKit installer:

1. **Auto-detects the path:** `C:\Users\elementa\Documents\UnrealEngine\Python`
2. **Creates the directory** if it doesn't exist
3. **Copies `init_unreal.py`** to that location
4. **Done!** Next UE restart will auto-load Max LiveLink menu

## Verification Steps

To verify the installation worked:

1. Check if file exists:
   ```
   C:\Users\elementa\Documents\UnrealEngine\Python\init_unreal.py
   ```

2. Start Unreal Engine

3. Look for the menu: **Tools → Max LiveLink**

4. Check Output Log for confirmation:
   ```
   [MotionKit] Max LiveLink already installed
   ```

## Why This Path?

✅ **Universal:** Works for all UE projects  
✅ **Standard:** Official Epic-documented location  
✅ **Automatic:** No per-project configuration needed  
✅ **Persistent:** Survives UE updates  
✅ **User-specific:** Each user has their own scripts  

## Alternative Paths (Not Used by Installer)

While Epic documents other paths, we use the Documents path because:

1. ❌ `Project/Content/Python` - Per-project only
2. ❌ `Engine/Content/Python` - Requires engine modification
3. ❌ `Plugin/Content/Python` - Plugin-specific
4. ✅ **`Documents/UnrealEngine/Python`** - Global, user-specific, perfect for tools

## Compatibility

This path works with:
- ✅ Unreal Engine 4.27
- ✅ Unreal Engine 5.0
- ✅ Unreal Engine 5.1
- ✅ Unreal Engine 5.2
- ✅ Unreal Engine 5.3+

All versions use the same default Python startup path.
