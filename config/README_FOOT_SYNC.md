# Foot Sync Character Presets Configuration

## Overview

The `foot_sync_presets.json` file contains character-specific parameters for the Generate Foot Sync tool. This file is **NOT tracked in git** to protect proprietary/NDA character data.

## Setup

1. **Copy the example file:**
   ```bash
   cp foot_sync_presets.example.json foot_sync_presets.json
   ```

2. **Edit `foot_sync_presets.json`** to add your custom characters

3. **The file will be automatically loaded** when you open the Generate Foot Sync tool

## File Structure

```json
{
  "version": "1.0.0",
  "description": "Character presets for foot sync generation",
  "presets": {
    "CharacterName": {
      "description": "Character description",
      "height_cm": 170,
      "toe": {
        "min": 0.0,
        "neutral": 5.0,
        "max": 10.0
      },
      "feet": {
        "min": 5.0,
        "neutral": 10.0,
        "max": 15.0
      },
      "thresholds": {
        "angle_speed": 1.2,
        "min_movement": 0.22,
        "height_tolerance": 2.0,
        "speed_tolerance": 0.4
      },
      "motion_range": {
        "feet": 4.5,
        "toe": 1.4
      }
    }
  }
}
```

## Parameter Definitions

### Toe Heights
- **min**: Toe height when heel strikes ground (toe up)
- **neutral**: Toe height when foot is flat on ground
- **max**: Maximum toe height during swing phase (toe lift)

### Feet Heights
- **min**: Foot height at lowest contact point
- **neutral**: Foot height when standing normally
- **max**: Maximum foot height during swing phase

### Thresholds
- **angle_speed**: Angular velocity threshold (degrees/frame) for rotation detection
- **min_movement**: Minimum displacement per frame to detect movement (units)
- **height_tolerance**: Vertical tolerance for ground contact detection (units)
- **speed_tolerance**: Speed threshold for determining lift-off (units/frame)

### Motion Range
- **feet**: Feet amplitude threshold - above this value = large motion
- **toe**: Toe amplitude threshold - above this value = large motion

## Calibrating Custom Characters

### Method 1: Automatic Calibration Tool (Recommended)
1. Open 3ds Max with your rigged character
2. Run a walk or run animation cycle (30-60 frames recommended)
3. Open **MotionKit → Animation → Calibrate Foot Sync Parameters**
4. Pick your biped object and enter character name
5. Click "Calibrate Animation" - the tool analyzes the entire animation
6. Review the results and click "Export to JSON"
7. Copy the exported JSON data into `foot_sync_presets.json`

### Method 2: Manual Measurement
1. Open your character in 3ds Max
2. Select the foot/toe biped nodes
3. Note the Z-axis position at different poses:
   - Standing flat (neutral)
   - Heel strike (toe up)
   - Toe strike (heel up)
4. Use these values in the preset

### Method 2: Analysis Tool (Coming Soon)
A calibration tool will be added to automatically analyze a character's animation and suggest parameters.

## Security Notes

- **DO NOT commit `foot_sync_presets.json`** to public repositories
- This file may contain proprietary character measurements
- The file is automatically excluded via `.gitignore`
- Share presets carefully - they may be under NDA
- **IMPORTANT**: If `foot_sync_presets.json` contains reverse-engineered or NDA data, you must manually load it each time
- The `.gitignore` only prevents **new** files from being tracked. Already tracked files need to be removed with `git rm --cached`

## Available Tools

### Generate Foot Sync
**Menu:** MotionKit → Animation → Generate Foot Sync
- Analyzes biped animation and creates sync group data
- Uses preset parameters from `foot_sync_presets.json`
- Creates custom attributes on root node with step keyframes
- Supports all configured character presets

### Calibrate Foot Sync Parameters
**Menu:** MotionKit → Animation → Calibrate Foot Sync Parameters
- Automatically analyzes a walk/run cycle animation
- Calculates optimal height and velocity parameters
- Exports results as JSON ready for presets file
- Uses statistical analysis (percentiles) for robust measurements

## Troubleshooting

### "Character presets file not found"
- The tool will use Generic preset only
- Copy `foot_sync_presets.example.json` to `foot_sync_presets.json`

### "Failed to load character presets"
- Check JSON syntax with a validator
- Ensure all required fields are present
- Check file encoding is UTF-8

### Preset not appearing in dropdown
- Restart 3ds Max or reload MotionKit
- Check preset name doesn't contain special characters
- Verify JSON is valid

## Version History

- **1.0.0** - Initial release with JSON-based preset system
