"""
MotionBuilder to Unreal Engine 5 Live Link
Real-time connection and object transfer between MoBu and UE5
"""

import socket
import json
import struct
import threading
from pyfbsdk import (
    FBMessageBox, FBApplication, FBSystem, FBModel, FBModelList,
    FBVector3d, FBMatrix, FBModelTransformationType
)
from core.logger import logger
from core.config import config

TOOL_NAME = "LiveLink Settings"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9998


class UnrealLiveLink:
    """Manages live connection between MotionBuilder and Unreal Engine 5"""

    def __init__(self):
        self.socket = None
        self.connected = False
        self.host = config.get('unreal.live_link_host', DEFAULT_HOST)
        self.port = config.get('unreal.live_link_port', DEFAULT_PORT)
        self.connection_thread = None

    def connect(self, host=None, port=None):
        """
        Establish connection to Unreal Engine

        Args:
            host (str): IP address of UE5 instance (default: localhost)
            port (int): Port number (default: 9998)

        Returns:
            bool: True if connection successful
        """
        if self.connected:
            logger.warning("Already connected to Unreal Engine")
            return True

        host = host or self.host
        port = port or self.port

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(2.0)  # Reduced from 5.0 to 2.0 seconds
            self.socket.connect((host, port))
            self.connected = True

            # Send handshake
            handshake = {
                "type": "handshake",
                "source": "MotionBuilder",
                "version": "1.0"
            }
            self._send_message(handshake)

            logger.info(f"Connected to Unreal Engine at {host}:{port}")
            return True

        except socket.timeout:
            logger.error(f"Connection timeout to {host}:{port}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Unreal Engine: {str(e)}")
            self.connected = False
            return False

    def disconnect(self):
        """Close connection to Unreal Engine"""
        if self.socket:
            try:
                # Send disconnect message
                disconnect_msg = {"type": "disconnect"}
                self._send_message(disconnect_msg)
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self.connected = False
                logger.info("Disconnected from Unreal Engine")

    def is_connected(self):
        """Check if currently connected to Unreal Engine"""
        return self.connected and self.socket is not None

    def _send_message(self, data):
        """
        Send JSON message with length prefix

        Args:
            data (dict): Data to send
        """
        if not self.socket:
            raise Exception("Not connected to Unreal Engine")

        # Convert to JSON and encode
        json_data = json.dumps(data)
        message = json_data.encode('utf-8')

        # Send length prefix (4 bytes) followed by message
        length = struct.pack('!I', len(message))
        self.socket.sendall(length + message)

    def send_object(self, fb_model):
        """
        Send a MotionBuilder object to Unreal Engine

        Args:
            fb_model (FBModel): MotionBuilder model to send

        Returns:
            bool: True if sent successfully
        """
        if not self.is_connected():
            logger.error("Not connected to Unreal Engine")
            return False

        try:
            # Get object transform
            translation = FBVector3d()
            rotation = FBVector3d()
            scaling = FBVector3d()

            fb_model.GetVector(translation, FBModelTransformationType.kModelTranslation)
            fb_model.GetVector(rotation, FBModelTransformationType.kModelRotation)
            fb_model.GetVector(scaling, FBModelTransformationType.kModelScaling)

            # Get mesh data if it's a geometric object
            geometry_data = None
            if hasattr(fb_model, 'Geometry') and fb_model.Geometry:
                geometry_data = self._extract_geometry(fb_model)

            # Build message
            message = {
                "type": "spawn_object",
                "object_name": fb_model.Name,
                "object_type": fb_model.ClassName(),
                "transform": {
                    "location": [translation[0], translation[1], translation[2]],
                    "rotation": [rotation[0], rotation[1], rotation[2]],
                    "scale": [scaling[0], scaling[1], scaling[2]]
                },
                "geometry": geometry_data
            }

            self._send_message(message)
            logger.info(f"Sent object '{fb_model.Name}' to Unreal Engine")
            return True

        except Exception as e:
            logger.error(f"Failed to send object: {str(e)}")
            return False

    def _extract_geometry(self, fb_model):
        """
        Extract mesh geometry data from MotionBuilder model

        Args:
            fb_model (FBModel): Model with geometry

        Returns:
            dict: Geometry data (vertices, indices, normals, UVs)
        """
        try:
            geometry = fb_model.Geometry

            # Get vertex positions
            vertices = []
            vertex_count = geometry.VertexCount()
            for i in range(vertex_count):
                pos = geometry.VertexGet(i)
                vertices.append([pos[0], pos[1], pos[2]])

            # Get polygon indices
            indices = []
            polygon_count = geometry.PolygonCount()
            for i in range(polygon_count):
                poly_vertex_count = geometry.PolygonVertexCount(i)
                polygon_indices = []
                for j in range(poly_vertex_count):
                    polygon_indices.append(geometry.PolygonVertexIndex(i, j))

                # Triangulate if needed (simple fan triangulation)
                if poly_vertex_count == 3:
                    indices.extend(polygon_indices)
                elif poly_vertex_count == 4:
                    # Quad to two triangles
                    indices.extend([polygon_indices[0], polygon_indices[1], polygon_indices[2]])
                    indices.extend([polygon_indices[0], polygon_indices[2], polygon_indices[3]])
                else:
                    # N-gon fan triangulation
                    for j in range(1, poly_vertex_count - 1):
                        indices.extend([polygon_indices[0], polygon_indices[j], polygon_indices[j + 1]])

            # Get normals
            normals = []
            for i in range(vertex_count):
                normal = geometry.VertexNormalGet(i)
                normals.append([normal[0], normal[1], normal[2]])

            return {
                "vertices": vertices,
                "indices": indices,
                "normals": normals,
                "vertex_count": vertex_count,
                "triangle_count": len(indices) // 3
            }

        except Exception as e:
            logger.warning(f"Could not extract geometry: {str(e)}")
            return None

    def send_selected_objects(self):
        """Send all currently selected objects to Unreal Engine"""
        if not self.is_connected():
            logger.error("Not connected to Unreal Engine")
            return False

        selected = FBModelList()
        FBGetSelectedModels(selected)

        if len(selected) == 0:
            logger.warning("No objects selected")
            return False

        success_count = 0
        for model in selected:
            if self.send_object(model):
                success_count += 1

        logger.info(f"Sent {success_count}/{len(selected)} objects to Unreal Engine")
        return success_count > 0


# Global instance
_live_link_instance = None


def get_live_link():
    """Get or create the global live link instance"""
    global _live_link_instance
    if _live_link_instance is None:
        _live_link_instance = UnrealLiveLink()
    return _live_link_instance


def execute(control, event):
    """Execute Unreal Live Link tool - Opens the monitoring UI"""
    logger.info("Opening Unreal Live Link Monitor...")

    try:
        # Import and launch the UI
        from mobu.tools.unreal.live_link_ui import execute as launch_ui
        launch_ui(control, event)

    except Exception as e:
        logger.error(f"Unreal Live Link error: {str(e)}")
        FBMessageBox("Error", f"Failed to open Live Link Monitor:\n{str(e)}", "OK")


def send_selected_to_ue5(control, event):
    """Send currently selected objects to Unreal Engine"""
    logger.info("Sending selected objects to UE5...")

    try:
        live_link = get_live_link()

        if not live_link.is_connected():
            FBMessageBox("UE5 Live Link", "Not connected to Unreal Engine.\n\nPlease connect first.", "OK")
            return

        selected = FBModelList()
        FBGetSelectedModels(selected)

        if len(selected) == 0:
            FBMessageBox("UE5 Live Link", "No objects selected.\n\nPlease select objects to send.", "OK")
            return

        # Send objects
        if live_link.send_selected_objects():
            FBMessageBox(
                "UE5 Live Link",
                f"Successfully sent {len(selected)} object(s) to Unreal Engine!",
                "OK"
            )
        else:
            FBMessageBox("UE5 Live Link", "Failed to send objects. Check connection.", "OK")

    except Exception as e:
        logger.error(f"Send to UE5 error: {str(e)}")
        FBMessageBox("Error", f"An error occurred: {str(e)}", "OK")
