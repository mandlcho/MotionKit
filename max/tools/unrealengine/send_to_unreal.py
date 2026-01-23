"""
Send selected objects to Unreal Engine
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    rt = None

from core.logger import logger
from core.localization import t

TOOL_NAME = "Send to Unreal"


def get_localized_message(key, *args):
    """Get localized message with optional arguments"""
    try:
        return t(f'tools.send_to_unreal.{key}').format(*args) if args else t(f'tools.send_to_unreal.{key}')
    except:
        # Fallback to English if localization fails
        fallbacks = {
            'error_no_selection': 'Please select at least one object to send to Unreal.',
            'info_selected': 'Send to Unreal - {0} object(s) selected\\n\\nThis feature requires Unreal Engine setup.',
            'error': 'Error: {0}'
        }
        return fallbacks.get(key, key).format(*args) if args else fallbacks.get(key, key)


def execute():
    """Send selected objects to Unreal Engine"""
    try:
        if not rt:
            logger.error("3ds Max runtime not available")
            return

        # Check selection
        selection = rt.selection
        if not selection or selection.count == 0:
            rt.messageBox(get_localized_message("error_no_selection"), title=get_localized_message("title"))
            return

        rt.messageBox(get_localized_message("info_selected", selection.count), title=get_localized_message("title"))
        logger.info(f"Send to Unreal: {selection.count} object(s) selected")

    except Exception as e:
        logger.error(f"Send to Unreal failed: {str(e)}")
        if rt:
            rt.messageBox(get_localized_message("error", str(e)), title=get_localized_message("title") + " Error")
