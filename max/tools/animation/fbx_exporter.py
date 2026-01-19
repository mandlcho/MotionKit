"""
FBX Animation Exporter Tool for MotionKit
Export animation with custom frame range and object selection to FBX
"""

import os
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[FBX Exporter] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t
from core.config import config

TOOL_NAME = "Animation Exporter"


def _detect_export_path():
    """
    Auto-detect FBX export path based on current Max file location.

    Priority:
    1. If in .../Max/ folder, use sibling ../FBX/ folder
    2. Otherwise, use fallback path from Settings
    3. If no fallback, return None (user will be prompted)

    Returns:
        str: Export directory path, or None if not detected
    """
    try:
        # Get current Max file path
        max_file_path = rt.maxFilePath
        max_file_name = rt.maxFileName

        if not max_file_path or not max_file_name:
            # File not saved yet, use fallback
            logger.info("Max file not saved, using fallback export path")
            return config.get('export.fbx_path', None)

        # Convert to Path object
        current_dir = Path(max_file_path)

        # Check if current directory is named "Max"
        if current_dir.name.lower() == "max":
            # Look for sibling FBX folder
            parent = current_dir.parent
            fbx_dir = parent / "FBX"

            if fbx_dir.exists() and fbx_dir.is_dir():
                logger.info(f"Auto-detected FBX export path: {fbx_dir}")
                return str(fbx_dir)
            else:
                logger.warning(f"Sibling FBX folder not found at: {fbx_dir}")

        # Fallback to configured path
        fallback = config.get('export.fbx_path', None)
        if fallback:
            logger.info(f"Using fallback export path: {fallback}")
            return fallback

        logger.warning("No export path detected or configured")
        return None

    except Exception as e:
        logger.error(f"Failed to detect export path: {str(e)}")
        return config.get('export.fbx_path', None)


def execute(control=None, event=None):
    """Execute the Animation Exporter tool"""
    if not pymxs or not rt:
        print("[Animation Exporter] ERROR: Not running in 3ds Max")
        return

    try:
        # Create and show the dialog
        dialog = AnimationExporterDialog()
        dialog.show()

    except Exception as e:
        logger.error(f"Failed to open Animation Exporter: {str(e)}")
        rt.messageBox(
            f"Failed to open Animation Exporter:\n{str(e)}",
            title="MotionKit Error"
        )


class AnimationExporterDialog:
    """Animation Exporter dialog for MotionKit"""

    def __init__(self):
        self.version = "1.0.0"

    def _escape_maxscript(self, text):
        """Escape special characters for MaxScript strings"""
        if not text:
            return ""
        # Escape backslashes and quotes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        return text

    def show(self):
        """Show the Animation Exporter dialog using MaxScript"""

        # Get all translations
        title = t('tools.fbx_exporter.title')
        name_label = t('tools.fbx_exporter.animation_name')
        start_label = t('tools.fbx_exporter.start_frame')
        end_label = t('tools.fbx_exporter.end_frame')
        objects_label = t('tools.fbx_exporter.objects')
        use_selection = t('tools.fbx_exporter.use_selection')
        use_timeline = t('tools.fbx_exporter.use_timeline')
        export_btn = t('tools.fbx_exporter.export_selected')
        close = t('common.close')

        # Get current timeline range
        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)

        # Get selection sets
        selection_sets = []
        for i in range(rt.selectionSets.count):
            selection_sets.append(rt.selectionSets[i].name)

        selection_sets_str = "#(" + ", ".join([f'"{s}"' for s in selection_sets]) + ")"

        # Get current selection
        selection_str = ""
        if rt.selection.count > 0:
            selection_str = ", ".join([obj.name for obj in rt.selection])

        # Get default animation name from scene file name
        default_anim_name = ""
        max_file_path = rt.maxFilePath + rt.maxFileName
        if rt.maxFileName and rt.maxFileName != "":
            # Remove file extension
            default_anim_name = rt.getFilenameFile(rt.maxFileName)

        # Detect export path
        export_path = _detect_export_path()
        export_path_display = export_path if export_path else "(Not configured - set in Settings)"
        export_path_escaped = self._escape_maxscript(export_path_display)

        maxscript = f'''
-- ============================================
-- MotionKit Animation Exporter Tool
-- ============================================

rollout MotionKitAnimExporter "{title}" width:480 height:330
(
    -- Animation Name
    group "Animation"
    (
        label nameLbl "{name_label}:" pos:[20,20] width:100 align:#left
        edittext nameEdit "" pos:[130,18] width:320 height:20 labelOnTop:false text:"{default_anim_name}"
    )

    -- Frame Range
    group "Frame Range"
    (
        label startLbl "{start_label}:" pos:[20,70] width:100 align:#left
        spinner startSpn "" pos:[130,68] width:80 height:20 type:#integer range:[-100000,100000,{start_frame}]

        checkbox useTimelineCB "{use_timeline}" pos:[230,70] checked:true width:130

        label endLbl "{end_label}:" pos:[370,70] width:30 align:#left
        spinner endSpn "" pos:[410,68] width:60 height:20 type:#integer range:[-100000,100000,{end_frame}]
    )

    -- Objects
    group "Objects"
    (
        label objLbl "{objects_label}:" pos:[20,120] width:100 align:#left
        edittext objEdit "" pos:[130,118] width:240 height:20 labelOnTop:false text:"{selection_str}"
        button btnPickObjs "{use_selection}" pos:[380,118] width:70 height:20

        label selSetLbl "Selection Set:" pos:[20,148] width:100 align:#left
        dropdownList selSetDDL "" pos:[130,146] width:240 height:20 items:{selection_sets_str}
        button btnUseSelSet "Use Set" pos:[380,146] width:70 height:20
    )

    -- Export Path Preview
    group "Export Path"
    (
        label pathPreviewLbl "Export to:" pos:[20,200] width:60 align:#left
        edittext pathValueEdit "" pos:[90,198] width:360 height:20 labelOnTop:false text:"{export_path_escaped}" readOnly:true
        button btnChangePath "Change..." pos:[380,222] width:70 height:20
    )

    -- Bottom buttons
    button btnExport "{export_btn}" pos:[250,290] width:100 height:30
    button btnClose "{close}" pos:[360,290] width:100 height:30

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

    -- Use Selection Set button
    on btnUseSelSet pressed do
    (
        local setName = selSetDDL.selected
        if setName != undefined and setName != "" then
        (
            local selSet = selectionSets[setName]
            if selSet != undefined then
            (
                local objNames = #()
                for obj in selSet do append objNames obj.name
                objEdit.text = objNames as string
            )
        )
        else
        (
            messageBox "Please select a selection set!" title:"{title}"
        )
    )

    -- Change Path button
    on btnChangePath pressed do
    (
        local newPath = getSavePath caption:"Select FBX Export Directory"
        if newPath != undefined then
        (
            pathValueEdit.text = newPath
            -- Save to config
            python.execute ("import max.tools.animation.fbx_exporter; from core.config import config; config.set('export.fbx_path', '" + newPath + "'); config.save()")
        )
    )

    -- Export button
    on btnExport pressed do
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

        if objEdit.text == "" then
        (
            messageBox "Please select objects to export!" title:"{title}"
            return false
        )

        -- Call Python export function
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_animation('" + nameEdit.text + "', " + (startSpn.value as string) + ", " + (endSpn.value as string) + ", '" + objEdit.text + "')")
    )

    -- Close button
    on btnClose pressed do
    (
        destroyDialog MotionKitAnimExporter
    )
)

-- Create and show dialog
try (destroyDialog MotionKitAnimExporter) catch()
createDialog MotionKitAnimExporter
'''

        # Execute the MaxScript to show the dialog
        rt.execute(maxscript)


# Global Python function called from MaxScript
def _export_animation(name, start_frame, end_frame, objects_str):
    """Export animation to FBX (placeholder for now)"""
    try:
        # Detect export path
        export_path = _detect_export_path()

        if not export_path:
            rt.messageBox(
                "Export path not configured!\n\nPlease set the default FBX export path in MotionKit Settings,\nor save your Max file in a folder structure with a sibling FBX folder.",
                title="Animation Exporter"
            )
            return

        # Build full export file path
        export_file = os.path.join(export_path, f"{name}.fbx")

        logger.info(f"Exporting animation '{name}' from frame {start_frame} to {end_frame}")
        logger.info(f"Objects: {objects_str}")
        logger.info(f"Export path: {export_file}")

        # TODO: Implement actual FBX export
        rt.messageBox(
            f"Export functionality will be implemented next!\n\nAnimation: {name}\nFrames: {start_frame}-{end_frame}\nObjects: {objects_str}\n\nExport to: {export_file}",
            title="Animation Exporter"
        )

    except Exception as e:
        logger.error(f"Failed to export animation: {str(e)}")
        rt.messageBox(f"Failed to export animation:\n{str(e)}", title="Export Error")
