"""
UNREAL ENGINE STARTUP SCRIPT for MotionKit
Auto-installs Max LiveLink menu on every UE launch

SETUP (ONE TIME):
    1. Copy this file to: C:\Users\[YourUsername]\Documents\UnrealEngine\Python\init_unreal.py
    2. Restart Unreal Engine
    3. Done! Max LiveLink menu appears automatically in Tools → Max LiveLink

NOTE:
    This path is the official UE Python startup directory as documented here:
    https://docs.unrealengine.com/5.0/en-US/scripting-the-unreal-editor-using-python/
    
    Any .py files in this directory are automatically executed when UE starts.
"""

import unreal
import os
import sys

# Path to MotionKit unreal_scripts directory
MOTIONKIT_DIR = r"C:\Users\elementa\projects\MotionKit\unreal_scripts"

def auto_install_max_livelink():
    """Automatically install Max LiveLink menu on startup"""
    try:
        # Add MotionKit to Python path
        if MOTIONKIT_DIR not in sys.path:
            sys.path.insert(0, MOTIONKIT_DIR)
        
        # Import and run the installer
        from install_max_livelink import install_max_livelink_menu
        
        # Check if already installed (to avoid duplicate menus)
        menus = unreal.ToolMenus.get()
        main_menu = menus.find_menu("LevelEditor.MainMenu.Tools")
        
        if main_menu:
            # Check if our section already exists
            sections = main_menu.get_sections()
            if "MaxLiveLink" not in [str(s) for s in sections]:
                # Not installed yet, install it
                install_max_livelink_menu()
            else:
                unreal.log("[MotionKit] Max LiveLink already installed")
        
    except Exception as e:
        unreal.log_warning(f"[MotionKit] Failed to auto-install Max LiveLink: {str(e)}")
        import traceback
        traceback.print_exc()

# Run on startup
auto_install_max_livelink()
