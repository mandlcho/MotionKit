"""
Hugin Tool — Save + Playblast
Run to open. Requires audio node in scene and cameras: front_before, front_after.
"""

import os
import shutil
import subprocess
import tempfile
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
import shiboken2

WINDOW_ID = "huginToolWin"
CAMERAS   = ["front_before", "front_after"]


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


class HuginTool(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent or _maya_main_window())
        self.setWindowTitle("quickRender")
        self.setFixedWidth(300)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        self._status = QtWidgets.QLabel("ready")
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#555; font-size:10px;")
        root.addWidget(self._status)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color:#2a2a2a;")
        root.addWidget(line)

        # character subfolder
        char_row = QtWidgets.QHBoxLayout()
        char_lbl = QtWidgets.QLabel("Character")
        char_lbl.setStyleSheet("color:#888; font-size:10px;")
        char_lbl.setFixedWidth(62)
        self._char_field = QtWidgets.QLineEdit()
        self._char_field.setPlaceholderText("e.g. Hugin, Cynthia …")
        self._char_field.setText("Hugin")
        self._char_field.setFixedHeight(26)
        self._char_field.setStyleSheet(
            "QLineEdit { background:#2a2a2a; color:#ccc; border:1px solid #444;"
            " border-radius:3px; padding:0 4px; font-size:11px; }"
            "QLineEdit:focus { border-color:#666; }"
        )
        char_row.addWidget(char_lbl)
        char_row.addWidget(self._char_field)
        root.addLayout(char_row)

        # cameras
        cam_header_row = QtWidgets.QHBoxLayout()
        cam_lbl = QtWidgets.QLabel("CAMERAS")
        cam_lbl.setStyleSheet("color:#555; font-size:9px; letter-spacing:1px;")
        refresh_btn = QtWidgets.QPushButton("↺")
        refresh_btn.setFixedSize(22, 22)
        refresh_btn.setStyleSheet(
            "QPushButton { background:#2a2a2a; color:#888; border:1px solid #444;"
            " border-radius:3px; font-size:13px; }"
            "QPushButton:hover { color:#ccc; }"
        )
        refresh_btn.setToolTip("Refresh camera list")
        refresh_btn.clicked.connect(self._refresh_cameras)
        cam_header_row.addWidget(cam_lbl)
        cam_header_row.addStretch()
        cam_header_row.addWidget(refresh_btn)
        root.addLayout(cam_header_row)

        self._cam_scroll = QtWidgets.QScrollArea()
        self._cam_scroll.setWidgetResizable(True)
        self._cam_scroll.setFixedHeight(100)
        self._cam_scroll.setStyleSheet(
            "QScrollArea { background:#1e1e1e; border:1px solid #333; border-radius:3px; }"
        )
        self._cam_container = QtWidgets.QWidget()
        self._cam_layout = QtWidgets.QVBoxLayout(self._cam_container)
        self._cam_layout.setContentsMargins(6, 4, 6, 4)
        self._cam_layout.setSpacing(2)
        self._cam_scroll.setWidget(self._cam_container)
        root.addWidget(self._cam_scroll)
        self._cam_checkboxes = {}
        self._refresh_cameras()

        save_btn = _btn("Save  .ma", "#2d4a6b", "#3a6090", "#1f3050")
        save_btn.clicked.connect(self._save)
        root.addWidget(save_btn)

        pb_btn = _btn("Playblast  selected cameras", "#4a2d6b", "#6040a0", "#30204a")
        pb_btn.clicked.connect(self._playblast)
        root.addWidget(pb_btn)

        root.addWidget(_divider())

        # ── Batch Playblast ───────────────────────────────────────────────────
        batch_lbl = QtWidgets.QLabel("BATCH PLAYBLAST")
        batch_lbl.setStyleSheet("color:#555; font-size:9px; letter-spacing:1px;")
        root.addWidget(batch_lbl)

        folder_row = QtWidgets.QHBoxLayout()
        folder_row.setSpacing(6)
        self._batch_folder = QtWidgets.QLineEdit()
        self._batch_folder.setPlaceholderText("folder of .ma / .mb files")
        self._batch_folder.setFixedHeight(26)
        self._batch_folder.setStyleSheet(
            "QLineEdit { background:#2a2a2a; color:#ccc; border:1px solid #444;"
            " border-radius:3px; padding:0 4px; font-size:11px; }"
            "QLineEdit:focus { border-color:#666; }"
        )
        browse_btn = QtWidgets.QPushButton("…")
        browse_btn.setFixedSize(28, 26)
        browse_btn.setStyleSheet(
            "QPushButton { background:#2a2a2a; color:#aaa; border:1px solid #444;"
            " border-radius:3px; font-size:13px; }"
            "QPushButton:hover { color:#fff; }"
        )
        browse_btn.clicked.connect(self._browse_batch_folder)
        folder_row.addWidget(self._batch_folder)
        folder_row.addWidget(browse_btn)
        root.addLayout(folder_row)

        batch_btn = _btn("Batch Playblast Folder", "#4a2d1a", "#7a4a28", "#301808")
        batch_btn.clicked.connect(self._batch_playblast)
        root.addWidget(batch_btn)

        root.addSpacing(2)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _set_status(self, msg, color="#aaa"):
        self._status.setText(msg)
        self._status.setStyleSheet(f"color:{color}; font-size:10px;")
        QtWidgets.QApplication.processEvents()

    def _all_custom_cameras(self):
        """Return list of (transform_short, shape_fullpath) for all non-default cameras."""
        skip_shapes = {"perspShape", "topShape", "frontShape", "sideShape",
                       "leftShape", "rightShape", "bottomShape", "backShape"}
        result = []
        for shape in (cmds.ls(type="camera", long=True) or []):
            short_shape = shape.split("|")[-1].split(":")[-1]
            if short_shape in skip_shapes:
                continue
            parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
            if not parents:
                continue
            transform_full = parents[0]
            transform_short = transform_full.split("|")[-1]  # keep namespace prefix
            result.append((transform_short, shape))
        return result

    def _refresh_cameras(self):
        for i in reversed(range(self._cam_layout.count())):
            w = self._cam_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._cam_checkboxes = {}  # label → (shape_fullpath, QCheckBox)

        custom = self._all_custom_cameras()
        if not custom:
            lbl = QtWidgets.QLabel("no custom cameras found")
            lbl.setStyleSheet("color:#444; font-size:10px; padding:2px;")
            self._cam_layout.addWidget(lbl)
        else:
            for label, shape in sorted(custom, key=lambda x: x[0]):
                cb = QtWidgets.QCheckBox(label)
                cb.setStyleSheet(
                    "QCheckBox { color:#ccc; font-size:11px; }"
                    "QCheckBox::indicator { width:13px; height:13px; }"
                )
                if label in CAMERAS:
                    cb.setChecked(True)
                self._cam_layout.addWidget(cb)
                self._cam_checkboxes[label] = (shape, cb)
        self._cam_layout.addStretch()
        self._log(f"cameras refreshed: {list(self._cam_checkboxes.keys())}")

    def _log(self, msg):
        print(f"[quickRender] {msg}")

    def _audio_info(self):
        nodes = cmds.ls(type="audio")
        if not nodes:
            self._log("ERROR: no audio node found in scene")
            return None, None
        node     = nodes[0]
        filepath = cmds.getAttr(node + ".filename") or ""
        name     = os.path.splitext(os.path.basename(filepath))[0] or "unnamed"
        self._log(f"audio node: {node}  |  file: {filepath}  |  name: {name}")
        return node, name

    def _save_dir(self, name):
        char = self._char_field.text().strip() or "Hugin"
        d = os.path.join(os.path.expanduser("~"), "Desktop", "BeforeAfter", char)
        os.makedirs(d, exist_ok=True)
        self._log(f"output dir: {d}")
        return d

    def _frame_range(self, audio_node):
        start = int(round(cmds.getAttr(audio_node + ".offset")))

        # Use last animation keyframe as end frame
        all_keys = cmds.keyframe(query=True, timeChange=True) or []
        if all_keys:
            end = int(round(max(all_keys)))
            self._log(f"last keyframe: {end}")
        else:
            # fallback: current timeline end
            end = int(cmds.playbackOptions(query=True, maxTime=True))
            self._log(f"no keys found, using timeline end: {end}")

        self._log(f"audio offset: {start}  last key: {end}  → frame range {start}–{end}")
        return start, end

    # ── Save ─────────────────────────────────────────────────────────────────

    def _save(self):
        self._log("--- Save ---")
        audio, name = self._audio_info()
        if not audio:
            self._set_status("no audio node in scene", "#c87050")
            return
        path = os.path.join(self._save_dir(name), name + ".ma")
        self._log(f"saving to: {path}")
        try:
            cmds.file(rename=path)
            cmds.file(save=True, type="mayaAscii", force=True)
            self._log(f"save OK → {path}")
            char = self._char_field.text().strip() or "Hugin"
            self._set_status(f"saved → Desktop/BeforeAfter/{char}/{name}.ma", "#8fc87a")
        except Exception as e:
            self._log(f"ERROR: {e}")
            self._set_status(f"save failed: {e}", "#c87050")
            cmds.warning(f"[quickRender] {e}")

    # ── Playblast ─────────────────────────────────────────────────────────────

    def _find_panel_for_camera(self, camera_shape):
        """Find a model panel already showing this camera, else return first panel."""
        parents = cmds.listRelatives(camera_shape, parent=True, fullPath=True) or []
        transform = parents[0] if parents else None
        panels = cmds.getPanel(type="modelPanel") or []
        # prefer panel already on this camera
        for p in panels:
            try:
                if cmds.modelEditor(p, q=True, camera=True) == transform:
                    self._log(f"found panel {p} already on {transform}")
                    return p
            except Exception:
                continue
        return panels[0] if panels else None

    def _playblast_camera(self, camera, camera_shape, output_path, start, end):
        if not cmds.objExists(camera_shape):
            self._log(f"ERROR: camera shape not found: {camera_shape}")
            self._set_status(f"camera not found: {camera}", "#c87050")
            return False

        # prefer qt (mov container), fall back to avi
        available_formats = cmds.playblast(query=True, format=True) or []
        # check ffmpeg — also probe known WinGet install location
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            winget_path = os.path.expanduser(
                r"~\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe")
            if os.path.exists(winget_path):
                ffmpeg = winget_path
        self._log(f"ffmpeg: {ffmpeg or 'NOT FOUND — will use maya encoder'}")

        # wire audio
        audio_nodes = cmds.ls(type="audio")
        audio_file  = None
        sound_flag  = {}
        if audio_nodes:
            sound_flag = {"sound": audio_nodes[0]}
            audio_file = cmds.getAttr(audio_nodes[0] + ".filename") or None
            self._log(f"audio node: {audio_nodes[0]}  file: {audio_file}")
        else:
            self._log("no audio node — playblast will be silent")

        panel = self._find_panel_for_camera(camera_shape)
        self._log(f"using panel: {panel}  camera: {cmds.modelEditor(panel, q=True, camera=True) if panel else 'none'}")

        try:
            if ffmpeg:
                tmp_dir  = tempfile.mkdtemp(prefix="qr_pb_")
                seq_path = os.path.join(tmp_dir, "frame")
                self._log(f"PNG sequence dir: {tmp_dir}")
                self._log(f"playblasting PNGs  frames {start}–{end}")
                pb_kwargs = dict(
                    filename=seq_path,
                    format="image",
                    compression="png",
                    sequenceTime=False,
                    clearCache=True,
                    viewer=False,
                    showOrnaments=False,
                    offScreen=True,
                    percent=100,
                    quality=100,
                    widthHeight=[1920, 1080],
                    startTime=start,
                    endTime=end,
                    forceOverwrite=True,
                )
                if panel:
                    pb_kwargs["editorPanelName"] = panel
                cmds.playblast(**pb_kwargs)
                import glob as _glob
                written = sorted(_glob.glob(seq_path + ".*.png"))
                self._log(f"PNG frames written: {len(written)}")
                if not written:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                    raise RuntimeError("playblast produced no PNG frames")

                # detect actual first frame number from written files
                first_frame = int(written[0].rsplit(".", 2)[-2])
                self._log(f"first PNG frame number: {first_frame}")

                out_mp4 = output_path + ".mp4"
                fps     = mel.eval("currentTimeUnitToFPS()")
                ff_cmd  = [ffmpeg, "-y",
                           "-framerate", str(fps),
                           "-start_number", str(first_frame),
                           "-i", seq_path + ".%04d.png"]
                if audio_file and os.path.exists(audio_file):
                    ff_cmd += ["-i", audio_file, "-shortest"]
                ff_cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "23",
                           "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "128k", out_mp4]
                self._log("ffmpeg: " + " ".join(ff_cmd))
                result = subprocess.run(ff_cmd, capture_output=True, text=True)
                shutil.rmtree(tmp_dir, ignore_errors=True)
                if result.returncode != 0:
                    self._log(f"ffmpeg stderr: {result.stderr[-500:]}")
                    raise RuntimeError(f"ffmpeg failed (code {result.returncode})")
                size_mb = os.path.getsize(out_mp4) / (1024 * 1024)
                self._log(f"encode OK → {out_mp4}  ({size_mb:.1f} MB)")

            else:
                available_formats = cmds.playblast(query=True, format=True) or []
                if "qt" in available_formats:
                    fmt, ext, compression = "qt", "mov", "H.264"
                else:
                    fmt, ext, compression = "avi", "avi", "MS-CRAM"
                self._log(f"playblasting {camera}  fmt={fmt}  → {output_path}.{ext}")
                cmds.playblast(
                    filename=output_path,
                    format=fmt,
                    compression=compression,
                    sequenceTime=False,
                    clearCache=True,
                    viewer=False,
                    showOrnaments=False,
                    offScreen=True,
                    percent=75,
                    quality=75,
                    widthHeight=[1280, 720],
                    startTime=start,
                    endTime=end,
                    forceOverwrite=True,
                    **sound_flag,
                )
                self._log(f"playblast OK → {output_path}.{ext}")

            return True

        except Exception as e:
            self._log(f"ERROR playblast {camera}: {e}")
            cmds.warning(f"[quickRender] playblast {camera}: {e}")
            return False

    def _browse_batch_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select folder of Maya files",
            os.path.expanduser("~"), QtWidgets.QFileDialog.ShowDirsOnly)
        if folder:
            self._batch_folder.setText(folder)

    def _batch_playblast(self):
        folder = self._batch_folder.text().strip()
        if not folder or not os.path.isdir(folder):
            self._set_status("set a valid folder first", "#c87050")
            return

        import glob as _glob
        ma_files = sorted(
            _glob.glob(os.path.join(folder, "*.ma")) +
            _glob.glob(os.path.join(folder, "*.mb"))
        )
        if not ma_files:
            self._set_status("no .ma/.mb files found in folder", "#c87050")
            return

        # save base names (strip namespace) of checked cameras to match across files
        # e.g. "cynthia:front_after" → "front_after"
        checked_base_names = [
            cam.split(":")[-1]
            for cam, (shape, cb) in self._cam_checkboxes.items() if cb.isChecked()
        ]
        if not checked_base_names:
            self._set_status("no cameras selected", "#c87050")
            return

        self._log(f"--- Batch Playblast: {len(ma_files)} files, cameras: {checked_base_names} ---")
        total_ok = 0
        for i, ma_path in enumerate(ma_files):
            self._set_status(f"[{i+1}/{len(ma_files)}] opening {os.path.basename(ma_path)}...")
            self._log(f"opening: {ma_path}")
            try:
                cmds.file(ma_path, open=True, force=True, loadReferenceDepth="all")
            except Exception as e:
                self._log(f"ERROR opening {ma_path}: {e}")
                continue

            self._refresh_cameras()

            audio, name = self._audio_info()
            if not audio:
                self._log(f"no audio in {ma_path}, skipping")
                continue

            save_dir = self._save_dir(name)
            start, end = self._frame_range(audio)
            cmds.playbackOptions(minTime=start, maxTime=end,
                                 animationStartTime=start, animationEndTime=end)

            # match cameras by base name regardless of namespace
            for base_name in checked_base_names:
                match = next(
                    ((label, shape) for label, (shape, cb) in self._cam_checkboxes.items()
                     if label.split(":")[-1] == base_name),
                    None
                )
                if not match:
                    self._log(f"camera '{base_name}' not found in {os.path.basename(ma_path)}, skipping")
                    continue
                cam_label, shape = match
                self._log(f"  playblasting {cam_label}")
                out = os.path.join(save_dir, f"{name}_{base_name}")
                ok = self._playblast_camera(cam_label, shape, out, start, end)
                if ok:
                    total_ok += 1

        self._set_status(f"batch done — {total_ok} clips rendered from {len(ma_files)} files", "#8fc87a")
        self._log(f"--- Batch done: {total_ok} clips ---")

    def _playblast(self):
        self._log("--- Playblast ---")
        audio, name = self._audio_info()
        if not audio:
            self._set_status("no audio node in scene", "#c87050")
            return

        save_dir = self._save_dir(name)
        start, end = self._frame_range(audio)

        self._log(f"setting frame range: {start} → {end}")
        cmds.playbackOptions(minTime=start, maxTime=end,
                             animationStartTime=start, animationEndTime=end)
        self._set_status(f"frame range → {start} : {end}")

        checked_cams = [(cam, shape) for cam, (shape, cb) in self._cam_checkboxes.items() if cb.isChecked()]
        if not checked_cams:
            self._set_status("no cameras selected", "#c87050")
            self._log("ERROR: no cameras checked")
            return

        results = []
        for cam, shape in checked_cams:
            self._log(f"--- camera: {cam} ---")
            self._set_status(f"playblasting {cam}...")
            out = os.path.join(save_dir, f"{name}_{cam.replace(':', '_')}")
            ok  = self._playblast_camera(cam, shape, out, start, end)
            results.append(("✓" if ok else "✗") + f" {cam}")

        self._log("--- done: " + "  |  ".join(results) + " ---")
        all_ok = all(r.startswith("✓") for r in results)
        self._set_status("  |  ".join(results), "#8fc87a" if all_ok else "#c8a040")


# ── launch ───────────────────────────────────────────────────────────────────

if cmds.window(WINDOW_ID, exists=True):
    cmds.deleteUI(WINDOW_ID)

win = HuginTool()
win.setObjectName(WINDOW_ID)
win.show()
