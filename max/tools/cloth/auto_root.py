"""
sp-cloth: Auto-Root Current Animation for 3ds Max
Applies driver-driven root keyframing to cloth attachments on the open animation.

Status: Phase 1 stub. See sp-cloth/plan/2026-05-17-phase1-implementation.md (Stage 4).
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[sp-cloth Auto-Root] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger

# Tool constant (required)
TOOL_NAME = "sp-cloth: Auto-Root Current Animation"

_STATUS_TEXT = """sp-cloth: Auto-Root Current Animation

Part of the sp-cloth pipeline (in development).

What this tool will do:
- Read the character preset for the currently loaded scene.
- For each cloth attachment (skirt, tail, long hair, sleeves):
  * Read driver bone rotations across the animation range.
  * Evaluate the authored response curves.
  * Sum multi-driver contributions and clamp to the attachment's max rotation.
  * Apply temporal smoothing.
  * Write keyframes to the attachment root bone.

Implementation tracked in:
  sp-cloth/plan/2026-05-17-phase1-implementation.md
Status: Phase 1 - Stage 4 (Auto-Root 3dsmax Integration)"""


def execute(control=None, event=None):
    """Main execution function called by menu system."""
    if not pymxs or not rt:
        print(f"[{TOOL_NAME}] ERROR: Not running in 3ds Max")
        return

    try:
        logger.info(f"{TOOL_NAME}: stub invocation (auto-root not yet implemented)")
        rt.messageBox(_STATUS_TEXT, title=f"MotionKit - {TOOL_NAME}")
    except Exception as e:
        logger.error(f"Failed to run {TOOL_NAME}: {str(e)}")
        rt.messageBox(f"Failed to run {TOOL_NAME}:\n{str(e)}", title="MotionKit Error")
