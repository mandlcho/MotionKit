"""
FBX Retarget to Biped Tool for MotionKit

Imports FBX bone animation and retargets it onto a 3ds Max Biped character.

Workflow:
  1. Select FBX file(s) — default path from config, or browse file/folder.
  2. Pick the target Biped from a dropdown of scene Bipeds.
  3. Auto-detect or manually configure bone name mapping.
     Save/load mapping presets for reuse across different source skeletons.
  4. Click Retarget — animation is transferred frame-by-frame using
     rest-pose offset compensation for correct results even when
     source and target have different rest poses.

Transfer pipeline:
  Phase 1 — importFBX: import FBX as scene nodes (no skin, animation only).
  Phase 2 — buildMapping: match source FBX bones to Biped nodes via
             auto-detection or preset, with manual override support.
  Phase 3 — computeOffsets: at reference frame, compute rotation offset
             per bone pair so different rest poses transfer correctly.
  Phase 4 — transferAnimation: per-frame loop writing transforms via
             biped.setTransform (world space).
  Phase 5 — cleanup: delete imported FBX nodes.
"""

import json
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[FBX Retarget] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t
from core.config import config

TOOL_NAME = "FBX Retarget to Biped"

# ---------------------------------------------------------------------------
# Bone name patterns for auto-detection (from MoBu auto_characterize.py)
# Keys = standard slot names, values = common FBX bone name variants (lowercase)
# ---------------------------------------------------------------------------
BONE_NAME_PATTERNS = {
    "Hips":          ["hips", "pelvis", "hip"],
    "Spine":         ["spine", "spine1", "spine_01"],
    "Spine1":        ["spine1", "spine2", "spine_02"],
    "Spine2":        ["spine2", "spine3", "spine_03"],
    "Neck":          ["neck", "neck1", "neck_01"],
    "Head":          ["head"],
    "LeftShoulder":  ["leftshoulder", "l_shoulder", "shoulder_l", "clavicle_l", "l_clavicle"],
    "LeftArm":       ["leftarm", "l_arm", "arm_l", "upperarm_l", "l_upperarm"],
    "LeftForeArm":   ["leftforearm", "l_forearm", "forearm_l", "lowerarm_l", "l_lowerarm"],
    "LeftHand":      ["lefthand", "l_hand", "hand_l"],
    "RightShoulder": ["rightshoulder", "r_shoulder", "shoulder_r", "clavicle_r", "r_clavicle"],
    "RightArm":      ["rightarm", "r_arm", "arm_r", "upperarm_r", "r_upperarm"],
    "RightForeArm":  ["rightforearm", "r_forearm", "forearm_r", "lowerarm_r", "r_lowerarm"],
    "RightHand":     ["righthand", "r_hand", "hand_r"],
    "LeftUpLeg":     ["leftupleg", "l_upleg", "upleg_l", "thigh_l", "l_thigh"],
    "LeftLeg":       ["leftleg", "l_leg", "leg_l", "calf_l", "l_calf", "shin_l", "l_shin"],
    "LeftFoot":      ["leftfoot", "l_foot", "foot_l"],
    "LeftToeBase":   ["lefttoebase", "l_toe", "toe_l", "l_ball", "ball_l"],
    "RightUpLeg":    ["rightupleg", "r_upleg", "upleg_r", "thigh_r", "r_thigh"],
    "RightLeg":      ["rightleg", "r_leg", "leg_r", "calf_r", "r_calf", "shin_r", "r_shin"],
    "RightFoot":     ["rightfoot", "r_foot", "foot_r"],
    "RightToeBase":  ["righttoebase", "r_toe", "toe_r", "r_ball", "ball_r"],
}

# Standard slot → biped.getNode arguments
# Format: (bodyPart, link) where link=None means no link arg
BIPED_SLOT_MAP = {
    "Hips":          ("pelvis", None),
    "Spine":         ("spine", 1),
    "Spine1":        ("spine", 2),
    "Spine2":        ("spine", 3),
    "Neck":          ("neck", 1),
    "Head":          ("head", None),
    "LeftShoulder":  ("larm", 0),
    "LeftArm":       ("larm", 1),
    "LeftForeArm":   ("larm", 2),
    "LeftHand":      ("larm", 3),
    "RightShoulder": ("rarm", 0),
    "RightArm":      ("rarm", 1),
    "RightForeArm":  ("rarm", 2),
    "RightHand":     ("rarm", 3),
    "LeftUpLeg":     ("lleg", 1),
    "LeftLeg":       ("lleg", 2),
    "LeftFoot":      ("lleg", 3),
    "LeftToeBase":   ("lleg", 4),
    "RightUpLeg":    ("rleg", 1),
    "RightLeg":      ("rleg", 2),
    "RightFoot":     ("rleg", 3),
    "RightToeBase":  ("rleg", 4),
}

# ---------------------------------------------------------------------------
# Global state — accessible from MaxScript callbacks via python.execute
# ---------------------------------------------------------------------------
_state = {
    "fbx_files": [],        # list of FBX file paths
    "source_bones": [],     # bone names from imported FBX
    "mapping": {},          # { slotName: sourceBoneName }
    "preset_names": [],     # available preset file names
    "biped_names": [],      # Biped root names in scene
    "selected_biped": None, # name of selected Biped root
    "imported_nodes": [],   # MaxScript node names for cleanup
}


# ---------------------------------------------------------------------------
# Preset helpers
# ---------------------------------------------------------------------------
def _get_presets_dir():
    """Return the retarget presets directory path."""
    return Path(__file__).resolve().parent.parent.parent.parent / "presets" / "retarget"


def _list_presets():
    """Return list of preset names (without .json extension)."""
    presets_dir = _get_presets_dir()
    if not presets_dir.exists():
        return []
    return sorted([f.stem for f in presets_dir.glob("*.json")])


def _load_preset(preset_name):
    """Load a preset JSON and return the mappings dict."""
    preset_path = _get_presets_dir() / f"{preset_name}.json"
    if not preset_path.exists():
        return {}
    with open(preset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("mappings", {})


def _save_preset(preset_name, mappings):
    """Save mappings to a preset JSON file."""
    presets_dir = _get_presets_dir()
    presets_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "name": preset_name,
        "version": "1.0",
        "mappings": mappings
    }
    preset_path = presets_dir / f"{preset_name}.json"
    with open(preset_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(preset_path)


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------
def _strip_namespace(bone_name):
    """Remove namespace prefix (e.g. 'Character1:Hips' → 'Hips')."""
    if ":" in bone_name:
        return bone_name.split(":")[-1]
    return bone_name


def _auto_detect_mapping(source_bone_names):
    """
    Match source FBX bone names to standard slots using BONE_NAME_PATTERNS.
    Returns dict: { slotName: sourceBoneName }.
    """
    mapping = {}
    stripped = {name: _strip_namespace(name).lower() for name in source_bone_names}

    for slot, patterns in BONE_NAME_PATTERNS.items():
        # Pass 1: exact match (lowered, stripped)
        for bone_name, stripped_lower in stripped.items():
            if stripped_lower in patterns:
                mapping[slot] = bone_name
                break
        if slot in mapping:
            continue
        # Pass 2: substring match
        for bone_name, stripped_lower in stripped.items():
            for pattern in patterns:
                if pattern in stripped_lower:
                    mapping[slot] = bone_name
                    break
            if slot in mapping:
                break

    return mapping


# ---------------------------------------------------------------------------
# Python callbacks called from MaxScript via python.execute
# ---------------------------------------------------------------------------
def _cb_browse_folder():
    """Open folder dialog, scan for FBX files and populate listbox."""
    result = rt.getSavePath(caption="Select FBX Folder")
    if result:
        _scan_folder(str(result))


def _scan_folder(folder_path):
    """Scan a folder for FBX files and update the UI."""
    folder = Path(folder_path)
    if not folder.exists():
        return
    fbx_files = sorted(folder.glob("*.fbx"))
    _state["fbx_files"] = [str(f) for f in fbx_files]
    escaped = str(folder).replace("\\", "\\\\")
    rt.execute(f'FBXRetargetDialog.fbxPathEdit.text = "{escaped}"')
    if fbx_files:
        items_str = "|".join([f.name for f in fbx_files])
        rt.execute(f'FBXRetargetDialog.fbxListBox.items = filterString "{items_str}" "|"')
        rt.execute('FBXRetargetDialog.fbxListBox.selection = 1')
    else:
        rt.execute('FBXRetargetDialog.fbxListBox.items = #("(No FBX files found)")')


def _cb_refresh_bipeds():
    """Scan scene for Biped roots and update the dropdown."""
    biped_names = []
    # Collect unique biped root names via MaxScript
    ms_result = rt.execute('''
    (
        local bipRoots = #()
        for obj in objects do
        (
            if classOf obj == Biped_Object then
            (
                local rootNode = obj
                try ( rootNode = biped.getNode obj #pelvis ) catch()
                if rootNode == undefined then rootNode = obj
                -- Walk up to find the actual COM
                try
                (
                    local comNode = rootNode
                    while comNode.parent != undefined and classOf comNode.parent == Biped_Object do
                        comNode = comNode.parent
                    rootNode = comNode
                )
                catch()
                local rName = rootNode.name
                if (findItem bipRoots rName) == 0 then
                    append bipRoots rName
            )
        )
        bipRoots
    )
    ''')
    if ms_result:
        for i in range(ms_result.Count):
            biped_names.append(str(ms_result[i]))

    _state["biped_names"] = biped_names
    if biped_names:
        items_str = "|".join(biped_names)
        rt.execute(f'FBXRetargetDialog.bipedDropdown.items = filterString "{items_str}" "|"')
        rt.execute(f'FBXRetargetDialog.bipedDropdown.selection = 1')
        _state["selected_biped"] = biped_names[0]
    else:
        rt.execute('FBXRetargetDialog.bipedDropdown.items = #("(No Biped found)")')


def _cb_biped_selected(index):
    """Called when user picks a biped from the dropdown."""
    idx = int(index) - 1  # MaxScript is 1-based
    if 0 <= idx < len(_state["biped_names"]):
        _state["selected_biped"] = _state["biped_names"][idx]


def _cb_load_preset():
    """Load selected preset and update mapping."""
    preset_idx = rt.execute('FBXRetargetDialog.presetDropdown.selection')
    if not preset_idx or int(preset_idx) < 1:
        return
    preset_names = _list_presets()
    idx = int(preset_idx) - 1
    if idx >= len(preset_names):
        return
    preset_name = preset_names[idx]
    mappings = _load_preset(preset_name)
    if mappings:
        _state["mapping"] = mappings
        _update_mapping_ui()
        status_msg = t('tools.fbx_retarget.msg_preset_loaded').replace("{0}", preset_name)
        rt.execute(f'FBXRetargetDialog.statusLabel.text = "{status_msg}"')


def _cb_save_preset():
    """Save current mapping as a preset."""
    if not _state["mapping"]:
        rt.messageBox(t('tools.fbx_retarget.err_no_mapping'), title="MotionKit")
        return
    name = rt.execute('''
        local result = ""
        result = getOpenFileName caption:"Save Preset As" types:"JSON Files (*.json)|*.json|"
        if result != undefined then
            (getFilenameFile result)
        else
            ""
    ''')
    if name and str(name) != "":
        preset_name = str(name)
        saved_path = _save_preset(preset_name, _state["mapping"])
        _refresh_preset_list()
        status_msg = t('tools.fbx_retarget.msg_preset_saved').replace("{0}", preset_name)
        rt.execute(f'FBXRetargetDialog.statusLabel.text = "{status_msg}"')


def _cb_retarget():
    """Main retarget execution — import FBX, build mapping, transfer animation."""
    # Validation
    if not _state["fbx_files"]:
        rt.messageBox(t('tools.fbx_retarget.err_no_fbx'), title="MotionKit")
        return
    if not _state["selected_biped"]:
        rt.messageBox(t('tools.fbx_retarget.err_no_biped'), title="MotionKit")
        return
    if not _state["mapping"]:
        rt.messageBox(t('tools.fbx_retarget.err_no_mapping'), title="MotionKit")
        return

    # Get selected FBX
    fbx_idx = rt.execute('FBXRetargetDialog.fbxListBox.selection')
    if fbx_idx and int(fbx_idx) > 0:
        fbx_path = _state["fbx_files"][int(fbx_idx) - 1]
    else:
        fbx_path = _state["fbx_files"][0]

    # Get frame range
    use_timeline = rt.execute('FBXRetargetDialog.useTimelineCB.checked')
    if use_timeline:
        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)
    else:
        start_frame = int(rt.execute('FBXRetargetDialog.startSpn.value'))
        end_frame = int(rt.execute('FBXRetargetDialog.endSpn.value'))

    biped_name = _state["selected_biped"]

    # Build the MaxScript mapping arrays from Python state
    # We need: source bone names and corresponding biped body part info
    mapping_pairs = []
    for slot, src_bone in _state["mapping"].items():
        if slot in BIPED_SLOT_MAP:
            body_part, link = BIPED_SLOT_MAP[slot]
            mapping_pairs.append((src_bone, body_part, link))

    if not mapping_pairs:
        rt.messageBox(t('tools.fbx_retarget.err_no_mapping'), title="MotionKit")
        return

    # Build MaxScript arrays for source names and biped targets
    src_names_ms = ", ".join([f'"{p[0]}"' for p in mapping_pairs])
    body_parts_ms = ", ".join([f'"{p[1]}"' for p in mapping_pairs])
    links_ms = ", ".join([str(p[2]) if p[2] is not None else "-1" for p in mapping_pairs])

    escaped_fbx = fbx_path.replace("\\", "\\\\")
    escaped_biped = biped_name.replace("\\", "\\\\")

    # Status update
    rt.execute(f'FBXRetargetDialog.statusLabel.text = "{t("tools.fbx_retarget.msg_importing")}"')
    rt.execute('FBXRetargetDialog.retargetProgress.value = 5')
    rt.execute('windows.processPostedMessages()')

    maxscript = f'''
    (
        local success = false
        local frameCount = 0
        local boneCount = 0
        local newNodes = #()

        -- Failsafe: save current Biped animation to a temp .bip file
        -- so we can restore it if the retarget fails mid-way.
        local bipBackupPath = ""
        local bipRootForBackup = undefined
        try
        (
            for obj in objects do
            (
                if obj.name == "{escaped_biped}" then
                (
                    bipRootForBackup = obj
                    exit
                )
            )
            if bipRootForBackup != undefined then
            (
                bipBackupPath = (getDir #temp) + "\\\\motionkit_retarget_backup.bip"
                biped.saveBipFile bipRootForBackup bipBackupPath
            )
        )
        catch()

        try
        (
            -- Phase 1: Import FBX
            --   try/catch: some FBX files have embedded MaxScript (ShaDu virus)
            --   that triggers security exceptions. Max blocks the malicious code
            --   but throws — the import itself still succeeds.
            local origObjs = for obj in objects collect obj
            FBXImporterSetParam "Animation" true
            FBXImporterSetParam "Skin" false
            FBXImporterSetParam "Shape" false
            try ( importFile "{escaped_fbx}" #noPrompt using:FBXIMP ) catch()
            newNodes = for obj in objects where (findItem origObjs obj) == 0 collect obj

            if newNodes.count == 0 then
                throw "FBX import returned no nodes"

            -- Build source node lookup by name
            local srcNames  = #({src_names_ms})
            local bodyParts = #({body_parts_ms})
            local links     = #({links_ms})

            -- Find the target biped root
            local bipRoot = undefined
            for obj in objects do
            (
                if obj.name == "{escaped_biped}" then
                (
                    bipRoot = obj
                    exit
                )
            )

            if bipRoot == undefined then
                throw "Could not find Biped: {escaped_biped}"

            -- Figure mode guard
            local inFigure = false
            try ( inFigure = biped.getFigureMode bipRoot ) catch()
            if inFigure then
                throw "{t('tools.fbx_retarget.err_figure_mode')}"

            -- Build mapping: #(#(srcNode, tgtNode), ...)
            local pairs = #()
            for i = 1 to srcNames.count do
            (
                local srcNode = undefined
                for n in newNodes do
                (
                    if n.name == srcNames[i] then
                    (
                        srcNode = n
                        exit
                    )
                )

                local tgtNode = undefined
                try
                (
                    if links[i] == -1 then
                        tgtNode = biped.getNode bipRoot (bodyParts[i] as name)
                    else if links[i] == 0 then
                        tgtNode = biped.getNode bipRoot (bodyParts[i] as name)
                    else
                        tgtNode = biped.getNode bipRoot (bodyParts[i] as name) link:links[i]
                )
                catch()

                if srcNode != undefined and tgtNode != undefined then
                    append pairs #(srcNode, tgtNode)
            )

            boneCount = pairs.count

            FBXRetargetDialog.statusLabel.text = "Mapping " + (boneCount as string) + " bones..."
            FBXRetargetDialog.retargetProgress.value = 15
            windows.processPostedMessages()

            -- Phase 2: Compute rest-pose offsets at frame 0
            local offsets = #()
            local savedTime = sliderTime
            sliderTime = 0

            for p in pairs do
            (
                local srcRest = p[1].transform.rotation
                local tgtRest = p[2].transform.rotation
                local offset  = tgtRest * (inverse srcRest)
                append offsets offset
            )

            FBXRetargetDialog.retargetProgress.value = 20
            windows.processPostedMessages()

            -- Phase 3: Transfer animation frame by frame
            local totalFrames = {end_frame} - {start_frame} + 1
            local cancelled = false

            with undo "FBX Retarget" on
            (
                with animate on
                (
                    for f = {start_frame} to {end_frame} do
                    (
                        if keyboard.escPressed then
                        (
                            cancelled = true
                            exit
                        )

                        sliderTime = f

                        for i = 1 to pairs.count do
                        (
                            local srcNode = pairs[i][1]
                            local tgtNode = pairs[i][2]
                            local srcTM   = srcNode.transform

                            local srcRot  = srcTM.rotation
                            local finalRot = srcRot * offsets[i]
                            try ( biped.setTransform tgtNode #rotation finalRot true ) catch()

                            local srcPos = srcTM.pos
                            try ( biped.setTransform tgtNode #pos srcPos true ) catch()
                        )

                        -- Progress update every 10 frames
                        if mod (f - {start_frame}) 10 == 0 then
                        (
                            local pct = 20 + (80.0 * (f - {start_frame}) / totalFrames) as integer
                            if pct > 100 then pct = 100
                            FBXRetargetDialog.retargetProgress.value = pct
                            windows.processPostedMessages()
                        )
                    )
                )
            )

            sliderTime = savedTime

            if cancelled then
                FBXRetargetDialog.statusLabel.text = "{t('tools.fbx_retarget.msg_cancelled')}"
            else
            (
                frameCount = totalFrames
                success = true
            )
        )
        catch
        (
            local errMsg = getCurrentException()

            -- Restore Biped from backup if we have one
            if bipBackupPath != "" and bipRootForBackup != undefined then
            (
                try
                (
                    biped.loadBipFile bipRootForBackup bipBackupPath
                    FBXRetargetDialog.statusLabel.text = "{t('tools.fbx_retarget.msg_restored')}"
                )
                catch
                (
                    FBXRetargetDialog.statusLabel.text = "{t('tools.fbx_retarget.msg_failed')}"
                )
            )
            else
                FBXRetargetDialog.statusLabel.text = "{t('tools.fbx_retarget.msg_failed')}"

            messageBox errMsg title:"MotionKit"
        )

        -- Phase 4: Cleanup — always runs, even after errors
        if FBXRetargetDialog.cleanupCB.checked and newNodes.count > 0 then
        (
            for n in newNodes do
                try (delete n) catch()
            gc light:true
        )

        if success then
        (
            local doneMsg = "{t('tools.fbx_retarget.msg_done')}"
            doneMsg = substituteString doneMsg "{{0}}" (frameCount as string)
            doneMsg = substituteString doneMsg "{{1}}" (boneCount as string)
            FBXRetargetDialog.statusLabel.text = doneMsg
        )

        -- Clean up temp backup file
        if bipBackupPath != "" then
            try ( deleteFile bipBackupPath ) catch()

        FBXRetargetDialog.retargetProgress.value = 0
    )
    '''

    try:
        rt.execute(maxscript)
    except Exception as e:
        logger.error(f"FBX Retarget failed: {str(e)}")
        rt.execute(f'FBXRetargetDialog.statusLabel.text = "{t("tools.fbx_retarget.msg_failed")}"')
        rt.execute('FBXRetargetDialog.retargetProgress.value = 0')


def _update_mapping_ui():
    """Update the mapping listbox in the UI."""
    items = []
    for slot in BONE_NAME_PATTERNS.keys():
        if slot in _state["mapping"]:
            items.append(f"{slot} -> {_state['mapping'][slot]}")
        else:
            items.append(f"{slot} -> (unmapped)")
    items_str = "|".join(items)
    rt.execute(f'FBXRetargetDialog.mappingListBox.items = filterString "{items_str}" "|"')
    # Update status count
    mapped = sum(1 for s in BONE_NAME_PATTERNS if s in _state["mapping"])
    total = len(BONE_NAME_PATTERNS)
    rt.execute(f'FBXRetargetDialog.mappingStatusLbl.text = "{mapped}/{total} bones mapped"')


def _refresh_preset_list():
    """Refresh the preset dropdown in the UI."""
    _state["preset_names"] = _list_presets()
    if _state["preset_names"]:
        items_str = "|".join(_state["preset_names"])
        rt.execute(f'FBXRetargetDialog.presetDropdown.items = filterString "{items_str}" "|"')
    else:
        rt.execute('FBXRetargetDialog.presetDropdown.items = #("(No presets)")')


# ---------------------------------------------------------------------------
# Register callbacks in global scope so MaxScript can reach them
# ---------------------------------------------------------------------------
def _register_callbacks():
    """Put callback functions into the module's global namespace."""
    import max.tools.animation.fbx_retarget as _self
    _self._cb_browse_folder = _cb_browse_folder
    _self._scan_folder = _scan_folder
    _self._cb_refresh_bipeds = _cb_refresh_bipeds
    _self._cb_biped_selected = _cb_biped_selected
    _self._cb_load_preset = _cb_load_preset
    _self._cb_save_preset = _cb_save_preset
    _self._cb_retarget = _cb_retarget


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
class FBXRetargetDialog:

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        _register_callbacks()

        start_frame = int(rt.animationRange.start.frame)
        end_frame = int(rt.animationRange.end.frame)

        # Default FBX path from config
        default_fbx_path = config.get('export.fbx_path', '')
        if default_fbx_path:
            default_fbx_path = default_fbx_path.replace("\\", "\\\\")

        # Load initial preset list
        _state["preset_names"] = _list_presets()
        preset_items_str = "|".join(_state["preset_names"]) if _state["preset_names"] else "(No presets)"

        # UI strings
        title              = t('tools.fbx_retarget.title')
        group_source       = t('tools.fbx_retarget.group_source')
        lbl_path           = t('tools.fbx_retarget.lbl_path')
        btn_browse         = t('common.browse')
        group_target       = t('tools.fbx_retarget.group_target')
        lbl_biped          = t('tools.fbx_retarget.lbl_biped')
        btn_refresh        = t('tools.fbx_retarget.btn_refresh')
        group_mapping      = t('tools.fbx_retarget.group_mapping')
        lbl_preset         = t('tools.fbx_retarget.lbl_preset')
        btn_save_preset    = t('tools.fbx_retarget.btn_save_preset')
        btn_load_preset    = t('tools.fbx_retarget.btn_load_preset')
        group_options      = t('tools.fbx_retarget.group_options')
        cb_use_timeline    = t('tools.fbx_retarget.cb_use_timeline')
        lbl_start          = t('tools.fbx_retarget.lbl_start')
        lbl_end            = t('tools.fbx_retarget.lbl_end')
        cb_cleanup         = t('tools.fbx_retarget.cb_cleanup')
        btn_retarget       = t('tools.fbx_retarget.btn_retarget')

        maxscript = f'''
-- ============================================
-- MotionKit FBX Retarget to Biped
-- ============================================

rollout FBXRetargetDialog "{title}" width:520 height:555
(
    -- FBX Source
    group "{group_source}"
    (
        label pathLbl "{lbl_path}" pos:[20,22] width:40 align:#left
        edittext fbxPathEdit "" pos:[62,20] width:350 height:20 readOnly:true text:"{default_fbx_path}"
        button browseBtn "{btn_browse}" pos:[418,19] width:82 height:22
        listbox fbxListBox "" pos:[20,46] width:480 height:5
    )

    -- Target Biped
    group "{group_target}"
    (
        label bipedLbl "{lbl_biped}" pos:[20,152] width:50 align:#left
        dropdownList bipedDropdown "" pos:[72,149] width:330 height:21
        button refreshBipedBtn "{btn_refresh}" pos:[410,149] width:90 height:22
    )

    -- Bone Mapping
    group "{group_mapping}"
    (
        label presetLbl "{lbl_preset}" pos:[20,197] width:50 align:#left
        dropdownList presetDropdown "" pos:[72,194] width:220 height:21 items:(filterString "{preset_items_str}" "|")
        button loadPresetBtn "{btn_load_preset}" pos:[300,194] width:95 height:22
        button savePresetBtn "{btn_save_preset}" pos:[400,194] width:100 height:22
        listbox mappingListBox "" pos:[20,222] width:480 height:8
        label mappingStatusLbl "0/{len(BONE_NAME_PATTERNS)} bones mapped" pos:[20,350] width:200 align:#left
    )

    -- Options
    group "{group_options}"
    (
        checkbox useTimelineCB "{cb_use_timeline}" pos:[20,378] width:160 checked:true
        label startLbl "{lbl_start}" pos:[195,378] width:40 align:#left
        spinner startSpn "" pos:[238,376] width:70 height:20 type:#integer range:[-100000,100000,{start_frame}] enabled:false
        label endLbl "{lbl_end}" pos:[320,378] width:35 align:#left
        spinner endSpn "" pos:[355,376] width:70 height:20 type:#integer range:[-100000,100000,{end_frame}] enabled:false
        checkbox cleanupCB "{cb_cleanup}" pos:[20,403] width:400 checked:true
    )

    -- Status & Execute
    label statusLabel "" pos:[20,436] width:480 height:16 align:#center
    progressBar retargetProgress "" pos:[20,456] width:480 height:12 value:0 color:(color 80 160 240)

    button retargetBtn "{btn_retarget}" pos:[20,478] width:480 height:40

    -- Event handlers
    on FBXRetargetDialog open do
    (
        python.execute "import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_refresh_bipeds()"

        -- If default path exists, scan it for FBX files
        local defaultPath = fbxPathEdit.text
        if defaultPath != "" then
        (
            python.execute ("import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._scan_folder('" + (substituteString defaultPath "\\\\" "\\\\\\\\") + "')")
        )
    )

    on browseBtn pressed do
        python.execute "import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_browse_folder()"

    on refreshBipedBtn pressed do
        python.execute "import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_refresh_bipeds()"

    on bipedDropdown selected idx do
        python.execute ("import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_biped_selected(" + (idx as string) + ")")

    on loadPresetBtn pressed do
        python.execute "import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_load_preset()"

    on savePresetBtn pressed do
        python.execute "import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_save_preset()"

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

    on retargetBtn pressed do
        python.execute "import max.tools.animation.fbx_retarget; max.tools.animation.fbx_retarget._cb_retarget()"

    on FBXRetargetDialog close do ()
)

try (destroyDialog FBXRetargetDialog) catch()
createDialog FBXRetargetDialog
'''

        rt.execute(maxscript)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def execute(control=None, event=None):
    if not pymxs or not rt:
        print("[FBX Retarget] ERROR: Not running in 3ds Max")
        return
    try:
        FBXRetargetDialog().show()
    except Exception as e:
        logger.error(f"Failed to open FBX Retarget: {str(e)}")
        rt.messageBox(f"Failed to open FBX Retarget:\n{str(e)}", title="MotionKit Error")
