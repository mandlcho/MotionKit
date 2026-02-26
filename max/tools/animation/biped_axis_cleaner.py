"""
Biped Axis Cleaner Tool for MotionKit

Workflow:
  1. "Create Helper" — bakes the pelvis world position to a Dummy helper,
     then replaces the forward axis with two linear keys (first and last frame).
     The other two axes retain all original keys; only the chosen forward axis is flattened.
  2. Inspect the helper in the viewport.
  3. "Apply to Pelvis" — bakes the helper's modified position back to the pelvis
     using the Amount slider to blend between original and fully linearized.

  On first Apply the original pelvis positions are locked in a hidden backup dummy
  so the Amount slider is non-destructive across multiple applies.
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
        group_amount        = t('tools.biped_axis_cleaner.group_amount')
        lbl_amount          = t('tools.biped_axis_cleaner.lbl_amount')
        lbl_amount_help     = t('tools.biped_axis_cleaner.lbl_amount_help')
        group_frame_range   = t('tools.biped_axis_cleaner.group_frame_range')
        cb_use_timeline     = t('tools.biped_axis_cleaner.cb_use_timeline')
        lbl_start           = t('tools.biped_axis_cleaner.lbl_start')
        lbl_end             = t('tools.biped_axis_cleaner.lbl_end')
        btn_create_helper   = t('tools.biped_axis_cleaner.btn_create_helper')
        btn_apply           = t('tools.biped_axis_cleaner.btn_apply')
        btn_delete_helper   = t('tools.biped_axis_cleaner.btn_delete_helper')

        # Error / status strings
        err_assign_pelvis       = t('tools.biped_axis_cleaner.err_assign_pelvis')
        err_no_helper           = t('tools.biped_axis_cleaner.err_no_helper')
        err_select_one          = t('tools.biped_axis_cleaner.err_select_one')
        confirm_apply_tpl       = t('tools.biped_axis_cleaner.confirm_apply')
        msg_detected_prefix     = t('tools.biped_axis_cleaner.msg_detected_prefix')
        msg_no_biped            = t('tools.biped_axis_cleaner.msg_no_biped')
        msg_creating            = t('tools.biped_axis_cleaner.msg_creating')
        msg_helper_created_sfx  = t('tools.biped_axis_cleaner.msg_helper_created_sfx')
        msg_failed_helper       = t('tools.biped_axis_cleaner.msg_failed_helper')
        msg_applying            = t('tools.biped_axis_cleaner.msg_applying')
        msg_done_tpl            = t('tools.biped_axis_cleaner.msg_done')
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
    -- Helper — visible dummy with linearized forward axis
    -- -------------------------------------------------------
    fn helperNodeName = "BipedAxisCleaner_Helper",

    fn createHelper pelvisNode axisIndex startFrame endFrame =
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

        -- Get forward value at first and last frame
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
        -- The two non-forward axes come straight from the original positions.
        -- The forward axis is replaced with a linear interpolation between
        -- the first and last frame values.
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

BipedAxisCleanerTool = BipedAxisCleanerStruct()

-- ============================================================
-- Dialog
-- ============================================================
rollout BipedAxisCleanerDialog "{title}" width:460 height:355
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

    group "{group_amount}"
    (
        label amountLbl "{lbl_amount}" pos:[20,165] width:60 align:#left
        slider amountSlider ""         pos:[85,163] width:285 height:22 range:[0,100,100] type:#integer ticks:10
        label amountValLbl "100%"      pos:[378,165] width:45 align:#left
        label helpTxt "{lbl_amount_help}" \\
            pos:[20,189] width:420 align:#left
    )

    group "{group_frame_range}"
    (
        checkbox useTimelineCB "{cb_use_timeline}" pos:[20,227] width:160 checked:true
        label startLbl "{lbl_start}" pos:[195,227] width:40 align:#left
        spinner startSpn "" pos:[238,225] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "{lbl_end}"     pos:[320,227] width:35 align:#left
        spinner endSpn ""   pos:[355,225] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    label statusLabel "" pos:[20,268] width:420 height:16 align:#center
    progressBar damperProgress "" pos:[20,288] width:420 height:10 value:0 color:(color 80 200 120)

    button createHelperBtn "{btn_create_helper}" pos:[20,308]  width:130 height:36
    button applyBtn        "{btn_apply}"         pos:[160,308] width:145 height:36
    button deleteHelperBtn "{btn_delete_helper}" pos:[315,308] width:125 height:36

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

    on amountSlider changed val do
        amountValLbl.text = val as string + "%"

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
            forwardAxisRadio.state \\
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

        local msg = substituteString "{confirm_apply_tpl}" "{{0}}" (amountSlider.value as string)
        msg = substituteString msg "{{1}}" BipedAxisCleanerTool.pelvisNode.name
        if not (queryBox msg title:"{title}") then return false

        statusLabel.text = "{msg_applying}"
        damperProgress.value = 20
        windows.processPostedMessages()

        local ok = BipedAxisCleanerTool.applyHelperToPelvis \\
            BipedAxisCleanerTool.pelvisNode \\
            forwardAxisRadio.state \\
            amountSlider.value \\
            startSpn.value \\
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if ok then
        (
            local doneMsg = substituteString "{msg_done_tpl}" "{{0}}" (amountSlider.value as string)
            statusLabel.text = doneMsg
        )
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
