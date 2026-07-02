"""
Batch Remove Reference — UI
Browse to a folder, enter the reference node name, click Run.
"""

import os
import glob
import maya.cmds as cmds
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
import shiboken2

WINDOW_ID = "batchRemoveRefWin"


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)


class BatchRemoveRef(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent or _maya_main_window())
        self.setWindowTitle("Batch Remove Reference")
        self.setFixedWidth(340)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # folder
        root.addWidget(self._lbl("FOLDER"))
        folder_row = QtWidgets.QHBoxLayout()
        self._folder = QtWidgets.QLineEdit()
        self._folder.setPlaceholderText("folder of .ma / .mb files")
        self._folder.setFixedHeight(26)
        self._folder.setStyleSheet(self._field_style())
        browse = QtWidgets.QPushButton("…")
        browse.setFixedSize(28, 26)
        browse.setStyleSheet(
            "QPushButton{background:#2a2a2a;color:#aaa;border:1px solid #444;"
            "border-radius:3px;font-size:13px;}"
            "QPushButton:hover{color:#fff;}")
        browse.clicked.connect(self._browse)
        folder_row.addWidget(self._folder)
        folder_row.addWidget(browse)
        root.addLayout(folder_row)

        # ref node name
        root.addWidget(self._lbl("REFERENCE NODE NAME"))
        self._ref_node = QtWidgets.QLineEdit()
        self._ref_node.setPlaceholderText("e.g. Munin_18mRN")
        self._ref_node.setFixedHeight(26)
        self._ref_node.setStyleSheet(self._field_style())
        root.addWidget(self._ref_node)

        # save checkbox
        self._save_cb = QtWidgets.QCheckBox("Save each file after removing")
        self._save_cb.setChecked(True)
        self._save_cb.setStyleSheet("color:#aaa; font-size:11px;")
        root.addWidget(self._save_cb)

        # run
        run_btn = QtWidgets.QPushButton("Run")
        run_btn.setFixedHeight(36)
        run_btn.setStyleSheet(
            "QPushButton{background:#4a2020;color:white;border-radius:4px;font-size:12px;}"
            "QPushButton:hover{background:#6a2a2a;}"
            "QPushButton:pressed{background:#331515;}")
        run_btn.clicked.connect(self._run)
        root.addWidget(run_btn)

        self._status = QtWidgets.QLabel("")
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#555; font-size:10px;")
        root.addWidget(self._status)

    @staticmethod
    def _lbl(text):
        l = QtWidgets.QLabel(text)
        l.setStyleSheet("color:#555; font-size:9px; letter-spacing:1px;")
        return l

    @staticmethod
    def _field_style():
        return ("QLineEdit{background:#2a2a2a;color:#ccc;border:1px solid #444;"
                "border-radius:3px;padding:0 4px;font-size:11px;}"
                "QLineEdit:focus{border-color:#666;}")

    def _set_status(self, msg, color="#aaa"):
        self._status.setText(msg)
        self._status.setStyleSheet(f"color:{color}; font-size:10px;")
        QtWidgets.QApplication.processEvents()

    def _browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select folder of Maya files",
            os.path.expanduser("~"), QtWidgets.QFileDialog.ShowDirsOnly)
        if folder:
            self._folder.setText(folder)

    def _run(self):
        folder   = self._folder.text().strip()
        ref_node = self._ref_node.text().strip()

        if not folder or not os.path.isdir(folder):
            self._set_status("set a valid folder first", "#c87050")
            return
        if not ref_node:
            self._set_status("enter the reference node name", "#c87050")
            return

        files = sorted(
            glob.glob(os.path.join(folder, "*.ma")) +
            glob.glob(os.path.join(folder, "*.mb"))
        )
        if not files:
            self._set_status("no .ma/.mb files found", "#c87050")
            return

        save = self._save_cb.isChecked()
        print(f"[BatchRef] {len(files)} files  ref: {ref_node}  save: {save}")
        ok = 0

        for i, path in enumerate(files):
            self._set_status(f"[{i+1}/{len(files)}] {os.path.basename(path)}...")
            print(f"[BatchRef] opening: {path}")
            try:
                cmds.file(path, open=True, force=True, loadReferenceDepth="all")
            except Exception as e:
                print(f"[BatchRef] ERROR opening: {e}")
                continue

            if not cmds.objExists(ref_node):
                print(f"[BatchRef] '{ref_node}' not found — skipping")
                continue

            try:
                cmds.file(removeReference=True, referenceNode=ref_node)
                print(f"[BatchRef] removed: {ref_node}")
            except Exception as e:
                print(f"[BatchRef] ERROR removing: {e}")
                continue

            if save:
                try:
                    cmds.file(save=True, force=True)
                    print(f"[BatchRef] saved")
                except Exception as e:
                    print(f"[BatchRef] ERROR saving: {e}")
                    continue

            ok += 1

        self._set_status(f"done — {ok}/{len(files)} files processed", "#8fc87a")
        print(f"[BatchRef] done — {ok}/{len(files)}")


if cmds.window(WINDOW_ID, exists=True):
    cmds.deleteUI(WINDOW_ID)

win = BatchRemoveRef()
win.setObjectName(WINDOW_ID)
win.show()
