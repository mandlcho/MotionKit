"""
ONE-CLICK INSTALLER for Max LiveLink in Unreal Engine

This script installs a "Max LiveLink" menu item in Unreal's Tools menu.
Run this ONCE, and the menu item persists across all Unreal sessions.

INSTALLATION:
    1. Open Unreal Engine
    2. Window → Developer Tools → Output Log → Python tab
    3. Paste this entire file and press Enter
    4. Done! Look for "Tools → Max LiveLink" menu

USAGE AFTER INSTALL:
    Just click: Tools → Max LiveLink → Start Server
    
ARTIST-FRIENDLY:
    - No Blueprint knowledge needed
    - No asset copying needed
    - Works in any Unreal project
    - Persists across editor restarts
"""

import unreal
import os
import sys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add to Python path so we can import the server
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def install_max_livelink_menu():
    """Install Max LiveLink menu items in Unreal's Tools menu"""
    
    try:
        # Get the menu system
        menus = unreal.ToolMenus.get()
        
        # Find or create the Tools menu
        main_menu = menus.extend_menu("LevelEditor.MainMenu.Tools")
        
        if not main_menu:
            unreal.log_error("Could not find Tools menu")
            return False
        
        # Create a new section for Max LiveLink
        section = main_menu.add_section(
            section_name="MaxLiveLink",
            label=unreal.Text("Max LiveLink"),
            insert_type=unreal.ToolMenuInsertType.FIRST
        )
        
        # Add "Start Server" menu item
        entry_start = unreal.ToolMenuEntry(
            name="StartMaxLiveLink",
            type=unreal.MultiBlockType.MENU_ENTRY,
            insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.FIRST)
        )
        entry_start.set_label(unreal.Text("▶ Start Max LiveLink Server"))
        entry_start.set_tool_tip(unreal.Text("Start the Max LiveLink server on port 9999"))
        entry_start.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type=unreal.Name(""),
            string="import sys; sys.path.insert(0, r'{}'); from max_live_link_server import start_server; start_server()".format(SCRIPT_DIR)
        )
        section.add_menu_entry("MaxLiveLinkCommands", entry_start)
        
        # Add "Stop Server" menu item
        entry_stop = unreal.ToolMenuEntry(
            name="StopMaxLiveLink",
            type=unreal.MultiBlockType.MENU_ENTRY,
            insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.FIRST)
        )
        entry_stop.set_label(unreal.Text("■ Stop Max LiveLink Server"))
        entry_stop.set_tool_tip(unreal.Text("Stop the Max LiveLink server"))
        entry_stop.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type=unreal.Name(""),
            string="import sys; sys.path.insert(0, r'{}'); from max_live_link_server import stop_server; stop_server()".format(SCRIPT_DIR)
        )
        section.add_menu_entry("MaxLiveLinkCommands", entry_stop)
        
        # Add separator
        separator = unreal.ToolMenuEntry(
            name="MaxLiveLinkSeparator",
            type=unreal.MultiBlockType.SEPARATOR,
            insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.FIRST)
        )
        section.add_menu_entry("MaxLiveLinkCommands", separator)
        
        # Add "Test Connection" menu item
        entry_test = unreal.ToolMenuEntry(
            name="TestMaxLiveLink",
            type=unreal.MultiBlockType.MENU_ENTRY,
            insert_position=unreal.ToolMenuInsert("", unreal.ToolMenuInsertType.FIRST)
        )
        entry_test.set_label(unreal.Text("🔧 Test Connection"))
        entry_test.set_tool_tip(unreal.Text("Check if server is running and show status"))
        entry_test.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_type=unreal.Name(""),
            string="import sys; sys.path.insert(0, r'{}'); from max_live_link_server import get_server_status; status = get_server_status(); unreal.log('Max LiveLink Status: ' + ('RUNNING on port ' + str(status['port']) + ' (' + str(status['clients']) + ' clients)' if status['running'] else 'STOPPED'))".format(SCRIPT_DIR)
        )
        section.add_menu_entry("MaxLiveLinkCommands", entry_test)
        
        # Refresh menus to show changes
        menus.refresh_all_widgets()
        
        unreal.log("=" * 70)
        unreal.log("✓ MAX LIVELINK INSTALLED SUCCESSFULLY!")
        unreal.log("=" * 70)
        unreal.log("")
        unreal.log("Menu items added to: Tools → Max LiveLink")
        unreal.log("")
        unreal.log("Available commands:")
        unreal.log("  • Start Max LiveLink Server  - Start the server")
        unreal.log("  • Stop Max LiveLink Server   - Stop the server")
        unreal.log("  • Test Connection            - Check server status")
        unreal.log("")
        unreal.log("These menu items will persist across editor sessions.")
        unreal.log("=" * 70)
        
        return True
        
    except Exception as e:
        unreal.log_error(f"Failed to install Max LiveLink menu: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# Run installer immediately
if __name__ == '__main__':
    install_max_livelink_menu()
