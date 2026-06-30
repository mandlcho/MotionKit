import maya.cmds as cmds
import maya.api.OpenMaya as om2
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore, QtGui
import shiboken2
import json, os


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)


SAVE_DIR  = os.path.join(os.path.expanduser("~"), "Documents", "vtx_bs")
SAVE_FILE = os.path.join(SAVE_DIR, "selections.json")


def _short(full_path):
    return full_path.split("|")[-1].split(":")[-1] if full_path else ""


BTN = (
    "QPushButton {{ background: {bg}; color: white; border-radius: 4px; font-size: 12px; }}"
    "QPushButton:hover {{ background: {hv}; }}"
    "QPushButton:pressed {{ background: {pr}; }}"
    "QPushButton:disabled {{ background: #333; color: #555; }}"
)


class VtxCopyPaste(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent or _maya_main_window())
        self._verts     = []
        self._src       = None
        self._saved_sels = []

        self.setWindowTitle("Vtx Tools")
        self.setFixedWidth(300)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build_ui()
        self.adjustSize()
        self._load_from_file()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        # ── Copy / Paste ──────────────────────────────────────────────────────
        root.addWidget(self._section("COPY / PASTE"))

        self._cp_lbl = QtWidgets.QLabel("nothing copied")
        self._cp_lbl.setStyleSheet("color: #555; font-size: 10px;")
        root.addWidget(self._cp_lbl)

        cp_row = QtWidgets.QHBoxLayout()
        cp_row.setSpacing(6)
        cp_row.addWidget(self._btn("Copy",  "#2d6b2d", "#3a8a3a", "#1f4d1f", self.copy))
        cp_row.addWidget(self._btn("Paste", "#2d3d7a", "#3a4f9e", "#1f2b56", self.paste))
        root.addLayout(cp_row)

        root.addWidget(self._divider())

        # ── Saved Selections ──────────────────────────────────────────────────
        root.addWidget(self._section("SAVED SELECTIONS"))

        self._search = QtWidgets.QLineEdit()
        self._search.setPlaceholderText("🔍  filter...")
        self._search.setFixedHeight(26)
        self._search.setStyleSheet(
            "QLineEdit { background: #222; color: #ccc; border: 1px solid #444;"
            " border-radius: 3px; padding: 0 4px; font-size: 11px; }"
            "QLineEdit:focus { border-color: #666; }"
        )
        self._search.textChanged.connect(self._filter_list)
        root.addWidget(self._search)

        save_row = QtWidgets.QHBoxLayout()
        save_row.setSpacing(6)
        self._sel_name = QtWidgets.QLineEdit()
        self._sel_name.setPlaceholderText("name  (optional)")
        self._sel_name.setFixedHeight(26)
        self._sel_name.setStyleSheet(
            "QLineEdit { background: #2a2a2a; color: #ccc; border: 1px solid #444;"
            " border-radius: 3px; padding: 0 4px; font-size: 11px; }"
            "QLineEdit:focus { border-color: #666; }"
        )
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.setFixedSize(54, 26)
        save_btn.setStyleSheet(BTN.format(bg="#3a3a2a", hv="#5a5a38", pr="#28280f"))
        save_btn.clicked.connect(self._save_selection)
        save_row.addWidget(self._sel_name)
        save_row.addWidget(save_btn)
        root.addLayout(save_row)

        self._sel_list = QtWidgets.QListWidget()
        self._sel_list.setMinimumHeight(240)
        self._sel_list.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._sel_list.setStyleSheet(
            "QListWidget { background: #1e1e1e; color: #ccc; border: 1px solid #333;"
            " border-radius: 3px; font-size: 12px; outline: none; }"
            "QListWidget::item { padding: 5px 8px; }"
            "QListWidget::item:selected { background: #2d4a2d; color: #8fc87a; }"
            "QListWidget::item:hover { background: #252525; }"
        )
        self._sel_list.currentItemChanged.connect(
            lambda cur, _prev: self._recall_selection(cur) if cur else None)
        root.addWidget(self._sel_list, 1)

        del_row = QtWidgets.QHBoxLayout()
        del_row.setSpacing(6)
        recall_btn = QtWidgets.QPushButton("Select")
        recall_btn.setFixedHeight(26)
        recall_btn.setStyleSheet(BTN.format(bg="#2d4a2d", hv="#3a6a3a", pr="#1f331f"))
        recall_btn.clicked.connect(self._recall_selected_item)

        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.setFixedHeight(26)
        delete_btn.setStyleSheet(BTN.format(bg="#4a2020", hv="#6a2a2a", pr="#331515"))
        delete_btn.clicked.connect(self._delete_selection)

        del_row.addWidget(recall_btn)
        del_row.addWidget(delete_btn)
        root.addLayout(del_row)

        root.addSpacing(2)

    # ── widget helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _btn(text, bg, hv, pr, slot):
        b = QtWidgets.QPushButton(text)
        b.setFixedHeight(30)
        b.setStyleSheet(BTN.format(bg=bg, hv=hv, pr=pr))
        b.clicked.connect(slot)
        return b

    @staticmethod
    def _section(text):
        lbl = QtWidgets.QLabel(text)
        lbl.setStyleSheet("color: #555; font-size: 9px; letter-spacing: 1px;")
        return lbl

    @staticmethod
    def _divider():
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("color: #2a2a2a;")
        return line

    def _set_cp_status(self, msg, color="#555"):
        self._cp_lbl.setText(msg)
        self._cp_lbl.setStyleSheet(f"color: {color}; font-size: 10px;")

    # ── mesh helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _dag_from_name(name):
        sl = om2.MSelectionList()
        sl.add(name)
        dag = sl.getDagPath(0)
        dag.extendToShape()
        return dag

    @staticmethod
    def _read_selection(space):
        active = om2.MGlobal.getActiveSelectionList()
        if active.isEmpty():
            return None, {}

        verts = {}
        mesh_name = None
        it = om2.MItSelectionList(active)
        while not it.isDone():
            try:
                dag, comp = it.getComponent()
                dag.extendToShape()
                if dag.apiType() != om2.MFn.kMesh:
                    it.next(); continue

                mesh_name = dag.fullPathName()
                fn = om2.MFnMesh(dag)

                if comp.isNull():
                    pts = fn.getPoints(space)
                    verts = {i: pts[i] for i in range(len(pts))}
                else:
                    ctype = comp.apiType()
                    if ctype == om2.MFn.kMeshVertComponent:
                        vit = om2.MItMeshVertex(dag, comp)
                        while not vit.isDone():
                            verts[vit.index()] = vit.position(space)
                            vit.next()
                    elif ctype == om2.MFn.kMeshPolygonComponent:
                        seen = set()
                        fit = om2.MItMeshPolygon(dag, comp)
                        while not fit.isDone():
                            for vi in fit.getVertices():
                                if vi not in seen:
                                    seen.add(vi)
                                    verts[vi] = fn.getPoint(vi, space)
                            fit.next()
            except Exception as e:
                print(f"[vtxCP] skip: {e}")
            it.next()

        return mesh_name, verts

    # ── Copy / Paste ──────────────────────────────────────────────────────────

    def copy(self):
        mesh, verts = self._read_selection(om2.MSpace.kObject)
        if not verts:
            self._set_cp_status("select a mesh / verts / faces first", "#c87050")
            return
        self._verts = list(verts.items())
        self._src   = mesh
        frame = cmds.currentTime(q=True)
        self._set_cp_status(
            f"copied  {len(self._verts)} verts  ·  {_short(mesh)}  (fr {frame:.0f})",
            "#8fc87a")

    def paste(self):
        if not self._verts:
            self._set_cp_status("nothing copied yet", "#c87050")
            return

        target_dag = None
        active = om2.MGlobal.getActiveSelectionList()
        if not active.isEmpty():
            try:
                dag = active.getDagPath(0)
                dag.extendToShape()
                if dag.apiType() == om2.MFn.kMesh:
                    target_dag = dag
            except Exception:
                pass

        if target_dag is None and self._src:
            try:
                target_dag = self._dag_from_name(self._src)
            except Exception:
                pass

        if target_dag is None:
            self._set_cp_status("select a target mesh first", "#c87050")
            return

        fn = om2.MFnMesh(target_dag)
        applied = 0
        try:
            for idx, pt in self._verts:
                if idx < fn.numVertices:
                    fn.setPoint(idx, pt, om2.MSpace.kObject)
                    applied += 1
            fn.updateSurface()
            frame = cmds.currentTime(q=True)
            self._set_cp_status(
                f"pasted  {applied} verts  ·  {_short(target_dag.fullPathName())}  (fr {frame:.0f})",
                "#7aafc8")
        except Exception as e:
            self._set_cp_status("paste error — see script editor", "#c87050")
            cmds.warning(f"[vtxCP] {e}")

    # ── Saved Selections ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_to_groups(flat_components):
        buckets = {}
        for c in flat_components:
            if "." not in c:
                continue
            mesh, rest = c.rsplit(".", 1)
            ctype = rest.split("[")[0]
            idx   = int(rest.split("[")[1].rstrip("]"))
            key   = (_short(mesh), ctype)
            buckets.setdefault(key, []).append(idx)
        return [
            {"mesh": mesh, "type": ctype, "indices": sorted(idxs)}
            for (mesh, ctype), idxs in buckets.items()
        ]

    @staticmethod
    def _build_components(groups, target_mesh=None):
        out = []
        for g in groups:
            mesh = target_mesh or g["mesh"]
            for idx in g["indices"]:
                out.append(f"{mesh}.{g['type']}[{idx}]")
        return out

    def _filter_list(self, text):
        q = text.strip().lower()
        for i in range(self._sel_list.count()):
            item = self._sel_list.item(i)
            item.setHidden(bool(q and q not in item.text().lower()))

    def _load_from_file(self):
        self._sel_list.clear()
        self._saved_sels = []
        if not os.path.exists(SAVE_FILE):
            return
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            for entry in data:
                self._saved_sels.append(entry)
                item = QtWidgets.QListWidgetItem(f"{entry['name']}   —   {entry['info']}")
                item.setData(QtCore.Qt.UserRole, len(self._saved_sels) - 1)
                self._sel_list.addItem(item)
        except Exception as e:
            print(f"[vtxSel] load error: {e}")

    def _write_to_file(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(self._saved_sels, f, indent=2)
        except Exception as e:
            print(f"[vtxSel] save error: {e}")

    def _save_selection(self):
        flat = cmds.ls(sl=True, fl=True, long=True)
        if not flat:
            print("[vtxSel] nothing selected")
            return

        name = self._sel_name.text().strip()
        if not name:
            name = f"sel_{len(self._saved_sels) + 1:02d}"

        groups = self._parse_to_groups(flat)
        total  = sum(len(g["indices"]) for g in groups)
        meshes = sorted(set(g["mesh"] for g in groups))
        info   = f"{total} {groups[0]['type'] if groups else 'items'}  ·  {', '.join(meshes)}"
        entry  = {"name": name, "info": info, "groups": groups}

        self._saved_sels.append(entry)
        item = QtWidgets.QListWidgetItem(f"{name}   —   {info}")
        item.setData(QtCore.Qt.UserRole, len(self._saved_sels) - 1)
        self._sel_list.addItem(item)
        self._sel_name.clear()
        self._filter_list(self._search.text())
        self._write_to_file()

    def _recall_selection(self, item):
        if item is None:
            return
        entry = self._saved_sels[item.data(QtCore.Qt.UserRole)]

        target = None
        active = cmds.ls(sl=True, o=True)
        if active:
            shapes = cmds.listRelatives(active[0], shapes=True, fullPath=True) or []
            if shapes and cmds.nodeType(shapes[0]) == "mesh":
                target = _short(active[0])

        try:
            components = self._build_components(entry["groups"], target)
            cmds.select(components)
        except Exception as e:
            print(f"[vtxSel] recall error: {e}")

    def _recall_selected_item(self):
        items = self._sel_list.selectedItems()
        if items:
            self._recall_selection(items[0])

    def _delete_selection(self):
        row = self._sel_list.currentRow()
        if row < 0:
            return
        self._sel_list.takeItem(row)
        self._saved_sels.pop(row)
        for i in range(self._sel_list.count()):
            self._sel_list.item(i).setData(QtCore.Qt.UserRole, i)
        self._write_to_file()
