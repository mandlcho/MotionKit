"""
vtx_tools_menu.py
Adds a "Vtx Tools" menu to Maya's main menu bar.
Called from userSetup.py via executeDeferred.
"""

import importlib
import maya.cmds as cmds
import maya.utils

MENU_ID = "vtxToolsMenu"
_tool   = None
_build_tries = 0
_MAX_BUILD_TRIES = 20


def build_menu():
    """Create the Vtx Tools menu, deferring if Maya's main window is not ready."""
    global _build_tries
    _build_tries += 1

    if not cmds.window("MayaWindow", exists=True):
        if _build_tries < _MAX_BUILD_TRIES:
            maya.utils.executeDeferred(build_menu)
        else:
            print("[vtxTools] failed: MayaWindow not ready after {} deferred tries".format(_MAX_BUILD_TRIES))
        return

    if cmds.menu(MENU_ID, exists=True):
        cmds.deleteUI(MENU_ID)

    cmds.menu(MENU_ID, label="Vtx Tools", parent="MayaWindow", tearOff=False)
    cmds.menuItem(label="Open",   command=lambda *_: open_tool())
    cmds.menuItem(label="Reload", command=lambda *_: reload_tool())
    print("[vtxTools] menu built")


def open_tool():
    global _tool
    import vtx_copy_paste

    # Raise existing window instead of opening a second one
    if _tool is not None:
        try:
            if _tool.isVisible():
                _tool.raise_()
                _tool.activateWindow()
                return
        except RuntimeError:
            pass  # C++ object already deleted — fall through and create fresh

    _tool = vtx_copy_paste.VtxCopyPaste()
    _tool.show()


def reload_tool():
    global _tool
    import vtx_copy_paste

    # Close existing window
    if _tool is not None:
        try:
            _tool.close()
            _tool.deleteLater()
        except RuntimeError:
            pass
        _tool = None

    # Hot-reload the module so every code change is picked up immediately
    importlib.reload(vtx_copy_paste)

    _tool = vtx_copy_paste.VtxCopyPaste()
    _tool.show()
    print("[vtxTools] reloaded")
