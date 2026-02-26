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
    rootNode = undefined,

    -- Auto-detect pelvis (Biped_Object with "pelvis" in name)
    -- and root bone (common export root names)
    fn autoDetect =
    (
        local foundPelvis = undefined
        local foundRoot = undefined

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

    -- Moving average smoothing on a flat array of floats
    fn smoothCurve values passes =
    (
        -- MaxScript's copy() returns OK on arrays; use collect instead
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

    -- Core damping logic shared by preview and apply
    -- Returns array of new pelvis world positions
    fn computeDampedPositions pelvisNode rootNode axisIndex reductionPct smoothPasses startFrame endFrame =
    (
        local totalFrames = endFrame - startFrame + 1
        local originalTime = sliderTime

        -- Sample world positions
        -- Biped_Object exposes world pos via .transform.pos, not .pos
        local pelvisPos = #()
        local rootPos = #()
        for f = startFrame to endFrame do
        (
            sliderTime = f
            append pelvisPos pelvisNode.transform.pos
            append rootPos rootNode.transform.pos
        )
        sliderTime = originalTime

        -- Extract relative forward values (pelvis - root on the chosen axis)
        local relFwd = #()
        for i = 1 to totalFrames do
        (
            local pF = if axisIndex == 1 then pelvisPos[i].x else pelvisPos[i].y
            local rF = if axisIndex == 1 then rootPos[i].x  else rootPos[i].y
            append relFwd (pF - rF)
        )

        -- Optional smoothing before reduction
        if smoothPasses > 0 then
            relFwd = this.smoothCurve relFwd smoothPasses

        -- Compute mean of relative forward
        local sum = 0.0
        for v in relFwd do sum += v
        local meanFwd = sum / totalFrames

        -- Reduce oscillation: new_rel = mean + (rel - mean) * (1 - reduction)
        local dampFactor = 1.0 - (reductionPct / 100.0)

        local newPositions = #()
        for i = 1 to totalFrames do
        (
            local rF = if axisIndex == 1 then rootPos[i].x else rootPos[i].y
            local newRelFwd = meanFwd + (relFwd[i] - meanFwd) * dampFactor
            local newFwd = rF + newRelFwd

            local origPos = pelvisPos[i]
            local newPos = if axisIndex == 1 then
                point3 newFwd origPos.y origPos.z
            else
                point3 origPos.x newFwd origPos.z

            append newPositions newPos
        )

        return newPositions
    ),

    -- Preview: bake to a dummy + draw original/adjusted splines
    fn previewDamping pelvisNode rootNode axisIndex reductionPct smoothPasses startFrame endFrame =
    (
        if pelvisNode == undefined or rootNode == undefined then
        (
            messageBox "Please assign both Pelvis and Root bones." title:"Pelvis Forward Damper"
            return undefined
        )

        this.cleanupPreview()

        local totalFrames = endFrame - startFrame + 1
        local originalTime = sliderTime

        -- Sample original pelvis positions for drawing
        local origPositions = #()
        for f = startFrame to endFrame do
        (
            sliderTime = f
            append origPositions pelvisNode.transform.pos
        )
        sliderTime = originalTime

        local newPositions = this.computeDampedPositions pelvisNode rootNode axisIndex \\
                             reductionPct smoothPasses startFrame endFrame

        -- Animated dummy showing the new path
        -- Note: avoid naming the local 'dummy' — MaxScript is case-insensitive
        -- and it would shadow the Dummy class before the right-hand side is evaluated
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
        sliderTime = originalTime

        -- Original path (red spline)
        local origSpline = SplineShape name:"PelvisDamper_Original"
        addNewSpline origSpline
        for p in origPositions do addKnot origSpline 1 #smooth #curve p
        updateShape origSpline
        origSpline.wirecolor = (color 255 70 70)
        origSpline.render_displayRenderMesh = false

        -- Adjusted path (green spline)
        local newSpline = SplineShape name:"PelvisDamper_Adjusted"
        addNewSpline newSpline
        for p in newPositions do addKnot newSpline 1 #smooth #curve p
        updateShape newSpline
        newSpline.wirecolor = (color 70 255 70)
        newSpline.render_displayRenderMesh = false

        return previewHelper
    ),

    -- Apply damped positions back to the pelvis bone
    fn applyDamping pelvisNode rootNode axisIndex reductionPct smoothPasses startFrame endFrame =
    (
        if pelvisNode == undefined or rootNode == undefined then
        (
            messageBox "Please assign both Pelvis and Root bones." title:"Pelvis Forward Damper"
            return false
        )

        local totalFrames = endFrame - startFrame + 1
        local originalTime = sliderTime

        -- Sample original positions BEFORE writing anything.
        -- Biped_Object requires .transform.pos for reading world position.
        local origPositions = #()
        for f = startFrame to endFrame do
        (
            sliderTime = f
            append origPositions pelvisNode.transform.pos
        )
        sliderTime = originalTime

        local newPositions = this.computeDampedPositions pelvisNode rootNode axisIndex \\
                             reductionPct smoothPasses startFrame endFrame

        -- Biped_Object does not accept .pos assignment.
        -- Use move() with a pre-computed delta instead — biped respects this
        -- and creates the appropriate internal position key.
        with animate on
        (
            for i = 1 to totalFrames do
            (
                sliderTime = startFrame + i - 1
                local delta = newPositions[i] - origPositions[i]
                move pelvisNode delta
            )
        )

        sliderTime = originalTime
        return true
    ),

    fn cleanupPreview =
    (
        local names = #("PelvisDamper_Preview", "PelvisDamper_Original", "PelvisDamper_Adjusted")
        local toDelete = #()
        for obj in objects do
        (
            for n in names do
                if obj.name == n then append toDelete obj
        )
        if toDelete.count > 0 then delete toDelete
    )
)

PelvisForwardDamperTool = PelvisForwardDamperStruct()

rollout PelvisForwardDamperDialog "Pelvis Forward Damper" width:480 height:415
(
    -- Source Bones
    group "Source Bones"
    (
        button autoDetectBtn "Auto-Detect Biped + Root" pos:[20,22] width:430 height:24

        label pelvisLbl "Pelvis:"   pos:[20,57]  width:65 align:#left
        edittext pelvisEdit ""      pos:[88,54]  width:210 height:20 readOnly:true
        pickbutton pelvisPickBtn "Pick" pos:[305,54] width:60 height:20
        button pelvisSelBtn "Sel"   pos:[372,54] width:68 height:20

        label rootLbl "Root:"       pos:[20,84]  width:65 align:#left
        edittext rootEdit ""        pos:[88,81]  width:210 height:20 readOnly:true
        pickbutton rootPickBtn "Pick" pos:[305,81] width:60 height:20
        button rootSelBtn "Sel"     pos:[372,81] width:68 height:20
    )

    -- Forward Axis
    group "World Forward Axis"
    (
        label axisLbl "Which world axis is your character's forward direction?" pos:[20,133] width:400 align:#left
        radiobuttons forwardAxisRadio labels:#("X Axis", "Y Axis") pos:[20,153] default:2 columns:2
    )

    -- Damping settings
    group "Damping"
    (
        label reductionLbl "Reduction:" pos:[20,200] width:75 align:#left
        slider reductionSlider ""       pos:[100,198] width:290 height:22 range:[0,100,50] type:#integer ticks:10
        label reductionValLbl "50%"     pos:[398,200] width:40 align:#left

        label helpTxt "0% = no change       100% = fully flatten (pelvis stays at average offset)" \\
            pos:[20,226] width:440 align:#left

        label smoothLbl "Smoothing passes:" pos:[20,250] width:130 align:#left
        spinner smoothSpn "" pos:[155,248] width:60 height:20 type:#integer range:[0,10,2]
        label smoothHelp "(0 = none, higher = softer curve)" pos:[225,250] width:220 align:#left
    )

    -- Frame Range
    group "Frame Range"
    (
        checkbox useTimelineCB "Use Timeline Range" pos:[20,285] width:160 checked:true
        label startLbl "Start:" pos:[200,285] width:40 align:#left
        spinner startSpn "" pos:[243,283] width:75 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "End:" pos:[330,285] width:35 align:#left
        spinner endSpn "" pos:[366,283] width:75 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    -- Status
    label statusLabel "" pos:[20,325] width:440 height:16 align:#center
    progressBar damperProgress "" pos:[20,344] width:440 height:10 value:0 color:(color 80 200 120)

    -- Action buttons
    button previewBtn  "Preview"         pos:[20,365]  width:130 height:36
    button applyBtn    "Apply to Pelvis" pos:[160,365] width:165 height:36
    button cleanupBtn  "Clear Preview"   pos:[335,365] width:125 height:36

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
    )

    on pelvisPickBtn picked obj do
    (
        PelvisForwardDamperTool.pelvisNode = obj
        pelvisEdit.text = obj.name
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
            statusLabel.text = "Preview ready  |  Red = original path    Green = adjusted path"
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
