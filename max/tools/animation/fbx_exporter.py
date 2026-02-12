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


def _load_file_settings():
    """
    Load per-file frame range settings from scene custom attributes.
    
    Returns:
        dict: Settings dict with keys: start_frame, end_frame, use_timeline
              Returns None if no settings found in this scene
    """
    try:
        if not rt:
            logger.error("MaxScript runtime not available")
            return None
            
        # Read settings from root node custom attribute
        maxscript = '''
(
    if rootNode.custAttributes[#MotionKitFBXExporterSettings] != undefined then
    (
        local ca = rootNode.MotionKitFBXExporterSettings
        local result = #()
        append result ca.startFrame
        append result ca.endFrame
        append result ca.useTimeline
        result
    )
    else
    (
        undefined
    )
)
'''
        result = rt.execute(maxscript)
        
        if result and result != "undefined" and len(result) == 3:
            settings = {
                "start_frame": int(result[0]),
                "end_frame": int(result[1]),
                "use_timeline": bool(result[2])
            }
            logger.info(f"Loaded per-file settings from scene: {settings}")
            return settings
        else:
            logger.debug("No per-file settings found in scene")
            return None
            
    except Exception as e:
        logger.error(f"Failed to load per-file settings: {str(e)}")
        return None


def _save_file_settings(start_frame, end_frame, use_timeline):
    """
    Save per-file frame range settings to scene custom attributes.
    
    Args:
        start_frame: Start frame value
        end_frame: End frame value
        use_timeline: Whether "Use Timeline Range" is enabled
    """
    try:
        if not rt:
            logger.error("MaxScript runtime not available")
            return False
            
        # Convert Python bool to MaxScript bool
        use_timeline_str = "true" if use_timeline else "false"
        
        # Store in scene root node custom attribute
        maxscript = f'''
(
    -- Get or create custom attribute definition
    local caDef = attributes MotionKitFBXExporterSettings
    (
        parameters main
        (
            startFrame type:#integer default:{start_frame}
            endFrame type:#integer default:{end_frame}
            useTimeline type:#boolean default:{use_timeline_str}
        )
    )
    
    -- Apply to root node if not already present
    if rootNode.custAttributes[#MotionKitFBXExporterSettings] == undefined then
    (
        custAttributes.add rootNode caDef
    )
    
    -- Update values
    rootNode.MotionKitFBXExporterSettings.startFrame = {start_frame}
    rootNode.MotionKitFBXExporterSettings.endFrame = {end_frame}
    rootNode.MotionKitFBXExporterSettings.useTimeline = {use_timeline_str}
    
    true
)
'''
        result = rt.execute(maxscript)
        
        if result:
            logger.info(f"Saved per-file settings to scene: start={start_frame}, end={end_frame}, use_timeline={use_timeline}")
            return True
        else:
            logger.error("Failed to save per-file settings to scene")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save per-file settings: {str(e)}")
        return False


# ============================================
# Multi-Take Export Functions
# ============================================

def _save_takes_to_scene(takes_data):
    """
    Save multi-take data to scene as custom attribute on root node.
    
    Args:
        takes_data: List of dicts with keys: name, start_frame, end_frame, selection_set, enabled
        
    Example:
        [
            {"name": "Idle", "start_frame": 0, "end_frame": 30, "selection_set": "Fbx", "enabled": True},
            {"name": "Walk", "start_frame": 31, "end_frame": 60, "selection_set": "Fbx", "enabled": True}
        ]
    """
    try:
        if not rt:
            logger.error("MaxScript runtime not available")
            return False
            
        # Convert takes to pipe-delimited strings
        # Format: "name|start|end|selset|enabled"
        take_strings = []
        for take in takes_data:
            enabled_str = "1" if take.get("enabled", True) else "0"
            take_str = f"{take['name']}|{take['start_frame']}|{take['end_frame']}|{take['selection_set']}|{enabled_str}"
            take_strings.append(take_str)
        
        # Create MaxScript array string
        takes_array = "#(" + ", ".join([f'"{s}"' for s in take_strings]) + ")"
        
        # Store in scene root node custom attribute
        maxscript = f'''
(
    -- Get or create custom attribute definition
    local caDef = attributes MotionKitMultiTake
    (
        parameters main
        (
            takes type:#stringTab tabSize:0 tabSizeVariable:true
        )
    )
    
    -- Apply to root node
    if rootNode.custAttributes[#MotionKitMultiTake] == undefined then
    (
        custAttributes.add rootNode caDef
    )
    
    -- Set takes data
    rootNode.MotionKitMultiTake.takes = {takes_array}
    
    true
)
'''
        result = rt.execute(maxscript)
        
        if result:
            logger.info(f"Saved {len(takes_data)} takes to scene")
            return True
        else:
            logger.error("Failed to save takes to scene")
            return False
            
    except Exception as e:
        logger.error(f"Failed to save takes to scene: {str(e)}")
        return False


def _load_takes_from_scene():
    """
    Load multi-take data from scene custom attribute.
    
    Returns:
        list: List of take dicts, or empty list if no data found
    """
    try:
        if not rt:
            logger.error("MaxScript runtime not available")
            return []
            
        # Read takes from root node custom attribute
        maxscript = '''
(
    if rootNode.custAttributes[#MotionKitMultiTake] != undefined then
    (
        rootNode.MotionKitMultiTake.takes
    )
    else
    (
        #()
    )
)
'''
        result = rt.execute(maxscript)
        
        if not result or len(result) == 0:
            logger.info("No multi-take data found in scene")
            return []
        
        # Parse take strings
        takes_data = []
        for take_str in result:
            parts = take_str.split('|')
            if len(parts) >= 4:
                take = {
                    "name": parts[0],
                    "start_frame": int(parts[1]),
                    "end_frame": int(parts[2]),
                    "selection_set": parts[3],
                    "enabled": parts[4] == "1" if len(parts) > 4 else True
                }
                takes_data.append(take)
        
        logger.info(f"Loaded {len(takes_data)} takes from scene")
        return takes_data
        
    except Exception as e:
        logger.error(f"Failed to load takes from scene: {str(e)}")
        return []


def _export_multi_takes(take_indices, export_path, all_takes=False):
    """
    Export multiple takes from the current file.
    
    Args:
        take_indices: List of take indices to export (0-based), or None if all_takes=True
        export_path: FBX export directory path
        all_takes: If True, export all enabled takes regardless of take_indices
    """
    try:
        # Load takes from scene
        takes_data = _load_takes_from_scene()
        
        if not takes_data:
            rt.messageBox("No takes defined! Please add takes to the Multi-Take table first.", title="Multi-Take Export")
            return
        
        # Filter takes to export
        if all_takes:
            takes_to_export = [t for t in takes_data if t.get("enabled", True)]
            logger.info(f"Exporting all {len(takes_to_export)} enabled takes")
        else:
            if not take_indices:
                rt.messageBox("No takes selected! Please select takes to export.", title="Multi-Take Export")
                return
            takes_to_export = [takes_data[i] for i in take_indices if i < len(takes_data) and takes_data[i].get("enabled", True)]
            logger.info(f"Exporting {len(takes_to_export)} selected takes")
        
        if not takes_to_export:
            rt.messageBox("No enabled takes to export!", title="Multi-Take Export")
            return
        
        total_takes = len(takes_to_export)
        exported_files = []
        
        for idx, take in enumerate(takes_to_export):
            take_num = idx + 1
            logger.info(f"Exporting take {take_num}/{total_takes}: {take['name']}")
            _update_progress(int((take_num - 1) / total_takes * 100), f"Exporting {take_num}/{total_takes}: {take['name']}")
            
            # Find selection set
            sel_set = None
            for i in range(rt.selectionSets.count):
                if rt.selectionSets[i].name == take['selection_set']:
                    sel_set = rt.selectionSets[i]
                    break
            
            if not sel_set:
                logger.warning(f"Selection set '{take['selection_set']}' not found for take '{take['name']}', skipping...")
                continue
            
            # Get objects from selection set
            objects_to_export = [obj for obj in sel_set]
            
            if not objects_to_export:
                logger.warning(f"Selection set '{take['selection_set']}' is empty for take '{take['name']}', skipping...")
                continue
            
            # Select objects
            rt.select(objects_to_export)
            logger.info(f"Exporting {len(objects_to_export)} objects from '{take['selection_set']}' set")
            
            # Export FBX with take name
            export_file = os.path.join(export_path, f"{take['name']}.fbx")
            
            # Check out from P4 if needed
            if not _p4_checkout(export_file):
                logger.warning(f"P4 checkout failed for {export_file}, continuing anyway...")
            
            # Remove read-only if file exists
            if os.path.exists(export_file):
                try:
                    import stat
                    os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
                except Exception as e:
                    logger.warning(f"Failed to remove read-only attribute: {str(e)}")
            
            # Configure FBX export
            original_start = rt.animationRange.start
            original_end = rt.animationRange.end
            
            try:
                rt.animationRange = rt.interval(take['start_frame'], take['end_frame'])
                
                rt.FBXExporterSetParam(rt.Name("Animation"), True)
                rt.FBXExporterSetParam(rt.Name("BakeAnimation"), True)
                rt.FBXExporterSetParam(rt.Name("BakeFrameStart"), take['start_frame'])
                rt.FBXExporterSetParam(rt.Name("BakeFrameEnd"), take['end_frame'])
                rt.FBXExporterSetParam(rt.Name("BakeFrameStep"), 1)
                rt.FBXExporterSetParam(rt.Name("Shape"), True)
                rt.FBXExporterSetParam(rt.Name("Skin"), True)
                rt.FBXExporterSetParam(rt.Name("UpAxis"), rt.Name("Z"))
                
                # Export
                rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
                
                exported_files.append(export_file)
                logger.info(f"Exported: {export_file}")
                
            finally:
                rt.animationRange = rt.interval(original_start, original_end)
        
        _update_progress(100, "Multi-take export complete!")
        logger.info(f"Multi-take export complete: {len(exported_files)} files exported")
        
        # Show completion notification
        if exported_files:
            _show_export_notification(exported_files)
        else:
            rt.messageBox("No takes were exported!", title="Multi-Take Export")
        
    except Exception as e:
        _update_progress(0, "Multi-take export failed!")
        logger.error(f"Multi-take export failed: {str(e)}")
        rt.messageBox(f"Multi-take export failed:\n{str(e)}", title="Multi-Take Export Error")


# ============================================
# Multi-Take UI Management Functions
# ============================================

def _refresh_take_list():
    """Refresh the take list display in the UI"""
    try:
        takes_data = _load_takes_from_scene()
        
        # Format takes for display: "☑ TakeName | 0-30 | Fbx"
        take_items = []
        for take in takes_data:
            enabled_icon = "☑" if take.get("enabled", True) else "☐"
            take_str = f"{enabled_icon} {take['name']} | {take['start_frame']}-{take['end_frame']} | {take['selection_set']}"
            take_items.append(take_str)
        
        # Update UI
        if not take_items:
            take_items = ["(No takes defined - click 'Add Take')"]
        
        # Create MaxScript array string
        items_array = "#(" + ", ".join([f'"{s}"' for s in take_items]) + ")"
        
        maxscript = f'''
(
    if motionKitAnimExporterRollout != undefined then
    (
        motionKitAnimExporterRollout.refreshTakeList {items_array}
    )
)
'''
        rt.execute(maxscript)
        
    except Exception as e:
        logger.error(f"Failed to refresh take list: {str(e)}")


def _add_new_take():
    """Add a new take to the list"""
    try:
        takes_data = _load_takes_from_scene()
        
        # Get timeline range for default values
        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)
        
        # Get first selection set name
        default_sel_set = "Fbx"
        if rt.selectionSets.count > 0:
            default_sel_set = rt.selectionSets[0].name
        
        # Show edit dialog
        result = _show_take_edit_dialog(
            f"Take{len(takes_data) + 1}",
            start_frame,
            end_frame,
            default_sel_set,
            True
        )
        
        if result:
            takes_data.append(result)
            _save_takes_to_scene(takes_data)
            _refresh_take_list()
            logger.info(f"Added new take: {result['name']}")
        
    except Exception as e:
        logger.error(f"Failed to add take: {str(e)}")
        rt.messageBox(f"Failed to add take:\n{str(e)}", title="Add Take Error")


def _duplicate_take(index):
    """Duplicate a take"""
    try:
        takes_data = _load_takes_from_scene()
        
        if index < 0 or index >= len(takes_data):
            rt.messageBox("Invalid take index!", title="Duplicate Take")
            return
        
        # Copy the take
        original_take = takes_data[index]
        new_take = {
            "name": f"{original_take['name']}_copy",
            "start_frame": original_take['start_frame'],
            "end_frame": original_take['end_frame'],
            "selection_set": original_take['selection_set'],
            "enabled": original_take.get('enabled', True)
        }
        
        takes_data.insert(index + 1, new_take)
        _save_takes_to_scene(takes_data)
        _refresh_take_list()
        logger.info(f"Duplicated take: {original_take['name']} -> {new_take['name']}")
        
    except Exception as e:
        logger.error(f"Failed to duplicate take: {str(e)}")
        rt.messageBox(f"Failed to duplicate take:\n{str(e)}", title="Duplicate Take Error")


def _remove_takes(indices_str):
    """Remove takes by indices"""
    try:
        indices = [int(i) for i in indices_str.split('|') if i.strip()]
        takes_data = _load_takes_from_scene()
        
        # Remove in reverse order to preserve indices
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(takes_data):
                removed_take = takes_data.pop(index)
                logger.info(f"Removed take: {removed_take['name']}")
        
        _save_takes_to_scene(takes_data)
        _refresh_take_list()
        
    except Exception as e:
        logger.error(f"Failed to remove takes: {str(e)}")
        rt.messageBox(f"Failed to remove takes:\n{str(e)}", title="Remove Takes Error")


def _edit_take(index):
    """Edit a take"""
    try:
        takes_data = _load_takes_from_scene()
        
        if index < 0 or index >= len(takes_data):
            rt.messageBox("Invalid take index!", title="Edit Take")
            return
        
        take = takes_data[index]
        
        # Show edit dialog
        result = _show_take_edit_dialog(
            take['name'],
            take['start_frame'],
            take['end_frame'],
            take['selection_set'],
            take.get('enabled', True)
        )
        
        if result:
            takes_data[index] = result
            _save_takes_to_scene(takes_data)
            _refresh_take_list()
            logger.info(f"Edited take: {result['name']}")
        
    except Exception as e:
        logger.error(f"Failed to edit take: {str(e)}")
        rt.messageBox(f"Failed to edit take:\n{str(e)}", title="Edit Take Error")


def _show_take_edit_dialog(name, start_frame, end_frame, selection_set, enabled):
    """
    Show dialog to edit take properties
    
    Returns:
        dict: Take data if OK pressed, None if cancelled
    """
    try:
        # Get selection sets
        selection_sets = []
        for i in range(rt.selectionSets.count):
            selection_sets.append(rt.selectionSets[i].name)
        
        if not selection_sets:
            selection_sets = ["(No selection sets)"]
        
        selection_sets_str = "#(" + ", ".join([f'"{s}"' for s in selection_sets]) + ")"
        
        # Find index of current selection set
        sel_set_index = 1
        if selection_set in selection_sets:
            sel_set_index = selection_sets.index(selection_set) + 1
        
        enabled_str = "true" if enabled else "false"
        
        # Escape name for MaxScript
        name_escaped = name.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"')
        
        maxscript = f'''
(
    local dialogResult = undefined
    
    rollout TakeEditDialog "Edit Take" width:400 height:220
    (
        label nameLbl "Take Name:" pos:[20,20] width:80 align:#left
        edittext nameEdit "" pos:[105,17] width:275 height:22 text:"{name_escaped}"
        
        label startLbl "Start Frame:" pos:[20,55] width:80 align:#left
        spinner startSpn "" pos:[105,52] width:100 height:22 type:#integer range:[-100000,100000,{start_frame}]
        
        label endLbl "End Frame:" pos:[20,90] width:80 align:#left
        spinner endSpn "" pos:[105,87] width:100 height:22 type:#integer range:[-100000,100000,{end_frame}]
        
        label selSetLbl "Selection Set:" pos:[20,125] width:80 align:#left
        dropdownList selSetDDL "" pos:[105,122] width:275 height:22 items:{selection_sets_str} selection:{sel_set_index}
        
        checkbox enabledCB "Enabled" pos:[20,160] checked:{enabled_str}
        
        button btnOK "OK" pos:[170,185] width:100 height:28
        button btnCancel "Cancel" pos:[280,185] width:100 height:28
        
        on btnOK pressed do
        (
            if nameEdit.text == "" then
            (
                messageBox "Please enter a take name!" title:"Edit Take"
                return false
            )
            
            if startSpn.value >= endSpn.value then
            (
                messageBox "End frame must be greater than start frame!" title:"Edit Take"
                return false
            )
            
            -- Return pipe-delimited result
            dialogResult = nameEdit.text + "|" + (startSpn.value as string) + "|" + (endSpn.value as string) + "|" + selSetDDL.selected + "|" + (enabledCB.checked as string)
            destroyDialog TakeEditDialog
        )
        
        on btnCancel pressed do
        (
            dialogResult = undefined
            destroyDialog TakeEditDialog
        )
    )
    
    createDialog TakeEditDialog modal:true
    dialogResult
)
'''
        
        result_str = rt.execute(maxscript)
        
        if result_str and result_str != "undefined":
            # Parse result
            parts = str(result_str).split('|')
            if len(parts) >= 4:
                return {
                    "name": parts[0],
                    "start_frame": int(parts[1]),
                    "end_frame": int(parts[2]),
                    "selection_set": parts[3],
                    "enabled": parts[4].lower() == "true" if len(parts) > 4 else True
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to show take edit dialog: {str(e)}")
        return None


def _export_selected_takes(indices_str, export_path):
    """Export selected takes"""
    try:
        indices = [int(i) for i in indices_str.split('|') if i.strip()]
        _export_multi_takes(indices, export_path, all_takes=False)
    except Exception as e:
        logger.error(f"Failed to export selected takes: {str(e)}")


def _export_all_takes(export_path):
    """Export all enabled takes"""
    try:
        _export_multi_takes(None, export_path, all_takes=True)
    except Exception as e:
        logger.error(f"Failed to export all takes: {str(e)}")


def _show_multitake_manager():
    """Show the multi-take manager window"""
    try:
        # Load existing takes
        takes_data = _load_takes_from_scene()
        
        # Get selection sets
        selection_sets = []
        for i in range(rt.selectionSets.count):
            selection_sets.append(rt.selectionSets[i].name)
        
        if not selection_sets:
            selection_sets = ["(No selection sets)"]
        
        selection_sets_str = "#(" + ", ".join([f'"{s}"' for s in selection_sets]) + ")"
        
        # Format takes for display
        take_items = []
        for take in takes_data:
            enabled_icon = "☑" if take.get("enabled", True) else "☐"
            take_str = f"{enabled_icon} {take['name']} | {take['start_frame']}-{take['end_frame']} | {take['selection_set']}"
            take_items.append(take_str)
        
        if not take_items:
            take_items = ["(No takes defined - click 'Add Take')"]
        
        items_str = "#(" + ", ".join([f'"{s}"' for s in take_items]) + ")"
        
        maxscript = f'''
global motionKitMultiTakeManager

rollout MultiTakeManager "Multi-Take Manager" width:750 height:500
(
    -- Table header
    label headerEnabled "✓" pos:[10,10] width:30 height:20 align:#center
    label headerName "Take Name" pos:[50,10] width:200 height:20 align:#left
    label headerStart "Start" pos:[260,10] width:60 height:20 align:#center
    label headerEnd "End" pos:[330,10] width:60 height:20 align:#center
    label headerSelSet "Selection Set" pos:[400,10] width:150 height:20 align:#left
    label headerActions "Actions" pos:[560,10] width:180 height:20 align:#center
    
    -- Separator line
    label separator "" pos:[10,32] width:730 height:2
    
    -- Scrollable dotNetControl for table rows
    dotNetControl tableControl "System.Windows.Forms.DataGridView" pos:[10,40] width:730 height:350
    
    -- Management buttons at bottom
    button btnAddTake "Add Take" pos:[10,405] width:90 height:28
    button btnMoveUp "Move Up" pos:[110,405] width:90 height:28
    button btnMoveDown "Move Down" pos:[210,405] width:90 height:28
    button btnRefresh "Refresh" pos:[310,405] width:90 height:28
    
    -- Close button
    button btnClose "Close" pos:[660,405] width:80 height:28
    
    -- Help text
    label helpText "Double-click a cell to edit. Check/uncheck to enable/disable takes." pos:[10,445] width:730 height:20 align:#left
    
    -- Initialize DataGridView
    fn initDataGrid =
    (
        tableControl.AllowUserToAddRows = false
        tableControl.SelectionMode = tableControl.SelectionMode.FullRowSelect
        tableControl.MultiSelect = true
        tableControl.RowHeadersVisible = false
        tableControl.BackgroundColor = (dotNetClass "System.Drawing.Color").FromArgb 240 240 240
        
        -- Enabled column (checkbox)
        local colEnabled = dotNetObject "System.Windows.Forms.DataGridViewCheckBoxColumn"
        colEnabled.Name = "Enabled"
        colEnabled.HeaderText = "✓"
        colEnabled.Width = 40
        tableControl.Columns.Add colEnabled
        
        -- Name column
        local colName = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        colName.Name = "Name"
        colName.HeaderText = "Take Name"
        colName.Width = 180
        tableControl.Columns.Add colName
        
        -- Start column
        local colStart = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        colStart.Name = "Start"
        colStart.HeaderText = "Start"
        colStart.Width = 70
        tableControl.Columns.Add colStart
        
        -- End column
        local colEnd = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        colEnd.Name = "End"
        colEnd.HeaderText = "End"
        colEnd.Width = 70
        tableControl.Columns.Add colEnd
        
        -- Selection Set column
        local colSelSet = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        colSelSet.Name = "SelectionSet"
        colSelSet.HeaderText = "Selection Set"
        colSelSet.Width = 180
        tableControl.Columns.Add colSelSet
        
        -- Actions column
        local colActions = dotNetObject "System.Windows.Forms.DataGridViewTextBoxColumn"
        colActions.Name = "Actions"
        colActions.HeaderText = "Actions"
        colActions.Width = 100
        colActions.ReadOnly = true
        tableControl.Columns.Add colActions
        
        -- Load takes data
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._populate_multitake_grid()"
    )
    
    -- Add Take button
    on btnAddTake pressed do
    (
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._add_new_take()"
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._populate_multitake_grid()"
    )
    
    -- Move Up button
    on btnMoveUp pressed do
    (
        if tableControl.SelectedRows.Count > 0 then
        (
            local rowIndex = tableControl.SelectedRows.item[0].Index
            if rowIndex > 0 then
            (
                python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._move_take_up(" + (rowIndex as string) + ")")
                python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._populate_multitake_grid()"
            )
        )
    )
    
    -- Move Down button
    on btnMoveDown pressed do
    (
        if tableControl.SelectedRows.Count > 0 then
        (
            local rowIndex = tableControl.SelectedRows.item[0].Index
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._move_take_down(" + (rowIndex as string) + ")")
            python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._populate_multitake_grid()"
        )
    )
    
    -- Refresh button
    on btnRefresh pressed do
    (
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._populate_multitake_grid()"
    )
    
    -- Handle cell value changes
    on tableControl CellValueChanged args do
    (
        local rowIndex = args.RowIndex
        local colIndex = args.ColumnIndex
        
        -- Save changes to scene (with small delay to ensure value is committed)
        dotNet.setLifetimeControl args #dotNet
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._update_take_from_grid(" + (rowIndex as string) + ")")
    )
    
    -- Handle checkbox clicks in Enabled column
    on tableControl CellContentClick args do
    (
        local rowIndex = args.RowIndex
        local colIndex = args.ColumnIndex
        
        -- Enabled column (index 0) - toggle checkbox
        if colIndex == 0 then
        (
            -- Commit the edit so value changes
            tableControl.CommitEdit tableControl.CommitEdit.CurrentCellChange
        )
        -- Actions column (index 5) - delete button
        else if colIndex == 5 then
        (
            local result = queryBox "Delete this take?" title:"Confirm Delete"
            if result then
            (
                python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._delete_take_at_index(" + (rowIndex as string) + ")")
                python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._populate_multitake_grid()"
            )
        )
    )
    
    -- Handle cell click to begin edit mode immediately
    on tableControl CellClick args do
    (
        local rowIndex = args.RowIndex
        local colIndex = args.ColumnIndex
        
        -- For enabled column (checkbox), begin edit immediately
        if colIndex == 0 then
        (
            tableControl.BeginEdit false
        )
    )
    
    -- Close button
    on btnClose pressed do
    (
        try
        (
            destroyDialog MultiTakeManager
        )
        catch
        (
            -- Ignore if already closed
        )
    )
    
    -- Initialize on open
    on MultiTakeManager open do
    (
        motionKitMultiTakeManager = MultiTakeManager
        initDataGrid()
    )
    
    on MultiTakeManager close do
    (
        motionKitMultiTakeManager = undefined
    )
)

try (destroyDialog MultiTakeManager) catch()
createDialog MultiTakeManager
'''
        
        rt.execute(maxscript)
        
    except Exception as e:
        logger.error(f"Failed to show multi-take manager: {str(e)}")
        rt.messageBox(f"Failed to show multi-take manager:\n{str(e)}", title="Multi-Take Manager Error")


def _populate_multitake_grid():
    """Populate the DataGridView with takes data"""
    try:
        takes_data = _load_takes_from_scene()
        
        # Build MaxScript to populate grid directly
        rows_data = []
        for take in takes_data:
            enabled = "true" if take.get('enabled', True) else "false"
            name = take['name'].replace('"', '\\"')
            start = take['start_frame']
            end = take['end_frame']
            sel_set = take['selection_set'].replace('"', '\\"')
            rows_data.append(f'#({enabled}, "{name}", {start}, {end}, "{sel_set}")')
        
        rows_array = "#(" + ", ".join(rows_data) + ")"
        
        maxscript = f'''
(
    if motionKitMultiTakeManager != undefined then
    (
        local grid = motionKitMultiTakeManager.tableControl
        grid.Rows.Clear()
        
        local takesData = {rows_array}
        
        for takeRow in takesData do
        (
            local rowIndex = grid.Rows.Add()
            local row = grid.Rows.item[rowIndex]
            
            row.Cells.item[0].Value = takeRow[1]
            row.Cells.item[1].Value = takeRow[2]
            row.Cells.item[2].Value = takeRow[3]
            row.Cells.item[3].Value = takeRow[4]
            row.Cells.item[4].Value = takeRow[5]
            row.Cells.item[5].Value = "[Delete]"
        )
    )
)
'''
        rt.execute(maxscript)
        
    except Exception as e:
        logger.error(f"Failed to populate multi-take grid: {str(e)}")


def _update_take_from_grid(row_index):
    """Update take data from grid row"""
    try:
        maxscript = f'''
(
    local grid = motionKitMultiTakeManager.tableControl
    local row = grid.Rows.item[{row_index}]
    
    local enabled = row.Cells.item[0].Value
    local name = row.Cells.item[1].Value as string
    local startFrame = row.Cells.item[2].Value as integer
    local endFrame = row.Cells.item[3].Value as integer
    local selSet = row.Cells.item[4].Value as string
    
    -- Pass data to Python
    python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._save_take_at_index({row_index}, '" + name + "', " + (startFrame as string) + ", " + (endFrame as string) + ", '" + selSet + "', " + (enabled as string) + ")")
)
'''
        rt.execute(maxscript)
        
    except Exception as e:
        logger.error(f"Failed to update take from grid: {str(e)}")


def _save_take_at_index(index, name, start_frame, end_frame, selection_set, enabled):
    """Save updated take data at specific index"""
    try:
        takes_data = _load_takes_from_scene()
        
        if 0 <= index < len(takes_data):
            takes_data[index] = {
                "name": name,
                "start_frame": int(start_frame),
                "end_frame": int(end_frame),
                "selection_set": selection_set,
                "enabled": enabled
            }
            _save_takes_to_scene(takes_data)
            logger.info(f"Updated take at index {index}: {name}")
        
    except Exception as e:
        logger.error(f"Failed to save take at index: {str(e)}")


def _delete_take_at_index(index):
    """Delete take at specific index"""
    try:
        takes_data = _load_takes_from_scene()
        
        if 0 <= index < len(takes_data):
            removed_take = takes_data.pop(index)
            _save_takes_to_scene(takes_data)
            logger.info(f"Deleted take: {removed_take['name']}")
        
    except Exception as e:
        logger.error(f"Failed to delete take: {str(e)}")


def _move_take_up(index):
    """Move take up in the list"""
    try:
        takes_data = _load_takes_from_scene()
        
        if 0 < index < len(takes_data):
            takes_data[index], takes_data[index - 1] = takes_data[index - 1], takes_data[index]
            _save_takes_to_scene(takes_data)
            logger.info(f"Moved take up: {takes_data[index]['name']}")
        
    except Exception as e:
        logger.error(f"Failed to move take up: {str(e)}")


def _move_take_down(index):
    """Move take down in the list"""
    try:
        takes_data = _load_takes_from_scene()
        
        if 0 <= index < len(takes_data) - 1:
            takes_data[index], takes_data[index + 1] = takes_data[index + 1], takes_data[index]
            _save_takes_to_scene(takes_data)
            logger.info(f"Moved take down: {takes_data[index]['name']}")
        
    except Exception as e:
        logger.error(f"Failed to move take down: {str(e)}")


def _toggle_takes_enabled(indices_str):
    """Toggle enabled/disabled state for takes"""
    try:
        indices = [int(i) for i in indices_str.split('|') if i.strip()]
        takes_data = _load_takes_from_scene()
        
        for index in indices:
            if 0 <= index < len(takes_data):
                current_state = takes_data[index].get('enabled', True)
                takes_data[index]['enabled'] = not current_state
                logger.info(f"Toggled take '{takes_data[index]['name']}' enabled state to {not current_state}")
        
        _save_takes_to_scene(takes_data)
        
    except Exception as e:
        logger.error(f"Failed to toggle takes: {str(e)}")
        rt.messageBox(f"Failed to toggle takes:\n{str(e)}", title="Toggle Takes Error")


def _batch_export_with_multitake(start_frame, end_frame, export_path, selected_files_str=None):
    """
    Batch export files using multi-take data if available
    
    Args:
        start_frame: Fallback start frame if no multi-take data
        end_frame: Fallback end frame if no multi-take data
        export_path: FBX export directory path
        selected_files_str: Pipe-delimited string of selected files, or None for all files
    """
    try:
        # Get current Max file directory
        current_max_path = rt.maxFilePath
        current_max_name = rt.maxFileName
        
        if not current_max_path or not current_max_name:
            rt.messageBox("Please save the current file before batch export!", title="Batch Export")
            return
        
        logger.info(f"Starting batch multi-take export from directory: {current_max_path}")
        
        # Get list of files to export
        if selected_files_str:
            # Parse selected files
            max_files = [f.strip() for f in selected_files_str.split('|') if f.strip()]
        else:
            # Get all .max files in the directory
            import glob
            max_files = glob.glob(os.path.join(current_max_path, "*.max"))
            max_files = [os.path.basename(f) for f in max_files]
            max_files.sort()
        
        if not max_files:
            rt.messageBox("No Max files found!", title="Batch Export")
            return
        
        logger.info(f"Found {len(max_files)} Max files to process: {max_files}")
        
        # Move current file to front of list if doing "All"
        if not selected_files_str and current_max_name in max_files:
            max_files.remove(current_max_name)
            max_files.insert(0, current_max_name)
        
        total_files = len(max_files)
        all_exported_files = []
        
        for idx, max_file in enumerate(max_files):
            file_num = idx + 1
            logger.info(f"Processing file {file_num}/{total_files}: {max_file}")
            _update_progress(int((file_num - 1) / total_files * 100), f"Processing {file_num}/{total_files}: {max_file}")
            
            # Load file if not current file
            if max_file != current_max_name:
                logger.info(f"Loading file: {max_file}")
                full_path = os.path.join(current_max_path, max_file)
                
                try:
                    rt.loadMaxFile(full_path, quiet=True)
                    logger.info(f"Loaded: {max_file}")
                except Exception as e:
                    logger.error(f"Failed to load {max_file}: {str(e)}")
                    continue
            
            # Check if file has multi-take data
            takes_data = _load_takes_from_scene()
            
            if takes_data:
                # Use multi-take export
                logger.info(f"File has {len(takes_data)} multi-takes, using multi-take export")
                takes_to_export = [t for t in takes_data if t.get("enabled", True)]
                
                for take in takes_to_export:
                    try:
                        # Export this take
                        sel_set = None
                        for i in range(rt.selectionSets.count):
                            if rt.selectionSets[i].name == take['selection_set']:
                                sel_set = rt.selectionSets[i]
                                break
                        
                        if not sel_set:
                            logger.warning(f"Selection set '{take['selection_set']}' not found for take '{take['name']}', skipping...")
                            continue
                        
                        objects_to_export = [obj for obj in sel_set]
                        if not objects_to_export:
                            logger.warning(f"Selection set '{take['selection_set']}' is empty for take '{take['name']}', skipping...")
                            continue
                        
                        rt.select(objects_to_export)
                        
                        export_file = os.path.join(export_path, f"{take['name']}.fbx")
                        
                        if not _p4_checkout(export_file):
                            logger.warning(f"P4 checkout failed for {export_file}, continuing anyway...")
                        
                        if os.path.exists(export_file):
                            try:
                                import stat
                                os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
                            except Exception as e:
                                logger.warning(f"Failed to remove read-only attribute: {str(e)}")
                        
                        original_start = rt.animationRange.start
                        original_end = rt.animationRange.end
                        
                        try:
                            rt.animationRange = rt.interval(take['start_frame'], take['end_frame'])
                            
                            rt.FBXExporterSetParam(rt.Name("Animation"), True)
                            rt.FBXExporterSetParam(rt.Name("BakeAnimation"), True)
                            rt.FBXExporterSetParam(rt.Name("BakeFrameStart"), take['start_frame'])
                            rt.FBXExporterSetParam(rt.Name("BakeFrameEnd"), take['end_frame'])
                            rt.FBXExporterSetParam(rt.Name("BakeFrameStep"), 1)
                            rt.FBXExporterSetParam(rt.Name("Shape"), True)
                            rt.FBXExporterSetParam(rt.Name("Skin"), True)
                            rt.FBXExporterSetParam(rt.Name("UpAxis"), rt.Name("Z"))
                            
                            rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
                            
                            all_exported_files.append(export_file)
                            logger.info(f"Exported: {export_file}")
                            
                        finally:
                            rt.animationRange = rt.interval(original_start, original_end)
                    
                    except Exception as e:
                        logger.error(f"Failed to export take '{take['name']}': {str(e)}")
                        continue
            else:
                # Fallback to single export using 'Fbx' selection set
                logger.info(f"No multi-take data, using fallback single export")
                
                fbx_set = None
                for i in range(rt.selectionSets.count):
                    if rt.selectionSets[i].name.lower() == "fbx":
                        fbx_set = rt.selectionSets[i]
                        break
                
                if not fbx_set:
                    logger.warning(f"No 'Fbx' selection set found in {max_file}, skipping...")
                    continue
                
                objects_to_export = [obj for obj in fbx_set]
                if not objects_to_export:
                    logger.warning(f"'Fbx' selection set is empty in {max_file}, skipping...")
                    continue
                
                rt.select(objects_to_export)
                
                anim_name = os.path.splitext(max_file)[0]
                export_file = os.path.join(export_path, f"{anim_name}.fbx")
                
                if not _p4_checkout(export_file):
                    logger.warning(f"P4 checkout failed for {export_file}, continuing anyway...")
                
                if os.path.exists(export_file):
                    try:
                        import stat
                        os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
                    except Exception as e:
                        logger.warning(f"Failed to remove read-only attribute: {str(e)}")
                
                original_start = rt.animationRange.start
                original_end = rt.animationRange.end
                
                try:
                    rt.animationRange = rt.interval(start_frame, end_frame)
                    
                    rt.FBXExporterSetParam(rt.Name("Animation"), True)
                    rt.FBXExporterSetParam(rt.Name("BakeAnimation"), True)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameStart"), start_frame)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameEnd"), end_frame)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameStep"), 1)
                    rt.FBXExporterSetParam(rt.Name("Shape"), True)
                    rt.FBXExporterSetParam(rt.Name("Skin"), True)
                    rt.FBXExporterSetParam(rt.Name("UpAxis"), rt.Name("Z"))
                    
                    rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
                    
                    all_exported_files.append(export_file)
                    logger.info(f"Exported: {export_file}")
                    
                finally:
                    rt.animationRange = rt.interval(original_start, original_end)
        
        # Restore original file
        if current_max_name and current_max_name != max_files[-1]:
            try:
                logger.info(f"Restoring original file: {current_max_name}")
                full_path = os.path.join(current_max_path, current_max_name)
                rt.loadMaxFile(full_path, quiet=True)
            except Exception as e:
                logger.error(f"Failed to restore original file: {str(e)}")
        
        _update_progress(100, "Batch export complete!")
        logger.info(f"Batch export complete: {len(all_exported_files)} files exported")
        
        if all_exported_files:
            _show_export_notification(all_exported_files)
        else:
            rt.messageBox("No files were exported!", title="Batch Export")
    
    except Exception as e:
        _update_progress(0, "Batch export failed!")
        logger.error(f"Batch export failed: {str(e)}")
        rt.messageBox(f"Batch export failed:\n{str(e)}", title="Batch Export Error")


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
        
        # Check if dialog already exists and bring to front
        try:
            check_existing = rt.execute("motionKitAnimExporterDialog != undefined")
            if check_existing:
                logger.info("Animation Exporter dialog already open, bringing to front")
                rt.execute("try (setDialogPos motionKitAnimExporterDialog (getDialogPos motionKitAnimExporterDialog)) catch()")
                return
        except Exception as e:
            logger.debug(f"Could not check for existing dialog: {str(e)}")

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

        # Get current timeline range (default)
        timeline_start = int(rt.animationRange.start.frame)
        timeline_end = int(rt.animationRange.end.frame)
        
        # Try to load per-file settings from scene
        start_frame = timeline_start
        end_frame = timeline_end
        use_timeline_checked = True
        
        file_settings = _load_file_settings()
        if file_settings:
            start_frame = file_settings.get('start_frame', timeline_start)
            end_frame = file_settings.get('end_frame', timeline_end)
            use_timeline_checked = file_settings.get('use_timeline', True)
            logger.info(f"Loaded saved settings: start={start_frame}, end={end_frame}, use_timeline={use_timeline_checked}")

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
        if rt.maxFileName and rt.maxFileName != "":
            # Remove file extension
            default_anim_name = rt.getFilenameFile(rt.maxFileName)

        # Detect export path
        export_path = _detect_export_path()
        export_path_display = export_path if export_path else "(Not configured - set in Settings)"
        export_path_escaped = self._escape_maxscript(export_path_display)
        
        # Convert use_timeline_checked to MaxScript boolean
        use_timeline_checked_str = "true" if use_timeline_checked else "false"

        maxscript = f'''
-- ============================================
-- MotionKit Animation Exporter Tool
-- ============================================

global motionKitAnimExporterRollout
global motionKitAnimExporterDialog

rollout MotionKitAnimExporter "{title}" width:500 height:430
(
    -- Animation Name
    group "Animation"
    (
        label nameLbl "{name_label}:" pos:[20,23] width:100 align:#left
        edittext nameEdit "" pos:[125,20] width:350 height:22 labelOnTop:false text:"{default_anim_name}"
    )

    -- Frame Range
    group "Frame Range"
    (
        label startLbl "Start:" pos:[20,75] width:45 align:#left
        spinner startSpn "" pos:[70,72] width:85 height:22 type:#integer range:[-100000,100000,{start_frame}]

        label endLbl "End:" pos:[180,75] width:35 align:#left
        spinner endSpn "" pos:[220,72] width:85 height:22 type:#integer range:[-100000,100000,{end_frame}]

        checkbox useTimelineCB "{use_timeline}" pos:[330,75] checked:{use_timeline_checked_str} width:150
    )

    -- Objects
    group "Objects"
    (
        label objLbl "{objects_label}:" pos:[20,130] width:90 align:#left
        edittext objEdit "" pos:[115,127] width:285 height:22 labelOnTop:false text:"{selection_str}"
        button btnPickObjs "{use_selection}" pos:[410,127] width:65 height:22

        label selSetLbl "Selection Set:" pos:[20,160] width:90 align:#left
        dropdownList selSetDDL "" pos:[115,157] width:285 height:22 items:{selection_sets_str}
        button btnUseSelSet "Use Set" pos:[410,157] width:65 height:22
    )

    -- Export Path Preview
    group "Export Path"
    (
        label pathPreviewLbl "Export to:" pos:[20,215] width:70 align:#left
        edittext pathValueEdit "" pos:[95,212] width:380 height:22 labelOnTop:false text:"{export_path_escaped}" readOnly:true
        button btnChangePath "Change..." pos:[410,238] width:65 height:22
    )
    
    -- Multi-Take Export Button
    button btnManageMultiTake "Manage Takes..." pos:[15,275] width:120 height:28
    checkbox enableMultiTakeCB "Use Multi-Take Export" pos:[145,280] width:180 checked:false

    -- Progress Bar and Status
    progressBar exportProgress "" pos:[15,315] width:470 height:14 value:0 color:(color 100 150 255)
    label statusLabel "" pos:[15,335] width:470 height:22 align:#center

    -- Export section
    group "Export"
    (
        button btnExportCurrent "Current" pos:[20,375] width:105 height:32
        button btnExportSelected "Selection" pos:[135,375] width:105 height:32
        button btnExportAll "All" pos:[250,375] width:105 height:32
    )

    -- Close button
    button btnClose "{close}" pos:[365,375] width:115 height:32

    -- ============================================
    -- Function Definitions (must be before event handlers)
    -- ============================================
    
    -- Function to update dialog with current scene info
    fn updateSceneInfo =
    (
        -- Update animation name from filename
        if maxFileName != "" then
            nameEdit.text = getFilenameFile maxFileName
        else
            nameEdit.text = ""

        -- Update selection sets dropdown
        local setNames = #()
        for i = 1 to selectionSets.count do
            append setNames selectionSets[i].name
        selSetDDL.items = setNames

        -- Load saved per-file settings from scene
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._load_and_apply_settings_to_dialog()"
    )

    -- ============================================
    -- Event Handlers
    -- ============================================

    -- Use Timeline checkbox handler
    on useTimelineCB changed state do
    (
        if state then
        (
            startSpn.value = animationRange.start.frame as integer
            endSpn.value = animationRange.end.frame as integer
            startSpn.enabled = false
            endSpn.enabled = false
        )
        else
        (
            startSpn.enabled = true
            endSpn.enabled = true
        )
        
        -- Save settings to scene
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._save_file_settings(" + (startSpn.value as string) + ", " + (endSpn.value as string) + ", " + (state as string) + ")")
    )
    
    -- Start frame spinner changed handler
    on startSpn changed val do
    (
        -- Save settings to scene
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._save_file_settings(" + (val as string) + ", " + (endSpn.value as string) + ", " + (useTimelineCB.checked as string) + ")")
    )
    
    -- End frame spinner changed handler
    on endSpn changed val do
    (
        -- Save settings to scene
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._save_file_settings(" + (startSpn.value as string) + ", " + (val as string) + ", " + (useTimelineCB.checked as string) + ")")
    )
    
    -- Manage Multi-Take button
    on btnManageMultiTake pressed do
    (
        python.execute "import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._show_multitake_manager()"
    )

    -- Set initial state on dialog open
    on MotionKitAnimExporter open do
    (
        -- Store reference to this rollout globally
        motionKitAnimExporterRollout = MotionKitAnimExporter

        -- Disable spinners if Use Timeline is checked by default
        if useTimelineCB.checked then
        (
            startSpn.enabled = false
            endSpn.enabled = false
        )

        -- Register file callbacks to update dialog when files are opened
        callbacks.addScript #filePostOpen "try (if motionKitAnimExporterRollout != undefined do motionKitAnimExporterRollout.updateSceneInfo()) catch()" id:#motionKitAnimExporter
        callbacks.addScript #systemPostNew "try (if motionKitAnimExporterRollout != undefined do motionKitAnimExporterRollout.updateSceneInfo()) catch()" id:#motionKitAnimExporter
        callbacks.addScript #filePostMerge "try (if motionKitAnimExporterRollout != undefined do motionKitAnimExporterRollout.updateSceneInfo()) catch()" id:#motionKitAnimExporter
    )

    -- Remove callbacks when dialog closes
    on MotionKitAnimExporter close do
    (
        callbacks.removeScripts #filePostOpen id:#motionKitAnimExporter
        callbacks.removeScripts #systemPostNew id:#motionKitAnimExporter
        callbacks.removeScripts #filePostMerge id:#motionKitAnimExporter
        motionKitAnimExporterRollout = undefined
        motionKitAnimExporterDialog = undefined
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

    -- Export Current button
    on btnExportCurrent pressed do
    (
        -- Check if multi-take export is enabled
        if enableMultiTakeCB.checked then
        (
            -- Export all enabled takes from current file
            local escapedPath = substituteString pathValueEdit.text "\\\\" "\\\\\\\\"
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_all_takes(r'" + escapedPath + "')")
        )
        else
        (
            -- Original single-export logic
            -- Validation
            if startSpn.value >= endSpn.value then
            (
                messageBox "End frame must be greater than start frame!" title:"{title}"
                return false
            )

            -- Reset progress and status
            exportProgress.value = 0
            statusLabel.text = "Exporting current file..."

            -- Escape backslashes for Python raw string
            local escapedPath = substituteString pathValueEdit.text "\\\\" "\\\\\\\\"

            -- Call Python export current function
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_current_file(" + (startSpn.value as string) + ", " + (endSpn.value as string) + ", r'" + escapedPath + "')")

            -- Reset UI after export
            exportProgress.value = 0
            statusLabel.text = ""
        )
    )

    -- Export Selected button
    on btnExportSelected pressed do
    (
        -- Check if multi-take export is enabled
        if enableMultiTakeCB.checked then
        (
            -- Show file selection dialog for multi-take batch export
            local escapedPath = substituteString pathValueEdit.text "\\\\" "\\\\\\\\"
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._show_file_selection_dialog_multitake(" + (startSpn.value as string) + ", " + (endSpn.value as string) + ", r'" + escapedPath + "')")
        )
        else
        (
            -- Original file selection dialog
            -- Validation
            if startSpn.value >= endSpn.value then
            (
                messageBox "End frame must be greater than start frame!" title:"{title}"
                return false
            )

            -- Escape backslashes for Python raw string
            local escapedPath = substituteString pathValueEdit.text "\\\\" "\\\\\\\\"

            -- Call Python function to show file selection dialog
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._show_file_selection_dialog(" + (startSpn.value as string) + ", " + (endSpn.value as string) + ", r'" + escapedPath + "')")
        )
    )

    -- Export All button
    on btnExportAll pressed do
    (
        -- Check if multi-take export is enabled
        if enableMultiTakeCB.checked then
        (
            -- Batch export all files using multi-take data
            local confirmMsg = "Export all Max files in current directory?\\n\\nThis will:\\n1. Open each .max file\\n2. Export all enabled takes (if multi-take data exists)\\n3. Or export 'Fbx' selection set (if no multi-take data)\\n\\nContinue?"
            if not (queryBox confirmMsg title:"Batch Multi-Take Export") then
                return false
            
            local escapedPath = substituteString pathValueEdit.text "\\\\" "\\\\\\\\"
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._batch_export_with_multitake(" + (startSpn.value as string) + ", " + (endSpn.value as string) + ", r'" + escapedPath + "', None)")
        )
        else
        (
            -- Original batch export
            -- Validation
            if startSpn.value >= endSpn.value then
            (
                messageBox "End frame must be greater than start frame!" title:"{title}"
                return false
            )

            -- Confirm batch export
            if not (queryBox "Export all Max files in current directory?\\n\\nThis will:\\n1. Export current file\\n2. Open next file in directory\\n3. Select 'Fbx' selection set\\n4. Export and repeat\\n\\nContinue?" title:"Export All") then
                return false

            -- Reset progress and status
            exportProgress.value = 0
            statusLabel.text = "Starting batch export..."

            -- Escape backslashes for Python raw string
            local escapedPath = substituteString pathValueEdit.text "\\\\" "\\\\\\\\"

            -- Call Python batch export function
            python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._batch_export_directory(" + (startSpn.value as string) + ", " + (endSpn.value as string) + ", r'" + escapedPath + "')")

            -- Reset UI after export
            exportProgress.value = 0
            statusLabel.text = ""
        )
    )

    -- Close button
    on btnClose pressed do
    (
        try
        (
            destroyDialog MotionKitAnimExporter
        )
        catch
        (
            -- If dialog already destroyed, ignore error
        )
    )
)

-- Create and show dialog (singleton pattern)
if motionKitAnimExporterDialog != undefined then
(
    -- Dialog already exists, just bring it to front
    try
    (
        setDialogPos motionKitAnimExporterDialog (getDialogPos motionKitAnimExporterDialog)
    )
    catch
    (
        -- Dialog reference is stale, destroy it and create new one
        try (destroyDialog MotionKitAnimExporter) catch()
        motionKitAnimExporterDialog = createDialog MotionKitAnimExporter
    )
)
else
(
    -- Create new dialog
    try (destroyDialog MotionKitAnimExporter) catch()
    motionKitAnimExporterDialog = createDialog MotionKitAnimExporter
)
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


def _load_and_apply_settings_to_dialog():
    """
    Load per-file settings from scene and apply them to the dialog.
    Called when opening a new file or changing scenes.
    """
    try:
        # Get timeline range as fallback
        timeline_start = int(rt.animationRange.start.frame)
        timeline_end = int(rt.animationRange.end.frame)
        
        # Load settings from scene
        file_settings = _load_file_settings()
        
        if file_settings:
            start_frame = file_settings.get('start_frame', timeline_start)
            end_frame = file_settings.get('end_frame', timeline_end)
            use_timeline = file_settings.get('use_timeline', True)
            
            # Apply to dialog
            use_timeline_str = "true" if use_timeline else "false"
            rt.execute(f"MotionKitAnimExporter.startSpn.value = {start_frame}")
            rt.execute(f"MotionKitAnimExporter.endSpn.value = {end_frame}")
            rt.execute(f"MotionKitAnimExporter.useTimelineCB.checked = {use_timeline_str}")
            
            # Update spinner enabled state based on use_timeline
            if use_timeline:
                rt.execute("MotionKitAnimExporter.startSpn.enabled = false")
                rt.execute("MotionKitAnimExporter.endSpn.enabled = false")
            else:
                rt.execute("MotionKitAnimExporter.startSpn.enabled = true")
                rt.execute("MotionKitAnimExporter.endSpn.enabled = true")
            
            logger.info(f"Applied saved settings to dialog: start={start_frame}, end={end_frame}, use_timeline={use_timeline}")
        else:
            # No saved settings, use timeline defaults
            rt.execute(f"MotionKitAnimExporter.startSpn.value = {timeline_start}")
            rt.execute(f"MotionKitAnimExporter.endSpn.value = {timeline_end}")
            rt.execute("MotionKitAnimExporter.useTimelineCB.checked = true")
            rt.execute("MotionKitAnimExporter.startSpn.enabled = false")
            rt.execute("MotionKitAnimExporter.endSpn.enabled = false")
            logger.debug("No saved settings found, using timeline defaults")
            
    except Exception as e:
        logger.error(f"Failed to load and apply settings to dialog: {str(e)}")


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


def _show_export_notification(exported_files):
    """
    Show simple notification after export with option to open folder

    Args:
        exported_files: List of exported FBX file paths

    Returns:
        bool: True if user opened the folder
    """
    if not exported_files:
        return False

    try:
        export_dir = str(Path(exported_files[0]).parent)

        file_names = [Path(f).stem for f in exported_files[:10]]
        if len(exported_files) > 10:
            file_list = "\\n".join([f"  • {name}" for name in file_names])
            file_list += f"\\n  • ... and {len(exported_files) - 10} more"
        else:
            file_list = "\\n".join([f"  • {name}" for name in file_names])

        result = rt.queryBox(
            f"Export complete!\\n\\n"
            f"{len(exported_files)} file(s) exported:\\n{file_list}\\n\\n"
            f"Open export folder in Windows Explorer?",
            title="Export Complete"
        )

        if result:
            # Open Windows Explorer to the export folder
            subprocess.Popen(f'explorer /select,"{exported_files[0]}"')
            logger.info(f"Opened Windows Explorer to: {export_dir}")
            return True

        return False

    except Exception as e:
        logger.error(f"Export notification error: {str(e)}")
        return False



def _get_p4_workspace_root():
    """
    Get Perforce workspace root directory

    Returns:
        str: P4 workspace root path, or None if not found
    """
    try:
        p4_workspace = config.get('perforce.workspace', '')
        if not p4_workspace:
            return None

        # Get P4 settings from config
        p4_server = config.get('perforce.server', '')
        p4_user = config.get('perforce.user', '')

        if not p4_server or not p4_user:
            return None

        # Set P4 environment variables
        env = os.environ.copy()
        env['P4PORT'] = p4_server
        env['P4USER'] = p4_user
        env['P4CLIENT'] = p4_workspace

        # Get workspace root from P4
        result = subprocess.run(
            ['p4', 'client', '-o'],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )

        if result.returncode == 0:
            # Parse output for Root: line
            for line in result.stdout.split('\n'):
                if line.startswith('Root:'):
                    root_path = line.split(':', 1)[1].strip()
                    logger.info(f"P4 workspace root: {root_path}")
                    return root_path

        return None

    except Exception as e:
        logger.warning(f"Failed to get P4 workspace root: {str(e)}")
        return None


def _export_current_file(start_frame, end_frame, export_path):
    """
    Export the currently open Max file

    Args:
        start_frame: Start frame for animation
        end_frame: End frame for animation
        export_path: FBX export directory path
    """
    try:
        current_max_name = rt.maxFileName

        if not current_max_name or current_max_name == "":
            rt.messageBox("Please save the current file before export!", title="Export Current")
            return

        # Get animation name from filename (without extension)
        anim_name = rt.getFilenameFile(current_max_name)

        logger.info(f"Exporting current file: {current_max_name}")

        # Find "Fbx" selection set
        fbx_set = None
        for i in range(rt.selectionSets.count):
            if rt.selectionSets[i].name.lower() == "fbx":
                fbx_set = rt.selectionSets[i]
                break

        if not fbx_set:
            rt.messageBox("No 'Fbx' selection set found in current file!", title="Export Current")
            return

        # Get objects from selection set
        objects_to_export = [obj for obj in fbx_set]

        if not objects_to_export:
            rt.messageBox("'Fbx' selection set is empty!", title="Export Current")
            return

        # Select objects
        rt.select(objects_to_export)

        # Create pipe-delimited string of object names
        objects_str = "|".join([obj.name for obj in objects_to_export])

        logger.info(f"Exporting {len(objects_to_export)} objects from 'Fbx' set")

        # Export file
        export_file = os.path.join(export_path, f"{anim_name}.fbx")

        _update_progress(10, "Checking Perforce...")
        if not _p4_checkout(export_file):
            logger.warning(f"P4 checkout failed, continuing anyway...")

        # Remove read-only if file exists
        if os.path.exists(export_file):
            try:
                import stat
                os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
            except Exception as e:
                logger.warning(f"Failed to remove read-only attribute: {str(e)}")

        # Configure FBX export
        original_start = rt.animationRange.start
        original_end = rt.animationRange.end

        try:
            _update_progress(30, "Configuring export...")
            rt.animationRange = rt.interval(start_frame, end_frame)

            rt.FBXExporterSetParam(rt.Name("Animation"), True)
            rt.FBXExporterSetParam(rt.Name("BakeAnimation"), True)
            rt.FBXExporterSetParam(rt.Name("BakeFrameStart"), start_frame)
            rt.FBXExporterSetParam(rt.Name("BakeFrameEnd"), end_frame)
            rt.FBXExporterSetParam(rt.Name("BakeFrameStep"), 1)
            rt.FBXExporterSetParam(rt.Name("Shape"), True)
            rt.FBXExporterSetParam(rt.Name("Skin"), True)
            rt.FBXExporterSetParam(rt.Name("UpAxis"), rt.Name("Z"))

            _update_progress(70, f"Exporting {os.path.basename(export_file)}...")
            rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)

            _update_progress(100, "Export complete!")
            logger.info(f"Exported: {export_file}")

            # Show completion notification
            # _show_export_notification([export_file])

        finally:
            rt.animationRange = rt.interval(original_start, original_end)

    except Exception as e:
        _update_progress(0, "Export failed!")
        logger.error(f"Export current file failed: {str(e)}")
        rt.messageBox(f"Export failed:\n{str(e)}", title="Export Current Error")


def _show_file_selection_dialog(start_frame, end_frame, export_path):
    """
    Show a dialog to select Max files to export

    Args:
        start_frame: Start frame for animation
        end_frame: End frame for animation
        export_path: FBX export directory path
    """
    try:
        # Get current Max file directory
        current_max_path = rt.maxFilePath

        # If no file open, use P4 workspace root
        if not current_max_path or current_max_path == "":
            current_max_path = _get_p4_workspace_root()
            if not current_max_path:
                rt.messageBox("No Max file open and P4 workspace not configured!", title="Export Selected")
                return

        logger.info(f"Scanning directory for Max files: {current_max_path}")

        # Get all .max files in the directory
        import glob
        max_files = glob.glob(os.path.join(current_max_path, "*.max"))
        max_files = [os.path.basename(f) for f in max_files]
        max_files.sort()

        if not max_files:
            rt.messageBox(f"No Max files found in:\n{current_max_path}", title="Export Selected")
            return

        logger.info(f"Found {len(max_files)} Max files")

        # Escape paths for Python string parsing (double backslashes)
        export_path_escaped = export_path.replace('\\', '\\\\')
        current_max_path_escaped = current_max_path.replace('\\', '\\\\')

        # Show file selection dialog via MaxScript
        maxscript = f'''
rollout FileSelectionDialog "Select Files to Export" width:420 height:600
(
    multiListBox fileList "" items:#({",".join([f'"{f}"' for f in max_files])}) selection:#{{}} pos:[10,10] width:400 height:29

    -- Selection helper buttons (under list)
    button btnSelectAll "Select All" pos:[20,505] width:90 height:25
    button btnDeselectAll "Deselect All" pos:[120,505] width:90 height:25
    button btnInvertSel "Invert Selection" pos:[220,505] width:110 height:25

    -- Selection count (under helper buttons)
    label selectionLabel "0 file(s) selected" pos:[10,535] width:400 align:#center

    -- Export/Cancel buttons (centered at bottom)
    button btnExport "Export Selection" pos:[80,565] width:125 height:28
    button btnCancel "Cancel" pos:[215,565] width:125 height:28

    -- Update selection count
    fn updateSelectionCount =
    (
        local count = (fileList.selection as bitArray).numberSet
        selectionLabel.text = (count as string) + " file(s) selected"
    )

    on fileList selectionEnd do
    (
        updateSelectionCount()
    )

    -- Select All button
    on btnSelectAll pressed do
    (
        local allBits = #{{}}
        for i = 1 to fileList.items.count do
            append allBits i
        fileList.selection = allBits as bitArray
        updateSelectionCount()
    )

    -- Deselect All button
    on btnDeselectAll pressed do
    (
        fileList.selection = #{{}}
        updateSelectionCount()
    )

    -- Invert Selection button
    on btnInvertSel pressed do
    (
        local currentSel = fileList.selection as bitArray
        local invertedSel = #{{}}
        for i = 1 to fileList.items.count do
        (
            if not (currentSel[i]) then
                append invertedSel i
        )
        fileList.selection = invertedSel as bitArray
        updateSelectionCount()
    )

    on btnExport pressed do
    (
        local selectedFiles = #()
        local selBits = fileList.selection as bitArray

        for i in selBits do
        (
            append selectedFiles (fileList.items[i])
        )

        if selectedFiles.count == 0 then
        (
            messageBox "Please select at least one file!" title:"Export Selected"
            return false
        )

        -- Create pipe-delimited string
        local filesStr = ""
        for i = 1 to selectedFiles.count do
        (
            filesStr += selectedFiles[i]
            if i < selectedFiles.count then filesStr += "|"
        )

        -- Call Python function to export selected files
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._export_selected_files({start_frame}, {end_frame}, r'{export_path_escaped}', r'{current_max_path_escaped}', '" + filesStr + "')")

        destroyDialog FileSelectionDialog
    )

    on btnCancel pressed do
    (
        destroyDialog FileSelectionDialog
    )
)

try (destroyDialog FileSelectionDialog) catch()
createDialog FileSelectionDialog
'''

        rt.execute(maxscript)

    except Exception as e:
        logger.error(f"Failed to show file selection dialog: {str(e)}")
        rt.messageBox(f"Failed to show file selection:\n{str(e)}", title="Export Selected Error")


def _show_file_selection_dialog_multitake(start_frame, end_frame, export_path):
    """
    Show a dialog to select Max files to export using multi-take mode
    
    Args:
        start_frame: Fallback start frame for files without multi-take data
        end_frame: Fallback end frame for files without multi-take data
        export_path: FBX export directory path
    """
    try:
        # Get current Max file directory
        current_max_path = rt.maxFilePath
        
        if not current_max_path or current_max_path == "":
            current_max_path = _get_p4_workspace_root()
            if not current_max_path:
                rt.messageBox("No Max file open and P4 workspace not configured!", title="Export Selected")
                return
        
        logger.info(f"Scanning directory for Max files: {current_max_path}")
        
        # Get all .max files in the directory
        import glob
        max_files = glob.glob(os.path.join(current_max_path, "*.max"))
        max_files = [os.path.basename(f) for f in max_files]
        max_files.sort()
        
        if not max_files:
            rt.messageBox(f"No Max files found in:\n{current_max_path}", title="Export Selected")
            return
        
        logger.info(f"Found {len(max_files)} Max files")
        
        # Escape paths for Python string parsing
        export_path_escaped = export_path.replace('\\', '\\\\')
        
        # Show file selection dialog via MaxScript
        maxscript = f'''
rollout FileSelectionDialog "Select Files to Export (Multi-Take Mode)" width:420 height:600
(
    multiListBox fileList "" items:#({",".join([f'"{f}"' for f in max_files])}) selection:#{{}} pos:[10,10] width:400 height:29

    -- Selection helper buttons
    button btnSelectAll "Select All" pos:[20,505] width:90 height:25
    button btnDeselectAll "Deselect All" pos:[120,505] width:90 height:25
    button btnInvertSel "Invert Selection" pos:[220,505] width:110 height:25

    -- Selection count
    label selectionLabel "0 file(s) selected" pos:[10,535] width:400 align:#center

    -- Export/Cancel buttons
    button btnExport "Export Selection" pos:[80,565] width:125 height:28
    button btnCancel "Cancel" pos:[215,565] width:125 height:28

    -- Update selection count
    fn updateSelectionCount =
    (
        local count = (fileList.selection as bitArray).numberSet
        selectionLabel.text = (count as string) + " file(s) selected"
    )

    on fileList selectionEnd do
    (
        updateSelectionCount()
    )

    on btnSelectAll pressed do
    (
        local allBits = #{{}}
        for i = 1 to fileList.items.count do
            append allBits i
        fileList.selection = allBits as bitArray
        updateSelectionCount()
    )

    on btnDeselectAll pressed do
    (
        fileList.selection = #{{}}
        updateSelectionCount()
    )

    on btnInvertSel pressed do
    (
        local currentSel = fileList.selection as bitArray
        local invertedSel = #{{}}
        for i = 1 to fileList.items.count do
        (
            if not (currentSel[i]) then
                append invertedSel i
        )
        fileList.selection = invertedSel as bitArray
        updateSelectionCount()
    )

    on btnExport pressed do
    (
        local selectedFiles = #()
        local selBits = fileList.selection as bitArray

        for i in selBits do
        (
            append selectedFiles (fileList.items[i])
        )

        if selectedFiles.count == 0 then
        (
            messageBox "Please select at least one file!" title:"Export Selected"
            return false
        )

        -- Create pipe-delimited string
        local filesStr = ""
        for i = 1 to selectedFiles.count do
        (
            filesStr += selectedFiles[i]
            if i < selectedFiles.count then filesStr += "|"
        )

        -- Call Python function for multi-take batch export
        python.execute ("import max.tools.animation.fbx_exporter; max.tools.animation.fbx_exporter._batch_export_with_multitake({start_frame}, {end_frame}, r'{export_path_escaped}', '" + filesStr + "')")

        destroyDialog FileSelectionDialog
    )

    on btnCancel pressed do
    (
        destroyDialog FileSelectionDialog
    )
)

try (destroyDialog FileSelectionDialog) catch()
createDialog FileSelectionDialog
'''
        
        rt.execute(maxscript)
    
    except Exception as e:
        logger.error(f"Failed to show file selection dialog (multi-take): {str(e)}")
        rt.messageBox(f"Failed to show file selection:\n{str(e)}", title="Export Selected Error")


def _export_selected_files(start_frame, end_frame, export_path, source_directory, files_str):
    """
    Export selected Max files

    Args:
        start_frame: Start frame for animation
        end_frame: End frame for animation
        export_path: FBX export directory path
        source_directory: Directory containing Max files
        files_str: Pipe-delimited string of selected file names
    """
    try:
        # Parse file names
        selected_files = [f.strip() for f in files_str.split('|') if f.strip()]

        if not selected_files:
            rt.messageBox("No files selected!", title="Export Selected")
            return

        logger.info(f"Exporting {len(selected_files)} selected files: {selected_files}")

        # Store current file info
        current_max_path = rt.maxFilePath
        current_max_name = rt.maxFileName

        total_files = len(selected_files)
        exported_files = []

        for idx, max_file in enumerate(selected_files):
            file_num = idx + 1
            logger.info(f"Processing {file_num}/{total_files}: {max_file}")
            _update_progress(int((file_num - 1) / total_files * 100), f"Processing {file_num}/{total_files}: {max_file}")

            # Get animation name from filename (without extension)
            anim_name = os.path.splitext(max_file)[0]

            # Load file
            logger.info(f"Loading file: {max_file}")
            full_path = os.path.join(source_directory, max_file)

            try:
                rt.loadMaxFile(full_path, quiet=True)
                logger.info(f"Loaded: {max_file}")
            except Exception as e:
                logger.error(f"Failed to load {max_file}: {str(e)}")
                continue

            # Find "Fbx" selection set
            fbx_set = None
            for i in range(rt.selectionSets.count):
                if rt.selectionSets[i].name.lower() == "fbx":
                    fbx_set = rt.selectionSets[i]
                    break

            if not fbx_set:
                logger.warning(f"No 'Fbx' selection set found in {max_file}, skipping...")
                continue

            # Get objects from selection set
            objects_to_export = [obj for obj in fbx_set]

            if not objects_to_export:
                logger.warning(f"'Fbx' selection set is empty in {max_file}, skipping...")
                continue

            # Select objects
            rt.select(objects_to_export)

            logger.info(f"Exporting {len(objects_to_export)} objects from 'Fbx' set")

            # Export this animation
            try:
                export_file = os.path.join(export_path, f"{anim_name}.fbx")

                # Check out from P4 if needed
                if not _p4_checkout(export_file):
                    logger.warning(f"P4 checkout failed for {export_file}, continuing anyway...")

                # Remove read-only if file exists
                if os.path.exists(export_file):
                    try:
                        import stat
                        os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
                    except Exception as e:
                        logger.warning(f"Failed to remove read-only attribute: {str(e)}")

                # Configure FBX export
                original_start = rt.animationRange.start
                original_end = rt.animationRange.end

                try:
                    rt.animationRange = rt.interval(start_frame, end_frame)

                    rt.FBXExporterSetParam(rt.Name("Animation"), True)
                    rt.FBXExporterSetParam(rt.Name("BakeAnimation"), True)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameStart"), start_frame)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameEnd"), end_frame)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameStep"), 1)
                    rt.FBXExporterSetParam(rt.Name("Shape"), True)
                    rt.FBXExporterSetParam(rt.Name("Skin"), True)
                    rt.FBXExporterSetParam(rt.Name("UpAxis"), rt.Name("Z"))

                    # Export
                    rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)

                    exported_files.append(export_file)
                    logger.info(f"Exported: {export_file}")

                finally:
                    rt.animationRange = rt.interval(original_start, original_end)

            except Exception as e:
                logger.error(f"Failed to export {max_file}: {str(e)}")
                continue

        # Restore original file if available
        if current_max_name and current_max_name != "":
            try:
                logger.info(f"Restoring original file: {current_max_name}")
                full_path = os.path.join(current_max_path, current_max_name)
                rt.loadMaxFile(full_path, quiet=True)
            except Exception as e:
                logger.error(f"Failed to restore original file: {str(e)}")

        _update_progress(100, "Export complete!")

        # Show completion notification
        if exported_files:
            # _show_export_notification(exported_files)
            logger.info(f"Exported {len(exported_files)} files successfully")
        else:
            rt.messageBox("No files were exported!", title="Export Selected")

    except Exception as e:
        _update_progress(0, "Export failed!")
        logger.error(f"Export selected files failed: {str(e)}")
        rt.messageBox(f"Export failed:\n{str(e)}", title="Export Selected Error")


def _batch_export_directory(start_frame, end_frame, export_path):
    """
    Batch export all Max files in the current directory

    Args:
        start_frame: Start frame for animation
        end_frame: End frame for animation
        export_path: FBX export directory path
    """
    try:
        # Get current Max file directory
        current_max_path = rt.maxFilePath
        current_max_name = rt.maxFileName

        if not current_max_path or not current_max_name:
            rt.messageBox("Please save the current file before batch export!", title="Batch Export")
            return

        logger.info(f"Starting batch export from directory: {current_max_path}")

        # Get all .max files in the directory
        import glob
        max_files = glob.glob(os.path.join(current_max_path, "*.max"))
        max_files = [os.path.basename(f) for f in max_files]
        max_files.sort()

        if not max_files:
            rt.messageBox("No Max files found in current directory!", title="Batch Export")
            return

        logger.info(f"Found {len(max_files)} Max files to process: {max_files}")

        # Move current file to front of list
        if current_max_name in max_files:
            max_files.remove(current_max_name)
            max_files.insert(0, current_max_name)

        total_files = len(max_files)
        exported_files = []

        for idx, max_file in enumerate(max_files):
            file_num = idx + 1
            logger.info(f"Processing {file_num}/{total_files}: {max_file}")
            _update_progress(int((file_num - 1) / total_files * 100), f"Processing {file_num}/{total_files}: {max_file}")

            # Get animation name from filename (without extension)
            anim_name = os.path.splitext(max_file)[0]

            # Load file if not current file
            if max_file != current_max_name:
                logger.info(f"Loading file: {max_file}")
                full_path = os.path.join(current_max_path, max_file)

                try:
                    # Load file without saving current
                    rt.loadMaxFile(full_path, quiet=True)
                    logger.info(f"Loaded: {max_file}")
                except Exception as e:
                    logger.error(f"Failed to load {max_file}: {str(e)}")
                    continue

            # Find "Fbx" selection set
            fbx_set = None
            for i in range(rt.selectionSets.count):
                if rt.selectionSets[i].name.lower() == "fbx":
                    fbx_set = rt.selectionSets[i]
                    break

            if not fbx_set:
                logger.warning(f"No 'Fbx' selection set found in {max_file}, skipping...")
                continue

            # Get objects from selection set
            objects_to_export = [obj for obj in fbx_set]

            if not objects_to_export:
                logger.warning(f"'Fbx' selection set is empty in {max_file}, skipping...")
                continue

            # Select objects
            rt.select(objects_to_export)

            # Create pipe-delimited string of object names
            objects_str = "|".join([obj.name for obj in objects_to_export])

            logger.info(f"Exporting {len(objects_to_export)} objects from 'Fbx' set: {[obj.name for obj in objects_to_export]}")

            # Export this animation
            try:
                export_file = os.path.join(export_path, f"{anim_name}.fbx")

                # Check out from P4 if needed
                if not _p4_checkout(export_file):
                    logger.warning(f"P4 checkout failed for {export_file}, continuing anyway...")

                # Remove read-only if file exists
                if os.path.exists(export_file):
                    try:
                        import stat
                        os.chmod(export_file, stat.S_IWRITE | stat.S_IREAD)
                    except Exception as e:
                        logger.warning(f"Failed to remove read-only attribute: {str(e)}")

                # Configure FBX export
                original_start = rt.animationRange.start
                original_end = rt.animationRange.end

                try:
                    rt.animationRange = rt.interval(start_frame, end_frame)

                    rt.FBXExporterSetParam(rt.Name("Animation"), True)
                    rt.FBXExporterSetParam(rt.Name("BakeAnimation"), True)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameStart"), start_frame)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameEnd"), end_frame)
                    rt.FBXExporterSetParam(rt.Name("BakeFrameStep"), 1)
                    rt.FBXExporterSetParam(rt.Name("Shape"), True)
                    rt.FBXExporterSetParam(rt.Name("Skin"), True)
                    rt.FBXExporterSetParam(rt.Name("UpAxis"), rt.Name("Z"))

                    # Export
                    rt.exportFile(export_file, rt.name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)

                    exported_files.append(export_file)
                    logger.info(f"Exported: {export_file}")

                finally:
                    rt.animationRange = rt.interval(original_start, original_end)

            except Exception as e:
                logger.error(f"Failed to export {max_file}: {str(e)}")
                continue

        # Restore original file
        if current_max_name and current_max_name != max_files[-1]:
            try:
                logger.info(f"Restoring original file: {current_max_name}")
                full_path = os.path.join(current_max_path, current_max_name)
                rt.loadMaxFile(full_path, quiet=True)
            except Exception as e:
                logger.error(f"Failed to restore original file: {str(e)}")

        _update_progress(100, "Batch export complete!")

        # Show completion notification
        if exported_files:
            # _show_export_notification(exported_files)
            logger.info(f"Batch export complete: {len(exported_files)} files exported")
        else:
            rt.messageBox("No files were exported!", title="Batch Export")

    except Exception as e:
        _update_progress(0, "Batch export failed!")
        logger.error(f"Batch export failed: {str(e)}")
        rt.messageBox(f"Batch export failed:\n{str(e)}", title="Batch Export Error")


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

            # Show export notification
            # try:
            #     _show_export_notification([export_file])
            # except Exception as e:
            #     logger.error(f"Export notification error: {str(e)}")

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

