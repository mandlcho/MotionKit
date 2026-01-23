"""
Calibrate Foot Sync Tool for MotionKit
Automatically analyzes biped animation to determine optimal foot sync parameters

This tool:
- Analyzes foot/toe positions throughout an animation
- Calculates height ranges (min/neutral/max)
- Determines velocity thresholds
- Suggests optimal parameters for character presets
- Exports calibration results to JSON format

Usage: Run on a walk/run cycle animation to get accurate measurements
"""

import json
import os
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Calibrate Foot Sync] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Calibrate Foot Sync Parameters"


def get_localized_message(key, *args):
    """Get localized message with optional arguments"""
    try:
        return t(f'tools.calibrate_foot_sync.{key}').format(*args) if args else t(f'tools.calibrate_foot_sync.{key}')
    except:
        # Fallback to English if localization fails
        fallbacks = {
            'error_select_biped': 'Please select a Biped object!',
            'error_no_nodes': 'Could not find biped foot/toe nodes!',
            'error_access_nodes': 'Error accessing biped nodes. Make sure a Biped is selected!',
            'error_no_results': 'No calibration results to export!',
            'error_pick_biped': 'Please pick a Biped object first!',
            'error_enter_name': 'Please enter a character name!',
            'success_calibration': 'Calibration complete!\\n\\nReview the results and click \'Export to JSON\' to save.',
            'success_export': 'Calibration data exported to:\\n{0}\\n\\nCopy the contents to config/foot_sync_presets.json'
        }
        return fallbacks.get(key, key).format(*args) if args else fallbacks.get(key, key)


def execute(control=None, event=None):
    """Execute the Calibrate Foot Sync tool"""
    if not pymxs or not rt:
        print("[Calibrate Foot Sync] ERROR: Not running in 3ds Max")
        return

    try:
        # Create and show the dialog using MaxScript
        dialog = CalibrateFootSyncDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open Calibrate Foot Sync: {str(e)}")
        rt.messageBox(
            f"Failed to open Calibrate Foot Sync: {str(e)}",
            title="MotionKit Error"
        )


class CalibrateFootSyncDialog:
    """Calibrate Foot Sync dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        """Show the Calibrate Foot Sync dialog using MaxScript"""

        # Get translations
        title = "Calibrate Foot Sync Parameters"
        description = "Analyze biped animation to determine optimal foot sync parameters"

        maxscript = '''-- ============================================
-- MotionKit Calibrate Foot Sync Tool
-- Automatically measures character parameters
-- ============================================

global CalibrateTool

struct CalibrateToolStruct
(
    -- Results storage
    results = undefined,

    -- Get biped nodes
    fn getBipedNodes bipedObj =
    (
        if bipedObj == undefined then
        (
            messageBox (get_localized_message "error_select_biped") title:"Calibration Error"
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
                messageBox (get_localized_message "error_no_nodes") title:"Calibration Error"
                return undefined
            )

            nodes = #(csLeftFeet, csLeftToe, csRightFeet, csRightToe)
            return nodes
        )
        catch
        (
            messageBox (get_localized_message "error_access_nodes") title:"Calibration Error"
            return undefined
        )
    ),

    -- Collect all foot/toe positions
    fn collectPositions bipedNodes startFrame endFrame =
    (
        local csLeftFeet = bipedNodes[1]
        local csLeftToe = bipedNodes[2]
        local csRightFeet = bipedNodes[3]
        local csRightToe = bipedNodes[4]

        local leftFeetPos = #()
        local leftToePos = #()
        local rightFeetPos = #()
        local rightToePos = #()

        format "[Calibrate] Analyzing % frames...\\n" (endFrame - startFrame + 1)

        for f = startFrame to endFrame do
        (
            at time f
            (
                append leftFeetPos csLeftFeet.transform.pos
                append leftToePos csLeftToe.transform.pos
                append rightFeetPos csRightFeet.transform.pos
                append rightToePos csRightToe.transform.pos
            )
        )

        return #(leftFeetPos, leftToePos, rightFeetPos, rightToePos)
    ),

    -- Analyze height statistics
    fn analyzeHeights posArray =
    (
        local heights = #()
        for pos in posArray do
            append heights pos.z

        sort heights

        local minVal = heights[1]
        local maxVal = heights[heights.count]
        local medianVal = heights[(heights.count / 2) as integer]

        -- Calculate percentiles for better ground/air detection
        local p10 = heights[(heights.count * 0.1) as integer]
        local p90 = heights[(heights.count * 0.9) as integer]

        return #(minVal, medianVal, maxVal, p10, p90)
    ),

    -- Calculate velocity statistics
    fn analyzeVelocities posArray =
    (
        local velocities = #()

        for i = 2 to posArray.count do
        (
            local dist = distance posArray[i] posArray[i-1]
            append velocities dist
        )

        sort velocities

        local minVel = velocities[1]
        local maxVel = velocities[velocities.count]
        local medianVel = velocities[(velocities.count / 2) as integer]
        local avgVel = 0.0

        for v in velocities do avgVel += v
        avgVel = avgVel / velocities.count

        -- Percentiles for threshold detection
        local p25 = velocities[(velocities.count * 0.25) as integer]
        local p75 = velocities[(velocities.count * 0.75) as integer]

        return #(minVel, maxVel, medianVel, avgVel, p25, p75)
    ),

    -- Calculate angular velocity (for foot rotation)
    fn analyzeAngularVelocity posArray1 posArray2 =
    (
        local angles = #()

        for i = 2 to posArray1.count do
        (
            local vec1 = normalize (posArray1[i] - posArray2[i])
            local vec2 = normalize (posArray1[i-1] - posArray2[i-1])
            local angle = acos (dot vec1 vec2)
            if angle != angle then angle = 0.0  -- Handle NaN
            append angles angle
        )

        sort angles

        local medianAngle = angles[(angles.count / 2) as integer]
        local p90 = angles[(angles.count * 0.9) as integer]

        return #(medianAngle, p90)
    ),

    -- Main calibration function
    fn calibrateCharacter bipedObj characterName =
    (
        format "\\n[Calibrate] ==========================================\\n"
        format "[Calibrate] Starting Calibration: %\\n" characterName
        format "[Calibrate] ==========================================\\n\\n"

        -- Get animation range
        local startFrame = animationRange.start as integer
        local endFrame = animationRange.end as integer
        format "[Calibrate] Animation Range: % to %\\n" startFrame endFrame

        -- Get biped nodes
        local nodes = this.getBipedNodes bipedObj
        if nodes == undefined then
            return undefined

        format "[Calibrate] Biped nodes found\\n"

        -- Collect positions
        format "[Calibrate] Collecting position data...\\n"
        local posData = this.collectPositions nodes startFrame endFrame
        local leftFeetPos = posData[1]
        local leftToePos = posData[2]
        local rightFeetPos = posData[3]
        local rightToePos = posData[4]

        -- Analyze heights
        format "[Calibrate] Analyzing height data...\\n"
        local leftFeetHeights = this.analyzeHeights leftFeetPos
        local leftToeHeights = this.analyzeHeights leftToePos
        local rightFeetHeights = this.analyzeHeights rightFeetPos
        local rightToeHeights = this.analyzeHeights rightToePos

        -- Analyze velocities
        format "[Calibrate] Analyzing velocity data...\\n"
        local leftFeetVel = this.analyzeVelocities leftFeetPos
        local leftToeVel = this.analyzeVelocities leftToePos
        local rightFeetVel = this.analyzeVelocities rightFeetPos
        local rightToeVel = this.analyzeVelocities rightToePos

        -- Analyze angular velocities
        format "[Calibrate] Analyzing angular velocities...\\n"
        local leftAngVel = this.analyzeAngularVelocity leftToePos leftFeetPos
        local rightAngVel = this.analyzeAngularVelocity rightToePos rightFeetPos

        -- Calculate recommendations
        format "[Calibrate] Calculating recommendations...\\n"

        -- Average left and right feet measurements
        local feetMin = (leftFeetHeights[1] + rightFeetHeights[1]) / 2.0
        local feetNeutral = (leftFeetHeights[4] + rightFeetHeights[4]) / 2.0  -- p10
        local feetMax = (leftFeetHeights[5] + rightFeetHeights[5]) / 2.0  -- p90

        local toeMin = (leftToeHeights[1] + rightToeHeights[1]) / 2.0
        local toeNeutral = (leftToeHeights[4] + rightToeHeights[4]) / 2.0
        local toeMax = (leftToeHeights[5] + rightToeHeights[5]) / 2.0

        -- Velocity thresholds
        local avgMovement = (leftFeetVel[4] + rightFeetVel[4]) / 2.0
        local minMovement = (leftFeetVel[5] + rightFeetVel[5]) / 2.0  -- p25
        local speedTolerance = (leftFeetVel[6] + rightFeetVel[6]) / 2.0  -- p75

        -- Angular velocity
        local angleSpeed = (leftAngVel[2] + rightAngVel[2]) / 2.0

        -- Motion range (difference between max and neutral)
        local tinyRangeFeet = feetMax - feetNeutral
        local tinyRangeToe = toeMax - toeNeutral

        -- Height tolerance (10% of range)
        local heightTolerance = (feetMax - feetMin) * 0.1

        -- Store results
        results = #(
            #("character_name", characterName),
            #("feet_min", feetMin),
            #("feet_neutral", feetNeutral),
            #("feet_max", feetMax),
            #("toe_min", toeMin),
            #("toe_neutral", toeNeutral),
            #("toe_max", toeMax),
            #("angle_speed", angleSpeed),
            #("min_movement", minMovement),
            #("height_tolerance", heightTolerance),
            #("speed_tolerance", speedTolerance),
            #("tiny_range_feet", tinyRangeFeet),
            #("tiny_range_toe", tinyRangeToe),
            #("avg_movement", avgMovement)
        )

        format "\\n[Calibrate] ==========================================\\n"
        format "[Calibrate] Calibration Complete!\\n"
        format "[Calibrate] ==========================================\\n"

        messageBox (get_localized_message "success_calibration") \\
            title:"Calibration Complete"

        return results
    ),

    -- Format results for display
    fn formatResults =
    (
        if results == undefined then
            return "No calibration results available"

        local output = ""
        output += "CALIBRATION RESULTS\\n"
        output += "==========================================\\n\\n"

        for item in results do
        (
            local key = item[1]
            local value = item[2]

            case key of
            (
                "character_name": output += "Character: " + value + "\\n\\n"
                "feet_min": output += "Feet Heights:\\n  Min: " + (value as string) + "\\n"
                "feet_neutral": output += "  Neutral: " + (value as string) + "\\n"
                "feet_max": output += "  Max: " + (value as string) + "\\n\\n"
                "toe_min": output += "Toe Heights:\\n  Min: " + (value as string) + "\\n"
                "toe_neutral": output += "  Neutral: " + (value as string) + "\\n"
                "toe_max": output += "  Max: " + (value as string) + "\\n\\n"
                "angle_speed": output += "Thresholds:\\n  Angle Speed: " + (value as string) + "\\n"
                "min_movement": output += "  Min Movement: " + (value as string) + "\\n"
                "height_tolerance": output += "  Height Tolerance: " + (value as string) + "\\n"
                "speed_tolerance": output += "  Speed Tolerance: " + (value as string) + "\\n\\n"
                "tiny_range_feet": output += "Motion Range:\\n  Feet: " + (value as string) + "\\n"
                "tiny_range_toe": output += "  Toe: " + (value as string) + "\\n\\n"
                "avg_movement": output += "Statistics:\\n  Avg Movement: " + (value as string) + "\\n"
            )
        )

        output += "\\n==========================================\\n"
        output += "Copy these values to foot_sync_presets.json\\n"

        return output
    ),

    -- Export to JSON file
    fn exportToJson filePath =
    (
        if results == undefined then
        (
            messageBox (get_localized_message "error_no_results") title:"Export Error"
            return false
        )

        local characterName = "Unknown"
        for item in results do
            if item[1] == "character_name" then
                characterName = item[2]

        -- Build JSON string manually (MaxScript doesn't have native JSON support)
        -- Use string concatenation to avoid backslash escaping issues
        local jsonStr = "{"
        jsonStr += "\n  \"" + characterName + "\": {"
        jsonStr += "\n    \"description\": \"Calibrated from animation\","
        jsonStr += "\n    \"height_cm\": null,"

        -- Toe
        jsonStr += "\n    \"toe\": {"
        for item in results do
        (
            if item[1] == "toe_min" then
                jsonStr += "\n      \"min\": " + (item[2] as string) + ","
            else if item[1] == "toe_neutral" then
                jsonStr += "\n      \"neutral\": " + (item[2] as string) + ","
            else if item[1] == "toe_max" then
                jsonStr += "\n      \"max\": " + (item[2] as string)
        )
        jsonStr += "\n    },"

        -- Feet
        jsonStr += "\n    \"feet\": {"
        for item in results do
        (
            if item[1] == "feet_min" then
                jsonStr += "\n      \"min\": " + (item[2] as string) + ","
            else if item[1] == "feet_neutral" then
                jsonStr += "\n      \"neutral\": " + (item[2] as string) + ","
            else if item[1] == "feet_max" then
                jsonStr += "\n      \"max\": " + (item[2] as string)
        )
        jsonStr += "\n    },"

        -- Thresholds
        jsonStr += "\n    \"thresholds\": {"
        for item in results do
        (
            if item[1] == "angle_speed" then
                jsonStr += "\n      \"angle_speed\": " + (item[2] as string) + ","
            else if item[1] == "min_movement" then
                jsonStr += "\n      \"min_movement\": " + (item[2] as string) + ","
            else if item[1] == "height_tolerance" then
                jsonStr += "\n      \"height_tolerance\": " + (item[2] as string) + ","
            else if item[1] == "speed_tolerance" then
                jsonStr += "\n      \"speed_tolerance\": " + (item[2] as string)
        )
        jsonStr += "\n    },"

        -- Motion range
        jsonStr += "\n    \"motion_range\": {"
        for item in results do
        (
            if item[1] == "tiny_range_feet" then
                jsonStr += "\n      \"feet\": " + (item[2] as string) + ","
            else if item[1] == "tiny_range_toe" then
                jsonStr += "\n      \"toe\": " + (item[2] as string)
        )
        jsonStr += "\n    }"

        jsonStr += "\n  }"
        jsonStr += "\n}"

        -- Write to file
        local outFile = createFile filePath
        format "%" jsonStr to:outFile
        close outFile

        format "[Calibrate] Exported to: %\\n" filePath
        return true
    )
)

-- Create dialog
rollout CalibrateDialog "{title}" width:520 height:540
(
    -- Description
    label descLabel "{description}" pos:[10,10] width:500 align:#center

    -- Instructions
    groupBox instructionsGroup "Instructions" pos:[10,35] width:500 height:85
    label instr1 "1. Select a Biped with a walk or run cycle animation" pos:[20,55] width:480
    label instr2 "2. Enter a name for this character preset" pos:[20,75] width:480
    label instr3 "3. Click Calibrate to analyze the animation" pos:[20,95] width:480
    label instr4 "4. Review results and export to JSON" pos:[20,115] width:480

    -- Biped Selection
    groupBox bipedGroup "Biped Selection" pos:[10,130] width:500 height:55
    pickbutton bipedPicker "Pick Biped Object" pos:[20,150] width:480 height:25 filter:bipedFilter

    -- Character Name
    groupBox nameGroup "Character Name" pos:[10,195] width:500 height:55
    edittext characterNameEdit "" pos:[20,215] width:480 text:"MyCharacter"

    -- Results Display
    groupBox resultsGroup "Calibration Results" pos:[10,260] width:500 height:210
    edittext resultsDisplay "" pos:[20,280] width:480 height:180 readonly:true

    -- Buttons
    button calibrateBtn "Calibrate Animation" pos:[10,480] width:160 height:35
    button exportBtn "Export to JSON..." pos:[180,480] width:160 height:35 enabled:false
    button closeBtn "Close" pos:[350,480] width:160 height:35

    -- Status
    label statusLabel "Ready to calibrate" pos:[10,520] width:500 align:#center

    -- Initialize
    on CalibrateDialog open do
    (
        CalibrateTool = CalibrateToolStruct()
        statusLabel.text = "Select a Biped and enter character name"
    )

    -- Biped picked
    on bipedPicker picked obj do
    (
        bipedPicker.text = obj.name
        statusLabel.text = "Biped selected: " + obj.name

        -- Auto-suggest character name from biped
        local bipedName = obj.name
        if findString bipedName "Bip" != undefined then
        (
            local parts = filterString bipedName " "
            if parts.count > 1 then
                characterNameEdit.text = parts[1]
        )
    )

    -- Calibrate button
    on calibrateBtn pressed do
    (
        if bipedPicker.object == undefined then
        (
            messageBox (get_localized_message "error_pick_biped") title:"Calibration Error"
            return false
        )

        if characterNameEdit.text == "" then
        (
            messageBox (get_localized_message "error_enter_name") title:"Calibration Error"
            return false
        )

        statusLabel.text = "Calibrating... please wait"
        calibrateBtn.enabled = false

        -- Run calibration
        local result = CalibrateTool.calibrateCharacter bipedPicker.object characterNameEdit.text

        if result != undefined then
        (
            resultsDisplay.text = CalibrateTool.formatResults()
            exportBtn.enabled = true
            statusLabel.text = "Calibration complete! Review results and export."
        )
        else
        (
            statusLabel.text = "Calibration failed - see listener for errors"
        )

        calibrateBtn.enabled = true
    )

    -- Export button
    on exportBtn pressed do
    (
        local exportPath = getSaveFileName \\
            caption:"Export Calibration Results" \\
            filename:(characterNameEdit.text + "_calibration.json") \\
            types:"JSON Files (*.json)|*.json|All Files (*.*)|*.*|"

        if exportPath != undefined then
        (
            if CalibrateTool.exportToJson exportPath then
            (
                messageBox (get_localized_message "success_export" exportPath) \\
                    title:"Export Complete"
                statusLabel.text = "Exported: " + (filenameFromPath exportPath)
            )
            else
            (
                statusLabel.text = "Export failed"
            )
        )
    )

    -- Close button
    on closeBtn pressed do
    (
        destroyDialog CalibrateDialog
    )
)

-- Show dialog
createDialog CalibrateDialog
'''.format(title=title, description=description)

        # Execute the MaxScript
        rt.execute(maxscript)

if __name__ == "__main__":
    execute()
