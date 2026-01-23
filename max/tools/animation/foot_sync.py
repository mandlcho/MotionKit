"""
Generate Foot Sync Tool for MotionKit
Analyzes biped foot animation and generates sync group data for export

This tool handles:
- Automatic foot contact detection (left/right foot)
- Ground contact analysis using height and velocity thresholds
- Sync group value generation (0=ground, 1=lift, 2=air)
- Custom attribute creation on root node (FootSpd_L, FootSpd_R)
- Character-specific parameter support

Character Presets Available:
- Generic: Default preset for standard biped characters
- Munin: Character from AniMax (height ~175cm)
- Cynthia: Character from AniMax (forensic doctor character)

Based on reverse-engineered AniMax foot sync system
"""

import json
import os
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Foot Sync] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Generate Foot Sync"


def validate_preset(name, preset):
    """
    Validate a character preset and return warnings/errors
    
    Returns:
        tuple: (is_valid, warnings_list, errors_list)
    """
    warnings = []
    errors = []
    
    # Check required top-level keys
    required_keys = ['toe', 'feet', 'thresholds', 'motion_range']
    for key in required_keys:
        if key not in preset:
            errors.append(f"Missing required section: '{key}'")
            continue
    
    # If we have errors already, return early
    if errors:
        return (False, warnings, errors)
    
    # Validate toe section
    toe = preset.get('toe', {})
    required_toe_keys = ['min', 'neutral', 'max']
    for key in required_toe_keys:
        if key not in toe:
            errors.append(f"Missing toe.{key}")
        elif not isinstance(toe[key], (int, float)):
            errors.append(f"toe.{key} must be a number, got {type(toe[key]).__name__}")
    
    if 'min' in toe and 'max' in toe and isinstance(toe['min'], (int, float)) and isinstance(toe['max'], (int, float)):
        if toe['min'] > toe['max']:
            warnings.append(f"toe.min ({toe['min']}) > toe.max ({toe['max']}) - unusual configuration")
    
    # Validate feet section
    feet = preset.get('feet', {})
    required_feet_keys = ['min', 'neutral', 'max']
    for key in required_feet_keys:
        if key not in feet:
            errors.append(f"Missing feet.{key}")
        elif not isinstance(feet[key], (int, float)):
            errors.append(f"feet.{key} must be a number, got {type(feet[key]).__name__}")
    
    if 'min' in feet and 'max' in feet and isinstance(feet['min'], (int, float)) and isinstance(feet['max'], (int, float)):
        if feet['min'] > feet['max']:
            warnings.append(f"feet.min ({feet['min']}) > feet.max ({feet['max']}) - unusual configuration")
    
    # Validate thresholds
    thresh = preset.get('thresholds', {})
    required_thresh_keys = ['angle_speed', 'min_movement', 'height_tolerance', 'speed_tolerance']
    for key in required_thresh_keys:
        if key not in thresh:
            errors.append(f"Missing thresholds.{key}")
        elif not isinstance(thresh[key], (int, float)):
            errors.append(f"thresholds.{key} must be a number, got {type(thresh[key]).__name__}")
        elif thresh[key] < 0:
            warnings.append(f"thresholds.{key} is negative ({thresh[key]}) - usually should be positive")
    
    # Validate motion_range
    motion = preset.get('motion_range', {})
    required_motion_keys = ['feet', 'toe']
    for key in required_motion_keys:
        if key not in motion:
            errors.append(f"Missing motion_range.{key}")
        elif not isinstance(motion[key], (int, float)):
            errors.append(f"motion_range.{key} must be a number, got {type(motion[key]).__name__}")
        elif motion[key] < 0:
            warnings.append(f"motion_range.{key} is negative ({motion[key]}) - usually should be positive")
    
    # Logical validations
    if 'feet' in preset and 'toe' in preset:
        if all(k in feet for k in ['min', 'max']) and all(k in toe for k in ['min', 'max']):
            # Check if toe is generally lower than feet (anatomically correct)
            if toe['max'] > feet['max']:
                warnings.append(f"toe.max ({toe['max']}) > feet.max ({feet['max']}) - toe is usually lower than foot")
    
    # Check for reasonable value ranges (based on typical 3ds Max units)
    if 'feet' in preset:
        if 'min' in feet and (feet['min'] < -100 or feet['min'] > 1000):
            warnings.append(f"feet.min ({feet['min']}) is outside typical range [-100, 1000]")
        if 'max' in feet and (feet['max'] < -100 or feet['max'] > 1000):
            warnings.append(f"feet.max ({feet['max']}) is outside typical range [-100, 1000]")
    
    is_valid = len(errors) == 0
    return (is_valid, warnings, errors)


def load_character_presets():
    """Load character presets from JSON config file"""
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "foot_sync_presets.json"
    
    if not config_path.exists():
        logger.warning(f"Character presets file not found: {config_path}")
        logger.info("Using default Generic preset only. Copy foot_sync_presets.example.json to foot_sync_presets.json to add custom presets.")
        return {
            "Generic": {
                "description": "Default preset for standard biped characters",
                "toe": {"min": 0.0, "neutral": 5.0, "max": 10.0},
                "feet": {"min": 5.0, "neutral": 10.0, "max": 15.0},
                "thresholds": {"angle_speed": 1.2, "min_movement": 0.22, "height_tolerance": 2.0, "speed_tolerance": 0.4},
                "motion_range": {"feet": 4.5, "toe": 1.4}
            }
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            presets = data.get('presets', {})
            
            # Validate each preset
            valid_presets = {}
            validation_errors_found = False
            
            for name, preset in presets.items():
                is_valid, warnings, errors = validate_preset(name, preset)
                
                if errors:
                    validation_errors_found = True
                    logger.error(f"Preset '{name}' has validation errors:")
                    for error in errors:
                        logger.error(f"  - {error}")
                    logger.warning(f"Skipping invalid preset: '{name}'")
                else:
                    valid_presets[name] = preset
                    if warnings:
                        logger.warning(f"Preset '{name}' has warnings:")
                        for warning in warnings:
                            logger.warning(f"  - {warning}")
            
            if not valid_presets:
                logger.error("No valid presets found! Using default Generic preset.")
                return {
                    "Generic": {
                        "description": "Default preset (no valid presets in config)",
                        "toe": {"min": 0.0, "neutral": 5.0, "max": 10.0},
                        "feet": {"min": 5.0, "neutral": 10.0, "max": 15.0},
                        "thresholds": {"angle_speed": 1.2, "min_movement": 0.22, "height_tolerance": 2.0, "speed_tolerance": 0.4},
                        "motion_range": {"feet": 4.5, "toe": 1.4}
                    }
                }
            
            logger.info(f"Loaded {len(valid_presets)}/{len(presets)} valid character preset(s) from {config_path}")
            if validation_errors_found:
                logger.warning("Some presets were skipped due to validation errors. Check the logs above.")
            
            return valid_presets
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in character presets file: {str(e)}")
        logger.error(f"Line {e.lineno}, Column {e.colno}: {e.msg}")
        return {
            "Generic": {
                "description": "Default preset (JSON parse error)",
                "toe": {"min": 0.0, "neutral": 5.0, "max": 10.0},
                "feet": {"min": 5.0, "neutral": 10.0, "max": 15.0},
                "thresholds": {"angle_speed": 1.2, "min_movement": 0.22, "height_tolerance": 2.0, "speed_tolerance": 0.4},
                "motion_range": {"feet": 4.5, "toe": 1.4}
            }
        }
    except Exception as e:
        logger.error(f"Failed to load character presets: {str(e)}")
        return {
            "Generic": {
                "description": "Default preset (config load failed)",
                "toe": {"min": 0.0, "neutral": 5.0, "max": 10.0},
                "feet": {"min": 5.0, "neutral": 10.0, "max": 15.0},
                "thresholds": {"angle_speed": 1.2, "min_movement": 0.22, "height_tolerance": 2.0, "speed_tolerance": 0.4},
                "motion_range": {"feet": 4.5, "toe": 1.4}
            }
        }


def convert_presets_to_maxscript(presets_dict):
    """Convert Python dict to MaxScript array format"""
    ms_array = "#(\n"
    
    for name, preset in presets_dict.items():
        toe = preset['toe']
        feet = preset['feet']
        thresh = preset['thresholds']
        motion = preset['motion_range']
        
        ms_array += f'''        #("{name}", #(
            #("toe_min", {toe['min']}),
            #("toe_neutral", {toe['neutral']}),
            #("toe_max", {toe['max']}),
            #("feet_min", {feet['min']}),
            #("feet_neutral", {feet['neutral']}),
            #("feet_max", {feet['max']}),
            #("angle_speed", {thresh['angle_speed']}),
            #("min_movement", {thresh['min_movement']}),
            #("height_tolerance", {thresh['height_tolerance']}),
            #("speed_tolerance", {thresh['speed_tolerance']}),
            #("tiny_range_feet", {motion['feet']}),
            #("tiny_range_toe", {motion['toe']})
        ))'''
        
        # Add comma if not last item
        if name != list(presets_dict.keys())[-1]:
            ms_array += ","
        ms_array += "\n"
    
    ms_array += "    )"
    return ms_array


def execute(control=None, event=None):
    """Execute the Generate Foot Sync tool"""
    if not pymxs or not rt:
        print("[Foot Sync] ERROR: Not running in 3ds Max")
        return

    try:
        # Create and show the dialog using MaxScript
        dialog = FootSyncDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open Foot Sync: {str(e)}")
        rt.messageBox(
            f"Failed to open Foot Sync:\n{str(e)}",
            title="MotionKit Error"
        )


class FootSyncDialog:
    """Generate Foot Sync dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        """Show the Generate Foot Sync dialog using MaxScript"""

        # Load character presets from JSON
        presets = load_character_presets()
        presets_ms = convert_presets_to_maxscript(presets)
        preset_names = list(presets.keys())
        preset_names_ms = ', '.join([f'"{name}"' for name in preset_names])

        # Get translations
        title = "Generate Foot Sync"
        description = "Analyze biped foot animation and generate sync group data"

        maxscript = f'''
-- ============================================
-- MotionKit Generate Foot Sync Tool
-- Reverse-engineered from AniMax ExportScriptFBX
-- ============================================

global FootSyncTool

struct FootSyncToolStruct
(
    -- Character parameter presets
    -- Loaded from config/foot_sync_presets.json
    -- To add custom characters: copy foot_sync_presets.example.json to foot_sync_presets.json
    characterPresets = {presets_ms},
    
    -- Current parameters
    toeMin = 0.0,
    toeNeutral = 5.0,
    toeMax = 10.0,
    feetMin = 5.0,
    feetNeutral = 10.0,
    feetMax = 15.0,
    angleSpeed = 1.2,
    minMovement = 0.22,
    heightTolerance = 2.0,
    speedTolerance = 0.4,
    tinyRangeFeet = 4.5,
    tinyRangeToe = 1.4,
    
    -- Data arrays
    leftFeetValArr = #(),
    rightFeetValArr = #(),
    leftCsFeetPosArr = #(),
    rightCsFeetPosArr = #(),
    leftCsToePosArr = #(),
    rightCsToePosArr = #(),
    leftCsToeDirArr = #(),
    rightCsToeDirArr = #(),
    allLeftFeetKeys = #(),
    allRightFeetKeys = #(),
    
    -- Get biped foot/toe nodes
    fn getBipedNodes bipedObj =
    (
        if bipedObj == undefined then
        (
            messageBox "Please select a Biped object!" title:"Foot Sync Error"
            return undefined
        )
        
        local nodes = #()
        try
        (
            local csLeftFeet = biped.getNode bipedObj #lleg link:3
            local csLeftToe = biped.getNode bipedObj #lleg link:4
            local csRightFeet = biped.getNode bipedObj #rleg link:3
            local csRightToe = biped.getNode bipedObj #rleg link:4
            
            if csLeftFeet == undefined or csLeftToe == undefined or \\
               csRightFeet == undefined or csRightToe == undefined then
            (
                messageBox "Could not find biped foot/toe nodes!" title:"Foot Sync Error"
                return undefined
            )
            
            nodes = #(csLeftFeet, csLeftToe, csRightFeet, csRightToe)
            return nodes
        )
        catch
        (
            messageBox "Error accessing biped nodes. Make sure a Biped is selected!" title:"Foot Sync Error"
            return undefined
        )
    ),
    
    -- Collect foot/toe positions throughout animation
    fn collectFootPositions bipedNodes startFrame endFrame =
    (
        local csLeftFeet = bipedNodes[1]
        local csLeftToe = bipedNodes[2]
        local csRightFeet = bipedNodes[3]
        local csRightToe = bipedNodes[4]
        
        leftCsFeetPosArr = #()
        leftCsToePosArr = #()
        rightCsFeetPosArr = #()
        rightCsToePosArr = #()
        
        format "[FootSync] Collecting positions from frame % to %\\n" startFrame endFrame
        
        for f = startFrame to endFrame do
        (
            at time f
            (
                append leftCsFeetPosArr csLeftFeet.transform.pos
                append leftCsToePosArr csLeftToe.transform.pos
                append rightCsFeetPosArr csRightFeet.transform.pos
                append rightCsToePosArr csRightToe.transform.pos
            )
        )
        
        format "[FootSync] Collected % frames of foot data\\n" leftCsFeetPosArr.count
        return true
    ),
    
    -- Analyze foot contact based on height threshold
    fn analyzeFeetContact posArr heightMin heightMax =
    (
        local contactArr = #()
        
        for i = 1 to posArr.count do
        (
            local z = posArr[i].z
            if z <= heightMax and z >= heightMin then
                append contactArr 0  -- On ground
            else
                append contactArr -1  -- Undetermined
        )
        
        return contactArr
    ),
    
    -- Calculate movement speed between frames
    fn calculateMovementSpeed posArr =
    (
        local speedArr = #()
        append speedArr -1  -- First frame has no previous reference
        
        for i = 2 to posArr.count do
        (
            local dist = distance posArr[i] posArr[i-1]
            append speedArr dist
        )
        
        return speedArr
    ),
    
    -- Determine foot state (0=ground, 1=lift, 2=air) based on height and speed
    fn determineFeetStates posArr heightMin heightNeutral heightMax speedThreshold =
    (
        local stateArr = #()
        local speedArr = this.calculateMovementSpeed posArr
        
        for i = 1 to posArr.count do
        (
            local z = posArr[i].z
            local speed = speedArr[i]
            local state = -1
            
            -- Ground contact (low height, low speed)
            if z <= heightNeutral then
            (
                if speed < speedThreshold or speed == -1 then
                    state = 0  -- On ground
                else
                    state = 1  -- Lifting off
            )
            -- In air (high height)
            else if z > heightNeutral then
            (
                state = 2  -- In air/swing phase
            )
            
            append stateArr state
        )
        
        return stateArr
    ),
    
    -- Refine foot states to follow 0,2,1 pattern
    fn refineFeetStates stateArr =
    (
        local refined = copy stateArr
        
        -- Fill in -1 (undetermined) values by looking at neighbors
        for i = 1 to refined.count do
        (
            if refined[i] == -1 then
            (
                -- Use previous value if available
                if i > 1 and refined[i-1] != -1 then
                    refined[i] = refined[i-1]
                -- Otherwise use next value
                else if i < refined.count and refined[i+1] != -1 then
                    refined[i] = refined[i+1]
                else
                    refined[i] = 0  -- Default to ground
            )
        )
        
        return refined
    ),
    
    -- Find key frame indices where state changes
    fn findKeyFrames stateArr startFrame =
    (
        local keyFrames = #(startFrame)
        
        for i = 2 to stateArr.count do
        (
            if stateArr[i] != stateArr[i-1] then
                append keyFrames (startFrame + i - 1)
        )
        
        return keyFrames
    ),
    
    -- Create or get custom attribute holder on root node
    fn getOrCreateCustomAttributes rootNode =
    (
        -- Check if attributes already exist
        local hasFootSpd = false
        try
        (
            local test = rootNode.FootSpd_L
            hasFootSpd = true
        )
        catch
        (
            hasFootSpd = false
        )
        
        if not hasFootSpd then
        (
            format "[FootSync] Creating custom attributes...\\n"
            
            -- Create custom attributes for foot sync data
            local attrDef = attributes "FootSyncData"
            (
                parameters main rollout:params
                (
                    FootSpd_L type:#float animatable:true ui:FootSpd_L_spin
                    FootSpd_R type:#float animatable:true ui:FootSpd_R_spin
                )
                
                rollout params "Foot Sync Group"
                (
                    spinner FootSpd_L_spin "Left Foot State:" range:[0,2,0] type:#integer
                    spinner FootSpd_R_spin "Right Foot State:" range:[0,2,0] type:#integer
                )
            )
            
            custAttributes.add rootNode attrDef
            format "[FootSync] Custom attributes created\\n"
        )
        else
        (
            format "[FootSync] Custom attributes already exist\\n"
        )
        
        return true
    ),
    
    -- Set keyframes for foot sync values
    fn setFootSyncKeys rootNode keyFrames stateArr isLeft:true =
    (
        local propName = if isLeft then "FootSpd_L" else "FootSpd_R"
        local sideName = if isLeft then "Left" else "Right"
        
        format "[FootSync] Setting % foot keys...\\n" sideName
        
        with animate on
        (
            -- Delete existing keys
            try
            (
                deleteKeys rootNode[propName]
            )
            catch()
            
            -- Set keys at state change frames
            for i = 1 to keyFrames.count do
            (
                local frameNum = keyFrames[i]
                local stateIndex = frameNum - (animationRange.start as integer) + 1
                
                if stateIndex > 0 and stateIndex <= stateArr.count then
                (
                    at time frameNum
                    (
                        rootNode[propName] = stateArr[stateIndex] as float
                    )
                )
            )
            
            -- Set tangents to step (hold values)
            try
            (
                for k in rootNode[propName].controller.keys do
                (
                    k.inTangentType = #step
                    k.outTangentType = #step
                )
            )
            catch()
        )
        
        format "[FootSync] Set % keys for % foot\\n" keyFrames.count sideName
    ),
    
    -- Main execution function
    fn generateFootSync bipedObj =
    (
        format "\\n[FootSync] ================================================\\n"
        format "[FootSync] Starting Foot Sync Generation\\n"
        format "[FootSync] ================================================\\n\\n"
        
        -- Get animation range
        local startFrame = animationRange.start as integer
        local endFrame = animationRange.end as integer
        format "[FootSync] Animation Range: % to %\\n" startFrame endFrame
        
        -- Get biped nodes
        local nodes = this.getBipedNodes bipedObj
        if nodes == undefined then
            return false
        
        format "[FootSync] Biped nodes found\\n"
        
        -- Collect foot positions
        if not this.collectFootPositions nodes startFrame endFrame then
            return false
        
        -- Analyze left foot
        format "\\n[FootSync] Analyzing left foot...\\n"
        leftFeetValArr = this.determineFeetStates leftCsFeetPosArr feetMin feetNeutral feetMax speedTolerance
        leftFeetValArr = this.refineFeetStates leftFeetValArr
        allLeftFeetKeys = this.findKeyFrames leftFeetValArr startFrame
        format "[FootSync] Left foot: % key frames\\n" allLeftFeetKeys.count
        
        -- Analyze right foot
        format "\\n[FootSync] Analyzing right foot...\\n"
        rightFeetValArr = this.determineFeetStates rightCsFeetPosArr feetMin feetNeutral feetMax speedTolerance
        rightFeetValArr = this.refineFeetStates rightFeetValArr
        allRightFeetKeys = this.findKeyFrames rightFeetValArr startFrame
        format "[FootSync] Right foot: % key frames\\n" allRightFeetKeys.count
        
        -- Find or create root node
        local rootNode = undefined
        try
        (
            -- Look for common root node names
            rootNode = getNodeByName "root"
            if rootNode == undefined then
                rootNode = getNodeByName "Root"
            if rootNode == undefined then
                rootNode = bipedObj.controller.rootNode
        )
        catch()
        
        if rootNode == undefined then
        (
            messageBox "Could not find root node for custom attributes!" title:"Foot Sync Error"
            return false
        )
        
        format "\\n[FootSync] Using root node: %\\n" rootNode.name
        
        -- Create custom attributes
        if not this.getOrCreateCustomAttributes rootNode then
            return false
        
        -- Set keyframes for both feet
        format "\\n[FootSync] Creating animation keys...\\n"
        this.setFootSyncKeys rootNode allLeftFeetKeys leftFeetValArr isLeft:true
        this.setFootSyncKeys rootNode allRightFeetKeys rightFeetValArr isLeft:false
        
        format "\\n[FootSync] ================================================\\n"
        format "[FootSync] Foot Sync Generation Complete!\\n"
        format "[FootSync] ================================================\\n"
        
        messageBox "Foot sync data generated successfully!\\n\\nLeft Foot: " + (allLeftFeetKeys.count as string) + " keys\\nRight Foot: " + (allRightFeetKeys.count as string) + " keys" \\
            title:"Foot Sync Complete"
        
        return true
    ),
    
    -- Load character preset
    fn loadCharacterPreset presetName =
    (
        for preset in characterPresets do
        (
            if preset[1] == presetName then
            (
                local params = preset[2]
                for param in params do
                (
                    case param[1] of
                    (
                        "toe_min": toeMin = param[2]
                        "toe_neutral": toeNeutral = param[2]
                        "toe_max": toeMax = param[2]
                        "feet_min": feetMin = param[2]
                        "feet_neutral": feetNeutral = param[2]
                        "feet_max": feetMax = param[2]
                        "angle_speed": angleSpeed = param[2]
                        "min_movement": minMovement = param[2]
                        "height_tolerance": heightTolerance = param[2]
                        "speed_tolerance": speedTolerance = param[2]
                        "tiny_range_feet": tinyRangeFeet = param[2]
                        "tiny_range_toe": tinyRangeToe = param[2]
                    )
                )
                format "[FootSync] Loaded preset: %\\n" presetName
                return true
            )
        )
        return false
    )
)

-- Create dialog
rollout FootSyncDialog "{title}" width:480 height:560
(
    -- Description
    label descLabel "{description}" pos:[10,10] width:460 align:#center
    
    -- Biped filter function
    fn bipedFilter obj = (classof obj.controller == Vertical_Horizontal_Turn)

    -- Biped Selection
    groupBox bipedGroup "Biped Selection" pos:[10,35] width:460 height:55
    pickbutton bipedPicker "Pick Biped Object" pos:[20,55] width:440 height:25 filter:bipedFilter
    
    -- Character Preset
    groupBox presetGroup "Character Preset" pos:[10,100] width:460 height:55
    dropdownlist presetDropdown "" pos:[20,120] width:440 \\
        items:#{preset_names_ms}
    
    -- Parameters
    groupBox paramsGroup "Detection Parameters" pos:[10,165] width:460 height:280
    
    label feetHeightLabel "Foot Height Range:" pos:[20,185] width:150
    spinner feetMinSpin "Min:" pos:[80,205] width:160 range:[0,1000,5] type:#float fieldwidth:60
    spinner feetNeutralSpin "Neutral:" pos:[80,230] width:160 range:[0,1000,10] type:#float fieldwidth:60
    spinner feetMaxSpin "Max:" pos:[80,255] width:160 range:[0,1000,15] type:#float fieldwidth:60
    
    label toeHeightLabel "Toe Height Range:" pos:[250,185] width:150
    spinner toeMinSpin "Min:" pos:[310,205] width:160 range:[0,1000,0] type:#float fieldwidth:60
    spinner toeNeutralSpin "Neutral:" pos:[310,230] width:160 range:[0,1000,5] type:#float fieldwidth:60
    spinner toeMaxSpin "Max:" pos:[310,255] width:160 range:[0,1000,10] type:#float fieldwidth:60
    
    label velocityLabel "Velocity Thresholds:" pos:[20,285] width:150
    spinner angleSpeedSpin "Angle Speed:" pos:[100,305] width:140 range:[0,10,1.2] type:#float fieldwidth:60
    spinner minMovementSpin "Min Movement:" pos:[100,330] width:140 range:[0,10,0.22] type:#float fieldwidth:60
    
    label toleranceLabel "Tolerances:" pos:[250,285] width:150
    spinner heightToleranceSpin "Height:" pos:[310,305] width:160 range:[0,10,2.0] type:#float fieldwidth:60
    spinner speedToleranceSpin "Speed:" pos:[310,330] width:160 range:[0,10,0.4] type:#float fieldwidth:60
    
    label infoLabel "Sync Groups: 0=Ground Contact | 1=Lifting | 2=In Air" \\
        pos:[20,365] width:440 align:#center
    
    -- Progress
    groupBox progressGroup "Status" pos:[10,455] width:460 height:55
    label statusLabel "" pos:[20,475] width:440 align:#center
    
    -- Buttons
    button generateBtn "Generate Foot Sync" pos:[10,520] width:220 height:30
    button closeBtn "Close" pos:[250,520] width:220 height:30
    
    -- Initialize
    on FootSyncDialog open do
    (
        FootSyncTool = FootSyncToolStruct()
        statusLabel.text = "Ready. Select a Biped and click Generate."
        
        -- Load Generic preset by default
        FootSyncTool.loadCharacterPreset "Generic"
        this.updateUIFromTool()
    )
    
    -- Update UI from tool values
    fn updateUIFromTool =
    (
        feetMinSpin.value = FootSyncTool.feetMin
        feetNeutralSpin.value = FootSyncTool.feetNeutral
        feetMaxSpin.value = FootSyncTool.feetMax
        toeMinSpin.value = FootSyncTool.toeMin
        toeNeutralSpin.value = FootSyncTool.toeNeutral
        toeMaxSpin.value = FootSyncTool.toeMax
        angleSpeedSpin.value = FootSyncTool.angleSpeed
        minMovementSpin.value = FootSyncTool.minMovement
        heightToleranceSpin.value = FootSyncTool.heightTolerance
        speedToleranceSpin.value = FootSyncTool.speedTolerance
    )
    
    -- Update tool from UI values
    fn updateToolFromUI =
    (
        FootSyncTool.feetMin = feetMinSpin.value
        FootSyncTool.feetNeutral = feetNeutralSpin.value
        FootSyncTool.feetMax = feetMaxSpin.value
        FootSyncTool.toeMin = toeMinSpin.value
        FootSyncTool.toeNeutral = toeNeutralSpin.value
        FootSyncTool.toeMax = toeMaxSpin.value
        FootSyncTool.angleSpeed = angleSpeedSpin.value
        FootSyncTool.minMovement = minMovementSpin.value
        FootSyncTool.heightTolerance = heightToleranceSpin.value
        FootSyncTool.speedTolerance = speedToleranceSpin.value
    )
    
    -- Preset changed
    on presetDropdown selected sel do
    (
        local presetName = presetDropdown.items[sel]
        FootSyncTool.loadCharacterPreset presetName
        this.updateUIFromTool()
        statusLabel.text = "Loaded preset: " + presetName
    )
    
    -- Biped picked
    on bipedPicker picked obj do
    (
        bipedPicker.text = obj.name
        statusLabel.text = "Biped selected: " + obj.name
    )
    
    -- Generate button
    on generateBtn pressed do
    (
        if bipedPicker.object == undefined then
        (
            messageBox "Please pick a Biped object first!" title:"Foot Sync Error"
            return false
        )
        
        statusLabel.text = "Generating foot sync data..."
        
        -- Update tool parameters from UI
        this.updateToolFromUI()
        
        -- Generate foot sync
        local result = FootSyncTool.generateFootSync bipedPicker.object
        
        if result then
            statusLabel.text = "Foot sync generated successfully!"
        else
            statusLabel.text = "Error generating foot sync data."
    )
    
    -- Close button
    on closeBtn pressed do
    (
        destroyDialog FootSyncDialog
    )
)

-- Show dialog
createDialog FootSyncDialog
'''

        # Execute the MaxScript
        rt.execute(maxscript)


# Make this module discoverable by menu builder
if __name__ == "__main__":
    execute()
