"""
MotionBuilder startup script for MotionKit
This script is automatically executed when MotionBuilder starts
"""

import sys
from pathlib import Path

# Add MotionKit root to Python path
MOTIONKIT_ROOT = Path(__file__).parent.parent
if str(MOTIONKIT_ROOT) not in sys.path:
    sys.path.insert(0, str(MOTIONKIT_ROOT))

from core.logger import logger
from core.config import config
from mobu.menu_builder import MenuBuilder


def initialize():
    """
    Initialize MotionKit for MotionBuilder
    Called automatically on MotionBuilder startup
    """
    print("[MotionKit] ========================================")
    print("[MotionKit] Starting MotionKit initialization...")
    print(f"[MotionKit] Version: 1.0.0")
    print(f"[MotionKit] Root directory: {MOTIONKIT_ROOT}")
    print("[MotionKit] ========================================")

    try:
        # Check MotionBuilder version
        print("[MotionKit] Checking MotionBuilder version...")
        from core.utils import get_mobu_version
        mobu_version = get_mobu_version()

        if mobu_version:
            print(f"[MotionKit] MotionBuilder version detected: {mobu_version}")

            if mobu_version < 2020:
                print("[MotionKit] WARNING: This version is older than 2020")
                print("[MotionKit] WARNING: Some features may not work correctly")
                logger.warning(
                    f"MotionBuilder {mobu_version} detected. "
                    "MotionKit is designed for MotionBuilder 2020+. "
                    "Some features may not work correctly."
                )
            else:
                print("[MotionKit] Version check passed")
        else:
            print("[MotionKit] WARNING: Could not determine MotionBuilder version")

        # Load configuration
        print("[MotionKit] Loading configuration...")
        menu_name = config.get('mobu.menu_name', 'MotionKit')
        categories = config.get('mobu.tool_categories', [])
        print(f"[MotionKit] Menu name: {menu_name}")
        print(f"[MotionKit] Enabled categories: {len([c for c in categories if c.get('enabled', True)])}")

        # Build the menu system
        print("[MotionKit] Building menu system...")
        menu_builder = MenuBuilder()
        menu_builder.build_menu()

        print("[MotionKit] ========================================")
        print("[MotionKit] Initialization completed successfully!")
        print(f"[MotionKit] Look for '{menu_name}' menu in the menu bar")
        print("[MotionKit] ========================================")

        logger.info("MotionKit initialized successfully!")

    except ImportError as e:
        print("[MotionKit ERROR] ========================================")
        print(f"[MotionKit ERROR] Import failed: {str(e)}")
        print("[MotionKit ERROR] ========================================")
        print("[MotionKit ERROR] Possible causes:")
        print("[MotionKit ERROR] - Missing MotionKit files")
        print("[MotionKit ERROR] - Incorrect Python path")
        print("[MotionKit ERROR] - Corrupted installation")
        print("[MotionKit ERROR] ========================================")
        logger.error(f"Failed to initialize MotionKit: {str(e)}")
        import traceback
        traceback.print_exc()

    except Exception as e:
        print("[MotionKit ERROR] ========================================")
        print(f"[MotionKit ERROR] Initialization failed: {str(e)}")
        print("[MotionKit ERROR] ========================================")
        logger.error(f"Failed to initialize MotionKit: {str(e)}")
        import traceback
        traceback.print_exc()


# Auto-initialize when this module is imported
if __name__ != "__main__":
    initialize()
