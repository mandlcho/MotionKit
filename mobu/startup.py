"""
MotionBuilder startup script for xMobu
This script is automatically executed when MotionBuilder starts
"""

import sys
from pathlib import Path

# Add xMobu root to Python path
XMOBU_ROOT = Path(__file__).parent.parent
if str(XMOBU_ROOT) not in sys.path:
    sys.path.insert(0, str(XMOBU_ROOT))

from core.logger import logger
from core.config import config
from mobu.menu_builder import MenuBuilder


def initialize():
    """
    Initialize xMobu for MotionBuilder
    Called automatically on MotionBuilder startup
    """
    try:
        logger.info("Initializing xMobu...")

        # Check MotionBuilder version
        from core.utils import get_mobu_version
        mobu_version = get_mobu_version()

        if mobu_version and mobu_version < 2020:
            logger.warning(
                f"MotionBuilder {mobu_version} detected. "
                "xMobu is designed for MotionBuilder 2020+. "
                "Some features may not work correctly."
            )

        # Build the menu system
        menu_builder = MenuBuilder()
        menu_builder.build_menu()

        logger.info("xMobu initialized successfully!")

    except Exception as e:
        logger.error(f"Failed to initialize xMobu: {str(e)}")
        import traceback
        traceback.print_exc()


# Auto-initialize when this module is imported
if __name__ != "__main__":
    initialize()
