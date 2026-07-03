"""
Blendshape Snapper
For each checked blendshape: set weight to 1, capture a screenshot from the
selected camera, save to disk, reset weight to 0.
"""

import os
import maya.cmds as cmds
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
import shiboken2


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)


def _divider():
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setStyleSheet("color:#2a2a2a;")
    return line


def _btn(text, bg, hv, pr):
    b = QtWidgets.QPushButton(text)
    b.setFixedHeight(36)
    b.setStyleSheet(
        f"QPushButton {{ background:{bg}; color:white; border-radius:4px; font-size:12px; }}"
        f"QPushButton:hover {{ background:{hv}; }}"
        f"QPushButton:pressed {{ background:{pr}; }}"
    )
    return b


_FIELD_STYLE = (
    "QLineEdit { background:#2a2a2a; color:#ccc; border:1px solid #444;"
    " border-radius:3px; padding:0 4px; font-size:11px; }"
    "QLineEdit:focus { border-color:#666; }"
)

_CB_STYLE = (
    "QCheckBox { color:#ccc; font-size:11px; }"
    "QCheckBox::indicator { width:13px; height:13px; }"
)

_SECTION_STYLE = "color:#555; font-size:9px; letter-spacing:1px;"


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _scene_cameras():
    """Return list of (transform_name, shape_fullpath) for all non-default cameras."""
    skip = {"perspShape", "topShape", "frontShape", "sideShape",
            "leftShape", "rightShape", "bottomShape", "backShape"}
    result = []
    for shape in (cmds.ls(type="camera", long=True) or []):
        short = shape.split("|")[-1].split(":")[-1]
        if short in skip:
            continue
        parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
        if not parents:
            continue
        transform = parents[0].split("|")[-1]
        result.append((transform, shape))
    return sorted(result, key=lambda x: x[0])


def _blendshape_targets(bs_node):
    aliases = cmds.aliasAttr(bs_node, query=True) or []
    return [aliases[i] for i in range(0, len(aliases), 2)]


def _set_weight(bs_node, target, value):
    cmds.setAttr(f"{bs_node}.{target}", value)


def _capture(camera_transform, output_path):
    """
    Playblast a single PNG from camera_transform.
    output_path should have no extension — playblast appends .####.png.
    Returns the written file path.
    """
    panels = cmds.getPanel(type="modelPanel") or []
    panel = next(
        (p for p in panels
         if cmds.modelEditor(p, q=True, camera=True) == camera_transform),
        panels[0] if panels else None,
    )
    if not panel:
        raise RuntimeError("No model panel available for playblast.")

    current = cmds.currentTime(query=True)
    pb_kwargs = dict(
        filename=output_path,
        format="image",
        compression="png",
        startTime=current,
        endTime=current,
        widthHeight=[1920, 1080],
        percent=100,
        quality=100,
        viewer=False,
        offScreen=True,
        forceOverwrite=True,
        clearCache=True,
        showOrnaments=False,
        editorPanelName=panel,
    )
    cmds.playblast(**pb_kwargs)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

class BlendshapeSnapper(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent or _maya_main_window())
        self.setWindowTitle("Blendshape Snapper")
        self.setFixedWidth(360)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._checkboxes = []   # list of (bs_node, target, QCheckBox)
        self._build_ui()
        self._refresh_cameras()

    # ── build ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        self._status = QtWidgets.QLabel("ready")
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#555; font-size:10px;")
        root.addWidget(self._status)

        root.addWidget(_divider())

        # ── Camera ───────────────────────────────────────────────────────────
        cam_hdr = QtWidgets.QHBoxLayout()
        cam_lbl = QtWidgets.QLabel("CAMERA")
        cam_lbl.setStyleSheet(_SECTION_STYLE)
        refresh_cam = QtWidgets.QPushButton("↺")
        refresh_cam.setFixedSize(22, 22)
        refresh_cam.setStyleSheet(
            "QPushButton { background:#2a2a2a; color:#888; border:1px solid #444;"
            " border-radius:3px; font-size:13px; }"
            "QPushButton:hover { color:#ccc; }"
        )
        refresh_cam.setToolTip("Refresh camera list")
        refresh_cam.clicked.connect(self._refresh_cameras)
        cam_hdr.addWidget(cam_lbl)
        cam_hdr.addStretch()
        cam_hdr.addWidget(refresh_cam)
        root.addLayout(cam_hdr)

        self._cam_combo = QtWidgets.QComboBox()
        self._cam_combo.setFixedHeight(26)
        self._cam_combo.setStyleSheet(
            "QComboBox { background:#2a2a2a; color:#ccc; border:1px solid #444;"
            " border-radius:3px; padding:0 6px; font-size:11px; }"
            "QComboBox::drop-down { border:none; }"
            "QComboBox QAbstractItemView { background:#2a2a2a; color:#ccc;"
            " selection-background-color:#444; }"
        )
        root.addWidget(self._cam_combo)

        root.addWidget(_divider())

        # ── Blendshapes ──────────────────────────────────────────────────────
        bs_hdr = QtWidgets.QHBoxLayout()
        bs_lbl = QtWidgets.QLabel("BLENDSHAPES")
        bs_lbl.setStyleSheet(_SECTION_STYLE)
        refresh_bs = QtWidgets.QPushButton("↺")
        refresh_bs.setFixedSize(22, 22)
        refresh_bs.setStyleSheet(
            "QPushButton { background:#2a2a2a; color:#888; border:1px solid #444;"
            " border-radius:3px; font-size:13px; }"
            "QPushButton:hover { color:#ccc; }"
        )
        refresh_bs.setToolTip("Refresh blendshape list")
        refresh_bs.clicked.connect(self._refresh_blendshapes)
        bs_hdr.addWidget(bs_lbl)
        bs_hdr.addStretch()
        bs_hdr.addWidget(refresh_bs)
        root.addLayout(bs_hdr)

        # select all / none / invert
        sel_row = QtWidgets.QHBoxLayout()
        sel_row.setSpacing(4)
        for label, slot in (("All", self._select_all),
                             ("None", self._select_none),
                             ("Invert", self._select_invert)):
            b = QtWidgets.QPushButton(label)
            b.setFixedHeight(22)
            b.setStyleSheet(
                "QPushButton { background:#2a2a2a; color:#aaa; border:1px solid #444;"
                " border-radius:3px; font-size:10px; }"
                "QPushButton:hover { color:#fff; }"
            )
            b.clicked.connect(slot)
            sel_row.addWidget(b)
        root.addLayout(sel_row)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(240)
        scroll.setStyleSheet(
            "QScrollArea { background:#1e1e1e; border:1px solid #333; border-radius:3px; }"
        )
        self._bs_container = QtWidgets.QWidget()
        self._bs_layout = QtWidgets.QVBoxLayout(self._bs_container)
        self._bs_layout.setContentsMargins(6, 4, 6, 4)
        self._bs_layout.setSpacing(2)
        scroll.setWidget(self._bs_container)
        root.addWidget(scroll)

        root.addWidget(_divider())

        # ── Output ───────────────────────────────────────────────────────────
        out_lbl = QtWidgets.QLabel("OUTPUT FOLDER")
        out_lbl.setStyleSheet(_SECTION_STYLE)
        root.addWidget(out_lbl)

        out_row = QtWidgets.QHBoxLayout()
        out_row.setSpacing(4)
        self._out_field = QtWidgets.QLineEdit(
            os.path.join(os.path.expanduser("~"), "Desktop", "BlendshapeSnaps")
        )
        self._out_field.setFixedHeight(26)
        self._out_field.setStyleSheet(_FIELD_STYLE)
        browse = QtWidgets.QPushButton("…")
        browse.setFixedSize(28, 26)
        browse.setStyleSheet(
            "QPushButton { background:#2a2a2a; color:#aaa; border:1px solid #444;"
            " border-radius:3px; font-size:13px; }"
            "QPushButton:hover { color:#fff; }"
        )
        browse.clicked.connect(self._browse)
        out_row.addWidget(self._out_field)
        out_row.addWidget(browse)
        root.addLayout(out_row)

        root.addSpacing(2)

        snap_btn = _btn("Snap", "#2d6b3a", "#3a9050", "#1f5028")
        snap_btn.clicked.connect(self._snap)
        root.addWidget(snap_btn)

        root.addSpacing(2)
        self._refresh_blendshapes()

    # ── camera ───────────────────────────────────────────────────────────────

    def _refresh_cameras(self):
        self._cam_combo.clear()
        self._cam_data = _scene_cameras()   # [(transform, shape), ...]
        if not self._cam_data:
            self._cam_combo.addItem("— no cameras found —")
        else:
            for transform, _ in self._cam_data:
                self._cam_combo.addItem(transform)
        self._log(f"cameras: {[t for t, _ in self._cam_data]}")

    def _selected_camera(self):
        idx = self._cam_combo.currentIndex()
        if not self._cam_data or idx < 0 or idx >= len(self._cam_data):
            return None, None
        return self._cam_data[idx]   # (transform, shape)

    # ── blendshapes ──────────────────────────────────────────────────────────

    def _refresh_blendshapes(self):
        for i in reversed(range(self._bs_layout.count())):
            w = self._bs_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._checkboxes = []

        bs_nodes = cmds.ls(type="blendShape") or []
        if not bs_nodes:
            lbl = QtWidgets.QLabel("  no blendShape nodes found")
            lbl.setStyleSheet("color:#444; font-size:10px; padding:2px;")
            self._bs_layout.addWidget(lbl)
            self._bs_layout.addStretch()
            return

        for node in bs_nodes:
            targets = _blendshape_targets(node)
            if not targets:
                continue
            hdr = QtWidgets.QLabel(f"  [ {node} ]")
            hdr.setStyleSheet("color:#777; font-size:10px; font-weight:bold; padding-top:4px;")
            self._bs_layout.addWidget(hdr)
            for target in targets:
                cb = QtWidgets.QCheckBox(f"  {target}")
                cb.setStyleSheet(_CB_STYLE)
                self._bs_layout.addWidget(cb)
                self._checkboxes.append((node, target, cb))

        self._bs_layout.addStretch()
        self._log(f"blendshapes: {len(self._checkboxes)} targets across {len(bs_nodes)} node(s)")

    def _select_all(self):
        for _, _, cb in self._checkboxes:
            cb.setChecked(True)

    def _select_none(self):
        for _, _, cb in self._checkboxes:
            cb.setChecked(False)

    def _select_invert(self):
        for _, _, cb in self._checkboxes:
            cb.setChecked(not cb.isChecked())

    # ── output ───────────────────────────────────────────────────────────────

    def _browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Choose output folder",
            self._out_field.text(), QtWidgets.QFileDialog.ShowDirsOnly)
        if folder:
            self._out_field.setText(folder)

    # ── snap ─────────────────────────────────────────────────────────────────

    def _snap(self):
        cam_transform, cam_shape = self._selected_camera()
        if not cam_transform:
            self._set_status("no camera selected", "#c87050")
            return

        out_dir = self._out_field.text().strip()
        if not out_dir:
            self._set_status("set an output folder", "#c87050")
            return
        os.makedirs(out_dir, exist_ok=True)

        checked = [(bs, tgt) for bs, tgt, cb in self._checkboxes if cb.isChecked()]
        if not checked:
            self._set_status("check at least one blendshape", "#c87050")
            return

        errors = []
        for i, (bs_node, target) in enumerate(checked, 1):
            self._set_status(f"[{i}/{len(checked)}] {target}…")
            QtWidgets.QApplication.processEvents()
            self._log(f"snapping {target}")
            try:
                _set_weight(bs_node, target, 1.0)
                cmds.refresh(force=True)
                _capture(cam_transform, os.path.join(out_dir, target))
            except Exception as e:
                errors.append(f"{target}: {e}")
                self._log(f"ERROR {target}: {e}")
            finally:
                _set_weight(bs_node, target, 0.0)

        msg = f"done — {len(checked) - len(errors)} snaps → {out_dir}"
        if errors:
            msg += f"  ({len(errors)} error(s))"
        self._set_status(msg, "#8fc87a" if not errors else "#c8a040")
        self._log(f"--- snap complete: {len(checked) - len(errors)}/{len(checked)} ok ---")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _set_status(self, msg, color="#aaa"):
        self._status.setText(msg)
        self._status.setStyleSheet(f"color:{color}; font-size:10px;")
        QtWidgets.QApplication.processEvents()

    def _log(self, msg):
        print(f"[blendshapeSnapper] {msg}")
