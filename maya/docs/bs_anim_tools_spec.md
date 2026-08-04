# BS Anim 工具规格说明

**工具：** BS Anim Export（导出）· BS Anim Import（导入）  
**运行环境：** Maya（Python，PySide2）  
**当前状态：** 原型可用，待正式化

---

## 0. 使用场景

### 场景 A — 跨绑定 / 跨场景传递动画

在**源场景**：打开 BS Anim Export，选择 blendShape 节点，设置输出路径，点击导出。  
将 JSON 文件复制到目标机器。  
在**目标场景**：打开 BS Anim Import，选择目标节点，加载 JSON，点击导入。  
查看状态栏——如有跳过的目标，说明目标名称不匹配。

> 源节点与目标节点的目标名称必须完全一致，工具仅按名称匹配。

---

### 场景 B — 动画存档与回滚

正常制作动画，导出到带版本号的路径（如 `face_v02.json`）。  
如果当前版本出问题：导入该文件并勾选"替换已有关键帧"即可恢复。

> 版本管理为手动操作，工具不提供自动历史记录。

---

### 场景 C — 同场景内跨节点复制

从节点 A 导出，导入到节点 B。  
名称匹配的目标正常导入；不匹配的目标被跳过，并在状态栏中列出。

---

## 1. BS Anim Export（`bs_anim_export.py`）

### 用途

将单个 blendShape 节点上所有**有动画**的权重曲线序列化为 JSON 文件。在源 Maya 实例中运行，用于将动画迁移到其他绑定或场景。

此 JSON 格式为共用交换格式，由本工具、BS Anim Import 以及规划中的 **BS制作工具** 共同读写。

### 界面

`QDialog`（宽 400），包含：
- blendShape 节点下拉框（自动从 `cmds.ls(type='blendShape')` 填充）
- 输出 JSON 路径输入框 + 文件浏览按钮（默认 `C:/tmp/bs_anim.json`）
- 导出按钮

### 核心函数

```python
export_bs_anim(bs_node: str, output_path: str) -> int
```

返回写入的曲线数量。

**每个目标导出的字段：**

| 字段 | Maya 调用 |
|---|---|
| `times` | `cmds.keyframe(attr, q=True, timeChange=True)` |
| `values` | `cmds.keyframe(attr, q=True, valueChange=True)` |
| `inTangentType` / `outTangentType` | `cmds.keyTangent(..., inTangentType=True)` |
| `inAngle` / `outAngle` | `cmds.keyTangent(..., inAngle=True)` |
| `inWeight` / `outWeight` | `cmds.keyTangent(..., inWeight=True)` |
| `weightedTangents` | `cmds.keyTangent(..., weightedTangents=True)` |
| `preInfinite` / `postInfinite` | `cmds.setInfinity(..., preInfinite=True)` |

**无关键帧的目标会被跳过**，不写入文件。

### JSON 格式

```json
{
  "blendShape": "<节点名>",
  "curves": {
    "<目标名>": {
      "times":            [0.0, 5.0, 12.0],
      "values":           [0.0, 1.0, 0.0],
      "inTangentType":    ["auto", "auto", "auto"],
      "outTangentType":   ["auto", "auto", "auto"],
      "inAngle":          [0.0, 0.0, 0.0],
      "outAngle":         [0.0, 0.0, 0.0],
      "inWeight":         [1.0, 1.0, 1.0],
      "outWeight":        [1.0, 1.0, 1.0],
      "weightedTangents": false,
      "preInfinite":      "constant",
      "postInfinite":     "constant"
    }
  }
}
```

---

## 2. BS Anim Import（`bs_anim_import.py`）

### 用途

将 JSON 文件中的 blendShape 权重曲线应用到目标场景的 blendShape 节点上。按目标名称匹配，名称不匹配的目标被跳过（不报错）。

### 界面

`QDialog`（宽 420），包含：
- 目标 blendShape 节点下拉框
- 源 JSON 路径输入框 + 文件浏览按钮
- "替换已有关键帧"复选框（默认勾选）
- 导入按钮

### 核心函数

```python
import_bs_anim(dst_bs_node: str, json_path: str, replace: bool = True) -> (list, list)
```

返回 `(已导入目标列表, 已跳过目标列表)`。

### 执行逻辑

1. 读取 JSON，获取 `curves` 字典。
2. 通过 `cmds.aliasAttr` 获取目标节点的所有目标名称。
3. 逐目标处理：
   - **目标节点中不存在** → 加入跳过列表，不写入任何数据。
   - **目标节点中存在且 `replace=True`** → 先用 `cmds.cutKey(..., clear=True)` 删除已有关键帧，再写入。
4. 用 `cmds.setKeyframe` 逐帧写入关键帧，再用 `cmds.keyTangent` 逐帧设置切线。
5. 切线角度与权重**仅在非自动切线类型下设置**（`auto`、`clamped`、`plateau` 不设置），避免覆盖 Maya 自动计算的切线。
6. 用 `cmds.setInfinity` 设置无限循环类型。

### 状态栏颜色

- 绿色 `#8fc87a` — 全部导入，无跳过
- 橙色 `#c8a040` — 部分导入，有名称不匹配被跳过
- 红色 `#c87050` — 发生异常

---

## 3. 已知问题 / 正式化前需决策的事项

| # | 问题 | 说明 |
|---|---|---|
| 1 | **导出的节点名在导入时未被使用** | JSON 中记录了 `"blendShape": "<名称>"`，但导入函数忽略此字段，直接使用传入的 `dst_bs_node` 参数。设计上是有意为之（支持迁移到不同名的节点），但可能让用户困惑。建议在导入界面增加只读的"源节点名"显示字段。 |
| 2 | **仅导出有动画的目标** | 无关键帧的目标会被静默忽略。若需要导出包含静态值的姿态快照，当前导出工具不支持。 |
| 3 | **导入无 undo 块** | 关键帧逐个写入，没有包裹在 `cmds.undoInfo(openChunk/closeChunk)` 中。导入中途失败会留下部分状态，撤销需要多步操作。 |
| 4 | **未做 PySide2 / PySide6 兼容处理** | Maya 2025 及以上使用 PySide6，当前工具无条件导入 PySide2，在新版本 Maya 中会报错。 |
| 5 | **默认路径硬编码为 `C:/tmp/`** | 仅适用于 Windows。应改为 `tempfile.gettempdir()` 或项目相对路径。 |
| 6 | **未接入本地化系统** | 界面字符串硬编码为英文。若要并入 MotionKit 菜单，需改用 `t()` 调用，并在 `en.json` / `zh.json` 中添加对应条目。 |
