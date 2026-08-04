"""
BS Anim 导出/导入 单元测试
无 Maya 依赖 — maya.cmds 全程使用 Mock 替代
"""

import json
import sys
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 在导入工具模块前，先将 Maya 相关模块 stub 掉
for mod in ('maya', 'maya.cmds', 'maya.OpenMayaUI', 'PySide2',
            'PySide2.QtWidgets', 'PySide2.QtCore', 'shiboken2'):
    sys.modules.setdefault(mod, MagicMock())

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / 'maya'))

import bs_anim_export as export_mod
import bs_anim_import as import_mod


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _make_curve(times, values, tangent_type='auto', weighted=False,
                pre='constant', post='constant'):
    n = len(times)
    return {
        'times':            list(times),
        'values':           list(values),
        'inTangentType':    [tangent_type] * n,
        'outTangentType':   [tangent_type] * n,
        'inAngle':          [0.0] * n,
        'outAngle':         [0.0] * n,
        'inWeight':         [1.0] * n,
        'outWeight':        [1.0] * n,
        'weightedTangents': weighted,
        'preInfinite':      pre,
        'postInfinite':     post,
    }


def _write_json(data, directory):
    path = os.path.join(directory, 'test_bs.json')
    with open(path, 'w') as f:
        json.dump(data, f)
    return path


# ---------------------------------------------------------------------------
# 导出 — 核心函数
# ---------------------------------------------------------------------------

class TestExportBsAnim(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _patch_cmds(self, targets, key_data):
        """
        targets  : 节点上的目标名称列表
        key_data : dict，target -> (times, values)；无关键帧则为空列表
        """
        cmds = MagicMock()

        def aliasAttr(node, q):
            flat = []
            for t in targets:
                flat += [t, f'weight[{targets.index(t)}]']
            return flat

        def keyframe(attr, query, **kwargs):
            target = attr.split('.')[-1]
            if 'keyframeCount' in kwargs:
                return len(key_data.get(target, (None, None))[0] or [])
            if 'timeChange' in kwargs:
                return key_data[target][0]
            if 'valueChange' in kwargs:
                return key_data[target][1]
            return []

        def keyTangent(attr, query, **kwargs):
            target = attr.split('.')[-1]
            n = len(key_data.get(target, ([], []))[0] or [])
            if 'inTangentType' in kwargs:
                return ['auto'] * n
            if 'outTangentType' in kwargs:
                return ['auto'] * n
            if 'inAngle' in kwargs:
                return [0.0] * n
            if 'outAngle' in kwargs:
                return [0.0] * n
            if 'inWeight' in kwargs:
                return [1.0] * n
            if 'outWeight' in kwargs:
                return [1.0] * n
            if 'weightedTangents' in kwargs:
                return [False]
            return []

        def setInfinity(attr, query, **kwargs):
            if 'preInfinite' in kwargs:
                return ['constant']
            if 'postInfinite' in kwargs:
                return ['constant']
            return []

        cmds.aliasAttr.side_effect = aliasAttr
        cmds.keyframe.side_effect = keyframe
        cmds.keyTangent.side_effect = keyTangent
        cmds.setInfinity.side_effect = setInfinity
        return cmds

    def test_导出有动画的目标(self):
        key_data = {
            'browUp':    ([0.0, 5.0, 10.0], [0.0, 1.0, 0.0]),
            'mouthOpen': ([0.0, 8.0],        [0.0, 0.8]),
        }
        cmds = self._patch_cmds(['browUp', 'mouthOpen'], key_data)
        out = os.path.join(self.tmp, 'out.json')
        with patch.object(export_mod, 'cmds', cmds):
            count = export_mod.export_bs_anim('faceBS', out)

        self.assertEqual(count, 2)
        with open(out) as f:
            data = json.load(f)
        self.assertEqual(data['blendShape'], 'faceBS')
        self.assertIn('browUp', data['curves'])
        self.assertIn('mouthOpen', data['curves'])
        self.assertEqual(data['curves']['browUp']['times'],  [0.0, 5.0, 10.0])
        self.assertEqual(data['curves']['browUp']['values'], [0.0, 1.0, 0.0])

    def test_跳过无关键帧的目标(self):
        key_data = {
            'browUp':   ([0.0, 5.0], [0.0, 1.0]),
            'cheekPuff': ([], []),   # 无关键帧
        }
        cmds = self._patch_cmds(['browUp', 'cheekPuff'], key_data)
        out = os.path.join(self.tmp, 'out.json')
        with patch.object(export_mod, 'cmds', cmds):
            count = export_mod.export_bs_anim('faceBS', out)

        self.assertEqual(count, 1)
        with open(out) as f:
            data = json.load(f)
        self.assertIn('browUp', data['curves'])
        self.assertNotIn('cheekPuff', data['curves'])

    def test_空节点写出空curves(self):
        cmds = self._patch_cmds([], {})
        out = os.path.join(self.tmp, 'out.json')
        with patch.object(export_mod, 'cmds', cmds):
            count = export_mod.export_bs_anim('faceBS', out)

        self.assertEqual(count, 0)
        with open(out) as f:
            data = json.load(f)
        self.assertEqual(data['curves'], {})

    def test_JSON包含所有必要字段(self):
        key_data = {'jawOpen': ([0.0, 3.0], [0.0, 1.0])}
        cmds = self._patch_cmds(['jawOpen'], key_data)
        out = os.path.join(self.tmp, 'out.json')
        with patch.object(export_mod, 'cmds', cmds):
            export_mod.export_bs_anim('faceBS', out)

        with open(out) as f:
            data = json.load(f)
        curve = data['curves']['jawOpen']
        for field in ('times', 'values', 'inTangentType', 'outTangentType',
                      'inAngle', 'outAngle', 'inWeight', 'outWeight',
                      'weightedTangents', 'preInfinite', 'postInfinite'):
            self.assertIn(field, curve, f'缺少字段: {field}')


# ---------------------------------------------------------------------------
# 导入 — 核心函数
# ---------------------------------------------------------------------------

class TestImportBsAnim(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_export(self, curves):
        data = {'blendShape': 'srcBS', 'curves': curves}
        return _write_json(data, self.tmp)

    def _make_cmds(self, dst_targets):
        cmds = MagicMock()

        def aliasAttr(node, q):
            flat = []
            for i, t in enumerate(dst_targets):
                flat += [t, f'weight[{i}]']
            return flat

        cmds.aliasAttr.side_effect = aliasAttr
        cmds.keyframe.return_value = 0  # 默认无已有关键帧
        return cmds

    def test_导入名称匹配的目标(self):
        curves = {
            'browUp':  _make_curve([0.0, 5.0], [0.0, 1.0]),
            'jawOpen': _make_curve([0.0, 8.0], [0.0, 0.5]),
        }
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp', 'jawOpen'])
        with patch.object(import_mod, 'cmds', cmds):
            imported, skipped = import_mod.import_bs_anim('dstBS', path)

        self.assertIn('browUp', imported)
        self.assertIn('jawOpen', imported)
        self.assertEqual(skipped, [])

    def test_跳过目标节点中不存在的目标(self):
        curves = {
            'browUp':     _make_curve([0.0, 5.0], [0.0, 1.0]),
            'noseScrunch': _make_curve([0.0, 3.0], [0.0, 1.0]),  # 目标节点中无此项
        }
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        with patch.object(import_mod, 'cmds', cmds):
            imported, skipped = import_mod.import_bs_anim('dstBS', path)

        self.assertIn('browUp', imported)
        self.assertIn('noseScrunch', skipped)

    def test_替换模式清除已有关键帧(self):
        curves = {'browUp': _make_curve([0.0, 5.0], [0.0, 1.0])}
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        cmds.keyframe.return_value = 3  # 已有关键帧

        with patch.object(import_mod, 'cmds', cmds):
            import_mod.import_bs_anim('dstBS', path, replace=True)

        cmds.cutKey.assert_called_once()

    def test_非替换模式保留已有关键帧(self):
        curves = {'browUp': _make_curve([0.0, 5.0], [0.0, 1.0])}
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        cmds.keyframe.return_value = 3

        with patch.object(import_mod, 'cmds', cmds):
            import_mod.import_bs_anim('dstBS', path, replace=False)

        cmds.cutKey.assert_not_called()

    def test_所有目标不匹配时全部跳过(self):
        curves = {
            'targetA': _make_curve([0.0], [1.0]),
            'targetB': _make_curve([0.0], [1.0]),
        }
        path = self._write_export(curves)
        cmds = self._make_cmds([])  # 目标节点无任何目标
        with patch.object(import_mod, 'cmds', cmds):
            imported, skipped = import_mod.import_bs_anim('dstBS', path)

        self.assertEqual(imported, [])
        self.assertCountEqual(skipped, ['targetA', 'targetB'])

    def test_每个关键帧都调用setKeyframe(self):
        curves = {'browUp': _make_curve([0.0, 5.0, 10.0], [0.0, 1.0, 0.0])}
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        with patch.object(import_mod, 'cmds', cmds):
            import_mod.import_bs_anim('dstBS', path)

        self.assertEqual(cmds.setKeyframe.call_count, 3)

    def test_无限循环类型被正确设置(self):
        curves = {'browUp': _make_curve([0.0, 5.0], [0.0, 1.0],
                                        pre='cycle', post='cycle')}
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        with patch.object(import_mod, 'cmds', cmds):
            import_mod.import_bs_anim('dstBS', path)

        calls = [str(c) for c in cmds.setInfinity.call_args_list]
        self.assertTrue(any('cycle' in c for c in calls))

    def test_auto切线不设置角度和权重(self):
        curves = {'browUp': _make_curve([0.0, 5.0], [0.0, 1.0],
                                        tangent_type='auto')}
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        with patch.object(import_mod, 'cmds', cmds):
            import_mod.import_bs_anim('dstBS', path)

        # auto 切线不应设置 inAngle / outAngle
        for call in cmds.keyTangent.call_args_list:
            kwargs = call[1]
            self.assertNotIn('inAngle', kwargs)
            self.assertNotIn('outAngle', kwargs)

    def test_weighted切线开启时设置权重值(self):
        curves = {'browUp': _make_curve([0.0, 5.0], [0.0, 1.0],
                                        tangent_type='spline', weighted=True)}
        path = self._write_export(curves)
        cmds = self._make_cmds(['browUp'])
        with patch.object(import_mod, 'cmds', cmds):
            import_mod.import_bs_anim('dstBS', path)

        calls = [str(c) for c in cmds.keyTangent.call_args_list]
        self.assertTrue(any('inWeight' in c or 'outWeight' in c for c in calls))

    def test_JSON文件不存在时抛出异常(self):
        with patch.object(import_mod, 'cmds', MagicMock()):
            with self.assertRaises(FileNotFoundError):
                import_mod.import_bs_anim('dstBS', '/不存在的路径/bs.json')

    def test_JSON格式错误时抛出异常(self):
        bad = os.path.join(self.tmp, 'bad.json')
        with open(bad, 'w') as f:
            f.write('{格式错误的json')
        with patch.object(import_mod, 'cmds', MagicMock()):
            with self.assertRaises(json.JSONDecodeError):
                import_mod.import_bs_anim('dstBS', bad)


# ---------------------------------------------------------------------------
# 完整往返测试
# ---------------------------------------------------------------------------

class TestRoundTrip(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_导出的JSON可被完整导入(self):
        """导出后立即导入；切线类型与无限循环设置应完整保留。"""
        exp_cmds = MagicMock()

        def aliasAttr(node, q):
            return ['browUp', 'weight[0]']

        def keyframe(attr, query, **kwargs):
            if 'keyframeCount' in kwargs:
                return 3
            if 'timeChange' in kwargs:
                return [0.0, 5.0, 10.0]
            if 'valueChange' in kwargs:
                return [0.0, 1.0, 0.0]
            return []

        def keyTangent(attr, query, **kwargs):
            if 'inTangentType' in kwargs:
                return ['spline', 'spline', 'spline']
            if 'outTangentType' in kwargs:
                return ['spline', 'spline', 'spline']
            if 'inAngle' in kwargs:
                return [10.0, 20.0, 30.0]
            if 'outAngle' in kwargs:
                return [10.0, 20.0, 30.0]
            if 'inWeight' in kwargs:
                return [0.5, 0.5, 0.5]
            if 'outWeight' in kwargs:
                return [0.5, 0.5, 0.5]
            if 'weightedTangents' in kwargs:
                return [True]
            return []

        def setInfinity(attr, query, **kwargs):
            if 'preInfinite' in kwargs:
                return ['cycle']
            if 'postInfinite' in kwargs:
                return ['cycle']
            return []

        exp_cmds.aliasAttr.side_effect = aliasAttr
        exp_cmds.keyframe.side_effect = keyframe
        exp_cmds.keyTangent.side_effect = keyTangent
        exp_cmds.setInfinity.side_effect = setInfinity

        out = os.path.join(self.tmp, 'roundtrip.json')
        with patch.object(export_mod, 'cmds', exp_cmds):
            export_mod.export_bs_anim('srcBS', out)

        imp_cmds = MagicMock()
        imp_cmds.aliasAttr.side_effect = lambda node, q: ['browUp', 'weight[0]']
        imp_cmds.keyframe.return_value = 0

        with patch.object(import_mod, 'cmds', imp_cmds):
            imported, skipped = import_mod.import_bs_anim('dstBS', out)

        self.assertIn('browUp', imported)
        self.assertEqual(skipped, [])

        kt_calls = [str(c) for c in imp_cmds.keyTangent.call_args_list]
        self.assertTrue(any('spline' in c for c in kt_calls), '切线类型应为 spline')
        inf_calls = [str(c) for c in imp_cmds.setInfinity.call_args_list]
        self.assertTrue(any('cycle' in c for c in inf_calls), '无限循环类型应为 cycle')


if __name__ == '__main__':
    unittest.main(verbosity=2)
