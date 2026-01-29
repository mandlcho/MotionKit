# Max LiveLink Setup Guide

**Stream animation data from Unreal Engine to 3ds Max in real-time!**

This guide shows you how to set up the Max LiveLink server in Unreal Engine with **just copy-paste**—no plugins, no complex setup.

---

## 📋 What You'll Get

After setup, you'll have:
- ✅ **Tools → Max LiveLink** menu in Unreal Engine
- ✅ One-click Start/Stop server buttons
- ✅ Real-time animation streaming to 3ds Max
- ✅ Timeline synchronization between Unreal and Max

---

## ⚡ Quick Setup (5 Minutes)

### Step 1: Install Menu in Unreal Engine (One-Time)

1. **Open Unreal Engine** with your project

2. **Open Python Console:**
   - Window → Developer Tools → Output Log
   - Click the **"Python"** tab at the bottom

3. **Copy the installer script:**
   - Open file: `unreal_scripts/install_max_livelink.py`
   - Press `Ctrl+A` to select all
   - Press `Ctrl+C` to copy

4. **Paste and run:**
   - Click in the Python console
   - Press `Ctrl+V` to paste
   - Press `Enter`

5. **Look for success message:**
   ```
   ======================================================================
   ✓ MAX LIVELINK INSTALLED SUCCESSFULLY!
   ======================================================================
   
   Menu items added to: Tools → Max LiveLink
   ```

6. **Find the menu:**
   - Look in **Tools** menu at the top
   - You'll see **"Max LiveLink"** section with:
     - ▶ Start Max LiveLink Server
     - ■ Stop Max LiveLink Server
     - 🔧 Test Connection

**Done!** This menu persists forever—you never need to run the installer again.

---

## 🎮 Daily Usage

### Starting the Server

**Every time you open Unreal Engine:**

1. Click **Tools → Max LiveLink → Start Max LiveLink Server**
2. Look for confirmation in Output Log:
   ```
   Max LiveLink Server started on port 9999
   ```

That's it! Server is now running.

### Using in 3ds Max

1. **In Unreal:** Select actors you want to stream (characters, cameras)
2. **In 3ds Max:** 
   - MotionKit → Unreal Engine → Rebuild from Unreal
   - Click "Refresh Selection"
   - Check objects to stream
   - Click "Start LiveLink"
3. **Watch the magic:** Objects update in real-time!

### Stopping the Server (Optional)

- Click **Tools → Max LiveLink → Stop Max LiveLink Server**
- Or just close Unreal (auto-stops)

---

## 🔍 Testing the Connection

### From Unreal

Click **Tools → Max LiveLink → Test Connection**

Output Log will show:
```
Max LiveLink Status: RUNNING on port 9999 (0 clients)
```

### From Command Line

Run the test script:
```bash
cd unreal_scripts
python test_connection.py
```

You should see:
```
✓ Connected successfully!
✓ Handshake successful
✓ Ping successful
✓ Query successful
```

---

## 📁 Files Overview

```
unreal_scripts/
├── install_max_livelink.py      ← Run ONCE to install menu
├── max_live_link_server.py      ← Server code (auto-loaded by menu)
├── widget_bindings.py           ← Helper functions (optional)
├── test_connection.py           ← Test script
└── README_SETUP.md              ← This file
```

**What you need to do:**
- Just run `install_max_livelink.py` once ✅
- Everything else is automatic!

---

## 🛠️ Troubleshooting

### Menu doesn't appear after installing

**Fix:**
1. Check Output Log for errors
2. Try restarting Unreal Editor
3. Make sure Python scripting is enabled:
   - Edit → Project Settings → Plugins → Python
   - Enable "Python Editor Script Plugin"

### "Server already running" message

**This is normal!** It means the server is working.

To check status: **Tools → Max LiveLink → Test Connection**

### Can't connect from 3ds Max

**Checklist:**
1. ✅ Is Unreal Engine running?
2. ✅ Did you start the server? (Tools → Max LiveLink → Start Server)
3. ✅ Check firewall isn't blocking port 9999
4. ✅ Run `test_connection.py` to verify server

### Port 9999 already in use

**Edit the port number:**

1. Open `max_live_link_server.py`
2. Find line: `DEFAULT_PORT = 9999`
3. Change to another port (e.g., `DEFAULT_PORT = 9998`)
4. Update 3ds Max config to match

### Server stops when Unreal closes

**This is expected!** The server runs inside Unreal's Python environment.

Just restart it next time you open Unreal: **Tools → Max LiveLink → Start Server**

---

## 🚀 Advanced: Auto-Start on Editor Launch

Want the server to start automatically when Unreal opens?

**Option 1: Project Startup Script**

Add to your project's `Content/Python/init_unreal.py`:
```python
import sys
sys.path.insert(0, r'C:\path\to\MotionKit\unreal_scripts')
from max_live_link_server import start_server
start_server()
```

**Option 2: User Startup Script**

Edit: `C:\Users\YourName\AppData\Local\UnrealEngine\Common\PythonScripts\init_user.py`

Add same code as above.

---

## 📖 For Developers

### Message Protocol

The server uses TCP sockets with this protocol:
- **Format:** 4-byte length prefix (big-endian) + JSON payload
- **Port:** 9999 (configurable)
- **Encoding:** UTF-8

### Message Types

| Type | Direction | Purpose |
|------|-----------|---------|
| `handshake` | Max → UE | Initial connection |
| `query_selection` | Max → UE | Get selected actors |
| `get_actor_data` | Max → UE | Request actor transform/skeleton |
| `set_timeline` | Max → UE | Sync timeline frame |
| `ping` | Max → UE | Connection check |

### Extending the Server

To add custom functionality, edit `max_live_link_server.py`:

```python
def _process_message(self, message):
    msg_type = message.get('type')
    
    # Add your custom message handler
    if msg_type == 'my_custom_command':
        return self._handle_my_custom_command(message)
    
    # ... existing handlers ...
```

---

## 📞 Support

**Issues with setup?**
1. Check Output Log for error messages
2. Run `test_connection.py` for diagnostics
3. See troubleshooting section above

**Feature requests?**
- The server is extensible—add custom message handlers
- Share improvements with the team!

---

## ✅ Quick Reference

### One-Time Setup
```
1. Open Unreal → Window → Developer Tools → Output Log → Python
2. Paste install_max_livelink.py
3. Press Enter
4. Done!
```

### Daily Usage
```
1. Open Unreal
2. Tools → Max LiveLink → Start Server
3. Open 3ds Max → MotionKit → Rebuild from Unreal
4. Stream!
```

### Testing
```bash
python test_connection.py
```

---

**That's it! Simple, fast, artist-friendly. 🎨**
