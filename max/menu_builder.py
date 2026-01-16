"""
Menu builder for 3ds Max integration
Dynamically builds menus from tool files in the tools/ directory
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
    """Builds MotionKit menu structure in 3ds Max"""

    def __init__(self):
        self.menu_name = config.get('max.menu_name', 'MotionKit')
        self.tool_categories = config.get('max.tool_categories', [])
        self.main_menu = None

    def build(self):
        """Build the complete MotionKit menu"""
        if not pymxs or not rt:
            logger.error("Cannot build menu - pymxs not available")
            return False

        try:
            logger.info("Building MotionKit menu system for 3ds Max...")

            # Get the main menu bar
            main_menu_bar = rt.menuMan.getMainMenuBar()

            # Check if MotionKit menu already exists
            existing_menu = None
            for i in range(main_menu_bar.numMenus()):
                menu = main_menu_bar.getMenu(i + 1)  # MaxScript is 1-indexed
                if menu.getTitle() == self.menu_name:
                    existing_menu = menu
                    logger.info(f"Menu '{self.menu_name}' already exists, rebuilding...")
                    break

            # Remove existing menu if found
            if existing_menu:
                main_menu_bar.removeMenu(existing_menu)

            # Create new menu
            self.main_menu = rt.menuMan.createMenu(self.menu_name)

            # Build category submenus
            for category in self.tool_categories:
                if category.get('enabled', True):
                    self._build_category(category['name'])

            # Add separator and utilities
            separator = rt.menuMan.createSeparatorItem()
            self.main_menu.addItem(separator, -1)

            self._add_utility_items()

            # Add menu to menu bar
            submenu_item = rt.menuMan.createSubMenuItem(self.menu_name, self.main_menu)
            main_menu_bar.addItem(submenu_item, -1)

            # Update the menu bar
            rt.menuMan.updateMenuBar()

            logger.info(f"✓ Menu '{self.menu_name}' built successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to build menu: {str(e)}")
            traceback.print_exc()
            return False

    def _build_category(self, category_name):
        """Build a tool category submenu"""
        logger.info(f"Building category: {category_name}")

        # Create category folder path
        category_folder = category_name.lower().replace(' ', '_')
        tools_path = Path(__file__).parent / 'tools' / category_folder

        if not tools_path.exists():
            logger.warning(f"Category folder not found: {tools_path}")
            return

        # Find all tool files
        tool_files = [f for f in tools_path.glob('*.py')
                     if f.name != '__init__.py' and not f.name.startswith('_')]

        if not tool_files:
            logger.info(f"  No tools found in {category_name}")
            return

        logger.info(f"  Found {len(tool_files)} tool(s) in {category_name}")

        # Create submenu for this category
        category_menu = rt.menuMan.createMenu(category_name)

        # Load each tool
        tools_loaded = 0
        for tool_file in tool_files:
            if self._load_tool(category_menu, category_folder, tool_file):
                tools_loaded += 1

        # Add category submenu to main menu
        if tools_loaded > 0:
            submenu_item = rt.menuMan.createSubMenuItem(category_name, category_menu)
            self.main_menu.addItem(submenu_item, -1)
            logger.info(f"  ✓ Loaded {tools_loaded}/{len(tool_files)} tools")
        else:
            logger.info(f"  No tools loaded for {category_name}")

    def _load_tool(self, category_menu, category_folder, tool_file):
        """Load a single tool and add it to the menu"""
        try:
            # Import the tool module
            module_name = f"max.tools.{category_folder}.{tool_file.stem}"

            # Remove from sys.modules if already loaded (for reload support)
            if module_name in sys.modules:
                del sys.modules[module_name]

            module = importlib.import_module(module_name)

            # Check for required attributes
            if not hasattr(module, 'TOOL_NAME'):
                logger.warning(f"  ⚠ {tool_file.name} missing TOOL_NAME constant")
                return False

            if not hasattr(module, 'execute'):
                logger.warning(f"  ⚠ {tool_file.name} missing execute() function")
                return False

            tool_name = module.TOOL_NAME

            # Create MaxScript callback that calls Python function
            # We need to store the Python callback globally
            callback_name = f"motionkit_{category_folder}_{tool_file.stem}"

            # Store in globals so MaxScript can call it
            globals()[callback_name] = lambda: module.execute()

            # Create MaxScript action
            action_id = f"MotionKit_{category_folder}_{tool_file.stem}"

            # Register MaxScript macro
            macroscript_code = f'''
            macroScript {action_id}
            category:"MotionKit"
            buttonText:"{tool_name}"
            tooltip:"{tool_name}"
            (
                python.execute "import max.menu_builder; max.menu_builder.{callback_name}()"
            )
            '''

            rt.execute(macroscript_code)

            # Create menu item that runs the macro
            action_item = rt.menuMan.createActionItem(action_id, "MotionKit")
            category_menu.addItem(action_item, -1)

            logger.debug(f"    ✓ {tool_name}")
            return True

        except Exception as e:
            logger.error(f"  ✗ Failed to load {tool_file.name}: {str(e)}")
            traceback.print_exc()
            return False

    def _add_utility_items(self):
        """Add utility menu items (settings, reload, about)"""

        # Reload MotionKit
        reload_callback = lambda: self._reload_motionkit()
        globals()['motionkit_reload'] = reload_callback

        reload_macro = '''
        macroScript MotionKit_Reload
        category:"MotionKit"
        buttonText:"Reload MotionKit"
        tooltip:"Reload MotionKit"
        (
            python.execute "import max.menu_builder; max.menu_builder.motionkit_reload()"
        )
        '''
        rt.execute(reload_macro)
        reload_item = rt.menuMan.createActionItem("MotionKit_Reload", "MotionKit")
        self.main_menu.addItem(reload_item, -1)

        # Separator
        separator = rt.menuMan.createSeparatorItem()
        self.main_menu.addItem(separator, -1)

        # About
        about_callback = lambda: self._show_about()
        globals()['motionkit_about'] = about_callback

        about_macro = '''
        macroScript MotionKit_About
        category:"MotionKit"
        buttonText:"About MotionKit"
        tooltip:"About MotionKit"
        (
            python.execute "import max.menu_builder; max.menu_builder.motionkit_about()"
        )
        '''
        rt.execute(about_macro)
        about_item = rt.menuMan.createActionItem("MotionKit_About", "MotionKit")
        self.main_menu.addItem(about_item, -1)

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
