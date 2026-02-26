"""
Pelvis Forward Damper Tool for MotionKit
Reduces pelvis forward-backward oscillation after the root curve is linearized

The problem this solves:
  When you linearize a root bone's forward movement (constant speed for game export),
  the pelvis's natural forward-backward bob becomes visually exaggerated because it's
  no longer partially masked by the root's uneven speed.

The fix:
  Compute the relative forward offset between pelvis and root, then reduce how much
  it deviates from its mean. All other axes (side-to-side, vertical) are untouched.

  On first Apply the original pelvis positions are locked into a hidden backup dummy.
  Every subsequent Apply and Preview always computes from those locked originals so
  the slider is non-destructive — you can dial it up or down freely. Use
  "Start Fresh" to commit the current state as the new baseline.

Usage: Pick pelvis and root bones, set reduction amount, preview, then apply.
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
    """Execute the Pelvis Forward Damper tool"""
    if not pymxs or not rt:
        print("[Pelvis Forward Damper] ERROR: Not running in 3ds Max")
        return

    try:
        dialog = PelvisForwardDamperDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open Pelvis Forward Damper: {str(e)}")
        rt.messageBox(
            f"Failed to open Pelvis Forward Damper:\n{str(e)}",
            title="MotionKit Error"
        )


class PelvisForwardDamperDialog:
    """Pelvis Forward Damper dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        """Show the dialog using MaxScript"""

        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)

        maxscript = f'''
-- ============================================
-- MotionKit Pelvis Forward Damper
-- ============================================

global PelvisForwardDamperTool

struct PelvisForwardDamperStruct
(
    pelvisNode = undefined,
    rootNode   = undefined,

    -- -------------------------------------------------------
    -- Detection
    -- -------------------------------------------------------
    fn autoDetect =
    (
        local foundPelvis = undefined
        local foundRoot   = undefined

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

        local rootCandidates = #("root", "Root", "ROOT", "root_bone", "Root_Bone",
                                  "character_root", "Character_Root", "pelvis_root")
        for n in rootCandidates do
        (
            local node = getNodeByName n
            if node != undefined then
            (
                foundRoot = node
                exit
            )
        )

        return #(foundPelvis, foundRoot)
    ),

    -- -------------------------------------------------------
    -- Position sampling — works for any node type
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
    -- Backup management
    -- The backup is a hidden Dummy whose baked animation holds
    -- the pelvis world positions from before any damping was applied.
    -- It persists in the scene so the slider stays non-destructive.
    -- -------------------------------------------------------
    fn backupNodeName = "PelvisDamper_OrigBackup",

    fn findBackup pelvisName startFrame endFrame =
    (
        local node = getNodeByName (this.backupNodeName())
        if node == undefined then return undefined

        -- Verify it matches the current pelvis and frame range
        try
        (
            if node.mk_pelvisName != pelvisName  then return undefined
            if node.mk_startFrame != startFrame  then return undefined
            if node.mk_endFrame   != endFrame    then return undefined
        )
        catch ( return undefined )

        return node
    ),

    fn createBackup pelvisNode startFrame endFrame =
    (
        -- Remove any stale backup
        local old = getNodeByName (this.backupNodeName())
        if old != undefined then delete old

        -- Sample the current (original) pelvis positions
        local origPos = this.samplePositions pelvisNode startFrame endFrame

        -- Hidden dummy to hold the baked positions
        local backupNode = Dummy name:(this.backupNodeName()) boxsize:[1,1,1]
        backupNode.isHidden = true

        -- Tag it with metadata so we can validate it later
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

        -- Bake original positions into the dummy
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

    -- Delete the backup (user wants a fresh baseline from current state)
    fn clearBackupData =
    (
        local node = getNodeByName (this.backupNodeName())
        if node != undefined then delete node
    ),

    -- Restore the pelvis to the stored originals
    fn restoreFromBackup pelvisNode startFrame endFrame =
    (
        local backup = this.findBackup pelvisNode.name startFrame endFrame
        if backup == undefined then
        (
            messageBox "No matching backup found for this pelvis / frame range." \\
                title:"Pelvis Forward Damper"
            return false
        )

        local origPos    = this.samplePositions backup   startFrame endFrame
        local currentPos = this.samplePositions pelvisNode startFrame endFrame
        local totalFrames = endFrame - startFrame + 1

        local savedTime = sliderTime
        with animate on
        (
            for i = 1 to totalFrames do
            (
                sliderTime = startFrame + i - 1
                local delta = origPos[i] - currentPos[i]
                move pelvisNode delta
            )
        )
        sliderTime = savedTime
        return true
    ),

    -- Return a human-readable backup status string for the UI
    fn backupStatus pelvisName startFrame endFrame =
    (
        local node = getNodeByName (this.backupNodeName())
        if node == undefined then return "No original locked"
        try
        (
            if node.mk_pelvisName == pelvisName and \\
               node.mk_startFrame == startFrame and \\
               node.mk_endFrame   == endFrame then
                return ("Original locked  [" + startFrame as string + " - " + endFrame as string + "]")
            else
                return "Backup exists but doesn't match current settings"
        )
        catch ( return "No original locked" )
    ),

    -- -------------------------------------------------------
    -- Math
    -- -------------------------------------------------------
    fn smoothCurve values passes =
    (
        -- MaxScript copy() returns OK on arrays; use collect instead
        local result = for v in values collect v
        for p = 1 to passes do
        (
            local smoothed = for v in result collect v
            for i = 2 to (result.count - 1) do
                smoothed[i] = (result[i-1] + result[i] + result[i+1]) / 3.0
            result = smoothed
        )
        return result
    ),

    -- Takes explicit position arrays (not scene nodes) so it always
    -- works from whichever baseline the caller chose.
    fn computeDampedPositions origPelvisPos rootPos axisIndex reductionPct smoothPasses =
    (
        local totalFrames = origPelvisPos.count

        local relFwd = #()
        for i = 1 to totalFrames do
        (
            local pF = if axisIndex == 1 then origPelvisPos[i].x else origPelvisPos[i].y
            local rF = if axisIndex == 1 then rootPos[i].x       else rootPos[i].y
            append relFwd (pF - rF)
        )

        if smoothPasses > 0 then
            relFwd = this.smoothCurve relFwd smoothPasses

        local sum = 0.0
        for v in relFwd do sum += v
        local meanFwd = sum / totalFrames

        local dampFactor = 1.0 - (reductionPct / 100.0)

        local newPositions = #()
        for i = 1 to totalFrames do
        (
            local rF       = if axisIndex == 1 then rootPos[i].x else rootPos[i].y
            local newRelFwd = meanFwd + (relFwd[i] - meanFwd) * dampFactor
            local newFwd    = rF + newRelFwd

            local origPos = origPelvisPos[i]
            local newPos  = if axisIndex == 1 then
                point3 newFwd origPos.y origPos.z
            else
                point3 origPos.x newFwd origPos.z

            append newPositions newPos
        )

        -- First and last frame must stay exactly at the original position
        newPositions[1]           = origPelvisPos[1]
        newPositions[totalFrames] = origPelvisPos[totalFrames]

        return newPositions
    ),

    -- -------------------------------------------------------
    -- Preview
    -- -------------------------------------------------------
    fn previewDamping pelvisNode rootNode axisIndex reductionPct smoothPasses startFrame endFrame =
    (
        if pelvisNode == undefined or rootNode == undefined then
        (
            messageBox "Please assign both Pelvis and Root bones." title:"Pelvis Forward Damper"
            return undefined
        )

        this.cleanupPreview()

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        -- Use locked originals if available, otherwise sample current pelvis
        local backup = this.findBackup pelvisNode.name startFrame endFrame
        local origPelvisPos = if backup != undefined then
            this.samplePositions backup   startFrame endFrame
        else
            this.samplePositions pelvisNode startFrame endFrame

        local rootPos     = this.samplePositions rootNode startFrame endFrame
        local newPositions = this.computeDampedPositions origPelvisPos rootPos \\
                             axisIndex reductionPct smoothPasses

        -- Animated dummy showing the adjusted path
        -- (name local 'previewHelper' to avoid shadowing the Dummy class)
        local previewHelper = Dummy name:"PelvisDamper_Preview" boxsize:[10,10,10]
        previewHelper.wirecolor = (color 80 255 120)
        with animate on
        (
            for i = 1 to totalFrames do
            (
                sliderTime = startFrame + i - 1
                previewHelper.pos = newPositions[i]
            )
        )
        sliderTime = savedTime

        -- Red = original path, Green = adjusted path
        local origSpline = SplineShape name:"PelvisDamper_Original"
        addNewSpline origSpline
        for p in origPelvisPos do addKnot origSpline 1 #smooth #curve p
        updateShape origSpline
        origSpline.wirecolor = (color 255 70 70)
        origSpline.render_displayRenderMesh = false

        local newSpline = SplineShape name:"PelvisDamper_Adjusted"
        addNewSpline newSpline
        for p in newPositions do addKnot newSpline 1 #smooth #curve p
        updateShape newSpline
        newSpline.wirecolor = (color 70 255 70)
        newSpline.render_displayRenderMesh = false

        return previewHelper
    ),

    -- -------------------------------------------------------
    -- Apply
    -- -------------------------------------------------------
    fn applyDamping pelvisNode rootNode axisIndex reductionPct smoothPasses startFrame endFrame =
    (
        if pelvisNode == undefined or rootNode == undefined then
        (
            messageBox "Please assign both Pelvis and Root bones." title:"Pelvis Forward Damper"
            return false
        )

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        -- Ensure we have locked originals. Create backup on first apply.
        local backup = this.findBackup pelvisNode.name startFrame endFrame
        if backup == undefined then
            backup = this.createBackup pelvisNode startFrame endFrame

        -- Always compute the target from the locked originals
        local origPelvisPos = this.samplePositions backup    startFrame endFrame
        local rootPos       = this.samplePositions rootNode  startFrame endFrame
        local newPositions  = this.computeDampedPositions origPelvisPos rootPos \\
                              axisIndex reductionPct smoothPasses

        -- Sample where the pelvis currently sits (may already be damped from a
        -- previous apply). The delta moves it from current to the new target.
        local currentPos = this.samplePositions pelvisNode startFrame endFrame
        sliderTime = savedTime

        with animate on
        (
            for i = 1 to totalFrames do
            (
                -- Leave first and last frame completely untouched
                if i != 1 and i != totalFrames then
                (
                    sliderTime = startFrame + i - 1
                    local delta = newPositions[i] - currentPos[i]
                    move pelvisNode delta
                )
            )
        )

        sliderTime = savedTime
        return true
    ),

    -- -------------------------------------------------------
    -- Cleanup
    -- -------------------------------------------------------
    fn cleanupPreview =
    (
        local names = #("PelvisDamper_Preview", "PelvisDamper_Original", "PelvisDamper_Adjusted")
        local toDelete = #()
        for obj in objects do
            for n in names do
                if obj.name == n then append toDelete obj
        if toDelete.count > 0 then delete toDelete
    )
)

PelvisForwardDamperTool = PelvisForwardDamperStruct()

-- ============================================================
-- Dialog
-- ============================================================
rollout PelvisForwardDamperDialog "Pelvis Forward Damper" width:480 height:465
(
    -- Source Bones
    group "Source Bones"
    (
        button autoDetectBtn "Auto-Detect Biped + Root" pos:[20,22] width:430 height:24

        label pelvisLbl "Pelvis:"  pos:[20,57]  width:60 align:#left
        edittext pelvisEdit ""     pos:[83,54]  width:215 height:20 readOnly:true
        pickbutton pelvisPickBtn "Pick" pos:[305,54] width:60 height:20
        button pelvisSelBtn "Sel"  pos:[372,54] width:68 height:20

        label rootLbl "Root:"      pos:[20,84]  width:60 align:#left
        edittext rootEdit ""       pos:[83,81]  width:215 height:20 readOnly:true
        pickbutton rootPickBtn "Pick" pos:[305,81] width:60 height:20
        button rootSelBtn "Sel"    pos:[372,81] width:68 height:20
    )

    -- Forward Axis
    group "World Forward Axis"
    (
        label axisLbl "Which world axis is your character's forward direction?" pos:[20,133] width:400 align:#left
        radiobuttons forwardAxisRadio labels:#("X Axis", "Y Axis") pos:[20,153] default:2 columns:2
    )

    -- Damping
    group "Damping"
    (
        label reductionLbl "Reduction:" pos:[20,200] width:75 align:#left
        slider reductionSlider ""       pos:[100,198] width:285 height:22 range:[0,100,50] type:#integer ticks:10
        label reductionValLbl "50%"     pos:[393,200] width:45 align:#left

        label helpTxt "0% = no change       100% = flatten to average offset" \\
            pos:[20,226] width:440 align:#left

        label smoothLbl "Smoothing passes:" pos:[20,250] width:130 align:#left
        spinner smoothSpn "" pos:[155,248] width:55 height:20 type:#integer range:[0,10,2]
        label smoothHelp "(0 = none)" pos:[218,250] width:90 align:#left
    )

    -- Frame Range
    group "Frame Range"
    (
        checkbox useTimelineCB "Use Timeline Range" pos:[20,285] width:160 checked:true
        label startLbl "Start:" pos:[200,285] width:40 align:#left
        spinner startSpn "" pos:[243,283] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "End:"   pos:[325,285] width:35 align:#left
        spinner endSpn ""   pos:[360,283] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    -- Backup status
    group "Original Baseline"
    (
        label backupStatusLbl "No original locked" pos:[20,325] width:340 height:16 align:#left
        button startFreshBtn  "Start Fresh"        pos:[320,320] width:120 height:22
        button restoreOrigBtn "Restore Original"   pos:[20,348]  width:200 height:22
        label restoreHelp "Reverts pelvis to the locked original" pos:[230,352] width:210 align:#left
    )

    -- Status / progress
    label statusLabel "" pos:[20,382] width:440 height:16 align:#center
    progressBar damperProgress "" pos:[20,401] width:440 height:10 value:0 color:(color 80 200 120)

    -- Action buttons
    button previewBtn  "Preview"         pos:[20,422]  width:130 height:36
    button applyBtn    "Apply to Pelvis" pos:[160,422] width:165 height:36
    button cleanupBtn  "Clear Preview"   pos:[335,422] width:125 height:36

    -- --------------------------------------------------------
    fn refreshBackupStatus =
    (
        if PelvisForwardDamperTool.pelvisNode == undefined then
        (
            backupStatusLbl.text = "No pelvis selected"
            return false
        )
        local s = PelvisForwardDamperTool.backupStatus \\
            PelvisForwardDamperTool.pelvisNode.name startSpn.value endSpn.value
        backupStatusLbl.text = s
    )

    -- Init
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

    on reductionSlider changed val do
    (
        reductionValLbl.text = val as string + "%"
    )

    on autoDetectBtn pressed do
    (
        local result  = PelvisForwardDamperTool.autoDetect()
        local pelvis  = result[1]
        local root    = result[2]

        if pelvis != undefined then
        (
            PelvisForwardDamperTool.pelvisNode = pelvis
            pelvisEdit.text = pelvis.name
        )
        if root != undefined then
        (
            PelvisForwardDamperTool.rootNode = root
            rootEdit.text = root.name
        )

        if pelvis != undefined and root != undefined then
            statusLabel.text = "Detected: " + pelvis.name + "  +  " + root.name
        else if pelvis == undefined and root == undefined then
            statusLabel.text = "Nothing found - pick bones manually"
        else
            statusLabel.text = "Partial detection - check assignments above"

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

    on rootPickBtn picked obj do
    (
        PelvisForwardDamperTool.rootNode = obj
        rootEdit.text = obj.name
    )

    on rootSelBtn pressed do
    (
        if selection.count != 1 then
        (
            messageBox "Select exactly one object first." title:"Pelvis Forward Damper"
            return false
        )
        PelvisForwardDamperTool.rootNode = selection[1]
        rootEdit.text = selection[1].name
    )

    on startFreshBtn pressed do
    (
        if queryBox "Clear the locked original?\\nThe next Apply will lock the current pelvis state as the new baseline." \\
            title:"Start Fresh" then
        (
            PelvisForwardDamperTool.clearBackupData()
            statusLabel.text = "Backup cleared - next Apply will lock current state"
            refreshBackupStatus()
        )
    )

    on restoreOrigBtn pressed do
    (
        if PelvisForwardDamperTool.pelvisNode == undefined then
        (
            messageBox "Please assign the Pelvis bone first." title:"Pelvis Forward Damper"
            return false
        )

        if not (queryBox "Restore pelvis to the locked original positions?\\nUndo with Ctrl+Z." \\
            title:"Restore Original") then return false

        statusLabel.text = "Restoring..."
        damperProgress.value = 30
        windows.processPostedMessages()

        local ok = PelvisForwardDamperTool.restoreFromBackup \\
            PelvisForwardDamperTool.pelvisNode startSpn.value endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if ok then
            statusLabel.text = "Pelvis restored to original"
        else
            statusLabel.text = "Restore failed - no matching backup"

        sleep 0.5
        damperProgress.value = 0
    )

    on previewBtn pressed do
    (
        if PelvisForwardDamperTool.pelvisNode == undefined or \\
           PelvisForwardDamperTool.rootNode == undefined then
        (
            messageBox "Please assign Pelvis and Root bones first." title:"Pelvis Forward Damper"
            return false
        )

        statusLabel.text = "Sampling and computing..."
        damperProgress.value = 30
        windows.processPostedMessages()

        PelvisForwardDamperTool.cleanupPreview()

        local result = PelvisForwardDamperTool.previewDamping \\
            PelvisForwardDamperTool.pelvisNode \\
            PelvisForwardDamperTool.rootNode \\
            forwardAxisRadio.state \\
            reductionSlider.value \\
            smoothSpn.value \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if result != undefined then
            statusLabel.text = "Preview ready  |  Red = original    Green = adjusted"
        else
            statusLabel.text = "Preview failed - check bone assignments"

        sleep 0.5
        damperProgress.value = 0
    )

    on applyBtn pressed do
    (
        if PelvisForwardDamperTool.pelvisNode == undefined or \\
           PelvisForwardDamperTool.rootNode == undefined then
        (
            messageBox "Please assign Pelvis and Root bones first." title:"Pelvis Forward Damper"
            return false
        )

        local msg = "Apply " + reductionSlider.value as string + "% forward damping to " + \\
                    PelvisForwardDamperTool.pelvisNode.name + "?\\n\\n" + \\
                    "This writes keys directly to the pelvis bone.\\nUndo with Ctrl+Z."
        if not (queryBox msg title:"Confirm Apply") then return false

        PelvisForwardDamperTool.cleanupPreview()

        statusLabel.text = "Applying..."
        damperProgress.value = 20
        windows.processPostedMessages()

        local ok = PelvisForwardDamperTool.applyDamping \\
            PelvisForwardDamperTool.pelvisNode \\
            PelvisForwardDamperTool.rootNode \\
            forwardAxisRadio.state \\
            reductionSlider.value \\
            smoothSpn.value \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if ok then
            statusLabel.text = "Done - forward oscillation reduced by " + reductionSlider.value as string + "%"
        else
            statusLabel.text = "Failed"

        refreshBackupStatus()

        sleep 0.5
        damperProgress.value = 0
    )

    on cleanupBtn pressed do
    (
        PelvisForwardDamperTool.cleanupPreview()
        statusLabel.text = "Preview cleared"
    )

    on PelvisForwardDamperDialog close do
    (
        PelvisForwardDamperTool.cleanupPreview()
    )
)

try (destroyDialog PelvisForwardDamperDialog) catch()
createDialog PelvisForwardDamperDialog
'''

        rt.execute(maxscript)
