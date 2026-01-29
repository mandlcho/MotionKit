"""
Widget Bindings for Max LiveLink Editor Utility Widget

This module exposes Python functions to Unreal Engine Blueprints,
allowing the Editor Utility Widget to control the Max LiveLink server.

USAGE IN BLUEPRINT:
    - Call these functions from Button OnClicked events
    - Display return values in UI text widgets
    - Update UI based on server status

FUNCTIONS EXPOSED TO BLUEPRINT:
    - start_max_livelink_server() -> bool
    - stop_max_livelink_server() -> bool
    - is_server_running() -> bool
    - get_server_status_text() -> str
    - get_server_port() -> int
"""

try:
    import unreal
    UNREAL_AVAILABLE = True
except ImportError:
    UNREAL_AVAILABLE = False
    print("[WidgetBindings] WARNING: unreal module not available")


# Import the server module
try:
    from max_live_link_server import (
        start_server,
        stop_server,
        is_server_running as _is_server_running,
        get_server_status
    )
    SERVER_AVAILABLE = True
except ImportError:
    SERVER_AVAILABLE = False
    print("[WidgetBindings] ERROR: max_live_link_server not found")
    print("[WidgetBindings] Make sure max_live_link_server.py is in the same folder")


def start_max_livelink_server():
    """
    Start the Max LiveLink server
    
    Called by Blueprint button: "Start Server"
    
    Returns:
        bool: True if started successfully, False if already running or error
    """
    if not SERVER_AVAILABLE:
        if UNREAL_AVAILABLE:
            unreal.log_error("Max LiveLink server module not available")
        return False
        
    try:
        result = start_server(port=9999)
        
        if result:
            if UNREAL_AVAILABLE:
                unreal.log("✓ Max LiveLink Server started via UI button")
        else:
            if UNREAL_AVAILABLE:
                unreal.log_warning("Server already running or failed to start")
                
        return result
        
    except Exception as e:
        if UNREAL_AVAILABLE:
            unreal.log_error(f"Failed to start server: {str(e)}")
        return False


def stop_max_livelink_server():
    """
    Stop the Max LiveLink server
    
    Called by Blueprint button: "Stop Server"
    
    Returns:
        bool: True if stopped successfully, False if not running
    """
    if not SERVER_AVAILABLE:
        if UNREAL_AVAILABLE:
            unreal.log_error("Max LiveLink server module not available")
        return False
        
    try:
        result = stop_server()
        
        if result:
            if UNREAL_AVAILABLE:
                unreal.log("✓ Max LiveLink Server stopped via UI button")
        else:
            if UNREAL_AVAILABLE:
                unreal.log_warning("Server was not running")
                
        return result
        
    except Exception as e:
        if UNREAL_AVAILABLE:
            unreal.log_error(f"Failed to stop server: {str(e)}")
        return False


def is_max_livelink_running():
    """
    Check if Max LiveLink server is currently running
    
    Called by Blueprint to update UI state (button colors, text, etc.)
    
    Returns:
        bool: True if server is running, False otherwise
    """
    if not SERVER_AVAILABLE:
        return False
        
    try:
        return _is_server_running()
    except Exception as e:
        if UNREAL_AVAILABLE:
            unreal.log_error(f"Failed to check server status: {str(e)}")
        return False


def get_server_status_text():
    """
    Get human-readable server status text for UI display
    
    Called by Blueprint to update status label
    
    Returns:
        str: Status text (e.g., "Running on Port 9999", "Stopped")
    """
    if not SERVER_AVAILABLE:
        return "Server Module Not Found"
        
    try:
        status = get_server_status()
        
        if status['running']:
            client_count = status.get('clients', 0)
            port = status.get('port', 9999)
            
            if client_count == 0:
                return f"Running on Port {port} (No Clients)"
            elif client_count == 1:
                return f"Running on Port {port} (1 Client Connected)"
            else:
                return f"Running on Port {port} ({client_count} Clients Connected)"
        else:
            return "Stopped"
            
    except Exception as e:
        return f"Error: {str(e)}"


def get_server_port():
    """
    Get the port number the server is running on
    
    Returns:
        int: Port number (9999 by default)
    """
    if not SERVER_AVAILABLE:
        return 9999
        
    try:
        status = get_server_status()
        return status.get('port', 9999)
    except:
        return 9999


def get_client_count():
    """
    Get number of connected Max clients
    
    Returns:
        int: Number of connected clients
    """
    if not SERVER_AVAILABLE:
        return 0
        
    try:
        status = get_server_status()
        return status.get('clients', 0)
    except:
        return 0


# ============================================================================
# BLUEPRINT-CALLABLE FUNCTIONS
# ============================================================================
# These functions are designed to be called from Unreal Blueprint graphs
# They can be used in Editor Utility Widgets for UI buttons

# Note: To expose these functions to Blueprint, you would typically use
# unreal.ufunction() decorator in a class that inherits from unreal.Object
# However, for simplicity, we're keeping these as pure Python functions
# that can be called via "Execute Python Command" nodes in Blueprint

# Example Blueprint usage:
#
# On Button "Start Server" Clicked:
#   Execute Python Script: "from widget_bindings import start_max_livelink_server; start_max_livelink_server()"
#
# On Button "Stop Server" Clicked:
#   Execute Python Script: "from widget_bindings import stop_max_livelink_server; stop_max_livelink_server()"
#
# On Tick (to update status text):
#   Execute Python Script: "from widget_bindings import get_server_status_text; print(get_server_status_text())"


if __name__ == '__main__':
    # Test the bindings
    print("=" * 60)
    print("Max LiveLink Widget Bindings - Test Mode")
    print("=" * 60)
    print(f"Server Available: {SERVER_AVAILABLE}")
    print(f"Unreal Available: {UNREAL_AVAILABLE}")
    print("")
    
    if SERVER_AVAILABLE:
        print("Testing server control...")
        print(f"Status: {get_server_status_text()}")
        print(f"Port: {get_server_port()}")
        print(f"Clients: {get_client_count()}")
        
        print("\nStarting server...")
        if start_max_livelink_server():
            print("✓ Server started")
            print(f"Status: {get_server_status_text()}")
        else:
            print("✗ Failed to start server")
            
        print("\nStopping server...")
        if stop_max_livelink_server():
            print("✓ Server stopped")
            print(f"Status: {get_server_status_text()}")
        else:
            print("✗ Failed to stop server")
    else:
        print("Server module not available for testing")
    
    print("=" * 60)
