"""
sp-cloth: Generate Collision Capsules for 3ds Max
Auto-generates body collision capsules from skinning weights for cloth sim.

Status: Phase 1 stub. See sp-cloth/plan/2026-05-17-phase1-implementation.md (Stage 5).
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[sp-cloth Capsule Generator] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger

# Tool constant (required)
TOOL_NAME = "sp-cloth: Generate Collision Capsules"

_STATUS_TEXT = """sp-cloth: Generate Collision Capsules

Part of the sp-cloth pipeline (in development).

What this tool will do:
- Read the character preset for the currently loaded character.
- For each bone in each collision set (legs, hips, torso, shoulders):
  * Find vertices skinned to that bone above a weight threshold.
  * Fit a bounding capsule via PCA (longest axis = capsule axis, perpendicular spread = radius).
  * Apply the preset's scaleFactor (default 0.9x for body-hugging fit).
- Create capsule primitive objects parented to each bone, named _collision_<bone>.
- These capsules become the collision targets for cloth sim in the next stage.

Run once per character (or whenever the mesh changes).

Implementation tracked in:
  sp-cloth/plan/2026-05-17-phase1-implementation.md
Status: Phase 1 - Stage 5 (Capsule Auto-Generator)"""


def execute(control=None, event=None):
    """Main execution function called by menu system."""
    if not pymxs or not rt:
        print(f"[{TOOL_NAME}] ERROR: Not running in 3ds Max")
        return

    try:
        logger.info(f"{TOOL_NAME}: stub invocation (capsule gen not yet implemented)")
        rt.messageBox(_STATUS_TEXT, title=f"MotionKit - {TOOL_NAME}")
    except Exception as e:
        logger.error(f"Failed to run {TOOL_NAME}: {str(e)}")
        rt.messageBox(f"Failed to run {TOOL_NAME}:\n{str(e)}", title="MotionKit Error")
