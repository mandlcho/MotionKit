"""Build the MotionKit menu in Maya's main menu bar."""

import importlib
import sys

import maya.cmds as cmds
import maya.utils


MENU_ID = "motionKitMenu"
MENU_LABEL = "MotionKit"
_build_tries = 0
_MAX_BUILD_TRIES = 20

# Add future tools here. A branch has ``children``; a tool has ``module`` and
# optionally ``class_name`` when it does not expose a module-level show().
MENU_STRUCTURE = (
    {
        "label": "Animation",
        "children": (),
    },
    {
        "label": "Rigging",
        "children": (
            {
                "label": "Blendshape Tools",
                "children": (
                    {"label": "Animation Export", "module": "bs_anim_export"},
                    {"label": "Animation Import", "module": "bs_anim_import"},
                    {"label": "Snapper", "module": "blendshape_snapper"},
                    {
                        "label": "Vertex Copy Paste",
                        "module": "vtx_copy_paste",
                        "class_name": "VtxCopyPaste",
                    },
                ),
            },
            {
                "label": "Bone Tools",
                "children": (),
            },
        ),
    },
    {
        "label": "Validation",
        "children": (
            {"label": "Scene Cleaner", "module": "scene_cleaner"},
        ),
    },
    {
        "label": "P4",
        "children": (),
    },
)


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
    _add_entries(menu, MENU_STRUCTURE)

    cmds.menuItem(divider=True, parent=menu)
    cmds.menuItem(label="Reload Menu", parent=menu, command=lambda *_: reload_menu())
    print("[MotionKit] menu built")


def reload_menu():
    """Reload this module and rebuild the menu for tool development."""
    module = importlib.reload(sys.modules[__name__])
    module.build_menu()


def _add_entries(parent, entries):
    """Recursively add menu branches and tools from the menu definition."""
    for entry in entries:
        module_name = entry.get("module")
        if module_name:
            _add_tool(
                parent,
                entry["label"],
                module_name,
                entry.get("class_name"),
            )
            continue

        submenu = cmds.menuItem(
            label=entry["label"],
            subMenu=True,
            parent=parent,
            tearOff=False,
        )
        children = entry.get("children", ())
        if children:
            _add_entries(submenu, children)
        else:
            cmds.menuItem(label="No tools yet", parent=submenu, enable=False)


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
