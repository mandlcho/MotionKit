"""Build the MotionKit menu in Maya's main menu bar."""

import importlib

import maya.cmds as cmds
import maya.utils


MENU_ID = "motionKitMenu"
MENU_LABEL = "MotionKit"
_build_tries = 0
_MAX_BUILD_TRIES = 20


def build_menu():
    """Create the MotionKit menu when Maya's main window is available."""
    global _build_tries
    _build_tries += 1

    if not cmds.window("MayaWindow", exists=True):
        if _build_tries < _MAX_BUILD_TRIES:
            maya.utils.executeDeferred(build_menu)
        else:
            print("[MotionKit] ERROR: MayaWindow was not ready for menu creation")
        return

    if cmds.menu(MENU_ID, exists=True):
        cmds.deleteUI(MENU_ID)

    menu = cmds.menu(MENU_ID, label=MENU_LABEL, parent="MayaWindow", tearOff=False)
    blendshape_menu = cmds.menuItem(label="Blendshape", subMenu=True, parent=menu)
    _add_tool(blendshape_menu, "Animation Export", "bs_anim_export")
    _add_tool(blendshape_menu, "Animation Import", "bs_anim_import")
    _add_tool(blendshape_menu, "Snapper", "blendshape_snapper")

    utilities_menu = cmds.menuItem(label="Utilities", subMenu=True, parent=menu)
    _add_tool(utilities_menu, "Vertex Copy Paste", "vtx_copy_paste", "VtxCopyPaste")
    _add_tool(utilities_menu, "Scene Cleaner", "scene_cleaner")

    cmds.menuItem(divider=True, parent=menu)
    cmds.menuItem(label="Rebuild Menu", parent=menu, command=lambda *_: build_menu())
    print("[MotionKit] menu built")


def _add_tool(parent, label, module_name, class_name=None):
    """Add a menu item that opens a MotionKit tool on demand."""
    cmds.menuItem(
        label=label,
        parent=parent,
        command=lambda *_: open_tool(module_name, class_name),
    )


def open_tool(module_name, class_name=None):
    """Import and open a MotionKit tool, reporting import or launch errors."""
    try:
        module = importlib.import_module(module_name)
        if class_name:
            getattr(module, class_name)().show()
        else:
            module.show()
    except Exception as error:
        message = "Could not open {}: {}".format(module_name, error)
        print("[MotionKit] ERROR: " + message)
        cmds.warning("[MotionKit] " + message)
