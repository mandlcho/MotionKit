# MotionBuilder to Unreal Engine 5 Live Link

Real-time connection system that allows you to send objects from MotionBuilder directly into Unreal Engine 5.

## Features

- **Live Connection**: TCP/IP socket connection between MotionBuilder and UE5
- **Object Transfer**: Send scene objects with full transform data
- **Geometry Support**: Transfers mesh geometry (vertices, normals, indices)
- **Menu Integration**: Access from xMobu > Unreal Engine menu
- **Simple API**: Easy-to-use Python API for custom workflows

## Quick Start

### 1. Start the UE5 Receiver

**Option A: Editor Utility Widget (Recommended - Permanent UI Button)**

Follow the [UE5_SETUP_GUIDE.md](UE5_SETUP_GUIDE.md) to create a permanent button panel in UE5. Once set up:
1. Click the toolbar button or run the widget
2. Click **"Start Receiver"**
3. Status shows: `"Listening on port 9998..."`

**Option B: Python Console (Quick & Temporary)**

In Unreal Engine 5:
1. Open your project
2. Go to **Window > Output Log**
3. Select **"Python"** from the dropdown
4. Run the receiver script:
   ```python
   py "C:/path/to/xMobu/mobu/tools/unreal/ue5_receiver.py"
   ```
5. Wait for the message: `"Ready to receive objects from MotionBuilder!"`

### 2. Connect from MotionBuilder

**Option A: Using the Menu**
1. In MotionBuilder, go to **xMobu > Unreal Engine > UE5 Live Link**
2. Click **"Connect"**
3. Once connected, select objects in your viewport
4. Go to **xMobu > Unreal Engine > Send Selected to UE5**

**Option B: Using Python**
```python
from mobu.tools.unreal.live_link import get_live_link

# Connect
live_link = get_live_link()
live_link.connect()

# Send selected objects
live_link.send_selected_objects()

# Disconnect when done
live_link.disconnect()
```

### 3. View in UE5

Check your Unreal Engine viewport - the objects should appear in the level!

## Configuration

Edit `config/config.json` to customize connection settings:

```json
{
  "unreal": {
    "live_link_host": "127.0.0.1",
    "live_link_port": 9998
  }
}
```

## How It Works

### Architecture

```
MotionBuilder                     Unreal Engine 5
┌─────────────────┐              ┌──────────────────┐
│  Live Link      │◄────TCP─────►│  Receiver Script │
│  (Sender)       │              │  (Listener)      │
└─────────────────┘              └──────────────────┘
         │                                │
         ▼                                ▼
   Extract Object                  Spawn Actor
   - Transform                     - Convert coords
   - Geometry                      - Create mesh
   - Properties                    - Apply transform
```

### Message Format

Messages are sent as JSON with a 4-byte length prefix:

```python
{
  "type": "spawn_object",
  "object_name": "MyCube",
  "object_type": "FBModelCube",
  "transform": {
    "location": [100.0, 50.0, 0.0],
    "rotation": [0.0, 0.0, 0.0],
    "scale": [1.0, 1.0, 1.0]
  },
  "geometry": {
    "vertices": [[x, y, z], ...],
    "indices": [0, 1, 2, ...],
    "normals": [[x, y, z], ...],
    "vertex_count": 8,
    "triangle_count": 12
  }
}
```

### Coordinate System Conversion

MotionBuilder and Unreal use different coordinate systems:

| Axis | MotionBuilder | Unreal Engine |
|------|---------------|---------------|
| Up   | Y-axis        | Z-axis        |
| Hand | Right-handed  | Left-handed   |

The receiver automatically converts coordinates:
```python
# MoBu (X, Y, Z) -> UE5 (X, Z, Y)
ue_location = Vector(mobu_x, mobu_z, mobu_y)
```

## API Reference

### UnrealLiveLink Class

#### `connect(host=None, port=None)`
Establish connection to Unreal Engine.

**Parameters:**
- `host` (str): IP address of UE5 instance (default: from config or 127.0.0.1)
- `port` (int): Port number (default: from config or 9998)

**Returns:**
- `bool`: True if connection successful

**Example:**
```python
live_link = get_live_link()
if live_link.connect():
    print("Connected!")
```

#### `disconnect()`
Close connection to Unreal Engine.

**Example:**
```python
live_link.disconnect()
```

#### `is_connected()`
Check if currently connected.

**Returns:**
- `bool`: True if connected

**Example:**
```python
if live_link.is_connected():
    print("Already connected")
```

#### `send_object(fb_model)`
Send a MotionBuilder object to Unreal Engine.

**Parameters:**
- `fb_model` (FBModel): MotionBuilder model to send

**Returns:**
- `bool`: True if sent successfully

**Example:**
```python
from pyfbsdk import FBModelCube

cube = FBModelCube("MyCube")
cube.Show = True

if live_link.send_object(cube):
    print("Cube sent!")
```

#### `send_selected_objects()`
Send all currently selected objects to Unreal Engine.

**Returns:**
- `bool`: True if at least one object was sent

**Example:**
```python
# User selects objects in viewport
live_link.send_selected_objects()
```

### Helper Functions

#### `get_live_link()`
Get or create the global live link instance.

**Returns:**
- `UnrealLiveLink`: The singleton instance

**Example:**
```python
from mobu.tools.unreal.live_link import get_live_link

live_link = get_live_link()
```

## Examples

See `examples/unreal_live_link_example.py` for complete examples:

### Example 1: Send a Single Cube

```python
from pyfbsdk import FBModelCube, FBVector3d
from mobu.tools.unreal.live_link import get_live_link

# Connect
live_link = get_live_link()
live_link.connect()

# Create cube
cube = FBModelCube("TestCube")
cube.Translation = FBVector3d(100, 50, 0)
cube.Show = True

# Send to UE5
live_link.send_object(cube)

# Disconnect
live_link.disconnect()
```

### Example 2: Send Multiple Objects

```python
from pyfbsdk import FBModelCube
from mobu.tools.unreal.live_link import get_live_link

live_link = get_live_link()
live_link.connect()

# Create multiple cubes
for i in range(5):
    cube = FBModelCube(f"Cube_{i:02d}")
    cube.Translation = FBVector3d(i * 100, 0, 0)
    cube.Show = True
    live_link.send_object(cube)

live_link.disconnect()
```

### Example 3: Remote Connection

```python
from mobu.tools.unreal.live_link import get_live_link

# Connect to UE5 on another machine
live_link = get_live_link()
live_link.connect(host="192.168.1.100", port=9998)

# Send objects...

live_link.disconnect()
```

## Troubleshooting

### "Failed to connect to Unreal Engine"

**Solution:**
1. Make sure the UE5 receiver script is running
2. Check that the port (default 9998) is not blocked by firewall
3. Verify host/port settings in config.json

### "Connection timeout"

**Solution:**
1. Ensure UE5 is running and the receiver is active
2. Check network connectivity if using remote connection
3. Try increasing timeout in `live_link.py:53`

### Objects not appearing in UE5

**Solution:**
1. Check the UE5 Output Log for errors
2. Verify the object has geometry (currently sends cube placeholders)
3. Make sure you're looking at the current level in UE5

### "Port already in use"

**Solution:**
1. Stop any existing receiver instances
2. Change the port in config.json and restart both sides
3. Use `netstat -ano | findstr 9998` (Windows) to find the process

## Advanced Usage

### Custom Object Types

You can extend the system to handle custom object types:

```python
def send_custom_object(live_link, custom_obj):
    """Send a custom object with additional data"""

    # Extract your custom data
    custom_data = {
        "type": "spawn_object",
        "object_name": custom_obj.Name,
        "custom_property": custom_obj.MyProperty,
        "transform": {
            "location": [x, y, z],
            "rotation": [rx, ry, rz],
            "scale": [sx, sy, sz]
        }
    }

    live_link._send_message(custom_data)
```

### Continuous Streaming

For real-time animation streaming:

```python
import time
from pyfbsdk import FBPlayerControl

live_link = get_live_link()
live_link.connect()

player = FBPlayerControl()
player.Play()

# Stream selected objects at 30 FPS
while player.IsPlaying:
    live_link.send_selected_objects()
    time.sleep(1.0 / 30.0)  # 30 FPS

live_link.disconnect()
```

### Error Handling

```python
try:
    live_link = get_live_link()

    if not live_link.connect():
        raise Exception("Failed to connect")

    # Send objects
    for obj in my_objects:
        if not live_link.send_object(obj):
            print(f"Warning: Failed to send {obj.Name}")

except Exception as e:
    print(f"Error: {e}")

finally:
    if live_link.is_connected():
        live_link.disconnect()
```

## Limitations

1. **Geometry Transfer**: Currently spawns cube placeholders. Full mesh generation requires additional UE5 asset creation code.
2. **One-Way Transfer**: Only supports MoBu → UE5. UE5 → MoBu coming soon.
3. **No Animation Data**: Currently sends static transforms only. Animation streaming in development.
4. **No Material Support**: Materials and textures are not transferred.

## Future Enhancements

- [ ] Full procedural mesh generation in UE5
- [ ] Material and texture transfer
- [ ] Animation streaming
- [ ] Bi-directional sync (UE5 → MoBu)
- [ ] Character rig transfer
- [ ] Camera sync
- [ ] Multi-client support

## Technical Details

### Protocol Specification

**Message Structure:**
```
[4 bytes: length][N bytes: JSON data]
```

**Handshake:**
```json
{
  "type": "handshake",
  "source": "MotionBuilder",
  "version": "1.0"
}
```

**Object Spawn:**
```json
{
  "type": "spawn_object",
  "object_name": "string",
  "object_type": "string",
  "transform": {
    "location": [float, float, float],
    "rotation": [float, float, float],
    "scale": [float, float, float]
  },
  "geometry": {
    "vertices": [[float, float, float], ...],
    "indices": [int, ...],
    "normals": [[float, float, float], ...],
    "vertex_count": int,
    "triangle_count": int
  }
}
```

**Disconnect:**
```json
{
  "type": "disconnect"
}
```

### Port Usage

Default port: **9998**

To use a different port, update both:
1. `config/config.json`: `"unreal.live_link_port"`
2. `ue5_receiver.py`: `PORT` constant

## Support

For issues, questions, or feature requests:
- Check the [examples](../../../examples/unreal_live_link_example.py)
- Review the [troubleshooting](#troubleshooting) section
- Check xMobu logs in MotionBuilder's Python console
- Check UE5 Output Log for receiver errors

## License

Part of the xMobu pipeline toolset.
