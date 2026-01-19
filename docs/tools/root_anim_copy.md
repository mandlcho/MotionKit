# Root Animation Copy Tool

## Overview
The **Root Animation Copy** tool transfers animation from a Biped root (CS pelvis) to a custom Root bone. This is essential for retargeting character animation from Character Studio (CS) rigs to custom rigging systems.

## Location
**Menu:** MotionKit → Animation → Root Animation Copy

## Features

### Core Functionality
- **Automatic Detection**: Automatically finds CS pelvis and custom root bone in the scene
- **Selective Axis Copying**: Choose which position axes to copy (X, Y, Z)
- **Rotation Control**: Optional Z-axis rotation copying
- **Frame Range**: Specify exact frame range or use current timeline
- **Height Offset**: Calculate and apply relative height offset between CS and root

### Improvements Over Original
✓ **Cleaner UI**: Modern, organized interface with grouped options
✓ **Better Error Handling**: Clear error messages for common issues
✓ **ESC to Cancel**: Cancel long operations with ESC key
✓ **Auto-detection**: Automatically finds Biped and root bone
✓ **Progress Feedback**: Frame count display on completion
✓ **MotionKit Integration**: Seamlessly integrated with MotionKit menu system

## Usage

### Basic Workflow

1. **Open the Tool**
   - In 3ds Max, go to: MotionKit menu → Animation → Root Animation Copy

2. **Configure Options**
   - **Position**: Check which axes to copy (X, Y, Z)
   - **Rotation**: Check "Z Rotation" if you want to copy Z-axis rotation
   - **Frame Range**: Set start/end frames (defaults to current timeline)

3. **Copy Animation**
   - Click "Copy Biped Root Animation to Root"
   - Tool will automatically find CS pelvis and root bone
   - Animation will be copied with progress tracking

### Advanced: Height Offset

Use this when your custom root bone is at a different height than the CS pelvis:

1. **Select CS Pelvis**
   - Select the CS pelvis node in the viewport
   - Click "Select CS Pelvis" button

2. **Select Root Bone**
   - Select your custom root bone
   - Click "Select Root Bone" button

3. **Calculate Offset**
   - Click "Calculate & Apply Height"
   - The height difference will be calculated and stored
   - This offset will be applied during animation copy

## Requirements

### Scene Setup
- **CS Biped**: Scene must contain a Character Studio Biped rig
- **Root Bone**: Must have a node named "root" (case-sensitive)
- **Animation**: CS Biped must have animated pelvis

### Naming Conventions
- Root bone must be named: `root`
- CS pelvis is automatically detected via Biped node index 13

## Technical Details

### What Gets Copied
- **Position**: X, Y, Z coordinates (selectable per axis)
- **Rotation**: Z-axis rotation only (optional)
- **Frame Range**: Any specified range within timeline

### Controller Setup
The tool automatically:
1. Resets root bone to PRS controller
2. Sets Position_XYZ, Euler_XYZ, ScaleXYZ sub-controllers
3. Clears existing keyframes on position and rotation
4. Creates new keyframes for each frame in range

### Axis Zeroing
When an axis is **unchecked**:
- The tool creates keys but zeros out that axis
- Example: Unchecked X = all X position values become 0

## Common Use Cases

### 1. Retarget CS Animation to Custom Rig
**Scenario**: You have animation on a CS Biped and need it on a custom root bone.

**Steps**:
1. Check all position axes (X, Y, Z)
2. Uncheck Z Rotation (usually not needed)
3. Click "Copy Biped Root Animation to Root"

### 2. Copy Only Horizontal Movement
**Scenario**: You want root motion but not vertical (jumping).

**Steps**:
1. Check X and Y axes only
2. Uncheck Z axis
3. Copy animation

### 3. Copy with Height Adjustment
**Scenario**: Root bone is at different height than CS pelvis.

**Steps**:
1. Select CS pelvis → Click "Select CS Pelvis"
2. Select root bone → Click "Select Root Bone"
3. Click "Calculate & Apply Height"
4. Check desired axes
5. Copy animation

## Troubleshooting

### "Root bone not found"
**Problem**: No node named "root" in scene
**Solution**: Rename your root bone to "root" or create one

### "CS Pelvis not found"
**Problem**: No Biped in scene or Biped not properly set up
**Solution**: Ensure scene contains a valid Character Studio Biped

### "End frame must be greater than start frame"
**Problem**: Invalid frame range specified
**Solution**: Set end frame higher than start frame

### Animation looks offset
**Problem**: Height difference between CS pelvis and root
**Solution**: Use the "Relative Height Offset" feature to calculate proper offset

### Only some axes copying
**Problem**: Some position axes are unchecked
**Solution**: Check all desired position axes (X, Y, Z) before copying

## Comparison with Original AniMax Tool

| Feature | Original | MotionKit |
|---------|----------|-----------|
| UI Style | Dense, Chinese text | Clean, organized, English |
| Auto-detection | Manual selection | Automatic CS/root finding |
| Error messages | Basic | Detailed and helpful |
| Frame validation | Limited | Automatic validation |
| Cancel operation | No | ESC key support |
| Height offset | Manual calculation | Automatic calculation |
| Progress feedback | None | Frame count display |
| Integration | Standalone | MotionKit menu system |

## API Reference

### Python Module
```python
# Import the tool
from max.tools.animation.root_anim_copy import execute

# Launch the tool
execute()
```

### MaxScript Access
```maxscript
-- Via MotionKit menu macro
python.execute "import max.tools.animation.root_anim_copy; max.tools.animation.root_anim_copy.execute()"
```

## Version History

**v1.0.0** - Initial Release
- Full feature parity with original AniMax tool
- Improved UI and error handling
- MotionKit integration
- Height offset calculator
- ESC to cancel support

## Related Tools
- **Loop Animation Generator** - Create seamless animation loops
- **Bone Alignment Tools** - Align bone chains
- **FBX Export** - Export animations to FBX

## Support
For issues or feature requests, visit: https://github.com/mandlcho/MotionKit/issues
