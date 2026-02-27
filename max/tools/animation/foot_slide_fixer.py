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

Fix pipeline (per apply):
  Phase 1 — computeFootFix: sample positions, detect plant segments,
             build XY correction array (does NOT write any keys).
  Phase 2 — clampCorrectionsByReach: scale back any correction that
             would place the foot beyond the original 3-D pelvis reach.
             Prevents h_new > d_orig which makes pelvis compensation
             unsolvable and causes the IK pop.
  Phase 3 — applyCorrections: write corrected keys.
  Phase 4 — compensatePelvis: lower pelvis Z to maintain leg length.
             pelvisCorr is smoothed before writing to remove jitter.
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
        lbl_height        = t('tools.foot_slide_fixer.lbl_height')
        group_frame_range = t('tools.foot_slide_fixer.group_frame_range')
        cb_use_timeline   = t('tools.foot_slide_fixer.cb_use_timeline')
        lbl_start         = t('tools.foot_slide_fixer.lbl_start')
        lbl_end           = t('tools.foot_slide_fixer.lbl_end')
        btn_apply         = t('tools.foot_slide_fixer.btn_apply')
        cb_compensate     = t('tools.foot_slide_fixer.cb_compensate')

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
                    if lFoot == undefined and \\
                       ((findString n "l foot") != undefined or \\
                        (findString n "lfoot")  != undefined) then
                        lFoot = obj
                    if rFoot == undefined and \\
                       ((findString n "r foot") != undefined or \\
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
    fn findPlantSegments velArr posArr minZ heightTolerance threshold minPlantFrames =
    (
        local segments  = #()
        local i         = 1
        local n         = velArr.count

        while i <= n do
        (
            if velArr[i] < threshold and (posArr[i].z - minZ) < heightTolerance then
            (
                local segStart = i
                while i <= n and velArr[i] < threshold and (posArr[i].z - minZ) < heightTolerance do i += 1
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
    -- Build per-frame XY correction array.
    --
    -- Pre-blend  (frames BEFORE segment): ramp 0→1 pulling toward
    --   the landing target so heel-strike approach is smooth.
    --
    -- Plant segment: full lock (weight = 1.0) throughout.
    --
    -- Post-blend (frames AFTER segment): fade the CONSTANT offset
    --   that existed at the last plant frame.  Critical difference
    --   from the old approach — we don't pull back toward targetX
    --   each frame (which generated an increasing backward force
    --   fighting the toe-off pivot).  Instead we let the residual
    --   offset dissolve while the foot sweeps forward naturally.
    -- -------------------------------------------------------
    fn buildCorrectionArray posArr plantSegs blendFrames totalFrames =
    (
        local corrections = for i = 1 to totalFrames collect [0.0, 0.0, 0.0]

        for seg in plantSegs do
        (
            local s       = seg[1]
            local e       = seg[2]
            local targetX = posArr[s].x
            local targetY = posArr[s].y

            -- Full correction inside the plant segment
            for i = s to e do
            (
                corrections[i].x += targetX - posArr[i].x
                corrections[i].y += targetY - posArr[i].y
            )

            -- Pre-blend: ramp 0→1 in the swing frames just before the segment
            if s > 1 then
            (
                local preStart = if (s - blendFrames) < 1 then 1 else (s - blendFrames)
                local span     = (s - preStart) as float
                for i = preStart to (s - 1) do
                (
                    local w = (i - preStart + 1) as float / span
                    corrections[i].x += (targetX - posArr[i].x) * w
                    corrections[i].y += (targetY - posArr[i].y) * w
                )
            )

            -- Post-blend: fade the fixed offset from the last plant frame.
            -- offsetX/Y is how far the foot had drifted from targetX/Y by
            -- frame e (i.e. corrections[e]).  Applying this as a fading
            -- constant means the foot starts its swing from the corrected
            -- plant position and glides back to the original curve — no
            -- backward force opposing toe-off.
            if e < totalFrames then
            (
                local offsetX = corrections[e].x
                local offsetY = corrections[e].y
                if (abs offsetX) > 0.001 or (abs offsetY) > 0.001 then
                (
                    local postEnd = if (e + blendFrames) > totalFrames then totalFrames else (e + blendFrames)
                    local span    = (postEnd - e) as float
                    for i = (e + 1) to postEnd do
                    (
                        local w = 1.0 - ((i - e) as float / span)
                        corrections[i].x += offsetX * w
                        corrections[i].y += offsetY * w
                    )
                )
            )
        )

        return corrections
    ),

    -- -------------------------------------------------------
    -- Clamp XY corrections so the corrected foot never exceeds
    -- its original 3-D reach from the pelvis.
    --
    -- Root cause of the IK pop:
    --   h_new > d_orig  →  compensatePelvis has no valid solution
    --   →  pelvisCorr[i] = 0  →  leg IS stretched  →  Biped IK snaps
    --
    -- Fix: scale back any correction so that h_new <= d_orig * safetyFactor.
    -- compensatePelvis then always finds sqrt(d_orig^2 - h_new^2) > 0
    -- and the pelvis drops smoothly.
    -- -------------------------------------------------------
    fn clampCorrectionsByReach corrections footPosArr pelvisPosArr =
    (
        local safetyFactor = 0.97
        for i = 1 to corrections.count do
        (
            if pelvisPosArr.count >= i then
            (
                local corr = corrections[i]
                if (abs corr.x) > 0.001 or (abs corr.y) > 0.001 then
                (
                    local pPos   = pelvisPosArr[i]
                    local fPos   = footPosArr[i]
                    local h_orig = sqrt ((pPos.x - fPos.x)^2 + (pPos.y - fPos.y)^2)
                    local v_orig = pPos.z - fPos.z
                    local d_orig = sqrt (h_orig^2 + v_orig^2)
                    local limit  = d_orig * safetyFactor

                    local newFx  = fPos.x + corr.x
                    local newFy  = fPos.y + corr.y
                    local h_new  = sqrt ((pPos.x - newFx)^2 + (pPos.y - newFy)^2)

                    if h_new > limit then
                    (
                        -- Scale the pelvis→foot vector to exactly 'limit'
                        local vx    = newFx - pPos.x
                        local vy    = newFy - pPos.y
                        local scale = limit / h_new
                        corrections[i] = [(pPos.x + vx * scale) - fPos.x, \\
                                          (pPos.y + vy * scale) - fPos.y, \\
                                          0.0]
                    )
                )
            )
        )
    ),

    -- -------------------------------------------------------
    -- Simple moving-average smoothing (window = 2*halfWin + 1)
    -- -------------------------------------------------------
    fn smoothArray arr halfWin =
    (
        local out = for v in arr collect v
        local n   = arr.count
        for i = 1 to n do
        (
            local lo  = if (i - halfWin) < 1 then 1 else (i - halfWin)
            local hi  = if (i + halfWin) > n then n else (i + halfWin)
            local sum = 0.0
            for j = lo to hi do sum += arr[j]
            out[i] = sum / (hi - lo + 1)
        )
        return out
    ),

    -- -------------------------------------------------------
    -- Apply corrections — XY only, Z left untouched.
    -- Re-reads current pos at each frame so Biped spline
    -- interpolation from earlier keys doesn't accumulate error.
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
                    local p          = posArr[i]
                    local currentPos = footNode.transform.pos
                    local dx = (p.x + corr.x) - currentPos.x
                    local dy = (p.y + corr.y) - currentPos.y
                    move footNode [dx, dy, 0]
                )
            )
        )
        sliderTime = savedTime
    ),

    -- -------------------------------------------------------
    -- Compute foot fix — returns #(segCount, posArr, corrections).
    -- Does NOT apply keys; caller should clamp then applyCorrections.
    -- -------------------------------------------------------
    fn computeFootFix footNode threshold heightTolerance startFrame endFrame =
    (
        local posArr      = this.samplePositions footNode startFrame endFrame
        local totalFrames = endFrame - startFrame + 1
        local velArr      = this.buildVelocityArray posArr
        velArr            = this.medianFilter3 velArr
        local minZ        = posArr[1].z
        for i = 2 to posArr.count do
            if posArr[i].z < minZ then minZ = posArr[i].z
        local segments    = this.findPlantSegments velArr posArr minZ heightTolerance threshold 3
        if segments.count == 0 then return #(0, posArr, #())
        local corrections = this.buildCorrectionArray posArr segments 4 totalFrames
        return #(segments.count, posArr, corrections)
    ),

    -- -------------------------------------------------------
    -- Compensate pelvis Z so corrected feet don't over-extend legs.
    -- Assumes clampCorrectionsByReach has already run so h_new < d_orig
    -- is guaranteed, making sqrt(d_orig^2 - h_new^2) always valid.
    -- pelvisCorr is smoothed before applying to remove jitter.
    -- -------------------------------------------------------
    fn compensatePelvis pelvisNode lFoot rFoot \\
                        origPelvisPos origLPos origRPos \\
                        startFrame endFrame =
    (
        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        local newLPos = if lFoot != undefined then \\
            this.samplePositions lFoot startFrame endFrame else #()
        local newRPos = if rFoot != undefined then \\
            this.samplePositions rFoot startFrame endFrame else #()

        local pelvisCorr = for i = 1 to totalFrames collect 0.0

        for i = 1 to totalFrames do
        (
            local bestAdj = 0.0

            -- Left foot contribution
            if origLPos.count >= i and newLPos.count >= i then
            (
                local cx = newLPos[i].x - origLPos[i].x
                local cy = newLPos[i].y - origLPos[i].y
                if (abs cx) > 0.001 or (abs cy) > 0.001 then
                (
                    local pPos   = origPelvisPos[i]
                    local h_orig = sqrt ((pPos.x - origLPos[i].x)^2 + \\
                                        (pPos.y - origLPos[i].y)^2)
                    local v_orig = pPos.z - origLPos[i].z
                    local d_orig = sqrt (h_orig^2 + v_orig^2)
                    local h_new  = sqrt ((pPos.x - newLPos[i].x)^2 + \\
                                        (pPos.y - newLPos[i].y)^2)
                    if h_new < d_orig then
                    (
                        local v_new = sqrt (d_orig^2 - h_new^2)
                        local adj   = v_new - v_orig
                        if adj < bestAdj then bestAdj = adj
                    )
                )
            )

            -- Right foot contribution
            if origRPos.count >= i and newRPos.count >= i then
            (
                local cx = newRPos[i].x - origRPos[i].x
                local cy = newRPos[i].y - origRPos[i].y
                if (abs cx) > 0.001 or (abs cy) > 0.001 then
                (
                    local pPos   = origPelvisPos[i]
                    local h_orig = sqrt ((pPos.x - origRPos[i].x)^2 + \\
                                        (pPos.y - origRPos[i].y)^2)
                    local v_orig = pPos.z - origRPos[i].z
                    local d_orig = sqrt (h_orig^2 + v_orig^2)
                    local h_new  = sqrt ((pPos.x - newRPos[i].x)^2 + \\
                                        (pPos.y - newRPos[i].y)^2)
                    if h_new < d_orig then
                    (
                        local v_new = sqrt (d_orig^2 - h_new^2)
                        local adj   = v_new - v_orig
                        if adj < bestAdj then bestAdj = adj
                    )
                )
            )

            pelvisCorr[i] = bestAdj
        )

        -- Smooth to remove frame-to-frame jitter in the pelvis correction
        pelvisCorr = this.smoothArray pelvisCorr 2

        with animate on
        (
            for i = 1 to totalFrames do
            (
                if (abs pelvisCorr[i]) > 0.001 then
                (
                    sliderTime = startFrame + i - 1
                    local curPos = pelvisNode.transform.pos
                    move pelvisNode [0, 0, (origPelvisPos[i].z + pelvisCorr[i]) - curPos.z]
                )
            )
        )
        sliderTime = savedTime
    )
)

FootSlideFixerTool = FootSlideFixerStruct()

-- ============================================================
-- Dialog
-- ============================================================
rollout FootSlideFixerDialog "{title}" width:460 height:325
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
        label heightLbl "{lbl_height}" pos:[20,132] width:130 align:#left
        spinner heightSpn "" pos:[155,130] width:70 height:20 type:#float range:[0,100,5.0]
    )

    group "{group_frame_range}"
    (
        checkbox useTimelineCB "{cb_use_timeline}" pos:[20,182] width:160 checked:true
        label startLbl "{lbl_start}" pos:[195,182] width:40 align:#left
        spinner startSpn "" pos:[238,180] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "{lbl_end}"     pos:[320,182] width:35 align:#left
        spinner endSpn ""   pos:[355,180] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
    )

    checkbox compensatePelvisCB "{cb_compensate}" pos:[20,214] width:420 checked:true

    label statusLabel "" pos:[20,238] width:420 height:16 align:#center
    progressBar fixProgress "" pos:[20,258] width:420 height:10 value:0 color:(color 80 200 120)

    button applyBtn "{btn_apply}" pos:[20,278] width:420 height:36

    on FootSlideFixerDialog open do
    (
        startSpn.value = animationRange.start.frame as integer
        endSpn.value   = animationRange.end.frame as integer

        -- Pre-populate from Biped Axis Cleaner if the user already picked a pelvis
        try
        (
            if BipedAxisCleanerTool != undefined and \\
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
        local feet  = FootSlideFixerTool.getFootNodes FootSlideFixerTool.bipedNode
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

        local startF          = startSpn.value
        local endF            = endSpn.value
        local thresh          = velocitySlider.value
        local heightTolerance = heightSpn.value
        local lCount          = 0
        local rCount          = 0

        -- Always pre-sample pelvis positions — needed for reach clamping
        -- even when pelvis compensation is disabled.
        local pelvisNode    = undefined
        local origPelvisPos = #()
        local origLPos      = #()
        local origRPos      = #()

        try ( pelvisNode = biped.getNode FootSlideFixerTool.bipedNode #pelvis ) catch()
        if pelvisNode == undefined then pelvisNode = FootSlideFixerTool.bipedNode
        if pelvisNode != undefined then
        (
            origPelvisPos = FootSlideFixerTool.samplePositions pelvisNode startF endF
            if lFoot != undefined then origLPos = FootSlideFixerTool.samplePositions lFoot startF endF
            if rFoot != undefined then origRPos = FootSlideFixerTool.samplePositions rFoot startF endF
        )

        -- Phase 1: compute corrections (no keys written yet)
        local lResult = #(0, #(), #())
        local rResult = #(0, #(), #())

        if lFoot != undefined then
            lResult = FootSlideFixerTool.computeFootFix lFoot thresh heightTolerance startF endF
        fixProgress.value = 30
        windows.processPostedMessages()

        if rFoot != undefined then
            rResult = FootSlideFixerTool.computeFootFix rFoot thresh heightTolerance startF endF
        fixProgress.value = 50
        windows.processPostedMessages()

        lCount = lResult[1]
        rCount = rResult[1]

        -- Phase 2: clamp corrections so no foot goes beyond its original
        --          3-D pelvis reach (prevents IK pop / overstretching)
        if origPelvisPos.count > 0 then
        (
            if lResult[3].count > 0 then
                FootSlideFixerTool.clampCorrectionsByReach lResult[3] lResult[2] origPelvisPos
            if rResult[3].count > 0 then
                FootSlideFixerTool.clampCorrectionsByReach rResult[3] rResult[2] origPelvisPos
        )

        -- Phase 3: apply clamped corrections
        if lResult[3].count > 0 then
            FootSlideFixerTool.applyCorrections lFoot lResult[2] lResult[3] startF
        fixProgress.value = 70
        windows.processPostedMessages()

        if rResult[3].count > 0 then
            FootSlideFixerTool.applyCorrections rFoot rResult[2] rResult[3] startF
        fixProgress.value = 85
        windows.processPostedMessages()

        -- Phase 4: pelvis compensation (optional — checkbox)
        if compensatePelvisCB.checked and pelvisNode != undefined and origPelvisPos.count > 0 then
        (
            FootSlideFixerTool.compensatePelvis pelvisNode lFoot rFoot \\
                origPelvisPos origLPos origRPos startF endF
        )
        fixProgress.value = 100
        windows.processPostedMessages()

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
