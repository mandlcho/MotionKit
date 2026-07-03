"""
vtx_tools_menu.py
Adds a "Vtx Tools" menu to Maya's main menu bar.
Called from userSetup.py via executeDeferred.
"""

import importlib
import maya.cmds as cmds
import maya.utils

MENU_ID = "vtxToolsMenu"
_tool    = None
_snapper = None
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
    cmds.menuItem(label="Vtx Copy Paste — Open",   command=lambda *_: open_tool())
    cmds.menuItem(label="Vtx Copy Paste — Reload", command=lambda *_: reload_tool())
    cmds.menuItem(divider=True)
    cmds.menuItem(label="Blendshape Snapper — Open",   command=lambda *_: open_snapper())
    cmds.menuItem(label="Blendshape Snapper — Reload", command=lambda *_: reload_snapper())
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


def open_snapper():
    global _snapper
    import blendshape_snapper

    if _snapper is not None:
        try:
            if _snapper.isVisible():
                _snapper.raise_()
                _snapper.activateWindow()
                return
        except RuntimeError:
            pass

    _snapper = blendshape_snapper.BlendshapeSnapper()
    _snapper.show()


def reload_snapper():
    global _snapper
    import blendshape_snapper

    if _snapper is not None:
        try:
            _snapper.close()
            _snapper.deleteLater()
        except RuntimeError:
            pass
        _snapper = None

    importlib.reload(blendshape_snapper)
    _snapper = blendshape_snapper.BlendshapeSnapper()
    _snapper.show()
    print("[vtxTools] blendshapeSnapper reloaded")
