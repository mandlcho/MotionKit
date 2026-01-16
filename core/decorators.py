"""
Decorators for the xMobu toolset
"""

from pyfbsdk import ShowTool
from core.logger import logger

# Global registry to track tool instances
_tool_registry = {}

def CreateUniqueTool(tool_class):
    """
    A decorator to ensure that only one instance of a tool is active at a time.
    If an instance already exists, brings it to front instead of creating a new one.
    """
    def wrapper(*args, **kwargs):
        tool_name = tool_class.__name__
        logger.info(f"Launching unique tool: {tool_name}")

        # Check if we have a previous instance in our registry
        if tool_name in _tool_registry:
            existing_tool = _tool_registry[tool_name]
            logger.info(f"Tool already exists, bringing to front: {tool_name}")
            # Bring existing window to front
            ShowTool(existing_tool)
            return existing_tool

        # Create a new instance of the tool
        logger.info(f"Creating new instance of tool: {tool_name}")
        new_tool = tool_class(*args, **kwargs)

        # Store in registry
        _tool_registry[tool_name] = new_tool

        # Show the tool
        ShowTool(new_tool)

        return new_tool

    return wrapper
