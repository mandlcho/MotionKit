"""
Bone Axis Speed Calculator for 3ds Max
Calculates bone movement speed along X, Y, Z axes in meters per second
"""

from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[BoneSpeedCalculator] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger

# Tool constant (required)
TOOL_NAME = "Bone Speed Calculator"


def execute(control=None, event=None):
    """Main execution function called by menu system"""
    if not pymxs or not rt:
        print("[BoneSpeedCalculator] ERROR: Not running in 3ds Max")
        return

    try:
        # Get the path to the MaxScript file
        script_path = Path(__file__).parent / "BoneSpeedCalculator.ms"
        
        if not script_path.exists():
            error_msg = f"MaxScript file not found: {script_path}"
            logger.error(error_msg)
            rt.messageBox(error_msg, title="MotionKit Error")
            return
        
        # Execute the MaxScript file
        logger.info(f"Loading Bone Speed Calculator from {script_path}")
        rt.fileIn(str(script_path))
        
    except Exception as e:
        logger.error(f"Failed to open Bone Speed Calculator: {str(e)}")
        rt.messageBox(
            f"Failed to open Bone Speed Calculator:\n{str(e)}", 
            title="MotionKit Error"
        )
