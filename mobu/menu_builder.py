"""
Menu builder for MotionBuilder integration
"""

from pyfbsdk import FBMenuManager, FBGenericMenu
from core.logger import logger
from core.config import config
import importlib
import sys
from pathlib import Path


class MenuBuilder:
    """Builds and manages the MotionKit menu in MotionBuilder"""

    def __init__(self):
        self.menu_manager = FBMenuManager()
        self.menu_name = config.get('mobu.menu_name', 'MotionKit')
        self.main_menu = None

    def build_menu(self):
        """Build the complete MotionKit menu structure"""
        print(f"[MotionKit] Building '{self.menu_name}' menu...")
        logger.info("Building MotionKit menu...")

        # Create main menu
        print(f"[MotionKit] Creating main menu: {self.menu_name}")
        self.main_menu = self.menu_manager.GetMenu(self.menu_name)
        if not self.main_menu:
            self.main_menu = self.menu_manager.InsertLast(None, self.menu_name)
            print(f"[MotionKit] Main menu '{self.menu_name}' created")
        else:
            print(f"[MotionKit] Main menu '{self.menu_name}' already exists")

        # Clear existing items (for reload scenarios)
        self._clear_menu(self.main_menu)

        # Get enabled categories from config
        categories = config.get('mobu.tool_categories', [])
        print(f"[MotionKit] Found {len(categories)} total categories")

        enabled_categories = [c for c in categories if c.get('enabled', True)]
        print(f"[MotionKit] {len(enabled_categories)} categories enabled")

        # Build category submenus
        for category in categories:
            if category.get('enabled', True):
                print(f"[MotionKit] Building category: {category['name']}")
                self._build_category_menu(category['name'])

        # Add separator and utilities
        self.menu_manager.InsertLast(self.menu_name, "")  # Separator
        print("[MotionKit] Adding utility menu items...")
        self._add_utility_items()

        print(f"[MotionKit] Menu '{self.menu_name}' built successfully")
        logger.info("MotionKit menu built successfully")

    def _clear_menu(self, menu):
        """Clear all items from a menu"""
        # Note: MotionBuilder doesn't provide a direct way to clear menus
        # This is a limitation we work around by rebuilding
        pass

    def _build_category_menu(self, category_name):
        """Build a submenu for a specific tool category"""
        print(f"[MotionKit]   Creating submenu: {category_name}")
        # InsertLast expects (parent_menu_name, item_name) - both strings
        category_menu = self.menu_manager.InsertLast(self.menu_name, category_name)

        # Dynamically load tools from the category folder
        tools = self._discover_tools(category_name)

        # Build the category menu path for sub-items
        category_menu_path = f"{self.menu_name}/{category_name}"

        # Store callbacks by menu item name for this category
        category_callbacks = {}

        if not tools:
            # Add placeholder if no tools found
            print(f"[MotionKit]   No tools found for: {category_name}")
            item_name = f"No {category_name} tools found"
            self.menu_manager.InsertLast(category_menu_path, item_name)
            category_callbacks[item_name] = self._no_tools_callback
        else:
            print(f"[MotionKit]   Found {len(tools)} tool(s) in {category_name}")
            # Add each tool to the menu
            for tool in tools:
                self.menu_manager.InsertLast(category_menu_path, tool['name'])
                category_callbacks[tool['name']] = tool['callback']
                print(f"[MotionKit]     - {tool['name']}")

        # Get the category menu and register a single callback handler
        menu_obj = self.menu_manager.GetMenu(category_menu_path)
        if menu_obj:
            # Create a closure that captures the category callbacks
            def menu_handler(control, event):
                callback = category_callbacks.get(event.Name)
                if callback:
                    try:
                        callback(control, event)
                    except Exception as e:
                        print(f"[MotionKit ERROR] Tool '{event.Name}' failed: {str(e)}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[MotionKit] No handler for menu item: {event.Name}")

            menu_obj.OnMenuActivate.Add(menu_handler)
            print(f"[MotionKit]   Registered menu handler for {category_name}")

    def _discover_tools(self, category_name):
        """
        Discover and load tools from a category folder

        Returns:
            list: List of tool dictionaries with 'name' and 'callback'
        """
        tools = []
        category_folder = category_name.lower().replace(' ', '_')

        # Handle special case for "Unreal Engine" category
        if category_folder == 'unreal_engine':
            category_folder = 'unreal'

        tools_path = Path(__file__).parent / 'tools' / category_folder

        print(f"[MotionKit]   Scanning for tools in: {category_folder}/")

        if not tools_path.exists():
            print(f"[MotionKit]   WARNING: Tools folder not found: {tools_path}")
            logger.warning(f"Tools folder not found: {tools_path}")
            return tools

        # Look for Python files in the category folder
        for tool_file in tools_path.glob('*.py'):
            if tool_file.name.startswith('_'):
                continue

            try:
                # Import the tool module
                module_name = f"mobu.tools.{category_folder}.{tool_file.stem}"
                if module_name in sys.modules:
                    # Reload if already imported
                    module = importlib.reload(sys.modules[module_name])
                else:
                    module = importlib.import_module(module_name)

                # Look for tool classes or functions
                if hasattr(module, 'TOOL_NAME') and hasattr(module, 'execute'):
                    tools.append({
                        'name': module.TOOL_NAME,
                        'callback': module.execute
                    })
                    logger.debug(f"Loaded tool: {module.TOOL_NAME}")
                else:
                    print(f"[MotionKit]   WARNING: {tool_file.name} missing TOOL_NAME or execute")

            except Exception as e:
                print(f"[MotionKit]   ERROR: Failed to load {tool_file.name}: {str(e)}")
                logger.error(f"Failed to load tool from {tool_file.name}: {str(e)}")

        return tools

    def _add_utility_items(self):
        """Add utility menu items (settings, reload, about, etc.)"""
        # Build utility callbacks dictionary
        utility_callbacks = {}

        # Settings
        self.menu_manager.InsertLast(self.menu_name, "Settings...")
        utility_callbacks["Settings..."] = self._open_settings

        # Reload
        self.menu_manager.InsertLast(self.menu_name, "Reload MotionKit")
        utility_callbacks["Reload MotionKit"] = self._reload_xmobu

        # Separator
        self.menu_manager.InsertLast(self.menu_name, "")

        # About
        self.menu_manager.InsertLast(self.menu_name, "About MotionKit")
        utility_callbacks["About MotionKit"] = self._show_about

        # Register callback handler for main menu
        main_menu_obj = self.menu_manager.GetMenu(self.menu_name)
        if main_menu_obj:
            def utility_handler(control, event):
                callback = utility_callbacks.get(event.Name)
                if callback:
                    try:
                        callback(control, event)
                    except Exception as e:
                        print(f"[MotionKit ERROR] Utility '{event.Name}' failed: {str(e)}")
                        import traceback
                        traceback.print_exc()

            main_menu_obj.OnMenuActivate.Add(utility_handler)
            print("[MotionKit] Registered utility menu handler")

    def _no_tools_callback(self, control, event):
        """Callback for placeholder menu items"""
        logger.info("No tools available in this category yet")

    def _open_settings(self, control, event):
        """Open settings dialog"""
        try:
            from mobu.tools.pipeline.settings_qt import execute as settings_execute
            settings_execute(control, event)
        except Exception as e:
            from pyfbsdk import FBMessageBox
            logger.error(f"Failed to open settings: {str(e)}")
            FBMessageBox(
                "MotionKit Settings Error",
                f"Failed to open settings:\n{str(e)}\n\n"
                "For now, edit config/config.json to customize MotionKit.",
                "OK"
            )

    def _reload_xmobu(self, control, event):
        """Reload MotionKit system"""
        logger.info("Reloading MotionKit...")
        try:
            # Reload core modules
            import core
            importlib.reload(core)

            # Rebuild menu
            self.build_menu()

            from pyfbsdk import FBMessageBox
            FBMessageBox("MotionKit", "MotionKit reloaded successfully!", "OK")

        except Exception as e:
            logger.error(f"Failed to reload MotionKit: {str(e)}")
            from pyfbsdk import FBMessageBox
            FBMessageBox("MotionKit Error", f"Failed to reload: {str(e)}", "OK")

    def _show_about(self, control, event):
        """Show about dialog"""
        from pyfbsdk import FBMessageBox
        from core import __version__

        about_text = f"""MotionKit Pipeline Toolset
Version: {__version__}

A comprehensive pipeline toolset for 3ds Max
with support for Animation, Modeling, Rendering,
and Pipeline integration.

Visit github.com/mandlcho/MotionKit for more information.
"""
        FBMessageBox("About MotionKit", about_text, "OK")
