# MotionKit — 3ds Max Tools Reference

---

## Animation Tools

### Biped Axis Cleaner
`max/tools/animation/biped_axis_cleaner.py`

Linearizes pelvis movement on a per-axis basis. Instead of forcing a straight path, it creates a visible Dummy helper that represents the 100% linearized target, then lets you blend each axis (X, Y, Z) independently between 0 (original motion) and 100 (fully linear).

**Workflow:**
1. Auto-detect or pick the Biped pelvis node.
2. Click **Create Helper** — a cyan Dummy appears showing the fully linearized path.
3. Set axis blend weights (e.g. Y=100 to straighten forward movement, X=0 to keep lateral sway).
4. Click **Apply to Pelvis**.

Non-destructive: the original pelvis positions are snapshotted to a hidden backup Dummy on first Apply. Re-applying with different weights always blends from the original, not the last applied result.

---

### Bone Speed Calculator
`max/tools/animation/bone_speed_calculator.py` + `BoneSpeedCalculator.ms`

Live speed readout for any scene object on selectable axes. Calculates velocity in **m/s** by sampling world-space positions at adjacent frames.

**Features:**
- Axis toggles (X, Y, Z) — enable only the axes you care about.
- Auto-Update mode: reads speed continuously as you scrub the timeline.
- **Curve Preview** — generates a visible Point helper trajectory for one of three modes:
  - *Movement Path (Root Loc)* — keys the helper at the bone's exact world position each frame.
  - *Turning / Rotation (Root Rot)* — plots accumulated yaw (in degrees) as a 2D graph, unwrapped to avoid sawtooth artifacts.
  - *Movement Speed (Root Vec)* — plots per-frame speed magnitude as a 2D graph.

---

### Build Retarget Map
`max/tools/animation/build_retarget_map.py`

Scans a scene that contains both a Biped and an export skeleton (e.g. bones driven by the Biped), then auto-generates a bone name mapping preset for the FBX Retarget tool.

**Workflow:**
1. Open a character Max file with both Biped and export skeleton in scene.
2. Click **Analyze** — the tool finds all Biped nodes, matches each to the nearest non-Biped bone by world-space position (within a 0.5 unit tolerance).
3. Review the mapping in the listbox. Unmatched slots are shown explicitly.
4. Enter a preset name and click **Save** — writes `presets/retarget/<name>.json`.

Preferentially reads from an "Fbx" named selection set if one exists; falls back to scanning all non-Biped bone-like nodes.

---

### Extract Animation Trajectory
`max/tools/animation/extract_trajectory.py`

Bakes any object's animation into a standalone Dummy helper for a given frame range. Useful for sharing motion paths between objects or preserving animation data before destructive edits.

**Modes:**
- *World Space* — bakes the object's world-space position/rotation directly.
- *Relative to Object* — bakes the transform relative to a reference object (e.g. root motion relative to a vehicle).

**Features:**
- Toggle Position and Rotation independently.
- Optional trajectory preview spline (orange) drawn before baking.
- Trajectory Manager panel lists all existing trajectory helpers in the scene, with Re-Bake and Delete controls. Re-Bake uses metadata stored on the helper to redo the bake without re-entering settings.

---

### FBX Exporter
`max/tools/animation/fbx_exporter.py`

Exports animation to FBX with control over frame range and object selection. Integrates with Perforce: if the output file already exists in a P4 workspace, it automatically runs `p4 edit` before writing.

**Options:**
- Custom frame range or use timeline range.
- Selected objects only or full scene.
- FBX export path configurable via Settings.

---

### FBX Retarget to Biped
`max/tools/animation/fbx_retarget.py`

Imports FBX bone animation and retargets it onto a 3ds Max Biped using a proxy-bone ASCII FBX round-trip. This approach bypasses `biped.setTransform` limitations by letting Max's native FBX importer write animation onto Biped controllers through its internal C++ path.

**Process:**
1. Import source FBX in merge mode.
2. Create Point helper proxies, constrain to source bones (position + orientation).
3. Two-pass bake: sample constrained transforms, then strip constraints and write clean keys.
4. Export proxies as ASCII FBX.
5. Strip the proxy name prefix from the ASCII text.
6. Re-import the modified FBX — Max writes the animation onto the Biped.
7. Clean up proxies and imported source nodes.

**UI Controls:**
- Browse a folder for FBX files; pick which file to retarget.
- Dropdown selects which Biped in the scene receives the animation.
- Bone mapping listbox shows slot-to-bone assignments. Load/save presets as JSON.
- Auto-detection matches FBX bone names to standard slots using name patterns and namespace stripping.
- Optional cleanup of imported source nodes after retarget.

Saves a `.bip` backup before touching the Biped; restores it on failure.

---

### Foot Slide Fixer
`max/tools/animation/foot_slide_fixer.py`

Detects and corrects foot sliding in Biped animations by locking feet during plant phases.

**Detection:** Frames where foot velocity (3-frame median-filtered) is below the threshold **and** the foot is within `height tolerance` of the ground minimum are classified as plant frames. Contiguous groups of 3+ frames become plant segments.

**Fix pipeline:**
1. *Compute* — builds per-frame XY correction array. Plant frames: full lock. Pre-plant: ramp from 0→1 approaching heel-strike. Post-plant: fade the fixed offset (not a pull-back force, so toe-off is not opposed).
2. *Clamp* — scales back any correction that would place the foot beyond 97% of its original 3D pelvis reach, preventing IK pop.
3. *Apply* — writes corrected XY keys frame-by-frame, re-reading the current position each frame to account for Biped curve fitting shifting earlier keys.
4. *Compensate pelvis* (optional) — lowers pelvis Z to maintain leg length where XY corrections reduce horizontal reach. Correction is smoothed with a 5-frame moving average before writing.

---

### Generate Foot Sync
`max/tools/animation/foot_sync.py`

Analyzes Biped foot animation and generates sync group data used by game engines. Creates animatable custom attributes `FootSpd_L` and `FootSpd_R` on the scene root node with step keyframes.

**Sync group values:** 0 = ground contact, 1 = lifting off, 2 = in air.

**Detection:** For each frame, classifies foot state based on Z height relative to the neutral threshold and per-frame movement speed. Undetermined frames inherit from neighbors. State-change frames become keyframes.

**Character Presets:** Loaded from `config/foot_sync_presets.json`. Each preset defines foot/toe height ranges (min, neutral, max), velocity thresholds, and motion range. Copy `foot_sync_presets.example.json` to add custom characters. Presets are validated on load; invalid ones are skipped with an error in the log.

---

### Root Animation Copy
`max/tools/animation/root_anim_copy.py`

Copies position and/or rotation from the Biped pelvis to a custom `root` bone, frame by frame. Used when the export skeleton has its own root bone that needs to carry the world-space motion.

**Options:**
- Toggle each position axis (X, Y, Z) independently.
- Optionally copy Z rotation.
- Height offset: applies a Z offset to correct for differences in pivot height between the Biped pelvis and the root bone. A helper button calculates the offset automatically from a two-object selection.
- Frame range: use timeline or pick start/end from the slider.

Pressing Esc during the loop cancels the copy and reports the last processed frame.

---

### Calibrate Foot Sync Parameters
`max/tools/animation/_calibrate_foot_sync.py`

Analyzes a walk or run cycle to measure optimal parameters for the Generate Foot Sync tool, removing the need to tune values manually per character.

**Measurements taken:**
- Foot and toe height statistics (min, 10th percentile, 90th percentile, max).
- Per-frame velocity (min, max, median, average, 25th/75th percentile).
- Angular velocity between toe and foot nodes (median, 90th percentile).

Derived recommendations cover all parameters in the foot sync preset schema: height ranges, thresholds, motion range, height tolerance.

Results are displayed in a text box and can be exported to JSON for pasting into `foot_sync_presets.json`.

---

## Cloth Tools (sp-cloth Pipeline)

These four tools form the sp-cloth pipeline for automated secondary cloth simulation. All are currently **Phase 1 stubs** — opening them shows a status panel describing the planned behavior.

### sp-cloth: Driver Setup
`max/tools/cloth/driver_setup.py`

Visual panel for authoring per-character cloth attachment configurations. Pick attachment root bones from the viewport, author driver response curves (e.g. thigh angle → skirt root rotation), choose cloth materials, and preview the result on the current frame. Saves a preset JSON consumed by Auto-Root and Batch Cloth Sim.

---

### sp-cloth: Auto-Root Current Animation
`max/tools/cloth/auto_root.py`

Reads the character preset for the current scene. For each cloth attachment (skirt, tail, long hair, sleeves): samples driver bone rotations across the animation range, evaluates response curves, sums multi-driver contributions (clamped to the attachment's max rotation), applies temporal smoothing, and writes keyframes to the attachment root bone.

---

### sp-cloth: Generate Collision Capsules
`max/tools/cloth/generate_capsules.py`

One-time setup tool. Reads the character preset and for each bone in each collision set, finds vertices skinned to that bone above a weight threshold, fits a bounding capsule via PCA (longest axis = capsule axis, perpendicular spread = radius), and creates capsule primitive objects parented to each bone. The capsules are named `_collision_<bone>` and become collision targets for cloth simulation.

---

### sp-cloth: Batch Cloth Sim
`max/tools/cloth/batch_sim.py`

Batch processor for a folder of auto-rooted FBXs. For each file: opens the FBX, applies the character's cloth modifier with material physics, wires up collision capsules, simulates, bakes cloth deformation back to attachment child bones, exports a baked FBX, and runs QA checks (frame-to-frame discontinuity, vertex velocity, self-intersection). Writes `batch_report.json` summarizing ok / flagged / failed items.

---

## Pipeline Tools

### Settings
`max/tools/pipeline/settings.py`

Configures MotionKit preferences. Changes persist to `config/config.json`.

**Sections:**
- *Language* — switch UI between English, Chinese (中文), and Korean (한국어). A restart message is shown if the language changes.
- *Perforce* — server address, username, and workspace. Load Workspaces queries `p4 clients` and populates a dropdown. Test Connection sets P4 environment variables and confirms the configuration.

---

## Unreal Engine Tools

### Max LiveLink
`max/tools/unrealengine/send_to_unreal.py`

Real-time socket connection from 3ds Max to an Unreal Engine LiveLink server. Uses a length-prefixed JSON protocol.

**Controls:**
- Configure host and port (default: `localhost:9999`).
- Connect / Disconnect buttons.
- Test Ping — sends a ping message and reports round-trip latency in ms.
- Query UE Selection — requests the list of currently selected actors in the UE viewport and displays their names and types.

Requires the companion `max_live_link_server.py` running inside Unreal Engine to accept connections.
