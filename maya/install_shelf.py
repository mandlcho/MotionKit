"""
Paste into Maya's Script Editor (Python tab) and run.
Installs the MotionKit shelf in the current session.
"""

import importlib
import sys
import os

# Point Maya at the MotionKit maya/ folder
MOTIONKIT_DIR = r"C:\Users\elementa\projects\MotionKit\maya"
if MOTIONKIT_DIR not in sys.path:
    sys.path.insert(0, MOTIONKIT_DIR)

import maya.cmds as cmds

SHELF_NAME = "MotionKit"

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


_btn("BSExp",  "BS Anim Export — 导出 blendShape 权重曲线",
     "import bs_anim_export; bs_anim_export.show()",
     bg=(0.22, 0.35, 0.22))

_btn("BSImp",  "BS Anim Import — 导入 blendShape 权重曲线",
     "import bs_anim_import; bs_anim_import.show()",
     bg=(0.22, 0.30, 0.45))

_btn("BSSnap", "Blendshape Snapper — 批量截图",
     "import blendshape_snapper; blendshape_snapper.show()",
     bg=(0.35, 0.28, 0.18))

cmds.separator(style="shelf", horizontal=False, parent=SHELF_NAME)

_btn("VtxCP",  "Vtx Copy Paste — 顶点复制粘贴",
     "import vtx_copy_paste; vtx_copy_paste.VtxCopyPaste().show()",
     bg=(0.35, 0.22, 0.35))

print("[MotionKit] shelf installed")
