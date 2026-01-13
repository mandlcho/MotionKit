# Unreal Engine 5 Setup Guide
## MotionBuilder Live Link Receiver - Editor Utility Widget

This guide will help you set up a permanent button panel in Unreal Engine 5 for the MotionBuilder Live Link receiver.

---

## Prerequisites

1. **Unreal Engine 5.0 or later**
2. **Python Editor Script Plugin** (usually enabled by default)

---

## Step 1: Enable Python Plugin

1. In Unreal Engine, go to **Edit > Plugins**
2. Search for **"Python Editor Script Plugin"**
3. Make sure it's **enabled** (checkmark)
4. Restart UE5 if prompted

---

## Step 2: Add Python Script to Project

### Option A: Copy to Project Folder (Recommended)

1. Copy `ue5_receiver_widget.py` to your UE5 project:
   ```
   YourProject/Content/Python/ue5_receiver_widget.py
   ```

2. If the `Python` folder doesn't exist, create it:
   ```
   YourProject/Content/Python/
   ```

### Option B: Use from xMobu Location

1. Note the path to your xMobu installation:
   ```
   C:/Users/elementa/projects/xMobu/mobu/tools/unreal/ue5_receiver_widget.py
   ```

2. You'll reference this path in the widget (Step 4)

---

## Step 3: Create Editor Utility Widget

1. In Unreal Engine Content Browser, **right-click** in any folder
2. Select **Editor Utilities > Editor Utility Widget**
3. Name it: **`EUW_MobuReceiver`**
4. **Double-click** to open the widget editor

---

## Step 4: Design the Widget UI

### A. Add Canvas Panel (if not present)

1. In the **Hierarchy** panel, ensure you have a **Canvas Panel** as root
2. If not, drag **Canvas Panel** from the Palette to the hierarchy

### B. Add Title Text

1. Drag a **Text** widget onto the Canvas Panel
2. In **Details** panel:
   - **Text**: `MotionBuilder Live Link`
   - **Font Size**: `18`
   - **Anchors**: Top-Left
   - **Position**: X=`10`, Y=`10`
   - **Size**: X=`300`, Y=`30`

### C. Add Status Text

1. Drag another **Text** widget onto Canvas Panel
2. Name it: **`StatusText`** (in the Details panel, rename)
3. Settings:
   - **Text**: `Status: Stopped`
   - **Font Size**: `12`
   - **Color**: Yellow
   - **Position**: X=`10`, Y=`45`
   - **Size**: X=`300`, Y=`25`
4. **Check "Is Variable"** (top right) - Important!

### D. Add Start Button

1. Drag a **Button** onto Canvas Panel
2. Name it: **`StartButton`**
3. Settings:
   - **Position**: X=`10`, Y=`80`
   - **Size**: X=`140`, Y=`35`
4. Add **Text** as child of Button:
   - **Text**: `Start Receiver`
   - **Font Size**: `14`
   - Set alignment to center
5. **Check "Is Variable"** for the button

### E. Add Stop Button

1. Drag another **Button** onto Canvas Panel
2. Name it: **`StopButton`**
3. Settings:
   - **Position**: X=`160`, Y=`80`
   - **Size**: X=`140`, Y=`35`
4. Add **Text** as child:
   - **Text**: `Stop Receiver`
   - **Font Size**: `14`
5. **Check "Is Variable"** for the button

### F. Add Objects Counter Text

1. Drag a **Text** widget onto Canvas Panel
2. Name it: **`ObjectsText`**
3. Settings:
   - **Text**: `Objects Received: 0`
   - **Font Size**: `11`
   - **Position**: X=`10`, Y=`125`
   - **Size**: X=`300`, Y=`20`
4. **Check "Is Variable"**

---

## Step 5: Add Blueprint Logic

Now switch to the **Graph** view (top right corner).

### A. Event Construct (Initialize)

1. Right-click in graph → Search: **"Event Construct"**
2. This runs when the widget opens

From **Event Construct**:

**Execute Python Script** node:
   - Right-click → Search: **"Execute Python Script"**
   - **Python Command**:
     ```python
     import sys
     sys.path.append('C:/Users/elementa/projects/xMobu/mobu/tools/unreal')
     import ue5_receiver_widget
     ```
   - Connect from **Event Construct**

> **Note**: Replace the path with your actual xMobu location. If you copied to `Content/Python/`, use:
> ```python
> import ue5_receiver_widget
> ```

### B. Start Button - On Clicked Event

1. Select **StartButton** in the Designer view
2. In **Details** panel, scroll to **Events**
3. Click **+** next to **"On Clicked"**

This creates an event in the graph. Add these nodes:

**Execute Python Script** node:
   - **Python Command**:
     ```python
     import ue5_receiver_widget
     ue5_receiver_widget.start_receiver()
     ```

**Print String** node (for debugging):
   - **In String**: `"Starting MotionBuilder receiver..."`
   - Connect after Execute Python Script

### C. Stop Button - On Clicked Event

1. Select **StopButton** in Designer
2. Click **+** next to **"On Clicked"** in Details

Add nodes:

**Execute Python Script**:
   - **Python Command**:
     ```python
     import ue5_receiver_widget
     ue5_receiver_widget.stop_receiver()
     ```

**Print String**:
   - **In String**: `"Stopping receiver..."`

### D. Event Tick (Update Status Display)

1. Right-click in graph → **"Event Tick"**

From **Event Tick**, create this chain:

**Execute Python Script**:
   - **Python Command**:
     ```python
     import ue5_receiver_widget
     status = ue5_receiver_widget.get_receiver_status()
     objects = ue5_receiver_widget.get_objects_received()
     ```
   - Connect from Event Tick

**Set Text (StatusText)**:
   - Drag **StatusText** from Variables panel to graph
   - Drag out → **Set Text**
   - **In Text**: Use a **Format Text** node with: `Status: {status}`
   - Connect **status** variable

**Set Text (ObjectsText)**:
   - Similar to above
   - **In Text**: `Objects Received: {objects}`

> **Simplified Approach**: If the above is complex, just update status on button clicks instead of every tick.

---

## Step 6: Test the Widget

1. **Save** and **Compile** the widget
2. Close the widget editor
3. In Content Browser, **right-click** on `EUW_MobuReceiver`
4. Select **"Run Editor Utility Widget"**

You should see a panel with Start/Stop buttons!

---

## Step 7: Make Widget Easily Accessible

### Option A: Add to Toolbar

1. In Content Browser, right-click `EUW_MobuReceiver`
2. Select **"Editor Utilities > Add to Toolbar"**
3. Now there's a button in the main toolbar!

### Option B: Add to Menu

1. Right-click widget
2. **"Editor Utilities > Add to Menu"**
3. Choose category (e.g., "Tools")

### Option C: Docked Tab (Advanced)

Create a dockable tab that stays open:

1. In the widget's Graph view
2. **Event Construct** → **Get Owning Player**
3. → **Add to Viewport**
4. → **Set is Enabled** → `True`

---

## Usage

### Starting the Receiver

1. Click **"Start Receiver"** in the widget
2. Wait for status to show: `"Listening on port 9998..."`
3. In MotionBuilder, connect via the xMobu menu
4. Status updates to: `"Connected | Port 9998 | Objects: 0"`

### Sending from MotionBuilder

1. Create objects in MotionBuilder
2. Select them
3. **xMobu > Unreal Engine > Send Selected to UE5**
4. Watch the objects counter increment!
5. Objects appear in your UE5 level

### Stopping the Receiver

1. Click **"Stop Receiver"**
2. Status returns to: `"Stopped"`

---

## Troubleshooting

### "Module not found: ue5_receiver_widget"

**Solution**: Check your Python path in Event Construct:
```python
import sys
sys.path.append('C:/Path/To/Your/xMobu/mobu/tools/unreal')
```

### Widget won't compile

**Solution**:
- Make sure all text widgets marked as "Is Variable" are checked
- Verify Python Editor Script Plugin is enabled
- Check Output Log for specific errors

### "Port already in use"

**Solution**:
- Stop any running instances (Output Log → Python tab → `stop_receiver()`)
- Close and reopen Unreal Engine
- Change port in `ue5_receiver_widget.py` (line 12)

### Status not updating

**Solution**:
- Event Tick might be too heavy; remove it
- Update status only on button clicks instead
- Use a **Timer** (Set Timer by Event) to update every 1 second

---

## Alternative: Quick Python Console Method

If the widget seems complex, you can still use the improved standalone script:

**In UE5 Output Log (Python console):**
```python
import sys
sys.path.append('C:/Users/elementa/projects/xMobu/mobu/tools/unreal')
import ue5_receiver_widget
ue5_receiver_widget.main()
```

To stop:
```python
ue5_receiver_widget.stop_receiver()
```

---

## Simplified Blueprint Instructions (Visual)

If you're more comfortable with visual instructions:

1. **Designer Tab**:
   ```
   [Canvas Panel]
   ├─ [Text] "MotionBuilder Live Link" (Title)
   ├─ [Text] StatusText (Variable)
   ├─ [Button] StartButton (Variable)
   │  └─ [Text] "Start Receiver"
   ├─ [Button] StopButton (Variable)
   │  └─ [Text] "Stop Receiver"
   └─ [Text] ObjectsText (Variable)
   ```

2. **Graph Tab**:
   ```
   Event Construct
      → Execute Python Script (import script)

   StartButton.OnClicked
      → Execute Python Script (start_receiver())

   StopButton.OnClicked
      → Execute Python Script (stop_receiver())
   ```

---

## Next Steps

- Test the connection with MotionBuilder
- Check the main `README_LIVE_LINK.md` for usage examples
- Run examples from `examples/unreal_live_link_example.py`

---

## Support

If you encounter issues:
1. Check UE5 **Output Log** for Python errors
2. Check MotionBuilder **Python Console** for connection errors
3. Verify firewall isn't blocking port 9998
4. Review `README_LIVE_LINK.md` for troubleshooting

---

**Congratulations!** You now have a permanent MotionBuilder receiver button in Unreal Engine 5!
