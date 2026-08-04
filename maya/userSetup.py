"""
userSetup.py
Place this file (or merge its contents) into your Maya scripts directory.
Builds the MotionKit shelf on startup.
"""

import maya.utils


def _build_shelf():
    import maya.cmds as cmds

    SHELF_NAME = "MotionKit"

    # Remove and recreate so the shelf is always up to date
    if cmds.shelfLayout(SHELF_NAME, exists=True):
        cmds.deleteUI(SHELF_NAME)

    cmds.shelfLayout(SHELF_NAME, parent="ShelfLayout")

    def _btn(label, tooltip, command, bg=(0.25, 0.25, 0.25)):
        cmds.shelfButton(
            label=label,
            annotation=tooltip,
            imageOverlayLabel=label,
            image="commandButton.png",
            command=command,
            backgroundColor=bg,
            parent=SHELF_NAME,
        )

    # ── Blendshape tools ────────────────────────────────────────────────────
    _btn(
        label="BSExp",
        tooltip="BS Anim Export — 导出 blendShape 权重曲线",
        command="import bs_anim_export; bs_anim_export.show()",
        bg=(0.22, 0.35, 0.22),
    )
    _btn(
        label="BSImp",
        tooltip="BS Anim Import — 导入 blendShape 权重曲线",
        command="import bs_anim_import; bs_anim_import.show()",
        bg=(0.22, 0.30, 0.45),
    )
    _btn(
        label="BSSnap",
        tooltip="Blendshape Snapper — 批量截图",
        command="import blendshape_snapper; blendshape_snapper.show()",
        bg=(0.35, 0.28, 0.18),
    )

    cmds.shelfButton(image="shelf_seperator.png", style="iconOnly",
                     width=8, parent=SHELF_NAME)

    # ── Vtx tools ───────────────────────────────────────────────────────────
    _btn(
        label="VtxCP",
        tooltip="Vtx Copy Paste — 顶点复制粘贴",
        command="import vtx_copy_paste; vtx_copy_paste.VtxCopyPaste().show()",
        bg=(0.35, 0.22, 0.35),
    )

    print("[MotionKit] shelf built")


maya.utils.executeDeferred(_build_shelf)
