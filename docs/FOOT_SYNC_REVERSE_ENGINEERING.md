# Foot Sync (同步组) - Reverse Engineering from AniMax

## Overview
The "同步组" (Sync Group) system in AniMax is a sophisticated foot contact detection and synchronization system for character animation. It analyzes foot movement to determine when feet are on the ground vs in the air, and classifies the animation's motion amplitude.

## Core Concepts

### Sync Group Values
The system uses three values to represent foot state:
- **0** = Foot on ground (planted)
- **1** = Foot transitioning (lifting/landing)
- **2** = Foot in air (fully lifted)

The pattern follows: `0, 2, 1, 0, 2, 1` for a walking cycle
- If value is **-1** = Undetermined (needs analysis)

### Motion Amplitude Classification
The system classifies animations as:
- **Small amplitude motion** (小幅度运动) - e.g., idle, subtle shifts
- **Large amplitude motion** (大幅度运动) - e.g., running, jumping
- **Cannot handle mixed motions** in a single animation

---

## Key MaxScript Functions (Extracted)

### Main Analysis Functions

#### 1. `ExcutSyncFeetArr CharacterName csPivot isTrue`
**Purpose:** Main execution function for foot sync analysis
- **CharacterName**: Character identifier (e.g., "Munin", "Cynthia")
- **csPivot**: CS center/pivot (Biped root)
- **isTrue**: Boolean flag for left/right foot

#### 2. `ComputFeetUpAndDown csHe1 minSpeed &leftCsToePosArr &rightCsToePosArr`
**Purpose:** Compute foot up/down states by analyzing timeline twice
- Gets position arrays and direction arrays
- Left and right foot have different frame counts
- Uses speed threshold to determine state

#### 3. `FeetIsOnGround toeHight feetHight CharacterName`
**Purpose:** Static determination if foot is on ground
- Checks toe height and foot height
- Returns initial assessment
- If no frame is on ground, returns error

### Detection Helper Functions

#### 4. `FristFrameRedefineVal feetArr`
**Purpose:** If first frame is determined as -1, re-analyze it
- Handles initial frame ambiguity
- Ensures first frame has valid state

#### 5. `GetCsFootAngSpeedArr oneLocTm AfterLocTm`
**Purpose:** Calculate angular speed of foot
- Removes X plane values for accurate foot lift calculation
- Uses root point as parent reference
- Returns angular velocity

#### 6. `AccordingLocalAngleGetFeetS`
**Purpose:** Get foot state based on local angle
- Analyzes foot-to-shin angle
- Determines if toe is up or down

### Array Processing Functions

#### 7. `CombineTheArrs CharacterName`
**Purpose:** Determine first frame state (0, 1, or 2)
- If first frame not on ground, analyze entire animation
- Check if any ground contact exists
- Exit if no ground contact found

#### 8. `FixTheDirArray &dirArray`
**Purpose:** Fix/correct the direction array
- Ensures proper sequence
- Validates order

#### 9. `CheckTheFeetValArr`
**Purpose:** Check if array contains undetermined sync group data (-1 values)
- Validates sync group data completeness

---

## Character-Specific Parameters

### Global Height Dictionary
```maxscript
global fGlobalCharacterFeetHightVal = Dictionary \
    #("Munin_toe", [3.46887, 4.0, 4.76591]) \
    #("Munin_feet", [14.8366, 15.5, 16.0052])
```

**Munin_toe values:**
- `3.46887` = Toe down minimum (tip-toe, heel raised, toe touching ground)
- `4.0` = Toe flat value
- `4.76591` = Toe up maximum (heel down, toe curled up)

**Munin_feet values:**
- `14.8366` = Foot down minimum
- `15.5` = Foot neutral
- `16.0052` = Foot up maximum

**Purpose:** Different characters have different heights, so each needs custom thresholds to determine when foot contacts ground

### Cynthia Parameters (from analysis doc)
```maxscript
#("Cynthia_angleSpeed", 1.2)
#("Cynthia_hasMoving", 0.22)
#("Cynthia_toleranceMax", 0.4)
#("Cynthia_tinyRange", [4.5, 1.4])
#("Cynthia_defaulPlane", [0.0125936, -0.562319, -0.826825])
#("Cynthia_toeUp", [-0.0116897, -0.63704, -0.770742])
#("Cynthia_toeDown", [0.0132505, -0.4976, -0.867305])
```

---

## Detection Algorithm (Reconstructed)

### Step 1: Initialize Foot Data
```maxscript
global leftCsToeDirArr = #()        -- Left foot direction
global rightCsToeDirArr = #()       -- Right foot direction
global leftCsFeetPosArr = #()       -- Left foot positions
global rightCsFeetPosArr = #()      -- Right foot positions
leftFeetValArr = #()                -- Left foot values (0,1,2,-1)
rightFeetValArr = #()               -- Right foot values (0,1,2,-1)
```

### Step 2: Get Foot Bones
```maxscript
local csLeftFeet = biped.getNode csHe1 #lleg link:3   -- Left foot
local csRightFeet = biped.getNode csHe1 #rleg link:3  -- Right foot
```
**Note:** `link:3` gets the foot bone (closer to ground contact)

### Step 3: Analyze Each Frame
For each frame in animation:
1. **Get foot height** (Y or Z position depending on up-axis)
2. **Get toe height**
3. **Calculate velocity** (position delta between frames)
4. **Calculate angular velocity** (rotation delta)
5. **Compare against thresholds:**
   - If height < minThreshold AND velocity < speedThreshold → **0** (on ground)
   - If height > maxThreshold AND velocity > speedThreshold → **2** (in air)
   - Otherwise → **1** (transitioning)

### Step 4: Validate Sequence
```maxscript
-- Correct pattern: 0, 2, 1, 0, 2, 1
-- Error if pattern doesn't match:
messagebox (maxFileName + "：右脚同步组顺序错误！")  -- Right foot sync order error
messagebox (maxFileName + "：左脚同步组顺序错误！")  -- Left foot sync order error
```

### Step 5: Handle -1 Values
```maxscript
-- If value == -1:
if val == -1 then
    -- Assign previous frame's value
    feetArr[ii] = feetArr[ii-1]
```

### Step 6: First Frame Special Handling
```maxscript
-- SetFirstFrameFeetValue CharacterName
-- Determines initial foot state at frame 0
-- Gets ground contact value for character model
```

---

## Error Messages Found

### Left Foot
```
"左脚同步组顺序错误！"
Left foot sync group order error!
```

### Right Foot
```
"右脚同步组顺序错误！"
Right foot sync group order error!
```

### Initial Frame
```
"脚步初始帧位置预设出错！"
Foot initial frame position preset error!
```

### IK Root Node
```
"ik_foot_root节点丢失！"
ik_foot_root node missing!
```

---

## Custom Attributes System

### Attribute Storage
```maxscript
-- Delete all custom attributes from imported bones
-- Sync group attributes need to be reloaded
-- Because attributes won't be replaced, only newly added
```

**Implementation:**
- Stores sync group data as custom MaxScript attributes on bones
- Attributes must be deleted before reimport
- Cannot replace attributes, only add new ones

---

## Export Integration

### FBX Export Function
```maxscript
fn whenexportFBXJustStartIsPressed = ---批量导出
    -- Batch export
    -- Validates sync group order before export
```

### Root Bone Locking
```
"加入根骨骼锁定"
Add root bone locking

"如果导出了根骨骼锁定，那么需要回滚文件"
If root bone locking exported, need to rollback file
```

---

## Implementation Strategy for MotionKit

### Phase 1: Core Detection
1. Implement foot bone detection (get left/right foot bones)
2. Calculate height and velocity per frame
3. Apply threshold comparison
4. Generate sync value array (0, 1, 2, -1)

### Phase 2: Character Profiles
1. Create character profiles with height parameters
2. Support custom threshold configuration
3. Auto-detect character from scene

### Phase 3: Validation
1. Validate sequence order (0→2→1 pattern)
2. Handle -1 (undetermined) values
3. First frame special handling

### Phase 4: Visualization
1. Display sync values on timeline
2. Color-code frames (green=0, yellow=1, red=2)
3. Show errors/warnings

### Phase 5: Export Integration
1. Store sync data as custom attributes
2. Use sync data to optimize FBX export
3. Validate before export

---

## Key Insights

### Why Two Foot Measurements?
The system tracks both **toe** and **foot** (ankle) because:
- **Toe height** determines if it's heel-down (toe up) vs toe-down (heel up)
- **Foot height** determines overall ground contact
- Combined analysis gives accurate contact state

### Why Angular Velocity?
```
"需要把x平面数值删除才能计算出他在真正的脚步上抬"
Need to remove X plane values to calculate true foot lift
```
- Linear velocity alone isn't enough
- Foot can rotate without translating (toe curl, heel pivot)
- Angular velocity detects rotational foot movement

### Why Frame 0 is Special?
- Initial pose may not have foot on ground
- Need to scan entire animation to find first contact
- If no contact found, animation might not need sync groups

### Pattern Recognition
The system expects: **0, 2, 1, 0, 2, 1**
- Not: 0, 1, 2 (this would be wrong)
- The "2" (in air) comes before "1" (landing transition)
- This matches natural biomechanics of walking

---

## TODO: Remaining Questions

1. What is `minSpeed` parameter in `ComputFeetUpAndDown`?
2. How is `angleSpeed` threshold calculated?
3. What is `toleranceMax` used for?
4. What does `tinyRange` represent?
5. How are `defaulPlane`, `toeUp`, `toeDown` vectors used?

These likely involve trigonometry and vector math for precise foot orientation detection.

---

## References

- Source: `ExportScriptFBX.cp39-win_amd64.pyd`
- Extracted via binary string analysis
- Functions written in MaxScript (embedded in compiled Python module)
