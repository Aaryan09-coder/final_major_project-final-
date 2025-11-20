#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script to test ESP32 connection
Checks WiFi connectivity, IP reachability, and port availability
"""
import socket
import subprocess
import sys
import platform
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def check_wifi_connection(ssid="ESP32_AP"):
    """Check if connected to ESP32 WiFi"""
    print(f"Checking WiFi connection to '{ssid}'...")
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if ssid in result.stdout:
                print(f"[OK] Connected to '{ssid}'")
                return True
            else:
                print(f"[FAIL] Not connected to '{ssid}'")
                print("  Please connect to ESP32_AP WiFi network (password: 12345678)")
                return False
        except Exception as e:
            print(f"[WARN] Could not check WiFi status: {e}")
            return None
    else:
        # Linux/Mac - would need different commands
        print("[WARN] WiFi check not implemented for this OS")
        return None

def ping_host(host, timeout=2):
    """Ping host to check if it's reachable"""
    print(f"Pinging {host}...")
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", str(timeout * 1000), host],
                capture_output=True,
                timeout=timeout + 1
            )
            if result.returncode == 0:
                print(f"✓ {host} is reachable")
                return True
            else:
                print(f"✗ {host} is not reachable")
                return False
        except Exception as e:
            print(f"✗ Ping failed: {e}")
            return False
    else:
        # Linux/Mac
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(timeout), host],
                capture_output=True,
                timeout=timeout + 1
            )
            if result.returncode == 0:
                print(f"✓ {host} is reachable")
                return True
            else:
                print(f"✗ {host} is not reachable")
                return False
        except Exception as e:
            print(f"✗ Ping failed: {e}")
            return False

def check_port(host, port, timeout=3):
    """Check if port is open and accepting connections"""
    print(f"Checking port {port} on {host}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"[OK] Port {port} is open and accepting connections")
            return True
        else:
            print(f"[FAIL] Port {port} is closed or not accepting connections")
            print(f"  Error code: {result}")
            if result == 10061:  # Windows: Connection refused
                print("  -> This means the ESP32 is reachable but not listening on this port")
                print("  -> Make sure the ESP32 firmware is uploaded and running")
            elif result == 10060:  # Windows: Connection timeout
                print("  -> This means the ESP32 might not be reachable or firewall is blocking")
            return False
    except socket.gaierror as e:
        print(f"[FAIL] DNS/Hostname resolution failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Connection test failed: {e}")
        return False

def test_tcp_connection(host, port, timeout=5):
    """Test actual TCP connection"""
    print(f"\nTesting TCP connection to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        print(f"[OK] Successfully connected to {host}:{port}")
        sock.close()
        return True
    except socket.timeout:
        print(f"[FAIL] Connection timeout after {timeout} seconds")
        return False
    except ConnectionRefusedError:
        print(f"[FAIL] Connection refused - ESP32 is not listening on port {port}")
        print("  -> Make sure ESP32 firmware is uploaded and server is running")
        return False
    except socket.error as e:
        print(f"[FAIL] Connection failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False

def main():
    print("="*80)
    print(" " * 25 + "ESP32 CONNECTION DIAGNOSTICS")
    print("="*80)
    print()
    
    host = "192.168.4.1"
    port = 8000
    
    print(f"Target: {host}:{port}")
    print()
    
    # Step 1: Check WiFi
    wifi_ok = check_wifi_connection()
    print()
    
    # Step 2: Ping host
    ping_ok = ping_host(host)
    print()
    
    # Step 3: Check port
    port_ok = check_port(host, port)
    print()
    
    # Step 4: Test TCP connection
    tcp_ok = test_tcp_connection(host, port)
    print()
    
    # Summary
    print("="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    if wifi_ok is False:
        print("[FAIL] WiFi: Not connected to ESP32_AP")
        print("   -> Connect your laptop to 'ESP32_AP' WiFi (password: 12345678)")
    elif wifi_ok is True:
        print("[OK] WiFi: Connected to ESP32_AP")
    else:
        print("[WARN] WiFi: Status unknown")
    
    if ping_ok:
        print("[OK] Network: ESP32 is reachable")
    else:
        print("[FAIL] Network: ESP32 is not reachable")
        print("   -> Check WiFi connection")
        print("   -> Make sure ESP32 is powered on")
    
    if port_ok:
        print("[OK] Port: Port 8000 is open")
    else:
        print("[FAIL] Port: Port 8000 is closed or not accepting connections")
        print("   -> Make sure ESP32 firmware is uploaded")
        print("   -> Check Serial Monitor to see if server started")
        print("   -> Verify ESP32 is running the updated firmware (port 8000, JSON protocol)")
    
    if tcp_ok:
        print("[OK] Connection: TCP connection successful")
        print("\n[SUCCESS] All checks passed! Your ESP32 should be ready to receive commands.")
    else:
        print("[FAIL] Connection: TCP connection failed")
        print("\n[TROUBLESHOOTING] Steps to fix:")
        print("   1. Make sure ESP32 is powered on")
        print("   2. Connect laptop to 'ESP32_AP' WiFi network (password: 12345678)")
        print("   3. Upload the updated firmware to ESP32 using PlatformIO")
        print("   4. Check Serial Monitor (115200 baud) to verify:")
        print("      - 'AP IP address: 192.168.4.1'")
        print("      - 'TCP server started on port 8000'")
        print("   5. If using Windows Firewall, allow Python through firewall")
    
    print("="*80)

if __name__ == "__main__":
    main()

