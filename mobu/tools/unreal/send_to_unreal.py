"""
Send to Unreal - Quick action tool
Send selected MotionBuilder objects directly to Unreal Engine
"""

from pyfbsdk import FBMessageBox, FBModelList
from core.logger import logger
from mobu.tools.unreal.live_link import get_live_link

TOOL_NAME = "Send to Unreal"


def execute(control, event):
    """Send currently selected objects to Unreal Engine"""
    logger.info("Send to Unreal - Checking selection...")

    try:
        live_link = get_live_link()

        # Check connection first
        if not live_link.is_connected():
            result = FBMessageBox(
                "Not Connected",
                "Not connected to Unreal Engine.\n\n"
                "Would you like to connect now?",
                "Connect", "Cancel"
            )

            if result == 1:  # Connect
                logger.info("Attempting to connect to Unreal Engine...")
                if not live_link.connect():
                    FBMessageBox(
                        "Connection Failed",
                        "Failed to connect to Unreal Engine.\n\n"
                        "Make sure:\n"
                        "1. Unreal Engine 5 is running\n"
                        "2. The receiver widget is started\n"
                        f"3. Port {live_link.port} is not blocked",
                        "OK"
                    )
                    return
                logger.info("Connected successfully")
            else:
                return

        # Get selected objects
        selected = FBModelList()
        from pyfbsdk import FBGetSelectedModels
        FBGetSelectedModels(selected)

        if len(selected) == 0:
            FBMessageBox(
                "No Selection",
                "No objects selected.\n\n"
                "Please select objects in the viewport to send to Unreal Engine.",
                "OK"
            )
            return

        # Show confirmation with object count
        # FBModelList doesn't support slice notation, use manual loop
        object_names = []
        max_display = min(5, len(selected))
        for i in range(max_display):
            object_names.append(selected[i].Name)

        if len(selected) > 5:
            object_list = "\n".join(f"  • {name}" for name in object_names)
            object_list += f"\n  • ... and {len(selected) - 5} more"
        else:
            object_list = "\n".join(f"  • {name}" for name in object_names)

        result = FBMessageBox(
            "Send to Unreal Engine",
            f"Send {len(selected)} object(s) to Unreal Engine?\n\n"
            f"{object_list}",
            "Send", "Cancel"
        )

        if result != 1:  # Cancelled
            logger.info("Send cancelled by user")
            return

        # Send objects
        logger.info(f"Sending {len(selected)} object(s) to Unreal Engine...")

        success_count = 0
        failed_objects = []

        for obj in selected:
            if live_link.send_object(obj):
                success_count += 1
                logger.info(f"  → Sent: {obj.Name}")
            else:
                failed_objects.append(obj.Name)
                logger.error(f"  ✗ Failed: {obj.Name}")

        # Show result
        if success_count == len(selected):
            # All successful
            FBMessageBox(
                "Success",
                f"Successfully sent all {len(selected)} object(s) to Unreal Engine!\n\n"
                "Check your UE5 viewport.",
                "OK"
            )
        elif success_count > 0:
            # Partial success
            failed_list = "\n".join(f"  • {name}" for name in failed_objects[:10])
            if len(failed_objects) > 10:
                failed_list += f"\n  • ... and {len(failed_objects) - 10} more"

            FBMessageBox(
                "Partial Success",
                f"Sent {success_count} of {len(selected)} object(s).\n\n"
                f"Failed objects:\n{failed_list}\n\n"
                "Check connection and object types.",
                "OK"
            )
        else:
            # All failed
            FBMessageBox(
                "Send Failed",
                "Failed to send objects to Unreal Engine.\n\n"
                "Check:\n"
                "• Connection is active\n"
                "• UE5 receiver is running\n"
                "• Objects are valid",
                "OK"
            )

        logger.info(f"Send complete: {success_count}/{len(selected)} successful")

    except Exception as e:
        logger.error(f"Send to Unreal error: {str(e)}")
        import traceback
        traceback.print_exc()
        FBMessageBox("Error", f"An error occurred:\n{str(e)}", "OK")
