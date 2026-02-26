"""
Pelvis Forward Damper Tool for MotionKit

Workflow:
  1. "Create Helper" — bakes the pelvis world position to a Dummy helper,
     then replaces the forward axis with two linear keys (first and last frame).
     X and Z retain all original keys; only the chosen forward axis is flattened.
  2. Inspect the helper in the viewport (green = adjusted path, red = original).
  3. "Apply to Pelvis" — bakes the helper's modified position back to the pelvis
     using the Amount slider to blend between original and fully linearized.

  On first Apply the original pelvis positions are locked in a hidden backup dummy
  so the Amount slider is non-destructive across multiple applies. Use "Start Fresh"
  to commit the current state as the new baseline.
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Pelvis Forward Damper] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger

TOOL_NAME = "Pelvis Forward Damper"


def execute(control=None, event=None):
    if not pymxs or not rt:
        print("[Pelvis Forward Damper] ERROR: Not running in 3ds Max")
        return
    try:
        PelvisForwardDamperDialog().show()
    except Exception as e:
        logger.error(f"Failed to open Pelvis Forward Damper: {str(e)}")
        rt.messageBox(f"Failed to open Pelvis Forward Damper:\n{str(e)}", title="MotionKit Error")


class PelvisForwardDamperDialog:

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        start_frame = int(rt.animationRange.start.frame)
        end_frame   = int(rt.animationRange.end.frame)

        maxscript = f'''
-- ============================================
-- MotionKit Pelvis Forward Damper
-- ============================================

global PelvisForwardDamperTool

struct PelvisForwardDamperStruct
(
    pelvisNode = undefined,

    -- -------------------------------------------------------
    -- Detection
    -- -------------------------------------------------------
    fn autoDetect =
    (
        local foundPelvis = undefined
        for obj in objects do
        (
            if classOf obj == Biped_Object then
            (
                if (findString (toLower obj.name) "pelvis") != undefined then
                (
                    foundPelvis = obj
                    exit
                )
            )
        )
        return foundPelvis
    ),

    -- -------------------------------------------------------
    -- Position sampling
    -- -------------------------------------------------------
    fn samplePositions node startFrame endFrame =
    (
        local positions = #()
        local savedTime = sliderTime
        for f = startFrame to endFrame do
        (
            sliderTime = f
            append positions node.transform.pos
        )
        sliderTime = savedTime
        return positions
    ),

    -- -------------------------------------------------------
    -- Backup — stores original pelvis positions as a hidden dummy
    -- -------------------------------------------------------
    fn backupNodeName = "PelvisDamper_OrigBackup",

    fn findBackup pelvisName startFrame endFrame =
    (
        local node = getNodeByName (this.backupNodeName())
        if node == undefined then return undefined
        try
        (
            if node.mk_pelvisName != pelvisName then return undefined
            if node.mk_startFrame != startFrame  then return undefined
            if node.mk_endFrame   != endFrame    then return undefined
        )
        catch ( return undefined )
        return node
    ),

    fn createBackup pelvisNode startFrame endFrame =
    (
        local old = getNodeByName (this.backupNodeName())
        if old != undefined then delete old

        local origPos = this.samplePositions pelvisNode startFrame endFrame

        local backupNode = Dummy name:(this.backupNodeName()) boxsize:[1,1,1]
        backupNode.isHidden = true

        local ca = attributes "PelvisDamperMeta"
        (
            parameters main
            (
                mk_pelvisName type:#string
                mk_startFrame type:#integer default:0
                mk_endFrame   type:#integer default:100
            )
        )
        custAttributes.add backupNode ca
        backupNode.mk_pelvisName = pelvisNode.name
        backupNode.mk_startFrame = startFrame
        backupNode.mk_endFrame   = endFrame

        local savedTime = sliderTime
        with animate on
        (
            for i = 1 to origPos.count do
            (
                sliderTime = startFrame + i - 1
                backupNode.pos = origPos[i]
            )
        )
        sliderTime = savedTime
        return backupNode
    ),

    fn clearBackupData =
    (
        local node = getNodeByName (this.backupNodeName())
        if node != undefined then delete node
    ),

    fn backupStatus pelvisName startFrame endFrame =
    (
        local node = getNodeByName (this.backupNodeName())
        if node == undefined then return "No original locked"
        try
        (
            if node.mk_pelvisName == pelvisName and \\
               node.mk_startFrame == startFrame  and \\
               node.mk_endFrame   == endFrame    then
                return ("Original locked  [" + startFrame as string + " - " + endFrame as string + "]")
            else
                return "Backup exists but doesn't match current settings"
        )
        catch ( return "No original locked" )
    ),

    -- -------------------------------------------------------
    -- Helper — visible dummy with linearized forward axis
    -- -------------------------------------------------------
    fn helperNodeName = "PelvisLinear_Helper",

    fn createHelper pelvisNode axisIndex startFrame endFrame =
    (
        if pelvisNode == undefined then
        (
            messageBox "Please assign the Pelvis bone first." title:"Pelvis Forward Damper"
            return undefined
        )

        -- Remove any existing helper
        local old = getNodeByName (this.helperNodeName())
        if old != undefined then delete old

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        -- Use backup positions if available so Create Helper is idempotent
        local backup   = this.findBackup pelvisNode.name startFrame endFrame
        local origPos  = if backup != undefined then
            this.samplePositions backup    startFrame endFrame
        else
            this.samplePositions pelvisNode startFrame endFrame

        -- Get forward value at first and last frame before we modify anything
        local startFwd = if axisIndex == 1 then origPos[1].x
                         else if axisIndex == 2 then origPos[1].y
                         else origPos[1].z

        local endFwd   = if axisIndex == 1 then origPos[totalFrames].x
                         else if axisIndex == 2 then origPos[totalFrames].y
                         else origPos[totalFrames].z

        -- Create the helper
        local newHelper = Dummy name:(this.helperNodeName()) boxsize:[8,8,8]
        newHelper.wirecolor = (color 80 200 255)

        -- Bake in a single pass:
        -- X and Z come straight from the original pelvis positions.
        -- The forward axis is replaced with a linear interpolation between
        -- the first and last frame values — no sub-controller manipulation needed.
        with animate on
        (
            for i = 1 to totalFrames do
            (
                local t = if totalFrames > 1 then
                    (i - 1) as float / (totalFrames - 1) as float
                else 0.0

                local linearFwd = startFwd + (endFwd - startFwd) * t
                local origP     = origPos[i]

                local newPos = if axisIndex == 1 then point3 linearFwd origP.y origP.z
                               else if axisIndex == 2 then point3 origP.x linearFwd origP.z
                               else point3 origP.x origP.y linearFwd

                sliderTime = startFrame + i - 1
                newHelper.pos = newPos
            )
        )
        sliderTime = savedTime

        return newHelper
    ),

    fn deleteHelper =
    (
        local node = getNodeByName (this.helperNodeName())
        if node != undefined then delete node
    ),

    -- -------------------------------------------------------
    -- Apply helper positions back to the pelvis
    -- amount (0-100): 0 = no change, 100 = fully linearized
    -- -------------------------------------------------------
    fn applyHelperToPelvis pelvisNode axisIndex amount startFrame endFrame =
    (
        if pelvisNode == undefined then
        (
            messageBox "Please assign the Pelvis bone first." title:"Pelvis Forward Damper"
            return false
        )

        local helperNode = getNodeByName (this.helperNodeName())
        if helperNode == undefined then
        (
            messageBox "No helper found. Run 'Create Helper' first." title:"Pelvis Forward Damper"
            return false
        )

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        -- Ensure original is backed up
        local backup = this.findBackup pelvisNode.name startFrame endFrame
        if backup == undefined then
            backup = this.createBackup pelvisNode startFrame endFrame

        -- Helper = linearized target; backup = original
        local helperPos = this.samplePositions helperNode startFrame endFrame
        local origPos   = this.samplePositions backup     startFrame endFrame

        -- Blend between original and helper
        local blendWeight = amount / 100.0
        local targetPos = #()
        for i = 1 to totalFrames do
        (
            local t = origPos[i] + (helperPos[i] - origPos[i]) * blendWeight
            append targetPos t
        )

        -- Delta from current pelvis to blended target
        local currentPos = this.samplePositions pelvisNode startFrame endFrame
        sliderTime = savedTime

        with animate on
        (
            for i = 1 to totalFrames do
            (
                sliderTime = startFrame + i - 1
                local delta = targetPos[i] - currentPos[i]
                move pelvisNode delta
            )
        )

        sliderTime = savedTime
        return true
    )
)

PelvisForwardDamperTool = PelvisForwardDamperStruct()

-- ============================================================
-- Dialog
-- ============================================================
rollout PelvisForwardDamperDialog "Pelvis Forward Damper" width:460 height:400
(
    group "Source Bone"
    (
        button autoDetectBtn "Auto-Detect Biped Pelvis" pos:[20,22] width:410 height:24
        label pelvisLbl "Pelvis:" pos:[20,57]  width:55 align:#left
        edittext pelvisEdit ""   pos:[78,54]  width:200 height:20 readOnly:true
        pickbutton pelvisPickBtn "Pick" pos:[285,54] width:60 height:20
        button pelvisSelBtn "Sel"       pos:[352,54] width:68 height:20
    )

    group "World Forward Axis"
    (
        label axisLbl "Which world axis is your character's forward direction?" pos:[20,133] width:400 align:#left
        radiobuttons forwardAxisRadio labels:#("X", "Y", "Z") pos:[20,153] default:2 columns:3
    )

    group "Amount"
    (
        label amountLbl "Amount:" pos:[20,198] width:60 align:#left
        slider amountSlider ""    pos:[85,196] width:285 height:22 range:[0,100,100] type:#integer ticks:10
        label amountValLbl "100%" pos:[378,198] width:45 align:#left
        label helpTxt "0% = no change    100% = straight line between first and last frame" \\
            pos:[20,222] width:420 align:#left
    )

    group "Frame Range"
    (
        checkbox useTimelineCB "Use Timeline Range" pos:[20,252] width:160 checked:true
        label startLbl "Start:" pos:[195,252] width:40 align:#left
        spinner startSpn "" pos:[238,250] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "End:"   pos:[320,252] width:35 align:#left
        spinner endSpn ""   pos:[355,250] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    group "Original Baseline"
    (
        label backupStatusLbl "No original locked" pos:[20,292] width:300 height:16 align:#left
        button startFreshBtn "Start Fresh"         pos:[300,287] width:130 height:22
    )

    label statusLabel "" pos:[20,322] width:420 height:16 align:#center
    progressBar damperProgress "" pos:[20,341] width:420 height:10 value:0 color:(color 80 200 120)

    button createHelperBtn "Create Helper"    pos:[20,362]  width:130 height:36
    button applyBtn        "Apply to Pelvis"  pos:[160,362] width:145 height:36
    button deleteHelperBtn "Delete Helper"    pos:[315,362] width:125 height:36

    -- --------------------------------------------------------
    fn refreshBackupStatus =
    (
        if PelvisForwardDamperTool.pelvisNode == undefined then
        (
            backupStatusLbl.text = "No pelvis selected"
            return false
        )
        backupStatusLbl.text = PelvisForwardDamperTool.backupStatus \\
            PelvisForwardDamperTool.pelvisNode.name startSpn.value endSpn.value
    )

    on PelvisForwardDamperDialog open do
    (
        startSpn.value = animationRange.start.frame as integer
        endSpn.value   = animationRange.end.frame as integer
    )

    on useTimelineCB changed state do
    (
        startSpn.enabled = not state
        endSpn.enabled   = not state
        if state then
        (
            startSpn.value = animationRange.start.frame as integer
            endSpn.value   = animationRange.end.frame as integer
        )
        refreshBackupStatus()
    )

    on amountSlider changed val do
        amountValLbl.text = val as string + "%"

    on autoDetectBtn pressed do
    (
        local pelvis = PelvisForwardDamperTool.autoDetect()
        if pelvis != undefined then
        (
            PelvisForwardDamperTool.pelvisNode = pelvis
            pelvisEdit.text = pelvis.name
            statusLabel.text = "Detected: " + pelvis.name
        )
        else
            statusLabel.text = "No biped pelvis found - pick manually"
        refreshBackupStatus()
    )

    on pelvisPickBtn picked obj do
    (
        PelvisForwardDamperTool.pelvisNode = obj
        pelvisEdit.text = obj.name
        refreshBackupStatus()
    )

    on pelvisSelBtn pressed do
    (
        if selection.count != 1 then
        (
            messageBox "Select exactly one object first." title:"Pelvis Forward Damper"
            return false
        )
        PelvisForwardDamperTool.pelvisNode = selection[1]
        pelvisEdit.text = selection[1].name
        refreshBackupStatus()
    )

    on startFreshBtn pressed do
    (
        if queryBox "Clear the locked original?\\nThe next Apply will lock the current pelvis state as the new baseline." \\
            title:"Start Fresh" then
        (
            PelvisForwardDamperTool.clearBackupData()
            statusLabel.text = "Backup cleared"
            refreshBackupStatus()
        )
    )

    on createHelperBtn pressed do
    (
        if PelvisForwardDamperTool.pelvisNode == undefined then
        (
            messageBox "Please assign the Pelvis bone first." title:"Pelvis Forward Damper"
            return false
        )

        statusLabel.text = "Creating helper..."
        damperProgress.value = 30
        windows.processPostedMessages()

        local result = PelvisForwardDamperTool.createHelper \\
            PelvisForwardDamperTool.pelvisNode \\
            forwardAxisRadio.state \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if result != undefined then
        (
            select result
            statusLabel.text = "Helper created: " + result.name + "  (forward axis linearized)"
        )
        else
            statusLabel.text = "Failed to create helper"

        sleep 0.5
        damperProgress.value = 0
    )

    on applyBtn pressed do
    (
        if PelvisForwardDamperTool.pelvisNode == undefined then
        (
            messageBox "Please assign the Pelvis bone first." title:"Pelvis Forward Damper"
            return false
        )

        local helperCheck = getNodeByName (PelvisForwardDamperTool.helperNodeName())
        if helperCheck == undefined then
        (
            messageBox "No helper found. Click 'Create Helper' first." title:"Pelvis Forward Damper"
            return false
        )

        local msg = "Apply " + amountSlider.value as string + "% linearization to " + \\
                    PelvisForwardDamperTool.pelvisNode.name + "?\\n\\nUndo with Ctrl+Z."
        if not (queryBox msg title:"Confirm Apply") then return false

        statusLabel.text = "Applying..."
        damperProgress.value = 20
        windows.processPostedMessages()

        local ok = PelvisForwardDamperTool.applyHelperToPelvis \\
            PelvisForwardDamperTool.pelvisNode \\
            forwardAxisRadio.state \\
            amountSlider.value \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if ok then
            statusLabel.text = "Done - forward axis linearized " + amountSlider.value as string + "%"
        else
            statusLabel.text = "Failed"

        refreshBackupStatus()

        sleep 0.5
        damperProgress.value = 0
    )

    on deleteHelperBtn pressed do
    (
        PelvisForwardDamperTool.deleteHelper()
        statusLabel.text = "Helper deleted"
    )

    on PelvisForwardDamperDialog close do
    (
        -- leave helper in scene so user can inspect it after closing
    )
)

try (destroyDialog PelvisForwardDamperDialog) catch()
createDialog PelvisForwardDamperDialog
'''

        rt.execute(maxscript)
