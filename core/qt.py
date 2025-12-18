"""
Qt-related utilities for loading UI files and managing Qt applications in DCCs.
"""

import sys
from pathlib import Path
from PySide2 import QtWidgets, QtCore
from PySide2.QtUiTools import QUiLoader

# Store references to open tool windows to prevent them from being garbage collected
open_windows = {}


def get_main_window():
    """Get the main window for the current DCC"""
    # In a standalone application, this is the top-level widget
    app = QtWidgets.QApplication.instance()
    if not app:
        return None

    for widget in app.topLevelWidgets():
        if "MotionBuilder" in widget.windowTitle():  # A bit of a hack, but reliable
            return widget
    return None


class UiLoader(QUiLoader):
    """
    Custom UI loader to handle widget promotion and signal/slot connections.
    """
    def __init__(self, base_instance, custom_widgets=None):
        super(UiLoader, self).__init__(base_instance)
        self.base_instance = base_instance
        self.custom_widgets = custom_widgets or {}

    def createWidget(self, class_name, parent=None, name=""):
        if class_name in self.custom_widgets:
            widget = self.custom_widgets[class_name](parent)
        else:
            widget = super(UiLoader, self).createWidget(class_name, parent, name)

        if self.base_instance:
            setattr(self.base_instance, name, widget)

        return widget


def load_ui(ui_file, parent=None):
    """
    Load a .ui file and return the widget.

    Args:
        ui_file (str or Path): Path to the .ui file.
        parent (QWidget): Parent widget for the loaded UI.

    Returns:
        QWidget: The loaded UI widget.
    """
    ui_file = Path(ui_file)
    if not ui_file.exists():
        raise FileNotFoundError(f"Could not find UI file: {ui_file}")

    loader = QUiLoader()
    ui = loader.load(str(ui_file), parent)
    ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    return ui


def show_tool_window(tool_class, name, *args, **kwargs):
    """
    Show a Qt tool window, ensuring it is not garbage collected.
    This function stores a reference to the window in a global dictionary.

    Args:
        tool_class: The class of the window to show.
        name (str): A unique name for the tool instance.
    """
    # Close existing window with the same name
    if name in open_windows:
        try:
            open_windows[name].close()
        except (RuntimeError, ReferenceError):
            pass  # Window was already deleted

    # In DCCs, get the main window as parent
    parent = get_main_window()

    # Create and show the new window
    window = tool_class(parent=parent, *args, **kwargs)
    window.show()

    # Store a reference to it
    open_windows[name] = window
    return window

