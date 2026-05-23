"""
sp-cloth: Driver Setup for 3ds Max
Opens the visual panel for authoring per-character cloth attachment configurations.

Status: Phase 1 stub. See sp-cloth/plan/2026-05-17-phase1-implementation.md (Stage 6).
"""

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[sp-cloth Driver Setup] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.logger import logger

# Tool constant (required)
TOOL_NAME = "sp-cloth: Driver Setup"

_STATUS_TEXT = """sp-cloth: Driver Setup

Part of the sp-cloth pipeline (in development).

What this tool will do:
- Open a visual panel for authoring per-character cloth attachment configs.
- Pick attachment root bones from the viewport.
- Author driver response curves (thigh angle -> skirt root rotation, etc.).
- Choose cloth materials.
- Preview the auto-root result on the current frame.
- Save the preset as JSON for use by Auto-Root and Batch Cloth Sim.

Implementation tracked in:
  sp-cloth/plan/2026-05-17-phase1-implementation.md
Status: Phase 1 - Stage 6 (Driver Setup Panel)"""


def execute(control=None, event=None):
    """Main execution function called by menu system."""
    if not pymxs or not rt:
        print(f"[{TOOL_NAME}] ERROR: Not running in 3ds Max")
        return

    try:
        logger.info(f"{TOOL_NAME}: stub invocation (panel not yet implemented)")
        rt.messageBox(_STATUS_TEXT, title=f"MotionKit - {TOOL_NAME}")
    except Exception as e:
        logger.error(f"Failed to open {TOOL_NAME}: {str(e)}")
        rt.messageBox(f"Failed to open {TOOL_NAME}:\n{str(e)}", title="MotionKit Error")
