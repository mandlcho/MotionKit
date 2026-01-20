"""
FBX Animation Exporter Tool for MotionKit
Export animation with custom frame range and object selection to FBX
"""

import os
import subprocess
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
from core.unreal_api import get_unreal_api

TOOL_NAME = "Animation Exporter"


def _p4_checkout(file_path):
    """
    Check out a file in Perforce if it exists.

    Args:
        file_path: Full path to the file to check out

    Returns:
        bool: True if checkout successful or file doesn't need checkout, False on error
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.info(f"File doesn't exist yet, no P4 checkout needed: {file_path}")
            return True

        # Get P4 settings from config
        p4_server = config.get('perforce.server', '')
        p4_user = config.get('perforce.user', '')
        p4_workspace = config.get('perforce.workspace', '')

        if not p4_server or not p4_user:
            logger.info("Perforce not configured, skipping checkout")
            return True

        # Set P4 environment variables
        env = os.environ.copy()
        if p4_server:
            env['P4PORT'] = p4_server
        if p4_user:
            env['P4USER'] = p4_user
        if p4_workspace:
            env['P4CLIENT'] = p4_workspace

        # Check if file is in P4 workspace first
        check_result = subprocess.run(
            ['p4', 'fstat', file_path],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )

        # If file is not in depot, skip P4 operations
        if check_result.returncode != 0:
            if "not under client's root" in check_result.stderr or "not in client view" in check_result.stderr or "no such file" in check_result.stderr:
                logger.info(f"File not in P4 workspace, skipping P4 operations: {file_path}")
                return True

        # Try to check out the file
        result = subprocess.run(
            ['p4', 'edit', file_path],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )

        if result.returncode == 0:
            logger.info(f"P4 checkout successful: {file_path}")
            return True
        else:
            # File might not be in depot or already checked out
            if "currently opened for edit" in result.stdout or "currently opened for edit" in result.stderr:
                logger.info(f"File already checked out: {file_path}")
                return True
            elif "not under client's root" in result.stdout or "not under client's root" in result.stderr:
                logger.info(f"File not in P4 workspace, proceeding anyway: {file_path}")
                return True
            else:
                logger.error(f"P4 checkout failed: {result.stderr}")
                return False

    except FileNotFoundError:
        logger.info("P4 command not found, skipping checkout")
        return True
    except subprocess.TimeoutExpired:
        logger.error("P4 checkout timeout")
        return False
    except Exception as e:
        logger.error(f"P4 checkout error: {str(e)}")
        return False


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

    -- Progress Bar and Status
    progressBar exportProgress "" pos:[20,250] width:440 height:10 value:0 color:(color 100 150 255)
    label statusLabel "" pos:[20,265] width:440 height:15 align:#left

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
            -- Use only selected objects, no hierarchy expansion
            local objNamesStr = ""
            for i = 1 to selection.count do
            (
                objNamesStr += selection[i].name
                if i < selection.count then objNamesStr += "|"
            )
            objEdit.text = objNamesStr
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
                -- Use only the objects in the selection set, no hierarchy expansion
                local allObjects = for obj in selSet collect obj

                -- Select all objects in the viewport
                select allObjects

                -- Create pipe-delimited string of object names
                local objNamesStr = ""
                for i = 1 to allObjects.count do
                (
                    objNamesStr += allObjects[i].name
                    if i < allObjects.count then objNamesStr += "|"
                )
                objEdit.text = objNamesStr
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
            -- Save to config via Python function
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._save_export_path(r'" + newPath + "')")
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

        -- Reset progress and status
        exportProgress.value = 0
        statusLabel.text = "Starting export..."

        -- Call Python export function
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_animation('" + nameEdit.text + "', " + (startSpn.value as string) + ", " + (endSpn.value as string) + ", '" + objEdit.text + "')")

        -- Reset UI after export
        exportProgress.value = 0
        statusLabel.text = ""
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


# Global Python functions called from MaxScript
def _update_progress(value, status=""):
    """Update progress bar and status label in the dialog"""
    try:
        rt.execute(f"MotionKitAnimExporter.exportProgress.value = {value}")
        if status:
            status_escaped = status.replace('\\', '\\\\').replace('"', '\\"')
            rt.execute(f'MotionKitAnimExporter.statusLabel.text = "{status_escaped}"')
    except Exception as e:
        logger.warning(f"Failed to update UI progress: {str(e)}")


def _save_export_path(path):
    """Save export path to config (called from MaxScript)"""
    try:
        config.set('export.fbx_path', path)
        config.save()
        logger.info(f"Saved export path: {path}")
    except Exception as e:
        logger.error(f"Failed to save export path: {str(e)}")
        if rt:
            rt.messageBox(f"Failed to save path:\n{str(e)}", title="Animation Exporter")


def _check_p4_status(file_path):
    """
    Check Perforce status of a file

    Returns:
        str: 'new' if file needs to be added, 'existing' if already in depot, 'unknown' if P4 not available
    """
    try:
        # Check if file is in P4
        env = os.environ.copy()
        p4_server = config.get('perforce.server', '')
        p4_user = config.get('perforce.user', '')
        p4_workspace = config.get('perforce.workspace', '')

        if not p4_server or not p4_user:
            return 'unknown'

        if p4_server:
            env['P4PORT'] = p4_server
        if p4_user:
            env['P4USER'] = p4_user
        if p4_workspace:
            env['P4CLIENT'] = p4_workspace

        # Check file status
        result = subprocess.run(
            ['p4', 'fstat', file_path],
            capture_output=True,
            text=True,
            timeout=5,
            env=env
        )

        if result.returncode == 0:
            # File exists in depot
            if 'headAction' in result.stdout:
                return 'existing'
            else:
                return 'new'
        else:
            # File not in depot
            return 'new'

    except Exception as e:
        logger.debug(f"P4 status check failed: {str(e)}")
        return 'unknown'


def _prompt_unreal_import(exported_files):
    """
    Prompt user to import exported files into Unreal Engine

    Args:
        exported_files: List of exported FBX file paths

    Returns:
        bool: True if import was attempted
    """
    if not exported_files:
        return False

    try:
        # Check if Unreal is connected
        unreal_api = get_unreal_api()

        if not unreal_api.is_connected():
            logger.info("Unreal Engine not connected, skipping import prompt")
            return False

        # Categorize files by P4 status
        new_files = []
        existing_files = []

        for file_path in exported_files:
            status = _check_p4_status(file_path)
            if status == 'new':
                new_files.append(file_path)
            elif status == 'existing':
                existing_files.append(file_path)
            else:
                # Unknown status, treat as existing (safer to reimport)
                existing_files.append(file_path)

        # Prompt for existing files (reimport)
        if existing_files:
            file_names = [Path(f).stem for f in existing_files]
            file_list = "\\n".join(file_names[:5])
            if len(existing_files) > 5:
                file_list += f"\\n... and {len(existing_files) - 5} more"

            result = rt.queryBox(
                f"Export complete!\\n\\n"
                f"{len(existing_files)} existing file(s) were updated:\\n{file_list}\\n\\n"
                f"Reimport in Unreal Engine?",
                title="Unreal Import"
            )

            if result:
                # Get Unreal asset paths (assume same structure)
                content_path = config.get('unreal.content_browser_path', '/Game/Animations')
                asset_paths = [f"{content_path}/{Path(f).stem}" for f in existing_files]

                logger.info(f"Reimporting {len(asset_paths)} assets in Unreal...")
                success = unreal_api.reimport_assets(asset_paths)

                if success:
                    rt.messageBox(
                        f"Reimport request sent to Unreal Engine for {len(asset_paths)} asset(s).\\n\\n"
                        f"Check Unreal Editor for import results.",
                        title="Unreal Import"
                    )
                else:
                    rt.messageBox(
                        f"Failed to send reimport request to Unreal Engine.\\n\\n"
                        f"Make sure Web Remote Control is enabled.",
                        title="Unreal Import Error"
                    )

                return success

        # Prompt for new files (import)
        if new_files:
            file_names = [Path(f).stem for f in new_files]
            file_list = "\\n".join(file_names[:10])
            if len(new_files) > 10:
                file_list += f"\\n... and {len(new_files) - 10} more"

            result = rt.queryBox(
                f"Export complete!\\n\\n"
                f"{len(new_files)} new file(s) were created:\\n{file_list}\\n\\n"
                f"Import into Unreal Engine?",
                title="Unreal Import"
            )

            if result:
                # Import FBX files
                content_path = config.get('unreal.content_browser_path', '/Game/Animations')
                skeleton_path = config.get('unreal.skeleton_path', None)

                logger.info(f"Importing {len(new_files)} FBX files into Unreal...")
                success = unreal_api.import_fbx_files(new_files, content_path, skeleton_path)

                if success:
                    rt.messageBox(
                        f"Import request sent to Unreal Engine for {len(new_files)} file(s).\\n\\n"
                        f"Check Unreal Editor for import results.",
                        title="Unreal Import"
                    )
                else:
                    rt.messageBox(
                        f"Failed to send import request to Unreal Engine.\\n\\n"
                        f"Make sure Web Remote Control is enabled.",
                        title="Unreal Import Error"
                    )

                return success

        return False

    except Exception as e:
        logger.error(f"Unreal import prompt error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False



def _export_animation(name, start_frame, end_frame, objects_str):
    """Export animation to FBX with Perforce checkout"""

    def _set_fbx_param(param_name, value):
        """Helper to set FBX parameter with detailed logging and error handling."""
        try:
            logger.debug(f"Setting FBX Param: {param_name} = {value}")
            rt.FBXExporterSetParam(rt.Name(param_name), value)
            return True
        except Exception as e:
            error_msg = f"Failed to set FBX Exporter parameter '{param_name}' to '{value}'."
            logger.error(error_msg)
            
            if "Error getting MAXScript value" in str(e):
                full_error = (f"{error_msg}\n\nThis often means the 3ds Max FBX Exporter plugin is not loaded, "
                              "is in a bad state, or does not support this parameter.\n\n"
                              "Please try restarting 3ds Max or reinstalling the FBX plugin.")
                logger.error(full_error.replace('\n\n', ' '))
                rt.messageBox(full_error, title="FBX Configuration Error")
            else:
                rt.messageBox(f"{error_msg}\n\nError: {str(e)}", title="FBX Configuration Error")
            raise e

    try:
        _update_progress(5, "Detecting export path...")
        export_path = _detect_export_path()

        if not export_path:
            _update_progress(0, "")
            rt.messageBox(
                "Export path not configured!\n\nPlease set the default FBX export path in MotionKit Settings,\nor save your Max file in a folder structure with a sibling FBX folder.",
                title="Animation Exporter"
            )
            return

        export_file = os.path.join(export_path, f"{name}.fbx")
        logger.info(f"Exporting animation '{name}' from frame {start_frame} to {end_frame}")
        logger.info(f"Objects: {objects_str}")
        logger.info(f"Export path: {export_file}")

        _update_progress(10, "Parsing object names...")
        # Parse pipe-delimited object names
        object_names = [name.strip() for name in objects_str.split('|') if name.strip()]

        logger.info(f"Parsed {len(object_names)} object names: {object_names}")

        _update_progress(20, f"Finding {len(object_names)} objects in scene...")
        objects_to_export = []
        missing_objects = []
        for obj_name in object_names:
            obj = rt.getNodeByName(obj_name)
            if obj:
                objects_to_export.append(obj)
                logger.info(f"Found object: {obj_name}")
            else:
                missing_objects.append(obj_name)
                logger.warning(f"Object not found: {obj_name}")

        if not objects_to_export:
            _update_progress(0, "")
            rt.messageBox(f"No valid objects found to export!\n\nLooking for: {', '.join(object_names)}", title="Animation Exporter")
            return

        if missing_objects:
            logger.warning(f"Some objects not found: {missing_objects}")

        logger.info(f"Found {len(objects_to_export)} objects to export: {[obj.name for obj in objects_to_export]}")

        _update_progress(30, f"Checking Perforce...")
        if not _p4_checkout(export_file):
            if not rt.queryBox(f"P4 checkout failed for:\n{export_file}\n\nContinue anyway?", title="Animation Exporter"):
                logger.info("Export cancelled by user due to P4 checkout failure")
                return

        _update_progress(40, "Preparing file...")
        if os.path.exists(export_file):
            try:
                import stat
                os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
                logger.info(f"Removed read-only attribute from: {export_file}")
            except Exception as e:
                logger.warning(f"Failed to remove read-only attribute: {str(e)}")

        original_selection = rt.selection if rt.selection else []
        original_start = rt.animationRange.start
        original_end = rt.animationRange.end

        try:
            logger.info("Setting export properties...")
            _update_progress(50, "Selecting objects...")
            rt.select(objects_to_export)

            # Verify selection
            selected_count = rt.selection.count
            logger.info(f"Selected {selected_count} objects in viewport")
            if selected_count != len(objects_to_export):
                logger.warning(f"Selection count mismatch! Expected {len(objects_to_export)}, got {selected_count}")

            _update_progress(60, "Setting animation range...")
            rt.animationRange = rt.interval(start_frame, end_frame)

            _update_progress(70, "Configuring FBX settings...")
            _set_fbx_param("Animation", True)
            _set_fbx_param("BakeAnimation", True)
            _set_fbx_param("BakeFrameStart", start_frame)
            _set_fbx_param("BakeFrameEnd", end_frame)
            _set_fbx_param("BakeFrameStep", 1)
            _set_fbx_param("Shape", True)
            _set_fbx_param("Skin", True)
            _set_fbx_param("UpAxis", rt.Name("Z"))

            _update_progress(80, f"Exporting to {os.path.basename(export_file)}...")
            logger.info(f"Performing silent FBX export to: {export_file}")
            rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
            logger.info("Silent export command executed without errors.")

            _update_progress(100, "Export complete!")
            logger.info(f"Export completed for: {export_file}")

            # Prompt for Unreal import
            try:
                _prompt_unreal_import([export_file])
            except Exception as e:
                logger.error(f"Unreal prompt error: {str(e)}")

        finally:
            logger.debug("Restoring original scene state.")
            rt.animationRange = rt.interval(original_start, original_end)
            if len(original_selection) > 0:
                rt.select(original_selection)
            else:
                rt.clearSelection()

    except Exception as e:
        _update_progress(0, "Export failed!")
        logger.error(f"Failed to export animation: {str(e)}")
        # Avoid showing a duplicate message box if one was already shown by a helper.
        if "FBX Configuration Error" not in str(e):
             rt.messageBox(f"Failed to export animation:\n{str(e)}", title="Export Error")

