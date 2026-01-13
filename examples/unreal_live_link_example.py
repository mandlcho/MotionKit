"""
Example: MotionBuilder to Unreal Engine 5 Live Link
Demonstrates how to connect MoBu to UE5 and send objects in real-time
"""

from pyfbsdk import FBApplication, FBModelCube, FBVector3d, FBSystem
from mobu.tools.unreal.live_link import get_live_link


def example_basic_connection():
    """
    Example 1: Basic connection to Unreal Engine
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic Connection")
    print("=" * 60)

    # Get the live link instance
    live_link = get_live_link()

    # Connect to Unreal Engine (default: localhost:9998)
    if live_link.connect():
        print("✓ Successfully connected to Unreal Engine!")

        # Check connection status
        if live_link.is_connected():
            print("✓ Connection verified")

        # Disconnect
        live_link.disconnect()
        print("✓ Disconnected")
    else:
        print("✗ Failed to connect. Make sure UE5 receiver is running.")


def example_send_cube():
    """
    Example 2: Create a cube in MoBu and send it to UE5
    """
    print("\n" + "=" * 60)
    print("Example 2: Send a Cube to Unreal Engine")
    print("=" * 60)

    live_link = get_live_link()

    # Connect to Unreal Engine
    if not live_link.connect():
        print("✗ Failed to connect to Unreal Engine")
        return

    # Create a cube in MotionBuilder
    cube = FBModelCube("MobuCube")
    cube.Show = True

    # Set position and scale
    cube.Translation = FBVector3d(100, 50, 0)
    cube.Scaling = FBVector3d(2, 2, 2)

    print(f"✓ Created cube: {cube.Name}")
    print(f"  Position: {cube.Translation}")
    print(f"  Scale: {cube.Scaling}")

    # Send to Unreal Engine
    if live_link.send_object(cube):
        print("✓ Cube sent to Unreal Engine!")
        print("  Check your UE5 viewport - the cube should appear!")
    else:
        print("✗ Failed to send cube")

    live_link.disconnect()


def example_send_selected():
    """
    Example 3: Send currently selected objects to UE5
    """
    print("\n" + "=" * 60)
    print("Example 3: Send Selected Objects")
    print("=" * 60)

    live_link = get_live_link()

    # Connect
    if not live_link.connect():
        print("✗ Failed to connect to Unreal Engine")
        return

    # Send selected objects
    print("Sending selected objects to Unreal Engine...")
    if live_link.send_selected_objects():
        print("✓ Selected objects sent successfully!")
    else:
        print("✗ No objects selected or send failed")

    live_link.disconnect()


def example_custom_host_port():
    """
    Example 4: Connect to UE5 on a custom host/port
    """
    print("\n" + "=" * 60)
    print("Example 4: Custom Host and Port")
    print("=" * 60)

    live_link = get_live_link()

    # Connect to a specific host and port
    custom_host = "192.168.1.100"  # Remote machine
    custom_port = 9999             # Custom port

    print(f"Attempting to connect to {custom_host}:{custom_port}...")

    if live_link.connect(host=custom_host, port=custom_port):
        print("✓ Connected to remote Unreal Engine!")
        live_link.disconnect()
    else:
        print("✗ Failed to connect to custom host/port")


def example_workflow():
    """
    Example 5: Complete workflow - create multiple objects and send
    """
    print("\n" + "=" * 60)
    print("Example 5: Complete Workflow")
    print("=" * 60)

    live_link = get_live_link()

    # Step 1: Connect
    print("\n[Step 1] Connecting to Unreal Engine...")
    if not live_link.connect():
        print("✗ Connection failed")
        return

    print("✓ Connected")

    # Step 2: Create some objects
    print("\n[Step 2] Creating objects in MotionBuilder...")

    cube1 = FBModelCube("Cube_01")
    cube1.Translation = FBVector3d(0, 0, 0)
    cube1.Show = True

    cube2 = FBModelCube("Cube_02")
    cube2.Translation = FBVector3d(200, 0, 0)
    cube2.Scaling = FBVector3d(1.5, 1.5, 1.5)
    cube2.Show = True

    cube3 = FBModelCube("Cube_03")
    cube3.Translation = FBVector3d(-200, 0, 0)
    cube3.Rotation = FBVector3d(45, 45, 0)
    cube3.Show = True

    print("✓ Created 3 cubes")

    # Step 3: Send each object
    print("\n[Step 3] Sending objects to Unreal Engine...")
    for cube in [cube1, cube2, cube3]:
        if live_link.send_object(cube):
            print(f"  ✓ Sent {cube.Name}")
        else:
            print(f"  ✗ Failed to send {cube.Name}")

    # Step 4: Disconnect
    print("\n[Step 4] Disconnecting...")
    live_link.disconnect()
    print("✓ Complete!")

    print("\n" + "=" * 60)
    print("Check your Unreal Engine viewport!")
    print("You should see 3 cubes arranged in a line")
    print("=" * 60)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MotionBuilder to Unreal Engine 5 Live Link Examples")
    print("=" * 60)
    print("\nBefore running these examples:")
    print("1. Start Unreal Engine 5")
    print("2. Open your project")
    print("3. In UE5, go to: Window > Output Log")
    print("4. Select 'Python' from the dropdown")
    print("5. Run: py \"C:/path/to/xMobu/mobu/tools/unreal/ue5_receiver.py\"")
    print("6. Wait for 'Ready to receive objects from MotionBuilder!'")
    print("\nThen run any example below:")
    print("\nAvailable examples:")
    print("  example_basic_connection()  - Test connection")
    print("  example_send_cube()         - Create and send a cube")
    print("  example_send_selected()     - Send selected objects")
    print("  example_custom_host_port()  - Connect to remote UE5")
    print("  example_workflow()          - Complete workflow demo")
    print("\n" + "=" * 60)

    # Uncomment to run an example:
    # example_basic_connection()
    # example_send_cube()
    # example_workflow()
