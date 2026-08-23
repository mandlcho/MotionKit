"""
userSetup.py
Place this file (or merge its contents) into your Maya scripts directory.
Builds the MotionKit shelf on startup.
"""

import maya.utils

from shelf_builder import build_shelf

maya.utils.executeDeferred(build_shelf)
