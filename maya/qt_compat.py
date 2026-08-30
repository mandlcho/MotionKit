"""Qt binding compatibility for supported Maya versions."""

try:
    from PySide6 import QtCore, QtWidgets
    from shiboken6 import wrapInstance

    TOOL_WINDOW_FLAG = QtCore.Qt.WindowType.Tool
    USER_ROLE = QtCore.Qt.ItemDataRole.UserRole
except ImportError:
    from PySide2 import QtCore, QtWidgets
    from shiboken2 import wrapInstance

    TOOL_WINDOW_FLAG = QtCore.Qt.Tool
    USER_ROLE = QtCore.Qt.UserRole


__all__ = (
    "QtCore",
    "QtWidgets",
    "TOOL_WINDOW_FLAG",
    "USER_ROLE",
    "wrapInstance",
)
