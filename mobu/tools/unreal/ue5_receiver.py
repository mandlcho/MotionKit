"""
Unreal Engine 5 Receiver Script
Run this in UE5's Python console to receive objects from MotionBuilder

To use:
1. Open your UE5 project
2. Go to Window > Output Log
3. Select "Python" from the dropdown
4. Copy and paste this script, or use: py "path/to/ue5_receiver.py"
"""

import unreal
import socket
import struct
import json
import threading

# Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 9998


class MotionBuilderReceiver:
    """Receives objects from MotionBuilder and spawns them in Unreal"""

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.thread = None
        self.editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        self.asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    def start(self):
        """Start the receiver server"""
        if self.running:
            unreal.log_warning("Receiver already running")
            return

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.running = True

            unreal.log(f"MotionBuilder Receiver listening on {self.host}:{self.port}")
            unreal.log("Waiting for MotionBuilder connection...")

            # Start listening thread
            self.thread = threading.Thread(target=self._listen)
            self.thread.daemon = True
            self.thread.start()

        except Exception as e:
            unreal.log_error(f"Failed to start receiver: {str(e)}")
            self.running = False

    def stop(self):
        """Stop the receiver server"""
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        unreal.log("MotionBuilder Receiver stopped")

    def _listen(self):
        """Listen for incoming connections"""
        while self.running:
            try:
                self.client_socket, address = self.server_socket.accept()
                unreal.log(f"MotionBuilder connected from {address}")

                # Handle messages from this client
                self._handle_client()

            except Exception as e:
                if self.running:
                    unreal.log_error(f"Connection error: {str(e)}")

        unreal.log("Receiver thread stopped")

    def _handle_client(self):
        """Handle messages from connected client"""
        while self.running:
            try:
                # Read message length (4 bytes)
                length_data = self._recv_exactly(4)
                if not length_data:
                    break

                message_length = struct.unpack('!I', length_data)[0]

                # Read message data
                message_data = self._recv_exactly(message_length)
                if not message_data:
                    break

                # Parse JSON
                message = json.loads(message_data.decode('utf-8'))

                # Process message
                self._process_message(message)

            except json.JSONDecodeError as e:
                unreal.log_error(f"Invalid JSON received: {str(e)}")
            except Exception as e:
                unreal.log_error(f"Error handling message: {str(e)}")
                break

        # Client disconnected
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
        unreal.log("MotionBuilder disconnected")

    def _recv_exactly(self, num_bytes):
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            chunk = self.client_socket.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _process_message(self, message):
        """Process received message"""
        msg_type = message.get("type")

        if msg_type == "handshake":
            unreal.log(f"Handshake from {message.get('source')} v{message.get('version')}")

        elif msg_type == "spawn_object":
            self._spawn_object(message)

        elif msg_type == "disconnect":
            unreal.log("Received disconnect request")
            self.running = False

        else:
            unreal.log_warning(f"Unknown message type: {msg_type}")

    def _spawn_object(self, data):
        """
        Spawn an object in the Unreal level

        Args:
            data (dict): Object data from MotionBuilder
        """
        try:
            object_name = data.get("object_name", "MobuObject")
            object_type = data.get("object_type", "FBModel")
            transform = data.get("transform", {})
            geometry = data.get("geometry")

            # Get transform data
            location = transform.get("location", [0, 0, 0])
            rotation = transform.get("rotation", [0, 0, 0])
            scale = transform.get("scale", [1, 1, 1])

            # Convert MotionBuilder coordinates to Unreal coordinates
            # MoBu: Y-up, right-handed -> UE5: Z-up, left-handed
            ue_location = unreal.Vector(location[0], location[2], location[1])
            ue_rotation = unreal.Rotator(rotation[0], rotation[2], rotation[1])
            ue_scale = unreal.Vector(scale[0], scale[2], scale[1])

            # Determine what type of actor to spawn
            if geometry and geometry.get("vertices"):
                # Has geometry - spawn as static mesh
                actor = self._create_mesh_actor(object_name, geometry, ue_location, ue_rotation, ue_scale)
            else:
                # No geometry - spawn as empty actor
                actor = self._create_empty_actor(object_name, ue_location, ue_rotation, ue_scale)

            if actor:
                unreal.log(f"Spawned '{object_name}' at {ue_location}")
            else:
                unreal.log_warning(f"Failed to spawn '{object_name}'")

        except Exception as e:
            unreal.log_error(f"Error spawning object: {str(e)}")

    def _create_empty_actor(self, name, location, rotation, scale):
        """Create an empty actor"""
        try:
            actor_class = unreal.Actor
            actor = self.editor_actor_subsystem.spawn_actor_from_class(
                actor_class,
                location,
                rotation
            )

            if actor:
                actor.set_actor_label(name)
                actor.set_actor_scale3d(scale)

            return actor

        except Exception as e:
            unreal.log_error(f"Error creating empty actor: {str(e)}")
            return None

    def _create_mesh_actor(self, name, geometry, location, rotation, scale):
        """Create a static mesh actor from geometry data"""
        try:
            # For now, spawn a cube as placeholder
            # Full mesh creation requires more complex asset generation
            unreal.log(f"Spawning cube placeholder for '{name}'")
            unreal.log(f"  Vertices: {geometry.get('vertex_count', 0)}")
            unreal.log(f"  Triangles: {geometry.get('triangle_count', 0)}")

            # Spawn a cube from engine content
            cube_asset = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")

            if cube_asset:
                actor = self.editor_actor_subsystem.spawn_actor_from_object(
                    cube_asset,
                    location,
                    rotation
                )

                if actor:
                    actor.set_actor_label(name)
                    actor.set_actor_scale3d(scale)

                return actor
            else:
                unreal.log_warning("Could not load cube mesh, spawning empty actor")
                return self._create_empty_actor(name, location, rotation, scale)

        except Exception as e:
            unreal.log_error(f"Error creating mesh actor: {str(e)}")
            return None


# Global instance
_receiver = None


def start_receiver():
    """Start the MotionBuilder receiver"""
    global _receiver

    if _receiver and _receiver.running:
        unreal.log_warning("Receiver is already running")
        return

    _receiver = MotionBuilderReceiver()
    _receiver.start()


def stop_receiver():
    """Stop the MotionBuilder receiver"""
    global _receiver

    if _receiver:
        _receiver.stop()
        _receiver = None
    else:
        unreal.log_warning("Receiver is not running")


def get_receiver_status():
    """Check if receiver is running"""
    global _receiver
    if _receiver and _receiver.running:
        unreal.log(f"Receiver is RUNNING on port {_receiver.port}")
    else:
        unreal.log("Receiver is NOT running")


# Auto-start when script is executed
if __name__ == "__main__":
    unreal.log("=" * 60)
    unreal.log("MotionBuilder to Unreal Engine 5 Live Link")
    unreal.log("=" * 60)
    unreal.log("")
    unreal.log("Commands:")
    unreal.log("  start_receiver()  - Start listening for MotionBuilder")
    unreal.log("  stop_receiver()   - Stop the receiver")
    unreal.log("  get_receiver_status() - Check receiver status")
    unreal.log("")

    # Automatically start the receiver
    start_receiver()

    unreal.log("")
    unreal.log("Ready to receive objects from MotionBuilder!")
    unreal.log("")
