#!/usr/bin/env python3
"""
Diagnostic script to identify why CAN bus monitoring captures zero messages.

This script tests each step of the CAN monitoring process to identify where it fails.
"""

import serial
import time

def test_elm327_connection(port='COM3', baudrate=38400):
    """Test basic ELM327 connection and configuration"""
    
    print("=" * 80)
    print("ELM327 CAN Monitoring Diagnostic")
    print("=" * 80)
    print()
    
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=2)
        print(f"✓ Serial port {port} opened successfully")
        time.sleep(2)
        
    except Exception as e:
        print(f"✗ Failed to open serial port: {e}")
        return False
    
    def send_cmd(cmd, description):
        """Send command and print response"""
        print(f"\n{description}")
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
        
        resp_str = response.decode('ascii', errors='ignore').strip()
        print(f"  Response: {repr(resp_str)}")
        
        return resp_str
    
    # Test sequence
    print("\n" + "=" * 80)
    print("STEP 1: Initialize Adapter")
    print("=" * 80)
    
    send_cmd("ATZ", "Reset adapter")
    time.sleep(1)
    
    send_cmd("ATI", "Get adapter version")
    send_cmd("ATE0", "Echo off")
    send_cmd("ATL0", "Linefeeds off")
    send_cmd("ATS0", "Spaces off")
    
    print("\n" + "=" * 80)
    print("STEP 2: Configure Headers")
    print("=" * 80)
    
    send_cmd("ATH0", "Headers OFF (baseline)")
    send_cmd("ATH1", "Headers ON (required for CAN IDs)")
    send_cmd("ATH", "Check header status")
    
    print("\n" + "=" * 80)
    print("STEP 3: Protocol Selection")
    print("=" * 80)
    
    send_cmd("ATSP0", "Auto protocol")
    time.sleep(0.5)
    send_cmd("ATDP", "Display current protocol")
    
    print("\n" + "=" * 80)
    print("STEP 4: Test Communication")
    print("=" * 80)
    
    resp = send_cmd("0100", "Mode 01 PID 00 (supported PIDs)")
    
    if "NO DATA" in resp or not resp or "?" in resp:
        print("\n  ⚠️  WARNING: No response to Mode 01 command")
        print("  Trying manual protocol selection...")
        send_cmd("ATSP6", "Set protocol to ISO 15765-4 CAN (11 bit, 500 kbaud)")
        time.sleep(0.5)
        send_cmd("ATDP", "Display protocol")
        resp = send_cmd("0100", "Retry Mode 01 PID 00")
    
    # Check for valid response (with or without spaces)
    if "4100" in resp or "41 00" in resp or "7E8" in resp:
        print("\n  ✓ Communication successful!")
        print(f"  PCM responded: {resp}")
    else:
        print("\n  ✗ Communication failed")
        print("  This means the adapter cannot talk to the vehicle")
        print("  Possible causes:")
        print("    - Vehicle not in accessory/run mode")
        print("    - Adapter not properly connected")
        print("    - Wrong protocol")
        ser.close()
        return False
    
    print("\n" + "=" * 80)
    print("STEP 5: Test CAN Monitoring")
    print("=" * 80)
    
    # Ensure headers are on
    send_cmd("ATH1", "Ensure headers ON")
    
    print("\nStarting ATMA (Monitor All) for 5 seconds...")
    print("(Looking for CAN messages with headers)")
    print()
    
    ser.reset_input_buffer()
    ser.write(b'ATMA\r')
    time.sleep(0.5)
    
    # Read initial response
    initial = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
    print(f"Initial ATMA response: {repr(initial[:200])}")
    
    if "?" in initial or "ERROR" in initial:
        print("\n  ✗ ATMA command failed")
        print("  Trying ATMT (Monitor for Transmit)...")
        ser.write(b'\r')
        time.sleep(0.2)
        ser.reset_input_buffer()
        ser.write(b'ATMT00\r')
        time.sleep(0.5)
        initial = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
        print(f"ATMT response: {repr(initial[:200])}")
    
    # Collect data for 5 seconds
    print("\nCollecting data...")
    start_time = time.time()
    all_data = ""
    line_count = 0
    
    while time.time() - start_time < 5:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
            all_data += chunk
            
            # Count lines
            line_count = all_data.count('\r') + all_data.count('\n')
        
        time.sleep(0.1)
    
    # Stop monitoring
    ser.write(b'\r')
    time.sleep(0.2)
    
    print(f"\nTotal characters received: {len(all_data)}")
    print(f"Total line breaks: {line_count}")
    print()
    
    if len(all_data) < 50:
        print("  ✗ Very little data received")
        print("  This suggests ATMA is not working")
        print()
        print("Raw data received:")
        print(repr(all_data))
    else:
        print("  ✓ Data is being received")
        print()
        print("First 500 characters:")
        print(repr(all_data[:500]))
        print()
        print("Last 500 characters:")
        print(repr(all_data[-500:]))
    
    print("\n" + "=" * 80)
    print("STEP 6: Parse Sample Data")
    print("=" * 80)
    
    # Try to parse CAN messages
    lines = all_data.replace('\r', '\n').split('\n')
    valid_can_messages = 0
    sample_messages = []
    
    for line in lines[:50]:  # Check first 50 lines
        line = line.strip()
        if not line or line == '>' or 'BUFFER' in line:
            continue
        
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 3:
            try:
                can_id = int(parts[0], 16)
                if 0 <= can_id <= 0x7FF:
                    valid_can_messages += 1
                    if len(sample_messages) < 5:
                        sample_messages.append(line)
            except ValueError:
                pass
    
    print(f"\nValid CAN messages found: {valid_can_messages}")
    
    if valid_can_messages > 0:
        print("\nSample messages:")
        for msg in sample_messages:
            print(f"  {msg}")
        print("\n  ✓ CAN monitoring is working!")
    else:
        print("\n  ✗ No valid CAN messages found")
        print("  Possible causes:")
        print("    - Headers are not actually ON (ATH1 not working)")
        print("    - ATMA is not returning CAN data")
        print("    - Data format is unexpected")
        print("    - Vehicle CAN bus is not active")
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print()
    
    if valid_can_messages > 0:
        print("✓ Everything is working correctly")
        print("  The explore_can_bus.py script should work")
        print("  If it's still capturing zero messages, there may be a parsing bug")
    else:
        print("✗ CAN monitoring is not working")
        print()
        print("Troubleshooting steps:")
        print("  1. Verify vehicle is in RUN mode (engine on or key in RUN)")
        print("  2. Check ELM327 adapter is fully inserted into OBD-II port")
        print("  3. Try a different ELM327 adapter if available")
        print("  4. Check if adapter supports ATMA command (some clones don't)")
        print("  5. Try alternative monitoring commands (ATMT, ATMR)")
    
    ser.close()
    return valid_can_messages > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnose CAN monitoring issues')
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--baudrate', type=int, default=38400, help='Baud rate (default: 38400)')
    
    args = parser.parse_args()
    
    test_elm327_connection(port=args.port, baudrate=args.baudrate)
