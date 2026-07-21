"""
BS Anim Import
Run in the TARGET Maya instance.
Imports blendshape weight curves from a JSON exported by bs_anim_export.py.
Matches by target name. Skips targets that don't exist on the destination node.
"""

import json
import maya.cmds as cmds
from maya import OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
import shiboken2


def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)


def _get_blendshape_nodes():
    return cmds.ls(type='blendShape') or []


def _get_targets(bs_node):
    aliases = cmds.aliasAttr(bs_node, q=True) or []
    return [aliases[i] for i in range(0, len(aliases), 2)]


def import_bs_anim(dst_bs_node, json_path, replace=True):
    with open(json_path, 'r') as f:
        data = json.load(f)

    dst_targets = set(_get_targets(dst_bs_node))
    curves = data.get('curves', {})

    imported = []
    skipped  = []

    for target, cdata in curves.items():
        if target not in dst_targets:
            skipped.append(target)
            continue

        attr = '{}.{}'.format(dst_bs_node, target)

        if replace:
            existing = cmds.keyframe(attr, query=True, keyframeCount=True)
            if existing:
                cmds.cutKey(attr, clear=True)

        times  = cdata['times']
        values = cdata['values']

        # Set keys
        for t, v in zip(times, values):
            cmds.setKeyframe(attr, time=t, value=v)

        # Set tangents
        wt = cdata.get('weightedTangents', False)
        cmds.keyTangent(attr, edit=True, weightedTangents=wt)

        for i, t in enumerate(times):
            it = cdata['inTangentType'][i]
            ot = cdata['outTangentType'][i]
            ia = cdata['inAngle'][i]
            oa = cdata['outAngle'][i]
            iw = cdata['inWeight'][i]
            ow = cdata['outWeight'][i]

            kwargs = dict(time=(t, t), inTangentType=it, outTangentType=ot)
            cmds.keyTangent(attr, edit=True, **kwargs)

            # Only set angles/weights for non-auto tangent types
            if it not in ('auto', 'clamped', 'plateau'):
                cmds.keyTangent(attr, edit=True, time=(t, t), inAngle=ia)
            if ot not in ('auto', 'clamped', 'plateau'):
                cmds.keyTangent(attr, edit=True, time=(t, t), outAngle=oa)
            if wt:
                cmds.keyTangent(attr, edit=True, time=(t, t), inWeight=iw, outWeight=ow)

        # Infinity
        pre  = cdata.get('preInfinite',  'constant')
        post = cdata.get('postInfinite', 'constant')
        cmds.setInfinity(attr, preInfinite=pre, postInfinite=post)

        imported.append(target)

    print('[bs_anim_import] Imported: {} | Skipped (not in dst): {}'.format(
        len(imported), len(skipped)))
    if skipped:
        print('[bs_anim_import] Skipped targets: {}'.format(', '.join(skipped)))

    return imported, skipped


class ImportUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ImportUI, self).__init__(parent or _maya_main_window())
        self.setWindowTitle('BS Anim Import')
        self.setFixedWidth(420)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build()

    def _build(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(6)
        lay.setContentsMargins(10, 10, 10, 10)

        lay.addWidget(QtWidgets.QLabel('Destination BlendShape Node:'))
        self._bs_combo = QtWidgets.QComboBox()
        self._bs_combo.addItems(_get_blendshape_nodes() or ['-- none found --'])
        lay.addWidget(self._bs_combo)

        lay.addWidget(QtWidgets.QLabel('Source JSON:'))
        row = QtWidgets.QHBoxLayout()
        self._path = QtWidgets.QLineEdit('C:/tmp/bs_anim.json')
        row.addWidget(self._path)
        browse = QtWidgets.QPushButton('…')
        browse.setFixedWidth(28)
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        lay.addLayout(row)

        self._replace_cb = QtWidgets.QCheckBox('Replace existing keys')
        self._replace_cb.setChecked(True)
        lay.addWidget(self._replace_cb)

        btn = QtWidgets.QPushButton('Import')
        btn.setFixedHeight(34)
        btn.setStyleSheet('background:#2d4f7a; color:white; border-radius:4px;')
        btn.clicked.connect(self._import)
        lay.addWidget(btn)

        self._status = QtWidgets.QLabel('')
        self._status.setWordWrap(True)
        lay.addWidget(self._status)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open JSON', self._path.text(), 'JSON (*.json)')
        if path:
            self._path.setText(path)

    def _import(self):
        bs   = self._bs_combo.currentText()
        path = self._path.text().strip()
        replace = self._replace_cb.isChecked()
        if not bs or not path:
            return
        try:
            imported, skipped = import_bs_anim(bs, path, replace=replace)
            msg = 'Imported {} curves.'.format(len(imported))
            if skipped:
                msg += ' Skipped {} (name mismatch): {}'.format(
                    len(skipped), ', '.join(skipped))
            color = '#8fc87a' if not skipped else '#c8a040'
            self._status.setStyleSheet('color:{};'.format(color))
            self._status.setText(msg)
        except Exception as e:
            self._status.setStyleSheet('color:#c87050;')
            self._status.setText('Error: {}'.format(e))


def show():
    global _win
    try:
        _win.close()
        _win.deleteLater()
    except Exception:
        pass
    _win = ImportUI()
    _win.show()
