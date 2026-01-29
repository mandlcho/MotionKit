"""
Max LiveLink - Connect to Unreal Engine
Real-time connection to UE for animation streaming

Features:
- Test connection to UE server
- Visual connection status
- Handshake protocol
- Simple UI for connection management
"""

import socket
import json
import struct
import threading
import time

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    rt = None
    print("[MaxLiveLink] pymxs not available")

from core.logger import logger
from core.localization import t

TOOL_NAME = "Max LiveLink"

# Connection settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9999
CONNECTION_TIMEOUT = 5.0


class MaxLiveLinkClient:
    """
    Client that connects to Unreal Engine LiveLink server
    Handles socket communication and protocol
    """
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        """
        Initialize LiveLink client
        
        Args:
            host: UE server hostname/IP
            port: UE server port
        """
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.server_info = {}
        
    def connect(self):
        """
        Connect to UE LiveLink server
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if self.connected:
            return (False, "Already connected")
            
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(CONNECTION_TIMEOUT)
            
            logger.info(f"Connecting to UE at {self.host}:{self.port}...")
            
            # Connect to server
            self.socket.connect((self.host, self.port))
            
            # Send handshake
            handshake_msg = {
                'type': 'handshake',
                'source': '3ds Max',
                'version': '1.0'
            }
            
            self._send_message(handshake_msg)
            
            # Wait for response
            response = self._receive_message()
            
            if response and response.get('type') == 'handshake_ack':
                self.connected = True
                self.server_info = response
                logger.info(f"Connected to UE! Server: {response.get('source')} v{response.get('version')}")
                return (True, f"Connected to {response.get('source')} v{response.get('version')}")
            else:
                self.disconnect()
                return (False, "Handshake failed - invalid response")
                
        except socket.timeout:
            self.disconnect()
            return (False, f"Connection timeout - is UE LiveLink server running?")
        except ConnectionRefusedError:
            self.disconnect()
            return (False, f"Connection refused - UE server not running on {self.host}:{self.port}")
        except Exception as e:
            self.disconnect()
            logger.error(f"Connection failed: {str(e)}")
            return (False, f"Error: {str(e)}")
            
    def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        logger.info("Disconnected from UE")
        
    def ping(self):
        """
        Send ping to server to test connection
        
        Returns:
            tuple: (success: bool, latency_ms: float or None)
        """
        if not self.connected:
            return (False, None)
            
        try:
            start_time = time.time()
            
            ping_msg = {'type': 'ping', 'timestamp': start_time}
            self._send_message(ping_msg)
            
            response = self._receive_message()
            
            if response and response.get('type') == 'pong':
                latency = (time.time() - start_time) * 1000  # Convert to ms
                return (True, latency)
            else:
                return (False, None)
                
        except Exception as e:
            logger.error(f"Ping failed: {str(e)}")
            self.disconnect()
            return (False, None)
            
    def query_selection(self):
        """
        Query selected actors in UE
        
        Returns:
            list: List of actor info dicts, or None on error
        """
        if not self.connected:
            return None
            
        try:
            query_msg = {'type': 'query_selection'}
            self._send_message(query_msg)
            
            response = self._receive_message()
            
            if response and response.get('type') == 'selection_data':
                actors = response.get('actors', [])
                logger.info(f"UE selection: {len(actors)} actors")
                return actors
            else:
                logger.error("Invalid response to query_selection")
                return None
                
        except Exception as e:
            logger.error(f"Query selection failed: {str(e)}")
            self.disconnect()
            return None
            
    def _send_message(self, data):
        """
        Send JSON message with length prefix
        
        Args:
            data: Dict to serialize and send
        """
        if not self.socket:
            raise Exception("Not connected")
            
        # Convert to JSON and encode
        json_data = json.dumps(data)
        message = json_data.encode('utf-8')
        
        # Send length prefix (4 bytes, big-endian) followed by message
        length = struct.pack('!I', len(message))
        self.socket.sendall(length + message)
        
    def _receive_message(self):
        """
        Receive JSON message with length prefix
        
        Returns:
            dict: Parsed message, or None on error
        """
        if not self.socket:
            raise Exception("Not connected")
            
        # Receive message length (4 bytes)
        length_data = self.socket.recv(4)
        if not length_data or len(length_data) < 4:
            return None
            
        message_length = struct.unpack('!I', length_data)[0]
        
        # Receive message data
        message_data = b''
        while len(message_data) < message_length:
            chunk = self.socket.recv(min(4096, message_length - len(message_data)))
            if not chunk:
                return None
            message_data += chunk
            
        # Parse JSON
        try:
            return json.loads(message_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {str(e)}")
            return None


# Global client instance
_client = None


def get_client():
    """Get or create global client instance"""
    global _client
    if _client is None:
        _client = MaxLiveLinkClient()
    return _client


def show_connection_dialog():
    """
    Show MaxScript dialog for testing connection to UE
    """
    if not rt:
        logger.error("3ds Max runtime not available")
        return
        
    client = get_client()
    
    # MaxScript dialog
    dialog_script = """
    rollout maxLiveLinkDialog "Max LiveLink - Connection Test" width:400 height:300
    (
        -- Connection settings
        group "Server Settings"
        (
            label lblHost "Unreal Engine Host:" align:#left
            editText txtHost "" text:"localhost" width:350 align:#left
            
            label lblPort "Port:" align:#left
            spinner spnPort "" range:[1, 65535, 9999] type:#integer width:100 align:#left
        )
        
        -- Connection status
        group "Connection Status"
        (
            label lblStatus "Status: Not Connected" align:#left
            label lblServerInfo "" align:#left
            label lblLatency "" align:#left
        )
        
        -- Connection buttons
        group "Actions"
        (
            button btnConnect "Connect to UE" width:180 height:30 align:#left across:2
            button btnDisconnect "Disconnect" width:180 height:30 align:#right enabled:false
            
            button btnTestPing "Test Ping" width:180 height:30 align:#left across:2 enabled:false
            button btnQuerySelection "Query UE Selection" width:180 height:30 align:#right enabled:false
        )
        
        -- Log output
        group "Log"
        (
            editText txtLog "" height:100 readOnly:true
        )
        
        -- Python callback functions (set externally)
        local pythonConnect = undefined
        local pythonDisconnect = undefined
        local pythonPing = undefined
        local pythonQuerySelection = undefined
        
        function updateUI connected =
        (
            btnConnect.enabled = not connected
            btnDisconnect.enabled = connected
            btnTestPing.enabled = connected
            btnQuerySelection.enabled = connected
            
            if connected then
                lblStatus.text = "Status: Connected ✓"
            else
                lblStatus.text = "Status: Not Connected"
        )
        
        function log msg =
        (
            local timestamp = localTime as string
            txtLog.text += timestamp + ": " + msg + "\\n"
        )
        
        on btnConnect pressed do
        (
            if pythonConnect != undefined do
            (
                local host = txtHost.text
                local port = spnPort.value as integer
                log ("Connecting to " + host + ":" + (port as string) + "...")
                python.execute ("max_livelink_dialog_connect('" + host + "', " + (port as string) + ")")
            )
        )
        
        on btnDisconnect pressed do
        (
            if pythonDisconnect != undefined do
            (
                log "Disconnecting..."
                python.execute "max_livelink_dialog_disconnect()"
            )
        )
        
        on btnTestPing pressed do
        (
            if pythonPing != undefined do
            (
                log "Sending ping..."
                python.execute "max_livelink_dialog_ping()"
            )
        )
        
        on btnQuerySelection pressed do
        (
            if pythonQuerySelection != undefined do
            (
                log "Querying UE selection..."
                python.execute "max_livelink_dialog_query_selection()"
            )
        )
    )
    
    createDialog maxLiveLinkDialog
    """
    
    # Execute dialog
    rt.execute(dialog_script)


# Python callback functions for MaxScript dialog
def max_livelink_dialog_connect(host, port):
    """Called from MaxScript when Connect button pressed"""
    client = get_client()
    client.host = host
    client.port = port
    
    success, message = client.connect()
    
    # Update UI
    rt.execute(f"maxLiveLinkDialog.updateUI {str(success).lower()}")
    rt.execute(f'maxLiveLinkDialog.log "{message}"')
    
    if success:
        info = client.server_info
        server_text = f"Server: {info.get('source', 'Unknown')} v{info.get('version', '?')}"
        rt.execute(f'maxLiveLinkDialog.lblServerInfo.text = "{server_text}"')
        
        # Show capabilities
        capabilities = info.get('capabilities', [])
        if capabilities:
            cap_text = "Capabilities: " + ", ".join(capabilities)
            rt.execute(f'maxLiveLinkDialog.log "{cap_text}"')


def max_livelink_dialog_disconnect():
    """Called from MaxScript when Disconnect button pressed"""
    client = get_client()
    client.disconnect()
    
    # Update UI
    rt.execute("maxLiveLinkDialog.updateUI false")
    rt.execute('maxLiveLinkDialog.lblServerInfo.text = ""')
    rt.execute('maxLiveLinkDialog.lblLatency.text = ""')
    rt.execute('maxLiveLinkDialog.log "Disconnected"')


def max_livelink_dialog_ping():
    """Called from MaxScript when Test Ping button pressed"""
    client = get_client()
    
    success, latency = client.ping()
    
    if success:
        latency_text = f"Latency: {latency:.1f} ms"
        rt.execute(f'maxLiveLinkDialog.lblLatency.text = "{latency_text}"')
        rt.execute(f'maxLiveLinkDialog.log "Ping successful: {latency:.1f} ms"')
    else:
        rt.execute('maxLiveLinkDialog.lblLatency.text = "Ping failed"')
        rt.execute('maxLiveLinkDialog.log "Ping failed - connection lost"')
        rt.execute('maxLiveLinkDialog.updateUI false')


def max_livelink_dialog_query_selection():
    """Called from MaxScript when Query Selection button pressed"""
    client = get_client()
    
    actors = client.query_selection()
    
    if actors is not None:
        rt.execute(f'maxLiveLinkDialog.log "Found {len(actors)} selected actors in UE"')
        
        for actor in actors[:5]:  # Show first 5
            name = actor.get('label', actor.get('name', 'Unknown'))
            actor_type = actor.get('type', 'unknown')
            rt.execute(f'maxLiveLinkDialog.log "  - {name} ({actor_type})"')
            
        if len(actors) > 5:
            rt.execute(f'maxLiveLinkDialog.log "  ... and {len(actors) - 5} more"')
    else:
        rt.execute('maxLiveLinkDialog.log "Failed to query selection - connection lost?"')
        rt.execute('maxLiveLinkDialog.updateUI false')


def execute():
    """Main entry point - show connection dialog"""
    try:
        if not rt:
            logger.error("3ds Max runtime not available")
            return
            
        show_connection_dialog()
        
    except Exception as e:
        logger.error(f"Max LiveLink failed: {str(e)}")
        if rt:
            rt.messageBox(f"Error: {str(e)}", title="Max LiveLink Error")
