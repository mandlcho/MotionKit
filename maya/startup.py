"""MotionKit startup helpers for Maya."""

import platform

import maya.utils

from motionkit_menu import build_menu
from shelf_builder import build_shelf


def get_maya_platform():
    """Return the current Maya host platform in MotionKit-friendly form."""
    system_name = platform.system()
    if system_name == "Darwin":
        return "macOS"
    if system_name == "Windows":
        return "Windows"
    return system_name


def start():
    """Schedule MotionKit's startup UI after Maya has finished loading."""
    host_platform = get_maya_platform()
    print("[MotionKit] starting on {}".format(host_platform))

    if host_platform not in ("macOS", "Windows"):
        print("[MotionKit] WARNING: {} has not been explicitly tested".format(host_platform))

    maya.utils.executeDeferred(build_shelf)
    maya.utils.executeDeferred(build_menu)
