# MotionBuilder Live Link Monitor UI Guide

## Overview

The Live Link Monitor is a Qt-based window that provides real-time monitoring and control of the connection between MotionBuilder and Unreal Engine 5.

## Accessing the Monitor

### From the Menu
**xMobu > Unreal Engine > UE5 Live Link**

This will open the Live Link Monitor window.

---

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│          MotionBuilder → Unreal Engine 5                │
├─────────────────────────────────────────────────────────┤
│  Connection Status                                      │
│  ● Connected to Unreal Engine                           │
│  Host: 127.0.0.1                                        │
│  Port: 9998                                             │
├─────────────────────────────────────────────────────────┤
│  Statistics                                             │
│  Objects Sent: 15                                       │
│  Session Time: 00:05:32                                 │
├─────────────────────────────────────────────────────────┤
│  Connection Controls                                    │
│  [Connect] [Disconnect] [Send Selected Objects]        │
├─────────────────────────────────────────────────────────┤
│  Activity Log                                           │
│  Show: [✓] All [✓] Info [✓] Warning [✓] Error [Clear]  │
│  ┌───────────────────────────────────────────────────┐ │
│  │ [10:23:45] [INFO] Connected to 127.0.0.1:9998    │ │
│  │ [10:24:12] [INFO] Sending 3 object(s)...         │ │
│  │ [10:24:12] [INFO]   → Sent: Cube_01              │ │
│  │ [10:24:12] [INFO]   → Sent: Cube_02              │ │
│  │ [10:24:12] [INFO]   → Sent: Cube_03              │ │
│  │ [10:24:13] [INFO] Successfully sent 3/3 objects  │ │
│  └───────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                                      [Help]    [Close]  │
└─────────────────────────────────────────────────────────┘
```

---

## Features

### 1. Connection Status Indicator

**Visual Status:**
- **Red ●** = Disconnected
- **Green ●** = Connected to Unreal Engine

**Details Shown:**
- Current connection state
- Target host (IP address)
- Target port number

### 2. Statistics Panel

Tracks your current session:
- **Objects Sent**: Total count of objects transferred to UE5
- **Session Time**: Duration since window opened (future feature)

### 3. Connection Controls

**Connect Button** (Green)
- Establishes connection to Unreal Engine
- Disabled when already connected
- Shows error dialog if connection fails

**Disconnect Button** (Red)
- Closes the connection to Unreal Engine
- Disabled when not connected

**Send Selected Objects Button** (Blue)
- Sends all currently selected objects in MoBu viewport to UE5
- Only enabled when connected
- Shows warning if nothing is selected

### 4. Activity Log

**Real-time verbose logging:**
- Timestamped entries `[HH:MM:SS]`
- Color-coded by severity:
  - **Green** = Info messages
  - **Yellow** = Warnings
  - **Red** = Errors
- Auto-scrolls to latest message
- Dark theme for readability

**Log Filters:**
- **All**: Show all messages (overrides individual filters)
- **Info**: General information messages
- **Warning**: Non-critical issues
- **Error**: Critical errors

**Clear Log Button:**
- Clears all log entries
- Resets the display

### 5. Bottom Actions

**Help Button:**
- Opens quick reference guide
- Shows usage instructions
- Lists troubleshooting steps

**Close Button:**
- Closes the monitor window
- Connection remains active if connected

---

## Usage Workflow

### Step 1: Start UE5 Receiver

Before using the monitor, ensure Unreal Engine 5 receiver is running:

1. Open Unreal Engine 5
2. Start the receiver (see [UE5_SETUP_GUIDE.md](UE5_SETUP_GUIDE.md))
3. Verify receiver shows "Listening on port 9998..."

### Step 2: Open Monitor in MotionBuilder

1. In MotionBuilder: **xMobu > Unreal Engine > UE5 Live Link**
2. The monitor window opens
3. Status shows **"Disconnected"** (red indicator)

### Step 3: Connect

1. Click **"Connect"** button
2. Watch activity log:
   ```
   [INFO] Connecting to Unreal Engine...
   [INFO] Connected to 127.0.0.1:9998
   ```
3. Status indicator turns **green**
4. "Send Selected Objects" button becomes enabled

### Step 4: Send Objects

1. In MotionBuilder viewport, **select one or more objects**
2. Click **"Send Selected Objects"**
3. Monitor shows progress in activity log:
   ```
   [INFO] Sending 3 object(s) to Unreal Engine...
   [INFO]   → Sent: MyCube
   [INFO]   → Sent: MySphere
   [INFO]   → Sent: MyCylinder
   [INFO] Successfully sent 3/3 objects
   ```
4. Objects counter increments
5. Check Unreal Engine viewport - objects appear!

### Step 5: Monitor Activity

- **Keep window open** to monitor all transfers
- **Filter logs** to focus on specific message types
- **Check statistics** to track session progress

### Step 6: Disconnect (Optional)

1. Click **"Disconnect"** when finished
2. Log shows:
   ```
   [INFO] Disconnecting from Unreal Engine...
   [INFO] Disconnected
   ```
3. Status returns to **red**

---

## Log Message Examples

### Successful Connection
```
[10:30:00] [INFO] Connecting to Unreal Engine...
[10:30:01] [INFO] Connected to 127.0.0.1:9998
```

### Sending Objects
```
[10:31:15] [INFO] Sending 1 object(s) to Unreal Engine...
[10:31:15] [INFO]   → Sent: TestCube
[10:31:15] [INFO] Successfully sent 1/1 object(s)
```

### Warning - No Selection
```
[10:32:00] [WARNING] No objects selected
```

### Error - Connection Failed
```
[10:33:00] [INFO] Connecting to Unreal Engine...
[10:33:05] [ERROR] Failed to connect to Unreal Engine
[10:33:05] [WARNING] Make sure UE5 receiver is running
```

### Failed Object Transfer
```
[10:34:00] [INFO] Sending 2 object(s) to Unreal Engine...
[10:34:00] [INFO]   → Sent: Cube_01
[10:34:01] [ERROR]   ✗ Failed: InvalidObject
[10:34:01] [INFO] Successfully sent 1/2 object(s)
```

---

## Tips & Best Practices

### Keep Monitor Open
- Leave the monitor window open during your workflow
- Provides instant feedback on all operations
- Easy access to send more objects

### Use Log Filters
- Disable **Info** messages for less clutter
- Enable only **Warnings** and **Errors** for troubleshooting
- Use **Clear Log** to start fresh

### Monitor Statistics
- Track how many objects you've sent
- Useful for batch operations
- Helps verify all objects were transferred

### Check Both Sides
- Monitor shows MotionBuilder side status
- Check UE5 receiver widget for UE5 side status
- Both should show "Connected"

---

## Troubleshooting

### "Failed to connect to Unreal Engine"

**Check:**
1. Is Unreal Engine 5 running?
2. Is the receiver widget started? (should show "Listening")
3. Is port 9998 available? (check firewall)

**Activity Log Shows:**
```
[ERROR] Failed to connect to Unreal Engine
[WARNING] Make sure UE5 receiver is running
```

**Solution:**
- Start UE5 receiver first
- Try disconnecting/reconnecting
- Restart both applications if needed

### "No objects selected"

**Activity Log Shows:**
```
[WARNING] No objects selected
```

**Solution:**
- Select objects in MotionBuilder viewport
- Click in viewport to refresh selection
- Try selecting different objects

### Objects Not Appearing in UE5

**Check Monitor Log:**
- Look for **[ERROR]** messages during send
- Verify **[INFO] Successfully sent X/X objects**

**Check UE5:**
- UE5 receiver should log received objects
- Check UE5 Output Log for errors
- Verify you're looking at correct level

### Monitor Window Won't Open

**Check:**
- MotionBuilder console for Python errors
- Make sure PySide2 is installed
- Try **xMobu > Reload xMobu** from menu

---

## Keyboard Shortcuts

Currently, the monitor doesn't have keyboard shortcuts, but you can:
- **Tab** through buttons
- **Enter** to activate focused button
- **Esc** to close help dialogs

---

## Window Behavior

### Always On Top
- Monitor stays above other windows
- Easy to access while working
- Can be disabled by editing `live_link_ui.py:45`

### Auto-Refresh
- Status updates every 500ms
- Log scrolls automatically to latest message
- Statistics update in real-time

### Close Behavior
- Closing window doesn't disconnect
- Connection remains active
- Reopen monitor to resume monitoring

---

## Advanced Usage

### Leave Connected
Keep connection active even when monitor is closed:
1. Connect via monitor
2. Close monitor window
3. Connection stays active
4. Use **Send Selected to UE5** from menu
5. Reopen monitor to see status

### Batch Sending
Send multiple objects quickly:
1. Connect once
2. Select objects (group 1)
3. Send Selected Objects
4. Select different objects (group 2)
5. Send Selected Objects
6. Repeat as needed

### Monitor Multiple Sessions
- Open multiple MotionBuilder instances
- Each can have its own monitor
- Connect to same or different UE5 instances
- Use different ports if needed (config.json)

---

## Configuration

Edit `config/config.json` to customize:

```json
{
  "unreal": {
    "live_link_host": "127.0.0.1",
    "live_link_port": 9998
  }
}
```

**Options:**
- `live_link_host`: Target IP (use `192.168.x.x` for network)
- `live_link_port`: Port number (default 9998)

**After changing:**
- Restart MotionBuilder
- Or use **xMobu > Reload xMobu**

---

## See Also

- [README_LIVE_LINK.md](README_LIVE_LINK.md) - Complete documentation
- [UE5_SETUP_GUIDE.md](UE5_SETUP_GUIDE.md) - UE5 receiver setup
- [examples/unreal_live_link_example.py](../../../examples/unreal_live_link_example.py) - Code examples

---

## Support

**For help:**
1. Click **Help** button in monitor
2. Check **Activity Log** for error details
3. Review documentation files
4. Check MotionBuilder Python Console for stack traces

**Common Issues:**
- Port blocked by firewall → Allow port 9998
- UE5 not receiving → Restart receiver widget
- Objects wrong position → Coordinate system conversion (normal)
