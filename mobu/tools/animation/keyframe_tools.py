"""
Keyframe manipulation tools
Example tool demonstrating xMobu tool structure
"""

from pyfbsdk import (
    FBMessageBox, FBModelList, FBSystem,
    FBPlayerControl, FBTime
)
from core.logger import logger

TOOL_NAME = "Keyframe Tools"


def execute(control, event):
    """
    Main execution function for the tool
    This function is called when the menu item is clicked
    """
    logger.info("Opening Keyframe Tools...")

    try:
        # Example: Get selected models
        selected = FBModelList()
        FBGetSelectedModels(selected)

        if len(selected) == 0:
            FBMessageBox(
                "Keyframe Tools",
                "Please select at least one object.",
                "OK"
            )
            return

        # Example tool functionality
        message = f"Keyframe Tools\n\n"
        message += f"Selected objects: {len(selected)}\n\n"
        message += "Available operations:\n"
        message += "- Delete all keys\n"
        message += "- Bake animation\n"
        message += "- Simplify keys\n"
        message += "- Offset keys\n\n"
        message += "Full implementation coming soon!"

        FBMessageBox("Keyframe Tools", message, "OK")

    except Exception as e:
        logger.error(f"Keyframe Tools error: {str(e)}")
        FBMessageBox("Error", f"An error occurred: {str(e)}", "OK")
