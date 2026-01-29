# Unreal Engine Max LiveLink - Installation Guide

## 🎯 Easiest Method: Use the DCCKit Installer GUI

### **One-Click Installation:**

1. **Run the installer:**
   ```bash
   python dcckit_installer.py
   ```

2. **In the installer window:**
   - Check the box: `⚡ Install Unreal Engine Max LiveLink`
   - Verify or browse to set the **UE Python Path**
     - Default: `C:\Users\[YourName]\Documents\UnrealEngine\Python`
   - Click **Install**

3. **Done!** The `init_unreal.py` script is automatically copied to your UE Python folder

4. **Restart Unreal Engine** to see the menu: `Tools → Max LiveLink`

---

## 📋 What the Installer Does

The installer copies `init_unreal.py` to your Unreal Engine Python startup folder:
- **Source:** `MotionKit/unreal_scripts/init_unreal.py`
- **Destination:** `[UE Python Path]/init_unreal.py`

This script auto-installs the Max LiveLink menu every time Unreal Engine starts.

---

## 🔧 Manual Installation (Alternative)

If you prefer manual installation:

1. **Copy the file:**
   ```
   From: MotionKit/unreal_scripts/init_unreal.py
   To:   C:\Users\[YourName]\Documents\UnrealEngine\Python\init_unreal.py
   ```

2. **Restart Unreal Engine**

3. **Done!**

---

## ✅ After Installation

You'll see: **Tools → Max LiveLink** with these options:
- ▶ **Start Max LiveLink Server** - Start the server
- ■ **Stop Max LiveLink Server** - Stop the server
- 🔧 **Test Connection** - Check if running

---

## 🎨 Features

✅ **Auto-installs on UE startup** - No manual steps after setup  
✅ **Works in all UE projects** - Global installation  
✅ **GUI installer** - No command-line needed  
✅ **Auto-detects UE path** - Smart path detection  
✅ **One-click install** - Simplest possible workflow  

---

## 🔧 Troubleshooting

**Menu doesn't appear?**
- Check Output Log for errors
- Make sure Python plugin is enabled: `Edit → Plugins → Python Editor Script Plugin`
- Verify file exists: `[UE Path]\Python\init_unreal.py`

**Can't find UE Python folder?**
- Default location: `C:\Users\[YourName]\Documents\UnrealEngine\Python`
- If folder doesn't exist, create it manually
- Browse using the `...` button in the installer

**Need to uninstall?**
- Delete `init_unreal.py` from UE Python folder
- Restart UE

---

## 📦 What's Included

- **dcckit_installer.py** - GUI installer with Unreal Engine support
- **init_unreal.py** - Auto-startup script for UE
- **install_max_livelink.py** - Menu installer (called by init_unreal.py)
- **max_live_link_server.py** - LiveLink server implementation

---

## 💡 Why This Method?

| Method | Steps | Persists? | Per-Project? |
|--------|-------|-----------|--------------|
| **GUI Installer** | 1 click | ✅ Yes | ❌ No (Global) |
| Manual Copy | 1 file copy | ✅ Yes | ❌ No (Global) |
| Python Console | Paste code | ✅ Yes | ✅ Yes |

**Recommendation:** Use the GUI installer - it's the fastest and works everywhere!
