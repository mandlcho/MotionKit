# Unreal Engine to 3ds Max LiveLink - Implementation Plan

## 🎯 Project Overview

Build a LiveLink feature for streaming character movement, camera data, and full animation from Unreal Engine to 3ds Max for lighting and rendering workflows.

### Goals
1. Select objects (characters, cameras) in Unreal Engine viewport
2. Click "Rebuild from Unreal" button in 3ds Max
3. Window shows selected objects in Unreal
4. Choose which objects to link and click OK
5. Real-time streaming of animation data from Unreal to Max
6. Bidirectional timeline control (Max scrubs timeline → Unreal updates frame)

### Constraints
- **Cannot install custom plugins** in Unreal Engine
- Must work with **vanilla Unreal Engine 5**
- **Can run Python scripts** in Unreal console that persist
- Full animation data (transforms, skeleton, properties)
- Real-time streaming with timeline synchronization
- Both apps on **same machine** (localhost)
- **Artist-friendly setup** - minimal technical friction

---

## 🏗️ Architecture Overview

### Communication Strategy: TCP Socket Communication

We use a **persistent Python socket server** running in Unreal Engine, with 3ds Max as the client.

**Artist-Friendly Setup:** Instead of pasting Python code, artists click a **button in Unreal's toolbar** that starts the server.

```
┌─────────────────────────────────┐              ┌──────────────────┐
│  Unreal Engine                  │              │    3ds Max       │
│                                 │              │                  │
│  [Start Max LiveLink] Button    │              │  LiveLink Client │
│         ↓                       │              │  (Python)        │
│  Python Socket Server           │◄─TCP Socket─►│                  │
│  (Running in background)        │              │  - Connects to   │
│                                 │              │    localhost:9999│
│  - Listen on port 9999          │              │  - Requests data │
│  - Send actor data on request   │              │  - Timeline sync │
│  - Receive timeline commands    │              │                  │
└─────────────────────────────────┘              └──────────────────┘
```

### Setup Components

1. **Editor Utility Widget** (Unreal UI button)
   - Blue button: "Start Max LiveLink Server"
   - Shows server status (Running/Stopped)
   - One-click start/stop

2. **Python Socket Server** (background script)
   - Listens on TCP port 9999
   - Handles requests from 3ds Max
   - Runs until manually stopped or engine closes

3. **3ds Max Client** (Python tool)
   - Connects to Unreal server
   - Creates/updates objects in Max
   - Syncs timeline bidirectionally

---

## 📐 Enhanced Setup (Artist-Friendly)

### **Option A: Editor Utility Widget (Recommended)**

**File:** `unreal_scripts/MaxLiveLink_Widget.uasset` (Blueprint)  
**File:** `unreal_scripts/max_live_link_server.py` (Python backend)

**What Artists See:**
1. Open Unreal project
2. Click **"Tools"** menu → **"Start Max LiveLink"**
3. Button turns green, shows "Server Running on Port 9999"
4. Done! Can now use Max tool

**Implementation:**
- Create Editor Utility Widget with button
- Button executes Python script via `unreal.PythonScriptLibrary.execute_python_command()`
- Widget shows status indicator (green/red)
- Widget persists across editor sessions

### **Option B: Toolbar Button**

**File:** `unreal_scripts/setup_toolbar.py`

**What Artists See:**
1. Run setup script once (drag .py file into Content Browser, double-click)
2. Toolbar button appears: 🔗 "Max Link"
3. Click button to start server
4. Button icon changes when running

**Implementation:**
- Python script registers toolbar button
- Button stored in editor preferences
- Persists across sessions

### **Option C: Auto-Start on Project Open (Ultimate Artist-Friendly)**

**File:** `.uproject` modification or startup script

**What Artists See:**
1. Open Unreal project
2. Server starts automatically
3. Notification: "Max LiveLink Server Ready"
4. Nothing to do!

**Implementation:**
- Add Python script to project startup
- Auto-starts server on editor launch
- Silent unless errors occur

---

## 📋 Revised Implementation - Phase 1

### **Phase 1A: Python Socket Server (1-2 days)**

Create the core Python server that will be triggered by the UI button.

**File:** `unreal_scripts/max_live_link_server.py`

**Tasks:**
1. ✅ Implement `MaxLiveLinkServer` class
2. ✅ Socket server with message protocol
3. ✅ Message handlers (query_selection, get_actor_data, set_timeline)
4. ✅ Data extraction (transforms, skeleton, camera)
5. ✅ Global instance management (start/stop/status)
6. ✅ Error handling and logging

### **Phase 1B: Unreal UI Button (1-2 days)**

Create the artist-friendly UI button.

**Option 1: Editor Utility Widget (Blueprint + Python)**

**File:** `unreal_scripts/WBP_MaxLiveLinkControl.uasset`

Create a Blueprint widget with:
- Button: "Start Server" / "Stop Server"
- Status text: "Stopped" / "Running on Port 9999"
- Color indicator (red/green)
- OnClicked event calls Python functions

**File:** `unreal_scripts/widget_bindings.py`

Python functions exposed to Blueprint:
```python
@unreal.ufunction(static=True, ret=bool)
def start_max_livelink_server():
    """Start the Max LiveLink server - called by Blueprint button"""
    from max_live_link_server import start_server
    return start_server()

@unreal.ufunction(static=True, ret=bool)
def stop_max_livelink_server():
    """Stop the server"""
    from max_live_link_server import stop_server
    stop_server()
    return True

@unreal.ufunction(static=True, ret=bool)
def is_server_running():
    """Check if server is running"""
    from max_live_link_server import _server
    return _server is not None and _server.running
```

**Option 2: Python Toolbar Button (Pure Python)**

**File:** `unreal_scripts/setup_max_livelink.py`

```python
"""
One-time setup script for Max LiveLink toolbar button
Run this once, button persists across sessions
"""
import unreal

def create_toolbar_button():
    """Add Max LiveLink button to Unreal toolbar"""
    
    # Create menu entry
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.LevelEditorToolBar.PlayToolBar")
    
    if not main_menu:
        unreal.log_warning("Could not find toolbar menu")
        return
    
    # Add button section
    section = main_menu.add_section("MaxLiveLink", label="Max LiveLink")
    
    # Create button entry
    entry = unreal.ToolMenuEntry(
        name="StartMaxLiveLink",
        type=unreal.MultiBlockType.TOOL_BAR_BUTTON
    )
    entry.set_label(unreal.Text("Max Link"))
    entry.set_tool_tip(unreal.Text("Start/Stop Max LiveLink Server"))
    entry.set_icon("EditorStyle", "LevelEditor.Tabs.Cinematics")
    
    # Set command to execute Python
    entry.set_string_command(
        unreal.ToolMenuStringCommandType.PYTHON,
        custom_type="",
        string="from max_live_link_server import toggle_server; toggle_server()"
    )
    
    section.add_entry(entry)
    menus.refresh_all_widgets()
    
    unreal.log("Max LiveLink toolbar button created!")

if __name__ == '__main__':
    create_toolbar_button()
```

---

## 🎮 Revised User Workflow (Artist-Friendly)

### **Setup (One-Time)**

**Option A: Using Editor Utility Widget (Recommended)**

1. **Install Max LiveLink Widget:**
   - Copy `WBP_MaxLiveLinkControl.uasset` to project's `Content/EditorUtilities/` folder
   - Copy `max_live_link_server.py` and `widget_bindings.py` to `Content/Python/` folder
   - Restart Unreal Editor

2. **Add Widget to Toolbar (Optional):**
   - Window → Editor Utility Widgets → WBP_MaxLiveLinkControl
   - Dock widget in toolbar or keep as floating window

**Option B: Using Toolbar Button**

1. **Run Setup Script:**
   - Copy Python scripts to `Content/Python/` folder
   - Open Unreal's Python console (Window → Developer Tools → Output Log → Python tab)
   - Run: `from setup_max_livelink import create_toolbar_button; create_toolbar_button()`
   - See new button in toolbar (persists across sessions)

**Option C: Auto-Start (Advanced)**

1. **Add to Project Startup:**
   - Add line to `.uproject` or create startup script
   - Server auto-starts when Unreal opens
   - No artist interaction needed

---

### **Daily Usage**

**Step 1: Start Unreal Server (Easy!)**

- **Widget:** Click blue "Start Server" button → turns green, shows "Running"
- **Toolbar:** Click 🔗 "Max Link" button → shows notification
- **Auto-start:** Nothing! Already running

**Step 2: Use in 3ds Max**

1. In Unreal: Select actors (character, camera)
2. In Max: MotionKit → Unreal Engine → Rebuild from Unreal
3. Click "Refresh Selection" → see Unreal actors
4. Check objects to stream → Click "Start LiveLink"
5. Real-time animation streaming!

**Step 3: Stop (Optional)**

- Click "Stop Server" button in Unreal
- Or just close Unreal (auto-stops)

---

## 📁 Updated File Structure

```
MotionKit/
├── unreal_scripts/                      # NEW FOLDER
│   ├── max_live_link_server.py          # ✅ Core Python server
│   ├── widget_bindings.py               # ✅ Blueprint-Python bridge
│   ├── setup_max_livelink.py            # ✅ One-time toolbar setup
│   ├── WBP_MaxLiveLinkControl.uasset    # ✅ Editor Utility Widget (Blueprint)
│   ├── test_connection.py               # ✅ Connection test script
│   └── README_SETUP.md                  # ✅ Installation guide
│
├── max/
│   ├── core/
│   │   ├── unreal_live_link.py          # Max LiveLink client
│   │   └── unreal_object_factory.py     # Object creation
│   │
│   └── tools/
│       └── unrealengine/
│           ├── rebuild_from_unreal.py   # Main UI tool
│           ├── live_link_monitor.py     # Status monitor
│           ├── timeline_sync.ms         # MaxScript callback
│           └── timeline_callback.py     # Timeline handler
│
└── docs/
    └── UNREAL_MAX_LIVELINK_PLAN.md      # This file
```

---

## 📝 Updated Phase 1 Tasks

### **Phase 1A: Core Python Server (Day 1-2)**

1. ✅ Create `unreal_scripts/max_live_link_server.py`
2. ✅ Implement socket server and message protocol
3. ✅ Implement message handlers
4. ✅ Add global start/stop/status functions
5. ✅ Test via console (manual Python execution)

### **Phase 1B: UI Button (Day 2-3)**

**Choose Implementation:**

**Option 1: Editor Utility Widget** (Most artist-friendly)
- ✅ Create Blueprint widget asset
- ✅ Create `widget_bindings.py` with exposed functions
- ✅ Add Start/Stop buttons and status display
- ✅ Test button functionality
- ✅ Package widget for easy installation

**Option 2: Toolbar Button** (Good middle ground)
- ✅ Create `setup_max_livelink.py`
- ✅ Implement toolbar button registration
- ✅ Add toggle function (start/stop from same button)
- ✅ Test persistence across sessions

**Option 3: Auto-Start** (Ultimate simplicity)
- ✅ Create startup script
- ✅ Add to project initialization
- ✅ Test auto-start on editor launch
- ✅ Add notification system

### **Phase 1C: Documentation (Day 3)**

1. ✅ Create `README_SETUP.md` with screenshots
2. ✅ Document installation steps for each option
3. ✅ Create troubleshooting guide
4. ✅ Record demo video (optional)

---

## ✅ Which UI Option Should We Build?

Let me ask you to choose:

<function_calls>
<invoke name="mcp_question">
<parameter name="questions">[{
  "header": "UI Button Implementation",
  "question": "Which artist-friendly UI approach should we implement for starting the Unreal server?",
  "options": [
    {
      "label": "Editor Utility Widget (Recommended)",
      "description": "Blueprint widget with Start/Stop button, dockable UI, visual status indicator"
    },
    {
      "label": "Toolbar Button",
      "description": "Python-registered toolbar button, one-click toggle, minimal UI"
    },
    {
      "label": "Auto-Start + Widget",
      "description": "Server auto-starts on editor launch, widget for manual control if needed"
    },
    {
      "label": "All Three Options",
      "description": "Build all approaches, let users choose (most flexible but more work)"
    }
  ]
}]