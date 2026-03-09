#!/usr/bin/env python3
"""
Simple test to verify if ATCRA (CAN Receive Address) filtering works.

This tests if the adapter can monitor a single CAN ID with headers included.
"""

import serial
import time

def test_atcra(port='COM3'):
    """Test ATCRA filtering on a single CAN ID"""
    
    print("=" * 80)
    print("ATCRA Simple Test")
    print("=" * 80)
    print()
    
    try:
        ser = serial.Serial(port=port, baudrate=38400, timeout=2)
        print(f"✓ Connected to {port}")
        time.sleep(2)
        
    except Exception as e:
        print(f"✗ Failed to open port: {e}")
        return False
    
    def send_cmd(cmd):
        """Send command and get response"""
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
        
        return response.decode('ascii', errors='ignore').strip()
    
    # Initialize
    print("\nInitializing adapter...")
    send_cmd("ATZ")
    time.sleep(1)
    send_cmd("ATE0")
    send_cmd("ATL0")
    send_cmd("ATS1")  # Spaces ON (easier to parse)
    send_cmd("ATH1")  # Headers ON
    send_cmd("ATSP0")  # Auto protocol
    
    # Test basic communication
    print("Testing basic communication...")
    resp = send_cmd("0100")
    print(f"  Response: {resp}")
    
    if "7E8" not in resp and "41" not in resp:
        print("  ✗ No communication with vehicle")
        ser.close()
        return False
    
    print("  ✓ Vehicle is responding")
    print()
    
    # Test ATCRA filtering
    print("=" * 80)
    print("Testing ATCRA Filtering")
    print("=" * 80)
    print()
    
    # Try monitoring CAN ID 0x080 (Engine RPM/Speed - should be active when engine running)
    print("Setting ATCRA filter to 0x080 (Engine RPM/Speed)...")
    resp = send_cmd("ATCRA080")
    print(f"  ATCRA080 response: {resp}")
    
    if "?" in resp or "ERROR" in resp:
        print("  ✗ ATCRA command not supported by this adapter")
        ser.close()
        return False
    
    print("  ✓ ATCRA command accepted")
    print()
    
    # Start monitoring
    print("Starting ATMA for 5 seconds...")
    print("(Looking for CAN ID 0x080 messages)")
    print()
    
    ser.reset_input_buffer()
    ser.write(b'ATMA\r')
    time.sleep(0.5)
    
    # Collect data
    start_time = time.time()
    all_data = ""
    
    while time.time() - start_time < 5:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
            all_data += chunk
        time.sleep(0.1)
    
    # Stop monitoring
    ser.write(b'\r')
    time.sleep(0.2)
    
    # Analyze data
    lines = [line.strip() for line in all_data.replace('\r', '\n').split('\n') if line.strip()]
    
    print(f"Received {len(lines)} lines")
    print()
    
    if len(lines) == 0:
        print("✗ No data received")
        print()
        print("Possible causes:")
        print("  - CAN ID 0x080 not active (engine not running?)")
        print("  - ATCRA filtering not working")
        print("  - ATMA not working")
        ser.close()
        return False
    
    # Show first 10 lines
    print("First 10 lines received:")
    for i, line in enumerate(lines[:10], 1):
        print(f"  {i}. {line}")
    print()
    
    # Check if lines have CAN ID 0x080
    valid_messages = 0
    for line in lines:
        if line.startswith('080 ') or line.startswith('080'):
            valid_messages += 1
    
    print(f"Valid 0x080 messages: {valid_messages}")
    print()
    
    if valid_messages > 0:
        print("✓ ATCRA filtering works!")
        print("  Headers are included in output")
        print("  CAN monitoring is functional with ATCRA")
    else:
        print("✗ No valid 0x080 messages found")
        print()
        print("Possible causes:")
        print("  - CAN ID 0x080 not active on this vehicle")
        print("  - Headers still not included despite ATCRA")
        print("  - Data format unexpected")
    
    # Clear filter
    send_cmd("ATCRA")
    
    ser.close()
    return valid_messages > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test ATCRA filtering')
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    
    args = parser.parse_args()
    
    success = test_atcra(port=args.port)
    
    if success:
        print("\n" + "=" * 80)
        print("CONCLUSION: ATCRA works - use targeted_can_monitor.py")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("CONCLUSION: ATCRA doesn't work - adapter limitation")
        print("=" * 80)
        print()
        print("Recommendation: Use quality adapter (Vgate iCar Pro, OBDLink)")
