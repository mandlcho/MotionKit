"""
Unreal Engine 5 - MotionBuilder Live Link Receiver
Editor Utility Widget backend script

This script provides the backend functionality for the Editor Utility Widget.
The widget UI calls these functions via the Python API.
"""

import unreal
import socket
import struct
import json
import threading

# Configuration
HOST = "0.0.0.0"
PORT = 9998

# Global receiver instance
_receiver_instance = None


class MotionBuilderReceiver:
    """Receives objects from MotionBuilder and spawns them in Unreal"""

    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.connected = False
        self.thread = None
        self.editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        self.objects_received = 0

    def start(self):
        """Start the receiver server"""
        if self.running:
            unreal.log_warning("Receiver already running")
            return False

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.running = True
            self.objects_received = 0

            unreal.log(f"[MoBu Link] Listening on {self.host}:{self.port}")
            unreal.log("[MoBu Link] Waiting for MotionBuilder connection...")

            # Start listening thread
            self.thread = threading.Thread(target=self._listen)
            self.thread.daemon = True
            self.thread.start()

            return True

        except Exception as e:
            unreal.log_error(f"[MoBu Link] Failed to start: {str(e)}")
            self.running = False
            return False

    def stop(self):
        """Stop the receiver server"""
        self.running = False
        self.connected = False

        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        unreal.log("[MoBu Link] Receiver stopped")
        return True

    def get_status(self):
        """Get current status"""
        return {
            "running": self.running,
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "objects_received": self.objects_received
        }

    def _listen(self):
        """Listen for incoming connections"""
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    self.client_socket, address = self.server_socket.accept()
                    self.connected = True
                    unreal.log(f"[MoBu Link] MotionBuilder connected from {address}")
                    self._handle_client()
                except socket.timeout:
                    continue

            except Exception as e:
                if self.running:
                    unreal.log_error(f"[MoBu Link] Connection error: {str(e)}")

    def _handle_client(self):
        """Handle messages from connected client"""
        while self.running and self.connected:
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
                unreal.log_error(f"[MoBu Link] Invalid JSON: {str(e)}")
            except Exception as e:
                if self.running:
                    unreal.log_error(f"[MoBu Link] Error: {str(e)}")
                break

        # Client disconnected
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        unreal.log("[MoBu Link] MotionBuilder disconnected")

    def _recv_exactly(self, num_bytes):
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            try:
                chunk = self.client_socket.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except:
                return None
        return data

    def _process_message(self, message):
        """Process received message"""
        msg_type = message.get("type")

        if msg_type == "handshake":
            source = message.get('source', 'Unknown')
            version = message.get('version', '?')
            unreal.log(f"[MoBu Link] Handshake from {source} v{version}")

        elif msg_type == "spawn_object":
            self._spawn_object(message)
            self.objects_received += 1

        elif msg_type == "disconnect":
            unreal.log("[MoBu Link] Disconnect requested")
            self.connected = False

        else:
            unreal.log_warning(f"[MoBu Link] Unknown message type: {msg_type}")

    def _spawn_object(self, data):
        """Spawn an object in the Unreal level"""
        try:
            object_name = data.get("object_name", "MobuObject")
            transform = data.get("transform", {})
            geometry = data.get("geometry")

            # Get transform data
            location = transform.get("location", [0, 0, 0])
            rotation = transform.get("rotation", [0, 0, 0])
            scale = transform.get("scale", [1, 1, 1])

            # Convert MotionBuilder to Unreal coordinates
            # MoBu: Y-up, right-handed -> UE5: Z-up, left-handed
            ue_location = unreal.Vector(location[0], location[2], location[1])
            ue_rotation = unreal.Rotator(rotation[0], rotation[2], rotation[1])
            ue_scale = unreal.Vector(scale[0], scale[2], scale[1])

            # Spawn appropriate actor type
            if geometry and geometry.get("vertices"):
                actor = self._create_mesh_actor(object_name, geometry, ue_location, ue_rotation, ue_scale)
            else:
                actor = self._create_empty_actor(object_name, ue_location, ue_rotation, ue_scale)

            if actor:
                unreal.log(f"[MoBu Link] Spawned '{object_name}'")
            else:
                unreal.log_warning(f"[MoBu Link] Failed to spawn '{object_name}'")

        except Exception as e:
            unreal.log_error(f"[MoBu Link] Error spawning: {str(e)}")

    def _create_empty_actor(self, name, location, rotation, scale):
        """Create an empty actor"""
        try:
            actor = self.editor_actor_subsystem.spawn_actor_from_class(
                unreal.Actor,
                location,
                rotation
            )

            if actor:
                actor.set_actor_label(name)
                actor.set_actor_scale3d(scale)

            return actor

        except Exception as e:
            unreal.log_error(f"[MoBu Link] Error creating actor: {str(e)}")
            return None

    def _create_mesh_actor(self, name, geometry, location, rotation, scale):
        """Create a static mesh actor"""
        try:
            # Load cube placeholder
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
                return self._create_empty_actor(name, location, rotation, scale)

        except Exception as e:
            unreal.log_error(f"[MoBu Link] Error creating mesh: {str(e)}")
            return None


# Public API - Simple functions (no decorators needed for Python console)
def start_receiver():
    """Start the MotionBuilder receiver"""
    global _receiver_instance

    if _receiver_instance and _receiver_instance.running:
        unreal.log_warning("[MoBu Link] Already running")
        return False

    _receiver_instance = MotionBuilderReceiver()
    return _receiver_instance.start()


def stop_receiver():
    """Stop the MotionBuilder receiver"""
    global _receiver_instance

    if _receiver_instance:
        return _receiver_instance.stop()
    else:
        unreal.log_warning("[MoBu Link] Not running")
        return False


def is_receiver_running():
    """Check if receiver is running"""
    global _receiver_instance
    return _receiver_instance is not None and _receiver_instance.running


def is_receiver_connected():
    """Check if MotionBuilder is connected"""
    global _receiver_instance
    return _receiver_instance is not None and _receiver_instance.connected


def get_receiver_status():
    """Get receiver status as string"""
    global _receiver_instance

    if _receiver_instance:
        status = _receiver_instance.get_status()
        if status["running"] and status["connected"]:
            return f"Connected | Port {status['port']} | Objects: {status['objects_received']}"
        elif status["running"]:
            return f"Listening on port {status['port']}..."
        else:
            return "Stopped"
    else:
        return "Not initialized"


def get_objects_received():
    """Get count of objects received"""
    global _receiver_instance
    if _receiver_instance:
        return _receiver_instance.objects_received
    return 0


# Helper function for direct execution
def main():
    """Direct execution entry point"""
    unreal.log("=" * 60)
    unreal.log("MotionBuilder Live Link Receiver")
    unreal.log("=" * 60)
    unreal.log("")
    unreal.log("Starting receiver...")

    if start_receiver():
        unreal.log("")
        unreal.log("Ready to receive from MotionBuilder!")
        unreal.log("To stop: stop_receiver()")
    else:
        unreal.log_error("Failed to start receiver")


if __name__ == "__main__":
    main()
