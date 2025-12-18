"""
Constraint helper tools
Example rigging tool for xMobu
"""

from pyfbsdk import FBMessageBox, FBModelList
from core.logger import logger

TOOL_NAME = "Constraint Helper"


def execute(control, event):
    """Execute constraint helper tool"""
    logger.info("Opening Constraint Helper...")

    try:
        selected = FBModelList()
        FBGetSelectedModels(selected)

        message = f"Constraint Helper\n\n"
        message += f"Selected objects: {len(selected)}\n\n"
        message += "Quick constraint operations:\n"
        message += "- Parent constraint\n"
        message += "- Position constraint\n"
        message += "- Rotation constraint\n"
        message += "- Aim constraint\n\n"
        message += "Full implementation coming soon!"

        FBMessageBox("Constraint Helper", message, "OK")

    except Exception as e:
        logger.error(f"Constraint Helper error: {str(e)}")
        FBMessageBox("Error", f"An error occurred: {str(e)}", "OK")
