"""
Foot Slide Fixer Tool for MotionKit

Automatically detects and corrects foot sliding in Biped animations
by locking feet during detected plant phases.

Workflow:
  1. Auto-detect or manually assign a Biped node — the tool finds both
     feet automatically via the Biped API.
  2. Adjust velocity threshold to tune plant phase detection.
     Lower = stricter (only very slow feet treated as planted).
     Higher = looser (more frames treated as planted).
  3. Click Apply — XY corrections are written back to the foot bones
     with smooth blend transitions at the edge of each plant phase.
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Foot Slide Fixer] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Foot Slide Fixer"


def execute(control=None, event=None):
    if not pymxs or not rt:
        print("[Foot Slide Fixer] ERROR: Not running in 3ds Max")
        return
    try:
        FootSlideFixerDialog().show()
    except Exception as e:
        logger.error(f"Failed to open Foot Slide Fixer: {str(e)}")
        rt.messageBox(f"Failed to open Foot Slide Fixer:\n{str(e)}", title="MotionKit Error")


class FootSlideFixerDialog:

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        start_frame = int(rt.animationRange.start.frame)
        end_frame   = int(rt.animationRange.end.frame)

        # UI strings
        title             = t('tools.foot_slide_fixer.title')
        group_source      = t('tools.foot_slide_fixer.group_source')
        btn_auto_detect   = t('tools.foot_slide_fixer.btn_auto_detect')
        lbl_biped         = t('tools.foot_slide_fixer.lbl_biped')
        btn_pick          = t('common.pick')
        btn_sel           = t('tools.foot_slide_fixer.btn_sel')
        group_detection   = t('tools.foot_slide_fixer.group_detection')
        lbl_threshold     = t('tools.foot_slide_fixer.lbl_threshold')
        group_frame_range = t('tools.foot_slide_fixer.group_frame_range')
        cb_use_timeline   = t('tools.foot_slide_fixer.cb_use_timeline')
        lbl_start         = t('tools.foot_slide_fixer.lbl_start')
        lbl_end           = t('tools.foot_slide_fixer.lbl_end')
        btn_apply         = t('tools.foot_slide_fixer.btn_apply')

        # Status / error strings
        err_no_biped      = t('tools.foot_slide_fixer.err_no_biped')
        err_figure_mode   = t('tools.foot_slide_fixer.err_figure_mode')
        err_no_feet       = t('tools.foot_slide_fixer.err_no_feet')
        msg_detected      = t('tools.foot_slide_fixer.msg_detected')
        msg_no_detect     = t('tools.foot_slide_fixer.msg_no_detect')
        msg_fixing        = t('tools.foot_slide_fixer.msg_fixing')
        msg_done_tpl      = t('tools.foot_slide_fixer.msg_done')
        msg_no_segments   = t('tools.foot_slide_fixer.msg_no_segments')
        msg_failed        = t('tools.foot_slide_fixer.msg_failed')

        maxscript = f'''
-- ============================================
-- MotionKit Foot Slide Fixer
-- ============================================

global FootSlideFixerTool

struct FootSlideFixerStruct
(
    bipedNode = undefined,

    -- -------------------------------------------------------
    -- Detection — find any Biped_Object in the scene
    -- -------------------------------------------------------
    fn autoDetect =
    (
        for obj in objects do
            if classOf obj == Biped_Object then return obj
        return undefined
    ),

    -- -------------------------------------------------------
    -- Get left and right foot nodes from any biped node
    -- Falls back to name search if the biped API fails
    -- -------------------------------------------------------
    fn getFootNodes bipObj =
    (
        local lFoot = undefined
        local rFoot = undefined

        try
        (
            lFoot = biped.getNode bipObj #lleg link:3
            rFoot = biped.getNode bipObj #rleg link:3
        )
        catch()

        -- Fallback: name search
        if lFoot == undefined or rFoot == undefined then
        (
            for obj in objects do
            (
                if classOf obj == Biped_Object then
                (
                    local n = toLower obj.name
                    if lFoot == undefined and \
                       ((findString n "l foot") != undefined or \
                        (findString n "lfoot")  != undefined) then
                        lFoot = obj
                    if rFoot == undefined and \
                       ((findString n "r foot") != undefined or \
                        (findString n "rfoot")  != undefined) then
                        rFoot = obj
                )
            )
        )

        return #(lFoot, rFoot)
    ),

    -- -------------------------------------------------------
    -- Sample world positions frame by frame
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
    -- 3D velocity array — index 1 is always 0.0 (no predecessor)
    -- Using full 3D distance: a planted foot has no XY *or* Z movement.
    -- Correction is still XY-only; Z is only used here for detection.
    -- -------------------------------------------------------
    fn buildVelocityArray posArr =
    (
        local vel = #(0.0)
        for i = 2 to posArr.count do
        (
            local dx = posArr[i].x - posArr[i-1].x
            local dy = posArr[i].y - posArr[i-1].y
            local dz = posArr[i].z - posArr[i-1].z
            append vel (sqrt (dx*dx + dy*dy + dz*dz))
        )
        return vel
    ),

    -- -------------------------------------------------------
    -- 3-frame median filter — suppresses single-frame spikes
    -- -------------------------------------------------------
    fn medianFilter3 arr =
    (
        local out = for v in arr collect v
        for i = 2 to (arr.count - 1) do
        (
            local vals = #(arr[i-1], arr[i], arr[i+1])
            sort vals
            out[i] = vals[2]
        )
        return out
    ),

    -- -------------------------------------------------------
    -- Detect contiguous plant segments
    -- -------------------------------------------------------
    fn findPlantSegments velArr threshold minPlantFrames =
    (
        local segments  = #()
        local i         = 1
        local n         = velArr.count

        while i <= n do
        (
            if velArr[i] < threshold then
            (
                local segStart = i
                while i <= n and velArr[i] < threshold do i += 1
                local segEnd = i - 1
                if (segEnd - segStart + 1) >= minPlantFrames then
                    append segments #(segStart, segEnd)
            )
            else
                i += 1
        )

        return segments
    ),

    -- -------------------------------------------------------
    -- Build per-frame XY correction array
    -- Blends smoothly at segment edges; segments at the
    -- start/end of the range use full weight immediately
    -- -------------------------------------------------------
    fn buildCorrectionArray posArr plantSegs blendFrames totalFrames =
    (
        local corrections = for i = 1 to totalFrames collect [0.0, 0.0, 0.0]

        for seg in plantSegs do
        (
            local s         = seg[1]
            local e         = seg[2]
            local targetX   = posArr[s].x
            local targetY   = posArr[s].y

            for i = s to e do
            (
                local dx = targetX - posArr[i].x
                local dy = targetY - posArr[i].y

                -- Ramp-in: full weight if segment starts at frame 1
                local blendIn = if s == 1 then 1.0 \
                    else if (i - s) < blendFrames then ((i - s) as float / blendFrames) \
                    else 1.0

                -- Ramp-out: full weight if segment ends at last frame
                local blendOut = if e == totalFrames then 1.0 \
                    else if (e - i) < blendFrames then ((e - i) as float / blendFrames) \
                    else 1.0

                local w = blendIn * blendOut

                -- Accumulate (handles overlapping blend zones from adjacent segments)
                corrections[i].x += dx * w
                corrections[i].y += dy * w
            )
        )

        return corrections
    ),

    -- -------------------------------------------------------
    -- Apply corrections — XY only, Z left untouched
    -- Uses pre-sampled positions to avoid ordering issues
    -- -------------------------------------------------------
    fn applyCorrections footNode posArr corrections startFrame =
    (
        local savedTime = sliderTime
        with animate on
        (
            for i = 1 to corrections.count do
            (
                local corr = corrections[i]
                if (abs corr.x) > 0.001 or (abs corr.y) > 0.001 then
                (
                    sliderTime = startFrame + i - 1
                    local p = posArr[i]
                    footNode.pos = [p.x + corr.x, p.y + corr.y, p.z]
                )
            )
        )
        sliderTime = savedTime
    ),

    -- -------------------------------------------------------
    -- Fix a single foot — returns number of plant segments found
    -- -------------------------------------------------------
    fn fixFoot footNode threshold startFrame endFrame =
    (
        local posArr      = this.samplePositions footNode startFrame endFrame
        local totalFrames = endFrame - startFrame + 1
        local velArr      = this.buildVelocityArray posArr
        velArr            = this.medianFilter3 velArr
        local segments    = this.findPlantSegments velArr threshold 3
        if segments.count == 0 then return 0

        local corrections = this.buildCorrectionArray posArr segments 4 totalFrames
        this.applyCorrections footNode posArr corrections startFrame
        return segments.count
    )
)

FootSlideFixerTool = FootSlideFixerStruct()

-- ============================================================
-- Dialog
-- ============================================================
rollout FootSlideFixerDialog "{title}" width:460 height:275
(
    group "{group_source}"
    (
        button autoDetectBtn "{btn_auto_detect}" pos:[20,22] width:410 height:24
        label bipedLbl "{lbl_biped}" pos:[20,57]  width:55 align:#left
        edittext bipedEdit ""        pos:[78,54]  width:200 height:20 readOnly:true
        pickbutton bipedPickBtn "{btn_pick}" pos:[285,54] width:60 height:20
        button bipedSelBtn "{btn_sel}"       pos:[352,54] width:68 height:20
    )

    group "{group_detection}"
    (
        label thresholdLbl "{lbl_threshold}" pos:[20,108] width:130 align:#left
        slider velocitySlider "" pos:[155,106] width:215 height:22 range:[0,20,1.5] type:#float ticks:10
        label velValLbl "1.5" pos:[378,108] width:45 align:#left
    )

    group "{group_frame_range}"
    (
        checkbox useTimelineCB "{cb_use_timeline}" pos:[20,156] width:160 checked:true
        label startLbl "{lbl_start}" pos:[195,156] width:40 align:#left
        spinner startSpn "" pos:[238,154] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "{lbl_end}"     pos:[320,156] width:35 align:#left
        spinner endSpn ""   pos:[355,154] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    label statusLabel "" pos:[20,188] width:420 height:16 align:#center
    progressBar fixProgress "" pos:[20,208] width:420 height:10 value:0 color:(color 80 200 120)

    button applyBtn "{btn_apply}" pos:[20,228] width:420 height:36

    on FootSlideFixerDialog open do
    (
        startSpn.value = animationRange.start.frame as integer
        endSpn.value   = animationRange.end.frame as integer

        -- Pre-populate from Biped Axis Cleaner if the user already picked a pelvis
        try
        (
            if BipedAxisCleanerTool != undefined and \
               BipedAxisCleanerTool.pelvisNode != undefined then
            (
                FootSlideFixerTool.bipedNode = BipedAxisCleanerTool.pelvisNode
                bipedEdit.text = BipedAxisCleanerTool.pelvisNode.name
                statusLabel.text = "{msg_detected}" + BipedAxisCleanerTool.pelvisNode.name
            )
        )
        catch()
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

    on velocitySlider changed val do
        velValLbl.text = (formattedPrint val format:".2f")

    on autoDetectBtn pressed do
    (
        local node = FootSlideFixerTool.autoDetect()
        if node != undefined then
        (
            FootSlideFixerTool.bipedNode = node
            bipedEdit.text = node.name
            statusLabel.text = "{msg_detected}" + node.name
        )
        else
            statusLabel.text = "{msg_no_detect}"
    )

    on bipedPickBtn picked obj do
    (
        FootSlideFixerTool.bipedNode = obj
        bipedEdit.text = obj.name
        statusLabel.text = "{msg_detected}" + obj.name
    )

    on bipedSelBtn pressed do
    (
        if selection.count != 1 then
        (
            messageBox "Select exactly one object first." title:"{title}"
            return false
        )
        FootSlideFixerTool.bipedNode = selection[1]
        bipedEdit.text = selection[1].name
        statusLabel.text = "{msg_detected}" + selection[1].name
    )

    on applyBtn pressed do
    (
        if FootSlideFixerTool.bipedNode == undefined then
        (
            messageBox "{err_no_biped}" title:"{title}"
            return false
        )

        -- Guard against figure mode
        try
        (
            if biped.getFigureMode FootSlideFixerTool.bipedNode then
            (
                messageBox "{err_figure_mode}" title:"{title}"
                return false
            )
        )
        catch()

        -- Get foot nodes
        local feet = FootSlideFixerTool.getFootNodes FootSlideFixerTool.bipedNode
        local lFoot = feet[1]
        local rFoot = feet[2]

        if lFoot == undefined and rFoot == undefined then
        (
            messageBox "{err_no_feet}" title:"{title}"
            return false
        )

        statusLabel.text = "{msg_fixing}"
        fixProgress.value = 10
        windows.processPostedMessages()

        local startF = startSpn.value
        local endF   = endSpn.value
        local thresh = velocitySlider.value
        local lCount = 0
        local rCount = 0

        if lFoot != undefined then
        (
            lCount = FootSlideFixerTool.fixFoot lFoot thresh startF endF
            fixProgress.value = 55
            windows.processPostedMessages()
        )

        if rFoot != undefined then
        (
            rCount = FootSlideFixerTool.fixFoot rFoot thresh startF endF
            fixProgress.value = 100
            windows.processPostedMessages()
        )

        if (lCount + rCount) == 0 then
            statusLabel.text = "{msg_no_segments}"
        else
        (
            local doneMsg = substituteString "{msg_done_tpl}" "{{0}}" (lCount as string)
            doneMsg = substituteString doneMsg "{{1}}" (rCount as string)
            statusLabel.text = doneMsg
        )

        sleep 0.5
        fixProgress.value = 0
    )

    on FootSlideFixerDialog close do ()
)

try (destroyDialog FootSlideFixerDialog) catch()
createDialog FootSlideFixerDialog
'''

        rt.execute(maxscript)
