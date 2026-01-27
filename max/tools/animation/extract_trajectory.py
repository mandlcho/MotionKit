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
    ),
    
    -- Find all trajectory helpers in scene
    fn findAllTrajectories =
    (
        local trajectories = #()
        for obj in objects do
        (
            if classOf obj == Dummy then
            (
                -- Check if it has TrajectoryData custom attributes
                if custAttributes.count obj > 0 then
                (
                    for i = 1 to custAttributes.count obj do
                    (
                        local ca = custAttributes.get obj i
                        if ca.name == "TrajectoryData" then
                        (
                            append trajectories obj
                            exit
                        )
                    )
                )
            )
        )
        return trajectories
    ),
    
    -- Get trajectory info string
    fn getTrajectoryInfo traj =
    (
        local info = traj.name
        if custAttributes.count traj > 0 then
        (
            for i = 1 to custAttributes.count traj do
            (
                local ca = custAttributes.get traj i
                if ca.name == "TrajectoryData" then
                (
                    local mode = if traj.isRelative then " (Relative)" else " (World)"
                    info = traj.name + mode
                    exit
                )
            )
        )
        return info
    ),
    
    -- Delete trajectory helper
    fn deleteTrajectory traj =
    (
        if traj != undefined and isValidNode traj then
        (
            delete traj
            return true
        )
        return false
    )
)

-- Create global instance
ExtractTrajectoryTool = ExtractTrajectoryToolStruct()

-- Dialog rollout
rollout ExtractTrajectoryDialog "Extract Animation Trajectory" width:700 height:520
(
    -- Left side: Trajectory Manager
    group "Trajectory Manager"
    (
        label trajLbl "Trajectories in Scene:" pos:[15,20] width:200 align:#left
        multiListBox trajList "" pos:[15,40] width:230 height:19
        
        button btnSelect "Select in Scene" pos:[15,355] width:110 height:26
        button btnRefresh "Refresh List" pos:[135,355] width:110 height:26
        
        button btnRebake "Re-Bake" pos:[15,387] width:110 height:26
        button btnDelete "Delete" pos:[135,387] width:110 height:26
    )
    
    -- Right side: Extract New Trajectory
    group "Extract New Trajectory"
    (
        -- Source Object
        label sourceLbl "Source Object:" pos:[270,20] width:100 align:#left
        pickbutton sourcePickBtn "Pick Object" pos:[270,42] width:100 height:26
        button sourceSelBtn "Use Selected" pos:[380,42] width:100 height:26
        edittext sourceEdit "" pos:[270,72] width:210 height:20 readOnly:true
        
        -- Extraction Mode
        label modeLbl "Mode:" pos:[270,100] width:50 align:#left
        radiobuttons modeRadio labels:#("World Space", "Relative to Object") pos:[320,98] default:1
        
        -- Reference Object (indented, initially disabled)
        label refLbl "Reference Object:" pos:[290,145] width:120 align:#left enabled:false
        pickbutton refPickBtn "Pick Reference" pos:[290,167] width:100 height:26 enabled:false
        button refSelBtn "Use Selected" pos:[400,167] width:100 height:26 enabled:false
        edittext refEdit "" pos:[290,197] width:190 height:20 readOnly:true enabled:false
        
        -- Components
        label compLbl "Extract Components:" pos:[270,225] width:120 align:#left
        checkbox posCheck "Position" pos:[270,247] checked:true
        checkbox rotCheck "Rotation" pos:[360,247] checked:true
        
        -- Frame Range
        label rangeLbl "Frame Range:" pos:[270,272] width:80 align:#left
        label startLbl "Start:" pos:[270,294] width:40 align:#left
        spinner startSpn "" pos:[315,292] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}]
        
        label endLbl "End:" pos:[400,294] width:30 align:#left
        spinner endSpn "" pos:[435,292] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}]
        
        checkbox useTimelineCB "Use Timeline Range" pos:[520,294] checked:true width:150
        
        -- Output
        label nameLbl "Helper Name:" pos:[270,322] width:80 align:#left
        edittext nameEdit "" pos:[360,320] width:310 height:20
        
        checkbox previewCheck "Show Trajectory Preview" pos:[270,347] checked:true
        
        -- Action Buttons
        button previewBtn "Preview Trajectory" pos:[270,375] width:130 height:28
        button extractBtn "Extract & Bake" pos:[410,375] width:130 height:28
    )
    
    -- Progress Bar
    progressBar extractProgress "" pos:[20,430] width:660 height:14 value:0 color:(color 100 150 255)
    label statusLabel "" pos:[20,450] width:660 height:20 align:#center
    
    -- Close Button
    button closeBtn "Close" pos:[295,480] width:110 height:32
    
    -- Initialize dialog
    on ExtractTrajectoryDialog open do
    (
        -- Disable timeline spinners by default
        startSpn.enabled = false
        endSpn.enabled = false
        
        -- Refresh trajectory list
        local trajectories = ExtractTrajectoryTool.findAllTrajectories()
        local trajNames = #()
        for traj in trajectories do
        (
            append trajNames (ExtractTrajectoryTool.getTrajectoryInfo traj)
        )
        trajList.items = trajNames
    )
    
    -- Refresh trajectory list
    on btnRefresh pressed do
    (
        local trajectories = ExtractTrajectoryTool.findAllTrajectories()
        local trajNames = #()
        for traj in trajectories do
        (
            append trajNames (ExtractTrajectoryTool.getTrajectoryInfo traj)
        )
        trajList.items = trajNames
        statusLabel.text = "Found " + (trajectories.count as string) + " trajectories"
    )
    
    -- Select trajectory in scene
    on btnSelect pressed do
    (
        if trajList.selection == 0 then
        (
            messageBox "Please select a trajectory from the list!" title:"Trajectory Manager"
            return false
        )
        
        local trajectories = ExtractTrajectoryTool.findAllTrajectories()
        if trajList.selection > 0 and trajList.selection <= trajectories.count then
        (
            local traj = trajectories[trajList.selection]
            select traj
            statusLabel.text = "Selected: " + traj.name
        )
    )
    
    -- Re-bake selected trajectory
    on btnRebake pressed do
    (
        if trajList.selection == 0 then
        (
            messageBox "Please select a trajectory from the list!" title:"Trajectory Manager"
            return false
        )
        
        local trajectories = ExtractTrajectoryTool.findAllTrajectories()
        if trajList.selection > 0 and trajList.selection <= trajectories.count then
        (
            local traj = trajectories[trajList.selection]
            
            -- Get stored metadata
            local srcName = traj.sourceName
            local refName = traj.referenceName
            local isRel = traj.isRelative
            local hasPos = traj.hasPosition
            local hasRot = traj.hasRotation
            local startF = traj.extractStartFrame
            local endF = traj.extractEndFrame
            
            -- Find source and reference objects
            local srcObj = getNodeByName srcName
            local refObj = if refName != "" then getNodeByName refName else undefined
            
            if srcObj == undefined then
            (
                messageBox ("Source object '" + srcName + "' not found in scene!") title:"Re-Bake Error"
                return false
            )
            
            if isRel and refObj == undefined then
            (
                messageBox ("Reference object '" + refName + "' not found in scene!") title:"Re-Bake Error"
                return false
            )
            
            -- Delete old animation keys
            deleteKeys traj
            
            -- Re-bake animation
            statusLabel.text = "Re-baking trajectory..."
            with animate on
            (
                for f = startF to endF do
                (
                    at time f
                    (
                        if isRel then
                        (
                            local refTM = refObj.transform
                            local srcTM = srcObj.transform
                            local relativeTM = srcTM * (inverse refTM)
                            
                            if hasPos then
                                traj.pos = relativeTM.translation
                            if hasRot then
                                traj.rotation = relativeTM.rotation
                        )
                        else
                        (
                            if hasPos then
                                traj.pos = srcObj.pos
                            if hasRot then
                                traj.rotation = srcObj.rotation
                        )
                    )
                )
            )
            
            statusLabel.text = "Re-baked: " + traj.name
        )
    )
    
    -- Delete selected trajectory
    on btnDelete pressed do
    (
        if trajList.selection == 0 then
        (
            messageBox "Please select a trajectory from the list!" title:"Trajectory Manager"
            return false
        )
        
        local trajectories = ExtractTrajectoryTool.findAllTrajectories()
        if trajList.selection > 0 and trajList.selection <= trajectories.count then
        (
            local traj = trajectories[trajList.selection]
            local trajName = traj.name
            
            if queryBox ("Delete trajectory '" + trajName + "'?") title:"Confirm Delete" then
            (
                if ExtractTrajectoryTool.deleteTrajectory traj then
                (
                    statusLabel.text = "Deleted: " + trajName
                    
                    -- Refresh list
                    trajectories = ExtractTrajectoryTool.findAllTrajectories()
                    local trajNames = #()
                    for t in trajectories do
                    (
                        append trajNames (ExtractTrajectoryTool.getTrajectoryInfo t)
                    )
                    trajList.items = trajNames
                )
            )
        )
    )
    
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
            
            -- Refresh trajectory list
            local trajectories = ExtractTrajectoryTool.findAllTrajectories()
            local trajNames = #()
            for traj in trajectories do
            (
                append trajNames (ExtractTrajectoryTool.getTrajectoryInfo traj)
            )
            trajList.items = trajNames
            
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
)

-- Create and show dialog
try (destroyDialog ExtractTrajectoryDialog) catch()
createDialog ExtractTrajectoryDialog
'''

        # Execute the MaxScript to show the dialog
        rt.execute(maxscript)
