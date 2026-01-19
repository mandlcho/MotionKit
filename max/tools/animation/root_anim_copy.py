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

        maxscript = f'''
-- ============================================
-- MotionKit Root Animation Copy Tool
-- ============================================

rollout MotionKitRootAnimCopy "Root Animation Copy - MotionKit v{self.version}" width:520 height:285
(
    -- Title with margins
    label titleLabel "Copy animation from Biped Root (CS Pelvis) to custom Root bone" \\
        pos:[10,6] width:500 align:#center

    -- Position Group
    groupBox positionGroup "Position Copy Options" pos:[10,26] width:245 height:48
    checkbox xAxisPos "X Axis" pos:[20,44] checked:true across:3
    checkbox yAxisPos "Y Axis" pos:[95,44] checked:true
    checkbox zAxisPos "Z Axis" pos:[170,44] checked:true

    -- Rotation Group
    groupBox rotationGroup "Rotation Copy Options" pos:[265,26] width:245 height:48
    checkbox zAxisRot "Z Rotation" pos:[275,44] checked:false

    -- Frame Range Group
    groupBox frameRangeGroup "Frame Range" pos:[10,82] width:500 height:73
    checkbox useTimelineRange "Use Current Timeline" pos:[20,98] checked:true

    label startLabel "Start:" pos:[20,120] width:40
    edittext frameStartEdit "" pos:[65,118] width:90 height:18 enabled:false
    button pickStartFrame "Pick" pos:[160,118] width:50 height:18 enabled:false

    label endLabel "End:" pos:[270,120] width:40
    edittext frameEndEdit "" pos:[310,118] width:90 height:18 enabled:false
    button pickEndFrame "Pick" pos:[405,118] width:50 height:18 enabled:false

    -- Height Offset Group
    groupBox heightOffsetGroup "Height Offset (Z-axis)" pos:[10,163] width:500 height:73
    checkbox useHeightOffset "Apply Height Offset" pos:[20,179] checked:false

    label offsetLabel "Offset:" pos:[20,201] width:45
    spinner heightOffsetSpn "" pos:[70,199] width:120 height:18 \\
        range:[-1000,1000,0] type:#float scale:0.1 enabled:false
    button calcHeightOffset "Calculate from Selection" pos:[200,199] width:300 height:18 enabled:false

    -- Main copy button
    button copyRootAnim "Copy Biped Root Animation to Root" pos:[10,245] width:500 height:35

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
            messageBox "Please select exactly 2 objects: CS Pelvis and Root bone" \\
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
            messageBox "Selection must contain one Biped node (CS Pelvis) and one regular node (Root)" \\
                title:"Height Offset"
            return undefined
        )

        -- Calculate height difference
        local heightDiff = csNode.pos.z - rootNode.pos.z
        heightOffsetSpn.value = heightDiff

        messageBox ("Height offset calculated: " + (heightDiff as string) + " units\\n\\n" + \\
                   "CS Pelvis Z: " + (csNode.pos.z as string) + "\\n" + \\
                   "Root Z: " + (rootNode.pos.z as string)) \\
            title:"Height Offset"
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
            messageBox "Root bone not found! Please ensure there is a node named 'root' in the scene." \\
                title:"Root Anim Copy"
            return undefined
        )

        if csRoot == undefined then
        (
            messageBox "CS Pelvis (Biped root) not found! Please ensure there is a Biped in the scene." \\
                title:"Root Anim Copy"
            return undefined
        )

        -- Get frame range
        local startFrameValue = frameStartEdit.text as integer
        local endFrameValue = frameEndEdit.text as integer

        if startFrameValue == undefined or endFrameValue == undefined then
        (
            messageBox "Invalid frame range! Please enter valid frame numbers." title:"Root Anim Copy"
            return undefined
        )

        local startFrame = startFrameValue as time
        local endFrame = endFrameValue as time

        -- Validate frame range
        if endFrame < startFrame then
        (
            messageBox "End frame must be greater than or equal to start frame!" title:"Root Anim Copy"
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
                messageBox ("Animation copy cancelled at frame " + t as string) title:"Root Anim Copy"
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
        messageBox ("Successfully copied " + frameCount as string + " frames from CS Pelvis to Root bone!") \\
            title:"Root Anim Copy"
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
