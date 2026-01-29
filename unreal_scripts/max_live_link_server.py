"""
Unreal Engine Socket Server for 3ds Max LiveLink

This script runs inside Unreal Engine and provides a TCP socket server
that 3ds Max can connect to for real-time animation data streaming.

USAGE:
    Run this script in Unreal's Python console, OR
    Click the "Start Max LiveLink" button in the Editor Utility Widget

ARTIST-FRIENDLY:
    - No plugin installation required
    - One-click start via UI button
    - Runs in background until stopped
    - Auto-stops when Unreal closes

PROTOCOL:
    - TCP socket on port 9999
    - Messages: 4-byte length prefix + JSON payload
    - Bidirectional communication
"""

import socket
import threading
import json
import struct
import time

try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False
    print("[MaxLiveLink] WARNING: unreal module not available (testing mode)")


class MaxLiveLinkServer:
    """
    Socket server running in Unreal Engine that streams animation data to 3ds Max
    
    Features:
    - Multi-threaded client handling
    - Query editor selection
    - Extract actor transforms, skeletons, cameras
    - Timeline synchronization
    - Graceful shutdown
    """
    
    def __init__(self, port=9999):
        """
        Initialize the Max LiveLink server
        
        Args:
            port: TCP port to listen on (default: 9999)
        """
        self.port = port
        self.running = False
        self.server_socket = None
        self.server_thread = None
        self.clients = []
        self.client_threads = []
        
    def start(self):
        """Start the socket server in a background thread"""
        if self.running:
            if UNREAL_AVAILABLE:
                unreal.log_warning("Max LiveLink Server already running!")
            else:
                print("[MaxLiveLink] Server already running!")
            return False
            
        try:
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            if UNREAL_AVAILABLE:
                unreal.log(f"Max LiveLink Server started on port {self.port}")
            else:
                print(f"[MaxLiveLink] Server started on port {self.port}")
                
            return True
            
        except Exception as e:
            self.running = False
            if UNREAL_AVAILABLE:
                unreal.log_error(f"Failed to start server: {str(e)}")
            else:
                print(f"[MaxLiveLink] ERROR: Failed to start server: {str(e)}")
            return False
        
    def stop(self):
        """Stop the socket server"""
        if not self.running:
            return
            
        self.running = False
        
        # Close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        if UNREAL_AVAILABLE:
            unreal.log("Max LiveLink Server stopped")
        else:
            print("[MaxLiveLink] Server stopped")
            
    def is_running(self):
        """Check if server is currently running"""
        return self.running
        
    def _run_server(self):
        """Main server loop - accepts client connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Allow periodic checks for shutdown
            
            if UNREAL_AVAILABLE:
                unreal.log(f"Server listening on 0.0.0.0:{self.port}")
            else:
                print(f"[MaxLiveLink] Server listening on 0.0.0.0:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    
                    if UNREAL_AVAILABLE:
                        unreal.log(f"Max client connected from {address}")
                    else:
                        print(f"[MaxLiveLink] Client connected from {address}")
                    
                    self.clients.append(client_socket)
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    self.client_threads.append(client_thread)
                    
                except socket.timeout:
                    # Normal timeout, continue loop
                    continue
                except Exception as e:
                    if self.running:  # Only log if not shutting down
                        if UNREAL_AVAILABLE:
                            unreal.log_error(f"Server accept error: {str(e)}")
                        else:
                            print(f"[MaxLiveLink] ERROR: {str(e)}")
                    break
                    
        except Exception as e:
            if UNREAL_AVAILABLE:
                unreal.log_error(f"Server error: {str(e)}")
            else:
                print(f"[MaxLiveLink] FATAL ERROR: {str(e)}")
        finally:
            self.stop()
            
    def _handle_client(self, client_socket, address):
        """
        Handle messages from a connected Max client
        
        Args:
            client_socket: Connected socket
            address: Client address tuple (ip, port)
        """
        try:
            while self.running:
                # Receive message length (4 bytes, big-endian unsigned int)
                length_data = client_socket.recv(4)
                if not length_data or len(length_data) < 4:
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    chunk = client_socket.recv(min(4096, message_length - len(message_data)))
                    if not chunk:
                        break
                    message_data += chunk
                    
                if len(message_data) < message_length:
                    break
                    
                # Parse JSON message
                try:
                    message = json.loads(message_data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    if UNREAL_AVAILABLE:
                        unreal.log_error(f"Invalid JSON from client: {str(e)}")
                    else:
                        print(f"[MaxLiveLink] ERROR: Invalid JSON: {str(e)}")
                    continue
                
                # Process message and get response
                response = self._process_message(message)
                
                # Send response if we have one
                if response:
                    self._send_message(client_socket, response)
                    
        except Exception as e:
            if self.running:  # Only log if not shutting down
                if UNREAL_AVAILABLE:
                    unreal.log_warning(f"Client handler error: {str(e)}")
                else:
                    print(f"[MaxLiveLink] Client error: {str(e)}")
        finally:
            # Clean up client connection
            try:
                client_socket.close()
            except:
                pass
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                
            if UNREAL_AVAILABLE:
                unreal.log(f"Client {address} disconnected")
            else:
                print(f"[MaxLiveLink] Client {address} disconnected")
                
    def _process_message(self, message):
        """
        Process incoming message from Max and return response
        
        Args:
            message: Parsed JSON message dict
            
        Returns:
            dict: Response message, or None if no response needed
        """
        msg_type = message.get('type')
        
        if msg_type == 'handshake':
            return self._handle_handshake(message)
            
        elif msg_type == 'query_selection':
            return self._handle_query_selection(message)
            
        elif msg_type == 'get_actor_data':
            return self._handle_get_actor_data(message)
            
        elif msg_type == 'set_timeline':
            return self._handle_set_timeline(message)
            
        elif msg_type == 'stream_start':
            return self._handle_stream_start(message)
            
        elif msg_type == 'ping':
            return {'type': 'pong', 'timestamp': time.time()}
            
        else:
            return {
                'type': 'error',
                'message': f'Unknown message type: {msg_type}'
            }
            
    def _handle_handshake(self, message):
        """Handle initial handshake from Max"""
        source = message.get('source', 'Unknown')
        version = message.get('version', '0.0')
        
        if UNREAL_AVAILABLE:
            unreal.log(f"Handshake from {source} v{version}")
        else:
            print(f"[MaxLiveLink] Handshake from {source} v{version}")
        
        return {
            'type': 'handshake_ack',
            'source': 'Unreal Engine',
            'version': '1.0',
            'capabilities': ['query_selection', 'actor_data', 'timeline_sync', 'streaming']
        }
        
    def _handle_query_selection(self, message):
        """Get currently selected actors in Unreal Editor"""
        if not UNREAL_AVAILABLE:
            return {
                'type': 'selection_data',
                'actors': []
            }
            
        try:
            # Get selected actors from editor
            actors = unreal.EditorLevelLibrary.get_selected_level_actors()
            
            actor_data = []
            for actor in actors:
                actor_info = {
                    'name': actor.get_name(),
                    'path': actor.get_path_name(),
                    'class': actor.get_class().get_name(),
                    'type': self._detect_actor_type(actor),
                    'label': actor.get_actor_label()
                }
                actor_data.append(actor_info)
                
            unreal.log(f"Query selection: {len(actor_data)} actors")
            
            return {
                'type': 'selection_data',
                'actors': actor_data
            }
            
        except Exception as e:
            unreal.log_error(f"Failed to query selection: {str(e)}")
            return {
                'type': 'error',
                'message': f'Failed to query selection: {str(e)}'
            }
            
    def _handle_get_actor_data(self, message):
        """Get full animation data for specific actor at specific frame"""
        if not UNREAL_AVAILABLE:
            return {'type': 'error', 'message': 'Unreal not available'}
            
        actor_path = message.get('actor_path')
        frame = message.get('frame', 0)
        
        if not actor_path:
            return {'type': 'error', 'message': 'Missing actor_path'}
            
        try:
            # Load actor by path
            actor = unreal.EditorAssetLibrary.load_asset(actor_path)
            if not actor:
                # Try as object path instead of asset path
                actor = unreal.load_object(None, actor_path)
                
            if not actor:
                return {
                    'type': 'error',
                    'message': f'Actor not found: {actor_path}'
                }
                
            # Build actor data response
            data = {
                'type': 'actor_data',
                'actor_path': actor_path,
                'frame': frame,
                'transform': self._get_transform(actor),
            }
            
            # Add type-specific data
            actor_type = self._detect_actor_type(actor)
            
            if actor_type == 'camera':
                data['camera'] = self._get_camera_data(actor)
                
            elif actor_type == 'character':
                # Get skeletal mesh component
                skeletal_component = None
                if hasattr(actor, 'skeletal_mesh_component'):
                    skeletal_component = actor.skeletal_mesh_component
                elif hasattr(actor, 'mesh'):
                    skeletal_component = actor.mesh
                    
                if skeletal_component:
                    data['skeleton'] = self._get_skeleton_data(skeletal_component)
                    
            return data
            
        except Exception as e:
            unreal.log_error(f"Failed to get actor data: {str(e)}")
            return {
                'type': 'error',
                'message': f'Failed to get actor data: {str(e)}'
            }
            
    def _handle_set_timeline(self, message):
        """Set Unreal timeline to specific frame"""
        if not UNREAL_AVAILABLE:
            return {'type': 'timeline_ack', 'frame': 0}
            
        frame = message.get('frame', 0)
        
        try:
            # TODO: Implement timeline control based on user's setup
            # This will depend on whether they use Sequencer, Animation Blueprint, etc.
            # For now, just acknowledge
            
            unreal.log(f"Timeline sync request: frame {frame}")
            
            return {
                'type': 'timeline_ack',
                'frame': frame
            }
            
        except Exception as e:
            unreal.log_error(f"Failed to set timeline: {str(e)}")
            return {
                'type': 'error',
                'message': f'Failed to set timeline: {str(e)}'
            }
            
    def _handle_stream_start(self, message):
        """Acknowledge start of streaming mode"""
        actor_paths = message.get('actors', [])
        
        if UNREAL_AVAILABLE:
            unreal.log(f"Streaming started for {len(actor_paths)} actors")
        else:
            print(f"[MaxLiveLink] Streaming started for {len(actor_paths)} actors")
        
        return {
            'type': 'stream_ready',
            'actors': actor_paths
        }
        
    def _detect_actor_type(self, actor):
        """
        Detect what type of actor this is
        
        Args:
            actor: Unreal actor object
            
        Returns:
            str: 'camera', 'character', or 'prop'
        """
        if not UNREAL_AVAILABLE:
            return 'prop'
            
        try:
            if actor.is_a(unreal.CameraActor):
                return 'camera'
            elif actor.is_a(unreal.SkeletalMeshActor):
                return 'character'
            elif actor.is_a(unreal.Character):
                return 'character'
            else:
                return 'prop'
        except:
            return 'prop'
            
    def _get_transform(self, actor):
        """
        Get actor transform (location, rotation, scale)
        
        Args:
            actor: Unreal actor object
            
        Returns:
            dict: Transform data
        """
        if not UNREAL_AVAILABLE:
            return {
                'location': [0, 0, 0],
                'rotation': [0, 0, 0],
                'scale': [1, 1, 1]
            }
            
        try:
            transform = actor.get_actor_transform()
            location = transform.translation
            rotation = transform.rotation.rotator()
            scale = transform.scale3d
            
            return {
                'location': [location.x, location.y, location.z],
                'rotation': [rotation.roll, rotation.pitch, rotation.yaw],
                'scale': [scale.x, scale.y, scale.z]
            }
        except Exception as e:
            unreal.log_warning(f"Failed to get transform: {str(e)}")
            return {
                'location': [0, 0, 0],
                'rotation': [0, 0, 0],
                'scale': [1, 1, 1]
            }
            
    def _get_camera_data(self, camera_actor):
        """
        Get camera-specific properties
        
        Args:
            camera_actor: Camera actor object
            
        Returns:
            dict: Camera properties
        """
        if not UNREAL_AVAILABLE:
            return {}
            
        try:
            camera_component = camera_actor.camera_component
            
            return {
                'fov': camera_component.field_of_view,
                'aspect_ratio': camera_component.aspect_ratio,
                'focal_length': camera_component.current_focal_length if hasattr(camera_component, 'current_focal_length') else 50.0
            }
        except Exception as e:
            unreal.log_warning(f"Failed to get camera data: {str(e)}")
            return {}
            
    def _get_skeleton_data(self, skeletal_mesh_component):
        """
        Get bone hierarchy and transforms from skeletal mesh
        
        Args:
            skeletal_mesh_component: SkeletalMeshComponent
            
        Returns:
            dict: Skeleton data with bone transforms
        """
        if not UNREAL_AVAILABLE:
            return {'bones': []}
            
        try:
            bones = []
            num_bones = skeletal_mesh_component.get_num_bones()
            
            for bone_index in range(num_bones):
                bone_name = skeletal_mesh_component.get_bone_name(bone_index)
                bone_transform = skeletal_mesh_component.get_bone_transform(bone_index)
                
                location = bone_transform.translation
                rotation = bone_transform.rotation.rotator()
                scale = bone_transform.scale3d
                
                bones.append({
                    'name': bone_name,
                    'index': bone_index,
                    'transform': {
                        'location': [location.x, location.y, location.z],
                        'rotation': [rotation.roll, rotation.pitch, rotation.yaw],
                        'scale': [scale.x, scale.y, scale.z]
                    }
                })
                
            return {'bones': bones, 'bone_count': num_bones}
            
        except Exception as e:
            unreal.log_warning(f"Failed to get skeleton data: {str(e)}")
            return {'bones': []}
            
    def _send_message(self, client_socket, data):
        """
        Send JSON message with length prefix
        
        Args:
            client_socket: Socket to send to
            data: Dict to serialize and send
        """
        try:
            # Convert to JSON and encode
            json_data = json.dumps(data)
            message = json_data.encode('utf-8')
            
            # Send length prefix (4 bytes, big-endian) followed by message
            length = struct.pack('!I', len(message))
            client_socket.sendall(length + message)
            
        except Exception as e:
            if UNREAL_AVAILABLE:
                unreal.log_error(f"Failed to send message: {str(e)}")
            else:
                print(f"[MaxLiveLink] ERROR: Failed to send message: {str(e)}")


# ============================================================================
# GLOBAL SERVER INSTANCE
# ============================================================================

_server = None


def start_server(port=9999):
    """
    Start the Max LiveLink server (called from UI button or console)
    
    Args:
        port: TCP port to listen on (default: 9999)
        
    Returns:
        bool: True if started successfully, False if already running or error
    """
    global _server
    
    if _server and _server.is_running():
        if UNREAL_AVAILABLE:
            unreal.log_warning("Max LiveLink Server is already running!")
        else:
            print("[MaxLiveLink] Server already running!")
        return False
        
    _server = MaxLiveLinkServer(port)
    return _server.start()


def stop_server():
    """
    Stop the Max LiveLink server
    
    Returns:
        bool: True if stopped, False if not running
    """
    global _server
    
    if not _server or not _server.is_running():
        if UNREAL_AVAILABLE:
            unreal.log_warning("Max LiveLink Server is not running")
        else:
            print("[MaxLiveLink] Server not running")
        return False
        
    _server.stop()
    return True


def toggle_server(port=9999):
    """
    Toggle server on/off (for toolbar button)
    
    Args:
        port: TCP port to listen on if starting
        
    Returns:
        bool: True if now running, False if now stopped
    """
    global _server
    
    if _server and _server.is_running():
        _server.stop()
        return False
    else:
        start_server(port)
        return True


def is_server_running():
    """
    Check if server is currently running
    
    Returns:
        bool: True if running, False otherwise
    """
    global _server
    return _server is not None and _server.is_running()


def get_server_status():
    """
    Get detailed server status
    
    Returns:
        dict: Status information
    """
    global _server
    
    if not _server:
        return {
            'running': False,
            'port': None,
            'clients': 0
        }
        
    return {
        'running': _server.is_running(),
        'port': _server.port,
        'clients': len(_server.clients)
    }


# ============================================================================
# AUTO-START (if executed directly)
# ============================================================================

if __name__ == '__main__':
    # Auto-start server when script is executed
    if start_server():
        if UNREAL_AVAILABLE:
            unreal.log("=" * 60)
            unreal.log("MAX LIVELINK SERVER STARTED")
            unreal.log("=" * 60)
            unreal.log("Server is running on port 9999")
            unreal.log("You can now connect from 3ds Max")
            unreal.log("")
            unreal.log("To stop: run 'stop_server()' in Python console")
            unreal.log("=" * 60)
        else:
            print("=" * 60)
            print("MAX LIVELINK SERVER STARTED (TEST MODE)")
            print("=" * 60)
            print("Server is running on port 9999")
            print("Note: Unreal module not available, running in test mode")
            print("=" * 60)
