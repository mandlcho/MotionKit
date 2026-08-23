"""
Paste into Maya's Script Editor (Python tab) and run.
Installs the MotionKit shelf in the current session.
"""

import importlib
import sys

# Point Maya at the MotionKit maya/ folder
MOTIONKIT_DIR = r"C:\Users\elementa\projects\MotionKit\maya"
if MOTIONKIT_DIR not in sys.path:
    sys.path.insert(0, MOTIONKIT_DIR)

import shelf_builder

importlib.reload(shelf_builder)
shelf_builder.build_shelf()
