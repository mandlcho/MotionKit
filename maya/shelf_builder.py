"""Build the MotionKit shelf in Maya."""

import maya.cmds as cmds


SHELF_NAME = "MotionKit"


def _button(label, tooltip, command, background=(0.25, 0.25, 0.25)):
    """Add a command button to the MotionKit shelf."""
    cmds.shelfButton(
        label=label,
        annotation=tooltip,
        imageOverlayLabel=label,
        image="commandButton.png",
        command=command,
        backgroundColor=background,
        parent=SHELF_NAME,
    )


def build_shelf():
    """Replace the current MotionKit shelf with the latest tool buttons."""
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.deleteUI(SHELF_NAME)

    cmds.shelfLayout(SHELF_NAME, parent="ShelfLayout")

    _button(
        "BSExp",
        "BS Anim Export — 导出 blendShape 权重曲线",
        "import bs_anim_export; bs_anim_export.show()",
        (0.22, 0.35, 0.22),
    )
    _button(
        "BSImp",
        "BS Anim Import — 导入 blendShape 权重曲线",
        "import bs_anim_import; bs_anim_import.show()",
        (0.22, 0.30, 0.45),
    )
    _button(
        "BSSnap",
        "Blendshape Snapper — 批量截图",
        "import blendshape_snapper; blendshape_snapper.show()",
        (0.35, 0.28, 0.18),
    )

    cmds.separator(style="shelf", horizontal=False, parent=SHELF_NAME)

    _button(
        "VtxCP",
        "Vtx Copy Paste — 顶点复制粘贴",
        "import vtx_copy_paste; vtx_copy_paste.VtxCopyPaste().show()",
        (0.35, 0.22, 0.35),
    )

    cmds.separator(style="shelf", horizontal=False, parent=SHELF_NAME)

    _button(
        "CleanScn",
        "Scene Cleaner — 删除未知节点和插件引用，修复无法保存的场景",
        "import importlib, scene_cleaner; "
        "importlib.reload(scene_cleaner); scene_cleaner.show()",
        (0.40, 0.18, 0.18),
    )

    print("[MotionKit] shelf built")
