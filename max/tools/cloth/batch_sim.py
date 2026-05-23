"""
sp-cloth: Batch Cloth Sim for 3ds Max
Processes a folder of FBXs through cloth sim with per-character config + QA report.

Status: Phase 1 stub. See sp-cloth/plan/2026-05-17-phase1-implementation.md (Stage 7).
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[sp-cloth Batch Sim] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger

# Tool constant (required)
TOOL_NAME = "sp-cloth: Batch Cloth Sim..."

_STATUS_TEXT = """sp-cloth: Batch Cloth Sim

Part of the sp-cloth pipeline (in development).

What this tool will do:
- Prompt for input folder (auto-rooted FBXs) and output folder (baked FBXs).
- For each FBX in the input folder:
  * Open the FBX, load the character's resolved config.
  * Apply Cloth modifier with the preset's material physics.
  * Wire up body collision capsules (from the Capsule Generator stage).
  * Simulate.
  * Bake cloth deformation back to attachment child bones.
  * Export baked FBX.
  * Run QA checks (frame-to-frame discontinuity, vertex velocity, self-intersection).
- Write batch_report.json summarizing ok / flagged / failed items.
- Flagged FBXs surfaced for TD review; the rest go to the import pipeline.

Implementation tracked in:
  sp-cloth/plan/2026-05-17-phase1-implementation.md
Status: Phase 1 - Stage 7 (Batch Cloth Sim Runner)"""


def execute(control=None, event=None):
    """Main execution function called by menu system."""
    if not pymxs or not rt:
        print(f"[{TOOL_NAME}] ERROR: Not running in 3ds Max")
        return

    try:
        logger.info(f"{TOOL_NAME}: stub invocation (batch runner not yet implemented)")
        rt.messageBox(_STATUS_TEXT, title=f"MotionKit - {TOOL_NAME}")
    except Exception as e:
        logger.error(f"Failed to run {TOOL_NAME}: {str(e)}")
        rt.messageBox(f"Failed to run {TOOL_NAME}:\n{str(e)}", title="MotionKit Error")
