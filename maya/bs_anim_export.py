"""
BS Anim Export
Run in the SOURCE Maya instance.
Exports all animated blendshape weight curves to a JSON file.
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


def export_bs_anim(bs_node, output_path):
    targets = _get_targets(bs_node)
    data = {'blendShape': bs_node, 'curves': {}}

    for target in targets:
        attr = '{}.{}'.format(bs_node, target)
        key_count = cmds.keyframe(attr, query=True, keyframeCount=True)
        if not key_count:
            continue

        times  = cmds.keyframe(attr, query=True, timeChange=True)
        values = cmds.keyframe(attr, query=True, valueChange=True)
        it     = cmds.keyTangent(attr, query=True, inTangentType=True)
        ot     = cmds.keyTangent(attr, query=True, outTangentType=True)
        ia     = cmds.keyTangent(attr, query=True, inAngle=True)
        oa     = cmds.keyTangent(attr, query=True, outAngle=True)
        iw     = cmds.keyTangent(attr, query=True, inWeight=True)
        ow     = cmds.keyTangent(attr, query=True, outWeight=True)
        wt     = cmds.keyTangent(attr, query=True, weightedTangents=True)
        pre    = cmds.setInfinity(attr, query=True, preInfinite=True)
        post   = cmds.setInfinity(attr, query=True, postInfinite=True)

        data['curves'][target] = {
            'times':            list(times),
            'values':           list(values),
            'inTangentType':    list(it),
            'outTangentType':   list(ot),
            'inAngle':          list(ia),
            'outAngle':         list(oa),
            'inWeight':         list(iw),
            'outWeight':        list(ow),
            'weightedTangents': bool(wt[0]) if wt else False,
            'preInfinite':      pre[0] if pre else 'constant',
            'postInfinite':     post[0] if post else 'constant',
        }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    count = len(data['curves'])
    print('[bs_anim_export] Exported {} curves from {} -> {}'.format(count, bs_node, output_path))
    return count


class ExportUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ExportUI, self).__init__(parent or _maya_main_window())
        self.setWindowTitle('BS Anim Export')
        self.setFixedWidth(400)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build()

    def _build(self):
        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(6)
        lay.setContentsMargins(10, 10, 10, 10)

        lay.addWidget(QtWidgets.QLabel('BlendShape Node:'))
        self._bs_combo = QtWidgets.QComboBox()
        self._bs_combo.addItems(_get_blendshape_nodes() or ['-- none found --'])
        lay.addWidget(self._bs_combo)

        lay.addWidget(QtWidgets.QLabel('Output JSON:'))
        row = QtWidgets.QHBoxLayout()
        self._path = QtWidgets.QLineEdit('C:/tmp/bs_anim.json')
        row.addWidget(self._path)
        browse = QtWidgets.QPushButton('…')
        browse.setFixedWidth(28)
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        lay.addLayout(row)

        btn = QtWidgets.QPushButton('Export')
        btn.setFixedHeight(34)
        btn.setStyleSheet('background:#2d6b3a; color:white; border-radius:4px;')
        btn.clicked.connect(self._export)
        lay.addWidget(btn)

        self._status = QtWidgets.QLabel('')
        self._status.setWordWrap(True)
        lay.addWidget(self._status)

    def _browse(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save JSON', self._path.text(), 'JSON (*.json)')
        if path:
            self._path.setText(path)

    def _export(self):
        bs = self._bs_combo.currentText()
        path = self._path.text().strip()
        if not bs or not path:
            return
        try:
            count = export_bs_anim(bs, path)
            self._status.setStyleSheet('color:#8fc87a;')
            self._status.setText('Exported {} curves -> {}'.format(count, path))
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
    _win = ExportUI()
    _win.show()
