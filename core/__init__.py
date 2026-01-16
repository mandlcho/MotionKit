"""
MotionKit Core Framework
DCC-agnostic core functionality for the MotionKit toolset.
"""

__version__ = "1.0.0"
__author__ = "MotionKit Team"

from .logger import Logger
from .config import ConfigManager
from .utils import get_dcc_app, is_motionbuilder, is_maya, is_max

__all__ = [
    'Logger',
    'ConfigManager',
    'get_dcc_app',
    'is_motionbuilder',
    'is_maya',
    'is_max'
]
