# Max LiveLink - Connection Testing Guide

## Quick Test Instructions

### Step 1: Start UE Server

**In Unreal Engine:**
1. Open your UE project
2. Go to **Tools → Max LiveLink → ▶ Start Max LiveLink Server**
3. Check Output Log for: `"Max LiveLink Server started on port 9999"`

### Step 2: Open Max Client

**In 3ds Max:**
1. Go to **MotionKit → Unreal Engine → Max LiveLink**
2. A dialog window will open: "Max LiveLink - Connection Test"

### Step 3: Test Connection

**In the Max LiveLink dialog:**

1. **Connection Settings:**
   - Host: `localhost` (should be pre-filled)
   - Port: `9999` (should be pre-filled)

2. **Click "Connect to UE"**
   - Watch the Log section at the bottom
   - Should see: "Connected to Unreal Engine v1.0"
   - Status should change to: "Status: Connected ✓"

3. **Test Ping:**
   - Click "Test Ping" button
   - Should see latency: "Latency: X.X ms" (typically < 1ms for localhost)
   - Log shows: "Ping successful: X.X ms"

4. **Test Query Selection:**
   - Select some actors in UE (Static Mesh, Camera, Character, etc.)
   - Click "Query UE Selection" in Max dialog
   - Log should show: "Found X selected actors in UE"
   - Shows list of selected actors with their types

5. **Disconnect:**
   - Click "Disconnect" button
   - Status returns to: "Status: Not Connected"

## What the UI Shows

### Connection Status Section
- **Status:** Connected/Not Connected
- **Server Info:** UE version and capabilities
- **Latency:** Ping time in milliseconds

### Log Section
- Real-time log of all operations
- Timestamps for each action
- Error messages if connection fails

## Testing Different Scenarios

### Test 1: UE Not Running
1. Make sure UE server is **NOT** running
2. Click "Connect to UE" in Max
3. **Expected:** "Connection refused - UE server not running on localhost:9999"

### Test 2: Wrong Port
1. Start UE server (port 9999)
2. In Max, change port to `9998`
3. Click "Connect to UE"
4. **Expected:** "Connection refused" or "Connection timeout"

### Test 3: Connection Lost
1. Connect successfully
2. Stop UE server (Tools → Max LiveLink → ■ Stop)
3. Click "Test Ping" in Max
4. **Expected:** "Ping failed - connection lost"
5. UI should auto-disable (Status: Not Connected)

### Test 4: Query Empty Selection
1. Connect successfully
2. Deselect everything in UE
3. Click "Query UE Selection"
4. **Expected:** "Found 0 selected actors in UE"

### Test 5: Query Multiple Actors
1. Connect successfully
2. Select 10+ actors in UE (Static Meshes, Cameras, etc.)
3. Click "Query UE Selection"
4. **Expected:** Shows first 5 actors + "... and X more"

## Troubleshooting

### "Connection timeout"
- UE server not running
- Firewall blocking port 9999
- Wrong host/port settings

### "Connection refused"
- UE server not started
- UE server crashed
- Port already in use by another app

### "Ping failed"
- Connection was established but lost
- UE server stopped
- Network issue

### "Invalid JSON received"
- Protocol mismatch (shouldn't happen)
- Corrupted data (network issue)

## Protocol Details

### Handshake Flow:
1. Max → UE: `{type: 'handshake', source: '3ds Max', version: '1.0'}`
2. UE → Max: `{type: 'handshake_ack', source: 'Unreal Engine', version: '1.0', capabilities: [...]}`

### Ping Flow:
1. Max → UE: `{type: 'ping', timestamp: 1234567890.123}`
2. UE → Max: `{type: 'pong', timestamp: 1234567890.456}`

### Query Selection Flow:
1. Max → UE: `{type: 'query_selection'}`
2. UE → Max: `{type: 'selection_data', actors: [{name, type, path, label}, ...]}`

### Message Format:
- 4-byte length prefix (big-endian unsigned int)
- JSON payload (UTF-8 encoded)

## Next Steps (After Connection Works)

Once connection testing is successful, we'll implement:

1. **Send Transform Data:**
   - Send Max object transforms to UE
   - Create/update UE actors from Max selection

2. **Real-time Streaming:**
   - Stream animation from Max timeline to UE
   - Sync playback between Max and UE

3. **Bidirectional Control:**
   - Control Max timeline from UE
   - Select objects in Max from UE selection

4. **Batch Operations:**
   - Send multiple objects at once
   - Export animation sequences

## Current Implementation Status

✅ **Implemented:**
- Socket connection
- Handshake protocol
- Ping/pong test
- Query UE selection
- Connection status UI
- Error handling
- Auto-reconnect detection

❌ **Not Yet Implemented:**
- Send Max object data to UE
- Stream animation data
- Timeline synchronization
- Batch operations
- Persistent connection (auto-reconnect)

## Files

- **Max Client:** `max/tools/unrealengine/send_to_unreal.py`
- **UE Server:** `unreal_scripts/max_live_link_server.py`
- **UE Menu Installer:** `unreal_scripts/install_max_livelink.py`
