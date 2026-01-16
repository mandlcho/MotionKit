"""
3ds Max startup script for MotionKit
This script is automatically executed when 3ds Max starts via motionkit_init.ms
"""

import sys
from pathlib import Path

# Add MotionKit root to Python path
MOTIONKIT_ROOT = Path(__file__).parent.parent
if str(MOTIONKIT_ROOT) not in sys.path:
    sys.path.insert(0, str(MOTIONKIT_ROOT))

from core.logger import logger
from core.config import config


def initialize():
    """
    Initialize MotionKit for 3ds Max
    Called automatically on 3ds Max startup
    """
    print("[MotionKit] ========================================")
    print("[MotionKit] Starting MotionKit initialization...")
    print(f"[MotionKit] Version: 1.0.0")
    print(f"[MotionKit] Root directory: {MOTIONKIT_ROOT}")
    print("[MotionKit] ========================================")

    try:
        # Check 3ds Max version
        print("[MotionKit] Checking 3ds Max version...")
        try:
            import pymxs
            rt = pymxs.runtime
            max_version = rt.maxVersion()[0]
            print(f"[MotionKit] 3ds Max version detected: {max_version}")
        except Exception as e:
            print(f"[MotionKit] WARNING: Could not determine 3ds Max version: {e}")

        # Load configuration
        print("[MotionKit] Loading configuration...")
        menu_name = config.get('max.menu_name', 'MotionKit')
        categories = config.get('max.tool_categories', [])
        print(f"[MotionKit] Menu name: {menu_name}")
        print(f"[MotionKit] Enabled categories: {len([c for c in categories if c.get('enabled', True)])}")

        # Build the menu system
        print("[MotionKit] Building menu system...")
        from max.menu_builder import MenuBuilder
        menu_builder = MenuBuilder()
        menu_builder.build()

        print("[MotionKit] ========================================")
        print("[MotionKit] Initialization completed successfully!")
        print(f"[MotionKit] Look for '{menu_name}' menu in the menu bar")
        print("[MotionKit] ========================================")

        logger.info("MotionKit initialized successfully for 3ds Max!")

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
