"""
FBX Animation Exporter Tool for MotionKit
Export multiple animations with custom frame ranges to FBX

UI/UX based on MotionBuilder's Animation Exporter
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[FBX Exporter] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "FBX Exporter"


def execute(control=None, event=None):
    """Execute the FBX Exporter tool"""
    if not pymxs or not rt:
        print("[FBX Exporter] ERROR: Not running in 3ds Max")
        return

    try:
        # Create and show the dialog
        dialog = FBXExporterDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open FBX Exporter: {str(e)}")
        rt.messageBox(
            f"Failed to open FBX Exporter:\n{str(e)}",
            title="MotionKit Error"
        )


class FBXExporterDialog:
    """FBX Animation Exporter dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"
        # Animation list: each entry is an array with [name, start, end, path, objects_string]
        self.animations = []

    def show(self):
        """Show the FBX Exporter dialog using MaxScript"""

        # Get all translations
        title = t('tools.fbx_exporter.title')
        animations_group = t('tools.fbx_exporter.animations_group')
        add_animation = t('tools.fbx_exporter.add_animation')
        edit_selected = t('tools.fbx_exporter.edit_selected')
        delete_selected = t('tools.fbx_exporter.delete_selected')
        delete_all = t('tools.fbx_exporter.delete_all')
        export_group = t('tools.fbx_exporter.export_group')
        export_selected = t('tools.fbx_exporter.export_selected')
        export_all = t('tools.fbx_exporter.export_all')
        close = t('common.close')

        maxscript = f'''
-- ============================================
-- MotionKit Animation Exporter Tool
-- ============================================

global MotionKitFBXExporter_AnimationList = #()
global MotionKitFBXExporter_DataGrid = undefined

rollout MotionKitFBXExporter "{title}" width:900 height:600
(
    -- Title
    label titleLabel "Export multiple animations with custom frame ranges" \\
        pos:[10,6] width:880 align:#center

    -- Animations List Group
    groupBox animationsGroup "{animations_group}" pos:[10,26] width:740 height:540

    -- DataGridView for Excel-like table
    dotNetControl animationsGrid "System.Windows.Forms.DataGridView" pos:[20,44] width:710 height:512

    -- Animation controls group
    groupBox animControlGroup "Animation" pos:[760,26] width:130 height:160
    button btnAddAnim "{add_animation}" pos:[770,46] width:110 height:28
    button btnEditAnim "{edit_selected}" pos:[770,78] width:110 height:28
    button btnDeleteSelected "{delete_selected}" pos:[770,110] width:110 height:28
    button btnDeleteAll "{delete_all}" pos:[770,142] width:110 height:28

    -- Export group
    groupBox exportControlGroup "{export_group}" pos:[760,380] width:130 height:92
    button btnExportSelected "{export_selected}" pos:[770,400] width:110 height:28
    button btnExportAll "{export_all}" pos:[770,432] width:110 height:28

    -- Close button at bottom
    button btnClose "{close}" pos:[770,530] width:110 height:28

    -- Setup DataGridView
    function setupDataGrid =
    (
        -- Store reference globally
        MotionKitFBXExporter_DataGrid = animationsGrid

        -- Basic appearance
        animationsGrid.BackgroundColor = animationsGrid.DefaultCellStyle.BackColor
        animationsGrid.BorderStyle = (dotNetClass "System.Windows.Forms.BorderStyle").FixedSingle
        animationsGrid.AllowUserToAddRows = false
        animationsGrid.AllowUserToDeleteRows = false
        animationsGrid.AllowUserToResizeRows = false
        animationsGrid.RowHeadersVisible = true
        animationsGrid.RowHeadersWidth = 40
        animationsGrid.SelectionMode = (dotNetClass "System.Windows.Forms.DataGridViewSelectionMode").FullRowSelect
        animationsGrid.MultiSelect = false
        animationsGrid.ReadOnly = true
        animationsGrid.AutoSizeColumnsMode = (dotNetClass "System.Windows.Forms.DataGridViewAutoSizeColumnsMode").Fill

        -- Alternating row colors
        animationsGrid.AlternatingRowsDefaultCellStyle.BackColor = (dotNetClass "System.Drawing.Color").FromArgb 240 240 240

        -- Add columns
        local nameCol = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        nameCol.HeaderText = "Animation Name"
        nameCol.Name = "Name"
        nameCol.FillWeight = 25
        animationsGrid.Columns.Add nameCol

        local startCol = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        startCol.HeaderText = "Start"
        startCol.Name = "Start"
        startCol.FillWeight = 12
        animationsGrid.Columns.Add startCol

        local endCol = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        endCol.HeaderText = "End"
        endCol.Name = "End"
        endCol.FillWeight = 12
        animationsGrid.Columns.Add endCol

        local objCol = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        objCol.HeaderText = "Objects"
        objCol.Name = "Objects"
        objCol.FillWeight = 20
        animationsGrid.Columns.Add objCol

        local pathCol = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        pathCol.HeaderText = "Path"
        pathCol.Name = "Path"
        pathCol.FillWeight = 31
        animationsGrid.Columns.Add pathCol
    )

    -- Update DataGridView with animation list
    function updateDataGrid =
    (
        animationsGrid.Rows.Clear()

        for anim in MotionKitFBXExporter_AnimationList do
        (
            local name = anim[1]
            local startFrame = anim[2] as string
            local endFrame = anim[3] as string
            local path = anim[4]
            local objects = anim[5]

            local rowIndex = animationsGrid.Rows.Add()
            local row = animationsGrid.Rows.item[rowIndex]
            row.Cells.item[0].Value = name
            row.Cells.item[1].Value = startFrame
            row.Cells.item[2].Value = endFrame
            row.Cells.item[3].Value = objects
            row.Cells.item[4].Value = path
        )
    )

    -- Get selected row index
    function getSelectedRowIndex =
    (
        if animationsGrid.SelectedRows.Count > 0 then
        (
            return (animationsGrid.SelectedRows.item[0].Index + 1)  -- Convert to 1-based
        )
        return 0
    )

    -- Initialize
    on MotionKitFBXExporter open do
    (
        setupDataGrid()
        updateDataGrid()
    )

    -- Add Animation
    on btnAddAnim pressed do
    (
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._add_animation_dialog()"
    )

    -- Edit Selected
    on btnEditAnim pressed do
    (
        local sel = getSelectedRowIndex()
        if sel > 0 then
        (
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._edit_animation_dialog(" + (sel as string) + ")")
        )
        else
        (
            messageBox "Please select an animation to edit" title:"{title}"
        )
    )

    -- Delete Selected
    on btnDeleteSelected pressed do
    (
        local sel = getSelectedRowIndex()
        if sel > 0 then
        (
            deleteItem MotionKitFBXExporter_AnimationList sel
            updateDataGrid()
        )
        else
        (
            messageBox "Please select an animation to delete" title:"{title}"
        )
    )

    -- Delete All
    on btnDeleteAll pressed do
    (
        if MotionKitFBXExporter_AnimationList.count > 0 then
        (
            if queryBox "Delete all animations from the list?" title:"{title}" then
            (
                MotionKitFBXExporter_AnimationList = #()
                updateDataGrid()
            )
        )
    )

    -- Export Selected
    on btnExportSelected pressed do
    (
        local sel = getSelectedRowIndex()
        if sel > 0 then
        (
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_animation(" + (sel as string) + ")")
        )
        else
        (
            messageBox "Please select an animation to export" title:"{title}"
        )
    )

    -- Export All
    on btnExportAll pressed do
    (
        if MotionKitFBXExporter_AnimationList.count > 0 then
        (
            python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_all_animations()"
        )
        else
        (
            messageBox "No animations to export!" title:"{title}"
        )
    )

    -- Close
    on btnClose pressed do
    (
        destroyDialog MotionKitFBXExporter
    )
)

-- Create and show dialog
try (destroyDialog MotionKitFBXExporter) catch()
createDialog MotionKitFBXExporter
'''

        # Execute the MaxScript to show the dialog
        rt.execute(maxscript)


# Global Python functions called from MaxScript

def _add_animation_dialog():
    """Show Add Animation dialog"""
    try:
        # Get translations
        title = t('tools.fbx_exporter.add_animation_title')
        name_label = t('tools.fbx_exporter.animation_name')
        start_label = t('tools.fbx_exporter.start_frame')
        end_label = t('tools.fbx_exporter.end_frame')
        objects_label = t('tools.fbx_exporter.objects')
        path_label = t('tools.fbx_exporter.export_path')
        use_selection = t('tools.fbx_exporter.use_selection')
        use_timeline = t('tools.fbx_exporter.use_timeline')
        browse = t('common.browse')
        add = t('common.ok')
        cancel = t('common.cancel')

        # Get current timeline range
        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)

        # Get current selection
        selection_str = ""
        if rt.selection.count > 0:
            selection_str = ", ".join([obj.name for obj in rt.selection])

        maxscript = f'''
rollout AddAnimationDialog "{title}" width:550 height:220
(
    label nameLbl "{name_label}:" pos:[10,10] width:80 align:#left
    edittext nameEdit "" pos:[100,8] width:440 height:18 labelOnTop:false

    label startLbl "{start_label}:" pos:[10,36] width:80 align:#left
    spinner startSpn "" pos:[100,34] width:80 height:18 type:#integer range:[-100000,100000,{start_frame}]

    checkbox useTimelineCB "{use_timeline}" pos:[190,36] checked:true

    label endLbl "{end_label}:" pos:[320,36] width:80 align:#left
    spinner endSpn "" pos:[410,34] width:80 height:18 type:#integer range:[-100000,100000,{end_frame}]

    label objLbl "{objects_label}:" pos:[10,62] width:80 align:#left
    edittext objEdit "" pos:[100,60] width:340 height:18 labelOnTop:false text:"{selection_str}"
    button btnPickObjs "{use_selection}" pos:[450,60] width:90 height:18

    label pathLbl "{path_label}:" pos:[10,88] width:80 align:#left
    edittext pathEdit "" pos:[100,86] width:340 height:18 labelOnTop:false
    button btnBrowse "{browse}" pos:[450,86] width:90 height:18

    button btnAdd "{add}" pos:[340,190] width:90 height:24
    button btnCancel "{cancel}" pos:[440,190] width:90 height:24

    -- Use Timeline checkbox handler
    on useTimelineCB changed state do
    (
        if state then
        (
            startSpn.value = animationRange.start.frame as integer
            endSpn.value = animationRange.end.frame as integer
        )
    )

    -- Pick Objects button
    on btnPickObjs pressed do
    (
        if selection.count > 0 then
        (
            local objNames = #()
            for obj in selection do append objNames obj.name
            objEdit.text = objNames as string
        )
        else
        (
            messageBox "No objects selected!" title:"{title}"
        )
    )

    -- Browse button
    on btnBrowse pressed do
    (
        local filepath = getSaveFileName caption:"{path_label}" \\
            filename:pathEdit.text types:"FBX Files (*.fbx)|*.fbx|All Files (*.*)|*.*"
        if filepath != undefined then
            pathEdit.text = filepath
    )

    -- Add button
    on btnAdd pressed do
    (
        -- Validation
        if nameEdit.text == "" then
        (
            messageBox "Please enter an animation name!" title:"{title}"
            return false
        )

        if startSpn.value >= endSpn.value then
        (
            messageBox "End frame must be greater than start frame!" title:"{title}"
            return false
        )

        -- Create animation entry
        local animEntry = #(nameEdit.text, startSpn.value, endSpn.value, pathEdit.text, objEdit.text)
        append MotionKitFBXExporter_AnimationList animEntry

        -- Update main dialog
        MotionKitFBXExporter.updateDataGrid()

        destroyDialog AddAnimationDialog
    )

    -- Cancel button
    on btnCancel pressed do
    (
        destroyDialog AddAnimationDialog
    )
)

createDialog AddAnimationDialog
'''
        rt.execute(maxscript)

    except Exception as e:
        logger.error(f"Failed to show Add Animation dialog: {str(e)}")
        rt.messageBox(f"Failed to show Add Animation dialog:\n{str(e)}", title="MotionKit Error")


def _edit_animation_dialog(index):
    """Show Edit Animation dialog"""
    try:
        # Get the animation data
        anim_list = rt.MotionKitFBXExporter_AnimationList
        if index < 1 or index > len(anim_list):
            rt.messageBox("Invalid animation index!", title="FBX Exporter")
            return

        anim = anim_list[index - 1]  # MaxScript uses 1-based indexing
        name = anim[0]
        start_frame = anim[1]
        end_frame = anim[2]
        path = anim[3]
        objects_str = anim[4]

        # Get translations
        title = t('tools.fbx_exporter.edit_animation_title')
        name_label = t('tools.fbx_exporter.animation_name')
        start_label = t('tools.fbx_exporter.start_frame')
        end_label = t('tools.fbx_exporter.end_frame')
        objects_label = t('tools.fbx_exporter.objects')
        path_label = t('tools.fbx_exporter.export_path')
        use_selection = t('tools.fbx_exporter.use_selection')
        browse = t('common.browse')
        save = t('common.save')
        cancel = t('common.cancel')

        maxscript = f'''
rollout EditAnimationDialog "{title}" width:550 height:200
(
    label nameLbl "{name_label}:" pos:[10,10] width:80 align:#left
    edittext nameEdit "" pos:[100,8] width:440 height:18 labelOnTop:false text:"{name}"

    label startLbl "{start_label}:" pos:[10,36] width:80 align:#left
    spinner startSpn "" pos:[100,34] width:80 height:18 type:#integer range:[-100000,100000,{start_frame}]

    label endLbl "{end_label}:" pos:[250,36] width:80 align:#left
    spinner endSpn "" pos:[340,34] width:80 height:18 type:#integer range:[-100000,100000,{end_frame}]

    label objLbl "{objects_label}:" pos:[10,62] width:80 align:#left
    edittext objEdit "" pos:[100,60] width:340 height:18 labelOnTop:false text:"{objects_str}"
    button btnPickObjs "{use_selection}" pos:[450,60] width:90 height:18

    label pathLbl "{path_label}:" pos:[10,88] width:80 align:#left
    edittext pathEdit "" pos:[100,86] width:340 height:18 labelOnTop:false text:"{path}"
    button btnBrowse "{browse}" pos:[450,86] width:90 height:18

    button btnSave "{save}" pos:[340,170] width:90 height:24
    button btnCancel "{cancel}" pos:[440,170] width:90 height:24

    -- Pick Objects button
    on btnPickObjs pressed do
    (
        if selection.count > 0 then
        (
            local objNames = #()
            for obj in selection do append objNames obj.name
            objEdit.text = objNames as string
        )
        else
        (
            messageBox "No objects selected!" title:"{title}"
        )
    )

    -- Browse button
    on btnBrowse pressed do
    (
        local filepath = getSaveFileName caption:"{path_label}" \\
            filename:pathEdit.text types:"FBX Files (*.fbx)|*.fbx|All Files (*.*)|*.*"
        if filepath != undefined then
            pathEdit.text = filepath
    )

    -- Save button
    on btnSave pressed do
    (
        -- Validation
        if nameEdit.text == "" then
        (
            messageBox "Please enter an animation name!" title:"{title}"
            return false
        )

        if startSpn.value >= endSpn.value then
        (
            messageBox "End frame must be greater than start frame!" title:"{title}"
            return false
        )

        -- Update animation entry
        MotionKitFBXExporter_AnimationList[{index}] = #(nameEdit.text, startSpn.value, endSpn.value, pathEdit.text, objEdit.text)

        -- Update main dialog
        MotionKitFBXExporter.updateDataGrid()

        destroyDialog EditAnimationDialog
    )

    -- Cancel button
    on btnCancel pressed do
    (
        destroyDialog EditAnimationDialog
    )
)

createDialog EditAnimationDialog
'''
        rt.execute(maxscript)

    except Exception as e:
        logger.error(f"Failed to show Edit Animation dialog: {str(e)}")
        rt.messageBox(f"Failed to show Edit Animation dialog:\n{str(e)}", title="MotionKit Error")


def _export_animation(index):
    """Export a single animation"""
    try:
        # Get the animation data
        anim_list = rt.MotionKitFBXExporter_AnimationList
        if index < 1 or index > len(anim_list):
            rt.messageBox("Invalid animation index!", title="FBX Exporter")
            return

        anim = anim_list[index - 1]
        name = anim[0]
        start_frame = int(anim[1])
        end_frame = int(anim[2])
        path = anim[3]
        objects_str = anim[4]

        # Validation
        if not path or path == "":
            rt.messageBox(f"Please set an export path for '{name}'", title="FBX Exporter")
            return

        # TODO: Implement actual FBX export logic here
        logger.info(f"Exporting animation: {name} [{start_frame}-{end_frame}] to {path}")
        rt.messageBox(
            f"Export functionality coming soon!\n\nAnimation: {name}\nFrames: {start_frame}-{end_frame}\nPath: {path}",
            title="FBX Exporter"
        )

    except Exception as e:
        logger.error(f"Failed to export animation: {str(e)}")
        rt.messageBox(f"Failed to export animation:\n{str(e)}", title="MotionKit Error")


def _export_all_animations():
    """Export all animations in the list"""
    try:
        anim_list = rt.MotionKitFBXExporter_AnimationList
        if not anim_list or len(anim_list) == 0:
            rt.messageBox("No animations to export!", title="FBX Exporter")
            return

        # TODO: Implement batch export logic
        logger.info(f"Exporting {len(anim_list)} animations...")
        rt.messageBox(
            f"Batch export functionality coming soon!\n\nAnimations to export: {len(anim_list)}",
            title="FBX Exporter"
        )

    except Exception as e:
        logger.error(f"Failed to export all animations: {str(e)}")
        rt.messageBox(f"Failed to export all animations:\n{str(e)}", title="MotionKit Error")
