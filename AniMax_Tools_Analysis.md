# AniMax Tools Analysis & Reverse Engineering

## Overview
AniMax is a comprehensive animation toolset for 3ds Max, compiled into Python extension modules (.pyd files). The tools are primarily focused on character animation, FBX export, and pipeline automation.

## Discovered Tool Names

### Main UI (tools_entry_max.cp39-win_amd64.pyd)
**Chinese Name:** 动画工具集 - 202512.1
**English:** Animation Tools Collection - 202512.1

The main entry point creates a Qt-based UI with buttons for each tool module.

### Tool Modules

1. **动画基础工具** (BaseAnimateTool)
   - **Module:** `BaseAnimateTool.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/BaseAnimateTool/`
   - **Size:** 449 KB
   - **Description:** Core animation tools

2. **白银用FBX导出工具** (ExportScriptFBX)
   - **Module:** `ExportScriptFBX.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/ExportScriptFBX/`
   - **Size:** 939 KB
   - **Description:** Silver FBX Export Tool

3. **CS骨骼镜像工具** (MirrorCS)
   - **Module:** `MirrorCS.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/MirrorCS/`
   - **Size:** 65 KB
   - **Description:** CS Bone Mirror Tool

4. **动画拆分** (SplitFile2)
   - **Module:** `SplitFile2.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/SplitFile2/`
   - **Description:** Animation Splitting Tool

5. **一键换绑定** (AutoChangeRigging)
   - **Module:** `AutoChangeRigging.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/AutoChangeRigging/`
   - **Description:** One-Click Rigging Replacement

6. **根节点动画拷贝** (CopyBipRootAniToRoot)
   - **Module:** `CopyBipRootAniToRoot.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/CopyBipRootAniToRoot/`
   - **Description:** Root Node Animation Copy

7. **修复乱转** (CgjoySpring)
   - **Module:** `CgjoySpring.cp39-win_amd64.pyd`
   - **Path:** `App/3DMax/3DMax2023/Module/ani_ms/CgjoySpring/`
   - **Description:** Fix Rotation Issues

---

## Key Findings

### 1. 同步组 (Sync Group) Tool

**Location:** Found in `BaseAnimateTool.cp39-win_amd64.pyd` and `ExportScriptFBX.cp39-win_amd64.pyd`

**Purpose:**
- Synchronizes animation groups across bones
- Manages custom attributes for bone synchronization
- Determines if animation is small or large amplitude motion

**Key Functionality (from extracted strings):**
- `---删除所有导入骨骼的自定义属性---同步组属性需要重载，因为属性不会替换，只能新加`
  - "Delete all custom attributes from imported bones --- Sync group attributes need to be reloaded because attributes won't be replaced, only newly added"

- `----同步组--只能判定整个动画是小幅度运动还是大幅度运动，暂时不考虑两种的混合运动！！！！`
  - "Sync Group -- Can only determine if the entire animation is small amplitude motion or large amplitude motion, temporarily not considering mixed motion!!!!!"

**Technical Details:**
- Works with custom MaxScript attributes
- Requires attribute reloading when importing bones
- Motion amplitude detection for animation analysis
- Cannot handle mixed amplitude motions in single animation

---

### 2. BsKey Tool - **NOT FOUND**

**Search Results:** No explicit "BsKey" tool was found in the compiled modules.

**Possible Alternatives:**
The morpher/blendshape functionality is integrated into the **ExportScriptFBX** module:
- `------关于morpher的检查` (About morpher checking)
- `----morpher通道检查` (Morpher channel checking)
- `----删除morpher非关键帧` (Delete morpher non-keyframes)
- `fn ExportFBXParamForBs = --morpher的删帧导出`

This suggests that blendshape (Bs) key functionality is part of the FBX export tool rather than a standalone module.

---

## BaseAnimateTool - Detailed Features

### Rollout Panels

1. **BaseAnimateTool** - 动画小工具 (Animation Small Tools)
2. **HoudiniAniToMax** - Houdini动画导入Max
3. **ImportFbxAniToCs** - 导入Fbx动画
4. **MaxFilesRiging** - Max文件前期架设准备
5. **MultiRolesScence** - 添加叠加动画(坐骑) (Add Overlay Animation - Mount)
6. **AniLayerAdd** - 骑乘动画合并 (Riding Animation Merge)

### Key Functions

#### Animation Tools
- `AlignBoneChainsPos` - 骨骼末端位置对齐 (Bone Chain End Position Alignment)
- `AlignBonesPos` - 位置对齐 (Position Alignment)
- `AlignFrame` - 对齐指定帧 (Align Specific Frame)
- `MakeLoopAni` - 生成循环动画 (Create Loop Animation)
- `CopyAniToMaxBone` - 开始 (Start)

#### Bone Management
- `MakeBones` - 骨骼生成 (Bone Generation)
- `AddBallToChains` - 把现有骨骼练添加球体 (Add Spheres to Bone Chains)
- `DepartChains` - 拆分Fbx骨骼链条 (Split FBX Bone Chains)
- `AlignWeapenPosition` - 灰姑娘武器位置对齐 (Cinderella Weapon Position Alignment)

#### FBX Import/Export
- `AddAni` - 导入Fbx动画 (Import FBX Animation)
- `autoCombineFbx` - 自动合并fbx (Auto Combine FBX)
- `DepartRole` - 叠加动画 (Overlay Animation)
- `MergeRole` - 合并文件 (Merge Files)

#### Overlay Animation (叠加动画)
- `GetAllCsNodes` - 选择叠加动画节点 (Select Overlay Animation Nodes)
- `CopyOverlayAni` - 拷贝叠加动画姿势 (Copy Overlay Animation Posture)
- `AddOverLayerAnimationWithLocalTm` - 最终方式 (Final Method)

#### Scene Management
- `CreateGif` - 动画预览文件生成 (Animation Preview File Generation)
- `UnhideSelection` - 显示所选物体 (Show Selected Objects)
- `FindtheLostBone` - 选中丢失的骨骼 (Select Lost Bones)

---

## ExportScriptFBX - Detailed Features

### FBX Export with Character Detection
The tool includes sophisticated foot detection for characters:

#### Supported Characters
- **Cynthia** (女法医)
- **Munin**

#### Foot Animation Detection Parameters
```maxscript
#("Cynthia_angleSpeed", 1.2)
#("Cynthia_hasMoving", 0.22)
#("Cynthia_toleranceMax", 0.4)
#("Cynthia_tinyRange", [4.5,1.4])
#("Cynthia_defaulPlane", [0.0125936,-0.562319,-0.826825])
#("Cynthia_toeUp", [-0.0116897,-0.63704,-0.770742])
#("Cynthia_toeDown", [0.0132505,-0.4976,-0.867305])
```

### Key Features

1. **Frame Rate Support**
   - 30fps and 60fps animations
   - Automatic frame rate detection

2. **Morpher/BlendShape Management**
   - Morpher channel checking
   - Delete non-keyframes for morphers
   - Key optimization for blendshapes

3. **Root Bone Locking**
   - `----加入根骨骼锁定` (Add root bone locking)
   - `----如果导出了根骨骼锁定，那么需要回滚文件` (If root bone locking exported, need to rollback file)

4. **Foot Motion Analysis**
   ```
   FeetArrHasNagetiveNum - Check if array contains negative values
   FeetArrCreatedByOrder - Analyze if array follows 0,2,1 order
   GetTheFeetArrMinAndMaxWithSpeed - Calculate min/max range for speed
   RedefineTheFeetArrBySegment - Micro-analysis between segments
   ```

5. **Sync Group Integration**
   - Motion amplitude detection (small/large)
   - Determines animation type for export optimization

6. **Non-uniform Scale Export**
   - `-------------加入非等比缩放导出，改骨骼链接关系`
   - Records bone matrix information before export
   - Modifies bone hierarchy for non-uniform scaling

---

## Technical Architecture

### Module Structure
```
ani_tools/
├── tools_entry_max.cp39-win_amd64.pyd  (Main UI - 84 KB)
├── App/
│   ├── 3DMax/3DMax2023/
│   │   ├── MaxCore/
│   │   │   └── MaxCore.cp39-win_amd64.pyd
│   │   └── Module/ani_ms/
│   │       ├── BaseAnimateTool/BaseAnimateTool.cp39-win_amd64.pyd (449 KB)
│   │       ├── ExportScriptFBX/ExportScriptFBX.cp39-win_amd64.pyd (939 KB)
│   │       ├── MirrorCS/MirrorCS.cp39-win_amd64.pyd (65 KB)
│   │       ├── SplitFile2/
│   │       ├── AutoChangeRigging/
│   │       ├── CopyBipRootAniToRoot/
│   │       └── CgjoySpring/
│   └── Common/UI/
│       └── UI.cp39-win_amd64.pyd
├── Core/py39/
│   ├── Get/
│   │   ├── Get.cp39-win_amd64.pyd
│   │   ├── FBXGet.cp39-win_amd64.pyd
│   │   └── MayaGet.cp39-win_amd64.pyd
│   └── DBCore/
└── Evn/
    └── Pipeline/ (3ds Max plugins - .gup files)
```

### Dependencies
- **Python 3.9** (cp39)
- **pymxs** - 3ds Max Python integration
- **PySide2/Qt** - UI framework
- **FBX SDK** - FBX import/export
- **PIL/Pillow** - Image processing for preview generation

### UI Framework
```python
class ToolsEntry:
    def __init__(self):
        # Creates QPushButton for each tool
        # Dynamically loads tool modules

    def launch_tool(self):
        # Module.ani_ms.BaseAnimateTool.BaseAnimateTool
        # Module.ani_ms.ExportScriptFBX.ExportScriptFBX
        # Module.ani_ms.MirrorCS.MirrorCS

    def update_grid_layout(self):
        # Auto-adjusts button layout based on window size

    def resizeEvent(self):
        # Triggers layout update on window resize
```

---

## Limitations & Constraints

1. **Expiration Date**
   - Tool expires on **January 01, 2026**

2. **Supported Max Versions**
   - 3ds Max 2018-2025

3. **Sync Group Limitations**
   - Cannot handle mixed amplitude motions in a single animation
   - Only detects overall animation as small OR large amplitude

4. **Character-Specific**
   - Foot detection parameters hardcoded for specific characters (Cynthia, Munin)
   - May need recalibration for other characters

---

## Next Steps for Recreation

### Priority 1: Core Animation Tools
1. **Loop Animation Generator**
   - Recreate `MakeLoopAni` function
   - Handle quaternion interpolation for rotation
   - Position offset smoothing

2. **Bone Alignment System**
   - Position alignment tools
   - Chain end alignment
   - Frame-specific alignment

### Priority 2: Sync Group System
1. **Motion Amplitude Detector**
   - Analyze animation velocity/amplitude
   - Classify as small/large motion
   - Custom attribute management

2. **Group Synchronization**
   - Sync multiple bone chains
   - Custom attribute propagation
   - Handle import/export attribute preservation

### Priority 3: FBX Export Enhancement
1. **Morpher Optimization**
   - Key frame reduction for blend shapes
   - Channel validation
   - Export parameter optimization

2. **Foot Detection System**
   - Generic foot contact detection
   - Character-agnostic parameters
   - Motion analysis for walk cycles

### Priority 4: UI Recreation
1. **Main Tool Launcher**
   - Qt-based button grid
   - Dynamic module loading
   - Responsive layout

2. **Individual Tool UIs**
   - Recreate each rollout panel
   - MaxScript-based dialogs for Max
   - PySide2 for standalone tools

---

## Extracted MaxScript Code Snippets

### Loop Animation
```maxscript
fn MakeLoopAni =
    -- Quaternion double coverage handling
    -- if val < 0 then -- Check if quaternion dot product is negative
    -- Position offset smoothing across frames
```

### Sync Group Attribute Management
```maxscript
-- Delete all imported bone custom attributes
-- Sync group attributes need to be reloaded
-- Because attributes won't be replaced, only newly added
```

### Foot Contact Detection
```maxscript
fn SetFirstFrameFeetValue characterName =
    -- Determines initial foot state at frame 0
    -- Gets ground contact value for character model

fn FeetArrHasNagetiveNum feetValArr =
    -- Check if array contains negative values (-1)

fn FeetArrCreatedByOrder feetValArr =
    -- Analyze if array follows 0,2,1 order pattern
```

### Overlay Animation (叠加动画)
```maxscript
fn AddOverLayerAnimationWithLocalTm departPath onePosPath =
    -- Final method for overlay animation

-- Create copy collection
biped.createCopyCollection $HE1.controller "overLayPosture"

-- Delete all collections
biped.deleteAllCopyCollections $HE1.controller

-- Copy posture
posName = biped.copyPosture $HE1.controller #posture false false false
```

---

## Conclusion

The AniMax toolset is a sophisticated animation pipeline tool with deep integration into 3ds Max's Biped system. The **同步组 (Sync Group)** functionality is embedded within the BaseAnimateTool and ExportScriptFBX modules, focusing on motion amplitude detection and custom attribute synchronization.

The **BsKey tool does not exist as a separate module** - blendshape/morpher key functionality is integrated into the ExportScriptFBX tool.

To properly recreate these tools, we need to:
1. Understand the underlying MaxScript/pymxs APIs
2. Reverse-engineer the motion detection algorithms
3. Recreate the UI in Qt/MaxScript
4. Implement the attribute management system
5. Build the FBX export optimization pipeline

Would you like me to start recreating any specific tool first?
