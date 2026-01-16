"""
Utility functions for xMobu
"""

import sys


def get_dcc_app():
    """
    Detect which DCC application is currently running

    Returns:
        str: 'motionbuilder', 'maya', 'max', or 'standalone'
    """
    if 'pyfbsdk' in sys.modules:
        return 'motionbuilder'
    elif 'maya' in sys.modules or 'maya.cmds' in sys.modules:
        return 'maya'
    elif 'MaxPlus' in sys.modules or 'pymxs' in sys.modules:
        return 'max'
    else:
        return 'standalone'


def is_motionbuilder():
    """Check if currently running in MotionBuilder"""
    return get_dcc_app() == 'motionbuilder'


def is_maya():
    """Check if currently running in Maya"""
    return get_dcc_app() == 'maya'


def is_max():
    """Check if currently running in 3ds Max"""
    return get_dcc_app() == 'max'


def get_mobu_version():
    """
    Get MotionBuilder version

    Returns:
        int: Version year (e.g., 2020, 2023) or None if not in MotionBuilder
    """
    if not is_motionbuilder():
        return None

    try:
        from pyfbsdk import FBSystem
        system = FBSystem()
        version_str = system.Version
        # Extract year from version string (e.g., "2023.0.1" -> 2023)
        return int(version_str.split('.')[0])
    except:
        return None
