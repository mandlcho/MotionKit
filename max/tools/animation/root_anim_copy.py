"""
Root Animation Copy Tool for MotionKit
Copies animation from Biped root (CS pelvis) to a custom Root bone

This tool handles:
- Copying position and rotation from Biped pelvis to custom root bone
- Selective axis copying (X, Y, Z position + Z rotation)
- Frame range specification
- Relative height offset calculation
- Execute animation setup (for finisher animations)
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Root Anim Copy] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Root Animation Copy"


def execute(control=None, event=None):
    """Execute the Root Animation Copy tool"""
    if not pymxs or not rt:
        print("[Root Anim Copy] ERROR: Not running in 3ds Max")
        return

    try:
        # Create and show the dialog using MaxScript
        dialog = RootAnimCopyDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open Root Animation Copy: {str(e)}")
        rt.messageBox(
            f"Failed to open Root Animation Copy:\n{str(e)}",
            title="MotionKit Error"
        )


class RootAnimCopyDialog:
    """Root Animation Copy dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        """Show the Root Animation Copy dialog using MaxScript"""

        # Get all translations
        title = t('tools.root_anim_copy.title')
        description = t('tools.root_anim_copy.description')
        position_group = t('tools.root_anim_copy.position_group')
        rotation_group = t('tools.root_anim_copy.rotation_group')
        x_axis = t('tools.root_anim_copy.x_axis')
        y_axis = t('tools.root_anim_copy.y_axis')
        z_axis = t('tools.root_anim_copy.z_axis')
        z_rotation = t('tools.root_anim_copy.z_rotation')
        frame_range_group = t('tools.root_anim_copy.frame_range_group')
        use_timeline = t('tools.root_anim_copy.use_timeline')
        start = t('tools.root_anim_copy.start')
        end = t('tools.root_anim_copy.end')
        height_offset_group = t('tools.root_anim_copy.height_offset_group')
        apply_offset = t('tools.root_anim_copy.apply_offset')
        offset = t('tools.root_anim_copy.offset')
        calc_from_selection = t('tools.root_anim_copy.calc_from_selection')
        copy_button = t('tools.root_anim_copy.copy_button')
        pick = t('common.pick')

        # Error messages
        error_root_not_found = t('tools.root_anim_copy.error_root_not_found')
        error_cs_not_found = t('tools.root_anim_copy.error_cs_not_found')
        error_invalid_frames = t('tools.root_anim_copy.error_invalid_frames')
        error_frame_range = t('tools.root_anim_copy.error_frame_range')
        error_select_2_objects = t('tools.root_anim_copy.error_select_2_objects')
        error_need_biped_and_root = t('tools.root_anim_copy.error_need_biped_and_root')
        success_copied = t('tools.root_anim_copy.success_copied')
        cancelled = t('tools.root_anim_copy.cancelled')
        height_calculated = t('tools.root_anim_copy.height_calculated')

        maxscript = f'''
-- ============================================
-- MotionKit Root Animation Copy Tool
-- ============================================

rollout MotionKitRootAnimCopy "{title}" width:520 height:285
(
    -- Title with margins
    label titleLabel "{description}" \\
        pos:[10,6] width:500 align:#center

    -- Position Group
    groupBox positionGroup "{position_group}" pos:[10,26] width:245 height:48
    checkbox xAxisPos "{x_axis}" pos:[20,44] checked:true across:3
    checkbox yAxisPos "{y_axis}" pos:[95,44] checked:true
    checkbox zAxisPos "{z_axis}" pos:[170,44] checked:true

    -- Rotation Group
    groupBox rotationGroup "{rotation_group}" pos:[265,26] width:245 height:48
    checkbox zAxisRot "{z_rotation}" pos:[275,44] checked:false

    -- Frame Range Group
    groupBox frameRangeGroup "{frame_range_group}" pos:[10,82] width:500 height:73
    checkbox useTimelineRange "{use_timeline}" pos:[20,98] checked:true

    label startLabel "{start}" pos:[20,120] width:40
    edittext frameStartEdit "" pos:[65,118] width:90 height:18 enabled:false labelOnTop:false
    button pickStartFrame "{pick}" pos:[160,118] width:50 height:18 enabled:false

    label endLabel "{end}" pos:[270,120] width:40
    edittext frameEndEdit "" pos:[310,118] width:90 height:18 enabled:false labelOnTop:false
    button pickEndFrame "{pick}" pos:[405,118] width:50 height:18 enabled:false

    -- Height Offset Group
    groupBox heightOffsetGroup "{height_offset_group}" pos:[10,163] width:500 height:73
    checkbox useHeightOffset "{apply_offset}" pos:[20,179] checked:false

    label offsetLabel "{offset}" pos:[20,201] width:45
    spinner heightOffsetSpn "" pos:[70,199] width:120 height:18 \\
        range:[-1000,1000,0] type:#float scale:0.1 enabled:false
    button calcHeightOffset "{calc_from_selection}" pos:[200,199] width:300 height:18 enabled:false

    -- Main copy button
    button copyRootAnim "{copy_button}" pos:[10,245] width:500 height:35

    -- Initialize with current timeline
    on MotionKitRootAnimCopy open do
    (
        -- Set timeline values
        local startFrame = animationRange.start.frame as integer
        local endFrame = animationRange.end.frame as integer
        frameStartEdit.text = startFrame as string
        frameEndEdit.text = endFrame as string
    )

    -- Toggle timeline range
    on useTimelineRange changed state do
    (
        -- Enable/disable manual frame inputs
        frameStartEdit.enabled = not state
        frameEndEdit.enabled = not state
        pickStartFrame.enabled = not state
        pickEndFrame.enabled = not state

        -- If toggled on, update with current timeline
        if state then
        (
            local startFrame = animationRange.start.frame as integer
            local endFrame = animationRange.end.frame as integer
            frameStartEdit.text = startFrame as string
            frameEndEdit.text = endFrame as string
        )
    )

    -- Pick start frame from current slider position
    on pickStartFrame pressed do
    (
        local currentFrame = sliderTime.frame as integer
        frameStartEdit.text = currentFrame as string
    )

    -- Pick end frame from current slider position
    on pickEndFrame pressed do
    (
        local currentFrame = sliderTime.frame as integer
        frameEndEdit.text = currentFrame as string
    )

    -- Toggle height offset
    on useHeightOffset changed state do
    (
        heightOffsetSpn.enabled = state
        calcHeightOffset.enabled = state
    )

    -- Calculate height offset from selection
    on calcHeightOffset pressed do
    (
        if selection.count != 2 then
        (
            messageBox "{error_select_2_objects}" \\
                title:"Height Offset"
            return undefined
        )

        local csNode = undefined
        local rootNode = undefined

        -- Determine which is which
        for obj in selection do
        (
            if classof obj == Biped_Object then
                csNode = obj
            else
                rootNode = obj
        )

        if csNode == undefined or rootNode == undefined then
        (
            messageBox "{error_need_biped_and_root}" \\
                title:"Height Offset"
            return undefined
        )

        -- Calculate height difference
        local heightDiff = csNode.pos.z - rootNode.pos.z
        heightOffsetSpn.value = heightDiff

        local msg = substituteString "{height_calculated}" "{{0}}" (heightDiff as string)
        msg = substituteString msg "{{1}}" (csNode.pos.z as string)
        msg = substituteString msg "{{2}}" (rootNode.pos.z as string)
        messageBox msg title:"Height Offset"
    )

    -- Main copy function
    on copyRootAnim pressed do
    (
        -- Find CS root (Biped pelvis) and custom root bone
        local csRoot = undefined
        local rootBone = undefined

        -- Find Biped in scene
        for obj in objects do
        (
            if classof obj == Biped_Object then
            (
                try
                (
                    csRoot = biped.getNode obj 13  -- Node 13 is pelvis
                    if csRoot != undefined then exit
                )
                catch()
            )
        )

        -- Find root bone
        try
        (
            rootBone = $root
        )
        catch
        (
            messageBox "{error_root_not_found}" \\
                title:"Root Anim Copy"
            return undefined
        )

        if csRoot == undefined then
        (
            messageBox "{error_cs_not_found}" \\
                title:"Root Anim Copy"
            return undefined
        )

        -- Get frame range
        local startFrameValue = frameStartEdit.text as integer
        local endFrameValue = frameEndEdit.text as integer

        if startFrameValue == undefined or endFrameValue == undefined then
        (
            messageBox "{error_invalid_frames}" title:"Root Anim Copy"
            return undefined
        )

        local startFrame = startFrameValue as time
        local endFrame = endFrameValue as time

        -- Validate frame range
        if endFrame < startFrame then
        (
            messageBox "{error_frame_range}" title:"Root Anim Copy"
            return undefined
        )

        -- Get options
        local copyX = xAxisPos.checked
        local copyY = yAxisPos.checked
        local copyZ = zAxisPos.checked
        local copyRotZ = zAxisRot.checked
        local applyHeightOffset = useHeightOffset.checked
        local heightOffsetValue = heightOffsetSpn.value

        -- Reset root bone controllers
        with animate off
        (
            rootBone.controller = prs()
            rootBone.controller[1].controller = Position_XYZ()
            rootBone.controller[2].controller = Euler_XYZ()
            rootBone.controller[3].controller = ScaleXYZ()

            -- Clear existing keys
            deleteKeys rootBone.controller[1][1].controller #allKeys  -- X pos
            deleteKeys rootBone.controller[1][2].controller #allKeys  -- Y pos
            deleteKeys rootBone.controller[2].controller #allKeys      -- Rotation
        )

        -- Copy animation frame by frame
        local frameCount = 0
        slidertime = startFrame

        for t = startFrame to endFrame do
        (
            at time t
            (
                -- Get CS root transform at this frame
                local csPos = csRoot.transform.pos
                local csRot = csRoot.transform.rotation

                -- Calculate new position
                local newPos = rootBone.pos

                if copyX then newPos.x = csPos.x
                if copyY then newPos.y = csPos.y
                if copyZ then
                (
                    if applyHeightOffset then
                        newPos.z = csPos.z - heightOffsetValue
                    else
                        newPos.z = csPos.z
                )

                -- Apply position
                with animate on
                (
                    rootBone.pos = newPos

                    -- Apply rotation if enabled
                    if copyRotZ then
                    (
                        local eulerRot = csRot as eulerAngles
                        rootBone.rotation = eulerAngles 0 0 eulerRot.z
                    )
                    else
                    (
                        -- Clear rotation
                        rootBone.controller[2].controller.value = matrix3 1
                    )
                )

                frameCount += 1
            )

            -- Allow ESC to cancel
            if keyboard.escPressed do
            (
                local cancelMsg = substituteString "{cancelled}" "{{0}}" (t as string)
                messageBox cancelMsg title:"Root Anim Copy"
                return undefined
            )
        )

        -- Handle axis zeroing if unchecked
        if not copyX then
        (
            for t = startFrame to endFrame do
            (
                at time t
                (
                    with animate on
                        rootBone.pos *= [0,1,1]  -- Zero X
                )
            )
        )

        if not copyY then
        (
            for t = startFrame to endFrame do
            (
                at time t
                (
                    with animate on
                        rootBone.pos *= [1,0,1]  -- Zero Y
                )
            )
        )

        slidertime = startFrame
        local successMsg = substituteString "{success_copied}" "{{0}}" (frameCount as string)
        messageBox successMsg title:"Root Anim Copy"
    )
)

-- Create and show dialog
try (destroyDialog MotionKitRootAnimCopy) catch()
createDialog MotionKitRootAnimCopy
'''

        # Execute the MaxScript
        rt.execute(maxscript)


# Global callback functions accessible from MaxScript
def _find_cs_root():
    """Find the CS root (Biped pelvis) in the scene"""
    for obj in rt.objects:
        if rt.classof(obj) == rt.Biped_Object:
            try:
                cs_root = rt.biped.getNode(obj, 13)  # Node 13 is pelvis
                if cs_root:
                    return cs_root
            except:
                pass
    return None


def _find_root_bone():
    """Find the custom root bone in the scene"""
    try:
        return rt.getNodeByName("root")
    except:
        return None
