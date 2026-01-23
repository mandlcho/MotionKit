"""
Send selected objects to Unreal Engine
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    rt = None

from core.logger import logger

TOOL_NAME = "Send to Unreal"


def execute():
    """Send selected objects to Unreal Engine"""
    try:
        if not rt:
            logger.error("3ds Max runtime not available")
            return

        # Check selection
        selection = rt.selection
        if not selection or selection.count == 0:
            rt.messageBox("Please select at least one object to send to Unreal.", title="Send to Unreal")
            return

        rt.messageBox(f"Send to Unreal - {selection.count} object(s) selected\n\nThis feature requires Unreal Engine setup.", title="Send to Unreal")
        logger.info(f"Send to Unreal: {selection.count} object(s) selected")

    except Exception as e:
        logger.error(f"Send to Unreal failed: {str(e)}")
        if rt:
            rt.messageBox(f"Error: {str(e)}", title="Send to Unreal Error")
