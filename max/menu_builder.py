"""
Menu builder for 3ds Max integration
Dynamically builds menus from tool files in the tools/ directory using MaxScript
"""

import os
import sys
import importlib
import traceback
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[MotionKit] Warning: pymxs not available (running outside 3ds Max?)")
    pymxs = None
    rt = None

from core.config import config
from core.logger import logger


class MenuBuilder:
    """Builds MotionKit menu structure in 3ds Max using MaxScript"""

    def __init__(self):
        self.menu_name = config.get('max.menu_name', 'MotionKit')
        self.tool_categories = config.get('max.tool_categories', [])
        self.tools_registry = {}  # Store Python callbacks

    def build(self):
        """Build the complete MotionKit menu using MaxScript"""
        if not pymxs or not rt:
            logger.error("Cannot build menu - pymxs not available")
            return False

        try:
            logger.info("Building MotionKit menu system for 3ds Max...")

            # Generate MaxScript code to build the menu
            maxscript_code = self._generate_menu_maxscript()

            # Execute the MaxScript
            rt.execute(maxscript_code)

            logger.info(f"✓ Menu '{self.menu_name}' built successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to build menu: {str(e)}")
            traceback.print_exc()
            return False

    def _generate_menu_maxscript(self):
        """Generate MaxScript code to create the entire menu structure"""

        # Start building the MaxScript
        ms = f'''
-- MotionKit Menu Builder
-- Auto-generated menu structure

(
    -- Get the main menu bar
    local mainMenuBar = menuMan.getMainMenuBar()

    -- Remove existing MotionKit menu if it exists
    local existingMenu = menuMan.findMenu "{self.menu_name}"
    if existingMenu != undefined then
    (
        menuMan.unRegisterMenu existingMenu
    )

    -- Create main MotionKit menu
    local motionKitMenu = menuMan.createMenu "{self.menu_name}"

'''

        # Discover and register tools for each category
        for category in self.tool_categories:
            if category.get('enabled', True):
                category_name = category['name']
                ms += self._generate_category_maxscript(category_name)

        # Add utility items
        ms += '''
    -- Add separator
    local sep1 = menuMan.createSeparatorItem()
    motionKitMenu.addItem sep1 -1

'''

        # Add Settings action
        ms += self._generate_settings_maxscript()

        # Add Reload action
        ms += self._generate_reload_maxscript()

        # Add separator and About
        ms += '''
    -- Add separator
    local sep2 = menuMan.createSeparatorItem()
    motionKitMenu.addItem sep2 -1

'''
        ms += self._generate_about_maxscript()

        # Finish the menu
        ms += f'''
    -- Create submenu item and add to main menu bar
    local motionKitSubMenu = menuMan.createSubMenuItem "{self.menu_name}" motionKitMenu

    -- Find a good position (before Help menu if possible)
    local insertPos = mainMenuBar.numItems()
    mainMenuBar.addItem motionKitSubMenu insertPos

    -- Update the menu bar
    menuMan.updateMenuBar()

    format "[MotionKit] Menu added to menu bar\\n"
)
'''

        return ms

    def _generate_category_maxscript(self, category_name):
        """Generate MaxScript for a tool category submenu"""

        category_folder = category_name.lower().replace(' ', '_')
        tools_path = Path(__file__).parent / 'tools' / category_folder

        if not tools_path.exists():
            logger.warning(f"Category folder not found: {tools_path}")
            return ""

        # Find all tool files
        tool_files = [f for f in tools_path.glob('*.py')
                     if f.name != '__init__.py' and not f.name.startswith('_')]

        if not tool_files:
            logger.info(f"  No tools found in {category_name}")
            return ""

        logger.info(f"  Found {len(tool_files)} tool(s) in {category_name}")

        # Create submenu for category
        ms = f'''
    -- Create {category_name} submenu
    local {category_folder}Menu = menuMan.createMenu "{category_name}"

'''

        # Add each tool
        tools_loaded = 0
        for tool_file in tool_files:
            tool_ms = self._generate_tool_maxscript(category_folder, tool_file)
            if tool_ms:
                ms += tool_ms
                tools_loaded += 1

        if tools_loaded > 0:
            # Add category submenu to main menu
            ms += f'''
    -- Add {category_name} submenu to main menu
    local {category_folder}SubMenu = menuMan.createSubMenuItem "{category_name}" {category_folder}Menu
    motionKitMenu.addItem {category_folder}SubMenu -1

'''
            logger.info(f"  ✓ Loaded {tools_loaded}/{len(tool_files)} tools")

        return ms

    def _generate_tool_maxscript(self, category_folder, tool_file):
        """Generate MaxScript macro for a single tool"""

        try:
            # Import the tool module to validate it
            module_name = f"max.tools.{category_folder}.{tool_file.stem}"

            # Remove from sys.modules if already loaded
            if module_name in sys.modules:
                del sys.modules[module_name]

            module = importlib.import_module(module_name)

            # Check for required attributes
            if not hasattr(module, 'TOOL_NAME'):
                logger.warning(f"  ⚠ {tool_file.name} missing TOOL_NAME constant")
                return ""

            if not hasattr(module, 'execute'):
                logger.warning(f"  ⚠ {tool_file.name} missing execute() function")
                return ""

            tool_name = module.TOOL_NAME

            # Register Python callback
            callback_key = f"{category_folder}_{tool_file.stem}"
            self.tools_registry[callback_key] = module.execute

            # Store in global namespace so MaxScript can access it
            globals()[f"motionkit_tool_{callback_key}"] = module.execute

            # Create unique macro ID
            macro_id = f"MotionKit_{category_folder}_{tool_file.stem}"

            # Generate MaxScript macro and menu item
            ms = f'''
    -- Tool: {tool_name}
    macroScript {macro_id}
    category:"MotionKit"
    buttonText:"{tool_name}"
    tooltip:"{tool_name}"
    (
        python.execute "import max.menu_builder; max.menu_builder.motionkit_tool_{callback_key}()"
    )

    local {callback_key}_action = menuMan.createActionItem "{macro_id}" "MotionKit"
    {category_folder}Menu.addItem {callback_key}_action -1

'''

            logger.debug(f"    ✓ {tool_name}")
            return ms

        except Exception as e:
            logger.error(f"  ✗ Failed to load {tool_file.name}: {str(e)}")
            traceback.print_exc()
            return ""

    def _generate_settings_maxscript(self):
        """Generate MaxScript for Settings menu item"""

        # Store settings callback
        def open_settings():
            try:
                from max.tools.pipeline.settings import execute
                execute()
            except Exception as e:
                logger.error(f"Failed to open settings: {str(e)}")
                rt.messageBox(f"Failed to open settings:\n{str(e)}", title="MotionKit Settings Error")

        globals()['motionkit_settings'] = open_settings

        ms = '''
    -- Settings
    macroScript MotionKit_Settings
    category:"MotionKit"
    buttonText:"Settings..."
    tooltip:"Configure MotionKit settings"
    (
        python.execute "import max.menu_builder; max.menu_builder.motionkit_settings()"
    )

    local settings_action = menuMan.createActionItem "MotionKit_Settings" "MotionKit"
    motionKitMenu.addItem settings_action -1

'''
        return ms

    def _generate_reload_maxscript(self):
        """Generate MaxScript for Reload menu item"""

        # Store reload callback
        globals()['motionkit_reload'] = self._reload_motionkit

        ms = '''
    -- Reload MotionKit
    macroScript MotionKit_Reload
    category:"MotionKit"
    buttonText:"Reload MotionKit"
    tooltip:"Reload MotionKit system"
    (
        python.execute "import max.menu_builder; max.menu_builder.motionkit_reload()"
    )

    local reload_action = menuMan.createActionItem "MotionKit_Reload" "MotionKit"
    motionKitMenu.addItem reload_action -1

'''
        return ms

    def _generate_about_maxscript(self):
        """Generate MaxScript for About menu item"""

        # Store about callback
        globals()['motionkit_about'] = self._show_about

        ms = '''
    -- About MotionKit
    macroScript MotionKit_About
    category:"MotionKit"
    buttonText:"About MotionKit"
    tooltip:"About MotionKit"
    (
        python.execute "import max.menu_builder; max.menu_builder.motionkit_about()"
    )

    local about_action = menuMan.createActionItem "MotionKit_About" "MotionKit"
    motionKitMenu.addItem about_action -1

'''
        return ms

    def _reload_motionkit(self):
        """Reload MotionKit system"""
        logger.info("Reloading MotionKit...")
        try:
            # Reload core modules
            import core.logger
            import core.config
            import core.utils
            importlib.reload(core.logger)
            importlib.reload(core.config)
            importlib.reload(core.utils)

            # Rebuild menu
            importlib.reload(sys.modules[__name__])
            from max.menu_builder import MenuBuilder
            builder = MenuBuilder()
            builder.build()

            rt.messageBox("MotionKit reloaded successfully!", title="MotionKit")
            logger.info("✓ Reload complete!")

        except Exception as e:
            logger.error(f"Reload failed: {str(e)}")
            rt.messageBox(f"Failed to reload:\n{str(e)}", title="MotionKit Error")
            traceback.print_exc()

    def _show_about(self):
        """Show about dialog"""
        from core import __version__

        about_text = f"""MotionKit Pipeline Toolset
Version: {__version__}

A comprehensive pipeline toolset for 3ds Max
with support for Animation, Modeling, Rendering,
and Pipeline integration.

Visit github.com/mandlcho/MotionKit for more information.
"""
        rt.messageBox(about_text, title="About MotionKit")


# Global menu builder instance
_menu_builder = None


def build_menu():
    """Build the MotionKit menu (called from startup)"""
    global _menu_builder
    _menu_builder = MenuBuilder()
    return _menu_builder.build()


def get_menu_builder():
    """Get the global menu builder instance"""
    return _menu_builder
