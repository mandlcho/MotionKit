"""
Unreal Engine Content Browser Integration
Allows direct push/pull of animation data to/from Unreal Engine
"""

from pyfbsdk import (
    FBMessageBox, FBApplication, FBSystem,
    FBFbxOptions, FBModelList, FBPlayerControl
)
from core.logger import logger
from core.config import config
from pathlib import Path
import subprocess
import json

TOOL_NAME = "UE Content Browser"


class UnrealContentBrowser:
    """Manages communication with Unreal Engine content browser"""

    def __init__(self):
        self.unreal_project = config.get('unreal.default_project_path', '')
        self.content_path = config.get('unreal.content_browser_path', '/Game/')

    def push_animation(self, fbx_path, unreal_path):
        """
        Push animation to Unreal Engine

        Args:
            fbx_path (str): Path to exported FBX file
            unreal_path (str): Target path in Unreal content browser
        """
        logger.info(f"Pushing animation to Unreal: {unreal_path}")

        # This would use Unreal's Python API or command line tools
        # For now, this is a placeholder showing the structure
        try:
            # Example: Using Unreal's commandlet
            # unreal_editor = Path(self.unreal_project).parent / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"

            # In a full implementation, you would:
            # 1. Export FBX from MotionBuilder
            # 2. Call Unreal's Python API or commandlet to import
            # 3. Handle import settings
            # 4. Return success/failure

            logger.info("Animation push completed")
            return True

        except Exception as e:
            logger.error(f"Failed to push animation: {str(e)}")
            return False

    def pull_animation(self, unreal_asset_path):
        """
        Pull animation from Unreal Engine

        Args:
            unreal_asset_path (str): Path to asset in Unreal content browser
        """
        logger.info(f"Pulling animation from Unreal: {unreal_asset_path}")

        try:
            # In a full implementation:
            # 1. Export FBX from Unreal using Python API
            # 2. Import into MotionBuilder
            # 3. Apply to current character/skeleton

            logger.info("Animation pull completed")
            return True

        except Exception as e:
            logger.error(f"Failed to pull animation: {str(e)}")
            return False


def execute(control, event):
    """Execute Unreal Engine content browser integration"""
    logger.info("Opening Unreal Engine Content Browser...")

    try:
        app = FBApplication()
        current_file = app.FBXFileName

        # Check if Unreal project is configured
        unreal_project = config.get('unreal.default_project_path', '')

        message = f"Unreal Engine Content Browser\n\n"

        if unreal_project:
            message += f"Unreal Project: {Path(unreal_project).name}\n\n"
        else:
            message += "No Unreal project configured\n"
            message += "Set 'unreal.default_project_path' in config.json\n\n"

        message += "Features:\n"
        message += "• Push Animation to UE\n"
        message += "  Export selected animation to Unreal content browser\n\n"
        message += "• Pull Animation from UE\n"
        message += "  Import animation from Unreal to current scene\n\n"
        message += "• Batch Export\n"
        message += "  Export multiple takes/characters to Unreal\n\n"
        message += "• Live Link\n"
        message += "  Real-time streaming to Unreal Engine\n\n"

        if current_file:
            message += f"\nCurrent scene: {Path(current_file).name}\n"

        message += "\nFull implementation coming soon!"
        message += "\n\nThis tool will support:"
        message += "\n- Automatic FBX export with UE settings"
        message += "\n- Direct content browser import"
        message += "\n- Metadata preservation"
        message += "\n- Animation retargeting"

        FBMessageBox("Unreal Engine Integration", message, "OK")

        # Future: Show custom UI for browsing Unreal content
        # and selecting import/export options

    except Exception as e:
        logger.error(f"Unreal Content Browser error: {str(e)}")
        FBMessageBox("Error", f"An error occurred: {str(e)}", "OK")


def export_for_unreal(selected_objects=None):
    """
    Export selected objects/animation for Unreal Engine with proper settings

    Args:
        selected_objects: List of objects to export (None = use selection)
    """
    try:
        app = FBApplication()

        if selected_objects is None:
            selected_objects = FBModelList()
            FBGetSelectedModels(selected_objects)

        if len(selected_objects) == 0:
            FBMessageBox(
                "Export to Unreal",
                "Please select objects to export",
                "OK"
            )
            return False

        # Configure FBX export options for Unreal
        fbx_options = FBFbxOptions(True)  # True = export
        fbx_options.SaveSelectedModelsOnly = True
        fbx_options.ShowFileDialog = True
        fbx_options.ShowOptionsDialog = True

        # UE-specific settings
        # fbx_options.EmbedMedia = False
        # fbx_options.UpAxis = FBUpAxis.kFBYAxis

        # Show export dialog
        result = app.FileSave(fbx_options)

        if result:
            logger.info("Export to Unreal completed successfully")
            return True
        else:
            logger.info("Export to Unreal cancelled by user")
            return False

    except Exception as e:
        logger.error(f"Export to Unreal failed: {str(e)}")
        FBMessageBox("Error", f"Export failed: {str(e)}", "OK")
        return False
