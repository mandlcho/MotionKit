"""
Scene Cleaner
Removes unknown nodes and unknown plugin references that block Maya from saving.
"""

import maya.cmds as cmds
from maya import OpenMayaUI as omui
from qt_compat import TOOL_WINDOW_FLAG, QtCore, QtWidgets, wrapInstance


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


def clean_scene():
    log = []

    unknown_nodes = (cmds.ls(type='unknown') or []) + (cmds.ls(type='unknownTransform') or [])
    if unknown_nodes:
        cmds.delete(unknown_nodes)
        msg = 'Deleted {} unknown node(s): {}'.format(len(unknown_nodes), ', '.join(unknown_nodes))
        log.append(msg)
        print('[scene_cleaner] ' + msg)
    else:
        log.append('No unknown nodes found.')

    unknown_plugins = cmds.unknownPlugin(query=True, list=True) or []
    removed_plugins = []
    failed_plugins  = []
    for p in unknown_plugins:
        try:
            cmds.unknownPlugin(p, remove=True)
            removed_plugins.append(p)
        except Exception as e:
            failed_plugins.append('{} ({})'.format(p, e))

    if removed_plugins:
        msg = 'Removed {} unknown plugin ref(s): {}'.format(len(removed_plugins), ', '.join(removed_plugins))
        log.append(msg)
        print('[scene_cleaner] ' + msg)
    if failed_plugins:
        msg = 'Could not remove: {}'.format(', '.join(failed_plugins))
        log.append(msg)
        print('[scene_cleaner] WARNING ' + msg)
    if not unknown_plugins:
        log.append('No unknown plugin references found.')

    return log


class SceneCleanerUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SceneCleanerUI, self).__init__(parent or _maya_main_window())
        self.setWindowTitle('Scene Cleaner')
        self.setFixedWidth(420)
        self.setWindowFlags(self.windowFlags() | TOOL_WINDOW_FLAG)
        self._build()

    def _build(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(8)
        lay.setContentsMargins(10, 10, 10, 10)

        info = QtWidgets.QLabel(
            'Removes unknown nodes and unknown plugin references\n'
            'that prevent Maya from saving the scene.'
        )
        info.setStyleSheet('color: #888; font-size: 11px;')
        info.setWordWrap(True)
        lay.addWidget(info)

        btn = QtWidgets.QPushButton('Clean Scene')
        btn.setFixedHeight(36)
        btn.setStyleSheet(
            'QPushButton { background: #6b2d2d; color: white; border-radius: 4px; font-size: 13px; }'
            'QPushButton:hover { background: #8a3a3a; }'
            'QPushButton:pressed { background: #4d1f1f; }'
        )
        btn.clicked.connect(self._run)
        lay.addWidget(btn)

        self._log = QtWidgets.QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFixedHeight(120)
        self._log.setStyleSheet(
            'QTextEdit { background: #1a1a1a; color: #aaa; border: 1px solid #333;'
            ' border-radius: 3px; font-size: 11px; font-family: Consolas, monospace; }'
        )
        lay.addWidget(self._log)

    def _run(self):
        self._log.clear()
        lines = clean_scene()
        self._log.setPlainText('\n'.join(lines))


def show():
    global _win
    try:
        _win.close()
        _win.deleteLater()
    except Exception:
        pass
    _win = SceneCleanerUI()
    _win.show()
