# sp-cloth Phase 1 Implementation Plan (Executable)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an offline 3dsmax pipeline that automates per-animation cloth attachment processing — driver-driven auto-root keyframing + batch cloth sim — for one body type and 5 characters, end-to-end.

**Architecture:** All-in-3dsmax. Per-frame curve evaluator wraps Reaction Manager to drive attachment root bones from designated body bones. Per-character JSON config inherits from one of 8 body type templates. Batch runner processes corrected animations through 3dsmax cloth sim with per-character capsule collisions. UE runtime KP layer unchanged.

**Tech Stack:** Python 3 (via pymxs in 3dsmax 2024+), pytest for pure-Python tests, PySide2 for the Driver Setup panel, plain JSON for configs, Reaction Manager for runtime curve evaluation.

**Phase 1 exit criteria:** 1 body type authored, 5 characters set up via the UI panel, ~50 animations batched end-to-end with zero per-animation human touch, visual quality matching the current manual pipeline.

---

## Legend

- **[AGENT]** — Can be executed in a Claude Code session. Pure code, JSON, tests, docs. No 3dsmax interaction required.
- **[HUMAN]** — Must be done by the TD inside 3dsmax or in a terminal with judgment calls. pymxs API discovery, scene fixtures, visual verification, UI testing, licensing checks, content decisions.
- **[HANDOFF]** — Boundary moment where one role hands work to the other. Read carefully.

## Owner Map (At a Glance)

| Stage | Tasks | Primary Owner | Notes |
|---|---|---|---|
| 0 — De-risking spikes | 0.1, 0.2 | HUMAN | Validate Reaction Manager + headless batch before committing to architecture |
| 1 — Config foundation | 1.1–1.4 | AGENT | Pure Python, fully TDD-able |
| 2 — Real-data authoring | 2.1, 2.2 | AGENT writes, HUMAN reviews | JSON content; human eyeballs values |
| 3 — Auto-Root curve evaluator | 3.1–3.3 | AGENT | Pure math, fully TDD-able |
| 4 — Auto-Root 3dsmax integration | 4.1–4.4 | HUMAN | pymxs glue + scene tests |
| 5 — Capsule auto-generator | 5.1 AGENT, 5.2 HUMAN | Mixed | PCA math vs skin-query |
| 6 — Driver Setup panel | 6.1–6.4 | HUMAN | PySide2 in 3dsmax, manual UI verification |
| 7 — Batch Cloth Sim Runner | 7.1 HUMAN, 7.2 HUMAN, 7.3 AGENT | Mixed | Cloth modifier work vs driver glue |
| 8 — Pilot run | 8.1–8.4 | HUMAN | Real characters, visual review, iteration |

## How to Use This Plan

1. **[HUMAN]** Read the whole plan top-to-bottom once. Note the [HANDOFF] markers.
2. Execute stages in order. Stage 0 is non-negotiable — if those spikes fail, the design changes before you continue.
3. For an **[AGENT]** task: open a Claude Code session in `sp-cloth/`, say *"Execute Task X.Y from `plan/2026-05-17-phase1-implementation.md`"*. The agent will run the steps and commit.
4. For a **[HUMAN]** task: work in 3dsmax / your terminal, check off boxes as you go, commit at the end of each task.
5. **Mark checkboxes** to track progress. Resume where you left off.
6. **Commit after every task.** Plan is structured so each commit lands at a working state.

---

## Stage 0 — De-risking Spikes

**Owner:** HUMAN
**Goal:** Confirm the two load-bearing technical assumptions in the spec before writing any code.
**Exit criteria:** Both spikes documented as PASS (or revised design committed if either FAILED).

If either spike FAILS, **do not proceed past Stage 0** until you've updated `plan/2026-05-17-design.md` with the revised approach.

### Task 0.1: Validate Reaction Manager covers the curve needs

**Primary owner:** [HUMAN]
**Estimated time:** 1–2 hours
**Files:**
- Create: `sp-cloth/spikes/0.1_reaction_manager/spike.py`
- Create: `sp-cloth/spikes/0.1_reaction_manager/spike_scene.max`
- Create: `sp-cloth/spikes/0.1_reaction_manager/findings.md`

#### Steps

- [ ] **[HUMAN] Step 0.1.1: Create the spike folder**

In a terminal:
```bash
mkdir -p /Users/mandl/Desktop/projects/sp-cloth/spikes/0.1_reaction_manager
```

- [ ] **[HUMAN] Step 0.1.2: Build a minimal test scene in 3dsmax**

In 3dsmax:
1. File → New, "Don't save."
2. Create → Systems → Biped. Drag in viewport to create a default biped.
3. Create a point/dummy object. Name it `Bip_Skirt_Root`. Parent it under the biped's `Pelvis` bone.
4. Animate `LeftUpLeg.rotation.x` with keyframes: frame 0 = 0°, frame 10 = -45°, frame 20 = -90°.
5. File → Save As → `sp-cloth/spikes/0.1_reaction_manager/spike_scene.max`.

- [ ] **[HUMAN] Step 0.1.3: Author Reaction Manager curves manually**

1. Animation → Reaction Manager.
2. Add a Master: pick `LeftUpLeg`, axis `rotation_x`.
3. Add a Slave: pick `Bip_Skirt_Root`, axis `rotation` (full rotation).
4. Author 3 reactions at driver values -90°, 0°, +90° with skirt root deltas:
   - -90° → rotate root +25° on X
   - 0° → 0
   - +90° → rotate root -10° on X
5. Add a second Master: `RightUpLeg.rotation_x`, with mirrored curve on the same slave.
6. Save scene.

- [ ] **[HUMAN] Step 0.1.4: Write the readback spike**

Create `sp-cloth/spikes/0.1_reaction_manager/spike.py`:

```python
"""Verify we can read & evaluate Reaction Manager curves programmatically via pymxs.
Run from inside 3dsmax after opening spike_scene.max."""
from pymxs import runtime as rt

print("=== Reaction Manager API discovery ===")

# 1. Enumerate masters
try:
    master_count = rt.reactionManager.numStates
    print(f"  numStates exists: {master_count}")
except Exception as e:
    print(f"  numStates failed: {e}")

# 2. Try common API names
for attr in ["NumMasters", "GetMasterCount", "Masters", "masters"]:
    try:
        v = getattr(rt.reactionManager, attr)
        print(f"  rt.reactionManager.{attr}: {v}")
    except Exception as e:
        print(f"  rt.reactionManager.{attr}: NOT AVAILABLE ({e})")

# 3. Confirm we can evaluate at an arbitrary driver value
#    (probably via setting the driver bone's rotation directly and reading the slave)
left_thigh = rt.getNodeByName("LeftUpLeg")
skirt_root = rt.getNodeByName("Bip_Skirt_Root")
print("\n=== Drive-and-read test ===")
for test_val in (-90, -45, 0, 45, 90):
    # Set driver
    # NOTE: exact API for setting one Euler axis is version-specific; this is the spike's job to confirm.
    # Typical pattern: build a quaternion from desired Euler and assign.
    rt.sliderTime = 0
    # ... set left_thigh rotation_x to test_val ...
    rt.redrawViews()
    print(f"  driver={test_val}°  slave_rotation={skirt_root.rotation}")

# 4. Determine if multi-driver behavior is sum or blend.
#    Set both LeftUpLeg and RightUpLeg to -90; predicted-if-sum: skirt root rotates by ~+50° (25+25);
#    predicted-if-blend: ~+25° (average). Note actual behavior in findings.md.
print("\n=== Multi-driver behavior ===")
# ... set both driver bones to -90° ...
print(f"  both_drivers=-90°  slave_rotation={skirt_root.rotation}")
```

- [ ] **[HUMAN] Step 0.1.5: Run the spike inside 3dsmax**

1. Open `spike_scene.max` in 3dsmax.
2. Scripting → Run Script → select `spike.py`.
3. Watch the Listener output.

- [ ] **[HUMAN] Step 0.1.6: Document findings**

Create `sp-cloth/spikes/0.1_reaction_manager/findings.md`:

```markdown
# Reaction Manager Spike Findings

**Date:** YYYY-MM-DD
**3dsmax version:** ...

## API questions
1. **Can we enumerate masters/slaves programmatically?** YES/NO + the exact pymxs API.
2. **Can we evaluate curves at arbitrary driver values without writing keyframes?** YES/NO + how.
3. **Multi-driver behavior — sum or blend?** SUM / BLEND / CONFIGURABLE. Implication for our design: ...
4. **Curve interpolation type** — linear / spline / configurable per key? ...

## Verdict
- [ ] PASS — design as-spec'd works
- [ ] PARTIAL — works with these caveats: ...
- [ ] FAIL — Reaction Manager doesn't fit; plan changes: ...

## Implications for the implementation plan
(If anything found above changes the design, write here what needs to change in the design spec.)
```

- [ ] **[HUMAN] Step 0.1.7: Decide go/no-go**

- If PASS: continue to Task 0.2.
- If PARTIAL: update the design spec to reflect the caveats, then continue.
- If FAIL: revise the design. Likely change: build a custom Python curve evaluator (we already have one designed in Stage 3) and skip Reaction Manager entirely. Update the design spec, then continue.

- [ ] **[HUMAN] Step 0.1.8: Commit**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth
git add spikes/0.1_reaction_manager/
git commit -m "spike: Reaction Manager API + multi-driver behavior verified"
```

### Task 0.2: Validate headless 3dsmax batch + cloth sim

**Primary owner:** [HUMAN]
**Estimated time:** 2–3 hours
**Files:**
- Create: `sp-cloth/spikes/0.2_headless_batch/sample.max`
- Create: `sp-cloth/spikes/0.2_headless_batch/headless_run.py`
- Create: `sp-cloth/spikes/0.2_headless_batch/spike.bat` (Win) or `spike.sh` (other)
- Create: `sp-cloth/spikes/0.2_headless_batch/findings.md`

#### Steps

- [ ] **[HUMAN] Step 0.2.1: Pick or create a minimal cloth scene**

Find the smallest existing scene in your project with a character + a cloth-modified skirt + 30 frames of body anim. Save a copy as `sample.max` in the spike folder. (If you don't have one yet, set up a minimum reproducible case: character + simple skirt mesh with Cloth modifier + 30 frames of leg lift.)

- [ ] **[HUMAN] Step 0.2.2: Write the headless processing script**

Create `sp-cloth/spikes/0.2_headless_batch/headless_run.py`:

```python
"""Headless cloth sim spike. Runs inside 3dsmax in batch mode.
Reads input .max, runs cloth sim, exports FBX, quits."""
import sys
from pymxs import runtime as rt

if len(sys.argv) < 3:
    print("Usage: headless_run.py <input.max> <output.fbx>")
    sys.exit(1)

input_path = sys.argv[1]
output_path = sys.argv[2]

print(f"Loading {input_path}...")
rt.loadMaxFile(input_path, useFileUnits=True, quiet=True)

# Find the cloth modifier on the skirt
# NOTE: exact API to trigger cloth sim is version-specific. This spike's job is to confirm it.
# Typical: find the Cloth modifier, call its simulate method or similar.
for node in rt.objects:
    for mod in node.modifiers:
        if rt.classOf(mod) == rt.Cloth:
            print(f"Found Cloth modifier on {node.name}")
            # Try common API names
            for method in ["simulate", "simulateLocal", "simulateForward"]:
                if hasattr(mod, method):
                    print(f"  has method: {method}")

# Trigger sim — adjust call based on what you found above
# rt.execute("$.modifiers[#Cloth].simulate()")

print(f"Exporting {output_path}...")
rt.exportFile(output_path, rt.Name("noPrompt"))

print("Done. Quitting.")
rt.quitMax(quiet=True)
```

- [ ] **[HUMAN] Step 0.2.3: Write the batch invocation script**

On Windows, create `spike.bat`:
```bat
@echo off
set MAX="C:\Program Files\Autodesk\3ds Max 2024\3dsmax.exe"
%MAX% -silent -U PythonHost "%~dp0headless_run.py" "%~dp0sample.max" "%~dp0sample_baked.fbx"
echo Exit code: %ERRORLEVEL%
```

On macOS/Linux, create `spike.sh`:
```bash
#!/bin/bash
# Adjust path to your 3dsmax binary
MAX="/Applications/Autodesk/3dsmax-2024/3dsmax"
"$MAX" -silent -U PythonHost "$(dirname "$0")/headless_run.py" "$(dirname "$0")/sample.max" "$(dirname "$0")/sample_baked.fbx"
echo "Exit code: $?"
```

- [ ] **[HUMAN] Step 0.2.4: Run the batch**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth/spikes/0.2_headless_batch/
./spike.sh   # or spike.bat on Windows
```

Watch the output. Time it.

- [ ] **[HUMAN] Step 0.2.5: Verify the output FBX**

Open `sample_baked.fbx` in 3dsmax interactively. Scrub the timeline. Confirm:
- The skirt bones have baked animation curves (not empty).
- The cloth deformation is visually plausible (not flat-rest-pose).

- [ ] **[HUMAN] Step 0.2.6: Test parallel licensing**

In two separate terminals, run `./spike.sh` simultaneously. Observe:
- Did the second instance wait? Fail? Succeed?
- Total wall-clock to complete both vs running them serially.

If your license server allows N concurrent runs, note N. This is the realistic batch parallelism ceiling.

- [ ] **[HUMAN] Step 0.2.7: Document findings**

Create `sp-cloth/spikes/0.2_headless_batch/findings.md`:

```markdown
# Headless Batch Spike Findings

**Date:** YYYY-MM-DD
**3dsmax version:** ...
**License config:** ...

## Cloth simulation in headless mode
1. **Does headless 3dsmax run cloth sim?** YES/NO.
2. **Exact pymxs API used to trigger sim:** ...
3. **Wall-clock time for a 30-frame sample:** ... seconds.

## Licensing
1. **Concurrent instances allowed:** N
2. **Behavior when over the limit:** wait/fail/queue?
3. **Realistic batch parallelism for Phase 2:** N machines

## Verdict
- [ ] PASS
- [ ] PARTIAL (caveats: ...)
- [ ] FAIL (must run interactive on dedicated workstations instead)

## Implications
...
```

- [ ] **[HUMAN] Step 0.2.8: Commit**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth
git add spikes/0.2_headless_batch/
git commit -m "spike: headless 3dsmax cloth sim + licensing verified"
```

### **[HANDOFF] Stage 0 → Stage 1**

- [ ] **[HUMAN]** Both `findings.md` reviewed. Either:
  - Both PASS → proceed to Stage 1 with the plan as-written.
  - Anything PARTIAL/FAIL → update `plan/2026-05-17-design.md` to reflect required changes, **then** proceed.

---

## Stage 1 — Config Foundation

**Owner:** AGENT (entire stage)
**Goal:** Pure-Python infrastructure for loading, resolving (body-type + character inheritance), and validating configs. No 3dsmax dependency.
**Exit criteria:** `pytest sp-cloth/tests/` runs clean, all Stage 1 tests pass.

### Task 1.1: Initialize project structure

**Primary owner:** [AGENT]
**Estimated time:** 5 min
**Files:**
- Create: `sp-cloth/README.md`
- Create: `sp-cloth/.gitignore`
- Create: `sp-cloth/pyproject.toml`
- Create: `sp-cloth/src/sp_cloth/__init__.py`
- Create: `sp-cloth/tests/__init__.py`
- Create: `sp-cloth/configs/.gitkeep`

#### Steps

- [ ] **[AGENT] Step 1.1.1: Write `sp-cloth/README.md`**

```markdown
# sp-cloth

Offline 3dsmax pipeline automating cloth attachment processing for our game's characters.

## Structure

- `src/sp_cloth/` — Python package, imported from 3dsmax via pymxs
- `configs/` — material library, body type templates, character presets
- `tests/` — pytest tests for pure-Python modules (no 3dsmax dependency)
- `tools/` — entry points for use from inside 3dsmax
- `spikes/` — throwaway validation spikes
- `plan/` — design spec + implementation plan

## Setup

```
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Run tests

```
pytest tests/
```
```

- [ ] **[AGENT] Step 1.1.2: Write `sp-cloth/.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
*.egg-info/
build/
dist/
*.bak
*.tmp
```

- [ ] **[AGENT] Step 1.1.3: Write `sp-cloth/pyproject.toml`**

```toml
[project]
name = "sp_cloth"
version = "0.1.0"
requires-python = ">=3.9"

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov"]

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **[AGENT] Step 1.1.4: Create empty package files**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth
touch src/sp_cloth/__init__.py tests/__init__.py configs/.gitkeep
mkdir -p src/sp_cloth tests configs
```

- [ ] **[HUMAN] Step 1.1.5: Verify scaffolding by creating venv and running pytest**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Expected: pytest output reads `no tests ran in 0.0s`.

- [ ] **[AGENT] Step 1.1.6: Commit**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth
git init  # if not already initialized
git add .
git commit -m "feat: initialize sp-cloth package structure"
```

### Task 1.2: Config types + merge resolver

**Primary owner:** [AGENT]
**Estimated time:** 30 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/config/__init__.py`
- Create: `sp-cloth/src/sp_cloth/config/types.py`
- Create: `sp-cloth/src/sp_cloth/config/resolver.py`
- Create: `sp-cloth/tests/test_config_resolver.py`

#### Steps

- [ ] **[AGENT] Step 1.2.1: Create config subpackage**

```bash
mkdir -p src/sp_cloth/config
touch src/sp_cloth/config/__init__.py
```

- [ ] **[AGENT] Step 1.2.2: Write `src/sp_cloth/config/types.py`**

```python
"""TypedDict definitions for config artifacts. Documentation-as-types."""
from typing import TypedDict, Optional, List, Literal

class Vec3Dict(TypedDict):
    rotX: float
    rotY: float
    rotZ: float

class CurveKey(TypedDict):
    driverValue: float
    rootDelta: Vec3Dict

class Driver(TypedDict):
    driverBone: str
    driverAxis: str  # "rotation_x", "rotation_y", or "rotation_z"
    responseCurve: List[CurveKey]

class AttachmentDefault(TypedDict):
    drivers: List[Driver]
    constraints: dict
    extrapolation: Literal["clamp"]
    temporalSmoothingFrames: int

class CollisionSet(TypedDict):
    bones: List[str]
    scaleFactor: float

class BodyType(TypedDict):
    id: str
    skeletonTemplate: str
    collisionSets: dict
    attachmentDriverDefaults: dict
    qaThresholds: dict

class Attachment(TypedDict, total=False):
    name: str
    rootBone: str
    type: str
    clothSim: Optional[dict]
    driverOverrides: Optional[List[Driver]]

class Character(TypedDict, total=False):
    id: str
    extends: str
    collisionSetOverrides: dict
    attachments: List[Attachment]
```

- [ ] **[AGENT] Step 1.2.3: Write failing test `tests/test_config_resolver.py`**

```python
import pytest
from sp_cloth.config.resolver import resolve_character

def make_fixtures():
    materials = {"soft_cotton": {"stiffness": 0.3, "bend": 0.2, "damping": 0.5, "airResistance": 0.1, "mass": 1.0}}
    body_types = {
        "AdultMale": {
            "id": "AdultMale",
            "collisionSets": {"legs": {"bones": ["LeftUpLeg", "RightUpLeg"], "scaleFactor": 0.9}},
            "attachmentDriverDefaults": {
                "skirt": {
                    "drivers": [{"driverBone": "LeftUpLeg", "driverAxis": "rotation_x",
                                 "responseCurve": [{"driverValue": 0, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}}]}],
                    "constraints": {"maxRotationDegrees": 35},
                    "extrapolation": "clamp",
                    "temporalSmoothingFrames": 3,
                }
            },
            "qaThresholds": {"maxVertexVelocity": 50, "maxSelfIntersectionsPerFrame": 5, "maxRootRotationJumpDegrees": 10},
        }
    }
    return materials, body_types

def test_resolve_basic_character_inherits_body_type():
    materials, body_types = make_fixtures()
    character = {
        "id": "AdultMale_Rex",
        "extends": "AdultMale",
        "attachments": [{"name": "skirt", "rootBone": "Bip_Skirt_Root", "type": "skirt",
                         "clothSim": {"material": "soft_cotton"}}],
    }
    resolved = resolve_character(character, body_types, materials)
    assert resolved["id"] == "AdultMale_Rex"
    assert resolved["collisionSets"]["legs"]["scaleFactor"] == 0.9
    assert resolved["attachments"][0]["drivers"][0]["driverBone"] == "LeftUpLeg"
    assert resolved["attachments"][0]["clothSim"]["physics"]["stiffness"] == 0.3
```

- [ ] **[AGENT] Step 1.2.4: Run test — verify it fails**

```bash
pytest tests/test_config_resolver.py -v
```
Expected: ImportError / ModuleNotFoundError on `sp_cloth.config.resolver`.

- [ ] **[AGENT] Step 1.2.5: Write `src/sp_cloth/config/resolver.py`**

```python
"""Merge materials + body type + character preset into a single resolved config."""
from copy import deepcopy
from typing import Any

def resolve_character(character: dict, body_types: dict, materials: dict) -> dict:
    body_type_id = character["extends"]
    if body_type_id not in body_types:
        raise ValueError(f"Unknown body type: {body_type_id}")
    body = body_types[body_type_id]

    resolved: dict[str, Any] = {
        "id": character["id"],
        "extendsBodyType": body_type_id,
        "collisionSets": deepcopy(body["collisionSets"]),
        "qaThresholds": deepcopy(body["qaThresholds"]),
        "attachments": [],
    }

    for set_name, override in character.get("collisionSetOverrides", {}).items():
        if set_name not in resolved["collisionSets"]:
            raise ValueError(f"Override targets unknown collision set: {set_name}")
        resolved["collisionSets"][set_name].update(override)

    for att in character.get("attachments", []):
        att_type = att["type"]
        if att_type not in body["attachmentDriverDefaults"]:
            raise ValueError(f"Attachment type '{att_type}' not defined in body type '{body_type_id}'")
        default = deepcopy(body["attachmentDriverDefaults"][att_type])
        if att.get("driverOverrides"):
            default["drivers"] = att["driverOverrides"]
        cloth = att.get("clothSim")
        if cloth and cloth.get("material"):
            mat_name = cloth["material"]
            if mat_name not in materials:
                raise ValueError(f"Unknown material: {mat_name}")
            cloth = {**cloth, "physics": materials[mat_name]}
        resolved["attachments"].append({
            "name": att["name"],
            "rootBone": att["rootBone"],
            "type": att_type,
            "drivers": default["drivers"],
            "constraints": default["constraints"],
            "extrapolation": default["extrapolation"],
            "temporalSmoothingFrames": default["temporalSmoothingFrames"],
            "clothSim": cloth,
        })
    return resolved
```

- [ ] **[AGENT] Step 1.2.6: Run test — verify pass**

```bash
pytest tests/test_config_resolver.py -v
```
Expected: 1 passed.

- [ ] **[AGENT] Step 1.2.7: Add edge-case tests**

Append to `tests/test_config_resolver.py`:

```python
def test_resolve_rejects_unknown_body_type():
    materials, body_types = make_fixtures()
    character = {"id": "X", "extends": "NotARealType", "attachments": []}
    with pytest.raises(ValueError, match="Unknown body type"):
        resolve_character(character, body_types, materials)

def test_resolve_rejects_unknown_material():
    materials, body_types = make_fixtures()
    character = {"id": "X", "extends": "AdultMale", "attachments": [
        {"name": "skirt", "rootBone": "B", "type": "skirt", "clothSim": {"material": "fictional"}}]}
    with pytest.raises(ValueError, match="Unknown material"):
        resolve_character(character, body_types, materials)

def test_resolve_collision_set_override_merges_fields():
    materials, body_types = make_fixtures()
    character = {"id": "X", "extends": "AdultMale",
                 "collisionSetOverrides": {"legs": {"scaleFactor": 1.1}},
                 "attachments": []}
    resolved = resolve_character(character, body_types, materials)
    assert resolved["collisionSets"]["legs"]["scaleFactor"] == 1.1
    assert resolved["collisionSets"]["legs"]["bones"] == ["LeftUpLeg", "RightUpLeg"]
```

Run: `pytest tests/test_config_resolver.py -v`. Expected: 4 passed.

- [ ] **[AGENT] Step 1.2.8: Commit**

```bash
git add src/sp_cloth/config/ tests/test_config_resolver.py
git commit -m "feat(config): resolver merges body type + character preset + materials"
```

### Task 1.3: Config validation

**Primary owner:** [AGENT]
**Estimated time:** 20 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/config/validate.py`
- Create: `sp-cloth/tests/test_config_validate.py`

#### Steps

- [ ] **[AGENT] Step 1.3.1: Write failing tests**

Create `tests/test_config_validate.py`:

```python
import pytest
from sp_cloth.config.validate import validate_resolved_character, ValidationError

def good_resolved():
    return {
        "id": "X", "extendsBodyType": "AdultMale",
        "collisionSets": {"legs": {"bones": ["LeftUpLeg"], "scaleFactor": 0.9}},
        "qaThresholds": {"maxVertexVelocity": 50, "maxSelfIntersectionsPerFrame": 5, "maxRootRotationJumpDegrees": 10},
        "attachments": [{
            "name": "skirt", "rootBone": "Bip_Skirt_Root", "type": "skirt",
            "drivers": [{"driverBone": "LeftUpLeg", "driverAxis": "rotation_x",
                         "responseCurve": [
                             {"driverValue": -90, "rootDelta": {"rotX": 25, "rotY": 0, "rotZ": 0}},
                             {"driverValue": 0,   "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}},
                             {"driverValue": 90,  "rootDelta": {"rotX": -10, "rotY": 0, "rotZ": 0}}]}],
            "constraints": {"maxRotationDegrees": 35},
            "extrapolation": "clamp", "temporalSmoothingFrames": 3,
            "clothSim": None,
        }],
    }

def test_valid_passes():
    validate_resolved_character(good_resolved())

def test_curve_must_be_monotonic():
    r = good_resolved()
    r["attachments"][0]["drivers"][0]["responseCurve"][1]["driverValue"] = -95
    with pytest.raises(ValidationError, match="monotonic"):
        validate_resolved_character(r)

def test_max_rotation_must_be_positive():
    r = good_resolved()
    r["attachments"][0]["constraints"]["maxRotationDegrees"] = -1
    with pytest.raises(ValidationError, match="maxRotationDegrees"):
        validate_resolved_character(r)

def test_curve_must_have_at_least_two_points():
    r = good_resolved()
    r["attachments"][0]["drivers"][0]["responseCurve"] = [{"driverValue": 0, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}}]
    with pytest.raises(ValidationError, match="at least two"):
        validate_resolved_character(r)

def test_empty_id_rejected():
    r = good_resolved(); r["id"] = ""
    with pytest.raises(ValidationError, match="id"):
        validate_resolved_character(r)
```

- [ ] **[AGENT] Step 1.3.2: Run — verify all fail**

```bash
pytest tests/test_config_validate.py -v
```
Expected: ModuleNotFoundError.

- [ ] **[AGENT] Step 1.3.3: Implement**

Create `src/sp_cloth/config/validate.py`:

```python
"""Validation rules for resolved character configs."""

class ValidationError(Exception):
    pass

def validate_resolved_character(resolved: dict) -> None:
    if not isinstance(resolved.get("id"), str) or not resolved["id"]:
        raise ValidationError("Character id must be a non-empty string")

    for att in resolved.get("attachments", []):
        name = att.get("name", "<unnamed>")
        constraints = att.get("constraints", {})
        max_rot = constraints.get("maxRotationDegrees")
        if not isinstance(max_rot, (int, float)) or max_rot <= 0:
            raise ValidationError(f"Attachment '{name}': maxRotationDegrees must be positive")

        for driver in att.get("drivers", []):
            curve = driver.get("responseCurve", [])
            if len(curve) < 2:
                raise ValidationError(
                    f"Attachment '{name}' driver '{driver.get('driverBone')}': "
                    f"responseCurve must have at least two key points")
            prev = None
            for pt in curve:
                v = pt.get("driverValue")
                if prev is not None and v <= prev:
                    raise ValidationError(
                        f"Attachment '{name}' driver '{driver.get('driverBone')}': "
                        f"responseCurve must be monotonic in driverValue")
                prev = v
```

- [ ] **[AGENT] Step 1.3.4: Run — verify all pass**

```bash
pytest tests/test_config_validate.py -v
```
Expected: 5 passed.

- [ ] **[AGENT] Step 1.3.5: Commit**

```bash
git add src/sp_cloth/config/validate.py tests/test_config_validate.py
git commit -m "feat(config): validation rules for resolved character configs"
```

### Task 1.4: JSON loader

**Primary owner:** [AGENT]
**Estimated time:** 20 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/config/loader.py`
- Create: `sp-cloth/tests/test_config_loader.py`
- Create: `sp-cloth/tests/fixtures/loader/cloth_materials.json`
- Create: `sp-cloth/tests/fixtures/loader/body_types/AdultMale.json`
- Create: `sp-cloth/tests/fixtures/loader/characters/TestChar.json`

#### Steps

- [ ] **[AGENT] Step 1.4.1: Create fixture directory + files**

```bash
mkdir -p tests/fixtures/loader/body_types tests/fixtures/loader/characters
```

Write `tests/fixtures/loader/cloth_materials.json`:
```json
{
  "materials": {
    "soft_cotton": { "stiffness": 0.3, "bend": 0.2, "damping": 0.5, "airResistance": 0.1, "mass": 1.0 }
  }
}
```

Write `tests/fixtures/loader/body_types/AdultMale.json`:
```json
{
  "id": "AdultMale",
  "skeletonTemplate": "biped_v3",
  "collisionSets": { "legs": { "bones": ["LeftUpLeg", "RightUpLeg"], "scaleFactor": 0.9 } },
  "attachmentDriverDefaults": {
    "skirt": {
      "drivers": [{
        "driverBone": "LeftUpLeg", "driverAxis": "rotation_x",
        "responseCurve": [
          {"driverValue": -90, "rootDelta": {"rotX": 25, "rotY": 0, "rotZ": 0}},
          {"driverValue":   0, "rootDelta": {"rotX": 0,  "rotY": 0, "rotZ": 0}},
          {"driverValue":  90, "rootDelta": {"rotX": -10, "rotY": 0, "rotZ": 0}}]
      }],
      "constraints": { "maxRotationDegrees": 35 },
      "extrapolation": "clamp", "temporalSmoothingFrames": 3
    }
  },
  "qaThresholds": { "maxVertexVelocity": 50, "maxSelfIntersectionsPerFrame": 5, "maxRootRotationJumpDegrees": 10 }
}
```

Write `tests/fixtures/loader/characters/TestChar.json`:
```json
{
  "id": "TestChar", "extends": "AdultMale",
  "attachments": [
    { "name": "skirt", "rootBone": "Bip_Skirt_Root", "type": "skirt",
      "clothSim": { "material": "soft_cotton" } }
  ]
}
```

- [ ] **[AGENT] Step 1.4.2: Write failing test**

Create `tests/test_config_loader.py`:

```python
from pathlib import Path
from sp_cloth.config.loader import load_character

def test_load_returns_resolved_validated():
    fixtures = Path(__file__).parent / "fixtures" / "loader"
    resolved = load_character(
        character_path=fixtures / "characters" / "TestChar.json",
        body_types_dir=fixtures / "body_types",
        materials_path=fixtures / "cloth_materials.json",
    )
    assert resolved["id"] == "TestChar"
    assert resolved["attachments"][0]["clothSim"]["physics"]["stiffness"] == 0.3
```

- [ ] **[AGENT] Step 1.4.3: Run — verify fails**

```bash
pytest tests/test_config_loader.py -v
```
Expected: ModuleNotFoundError on `sp_cloth.config.loader`.

- [ ] **[AGENT] Step 1.4.4: Implement loader**

Create `src/sp_cloth/config/loader.py`:

```python
"""Disk-to-resolved-config loader. Composes materials + body types + character preset."""
import json
from pathlib import Path
from .resolver import resolve_character
from .validate import validate_resolved_character

def load_character(character_path: Path, body_types_dir: Path, materials_path: Path) -> dict:
    with open(materials_path) as f:
        materials = json.load(f)["materials"]
    body_types = {}
    for p in Path(body_types_dir).glob("*.json"):
        with open(p) as f:
            data = json.load(f)
            body_types[data["id"]] = data
    with open(character_path) as f:
        character = json.load(f)
    resolved = resolve_character(character, body_types, materials)
    validate_resolved_character(resolved)
    return resolved
```

- [ ] **[AGENT] Step 1.4.5: Run — verify pass**

```bash
pytest tests/test_config_loader.py -v
```
Expected: 1 passed.

- [ ] **[AGENT] Step 1.4.6: Commit**

```bash
git add src/sp_cloth/config/loader.py tests/test_config_loader.py tests/fixtures/
git commit -m "feat(config): loader composes materials + body types + character preset"
```

### **[HANDOFF] Stage 1 → Stage 2**

- [ ] **[AGENT]** All Stage 1 tests pass: `pytest tests/` reports green.
- [ ] **[AGENT]** Hand off to authoring stage. Stage 2 produces real JSON content; Stage 3 keeps building pure-Python code in parallel.

---

## Stage 2 — Real-Data Authoring

**Owner:** [AGENT] writes scaffolds, [HUMAN] reviews values
**Goal:** Create the first material library and body type template with sensible starter values.
**Exit criteria:** Real configs load through the Stage 1 loader without validation errors.

### Task 2.1: Author the material library

**Primary owner:** [AGENT] (writes), [HUMAN] (reviews)
**Estimated time:** 15 min agent + 10 min human review
**Files:**
- Create: `sp-cloth/configs/cloth_materials.json`
- Create: `sp-cloth/tests/test_config_real_data.py`

#### Steps

- [ ] **[AGENT] Step 2.1.1: Author initial material library**

Create `configs/cloth_materials.json`:

```json
{
  "materials": {
    "soft_pleated_cotton": { "stiffness": 0.30, "bend": 0.20, "damping": 0.55, "airResistance": 0.10, "mass": 1.0 },
    "stiff_cotton":        { "stiffness": 0.55, "bend": 0.45, "damping": 0.50, "airResistance": 0.08, "mass": 1.2 },
    "heavy_leather":       { "stiffness": 0.85, "bend": 0.75, "damping": 0.40, "airResistance": 0.02, "mass": 2.4 },
    "flowing_silk":        { "stiffness": 0.12, "bend": 0.08, "damping": 0.30, "airResistance": 0.15, "mass": 0.6 },
    "wool_blend":          { "stiffness": 0.45, "bend": 0.35, "damping": 0.55, "airResistance": 0.06, "mass": 1.4 }
  }
}
```

- [ ] **[AGENT] Step 2.1.2: Write structural test**

Create `tests/test_config_real_data.py`:

```python
import json
from pathlib import Path

REPO_CONFIGS = Path(__file__).parent.parent / "configs"

def test_materials_file_loads():
    with open(REPO_CONFIGS / "cloth_materials.json") as f:
        data = json.load(f)
    assert "materials" in data
    for name, m in data["materials"].items():
        for key in ("stiffness", "bend", "damping", "airResistance", "mass"):
            assert key in m, f"Material {name} missing {key}"
            assert isinstance(m[key], (int, float))
```

Run: `pytest tests/test_config_real_data.py -v`. Expected: 1 passed.

- [ ] **[HUMAN] Step 2.1.3: Review starting values**

Open `configs/cloth_materials.json`. The values are first-pass estimates from generic cloth physics. Adjust if you have ground-truth values from your team's existing cloth setup. These will be tuned during Stage 8 pilot anyway — they just need to be in the ballpark to start.

If you change any values, re-run the test.

- [ ] **[AGENT] Step 2.1.4: Commit**

```bash
git add configs/cloth_materials.json tests/test_config_real_data.py
git commit -m "feat(configs): initial cloth material library (5 materials)"
```

### Task 2.2: Author first body type template

**Primary owner:** [AGENT] (writes scaffold), [HUMAN] (refines values)
**Estimated time:** 30 min agent + 30 min human review
**Files:**
- Create: `sp-cloth/configs/body_types/AdultMale.json`
- Modify: `sp-cloth/tests/test_config_real_data.py`

#### Steps

- [ ] **[AGENT] Step 2.2.1: Create body_types dir + scaffold AdultMale**

```bash
mkdir -p configs/body_types
```

Create `configs/body_types/AdultMale.json`:

```json
{
  "id": "AdultMale",
  "skeletonTemplate": "biped_v3",
  "collisionSets": {
    "legs":      { "bones": ["LeftUpLeg","RightUpLeg","LeftLeg","RightLeg"], "scaleFactor": 0.9 },
    "hips":      { "bones": ["Hip","Pelvis"], "scaleFactor": 0.95 },
    "torso":     { "bones": ["Spine_01","Spine_02","Spine_03"], "scaleFactor": 0.92 },
    "shoulders": { "bones": ["LeftShoulder","RightShoulder","LeftArm","RightArm"], "scaleFactor": 0.9 }
  },
  "attachmentDriverDefaults": {
    "skirt": {
      "drivers": [
        { "driverBone": "LeftUpLeg",  "driverAxis": "rotation_x",
          "responseCurve": [
            {"driverValue": -90, "rootDelta": {"rotX": 25, "rotY":  5, "rotZ": 0}},
            {"driverValue":   0, "rootDelta": {"rotX":  0, "rotY":  0, "rotZ": 0}},
            {"driverValue":  90, "rootDelta": {"rotX": -10, "rotY": -5, "rotZ": 0}}
          ]},
        { "driverBone": "RightUpLeg", "driverAxis": "rotation_x",
          "responseCurve": [
            {"driverValue": -90, "rootDelta": {"rotX": 25, "rotY": -5, "rotZ": 0}},
            {"driverValue":   0, "rootDelta": {"rotX":  0, "rotY":  0, "rotZ": 0}},
            {"driverValue":  90, "rootDelta": {"rotX": -10, "rotY":  5, "rotZ": 0}}
          ]}
      ],
      "constraints": { "maxRotationDegrees": 35 },
      "extrapolation": "clamp",
      "temporalSmoothingFrames": 3
    },
    "tail":     { "drivers": [], "constraints": { "maxRotationDegrees": 50 }, "extrapolation": "clamp", "temporalSmoothingFrames": 3 },
    "hairLong": { "drivers": [], "constraints": { "maxRotationDegrees": 60 }, "extrapolation": "clamp", "temporalSmoothingFrames": 3 },
    "sleeve":   { "drivers": [], "constraints": { "maxRotationDegrees": 45 }, "extrapolation": "clamp", "temporalSmoothingFrames": 3 }
  },
  "qaThresholds": { "maxVertexVelocity": 50, "maxSelfIntersectionsPerFrame": 5, "maxRootRotationJumpDegrees": 10 }
}
```

Note: tail / hairLong / sleeve `drivers` are intentionally empty for now. They'll be filled in by [HUMAN] in Step 2.2.4 once Stage 3 (curve evaluator) is working and the Driver Setup panel can preview.

- [ ] **[AGENT] Step 2.2.2: Add resolver test for real body type**

Append to `tests/test_config_real_data.py`:

```python
from sp_cloth.config.loader import load_character

def test_real_body_type_resolves_with_minimal_character(tmp_path):
    char_dir = tmp_path / "characters"
    char_dir.mkdir()
    char_path = char_dir / "Synthetic.json"
    char_path.write_text("""{
      "id": "Synthetic", "extends": "AdultMale",
      "attachments": [{"name":"skirt","rootBone":"Bip_Skirt_Root","type":"skirt",
                       "clothSim":{"material":"soft_pleated_cotton"}}]
    }""")
    resolved = load_character(
        character_path=char_path,
        body_types_dir=REPO_CONFIGS / "body_types",
        materials_path=REPO_CONFIGS / "cloth_materials.json",
    )
    assert resolved["attachments"][0]["drivers"][0]["driverBone"] == "LeftUpLeg"
```

Run: `pytest tests/test_config_real_data.py -v`. Expected: 2 passed.

- [ ] **[HUMAN] Step 2.2.3: Review bone names against your project's biped naming**

Critical — open the body type JSON and verify every bone name (`LeftUpLeg`, `RightUpLeg`, `Hip`, `Pelvis`, `Spine_01`, `LeftShoulder`, etc.) matches the exact bone names in your project's biped rig.

If they differ (e.g., `Bip01_L_Thigh` instead of `LeftUpLeg`), do a global find/replace in the JSON. Re-run the test to confirm it still loads.

- [ ] **[HUMAN] Step 2.2.4: Defer authoring tail/hairLong/sleeve drivers**

Don't fill in the empty driver arrays yet. They're easier to author once Stage 3 (curve eval) is working and you can preview. Task 4.4 picks this up.

- [ ] **[AGENT] Step 2.2.5: Commit**

```bash
git add configs/body_types/AdultMale.json tests/test_config_real_data.py
git commit -m "feat(configs): AdultMale body type scaffold with skirt drivers authored"
```

### **[HANDOFF] Stage 2 → Stage 3**

- [ ] **[HUMAN]** Bone names verified against project rig.
- [ ] **[AGENT]** Continue to Stage 3 — pure Python curve evaluator. No 3dsmax needed yet.

---

## Stage 3 — Auto-Root Curve Evaluator

**Owner:** [AGENT] (entire stage)
**Goal:** Pure-math curve evaluator that maps driver bone rotations → root deltas. No 3dsmax dependency.
**Exit criteria:** Curve eval handles single/multi-driver, clamps extrapolation, smooths temporally.

### Task 3.1: Single-driver curve evaluation with clamp

**Primary owner:** [AGENT]
**Estimated time:** 20 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/autoroot/__init__.py`
- Create: `sp-cloth/src/sp_cloth/autoroot/evaluate.py`
- Create: `sp-cloth/tests/test_autoroot_evaluate.py`

#### Steps

- [ ] **[AGENT] Step 3.1.1: Create autoroot subpackage**

```bash
mkdir -p src/sp_cloth/autoroot
touch src/sp_cloth/autoroot/__init__.py
```

- [ ] **[AGENT] Step 3.1.2: Write failing tests**

Create `tests/test_autoroot_evaluate.py`:

```python
from sp_cloth.autoroot.evaluate import evaluate_curve

CURVE = [
    {"driverValue": -90, "rootDelta": {"rotX": 25, "rotY": 5, "rotZ": 0}},
    {"driverValue":   0, "rootDelta": {"rotX": 0,  "rotY": 0, "rotZ": 0}},
    {"driverValue":  90, "rootDelta": {"rotX": -10,"rotY": -5,"rotZ": 0}},
]

def test_evaluate_at_exact_key():
    assert evaluate_curve(CURVE, 0) == {"rotX": 0, "rotY": 0, "rotZ": 0}
    assert evaluate_curve(CURVE, -90) == {"rotX": 25, "rotY": 5, "rotZ": 0}
    assert evaluate_curve(CURVE, 90) == {"rotX": -10, "rotY": -5, "rotZ": 0}

def test_evaluate_linear_interpolation():
    result = evaluate_curve(CURVE, -45)
    assert result == {"rotX": 12.5, "rotY": 2.5, "rotZ": 0}

def test_evaluate_clamps_below_range():
    assert evaluate_curve(CURVE, -120) == {"rotX": 25, "rotY": 5, "rotZ": 0}

def test_evaluate_clamps_above_range():
    assert evaluate_curve(CURVE, 150) == {"rotX": -10, "rotY": -5, "rotZ": 0}
```

- [ ] **[AGENT] Step 3.1.3: Run — verify fails**

```bash
pytest tests/test_autoroot_evaluate.py -v
```
Expected: ModuleNotFoundError.

- [ ] **[AGENT] Step 3.1.4: Implement**

Create `src/sp_cloth/autoroot/evaluate.py`:

```python
"""Driver curve evaluation. Pure math, no 3dsmax dependency."""
from typing import List

Vec3 = dict  # {"rotX": float, "rotY": float, "rotZ": float}

def evaluate_curve(curve: List[dict], driver_value: float) -> Vec3:
    """Linear interpolation with clamp-extrapolation. Curve is monotonic in driverValue."""
    if driver_value <= curve[0]["driverValue"]:
        return dict(curve[0]["rootDelta"])
    if driver_value >= curve[-1]["driverValue"]:
        return dict(curve[-1]["rootDelta"])
    for i in range(len(curve) - 1):
        lo, hi = curve[i], curve[i + 1]
        if lo["driverValue"] <= driver_value <= hi["driverValue"]:
            t = (driver_value - lo["driverValue"]) / (hi["driverValue"] - lo["driverValue"])
            return {
                axis: lo["rootDelta"][axis] + t * (hi["rootDelta"][axis] - lo["rootDelta"][axis])
                for axis in ("rotX", "rotY", "rotZ")
            }
    raise RuntimeError("Unreachable: curve must be monotonic")
```

- [ ] **[AGENT] Step 3.1.5: Run — verify pass**

```bash
pytest tests/test_autoroot_evaluate.py -v
```
Expected: 4 passed.

- [ ] **[AGENT] Step 3.1.6: Commit**

```bash
git add src/sp_cloth/autoroot/ tests/test_autoroot_evaluate.py
git commit -m "feat(autoroot): single-driver curve evaluation with clamp extrapolation"
```

### Task 3.2: Multi-driver summing + per-attachment clamp

**Primary owner:** [AGENT]
**Estimated time:** 20 min
**Files:**
- Modify: `sp-cloth/src/sp_cloth/autoroot/evaluate.py`
- Modify: `sp-cloth/tests/test_autoroot_evaluate.py`

#### Steps

- [ ] **[AGENT] Step 3.2.1: Append failing tests**

Append to `tests/test_autoroot_evaluate.py`:

```python
from sp_cloth.autoroot.evaluate import evaluate_driver, evaluate_attachment

def test_evaluate_driver_returns_rootdelta_for_one_driver():
    driver = {"driverBone": "LeftUpLeg", "driverAxis": "rotation_x", "responseCurve": CURVE}
    bone_rotations = {"LeftUpLeg": {"rotation_x": -45}}
    result = evaluate_driver(driver, bone_rotations)
    assert result == {"rotX": 12.5, "rotY": 2.5, "rotZ": 0}

def test_evaluate_attachment_sums_multiple_drivers_and_clamps():
    drivers = [
        {"driverBone": "LeftUpLeg",  "driverAxis": "rotation_x", "responseCurve": CURVE},
        {"driverBone": "RightUpLeg", "driverAxis": "rotation_x", "responseCurve": CURVE},
    ]
    bone_rotations = {"LeftUpLeg": {"rotation_x": -90}, "RightUpLeg": {"rotation_x": -90}}
    # Sum is rotX=50, rotY=10, rotZ=0; max=35 → rotX clamps to 35
    result = evaluate_attachment(drivers, bone_rotations, max_rotation=35)
    assert result["rotX"] == 35
    assert result["rotY"] == 10  # within range

def test_evaluate_attachment_clamps_negative():
    drivers = [
        {"driverBone": "LeftUpLeg",  "driverAxis": "rotation_x", "responseCurve": CURVE},
        {"driverBone": "RightUpLeg", "driverAxis": "rotation_x", "responseCurve": CURVE},
    ]
    bone_rotations = {"LeftUpLeg": {"rotation_x": 90}, "RightUpLeg": {"rotation_x": 90}}
    # Sum is rotX=-20, rotY=0, rotZ=0; max=15 → rotX clamps to -15
    result = evaluate_attachment(drivers, bone_rotations, max_rotation=15)
    assert result["rotX"] == -15
```

- [ ] **[AGENT] Step 3.2.2: Run — verify fails**

```bash
pytest tests/test_autoroot_evaluate.py -v
```

- [ ] **[AGENT] Step 3.2.3: Implement**

Append to `src/sp_cloth/autoroot/evaluate.py`:

```python
def evaluate_driver(driver: dict, bone_rotations: dict) -> Vec3:
    bone = driver["driverBone"]
    axis = driver["driverAxis"]
    value = bone_rotations[bone][axis]
    return evaluate_curve(driver["responseCurve"], value)

def evaluate_attachment(drivers: List[dict], bone_rotations: dict, max_rotation: float) -> Vec3:
    summed = {"rotX": 0.0, "rotY": 0.0, "rotZ": 0.0}
    for d in drivers:
        contribution = evaluate_driver(d, bone_rotations)
        for axis in summed:
            summed[axis] += contribution[axis]
    for axis in summed:
        if summed[axis] > max_rotation:
            summed[axis] = max_rotation
        elif summed[axis] < -max_rotation:
            summed[axis] = -max_rotation
    return summed
```

- [ ] **[AGENT] Step 3.2.4: Run — verify all pass**

```bash
pytest tests/test_autoroot_evaluate.py -v
```
Expected: 7 passed.

- [ ] **[AGENT] Step 3.2.5: Commit**

```bash
git add src/sp_cloth/autoroot/evaluate.py tests/test_autoroot_evaluate.py
git commit -m "feat(autoroot): multi-driver summing with per-attachment rotation clamp"
```

### Task 3.3: Temporal smoothing

**Primary owner:** [AGENT]
**Estimated time:** 15 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/autoroot/smooth.py`
- Create: `sp-cloth/tests/test_autoroot_smooth.py`

#### Steps

- [ ] **[AGENT] Step 3.3.1: Write failing tests**

Create `tests/test_autoroot_smooth.py`:

```python
from sp_cloth.autoroot.smooth import moving_average

def test_moving_average_passthrough_when_window_one():
    values = [{"rotX": 1, "rotY": 0, "rotZ": 0}, {"rotX": 5, "rotY": 0, "rotZ": 0}]
    out = moving_average(values, window=1)
    assert out == values

def test_moving_average_smooths_step_function():
    values = [{"rotX": 0, "rotY": 0, "rotZ": 0}] * 3 + [{"rotX": 30, "rotY": 0, "rotZ": 0}] * 3
    out = moving_average(values, window=3)
    # Frame index 3 (the step): centered window covers indices 2,3,4 → (0+30+30)/3 = 20
    assert out[3]["rotX"] == 20

def test_moving_average_preserves_length():
    values = [{"rotX": float(i), "rotY": 0, "rotZ": 0} for i in range(10)]
    out = moving_average(values, window=3)
    assert len(out) == 10

def test_moving_average_edges_use_shrinking_window():
    values = [{"rotX": 10, "rotY": 0, "rotZ": 0}, {"rotX": 20, "rotY": 0, "rotZ": 0}, {"rotX": 30, "rotY": 0, "rotZ": 0}]
    out = moving_average(values, window=3)
    # Index 0: window=[0,1] → (10+20)/2 = 15
    assert out[0]["rotX"] == 15
    # Index 2: window=[1,2] → (20+30)/2 = 25
    assert out[2]["rotX"] == 25
```

- [ ] **[AGENT] Step 3.3.2: Run — verify fails**

- [ ] **[AGENT] Step 3.3.3: Implement**

Create `src/sp_cloth/autoroot/smooth.py`:

```python
"""Temporal smoothing for per-frame root deltas."""
from typing import List

def moving_average(values: List[dict], window: int) -> List[dict]:
    """Centered moving average over rotation values. Edge frames use shrinking window."""
    if window <= 1:
        return [dict(v) for v in values]
    half = window // 2
    out = []
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        chunk = values[lo:hi]
        avg = {axis: sum(v[axis] for v in chunk) / len(chunk) for axis in ("rotX", "rotY", "rotZ")}
        out.append(avg)
    return out
```

- [ ] **[AGENT] Step 3.3.4: Run — verify pass**

```bash
pytest tests/test_autoroot_smooth.py -v
```
Expected: 4 passed.

- [ ] **[AGENT] Step 3.3.5: Commit**

```bash
git add src/sp_cloth/autoroot/smooth.py tests/test_autoroot_smooth.py
git commit -m "feat(autoroot): centered moving-average temporal smoothing"
```

### Task 3.4: Auto-Root orchestrator (testable with injected I/O)

**Primary owner:** [AGENT]
**Estimated time:** 25 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/autoroot/apply.py`
- Modify: `sp-cloth/tests/test_autoroot_evaluate.py`

#### Steps

- [ ] **[AGENT] Step 3.4.1: Append integration test using fake I/O**

Append to `tests/test_autoroot_evaluate.py`:

```python
def test_apply_calls_evaluate_per_frame_and_writes_smoothed():
    from sp_cloth.autoroot.apply import apply_autoroot
    resolved = {
        "attachments": [{
            "name": "skirt", "rootBone": "Bip_Skirt_Root", "type": "skirt",
            "drivers": [{"driverBone": "LeftUpLeg", "driverAxis": "rotation_x",
                         "responseCurve": [{"driverValue": 0, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}},
                                           {"driverValue": 90, "rootDelta": {"rotX": 30, "rotY": 0, "rotZ": 0}}]}],
            "constraints": {"maxRotationDegrees": 50},
            "temporalSmoothingFrames": 1,
        }]
    }
    rotations_per_frame = {0: 0, 1: 30, 2: 60, 3: 90}
    def read(bones, frame): return {"LeftUpLeg": {"rotation_x": rotations_per_frame[frame]}}
    written = []
    def write(bone, frame, delta): written.append((bone, frame, delta))
    apply_autoroot(resolved, start_frame=0, end_frame=3,
                   read_bone_rotations=read, write_keyframe=write)
    assert len(written) == 4
    assert written[0] == ("Bip_Skirt_Root", 0, {"rotX": 0, "rotY": 0, "rotZ": 0})
    assert written[3] == ("Bip_Skirt_Root", 3, {"rotX": 30, "rotY": 0, "rotZ": 0})

def test_apply_skips_attachments_with_empty_drivers():
    from sp_cloth.autoroot.apply import apply_autoroot
    resolved = {"attachments": [{"name": "tail", "rootBone": "Bip_Tail", "type": "tail",
                                  "drivers": [], "constraints": {"maxRotationDegrees": 50},
                                  "temporalSmoothingFrames": 1}]}
    written = []
    apply_autoroot(resolved, 0, 0,
                   read_bone_rotations=lambda b, f: {},
                   write_keyframe=lambda *a: written.append(a))
    assert written == []
```

- [ ] **[AGENT] Step 3.4.2: Run — verify fails**

- [ ] **[AGENT] Step 3.4.3: Implement**

Create `src/sp_cloth/autoroot/apply.py`:

```python
"""End-to-end Auto-Root orchestrator. I/O injected for testability without 3dsmax."""
from sp_cloth.autoroot.evaluate import evaluate_attachment
from sp_cloth.autoroot.smooth import moving_average

def apply_autoroot(resolved_config: dict, start_frame: int, end_frame: int,
                   read_bone_rotations, write_keyframe) -> None:
    """Apply auto-root keyframing across [start_frame, end_frame] for every attachment.

    Parameters
    ----------
    resolved_config : dict
        Output of sp_cloth.config.loader.load_character(). Must have 'attachments'.
    start_frame, end_frame : int
        Inclusive range.
    read_bone_rotations : callable
        (bone_names: list[str], frame: int) -> {bone: {axis: degrees}}
    write_keyframe : callable
        (bone_name: str, frame: int, root_delta: {rotX, rotY, rotZ}) -> None
    """
    for attachment in resolved_config["attachments"]:
        drivers = attachment["drivers"]
        if not drivers:
            continue
        driver_bones = list({d["driverBone"] for d in drivers})
        max_rot = attachment["constraints"]["maxRotationDegrees"]
        smoothing = attachment.get("temporalSmoothingFrames", 1)
        root_bone = attachment["rootBone"]

        per_frame_deltas = []
        for f in range(start_frame, end_frame + 1):
            rotations = read_bone_rotations(driver_bones, f)
            delta = evaluate_attachment(drivers, rotations, max_rotation=max_rot)
            per_frame_deltas.append(delta)

        smoothed = moving_average(per_frame_deltas, window=smoothing)

        for offset, delta in enumerate(smoothed):
            write_keyframe(root_bone, start_frame + offset, delta)
```

- [ ] **[AGENT] Step 3.4.4: Run — verify pass**

```bash
pytest tests/ -v
```
Expected: all green so far.

- [ ] **[AGENT] Step 3.4.5: Commit**

```bash
git add src/sp_cloth/autoroot/apply.py tests/test_autoroot_evaluate.py
git commit -m "feat(autoroot): end-to-end orchestrator with injectable I/O"
```

### **[HANDOFF] Stage 3 → Stage 4**

- [ ] **[AGENT]** All pure-Python autoroot tests pass.
- [ ] **[HUMAN]** Now you take over: wire the orchestrator to real pymxs reads/writes in 3dsmax.

---

## Stage 4 — Auto-Root 3dsmax Integration

**Owner:** [HUMAN] (you, the TD)
**Goal:** Wire the pure-Python orchestrator to pymxs. Read driver bone rotations, write attachment root keyframes, run end-to-end on a real scene.
**Exit criteria:** Open a real character + animation, run `tools/run_autoroot.py`, see the skirt root react to thigh motion per the authored curves.

> **Note on pymxs APIs:** the exact function names below are educated guesses pending verification. Some may need adjustment based on Spike 0.1 findings or your 3dsmax version. **When in doubt, drop into MaxScript via `rt.execute("max script string here")`** — that bridge always works even when pymxs has gaps.

### Task 4.1: Bone rotation reader

**Primary owner:** [HUMAN]
**Estimated time:** 45–90 min (pymxs API discovery may take a while)
**Files:**
- Create: `sp-cloth/src/sp_cloth/maxio/__init__.py`
- Create: `sp-cloth/src/sp_cloth/maxio/bones.py`
- Create: `sp-cloth/tools/test_scenes/biped_test.max`
- Create: `sp-cloth/tools/manual_tests/test_bone_reader.py`
- Create: `sp-cloth/notes/pymxs_findings.md`

#### Steps

- [ ] **[HUMAN] Step 4.1.1: Set up the test scene**

In 3dsmax:
1. New scene.
2. Create a default biped.
3. Animate `LeftUpLeg.rotation.x`: frame 0 = 0°, frame 10 = -45°, frame 20 = -90°.
4. File → Save As → `sp-cloth/tools/test_scenes/biped_test.max`.

If Git LFS is set up for `.max` files, commit it via LFS. Otherwise add to `.gitignore` for now and keep the file local-only.

- [ ] **[HUMAN] Step 4.1.2: Create the maxio package**

```bash
cd /Users/mandl/Desktop/projects/sp-cloth
mkdir -p src/sp_cloth/maxio tools/test_scenes tools/manual_tests notes
touch src/sp_cloth/maxio/__init__.py
touch notes/pymxs_findings.md
```

- [ ] **[HUMAN] Step 4.1.3: Write the first cut of the bone reader**

Create `src/sp_cloth/maxio/bones.py`:

```python
"""Read bone rotation state from 3dsmax via pymxs. Must run inside 3dsmax.

NOTE: pymxs is imported at function-call time so pure-Python tests can import
this module without 3dsmax present."""

def read_bone_rotations(bone_names: list, frame: int) -> dict:
    """Return {bone_name: {'rotation_x': degrees, 'rotation_y': degrees, 'rotation_z': degrees}}
    at the given frame. Uses Euler XYZ decomposition (order=1)."""
    from pymxs import runtime as rt
    rt.sliderTime = frame
    out = {}
    for name in bone_names:
        node = rt.getNodeByName(name)
        if node is None:
            raise ValueError(f"Bone not found in scene: {name}")
        q = node.rotation
        euler = rt.quatToEuler2(q, order=1)
        out[name] = {
            "rotation_x": float(euler.x),
            "rotation_y": float(euler.y),
            "rotation_z": float(euler.z),
        }
    return out
```

- [ ] **[HUMAN] Step 4.1.4: Write the manual test runner**

Create `tools/manual_tests/test_bone_reader.py`:

```python
"""Run from inside 3dsmax: Scripting → Run Script → this file.
Assumes biped_test.max is currently loaded."""
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "src"))

from sp_cloth.maxio.bones import read_bone_rotations

for f in (0, 10, 20):
    rotations = read_bone_rotations(["LeftUpLeg"], f)
    print(f"Frame {f}: {rotations}")
```

- [ ] **[HUMAN] Step 4.1.5: Run and verify**

1. Open `biped_test.max`.
2. Scripting → Run Script → `tools/manual_tests/test_bone_reader.py`.
3. Watch the Listener.

Expected:
- Frame 0: rotation_x ≈ 0
- Frame 10: rotation_x ≈ -45 (within ±2° tolerance — Euler decomposition has gotchas)
- Frame 20: rotation_x ≈ -90

- [ ] **[HUMAN] Step 4.1.6: Troubleshoot if values are wrong**

If readings don't match:
- Maybe the biped's bone naming differs (`Bip001 L Thigh` not `LeftUpLeg`). Update bone names everywhere — including `AdultMale.json` — and re-run.
- Maybe Euler decomposition order is wrong. Try `order=2, 3, 4, 5, 6` in `rt.quatToEuler2(q, order=...)` until you find the one matching what 3dsmax displays.
- Maybe `rt.quatToEuler2` returns radians, not degrees. Convert with `math.degrees()` if so.

Document the working approach in `notes/pymxs_findings.md`:

```markdown
# pymxs findings (running log)

## Bone rotation read (Task 4.1)
- Working biped bone names in this project: ...
- `rt.quatToEuler2` order=N matches viewport rotation values
- Units: degrees / radians
- Sample reading at frame 10 for keyframed -45°: actual = ...
```

- [ ] **[HUMAN] Step 4.1.7: Update bones.py if needed**

If you discovered a different Euler order or unit conversion in 4.1.6, update `read_bone_rotations` accordingly. Re-run the manual test to confirm.

- [ ] **[HUMAN] Step 4.1.8: Commit**

```bash
git add src/sp_cloth/maxio/ tools/manual_tests/test_bone_reader.py notes/pymxs_findings.md
git commit -m "feat(maxio): bone rotation reader (pymxs) with Euler decomposition"
```

### Task 4.2: Keyframe writer for attachment roots

**Primary owner:** [HUMAN]
**Estimated time:** 45–90 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/maxio/keyframes.py`
- Create: `sp-cloth/tools/manual_tests/test_keyframe_writer.py`

#### Steps

- [ ] **[HUMAN] Step 4.2.1: Add a skirt root bone to the test scene**

Open `biped_test.max`. Create a Point/Dummy. Name it `Bip_Skirt_Root`. Parent it under the biped's `Pelvis`. Save.

- [ ] **[HUMAN] Step 4.2.2: Write the keyframe writer**

Create `src/sp_cloth/maxio/keyframes.py`:

```python
"""Write rotation keyframes to attachment root bones via pymxs."""

def write_root_rotation_keyframe(bone_name: str, frame: int, root_delta: dict) -> None:
    """Add (or update) a rotation keyframe at `frame` for `bone_name` adding root_delta
    (rotX, rotY, rotZ degrees) on top of the bone's rig-bound orientation.

    Implementation: builds a delta quaternion from Euler and composes onto the bone's
    current rotation, with animate(True) so a key is recorded."""
    from pymxs import runtime as rt
    node = rt.getNodeByName(bone_name)
    if node is None:
        raise ValueError(f"Bone not found: {bone_name}")
    rt.sliderTime = frame
    delta_euler = rt.eulerAngles(root_delta["rotX"], root_delta["rotY"], root_delta["rotZ"])
    delta_q = rt.eulerToQuat(delta_euler)
    with rt.animate(True):
        # Compose delta onto current rotation. Right-multiply applies delta in local space.
        node.rotation = node.rotation * delta_q
```

- [ ] **[HUMAN] Step 4.2.3: Write the manual test**

Create `tools/manual_tests/test_keyframe_writer.py`:

```python
from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / "src"))

from sp_cloth.maxio.keyframes import write_root_rotation_keyframe

# After loading biped_test.max
write_root_rotation_keyframe("Bip_Skirt_Root", 5, {"rotX": 10, "rotY": 0, "rotZ": 0})
print("Keyframe written at frame 5.")
```

- [ ] **[HUMAN] Step 4.2.4: Run and visually verify**

1. Open `biped_test.max`.
2. Scripting → Run Script → `test_keyframe_writer.py`.
3. Select `Bip_Skirt_Root` in viewport.
4. In the timeline, confirm a keyframe appeared at frame 5.
5. Scrub to frame 5; the dummy should be rotated +10° on X.
6. Scrub to frame 0 and frame 10; the dummy should NOT be rotated (no keyframes there).

- [ ] **[HUMAN] Step 4.2.5: Troubleshoot if rotation doesn't apply or no key appears**

Common pitfalls:
- `animate(True)` context block syntax varies across pymxs versions. Alternative: `rt.animButtonState = True` before assignment, restore after.
- Quaternion multiplication order. Try `delta_q * node.rotation` if right-multiply doesn't produce expected result.
- For some bone types in biped, you must use `rt.biped.setTransform` instead of direct rotation assignment.

Update `notes/pymxs_findings.md` with the working approach.

- [ ] **[HUMAN] Step 4.2.6: Commit**

```bash
git add src/sp_cloth/maxio/keyframes.py tools/manual_tests/test_keyframe_writer.py notes/pymxs_findings.md
git commit -m "feat(maxio): rotation keyframe writer for attachment root bones"
```

### Task 4.3: End-to-end Auto-Root in 3dsmax

**Primary owner:** [HUMAN]
**Estimated time:** 30–60 min
**Files:**
- Create: `sp-cloth/tools/run_autoroot.py`
- Create: `sp-cloth/configs/characters/TestCharacter.json`

#### Steps

- [ ] **[HUMAN] Step 4.3.1: Create the test character preset**

Create `configs/characters/TestCharacter.json`:

```json
{
  "id": "TestCharacter",
  "extends": "AdultMale",
  "attachments": [
    { "name": "skirt", "rootBone": "Bip_Skirt_Root", "type": "skirt",
      "clothSim": { "material": "soft_pleated_cotton" } }
  ]
}
```

- [ ] **[HUMAN] Step 4.3.2: Write the 3dsmax entry point**

Create `tools/run_autoroot.py`:

```python
"""Entry point from inside 3dsmax. Loads a character preset and applies Auto-Root
to the currently open animation."""
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "src"))

from pymxs import runtime as rt
from sp_cloth.config.loader import load_character
from sp_cloth.maxio.bones import read_bone_rotations
from sp_cloth.maxio.keyframes import write_root_rotation_keyframe
from sp_cloth.autoroot.apply import apply_autoroot

CHARACTER_PATH = repo / "configs" / "characters" / "TestCharacter.json"
BODY_TYPES_DIR = repo / "configs" / "body_types"
MATERIALS_PATH = repo / "configs" / "cloth_materials.json"

resolved = load_character(CHARACTER_PATH, BODY_TYPES_DIR, MATERIALS_PATH)
start = int(rt.animationRange.start)
end = int(rt.animationRange.end)
print(f"Applying Auto-Root to '{resolved['id']}' across frames {start}–{end}...")
apply_autoroot(resolved, start, end, read_bone_rotations, write_root_rotation_keyframe)
print("Auto-Root complete.")
```

- [ ] **[HUMAN] Step 4.3.3: Run end-to-end**

1. Open `biped_test.max` in 3dsmax.
2. Scripting → Run Script → `tools/run_autoroot.py`.
3. Wait for "Auto-Root complete."

- [ ] **[HUMAN] Step 4.3.4: Visually verify**

- Select `Bip_Skirt_Root` in viewport.
- Scrub the timeline. At every frame, the skirt root should have a keyframe.
- Compare frame 0 (no rotation) vs frame 20 (LeftUpLeg at -90°). The skirt root should be rotated ~+25° on X (per the body type's authored curve), summed with whatever RightUpLeg contributes (likely 0 since RightUpLeg isn't keyframed).
- Smoothing should make adjacent frames similar; no sudden jumps.

If the result is wrong:
- Drivers reading from incorrect bones? Check bone names in `AdultMale.json`.
- Smoothing window too large or too small? Adjust `temporalSmoothingFrames` in the body type.
- Quaternion composition wrong? Revisit Task 4.2.5 troubleshooting.

- [ ] **[HUMAN] Step 4.3.5: Commit**

```bash
git add tools/run_autoroot.py configs/characters/TestCharacter.json
git commit -m "feat(autoroot): end-to-end Auto-Root entry point + test character"
```

### Task 4.4: Author drivers for tail / hairLong / sleeve

**Primary owner:** [HUMAN]
**Estimated time:** 30–60 min
**Files:**
- Modify: `sp-cloth/configs/body_types/AdultMale.json`

#### Steps

- [ ] **[HUMAN] Step 4.4.1: Pick a real character with each attachment type**

Identify characters in your project's roster that have: a tail, long hair, and visible sleeves. You'll iterate driver curves against their actual animations.

- [ ] **[HUMAN] Step 4.4.2: Author tail drivers**

In `AdultMale.json`, fill `attachmentDriverDefaults.tail.drivers`:

```json
"drivers": [
  { "driverBone": "Pelvis", "driverAxis": "rotation_x",
    "responseCurve": [
      {"driverValue": -45, "rootDelta": {"rotX": 15, "rotY": 0, "rotZ": 0}},
      {"driverValue":   0, "rootDelta": {"rotX": 0,  "rotY": 0, "rotZ": 0}},
      {"driverValue":  45, "rootDelta": {"rotX": -15, "rotY": 0, "rotZ": 0}}
    ]}
]
```

These are starting values. Tune in pilot.

- [ ] **[HUMAN] Step 4.4.3: Author hairLong drivers**

Fill `hairLong.drivers`. Driver is usually the upper spine / shoulders for hair sway:

```json
"drivers": [
  { "driverBone": "Spine_03", "driverAxis": "rotation_x",
    "responseCurve": [
      {"driverValue": -30, "rootDelta": {"rotX":  20, "rotY": 0, "rotZ": 0}},
      {"driverValue":   0, "rootDelta": {"rotX":   0, "rotY": 0, "rotZ": 0}},
      {"driverValue":  30, "rootDelta": {"rotX": -20, "rotY": 0, "rotZ": 0}}
    ]}
]
```

- [ ] **[HUMAN] Step 4.4.4: Author sleeve drivers**

Fill `sleeve.drivers`:

```json
"drivers": [
  { "driverBone": "LeftArm", "driverAxis": "rotation_x",
    "responseCurve": [
      {"driverValue": -90, "rootDelta": {"rotX":  10, "rotY": 5, "rotZ": 0}},
      {"driverValue":   0, "rootDelta": {"rotX":   0, "rotY": 0, "rotZ": 0}},
      {"driverValue":  90, "rootDelta": {"rotX": -10, "rotY": -5, "rotZ": 0}}
    ]},
  { "driverBone": "RightArm", "driverAxis": "rotation_x",
    "responseCurve": [
      {"driverValue": -90, "rootDelta": {"rotX":  10, "rotY": -5, "rotZ": 0}},
      {"driverValue":   0, "rootDelta": {"rotX":   0, "rotY": 0, "rotZ": 0}},
      {"driverValue":  90, "rootDelta": {"rotX": -10, "rotY":  5, "rotZ": 0}}
    ]}
]
```

- [ ] **[HUMAN] Step 4.4.5: Re-run tests to confirm everything still loads**

```bash
pytest tests/ -v
```

Expected: all green.

- [ ] **[HUMAN] Step 4.4.6: Commit**

```bash
git add configs/body_types/AdultMale.json
git commit -m "feat(configs): rough driver defaults for tail/hairLong/sleeve attachments"
```

### **[HANDOFF] Stage 4 → Stage 5**

- [ ] **[HUMAN]** Auto-Root works end-to-end on a synthetic biped scene.
- [ ] Next: capsule generation (Stage 5). 5.1 (PCA math) is [AGENT] work; 5.2 (pymxs skin queries) is [HUMAN].

---

## Stage 5 — Capsule Auto-Generator

**Owner:** Mixed. 5.1 [AGENT], 5.2 [HUMAN].
**Goal:** Auto-generate body collision capsules from skinning weights. Used by Batch Cloth Sim Runner in Stage 7.
**Exit criteria:** Open a character, run `tools/run_capsule_generator.py`, see capsules appear correctly placed parented to leg/hip/spine/shoulder bones.

### Task 5.1: PCA capsule fitting (pure math)

**Primary owner:** [AGENT]
**Estimated time:** 30 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/capsule/__init__.py`
- Create: `sp-cloth/src/sp_cloth/capsule/fit.py`
- Create: `sp-cloth/tests/test_capsule_fit.py`

#### Steps

- [ ] **[AGENT] Step 5.1.1: Create capsule subpackage**

```bash
mkdir -p src/sp_cloth/capsule
touch src/sp_cloth/capsule/__init__.py
```

- [ ] **[AGENT] Step 5.1.2: Write failing tests**

Create `tests/test_capsule_fit.py`:

```python
import math
from sp_cloth.capsule.fit import fit_capsule

def test_fit_capsule_along_x_axis():
    verts = [(float(x), 0.0, 0.0) for x in range(-10, 11)]
    capsule = fit_capsule(verts, scale_factor=1.0)
    assert abs(capsule["axis"][0]) > 0.9
    assert 18 < capsule["length"] < 22
    assert capsule["radius"] < 0.5

def test_fit_capsule_scale_factor_applied():
    verts = [(float(x), 0.0, 0.0) for x in range(-10, 11)]
    capsule = fit_capsule(verts, scale_factor=0.5)
    assert capsule["length"] < 11

def test_fit_capsule_handles_thick_cluster():
    verts = []
    for y in range(-10, 11):
        for theta in range(0, 360, 45):
            r = 3
            verts.append((r * math.cos(math.radians(theta)), float(y), r * math.sin(math.radians(theta))))
    capsule = fit_capsule(verts, scale_factor=1.0)
    assert abs(capsule["axis"][1]) > 0.9
    assert 2.5 < capsule["radius"] < 3.5

def test_fit_capsule_rejects_too_few_vertices():
    import pytest
    with pytest.raises(ValueError, match="at least"):
        fit_capsule([(0.0, 0.0, 0.0)], scale_factor=1.0)
```

- [ ] **[AGENT] Step 5.1.3: Run — verify fails**

- [ ] **[AGENT] Step 5.1.4: Implement**

Create `src/sp_cloth/capsule/fit.py`:

```python
"""PCA-based capsule fitting from a vertex set. Pure math, no 3dsmax dependency."""
import math
from typing import List, Tuple

def fit_capsule(vertices: List[Tuple[float, float, float]], scale_factor: float = 1.0) -> dict:
    """Fit a bounding capsule via PCA.

    Returns
    -------
    {'center': (x,y,z),
     'axis': (x,y,z) unit vector along principal axis,
     'length': float (distance between endpoint centers, NOT including hemispherical caps),
     'radius': float}
    """
    n = len(vertices)
    if n < 2:
        raise ValueError("fit_capsule needs at least 2 vertices")

    cx = sum(v[0] for v in vertices) / n
    cy = sum(v[1] for v in vertices) / n
    cz = sum(v[2] for v in vertices) / n

    sxx = syy = szz = sxy = sxz = syz = 0.0
    for x, y, z in vertices:
        dx, dy, dz = x - cx, y - cy, z - cz
        sxx += dx * dx; syy += dy * dy; szz += dz * dz
        sxy += dx * dy; sxz += dx * dz; syz += dy * dz

    cov = [[sxx, sxy, sxz], [sxy, syy, syz], [sxz, syz, szz]]
    axis = _dominant_eigenvector(cov)

    projs = [(x - cx) * axis[0] + (y - cy) * axis[1] + (z - cz) * axis[2] for x, y, z in vertices]
    length = max(projs) - min(projs)

    radius = 0.0
    for x, y, z in vertices:
        dx, dy, dz = x - cx, y - cy, z - cz
        proj = dx * axis[0] + dy * axis[1] + dz * axis[2]
        perp_x = dx - proj * axis[0]
        perp_y = dy - proj * axis[1]
        perp_z = dz - proj * axis[2]
        d = math.sqrt(perp_x ** 2 + perp_y ** 2 + perp_z ** 2)
        if d > radius:
            radius = d

    return {
        "center": (cx, cy, cz),
        "axis": tuple(axis),
        "length": length * scale_factor,
        "radius": radius * scale_factor,
    }

def _dominant_eigenvector(m: List[List[float]], iterations: int = 50) -> List[float]:
    v = [1.0, 0.0, 0.0]
    for _ in range(iterations):
        w = [m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
             m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
             m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2]]
        norm = math.sqrt(w[0]**2 + w[1]**2 + w[2]**2)
        if norm < 1e-12:
            return [1.0, 0.0, 0.0]
        v = [w[0]/norm, w[1]/norm, w[2]/norm]
    return v
```

- [ ] **[AGENT] Step 5.1.5: Run — verify pass**

```bash
pytest tests/test_capsule_fit.py -v
```
Expected: 4 passed.

- [ ] **[AGENT] Step 5.1.6: Commit**

```bash
git add src/sp_cloth/capsule/ tests/test_capsule_fit.py
git commit -m "feat(capsule): PCA-based capsule fitting from vertex set"
```

### Task 5.2: pymxs integration — skinning queries + scene materialization

**Primary owner:** [HUMAN]
**Estimated time:** 60–120 min (Skin Ops API is finicky)
**Files:**
- Create: `sp-cloth/src/sp_cloth/capsule/generate.py`
- Create: `sp-cloth/tools/run_capsule_generator.py`

#### Steps

- [ ] **[HUMAN] Step 5.2.1: Write the vertex-gathering function**

Create `src/sp_cloth/capsule/generate.py`:

```python
"""Generate body collision capsules from skinning weights in a 3dsmax scene."""
from sp_cloth.capsule.fit import fit_capsule

def generate_capsules_for_character(resolved_config: dict, mesh_node_name: str,
                                    weight_threshold: float = 0.5) -> dict:
    """For each bone in each collisionSet, fit a capsule from vertices skinned to that bone
    above weight_threshold. Returns {bone_name: capsule_dict}. Read-only on the scene."""
    from pymxs import runtime as rt
    mesh = rt.getNodeByName(mesh_node_name)
    if mesh is None:
        raise ValueError(f"Mesh not found: {mesh_node_name}")
    skin_mod = _find_skin_modifier(mesh, rt)
    if skin_mod is None:
        raise ValueError(f"Mesh '{mesh_node_name}' has no Skin modifier")

    capsules = {}
    seen_bones = set()
    for set_name, set_def in resolved_config["collisionSets"].items():
        scale = set_def["scaleFactor"]
        for bone_name in set_def["bones"]:
            if bone_name in seen_bones:
                continue
            seen_bones.add(bone_name)
            verts = _gather_vertices_for_bone(mesh, skin_mod, bone_name, weight_threshold, rt)
            if len(verts) < 4:
                print(f"WARN: bone '{bone_name}' has <4 vertices above threshold {weight_threshold}; skipping")
                continue
            capsules[bone_name] = fit_capsule(verts, scale_factor=scale)
    return capsules

def _find_skin_modifier(node, rt):
    for m in node.modifiers:
        if rt.classOf(m) == rt.Skin:
            return m
    return None

def _gather_vertices_for_bone(mesh, skin_mod, bone_name, threshold, rt):
    """Return world-space vertex positions skinned to bone_name with weight > threshold.
    Uses skinOps API which is 1-indexed and slightly different from typical MaxScript."""
    # Modifier must be active for skinOps to work
    rt.modPanel.setCurrentObject(skin_mod, node=mesh)

    # Find bone ID
    bone_id = None
    bone_count = rt.skinOps.GetNumberBones(skin_mod)
    for i in range(1, bone_count + 1):
        bname = rt.skinOps.GetBoneName(skin_mod, i, 0)
        if bname == bone_name:
            bone_id = i
            break
    if bone_id is None:
        return []

    verts = []
    vcount = rt.skinOps.GetNumberVertices(skin_mod)
    for vi in range(1, vcount + 1):
        wcount = rt.skinOps.GetVertexWeightCount(skin_mod, vi)
        for wi in range(1, wcount + 1):
            wbone = rt.skinOps.GetVertexWeightBoneID(skin_mod, vi, wi)
            if wbone == bone_id:
                w = rt.skinOps.GetVertexWeight(skin_mod, vi, wi)
                if w > threshold:
                    pos = rt.GetVert(mesh.mesh, vi)
                    verts.append((float(pos.x), float(pos.y), float(pos.z)))
                break
    return verts
```

- [ ] **[HUMAN] Step 5.2.2: Write the scene-materialization function**

Append to `src/sp_cloth/capsule/generate.py`:

```python
def create_capsule_primitives(capsules: dict, parent_bones: bool = True) -> list:
    """Create Capsule primitives representing each capsule, parented to its bone."""
    from pymxs import runtime as rt
    import math

    created = []
    for bone_name, cap in capsules.items():
        bone_node = rt.getNodeByName(bone_name)
        if bone_node is None:
            print(f"WARN: bone '{bone_name}' not found; cannot parent capsule")
            continue

        # 3dsmax built-in: Capsule extended primitive
        node = rt.Capsule(radius=cap["radius"], height=cap["length"])
        node.name = f"_collision_{bone_name}"

        # Center
        cx, cy, cz = cap["center"]
        node.position = rt.Point3(cx, cy, cz)

        # Orient along axis: build rotation from world-up (Z) to capsule axis
        ax, ay, az = cap["axis"]
        # If axis is essentially Z-up, no rotation needed
        if abs(az) > 0.999:
            pass
        else:
            # Build rotation that maps (0,0,1) to (ax,ay,az)
            cross = (ay * 1.0 - az * 0.0, az * 0.0 - ax * 1.0, ax * 0.0 - ay * 0.0)  # (0,0,1) × axis
            dot = az
            angle_rad = math.acos(max(-1.0, min(1.0, dot)))
            angle_deg = math.degrees(angle_rad)
            cnorm = math.sqrt(cross[0]**2 + cross[1]**2 + cross[2]**2)
            if cnorm > 1e-6:
                axis_normalized = (cross[0]/cnorm, cross[1]/cnorm, cross[2]/cnorm)
                rot = rt.AngleAxis(angle_deg, rt.Point3(*axis_normalized))
                node.rotation = rot

        if parent_bones:
            node.parent = bone_node
        created.append(node)
    return created
```

- [ ] **[HUMAN] Step 5.2.3: Write the entry point**

Create `tools/run_capsule_generator.py`:

```python
"""Run inside 3dsmax. Generates collision capsules for the loaded character.
The character's body mesh must be named matching MESH_NODE below (or edit the script)."""
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "src"))

from sp_cloth.config.loader import load_character
from sp_cloth.capsule.generate import generate_capsules_for_character, create_capsule_primitives

CHARACTER_PATH = repo / "configs" / "characters" / "TestCharacter.json"
BODY_TYPES_DIR = repo / "configs" / "body_types"
MATERIALS_PATH = repo / "configs" / "cloth_materials.json"

# Edit per scene:
MESH_NODE = "TestCharacter_Body"   # the skinned mesh name in the loaded scene

resolved = load_character(CHARACTER_PATH, BODY_TYPES_DIR, MATERIALS_PATH)
print(f"Generating capsules for '{resolved['id']}', mesh '{MESH_NODE}'...")
capsules = generate_capsules_for_character(resolved, MESH_NODE)
print(f"Fit {len(capsules)} capsules.")
created = create_capsule_primitives(capsules)
print(f"Created {len(created)} capsule primitives in scene.")
```

- [ ] **[HUMAN] Step 5.2.4: Pick a real character scene for testing**

You need a real character (skinned mesh with a Skin modifier, biped skeleton, named bones matching your `AdultMale.json`). Open it in 3dsmax.

- [ ] **[HUMAN] Step 5.2.5: Update MESH_NODE in run_capsule_generator.py**

Set `MESH_NODE` to the actual skinned mesh's name in the open scene.

- [ ] **[HUMAN] Step 5.2.6: Run and visually verify**

1. Scripting → Run Script → `run_capsule_generator.py`.
2. Watch the Listener for `WARN` messages (bones with too few vertices).
3. Look in viewport — capsules should appear at thigh, hip, spine, shoulder positions.

Expected:
- Each capsule is parented to its bone (selecting `_collision_LeftUpLeg` selects an object under `LeftUpLeg` in hierarchy).
- Capsule axis runs along the bone's length.
- Capsule radius hugs the body geometry × 0.9 scale.

- [ ] **[HUMAN] Step 5.2.7: Troubleshoot if capsules are wrong**

Common issues:
- **Capsule positioned at world origin** — probably `GetVert` returned local-space verts. Use `rt.meshOp.getVert` or transform by `mesh.objectTransform` to get world space.
- **Capsule oriented wrong** — the rotation construction in `create_capsule_primitives` may be off. Try alternative quaternion construction or use Aimer constraint.
- **`skinOps.GetVertexWeightBoneID` always returns 0** — modifier may not be active. Confirm `rt.modPanel.setCurrentObject(...)` succeeded.
- **Capsules too big** — `0.9` scale wasn't applied. Check `fit_capsule(verts, scale_factor=scale)` is being called correctly.

Document working approach in `notes/pymxs_findings.md`.

- [ ] **[HUMAN] Step 5.2.8: Refine and re-test**

Once the first character looks right, test on 1–2 more characters. Capsule generation should produce sensible output across body types without manual tuning.

- [ ] **[HUMAN] Step 5.2.9: Commit**

```bash
git add src/sp_cloth/capsule/generate.py tools/run_capsule_generator.py notes/pymxs_findings.md
git commit -m "feat(capsule): auto-generate body collision capsules from skinning weights"
```

### **[HANDOFF] Stage 5 → Stage 6**

- [ ] **[HUMAN]** Capsules generate correctly on real characters.
- [ ] Next: build the Driver Setup UI panel (entirely [HUMAN] in 3dsmax).

---

## Stage 6 — Driver Setup Panel (PySide2 UI in 3dsmax)

**Owner:** [HUMAN]
**Goal:** Build the visual editor animators use to author character presets.
**Exit criteria:** Animator can open the panel, create a new character preset for the AdultMale body type, declare attachments, override driver curves, preview the result, and save — without ever touching JSON.

> **PySide2 verification:** 3dsmax 2024+ ships PySide2. If your version doesn't have it, use 3dsmax's native MaxScript rollout instead. The structure stays the same; the implementation language changes.

### Task 6.1: Panel skeleton with load/save and body type dropdown

**Primary owner:** [HUMAN]
**Estimated time:** 60 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/ui/__init__.py`
- Create: `sp-cloth/src/sp_cloth/ui/driver_setup_panel.py`
- Create: `sp-cloth/tools/run_driver_setup_panel.py`

#### Steps

- [ ] **[HUMAN] Step 6.1.1: Create ui subpackage**

```bash
mkdir -p src/sp_cloth/ui
touch src/sp_cloth/ui/__init__.py
```

- [ ] **[HUMAN] Step 6.1.2: Build the panel skeleton**

Create `src/sp_cloth/ui/driver_setup_panel.py`:

```python
"""Driver Setup panel for animators. Runs as a PySide2 window inside 3dsmax."""
import json
from pathlib import Path
from PySide2 import QtWidgets, QtCore


class DriverSetupPanel(QtWidgets.QWidget):
    def __init__(self, configs_dir: Path, parent=None):
        super().__init__(parent)
        self.configs_dir = configs_dir
        self.current_path = None
        self.preset = {"id": "", "extends": "", "attachments": []}
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Header row
        header = QtWidgets.QHBoxLayout()
        self.id_label = QtWidgets.QLabel("Character ID:")
        self.id_edit = QtWidgets.QLineEdit()
        self.id_edit.textChanged.connect(self._on_id_changed)

        self.body_type_label = QtWidgets.QLabel("Body type:")
        self.body_type_combo = QtWidgets.QComboBox()
        self._populate_body_types()
        self.body_type_combo.currentTextChanged.connect(self._on_body_type_changed)

        self.load_btn = QtWidgets.QPushButton("Load…")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.load_btn.clicked.connect(self._on_load)
        self.save_btn.clicked.connect(self._on_save)

        header.addWidget(self.id_label)
        header.addWidget(self.id_edit)
        header.addSpacing(20)
        header.addWidget(self.body_type_label)
        header.addWidget(self.body_type_combo)
        header.addStretch(1)
        header.addWidget(self.load_btn)
        header.addWidget(self.save_btn)
        layout.addLayout(header)

        # Body placeholder (Task 6.2 fills in)
        self.body = QtWidgets.QLabel("Per-attachment editor goes here (Task 6.2)")
        layout.addWidget(self.body)
        layout.addStretch(1)

    def _populate_body_types(self):
        body_types_dir = self.configs_dir / "body_types"
        for p in sorted(body_types_dir.glob("*.json")):
            self.body_type_combo.addItem(p.stem)

    def _on_id_changed(self, text):
        self.preset["id"] = text

    def _on_body_type_changed(self, text):
        self.preset["extends"] = text

    def _on_load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load character preset",
            str(self.configs_dir / "characters"),
            "JSON (*.json)")
        if not path:
            return
        self.current_path = Path(path)
        with open(path) as f:
            self.preset = json.load(f)
        self.id_edit.setText(self.preset.get("id", ""))
        idx = self.body_type_combo.findText(self.preset.get("extends", ""))
        if idx >= 0:
            self.body_type_combo.setCurrentIndex(idx)

    def _on_save(self):
        if not self.preset.get("id"):
            QtWidgets.QMessageBox.warning(self, "Missing ID", "Set a Character ID before saving.")
            return
        if not self.current_path:
            default = self.configs_dir / "characters" / f"{self.preset['id']}.json"
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save character preset", str(default), "JSON (*.json)")
            if not path:
                return
            self.current_path = Path(path)
        with open(self.current_path, "w") as f:
            json.dump(self.preset, f, indent=2)
        QtWidgets.QMessageBox.information(self, "Saved", str(self.current_path))
```

- [ ] **[HUMAN] Step 6.1.3: Write the entry point**

Create `tools/run_driver_setup_panel.py`:

```python
"""Run inside 3dsmax. Opens the Driver Setup panel."""
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "src"))

from PySide2 import QtWidgets
from sp_cloth.ui.driver_setup_panel import DriverSetupPanel

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

# Keep a module-level reference to prevent GC
global _panel
_panel = DriverSetupPanel(configs_dir=repo / "configs")
_panel.setWindowTitle("sp-cloth Driver Setup")
_panel.resize(800, 600)
_panel.show()
```

- [ ] **[HUMAN] Step 6.1.4: Run and verify**

1. In 3dsmax, Scripting → Run Script → `run_driver_setup_panel.py`.
2. Window should appear.
3. Body type dropdown should list `AdultMale`.
4. Click Load → should open a file dialog rooted at `configs/characters/`.
5. Type an ID, pick body type, click Save → confirm new JSON file appears at `configs/characters/<id>.json` with correct structure.

- [ ] **[HUMAN] Step 6.1.5: Troubleshoot if window doesn't appear or PySide2 missing**

If PySide2 isn't available:
- Try `from PySide6 import QtWidgets` (newer 3dsmax versions)
- Or switch to 3dsmax MaxScript rollout (less elegant but reliable)

If window appears but closes immediately, the GC issue: make sure `_panel` is module-level (the `global _panel` line above).

- [ ] **[HUMAN] Step 6.1.6: Commit**

```bash
git add src/sp_cloth/ui/ tools/run_driver_setup_panel.py
git commit -m "feat(ui): driver setup panel skeleton with load/save + body type dropdown"
```

### Task 6.2: Attachment editor (list + add/remove + bone picker)

**Primary owner:** [HUMAN]
**Estimated time:** 90 min
**Files:**
- Modify: `sp-cloth/src/sp_cloth/ui/driver_setup_panel.py`

#### Steps

- [ ] **[HUMAN] Step 6.2.1: Replace the placeholder with an attachment list + detail panel**

In `_build_ui`, replace the `self.body = QtWidgets.QLabel(...)` line with:

```python
        # Body: split view of attachment list + detail editor
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left: list of attachments + add/remove
        left = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left)
        self.attachment_list = QtWidgets.QListWidget()
        self.attachment_list.currentRowChanged.connect(self._on_attachment_selected)
        left_layout.addWidget(QtWidgets.QLabel("Attachments"))
        left_layout.addWidget(self.attachment_list)
        btn_row = QtWidgets.QHBoxLayout()
        self.add_att_btn = QtWidgets.QPushButton("Add")
        self.remove_att_btn = QtWidgets.QPushButton("Remove")
        self.add_att_btn.clicked.connect(self._on_add_attachment)
        self.remove_att_btn.clicked.connect(self._on_remove_attachment)
        btn_row.addWidget(self.add_att_btn)
        btn_row.addWidget(self.remove_att_btn)
        left_layout.addLayout(btn_row)

        # Right: detail editor
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QFormLayout(right)
        self.att_name_edit = QtWidgets.QLineEdit()
        self.att_name_edit.editingFinished.connect(self._on_detail_changed)
        self.att_type_combo = QtWidgets.QComboBox()
        self.att_type_combo.addItems(["skirt", "tail", "hairLong", "sleeve"])
        self.att_type_combo.currentTextChanged.connect(self._on_detail_changed)
        self.att_rootbone_edit = QtWidgets.QLineEdit()
        self.att_rootbone_pick = QtWidgets.QPushButton("Pick from scene")
        self.att_rootbone_pick.clicked.connect(self._on_pick_rootbone)
        rootbone_row = QtWidgets.QHBoxLayout()
        rootbone_row.addWidget(self.att_rootbone_edit)
        rootbone_row.addWidget(self.att_rootbone_pick)
        self.att_material_combo = QtWidgets.QComboBox()
        self._populate_materials()
        self.att_material_combo.currentTextChanged.connect(self._on_detail_changed)
        right_layout.addRow("Name:", self.att_name_edit)
        right_layout.addRow("Type:", self.att_type_combo)
        right_layout.addRow("Root bone:", rootbone_row)
        right_layout.addRow("Cloth material:", self.att_material_combo)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        layout.addWidget(split)
```

- [ ] **[HUMAN] Step 6.2.2: Add the supporting methods**

Add these methods to `DriverSetupPanel`:

```python
    def _populate_materials(self):
        with open(self.configs_dir / "cloth_materials.json") as f:
            mats = json.load(f)["materials"]
        self.att_material_combo.addItem("(no cloth sim)")
        for name in sorted(mats.keys()):
            self.att_material_combo.addItem(name)

    def _on_add_attachment(self):
        new_att = {"name": "new_attachment", "rootBone": "", "type": "skirt", "clothSim": None}
        self.preset.setdefault("attachments", []).append(new_att)
        self.attachment_list.addItem(new_att["name"])
        self.attachment_list.setCurrentRow(self.attachment_list.count() - 1)

    def _on_remove_attachment(self):
        row = self.attachment_list.currentRow()
        if row < 0:
            return
        self.attachment_list.takeItem(row)
        del self.preset["attachments"][row]

    def _on_attachment_selected(self, row):
        if row < 0 or row >= len(self.preset.get("attachments", [])):
            return
        att = self.preset["attachments"][row]
        self.att_name_edit.setText(att.get("name", ""))
        self.att_type_combo.setCurrentText(att.get("type", "skirt"))
        self.att_rootbone_edit.setText(att.get("rootBone", ""))
        cs = att.get("clothSim")
        if cs and cs.get("material"):
            self.att_material_combo.setCurrentText(cs["material"])
        else:
            self.att_material_combo.setCurrentText("(no cloth sim)")

    def _on_detail_changed(self):
        row = self.attachment_list.currentRow()
        if row < 0:
            return
        att = self.preset["attachments"][row]
        att["name"] = self.att_name_edit.text()
        att["type"] = self.att_type_combo.currentText()
        att["rootBone"] = self.att_rootbone_edit.text()
        mat = self.att_material_combo.currentText()
        att["clothSim"] = None if mat == "(no cloth sim)" else {"material": mat}
        self.attachment_list.currentItem().setText(att["name"])

    def _on_pick_rootbone(self):
        from pymxs import runtime as rt
        sel = rt.selection
        if len(sel) == 0:
            QtWidgets.QMessageBox.information(self, "No selection", "Select a bone in viewport first.")
            return
        self.att_rootbone_edit.setText(sel[0].name)
        self._on_detail_changed()
```

- [ ] **[HUMAN] Step 6.2.3: Update _on_load to populate the attachment list**

Modify `_on_load` to add at the end:

```python
        self.attachment_list.clear()
        for att in self.preset.get("attachments", []):
            self.attachment_list.addItem(att["name"])
```

- [ ] **[HUMAN] Step 6.2.4: Manual test**

1. Restart the panel (close + run script again).
2. Set Character ID = "TestPanel", body type = AdultMale.
3. Add an attachment. Set name = "skirt", type = "skirt", select a bone in 3dsmax viewport, click "Pick from scene" — the rootBone field should populate.
4. Pick a material.
5. Save. Open the saved JSON and confirm structure:

```json
{
  "id": "TestPanel",
  "extends": "AdultMale",
  "attachments": [
    {"name": "skirt", "rootBone": "...", "type": "skirt", "clothSim": {"material": "..."}}
  ]
}
```

6. Restart panel, Load the file — confirm everything repopulates.

- [ ] **[HUMAN] Step 6.2.5: Commit**

```bash
git add src/sp_cloth/ui/driver_setup_panel.py
git commit -m "feat(ui): per-attachment list/detail editor with pick-from-scene"
```

### Task 6.3: Driver curve override editor

**Primary owner:** [HUMAN]
**Estimated time:** 90–120 min
**Files:**
- Modify: `sp-cloth/src/sp_cloth/ui/driver_setup_panel.py`

#### Steps

- [ ] **[HUMAN] Step 6.3.1: Add a "Drivers" section to the detail editor**

After the material row in the right-side form, add:

```python
        # Drivers section
        self.use_default_drivers_check = QtWidgets.QCheckBox("Use body type defaults")
        self.use_default_drivers_check.setChecked(True)
        self.use_default_drivers_check.stateChanged.connect(self._on_use_default_drivers_changed)
        right_layout.addRow("Drivers:", self.use_default_drivers_check)

        self.drivers_widget = QtWidgets.QWidget()
        drivers_layout = QtWidgets.QVBoxLayout(self.drivers_widget)
        self.drivers_table = QtWidgets.QTableWidget(0, 5)
        self.drivers_table.setHorizontalHeaderLabels(["Driver Bone", "Axis", "Driver Value", "Root Δ XYZ", ""])
        self.drivers_table.horizontalHeader().setStretchLastSection(True)
        drivers_layout.addWidget(self.drivers_table)
        driver_btn_row = QtWidgets.QHBoxLayout()
        self.add_driver_btn = QtWidgets.QPushButton("Add Driver")
        self.add_key_btn = QtWidgets.QPushButton("Add Curve Point")
        self.add_driver_btn.clicked.connect(self._on_add_driver)
        self.add_key_btn.clicked.connect(self._on_add_key)
        driver_btn_row.addWidget(self.add_driver_btn)
        driver_btn_row.addWidget(self.add_key_btn)
        drivers_layout.addLayout(driver_btn_row)
        self.drivers_widget.setVisible(False)
        right_layout.addRow("", self.drivers_widget)
```

- [ ] **[HUMAN] Step 6.3.2: Add the supporting methods**

```python
    def _on_use_default_drivers_changed(self, state):
        use_default = state == QtCore.Qt.Checked
        self.drivers_widget.setVisible(not use_default)
        row = self.attachment_list.currentRow()
        if row < 0:
            return
        att = self.preset["attachments"][row]
        if use_default:
            att.pop("driverOverrides", None)
        else:
            att.setdefault("driverOverrides", [])
        self._refresh_drivers_table()

    def _on_add_driver(self):
        row = self.attachment_list.currentRow()
        if row < 0:
            return
        att = self.preset["attachments"][row]
        att.setdefault("driverOverrides", []).append({
            "driverBone": "",
            "driverAxis": "rotation_x",
            "responseCurve": [
                {"driverValue": -90, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}},
                {"driverValue":   0, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}},
                {"driverValue":  90, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}},
            ],
        })
        self._refresh_drivers_table()

    def _on_add_key(self):
        # Simple: append a new key at the end of every driver's curve
        row = self.attachment_list.currentRow()
        if row < 0:
            return
        att = self.preset["attachments"][row]
        for d in att.get("driverOverrides", []):
            last = d["responseCurve"][-1]["driverValue"]
            d["responseCurve"].append({"driverValue": last + 10, "rootDelta": {"rotX": 0, "rotY": 0, "rotZ": 0}})
        self._refresh_drivers_table()

    def _refresh_drivers_table(self):
        row = self.attachment_list.currentRow()
        if row < 0:
            self.drivers_table.setRowCount(0)
            return
        att = self.preset["attachments"][row]
        drivers = att.get("driverOverrides", [])
        all_rows = []
        for di, d in enumerate(drivers):
            for ki, k in enumerate(d["responseCurve"]):
                all_rows.append((di, ki, d, k))
        self.drivers_table.setRowCount(len(all_rows))
        for i, (di, ki, d, k) in enumerate(all_rows):
            self.drivers_table.setItem(i, 0, QtWidgets.QTableWidgetItem(d["driverBone"]))
            self.drivers_table.setItem(i, 1, QtWidgets.QTableWidgetItem(d["driverAxis"]))
            self.drivers_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(k["driverValue"])))
            rd = k["rootDelta"]
            self.drivers_table.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{rd['rotX']}, {rd['rotY']}, {rd['rotZ']}"))
        self.drivers_table.itemChanged.connect(self._on_table_edited)

    def _on_table_edited(self, item):
        # Update model from edited cell
        # This is intentionally simple — for production, swap to a proper QAbstractTableModel
        pass  # Skipping full bidirectional binding for Phase 1 MVP; rely on JSON edit if needed
```

Note: full bidirectional editing of the table is a lot of plumbing. For Phase 1 MVP, the table is mostly read-display + add/remove keys; if an animator wants to nudge a specific curve value, they can also edit the JSON directly. Phase 2 cleans up the UI.

- [ ] **[HUMAN] Step 6.3.3: Update _on_attachment_selected to refresh drivers**

Add to end of `_on_attachment_selected`:

```python
        has_overrides = "driverOverrides" in att
        self.use_default_drivers_check.setChecked(not has_overrides)
        self.drivers_widget.setVisible(has_overrides)
        self._refresh_drivers_table()
```

- [ ] **[HUMAN] Step 6.3.4: Add validation on save**

Modify `_on_save` to validate before writing:

```python
    def _on_save(self):
        if not self.preset.get("id"):
            QtWidgets.QMessageBox.warning(self, "Missing ID", "Set a Character ID before saving.")
            return
        # Validate via the resolver/validator
        try:
            from sp_cloth.config.loader import load_character
            # Write to a temp file, validate, then commit
            import tempfile, os
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
                json.dump(self.preset, tmp, indent=2)
                tmp_path = tmp.name
            try:
                load_character(Path(tmp_path), self.configs_dir / "body_types", self.configs_dir / "cloth_materials.json")
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Validation Error", str(e))
            return

        if not self.current_path:
            default = self.configs_dir / "characters" / f"{self.preset['id']}.json"
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save character preset", str(default), "JSON (*.json)")
            if not path:
                return
            self.current_path = Path(path)
        with open(self.current_path, "w") as f:
            json.dump(self.preset, f, indent=2)
        QtWidgets.QMessageBox.information(self, "Saved", str(self.current_path))
```

- [ ] **[HUMAN] Step 6.3.5: Manual test**

1. Restart panel.
2. Load `TestCharacter.json`.
3. Select the skirt attachment, uncheck "Use body type defaults".
4. Click "Add Driver". A new row should appear in the drivers table with empty bone name.
5. Save → validation should reject (empty bone names? or monotonic curve already? Adjust depending on validator output).
6. Re-check "Use body type defaults". Save. → Should succeed (no overrides).

- [ ] **[HUMAN] Step 6.3.6: Commit**

```bash
git add src/sp_cloth/ui/driver_setup_panel.py
git commit -m "feat(ui): driver override editor + save-time validation"
```

### Task 6.4: "Preview on current frame" button

**Primary owner:** [HUMAN]
**Estimated time:** 30 min
**Files:**
- Modify: `sp-cloth/src/sp_cloth/ui/driver_setup_panel.py`

#### Steps

- [ ] **[HUMAN] Step 6.4.1: Add preview button to header**

Append to the header row in `_build_ui`:

```python
        self.preview_btn = QtWidgets.QPushButton("Preview on current frame")
        self.preview_btn.clicked.connect(self._on_preview_frame)
        header.addWidget(self.preview_btn)
```

- [ ] **[HUMAN] Step 6.4.2: Implement preview**

Add method:

```python
    def _on_preview_frame(self):
        from pymxs import runtime as rt
        from sp_cloth.config.loader import load_character
        from sp_cloth.maxio.bones import read_bone_rotations
        from sp_cloth.maxio.keyframes import write_root_rotation_keyframe
        from sp_cloth.autoroot.apply import apply_autoroot
        import tempfile, os

        if not self.preset.get("id") or not self.preset.get("extends"):
            QtWidgets.QMessageBox.warning(self, "Incomplete", "Set ID and body type first.")
            return

        # Write current preset to temp, load via resolver, run on current frame only
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(self.preset, tmp, indent=2)
            tmp_path = tmp.name
        try:
            resolved = load_character(
                Path(tmp_path),
                self.configs_dir / "body_types",
                self.configs_dir / "cloth_materials.json")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Validation Error", str(e))
            os.unlink(tmp_path)
            return
        os.unlink(tmp_path)

        f = int(rt.sliderTime)
        apply_autoroot(resolved, f, f, read_bone_rotations, write_root_rotation_keyframe)
        rt.redrawViews()
```

- [ ] **[HUMAN] Step 6.4.3: Manual test**

1. Open a character scene + load a character preset in the panel.
2. Scrub to a frame where the thigh is rotated (e.g., a kick frame).
3. Click "Preview on current frame".
4. The skirt root should rotate per the curve.
5. Scrub away, scrub back — the keyframe should still be there.

- [ ] **[HUMAN] Step 6.4.4: Commit**

```bash
git add src/sp_cloth/ui/driver_setup_panel.py
git commit -m "feat(ui): preview-on-current-frame button for live iteration"
```

### **[HANDOFF] Stage 6 → Stage 7**

- [ ] **[HUMAN]** Panel works: load/save, attachment editor, driver overrides, preview.
- [ ] Next: batch cloth sim runner. Most of this is [HUMAN] (cloth modifier work in 3dsmax). The folder-driver wrapper (Task 7.3) is [AGENT].

---

## Stage 7 — Batch Cloth Sim Runner

**Owner:** Mixed. 7.1, 7.2 [HUMAN] (cloth modifier work). 7.3 [AGENT] (folder driver).
**Goal:** Process a folder of FBXs (Auto-Root output) through 3dsmax cloth sim with per-character config. Emit a QA report.
**Exit criteria:** `tools/run_batch.py` on a folder produces baked FBXs + `batch_report.json`.

### Task 7.1: Single-FBX cloth sim scaffold

**Primary owner:** [HUMAN]
**Estimated time:** 60 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/batch/__init__.py`
- Create: `sp-cloth/src/sp_cloth/batch/cloth_sim.py`
- Create: `sp-cloth/tools/run_cloth_sim_single.py`

#### Steps

- [ ] **[HUMAN] Step 7.1.1: Create batch subpackage**

```bash
mkdir -p src/sp_cloth/batch
touch src/sp_cloth/batch/__init__.py
```

- [ ] **[HUMAN] Step 7.1.2: Write the per-FBX scaffold**

Create `src/sp_cloth/batch/cloth_sim.py`:

```python
"""Per-FBX cloth sim processor. Most function bodies filled in Task 7.2 after
verifying the cloth modifier API in 3dsmax."""

def process_single_fbx(input_fbx: str, output_fbx: str, resolved_config: dict) -> dict:
    """Open input_fbx in 3dsmax, set up cloth modifier from resolved_config, simulate,
    bake to bones, export output_fbx. Return QA stats dict.

    Stats dict shape: {'attachments_processed': int, 'anomalies': list[dict]}
    """
    from pymxs import runtime as rt

    rt.resetMaxFile(rt.Name("noPrompt"))
    rt.importFile(input_fbx, rt.Name("noPrompt"))

    stats = {"attachments_processed": 0, "anomalies": []}
    for att in resolved_config["attachments"]:
        if att.get("clothSim") is None:
            continue
        _apply_cloth_modifier(att, rt)
        stats["attachments_processed"] += 1

    _wire_capsule_collisions(resolved_config, rt)
    _simulate_cloth(rt)
    _bake_cloth_to_bones(resolved_config, rt)
    stats["anomalies"] = _qa_check(resolved_config, rt)

    rt.exportFile(output_fbx, rt.Name("noPrompt"))
    return stats

def _apply_cloth_modifier(att, rt):
    """Apply Cloth modifier with physics from att['clothSim']['physics']."""
    raise NotImplementedError("Filled in Task 7.2")

def _wire_capsule_collisions(resolved_config, rt):
    """Register all _collision_* primitives in scene as cloth collision objects."""
    raise NotImplementedError("Filled in Task 7.2")

def _simulate_cloth(rt):
    """Trigger cloth sim across animation range; block until done."""
    raise NotImplementedError("Filled in Task 7.2")

def _bake_cloth_to_bones(resolved_config, rt):
    """Bake cloth mesh deformation back to attachment child bones."""
    raise NotImplementedError("Filled in Task 7.2")

def _qa_check(resolved_config, rt) -> list:
    """Return list of anomaly dicts. Checks frame-to-frame rotation jumps for now."""
    thresholds = resolved_config["qaThresholds"]
    anomalies = []
    for att in resolved_config["attachments"]:
        root_node = rt.getNodeByName(att["rootBone"])
        if root_node is None:
            continue
        prev_rot = None
        for f in range(int(rt.animationRange.start), int(rt.animationRange.end) + 1):
            rt.sliderTime = f
            q = root_node.rotation
            euler = rt.quatToEuler2(q, order=1)
            cur_rot = (float(euler.x), float(euler.y), float(euler.z))
            if prev_rot is not None:
                jump = max(abs(cur_rot[i] - prev_rot[i]) for i in range(3))
                if jump > thresholds["maxRootRotationJumpDegrees"]:
                    anomalies.append({
                        "attachment": att["name"],
                        "frame": f,
                        "kind": "root_rotation_jump",
                        "value": round(jump, 2),
                        "threshold": thresholds["maxRootRotationJumpDegrees"],
                    })
            prev_rot = cur_rot
    return anomalies
```

- [ ] **[HUMAN] Step 7.1.3: Write the single-FBX entry point**

Create `tools/run_cloth_sim_single.py`:

```python
"""Run inside 3dsmax. Processes ONE FBX through cloth sim."""
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "src"))

from sp_cloth.config.loader import load_character
from sp_cloth.batch.cloth_sim import process_single_fbx

if len(sys.argv) < 3:
    print("Usage: run_cloth_sim_single.py <input.fbx> <output.fbx> [character_id]")
    sys.exit(1)
input_fbx = sys.argv[1]
output_fbx = sys.argv[2]
character_id = sys.argv[3] if len(sys.argv) > 3 else "TestCharacter"

resolved = load_character(
    repo / "configs" / "characters" / f"{character_id}.json",
    repo / "configs" / "body_types",
    repo / "configs" / "cloth_materials.json",
)
stats = process_single_fbx(input_fbx, output_fbx, resolved)
print("Stats:", stats)
```

- [ ] **[HUMAN] Step 7.1.4: Commit (scaffold only — tasks 7.2 fills in)**

```bash
git add src/sp_cloth/batch/ tools/run_cloth_sim_single.py
git commit -m "feat(batch): single-FBX cloth sim scaffold (helpers stubbed)"
```

### Task 7.2: Fill in cloth sim helpers

**Primary owner:** [HUMAN]
**Estimated time:** 2–4 hours (depends on familiarity with 3dsmax Cloth modifier API)
**Files:**
- Modify: `sp-cloth/src/sp_cloth/batch/cloth_sim.py`

> **Strategy:** rather than guessing pymxs APIs blindly, do this work iteratively in the Listener — set up cloth manually on a test object once, then translate each step into pymxs. Reference your team's existing manual cloth setup as ground truth.

#### Steps

- [ ] **[HUMAN] Step 7.2.1: Verify your team's existing cloth modifier setup**

Open one of your characters with a hand-set-up working cloth modifier. Document the exact settings:
- Cloth modifier params (stiffness, bend, damping, ...) and how they map from your material library
- Which subobject groups define cloth, locked, etc.
- Collision object setup
- Simulation params

Write this in `notes/cloth_modifier_setup.md`.

- [ ] **[HUMAN] Step 7.2.2: Implement `_apply_cloth_modifier`**

Replace the `raise NotImplementedError` body with:

```python
def _apply_cloth_modifier(att, rt):
    """Apply Cloth modifier with physics from att['clothSim']['physics']."""
    physics = att["clothSim"]["physics"]

    # Find the skirt mesh — by convention, mesh name matches rootBone with suffix
    # Adjust per your project's naming
    cloth_mesh_name = att.get("clothMeshName", att["name"])  # may need to add this field to attachment schema
    mesh = rt.getNodeByName(cloth_mesh_name)
    if mesh is None:
        raise ValueError(f"Cloth mesh not found: {cloth_mesh_name}")

    cloth = rt.Cloth()
    rt.addModifier(mesh, cloth)

    # Map physics to Cloth properties (exact prop names verified per your version)
    cloth.U_Stretch = physics["stiffness"] * 100   # or whatever the scale needs to be
    cloth.U_Bend = physics["bend"] * 100
    cloth.damping = physics["damping"]
    cloth.airDamping = physics["airResistance"]
    cloth.density = physics["mass"]
    # ... more fields per your manual setup ...
```

Note: you may need to extend the JSON schema to include `clothMeshName` per attachment. If so, update:
- The schema example in `plan/2026-05-17-design.md`
- The types in `src/sp_cloth/config/types.py`
- The UI panel in Task 6.2

If you make schema changes, write `clothMeshName` into existing character JSONs by hand, then re-run validation tests.

- [ ] **[HUMAN] Step 7.2.3: Implement `_wire_capsule_collisions`**

```python
def _wire_capsule_collisions(resolved_config, rt):
    """Register all _collision_* primitives in scene as cloth collision objects."""
    # Find all capsule primitives we generated (named _collision_<bone>)
    collision_nodes = [n for n in rt.objects if n.name.startswith("_collision_")]
    # For each cloth modifier in the scene, add these as collision objects
    for node in rt.objects:
        for mod in node.modifiers:
            if rt.classOf(mod) == rt.Cloth:
                for col in collision_nodes:
                    # exact API: cloth modifier's collision object list
                    # Often: rt.Cloth.AddCollisionObject(mod, col)
                    rt.execute(f'$.modifiers[#Cloth].AddObject {col.name} true')
                    # ... or rt.cloth.addCollisionObject(mod, col) — version-dependent
```

The execute() string-MaxScript fallback is shown above; switch to direct pymxs once you find the right call.

- [ ] **[HUMAN] Step 7.2.4: Implement `_simulate_cloth`**

```python
def _simulate_cloth(rt):
    """Trigger cloth sim across animation range; block until done."""
    # Find first cloth modifier (one per scene for typical setup; if multiple, loop)
    for node in rt.objects:
        for mod in node.modifiers:
            if rt.classOf(mod) == rt.Cloth:
                # Reset any cached sim
                rt.execute('$.modifiers[#Cloth].resetState()')
                # Run sim
                rt.execute('$.modifiers[#Cloth].simulate()')
                # If sim is async in your version, you may need to poll
                # until rt.cloth.isSimulating(mod) == False
                return
```

- [ ] **[HUMAN] Step 7.2.5: Implement `_bake_cloth_to_bones`**

This depends heavily on your team's bake-to-bones technique. If you use Skin Wrap:

```python
def _bake_cloth_to_bones(resolved_config, rt):
    """Bake cloth mesh deformation back to attachment child bones via Skin Wrap."""
    for att in resolved_config["attachments"]:
        if att.get("clothSim") is None:
            continue
        # 1. Find the skirt child bones (children of rootBone in hierarchy)
        root = rt.getNodeByName(att["rootBone"])
        if root is None:
            continue
        children = list(root.children)  # may need to recurse
        # 2. For each bone, fit a Point primitive to the cloth mesh's nearest vertex group
        #    or use your existing skin-wrap bake pipeline
        # 3. Bake each bone's animation curve from the cloth-driven position
        #    via your existing tooling
        rt.execute('-- TODO: invoke your project bake-to-bones script here')
```

If your bake-to-bones is an existing MaxScript function (e.g., `_bakeSkinWrapToBones`), call it via `rt.execute('...')` or wrap it as a pymxs function.

- [ ] **[HUMAN] Step 7.2.6: Test end-to-end on the test character**

1. Open `biped_test.max` with the test character's skirt mesh + skin.
2. Run Auto-Root via `tools/run_autoroot.py`.
3. Run cloth sim via:
   ```python
   # In 3dsmax Listener
   import sys; sys.path.insert(0, str(repo / "tools"))
   # then... call run_cloth_sim_single.py with the test FBX paths
   ```
4. Verify the output FBX has baked skirt-bone animation curves.

- [ ] **[HUMAN] Step 7.2.7: Iterate until the output looks right**

Most likely issues:
- Cloth params don't map cleanly between your material library and the Cloth modifier — adjust the multiplication factors in `_apply_cloth_modifier`.
- Collision objects aren't being added correctly — check via the Cloth modifier UI after sim setup to confirm.
- Bake produces empty bone curves — likely your team's bake script needs to be invoked differently.

Document everything in `notes/cloth_modifier_setup.md`.

- [ ] **[HUMAN] Step 7.2.8: Commit**

```bash
git add src/sp_cloth/batch/cloth_sim.py notes/cloth_modifier_setup.md
git commit -m "feat(batch): implement cloth sim helpers (apply, collide, simulate, bake, qa)"
```

### Task 7.3: Folder batch driver

**Primary owner:** [AGENT]
**Estimated time:** 20 min
**Files:**
- Create: `sp-cloth/src/sp_cloth/batch/runner.py`
- Create: `sp-cloth/tools/run_batch.py`
- Create: `sp-cloth/tests/test_batch_runner.py`

#### Steps

- [ ] **[AGENT] Step 7.3.1: Write failing test with mocked processor**

Create `tests/test_batch_runner.py`:

```python
from pathlib import Path
from sp_cloth.batch.runner import run_batch

def test_runner_aggregates_results(tmp_path):
    fixtures = Path(__file__).parent / "fixtures" / "loader"
    in_dir = tmp_path / "in"; out_dir = tmp_path / "out"
    in_dir.mkdir()
    (in_dir / "a.fbx").touch()
    (in_dir / "b.fbx").touch()

    def fake_processor(inp, outp, resolved):
        return {"attachments_processed": 1,
                "anomalies": [] if "a" in inp else [{"frame": 5}]}

    char_path = tmp_path / "TestChar.json"
    char_path.write_text('{"id":"X","extends":"AdultMale","attachments":[]}')
    report = run_batch(in_dir, out_dir, char_path,
                       fixtures / "body_types", fixtures / "cloth_materials.json",
                       fake_processor)
    assert len(report["items"]) == 2
    assert report["items"][0]["status"] == "ok"
    assert report["items"][1]["status"] == "flagged"
    assert (out_dir / "batch_report.json").exists()

def test_runner_records_failed_when_processor_raises(tmp_path):
    fixtures = Path(__file__).parent / "fixtures" / "loader"
    in_dir = tmp_path / "in"; out_dir = tmp_path / "out"
    in_dir.mkdir()
    (in_dir / "a.fbx").touch()

    def boom(*args):
        raise RuntimeError("simulated failure")

    char_path = tmp_path / "X.json"
    char_path.write_text('{"id":"X","extends":"AdultMale","attachments":[]}')
    report = run_batch(in_dir, out_dir, char_path,
                       fixtures / "body_types", fixtures / "cloth_materials.json",
                       boom)
    assert report["items"][0]["status"] == "failed"
    assert "simulated failure" in report["items"][0]["stats"]["error"]
```

- [ ] **[AGENT] Step 7.3.2: Run — verify fails**

- [ ] **[AGENT] Step 7.3.3: Implement**

Create `src/sp_cloth/batch/runner.py`:

```python
"""Batch driver: process a folder of FBXs through a processor function.
Aggregates per-FBX stats into a JSON report."""
import json
from pathlib import Path
from sp_cloth.config.loader import load_character


def run_batch(input_dir, output_dir, character_config_path,
              body_types_dir, materials_path, processor) -> dict:
    """Process every .fbx in input_dir through `processor`. Aggregate QA stats."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    resolved = load_character(character_config_path, body_types_dir, materials_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {"character": resolved["id"], "items": []}
    for fbx_path in sorted(input_dir.glob("*.fbx")):
        out_path = output_dir / f"{fbx_path.stem}_baked.fbx"
        try:
            stats = processor(str(fbx_path), str(out_path), resolved)
            status = "ok" if not stats.get("anomalies") else "flagged"
        except Exception as e:
            stats = {"error": str(e)}
            status = "failed"
        report["items"].append({"input": fbx_path.name, "status": status, "stats": stats})

    report_path = output_dir / "batch_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    return report
```

- [ ] **[AGENT] Step 7.3.4: Run — verify pass**

```bash
pytest tests/test_batch_runner.py -v
```
Expected: 2 passed.

- [ ] **[AGENT] Step 7.3.5: Write the 3dsmax entry point**

Create `tools/run_batch.py`:

```python
"""Run inside 3dsmax. Processes a folder of FBXs through cloth sim with QA report."""
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "src"))

from sp_cloth.batch.runner import run_batch
from sp_cloth.batch.cloth_sim import process_single_fbx

if len(sys.argv) < 4:
    print("Usage: run_batch.py <input_dir> <output_dir> <character_id>")
    sys.exit(1)

input_dir, output_dir, character_id = sys.argv[1:4]
character_path = repo / "configs" / "characters" / f"{character_id}.json"
report = run_batch(
    Path(input_dir), Path(output_dir), character_path,
    repo / "configs" / "body_types", repo / "configs" / "cloth_materials.json",
    process_single_fbx,
)
ok = sum(1 for i in report["items"] if i["status"] == "ok")
flagged = sum(1 for i in report["items"] if i["status"] == "flagged")
failed = sum(1 for i in report["items"] if i["status"] == "failed")
print(f"Batch complete: {ok} ok, {flagged} flagged, {failed} failed.")
print(f"Report: {Path(output_dir) / 'batch_report.json'}")
```

- [ ] **[AGENT] Step 7.3.6: Commit**

```bash
git add src/sp_cloth/batch/runner.py tools/run_batch.py tests/test_batch_runner.py
git commit -m "feat(batch): folder-of-FBX runner with aggregated JSON report"
```

### **[HANDOFF] Stage 7 → Stage 8**

- [ ] **[HUMAN]** End-to-end batch run succeeds on the test character.
- [ ] **[HUMAN]** Now the pipeline is in place. Stage 8 = run it on real production characters and iterate.

---

## Stage 8 — Pilot run on real characters

**Owner:** [HUMAN]
**Goal:** Phase 1 exit. Run the full pipeline on 5 real AdultMale characters with ~50 total animations. Iterate driver curves + materials. Confirm visual quality.
**Exit criteria:** All 5 pilot characters baked end-to-end. Visual review PASS against current manual pipeline. `phase1-complete` git tag.

### Task 8.1: Set up the pilot character #1

**Primary owner:** [HUMAN]
**Estimated time:** 60–90 min
**Files:**
- Create: `sp-cloth/configs/characters/<PilotCharId>.json` (via Driver Setup panel)
- Create: `sp-cloth/notes/phase1_pilot.md`

#### Steps

- [ ] **[HUMAN] Step 8.1.1: Pick pilot character #1**

Criteria: extends `AdultMale`, has a skirt (most common case), has ~10 animations covering varied poses (idle, walk, run, jump, crouch).

- [ ] **[HUMAN] Step 8.1.2: Open the character's master scene**

Load it in 3dsmax. Open the Driver Setup panel.

- [ ] **[HUMAN] Step 8.1.3: Create the character preset via the panel**

1. New preset: Character ID = `AdultMale_<Name>`, body type = `AdultMale`.
2. Add "skirt" attachment, pick its root bone from viewport (pick the actual `Bip_Skirt_Root` in this character's rig).
3. Pick material (probably `soft_pleated_cotton` or similar).
4. Leave drivers as "Use body type defaults" for now — overrides come later if needed.
5. Save.

- [ ] **[HUMAN] Step 8.1.4: Generate collision capsules**

1. Edit `tools/run_capsule_generator.py` — set `MESH_NODE` to this character's body mesh name and `CHARACTER_PATH` to the new preset.
2. Run the script.
3. Visually verify capsules look right.

- [ ] **[HUMAN] Step 8.1.5: Document the pilot**

Create `sp-cloth/notes/phase1_pilot.md`:

```markdown
# Phase 1 Pilot Log

## Character #1: AdultMale_<Name>
- Skirt material: ...
- Animations selected: 1. ..., 2. ..., 3. ..., ...
- Capsule generation: PASS / FAIL — notes ...
- Driver overrides used: none / list
- Issues found: ...
```

- [ ] **[HUMAN] Step 8.1.6: Commit**

```bash
git add configs/characters/AdultMale_<Name>.json notes/phase1_pilot.md
git commit -m "feat(pilot): set up AdultMale_<Name> as pilot character #1"
```

### Task 8.2: Run the full pipeline on pilot character #1

**Primary owner:** [HUMAN]
**Estimated time:** 60–120 min (mostly batch waiting)
**Files:**
- Create: `sp-cloth/notes/phase1_pilot_results.md`

#### Steps

- [ ] **[HUMAN] Step 8.2.1: For each of ~10 pilot animations, run Auto-Root**

For each animation:
1. Open the animation .max file.
2. Run `tools/run_autoroot.py` (uses TestCharacter — temporarily edit to use the pilot character path).
3. Export the auto-rooted result as FBX into a dedicated folder, e.g., `pilot1_autorooted/`.

(Tedious step — you can write a small "open all .max files in a folder and apply auto-root then export" wrapper script if useful.)

- [ ] **[HUMAN] Step 8.2.2: Run the batch cloth sim runner**

In a 3dsmax Python prompt or via batch invocation:

```bash
# Adjust paths
3dsmax -silent -U PythonHost run_batch.py /path/to/pilot1_autorooted/ /path/to/pilot1_baked/ AdultMale_<Name>
```

(Or interactive: open 3dsmax, run `tools/run_batch.py` with the args.)

Wait for completion. Note wall-clock time.

- [ ] **[HUMAN] Step 8.2.3: Open the batch report**

```bash
cat /path/to/pilot1_baked/batch_report.json
```

For each item:
- `ok` — proceed to visual review.
- `flagged` — anomalies listed; open the input FBX and inspect those frames.
- `failed` — error in stats; debug.

- [ ] **[HUMAN] Step 8.2.4: Visual review**

Import all 10 baked FBXs into UE, alongside the manually-authored existing versions of the same animations.

For each animation, side-by-side:
- Mesh clipping: any frame where skirt mesh visibly intersects the body?
- Cloth motion: does it look equivalent to or better than the manual version?
- Discontinuities: any frame-to-frame jumps?

Record PASS/FAIL with notes per animation in `sp-cloth/notes/phase1_pilot_results.md`.

- [ ] **[HUMAN] Step 8.2.5: Commit**

```bash
git add notes/phase1_pilot_results.md
git commit -m "docs(pilot): pilot #1 visual review results"
```

### Task 8.3: Iterate on drivers and materials

**Primary owner:** [HUMAN]
**Estimated time:** Variable (1–8 hours depending on how many things need tuning)
**Files:**
- Modify: `sp-cloth/configs/body_types/AdultMale.json`
- Modify: `sp-cloth/configs/cloth_materials.json` (if needed)

#### Steps

- [ ] **[HUMAN] Step 8.3.1: For each visual failure, classify the cause**

| Failure pattern | Tune this |
|---|---|
| Skirt clips into thigh during high knee lift | Skirt driver curve too weak at -90° on LeftUpLeg/RightUpLeg → increase `rootDelta.rotX` |
| Skirt over-rotates and looks unnatural | Reduce curve magnitudes or lower `maxRotationDegrees` |
| Skirt jitters frame-to-frame | Increase `temporalSmoothingFrames` |
| Cloth folds wrong (too stiff / too floppy) | Tune cloth material physics, not driver |
| Cloth penetrates body persistently | Capsule scale too small → increase `scaleFactor` in collision sets |

- [ ] **[HUMAN] Step 8.3.2: Make ONE change at a time**

Edit one knob, re-run auto-root + cloth sim for ONE animation, visual review. Tight loop.

- [ ] **[HUMAN] Step 8.3.3: Commit each iteration with a clear message**

```bash
git commit -m "tune(AdultMale): bump skirt response at -60° thigh angle to fix knee-lift clipping"
```

- [ ] **[HUMAN] Step 8.3.4: Re-run the full 10-animation batch**

Once you've tuned enough that single-animation tests pass, re-run all 10 to confirm overall PASS. Document final state in `phase1_pilot_results.md`.

### Task 8.4: Set up + run 4 more pilot characters

**Primary owner:** [HUMAN]
**Estimated time:** 4–8 hours total

#### Steps

- [ ] **[HUMAN] Step 8.4.1: Pick 4 more characters**

All extending AdultMale. Aim for variety in body proportions to surface cases where the body type defaults aren't sufficient. If you have any visibly heavier/lighter AdultMale variants, prioritize those — they're the most likely to need character-specific driver overrides.

- [ ] **[HUMAN] Step 8.4.2: For each character, run Tasks 8.1 + 8.2**

You're doing it 4 more times. Should go faster now that you know the workflow. Most characters should need ZERO driver overrides — body type defaults handle them. Note which ones DO need overrides; that's signal for what to fix in the body type defaults vs accept as per-character variance.

- [ ] **[HUMAN] Step 8.4.3: Compare across the 5 characters**

In `phase1_pilot_results.md`, write a summary section:
- How many characters needed zero overrides?
- For those that needed overrides, what was the pattern? Heavier body? Different skirt length?
- Is the AdultMale body type "good enough" or does the experience suggest splitting into AdultMale_Heavyset and AdultMale_Lean (Phase 2 work)?

- [ ] **[HUMAN] Step 8.4.4: Final exit criteria check**

Verify against Phase 1 exit criteria from the spec:

- [ ] 1 body type fully authored: YES (AdultMale with all 4 attachment types)
- [ ] 5 characters set up via the UI panel: YES
- [ ] ~50 animations batched end-to-end: YES (~10 per character × 5 = 50)
- [ ] Zero per-animation human touch (excluding flagged QA items): YES / NO + notes
- [ ] Visual quality matches manual pipeline on hand-picked review set: YES / NO + notes

- [ ] **[HUMAN] Step 8.4.5: Commit + tag**

```bash
git add notes/phase1_pilot_results.md configs/characters/
git commit -m "feat(phase1): pilot complete — 5 characters, ~50 animations, end-to-end"
git tag phase1-complete
```

### **[HANDOFF] Stage 8 → Phase 2**

- [ ] **[HUMAN]** Phase 1 done. Tag committed.
- Phase 2 starts: remaining 7 body types, parallelism, QA dashboard UI, preset validation tool. Plan that separately when you're ready.

---

## Self-Review

Coverage of spec sections vs plan tasks:

| Spec section | Plan coverage |
|---|---|
| Material library | Task 2.1 |
| Body type templates (Phase 1: 1 of 8) | Tasks 2.2 + 4.4 |
| Character preset + inheritance | Tasks 1.2, 1.3, 1.4 + 6.1, 6.2 |
| Auto-Root curve evaluator | Tasks 3.1, 3.2, 3.3 |
| Auto-Root orchestrator | Task 3.4 |
| Auto-Root 3dsmax integration | Tasks 4.1, 4.2, 4.3 |
| Driver Setup panel | Tasks 6.1, 6.2, 6.3, 6.4 |
| Capsule Auto-Generator | Tasks 5.1, 5.2 |
| Batch Cloth Sim Runner | Tasks 7.1, 7.2, 7.3 |
| QA report | `_qa_check` in 7.1 + aggregator in 7.3 |
| Validation | Task 1.3 + save-time check in 6.3 |
| End-to-end pilot | Tasks 8.1, 8.2, 8.3, 8.4 |
| Risks (Reaction Manager fit, headless licensing) | Stage 0 spikes |

Open spec questions still unresolved at plan time:
- (1) MaxScript vs Python-in-Max — committed to Python-in-Max throughout this plan.
- (2) Preset storage location — committed to `sp-cloth/configs/`.
- (3) Specific 8 body types — Phase 1 only authors `AdultMale`; remaining 7 are Phase 2.
- (4, 5) Reaction Manager fidelity + headless licensing — handled by Stage 0 spikes.

---

*End of Phase 1 implementation plan.*
