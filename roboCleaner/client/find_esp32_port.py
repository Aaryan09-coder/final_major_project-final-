#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to find which port the ESP32 is listening on
Tries both 8000 (new JSON protocol) and 8080 (old binary protocol)
"""
import socket
import sys

def test_port(host, port, timeout=2):
    """Test if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def main():
    host = "192.168.4.1"
    ports_to_test = [8000, 8080]
    
    print("="*60)
    print("ESP32 Port Detection")
    print("="*60)
    print(f"Testing {host}...")
    print()
    
    found_port = None
    for port in ports_to_test:
        print(f"Testing port {port}...", end=" ")
        if test_port(host, port):
            print(f"[OK] Port {port} is OPEN")
            found_port = port
            break
        else:
            print(f"[CLOSED]")
    
    print()
    print("="*60)
    if found_port:
        print(f"[SUCCESS] ESP32 is listening on port {found_port}")
        if found_port == 8000:
            print("  -> This is the NEW firmware (JSON protocol)")
        elif found_port == 8080:
            print("  -> This is the OLD firmware (binary protocol)")
            print("  -> You need to upload the updated firmware!")
        print()
        print(f"Update your code to use: esp32_port={found_port}")
    else:
        print("[FAIL] ESP32 is not listening on any known port")
        print()
        print("Possible issues:")
        print("  1. ESP32 firmware not uploaded")
        print("  2. ESP32 server failed to start")
        print("  3. ESP32 is not powered on")
        print()
        print("Next steps:")
        print("  1. Check Serial Monitor (115200 baud)")
        print("  2. Look for 'TCP server started on port XXXX'")
        print("  3. Upload the updated firmware if needed")
    
    print("="*60)
    return found_port

if __name__ == "__main__":
    main()

