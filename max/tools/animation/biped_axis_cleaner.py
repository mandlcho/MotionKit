"""
Biped Axis Cleaner Tool for MotionKit

Workflow:
  1. "Create Helper" — bakes the pelvis world position to a Dummy helper,
     then replaces ALL three axes with two linear keys (first and last frame).
     The helper represents the 100% fully-linearized target path.
  2. Inspect the helper in the viewport.
  3. Set per-axis blend weights (0 = keep original, 100 = fully linearized).
  4. "Apply to Pelvis" — blends each axis independently toward the helper.

  On first Apply the original pelvis positions are locked in a hidden backup dummy
  so the weights are non-destructive across multiple applies.
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Biped Axis Cleaner] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Biped Axis Cleaner"


def execute(control=None, event=None):
    if not pymxs or not rt:
        print("[Biped Axis Cleaner] ERROR: Not running in 3ds Max")
        return
    try:
        BipedAxisCleanerDialog().show()
    except Exception as e:
        logger.error(f"Failed to open Biped Axis Cleaner: {str(e)}")
        rt.messageBox(f"Failed to open Biped Axis Cleaner:\n{str(e)}", title="MotionKit Error")


class BipedAxisCleanerDialog:

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        start_frame = int(rt.animationRange.start.frame)
        end_frame   = int(rt.animationRange.end.frame)

        # UI strings
        title               = t('tools.biped_axis_cleaner.title')
        group_source        = t('tools.biped_axis_cleaner.group_source')
        btn_auto_detect     = t('tools.biped_axis_cleaner.btn_auto_detect')
        lbl_pelvis          = t('tools.biped_axis_cleaner.lbl_pelvis')
        btn_pick            = t('common.pick')
        btn_sel             = t('tools.biped_axis_cleaner.btn_sel')
        group_axis          = t('tools.biped_axis_cleaner.group_axis')
        lbl_axis_question   = t('tools.biped_axis_cleaner.lbl_axis_question')
        group_frame_range   = t('tools.biped_axis_cleaner.group_frame_range')
        cb_use_timeline     = t('tools.biped_axis_cleaner.cb_use_timeline')
        lbl_start           = t('tools.biped_axis_cleaner.lbl_start')
        lbl_end             = t('tools.biped_axis_cleaner.lbl_end')
        group_weights       = t('tools.biped_axis_cleaner.group_weights')
        lbl_weight_hint     = t('tools.biped_axis_cleaner.lbl_weight_hint')
        btn_create_helper   = t('tools.biped_axis_cleaner.btn_create_helper')
        btn_apply           = t('tools.biped_axis_cleaner.btn_apply')
        btn_delete_helper   = t('tools.biped_axis_cleaner.btn_delete_helper')

        # Error / status strings
        err_assign_pelvis       = t('tools.biped_axis_cleaner.err_assign_pelvis')
        err_no_helper           = t('tools.biped_axis_cleaner.err_no_helper')
        err_select_one          = t('tools.biped_axis_cleaner.err_select_one')
        confirm_apply_tpl       = t('tools.biped_axis_cleaner.confirm_apply')
        msg_done                = t('tools.biped_axis_cleaner.msg_done')
        msg_detected_prefix     = t('tools.biped_axis_cleaner.msg_detected_prefix')
        msg_no_biped            = t('tools.biped_axis_cleaner.msg_no_biped')
        msg_creating            = t('tools.biped_axis_cleaner.msg_creating')
        msg_helper_created_sfx  = t('tools.biped_axis_cleaner.msg_helper_created_sfx')
        msg_failed_helper       = t('tools.biped_axis_cleaner.msg_failed_helper')
        msg_applying            = t('tools.biped_axis_cleaner.msg_applying')
        msg_failed              = t('tools.biped_axis_cleaner.msg_failed')
        msg_helper_deleted      = t('tools.biped_axis_cleaner.msg_helper_deleted')

        maxscript = f'''
-- ============================================
-- MotionKit Biped Axis Cleaner
-- ============================================

global BipedAxisCleanerTool

struct BipedAxisCleanerStruct
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
    fn backupNodeName = "BipedAxisCleaner_OrigBackup",

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

        local ca = attributes "BipedAxisCleanerMeta"
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

    -- -------------------------------------------------------
    -- Helper — visible dummy with ALL axes linearized
    -- This is the 100% target; per-axis blend weights are
    -- applied at Apply time, not baked into the helper.
    -- -------------------------------------------------------
    fn helperNodeName = "BipedAxisCleaner_Helper",

    fn createHelper pelvisNode startFrame endFrame =
    (
        if pelvisNode == undefined then
        (
            messageBox "{err_assign_pelvis}" title:"{title}"
            return undefined
        )

        -- Remove any existing helper
        local old = getNodeByName (this.helperNodeName())
        if old != undefined then delete old

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        -- Use backup positions if available so Create Helper is idempotent
        local backup  = this.findBackup pelvisNode.name startFrame endFrame
        local origPos = if backup != undefined then
            this.samplePositions backup     startFrame endFrame
        else
            this.samplePositions pelvisNode startFrame endFrame

        -- First and last world positions
        local p0 = origPos[1]
        local p1 = origPos[totalFrames]

        -- Create the helper
        local newHelper = Dummy name:(this.helperNodeName()) boxsize:[8,8,8]
        newHelper.wirecolor = (color 80 200 255)

        -- Bake a fully linearized path on all three axes.
        -- X, Y, Z each interpolate independently from their
        -- first-frame value to their last-frame value.
        with animate on
        (
            for i = 1 to totalFrames do
            (
                local lerpT = if totalFrames > 1 then
                    (i - 1) as float / (totalFrames - 1) as float
                else 0.0

                local newPos = point3 \\
                    (p0.x + (p1.x - p0.x) * lerpT) \\
                    (p0.y + (p1.y - p0.y) * lerpT) \\
                    (p0.z + (p1.z - p0.z) * lerpT)

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
    -- Apply helper positions back to the pelvis with
    -- independent per-axis blend weights (0-100 each).
    --   0   = keep original movement on that axis
    --   100 = fully linearized on that axis
    -- -------------------------------------------------------
    fn applyHelperToPelvis pelvisNode amountX amountY amountZ startFrame endFrame =
    (
        if pelvisNode == undefined then
        (
            messageBox "{err_assign_pelvis}" title:"{title}"
            return false
        )

        local helperNode = getNodeByName (this.helperNodeName())
        if helperNode == undefined then
        (
            messageBox "{err_no_helper}" title:"{title}"
            return false
        )

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        -- Ensure original is backed up
        local backup = this.findBackup pelvisNode.name startFrame endFrame
        if backup == undefined then
            backup = this.createBackup pelvisNode startFrame endFrame

        -- Helper = fully linearized target; backup = original
        local helperPos = this.samplePositions helperNode startFrame endFrame
        local origPos   = this.samplePositions backup     startFrame endFrame

        local wX = amountX / 100.0
        local wY = amountY / 100.0
        local wZ = amountZ / 100.0

        -- Blend each axis independently toward the linearized target
        local targetPos = #()
        for i = 1 to totalFrames do
        (
            local orig   = origPos[i]
            local helper = helperPos[i]
            local blended = point3 \\
                (orig.x + (helper.x - orig.x) * wX) \\
                (orig.y + (helper.y - orig.y) * wY) \\
                (orig.z + (helper.z - orig.z) * wZ)
            append targetPos blended
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

BipedAxisCleanerTool = BipedAxisCleanerStruct()

-- ============================================================
-- Dialog
-- ============================================================
rollout BipedAxisCleanerDialog "{title}" width:460 height:370
(
    group "{group_source}"
    (
        button autoDetectBtn "{btn_auto_detect}" pos:[20,22] width:410 height:24
        label pelvisLbl "{lbl_pelvis}" pos:[20,57]  width:55 align:#left
        edittext pelvisEdit ""         pos:[78,54]  width:200 height:20 readOnly:true
        pickbutton pelvisPickBtn "{btn_pick}" pos:[285,54] width:60 height:20
        button pelvisSelBtn "{btn_sel}"       pos:[352,54] width:68 height:20
    )

    group "{group_axis}"
    (
        label axisLbl "{lbl_axis_question}" pos:[20,100] width:400 align:#left
        radiobuttons forwardAxisRadio labels:#("X", "Y", "Z") pos:[20,120] default:2 columns:3
    )

    group "{group_frame_range}"
    (
        checkbox useTimelineCB "{cb_use_timeline}" pos:[20,173] width:160 checked:true
        label startLbl "{lbl_start}" pos:[195,173] width:40 align:#left
        spinner startSpn "" pos:[238,171] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "{lbl_end}"     pos:[320,173] width:35 align:#left
        spinner endSpn ""   pos:[355,171] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    group "{group_weights}"
    (
        label weightHintLbl "{lbl_weight_hint}" pos:[20,223] width:420 align:#center
        label lblWX "X" pos:[52,248]  width:20 align:#right
        spinner spnWeightX "" pos:[75,246]  width:75 height:20 type:#integer range:[0,100,0]
        label lblWY "Y" pos:[182,248] width:20 align:#right
        spinner spnWeightY "" pos:[205,246] width:75 height:20 type:#integer range:[0,100,100]
        label lblWZ "Z" pos:[312,248] width:20 align:#right
        spinner spnWeightZ "" pos:[335,246] width:75 height:20 type:#integer range:[0,100,0]
    )

    label statusLabel "" pos:[20,283] width:420 height:16 align:#center
    progressBar damperProgress "" pos:[20,303] width:420 height:10 value:0 color:(color 80 200 120)

    button createHelperBtn "{btn_create_helper}" pos:[20,323]  width:130 height:36
    button applyBtn        "{btn_apply}"         pos:[160,323] width:145 height:36
    button deleteHelperBtn "{btn_delete_helper}" pos:[315,323] width:125 height:36

    on BipedAxisCleanerDialog open do
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

    -- When the forward axis changes, snap weights to match:
    -- the selected forward axis goes to 100, others reset to 0.
    -- This is a convenience default — weights are still fully editable.
    on forwardAxisRadio changed state do
    (
        spnWeightX.value = if state == 1 then 100 else 0
        spnWeightY.value = if state == 2 then 100 else 0
        spnWeightZ.value = if state == 3 then 100 else 0
    )

    on autoDetectBtn pressed do
    (
        local pelvis = BipedAxisCleanerTool.autoDetect()
        if pelvis != undefined then
        (
            BipedAxisCleanerTool.pelvisNode = pelvis
            pelvisEdit.text = pelvis.name
            statusLabel.text = "{msg_detected_prefix}" + pelvis.name
        )
        else
            statusLabel.text = "{msg_no_biped}"
    )

    on pelvisPickBtn picked obj do
    (
        BipedAxisCleanerTool.pelvisNode = obj
        pelvisEdit.text = obj.name
    )

    on pelvisSelBtn pressed do
    (
        if selection.count != 1 then
        (
            messageBox "{err_select_one}" title:"{title}"
            return false
        )
        BipedAxisCleanerTool.pelvisNode = selection[1]
        pelvisEdit.text = selection[1].name
    )

    on createHelperBtn pressed do
    (
        if BipedAxisCleanerTool.pelvisNode == undefined then
        (
            messageBox "{err_assign_pelvis}" title:"{title}"
            return false
        )

        statusLabel.text = "{msg_creating}"
        damperProgress.value = 30
        windows.processPostedMessages()

        local result = BipedAxisCleanerTool.createHelper \\
            BipedAxisCleanerTool.pelvisNode \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if result != undefined then
        (
            select result
            statusLabel.text = result.name + "  {msg_helper_created_sfx}"
        )
        else
            statusLabel.text = "{msg_failed_helper}"

        sleep 0.5
        damperProgress.value = 0
    )

    on applyBtn pressed do
    (
        if BipedAxisCleanerTool.pelvisNode == undefined then
        (
            messageBox "{err_assign_pelvis}" title:"{title}"
            return false
        )

        local helperCheck = getNodeByName (BipedAxisCleanerTool.helperNodeName())
        if helperCheck == undefined then
        (
            messageBox "{err_no_helper}" title:"{title}"
            return false
        )

        local msg = substituteString "{confirm_apply_tpl}" "{{0}}" BipedAxisCleanerTool.pelvisNode.name
        if not (queryBox msg title:"{title}") then return false

        statusLabel.text = "{msg_applying}"
        damperProgress.value = 20
        windows.processPostedMessages()

        local ok = BipedAxisCleanerTool.applyHelperToPelvis \\
            BipedAxisCleanerTool.pelvisNode \\
            spnWeightX.value \\
            spnWeightY.value \\
            spnWeightZ.value \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if ok then
            statusLabel.text = "{msg_done}"
        else
            statusLabel.text = "{msg_failed}"

        sleep 0.5
        damperProgress.value = 0
    )

    on deleteHelperBtn pressed do
    (
        BipedAxisCleanerTool.deleteHelper()
        statusLabel.text = "{msg_helper_deleted}"
    )

    on BipedAxisCleanerDialog close do
    (
        -- leave helper in scene so user can inspect it after closing
    )
)

try (destroyDialog BipedAxisCleanerDialog) catch()
createDialog BipedAxisCleanerDialog
'''

        rt.execute(maxscript)
