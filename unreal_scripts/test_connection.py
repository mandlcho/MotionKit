"""
Test Connection Script for Max LiveLink

This script tests the Max LiveLink server connection from outside Unreal.
Use this to verify the server is running and accepting connections.

USAGE:
    python test_connection.py

REQUIREMENTS:
    - Max LiveLink server running in Unreal Engine
    - Python 3.7+ (standard library only, no external packages)
"""

import socket
import json
import struct
import sys


def send_message(sock, data):
    """Send JSON message with length prefix"""
    json_data = json.dumps(data)
    message = json_data.encode('utf-8')
    length = struct.pack('!I', len(message))
    sock.sendall(length + message)


def receive_message(sock):
    """Receive JSON message with length prefix"""
    # Receive length (4 bytes)
    length_data = sock.recv(4)
    if not length_data or len(length_data) < 4:
        return None
        
    message_length = struct.unpack('!I', length_data)[0]
    
    # Receive message data
    message_data = b''
    while len(message_data) < message_length:
        chunk = sock.recv(min(4096, message_length - len(message_data)))
        if not chunk:
            return None
        message_data += chunk
        
    return json.loads(message_data.decode('utf-8'))


def test_connection(host='127.0.0.1', port=9999):
    """Test connection to Max LiveLink server"""
    print("=" * 60)
    print("Max LiveLink Connection Test")
    print("=" * 60)
    print(f"Connecting to {host}:{port}...")
    
    try:
        # Create socket and connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        
        print("✓ Connected successfully!")
        print("")
        
        # Test 1: Handshake
        print("Test 1: Handshake")
        print("-" * 40)
        handshake = {
            'type': 'handshake',
            'source': '3ds Max Test Client',
            'version': '1.0'
        }
        
        send_message(sock, handshake)
        response = receive_message(sock)
        
        if response and response.get('type') == 'handshake_ack':
            print("✓ Handshake successful")
            print(f"  Server: {response.get('source', 'Unknown')}")
            print(f"  Version: {response.get('version', 'Unknown')}")
            print(f"  Capabilities: {', '.join(response.get('capabilities', []))}")
        else:
            print("✗ Handshake failed")
            print(f"  Response: {response}")
        
        print("")
        
        # Test 2: Ping
        print("Test 2: Ping")
        print("-" * 40)
        ping = {'type': 'ping'}
        
        send_message(sock, ping)
        response = receive_message(sock)
        
        if response and response.get('type') == 'pong':
            print("✓ Ping successful")
            print(f"  Timestamp: {response.get('timestamp', 'N/A')}")
        else:
            print("✗ Ping failed")
            print(f"  Response: {response}")
        
        print("")
        
        # Test 3: Query Selection
        print("Test 3: Query Selection")
        print("-" * 40)
        query = {'type': 'query_selection'}
        
        send_message(sock, query)
        response = receive_message(sock)
        
        if response and response.get('type') == 'selection_data':
            actors = response.get('actors', [])
            print(f"✓ Query successful ({len(actors)} actors)")
            
            if actors:
                print("  Selected actors:")
                for actor in actors:
                    print(f"    - {actor.get('name')} ({actor.get('type')})")
            else:
                print("  No actors selected in Unreal")
        else:
            print("✗ Query failed")
            print(f"  Response: {response}")
        
        print("")
        
        # Close connection
        sock.close()
        
        print("=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        print("")
        print("The Max LiveLink server is working correctly.")
        print("You can now connect from 3ds Max.")
        
        return True
        
    except socket.timeout:
        print("")
        print("=" * 60)
        print("✗ Connection Timeout")
        print("=" * 60)
        print("")
        print("The server did not respond within 5 seconds.")
        print("")
        print("Troubleshooting:")
        print("1. Make sure Unreal Engine is running")
        print("2. Make sure the Max LiveLink server is started")
        print("3. Check the port number (default: 9999)")
        print("4. Check firewall settings")
        
        return False
        
    except ConnectionRefusedError:
        print("")
        print("=" * 60)
        print("✗ Connection Refused")
        print("=" * 60)
        print("")
        print("Could not connect to the server.")
        print("")
        print("Troubleshooting:")
        print("1. Make sure Unreal Engine is running")
        print("2. Make sure the Max LiveLink server is started:")
        print("   - Open Unreal's Python console")
        print("   - Paste the max_live_link_server.py script")
        print("   - Look for: 'Max LiveLink Server started on port 9999'")
        print("3. Check if another program is using port 9999")
        
        return False
        
    except Exception as e:
        print("")
        print("=" * 60)
        print(f"✗ Error: {str(e)}")
        print("=" * 60)
        
        return False


if __name__ == '__main__':
    # Parse command line arguments
    host = '127.0.0.1'
    port = 9999
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    
    # Run test
    success = test_connection(host, port)
    
    # Exit code for automation
    sys.exit(0 if success else 1)
