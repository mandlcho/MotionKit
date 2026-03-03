"""
Build Retarget Map Tool for MotionKit

Analyzes a character scene that has both a Biped and a bone skeleton
(where the Biped drives the bones) and auto-generates a mapping preset
for the FBX Retarget tool.

Workflow:
  1. Open a character Max file that has both Biped and export skeleton.
  2. Run this tool — it finds all Biped nodes and all non-Biped bones.
  3. Matches each Biped node to the nearest bone by world-space position.
  4. Saves the result as a preset JSON in presets/retarget/.

The generated preset maps standard slot names (Hips, Spine, etc.) to
the actual bone names used in the export skeleton. This preset is then
used by the FBX Retarget tool to transfer animation from FBX back onto
the Biped.
"""

import json
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Build Retarget Map] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Build Retarget Map"

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


def _get_presets_dir():
    return Path(__file__).resolve().parent.parent.parent.parent / "presets" / "retarget"


def _save_preset(preset_name, mappings):
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
# Python callbacks for MaxScript
# ---------------------------------------------------------------------------
_state = {
    "mapping_preview": [],   # list of "Slot -> BoneName (dist)" strings
    "mapping": {},           # { slotName: boneName }
    "biped_name": "",
}


def _cb_analyze():
    """Analyze scene: match Biped nodes to nearest non-Biped bones."""
    # Get Biped nodes via biped API
    bip_root = rt.execute('''
    (
        local bipRoot = undefined
        for obj in objects do
        (
            if classOf obj == Biped_Object then
            (
                bipRoot = obj
                exit
            )
        )
        bipRoot
    )
    ''')

    if not bip_root:
        rt.messageBox(t('tools.build_retarget_map.err_no_biped'), title="MotionKit")
        return

    _state["biped_name"] = str(bip_root.name) if bip_root else ""

    # Get export bones from the "Fbx" selection set (the definitive list
    # of bones that get exported to FBX for Unreal).  Fall back to scanning
    # all non-Biped bones if the set doesn't exist.
    non_biped_bones = rt.execute('''
    (
        local bones = #()
        local selSetIdx = 0
        -- Look for a selection set named "Fbx" (case-insensitive)
        for i = 1 to selectionSets.count do
        (
            if toLower (selectionSets[i].name) == "fbx" then
            (
                selSetIdx = i
                exit
            )
        )
        if selSetIdx > 0 then
        (
            -- Use the Fbx selection set directly
            for obj in selectionSets[selSetIdx] do
                append bones obj
        )
        else
        (
            -- Fallback: collect all non-Biped bone-like nodes
            for obj in objects do
            (
                local cls = classOf obj
                if cls != Biped_Object and \\
                   (cls == BoneGeometry or cls == Dummy or cls == Point or \\
                    cls == PointHelperObj or \\
                    (obj.parent != undefined and cls != Editable_Mesh and \\
                     cls != Editable_Poly and cls != PolyMeshObject)) then
                    append bones obj
            )
        )
        #(bones, selSetIdx > 0)
    )
    ''')

    used_selection_set = False
    if non_biped_bones and non_biped_bones.Count == 2:
        bone_array = non_biped_bones[0]
        used_selection_set = bool(non_biped_bones[1])
    else:
        bone_array = non_biped_bones

    if not bone_array or bone_array.Count == 0:
        rt.messageBox(t('tools.build_retarget_map.err_no_bones'), title="MotionKit")
        return

    # Warn if no Fbx selection set
    if not used_selection_set:
        rt.messageBox(
            t('tools.build_retarget_map.warn_no_sel_set'),
            title="MotionKit"
        )
        rt.execute("BuildRetargetMapDialog.statusLabel.text = \"Warning: No 'Fbx' selection set. Using fallback scan...\"")
    else:
        count = str(bone_array.Count)
        rt.execute(f"BuildRetargetMapDialog.statusLabel.text = \"Using 'Fbx' selection set ({count} bones)...\"")
    rt.execute('windows.processPostedMessages()')

    non_biped_bones = bone_array

    # For each standard Biped slot, get the Biped node position and find
    # the nearest non-Biped bone
    mapping = {}
    preview_lines = []
    tolerance = 0.5  # max distance in scene units to consider a match

    for slot, (body_part, link) in BIPED_SLOT_MAP.items():
        # Get biped node for this slot
        if link is None:
            bip_node = rt.execute(
                f'try (biped.getNode ${_state["biped_name"]} #{body_part}) catch(undefined)'
            )
        elif link == 0:
            bip_node = rt.execute(
                f'try (biped.getNode ${_state["biped_name"]} #{body_part}) catch(undefined)'
            )
        else:
            bip_node = rt.execute(
                f'try (biped.getNode ${_state["biped_name"]} #{body_part} link:{link}) catch(undefined)'
            )

        if not bip_node:
            preview_lines.append(f"{slot} -> (no biped node)")
            continue

        bip_pos = bip_node.transform.pos

        # Find nearest non-Biped bone
        best_bone = None
        best_dist = float('inf')

        for i in range(non_biped_bones.Count):
            bone = non_biped_bones[i]
            bone_pos = bone.transform.pos
            dx = float(bip_pos.x) - float(bone_pos.x)
            dy = float(bip_pos.y) - float(bone_pos.y)
            dz = float(bip_pos.z) - float(bone_pos.z)
            dist = (dx*dx + dy*dy + dz*dz) ** 0.5

            if dist < best_dist:
                best_dist = dist
                best_bone = bone

        if best_bone and best_dist <= tolerance:
            bone_name = str(best_bone.name)
            mapping[slot] = bone_name
            preview_lines.append(f"{slot} -> {bone_name}  ({best_dist:.3f})")
        else:
            dist_str = f"{best_dist:.1f}" if best_bone else "N/A"
            preview_lines.append(f"{slot} -> (no match, nearest: {dist_str})")

    _state["mapping"] = mapping
    _state["mapping_preview"] = preview_lines

    # Update UI
    items_str = "|".join(preview_lines)
    rt.execute(f'BuildRetargetMapDialog.mappingListBox.items = filterString "{items_str}" "|"')

    matched = len(mapping)
    total = len(BIPED_SLOT_MAP)
    status = t('tools.build_retarget_map.msg_analyzed').replace("{0}", str(matched)).replace("{1}", str(total))
    rt.execute(f'BuildRetargetMapDialog.statusLabel.text = "{status}"')


def _cb_save():
    """Save the generated mapping as a preset."""
    if not _state["mapping"]:
        rt.messageBox(t('tools.build_retarget_map.err_no_mapping'), title="MotionKit")
        return

    # Get preset name from the edittext
    preset_name = str(rt.execute('BuildRetargetMapDialog.presetNameEdit.text'))
    preset_name = preset_name.strip()

    if not preset_name:
        rt.messageBox(t('tools.build_retarget_map.err_no_name'), title="MotionKit")
        return

    saved_path = _save_preset(preset_name, _state["mapping"])

    matched = len(_state["mapping"])
    msg = t('tools.build_retarget_map.msg_saved').replace("{0}", preset_name).replace("{1}", str(matched))
    rt.execute(f'BuildRetargetMapDialog.statusLabel.text = "{msg}"')
    rt.messageBox(
        f"{msg}\n\n{saved_path}",
        title="MotionKit"
    )


def _register_callbacks():
    import max.tools.animation.build_retarget_map as _self
    _self._cb_analyze = _cb_analyze
    _self._cb_save = _cb_save


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
class BuildRetargetMapDialog:

    def __init__(self):
        self.version = "1.0.0"

    def show(self):
        _register_callbacks()

        title           = t('tools.build_retarget_map.title')
        group_analyze   = t('tools.build_retarget_map.group_analyze')
        btn_analyze     = t('tools.build_retarget_map.btn_analyze')
        group_result    = t('tools.build_retarget_map.group_result')
        group_save      = t('tools.build_retarget_map.group_save')
        lbl_preset_name = t('tools.build_retarget_map.lbl_preset_name')
        btn_save        = t('tools.build_retarget_map.btn_save')
        lbl_info        = t('tools.build_retarget_map.lbl_info')

        maxscript = f'''
-- ============================================
-- MotionKit Build Retarget Map
-- ============================================

rollout BuildRetargetMapDialog "{title}" width:460 height:470
(
    label infoLabel "{lbl_info}" pos:[15,8] width:430 height:20

    button analyzeBtn "{btn_analyze}" pos:[15,32] width:430 height:30

    group "{group_result}"
    (
        listbox mappingListBox "" pos:[15,85] width:430 height:14
        label statusLabel "" pos:[15,315] width:430 height:16
    )

    group "{group_save}"
    (
        label presetNameLbl "{lbl_preset_name}" pos:[15,355] width:85 align:#left
        edittext presetNameEdit "" pos:[100,352] width:225 height:20
        button saveBtn "{btn_save}" pos:[335,351] width:110 height:24
    )

    on BuildRetargetMapDialog open do
    (
        -- Default preset name from scene file name
        local sceneName = getFilenameFile maxFileName
        if sceneName != "" then
            presetNameEdit.text = sceneName
        else
            presetNameEdit.text = "custom_character"
    )

    on analyzeBtn pressed do
        python.execute "import max.tools.animation.build_retarget_map; max.tools.animation.build_retarget_map._cb_analyze()"

    on saveBtn pressed do
        python.execute "import max.tools.animation.build_retarget_map; max.tools.animation.build_retarget_map._cb_save()"

    on BuildRetargetMapDialog close do ()
)

try (destroyDialog BuildRetargetMapDialog) catch()
createDialog BuildRetargetMapDialog
'''

        rt.execute(maxscript)


def execute(control=None, event=None):
    if not pymxs or not rt:
        print("[Build Retarget Map] ERROR: Not running in 3ds Max")
        return
    try:
        BuildRetargetMapDialog().show()
    except Exception as e:
        logger.error(f"Failed to open Build Retarget Map: {str(e)}")
        rt.messageBox(f"Failed to open Build Retarget Map:\n{str(e)}", title="MotionKit Error")
