#!/usr/bin/env python3
"""
Test ATCRA with spaces enabled to see raw output format.

This will help us understand if:
1. ATCRA is working but CAN IDs aren't active
2. ATCRA is not working at all
3. Data format is unexpected
"""

import serial
import time

def test_atcra_verbose(port='COM3'):
    """Test ATCRA with verbose output"""
    
    print("=" * 80)
    print("ATCRA Verbose Test")
    print("=" * 80)
    print()
    
    try:
        ser = serial.Serial(port=port, baudrate=38400, timeout=2)
        print(f"✓ Connected to {port}")
        time.sleep(2)
    except Exception as e:
        print(f"✗ Failed: {e}")
        return
    
    def send_cmd(cmd, desc=""):
        """Send command and show response"""
        if desc:
            print(f"\n{desc}")
        print(f"  Command: {cmd}")
        
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write((cmd + '\r').encode())
        
        response = b''
        start = time.time()
        
        while time.time() - start < 2:
            if ser.in_waiting:
                response += ser.read(ser.in_waiting)
                if b'>' in response:
                    break
            time.sleep(0.05)
        
        resp_str = response.decode('ascii', errors='ignore')
        print(f"  Response: {repr(resp_str)}")
        return resp_str
    
    # Initialize
    print("Initializing...")
    send_cmd("ATZ", "Reset")
    time.sleep(1)
    send_cmd("ATE0", "Echo off")
    send_cmd("ATL0", "Linefeeds off")
    send_cmd("ATS1", "Spaces ON (for readability)")
    send_cmd("ATH1", "Headers ON")
    send_cmd("ATSP0", "Auto protocol")
    
    # Test communication
    send_cmd("0100", "Test communication")
    
    print("\n" + "=" * 80)
    print("Test 1: ATCRA for 0x080 (Engine RPM)")
    print("=" * 80)
    
    send_cmd("ATCRA080", "Set filter to 0x080")
    
    print("\nStarting ATMA for 3 seconds...")
    ser.reset_input_buffer()
    ser.write(b'ATMA\r')
    time.sleep(0.3)
    
    # Read initial response
    initial = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
    print(f"Initial: {repr(initial[:100])}")
    
    # Collect for 3 seconds
    start = time.time()
    data = ""
    while time.time() - start < 3:
        if ser.in_waiting:
            data += ser.read(ser.in_waiting).decode('ascii', errors='ignore')
        time.sleep(0.1)
    
    # Stop
    ser.write(b'\r')
    time.sleep(0.2)
    
    print(f"\nTotal characters: {len(data)}")
    print(f"First 300 chars: {repr(data[:300])}")
    print(f"Last 300 chars: {repr(data[-300:])}")
    
    # Clear filter
    send_cmd("ATCRA", "Clear filter")
    
    print("\n" + "=" * 80)
    print("Test 2: ATCRA for 0x7E8 (PCM Response)")
    print("=" * 80)
    print("(This is the response ID - might see echoes of our commands)")
    
    send_cmd("ATCRA7E8", "Set filter to 0x7E8")
    
    print("\nStarting ATMA for 3 seconds...")
    ser.reset_input_buffer()
    ser.write(b'ATMA\r')
    time.sleep(0.3)
    
    # Collect for 3 seconds
    start = time.time()
    data = ""
    while time.time() - start < 3:
        if ser.in_waiting:
            data += ser.read(ser.in_waiting).decode('ascii', errors='ignore')
        time.sleep(0.1)
    
    # Stop
    ser.write(b'\r')
    time.sleep(0.2)
    
    print(f"\nTotal characters: {len(data)}")
    print(f"First 300 chars: {repr(data[:300])}")
    
    # Clear filter
    send_cmd("ATCRA", "Clear filter")
    
    print("\n" + "=" * 80)
    print("Test 3: No filter (ATMA without ATCRA)")
    print("=" * 80)
    
    print("\nStarting ATMA for 3 seconds (no filter)...")
    ser.reset_input_buffer()
    ser.write(b'ATMA\r')
    time.sleep(0.3)
    
    # Collect for 3 seconds
    start = time.time()
    data = ""
    while time.time() - start < 3:
        if ser.in_waiting:
            data += ser.read(ser.in_waiting).decode('ascii', errors='ignore')
        time.sleep(0.1)
    
    # Stop
    ser.write(b'\r')
    time.sleep(0.2)
    
    print(f"\nTotal characters: {len(data)}")
    print(f"First 500 chars: {repr(data[:500])}")
    
    lines = [l.strip() for l in data.replace('\r', '\n').split('\n') if l.strip() and l.strip() != '>']
    print(f"\nTotal lines: {len(lines)}")
    
    if len(lines) > 0:
        print("\nFirst 5 lines:")
        for i, line in enumerate(lines[:5], 1):
            print(f"  {i}. {line}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    
    if len(lines) == 0:
        print("✗ No CAN data received at all")
        print("  Possible causes:")
        print("    - Vehicle CAN bus not active (engine off?)")
        print("    - Adapter not connected to CAN bus")
        print("    - ATMA command not supported")
    else:
        print(f"✓ Receiving CAN data ({len(lines)} lines)")
        print()
        
        # Check format
        sample = lines[0] if lines else ""
        has_spaces = ' ' in sample
        starts_with_3hex = len(sample) >= 3 and all(c in '0123456789ABCDEF' for c in sample[:3])
        
        print(f"Sample line: {sample}")
        print(f"  Has spaces: {has_spaces}")
        print(f"  Starts with 3 hex digits: {starts_with_3hex}")
        print()
        
        if has_spaces and starts_with_3hex:
            print("✓ Format looks correct (CAN ID + spaces + data)")
            print("  Headers are working!")
        elif not has_spaces:
            print("✗ No spaces - headerless format")
            print("  ATH1 not working in ATMA mode")
        else:
            print("? Unexpected format")
    
    ser.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ATCRA filtering')
    parser.add_argument('--port', default='COM3', help='Serial port')
    
    args = parser.parse_args()
    
    test_atcra_verbose(port=args.port)
