"""
Extract Animation Trajectory Tool for MotionKit
Extract animation data from objects and bake to dummy helpers

This tool:
- Extracts position/rotation animation from any object
- Supports World Space or Relative to Object modes
- Bakes animation to a dummy helper for easy sharing
- Provides trajectory preview visualization
- Easy cleanup (delete dummy when done)

Usage: Select object to extract, choose mode, bake to dummy helper
"""

import os
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Extract Trajectory] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t
from core.config import config

TOOL_NAME = "Extract Animation Trajectory"


def execute(control=None, event=None):
    """Execute the Extract Animation Trajectory tool"""
    if not pymxs or not rt:
        print("[Extract Trajectory] ERROR: Not running in 3ds Max")
        return

    try:
        # Create and show the dialog
        dialog = ExtractTrajectoryDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open Extract Trajectory: {str(e)}")
        rt.messageBox(
            f"Failed to open Extract Trajectory:\n{str(e)}",
            title="MotionKit Error"
        )


class ExtractTrajectoryDialog:
    """Extract Animation Trajectory dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        """Show the Extract Trajectory dialog using MaxScript"""

        # Get current timeline range
        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)

        maxscript = f'''
-- ============================================
-- MotionKit Extract Animation Trajectory Tool
-- ============================================

global ExtractTrajectoryTool

-- Tool struct
struct ExtractTrajectoryToolStruct
(
    sourceObj = undefined,
    referenceObj = undefined,
    trajectoryHelper = undefined,
    previewSpline = undefined,
    
    -- Extract animation and bake to dummy helper
    fn extractTrajectory sourceObj referenceObj useRelative extractPos extractRot startFrame endFrame outputName showPreview =
    (
        if sourceObj == undefined then
        (
            messageBox "Please select a source object!" title:"Extract Trajectory Error"
            return undefined
        )
        
        if useRelative and referenceObj == undefined then
        (
            messageBox "Please select a reference object for relative mode!" title:"Extract Trajectory Error"
            return undefined
        )
        
        -- Create dummy helper
        local helperName = if outputName != "" then outputName else (sourceObj.name + "_Trajectory")
        local helper = Dummy name:helperName boxsize:[5,5,5]
        helper.wirecolor = (color 100 200 255)
        
        -- Store metadata as custom attributes
        local ca = attributes "TrajectoryData"
        (
            parameters main
            (
                sourceName type:#string
                isRelative type:#boolean default:false
                referenceName type:#string
                hasPosition type:#boolean default:true
                hasRotation type:#boolean default:true
                extractStartFrame type:#integer default:0
                extractEndFrame type:#integer default:100
            )
        )
        
        custAttributes.add helper ca
        helper.sourceName = sourceObj.name
        helper.isRelative = useRelative
        helper.referenceName = if referenceObj != undefined then referenceObj.name else ""
        helper.hasPosition = extractPos
        helper.hasRotation = extractRot
        helper.extractStartFrame = startFrame
        helper.extractEndFrame = endFrame
        
        -- Bake animation
        with animate on
        (
            for f = startFrame to endFrame do
            (
                at time f
                (
                    if useRelative then
                    (
                        -- Calculate position/rotation relative to reference object
                        local refTM = referenceObj.transform
                        local srcTM = sourceObj.transform
                        
                        -- Calculate relative transform
                        local relativeTM = srcTM * (inverse refTM)
                        
                        if extractPos then
                            helper.pos = relativeTM.translation
                        if extractRot then
                            helper.rotation = relativeTM.rotation
                    )
                    else
                    (
                        -- World space extraction
                        if extractPos then
                            helper.pos = sourceObj.pos
                        if extractRot then
                            helper.rotation = sourceObj.rotation
                    )
                )
            )
        )
        
        -- Create preview spline if requested
        if showPreview and extractPos then
        (
            this.createPreviewSpline helper startFrame endFrame
        )
        
        select helper
        return helper
    ),
    
    -- Create trajectory preview spline
    fn createPreviewSpline helper startFrame endFrame =
    (
        local positions = #()
        
        -- Sample positions
        for f = startFrame to endFrame do
        (
            at time f
            (
                append positions helper.pos
            )
        )
        
        if positions.count > 1 then
        (
            -- Create spline
            local splineName = helper.name + "_Preview"
            local spline = SplineShape name:splineName
            addNewSpline spline
            
            -- Add points
            for p in positions do
            (
                addKnot spline 1 #smooth #curve p
            )
            
            updateShape spline
            spline.wirecolor = (color 255 200 100)
            spline.render_displayRenderMesh = false
            
            this.previewSpline = spline
        )
    ),
    
    -- Clean up preview
    fn cleanupPreview =
    (
        if this.previewSpline != undefined and isValidNode this.previewSpline then
            delete this.previewSpline
        this.previewSpline = undefined
    )
)

-- Create global instance
ExtractTrajectoryTool = ExtractTrajectoryToolStruct()

-- Dialog rollout
rollout ExtractTrajectoryDialog "Extract Animation Trajectory" width:420 height:440
(
    -- Source Object
    group "Source Object"
    (
        label sourceLbl "Object to Extract:" pos:[20,20] width:120 align:#left
        pickbutton sourcePickBtn "Pick Object" pos:[20,42] width:100 height:24
        button sourceSelBtn "Use Selected" pos:[130,42] width:90 height:24
        edittext sourceEdit "" pos:[230,44] width:160 height:20 readOnly:true
    )
    
    -- Extraction Mode
    group "Extraction Mode"
    (
        radiobuttons modeRadio labels:#("World Space", "Relative to Object") pos:[20,95] default:1
        
        label refLbl "Reference Object:" pos:[40,135] width:120 align:#left enabled:false
        pickbutton refPickBtn "Pick Reference" pos:[40,155] width:120 height:24 enabled:false
        button refSelBtn "Use Selected" pos:[170,155] width:90 height:24 enabled:false
        edittext refEdit "" pos:[270,157] width:120 height:20 readOnly:true enabled:false
    )
    
    -- Components to Extract
    group "Components to Extract"
    (
        checkbox posCheck "Position" pos:[20,217] checked:true
        checkbox rotCheck "Rotation" pos:[120,217] checked:true
    )
    
    -- Frame Range
    group "Frame Range"
    (
        label startLbl "Start:" pos:[20,267] width:40 align:#left
        spinner startSpn "" pos:[65,265] width:80 height:20 type:#integer range:[-100000,100000,{start_frame}]
        
        label endLbl "End:" pos:[160,267] width:30 align:#left
        spinner endSpn "" pos:[195,265] width:80 height:20 type:#integer range:[-100000,100000,{end_frame}]
        
        checkbox useTimelineCB "Use Timeline Range" pos:[290,267] checked:true width:120
    )
    
    -- Output Options
    group "Output"
    (
        label nameLbl "Helper Name:" pos:[20,317] width:80 align:#left
        edittext nameEdit "" pos:[110,315] width:280 height:20
        
        checkbox previewCheck "Show Trajectory Preview" pos:[20,342] checked:true
    )
    
    -- Progress
    progressBar extractProgress "" pos:[20,370] width:380 height:12 value:0 color:(color 100 150 255)
    label statusLabel "" pos:[20,388] width:380 height:20 align:#center
    
    -- Buttons
    button previewBtn "Preview Trajectory" pos:[30,410] width:120 height:26
    button extractBtn "Extract & Bake" pos:[160,410] width:120 height:26
    button closeBtn "Close" pos:[290,410] width:120 height:26
    
    -- Update timeline spinners when checkbox changes
    on useTimelineCB changed state do
    (
        if state then
        (
            startSpn.value = animationRange.start.frame as integer
            endSpn.value = animationRange.end.frame as integer
            startSpn.enabled = false
            endSpn.enabled = false
        )
        else
        (
            startSpn.enabled = true
            endSpn.enabled = true
        )
    )
    
    -- Mode radio changed
    on modeRadio changed state do
    (
        local isRelative = (state == 2)
        refLbl.enabled = isRelative
        refPickBtn.enabled = isRelative
        refSelBtn.enabled = isRelative
        refEdit.enabled = isRelative
    )
    
    -- Pick source object
    on sourcePickBtn picked obj do
    (
        ExtractTrajectoryTool.sourceObj = obj
        sourceEdit.text = obj.name
        
        -- Auto-generate output name
        if nameEdit.text == "" then
            nameEdit.text = obj.name + "_Trajectory"
    )
    
    -- Use selected source object
    on sourceSelBtn pressed do
    (
        if selection.count == 0 then
        (
            messageBox "Please select an object in the viewport first!" title:"Extract Trajectory"
            return false
        )
        
        if selection.count > 1 then
        (
            messageBox "Please select only one object!" title:"Extract Trajectory"
            return false
        )
        
        local obj = selection[1]
        ExtractTrajectoryTool.sourceObj = obj
        sourceEdit.text = obj.name
        
        -- Auto-generate output name
        if nameEdit.text == "" then
            nameEdit.text = obj.name + "_Trajectory"
    )
    
    -- Pick reference object
    on refPickBtn picked obj do
    (
        ExtractTrajectoryTool.referenceObj = obj
        refEdit.text = obj.name
    )
    
    -- Use selected reference object
    on refSelBtn pressed do
    (
        if selection.count == 0 then
        (
            messageBox "Please select an object in the viewport first!" title:"Extract Trajectory"
            return false
        )
        
        if selection.count > 1 then
        (
            messageBox "Please select only one object!" title:"Extract Trajectory"
            return false
        )
        
        local obj = selection[1]
        ExtractTrajectoryTool.referenceObj = obj
        refEdit.text = obj.name
    )
    
    -- Preview trajectory
    on previewBtn pressed do
    (
        -- Clean up old preview
        ExtractTrajectoryTool.cleanupPreview()
        
        if ExtractTrajectoryTool.sourceObj == undefined then
        (
            messageBox "Please pick a source object first!" title:"Extract Trajectory"
            return false
        )
        
        local useRelative = (modeRadio.state == 2)
        if useRelative and ExtractTrajectoryTool.referenceObj == undefined then
        (
            messageBox "Please pick a reference object for relative mode!" title:"Extract Trajectory"
            return false
        )
        
        if not posCheck.checked then
        (
            messageBox "Position must be enabled to preview trajectory!" title:"Extract Trajectory"
            return false
        )
        
        statusLabel.text = "Generating preview..."
        extractProgress.value = 50
        
        -- Create temporary helper for preview
        local tempHelper = Dummy name:"TempPreview" boxsize:[5,5,5]
        
        with animate on
        (
            for f = startSpn.value to endSpn.value do
            (
                at time f
                (
                    if useRelative then
                    (
                        local refTM = ExtractTrajectoryTool.referenceObj.transform
                        local srcTM = ExtractTrajectoryTool.sourceObj.transform
                        local relativeTM = srcTM * (inverse refTM)
                        tempHelper.pos = relativeTM.translation
                    )
                    else
                    (
                        tempHelper.pos = ExtractTrajectoryTool.sourceObj.pos
                    )
                )
            )
        )
        
        -- Create preview spline
        ExtractTrajectoryTool.createPreviewSpline tempHelper startSpn.value endSpn.value
        delete tempHelper
        
        extractProgress.value = 100
        statusLabel.text = "Preview ready - orange spline shows trajectory"
        
        -- Reset progress after delay
        sleep 2
        extractProgress.value = 0
        statusLabel.text = ""
    )
    
    -- Extract and bake
    on extractBtn pressed do
    (
        -- Validation
        if ExtractTrajectoryTool.sourceObj == undefined then
        (
            messageBox "Please pick a source object first!" title:"Extract Trajectory"
            return false
        )
        
        local useRelative = (modeRadio.state == 2)
        if useRelative and ExtractTrajectoryTool.referenceObj == undefined then
        (
            messageBox "Please pick a reference object for relative mode!" title:"Extract Trajectory"
            return false
        )
        
        if not posCheck.checked and not rotCheck.checked then
        (
            messageBox "Please enable at least Position or Rotation!" title:"Extract Trajectory"
            return false
        )
        
        if nameEdit.text == "" then
        (
            messageBox "Please enter a name for the helper object!" title:"Extract Trajectory"
            return false
        )
        
        -- Clean up old preview
        ExtractTrajectoryTool.cleanupPreview()
        
        statusLabel.text = "Extracting trajectory..."
        extractProgress.value = 20
        
        -- Extract
        local helper = ExtractTrajectoryTool.extractTrajectory \\
            ExtractTrajectoryTool.sourceObj \\
            ExtractTrajectoryTool.referenceObj \\
            useRelative \\
            posCheck.checked \\
            rotCheck.checked \\
            startSpn.value \\
            endSpn.value \\
            nameEdit.text \\
            previewCheck.checked
        
        extractProgress.value = 100
        
        if helper != undefined then
        (
            statusLabel.text = "Extraction complete!"
            messageBox ("Trajectory extracted successfully!\\n\\n" + \\
                       "Helper created: " + helper.name + "\\n\\n" + \\
                       "You can now use 'Apply Animation Trajectory' to apply this to another object.") \\
                       title:"Extract Complete"
        )
        else
        (
            statusLabel.text = "Extraction failed"
            extractProgress.value = 0
        )
        
        -- Reset progress after delay
        sleep 2
        extractProgress.value = 0
        statusLabel.text = ""
    )
    
    -- Close button
    on closeBtn pressed do
    (
        -- Clean up preview on close
        ExtractTrajectoryTool.cleanupPreview()
        destroyDialog ExtractTrajectoryDialog
    )
    
    -- Dialog close handler
    on ExtractTrajectoryDialog close do
    (
        ExtractTrajectoryTool.cleanupPreview()
    )
    
    -- Initialize dialog
    on ExtractTrajectoryDialog open do
    (
        -- Disable timeline spinners by default
        startSpn.enabled = false
        endSpn.enabled = false
    )
)

-- Create and show dialog
try (destroyDialog ExtractTrajectoryDialog) catch()
createDialog ExtractTrajectoryDialog
'''

        # Execute the MaxScript to show the dialog
        rt.execute(maxscript)
