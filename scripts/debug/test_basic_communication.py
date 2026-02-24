"""
Test Basic ELM327 Communication

This script tests if we can communicate with the vehicle at all.
"""

import serial
import time

COM_PORT = "COM3"
BAUDRATE = 38400

def test_communication():
    print("="*70)
    print("Basic Communication Test")
    print("="*70)
    print()
    
    try:
        # Connect
        print(f"Connecting to {COM_PORT}...")
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=2.0)
        time.sleep(2)
        print("✓ Serial port opened\n")
        
        # Test 1: Reset
        print("Test 1: Reset adapter (ATZ)")
        ser.write(b"ATZ\r")
        time.sleep(1)
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"Response: {repr(response)}")
        print()
        
        # Test 2: Echo off
        print("Test 2: Echo off (ATE0)")
        ser.write(b"ATE0\r")
        time.sleep(0.3)
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"Response: {repr(response)}")
        print()
        
        # Test 3: Auto protocol
        print("Test 3: Auto protocol (ATSP0)")
        ser.write(b"ATSP0\r")
        time.sleep(0.3)
        response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
        print(f"Response: {repr(response)}")
        print()
        
        # Test 4: Read DTCs (Mode 03)
        print("Test 4: Read DTCs (03)")
        ser.write(b"03\r")
        time.sleep(0.5)
        response = ""
        while ser.in_waiting > 0:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        print(f"Response: {repr(response)}")
        print()
        
        # Test 5: Read supported PIDs (01 00)
        print("Test 5: Read supported PIDs (01 00)")
        ser.write(b"01 00\r")
        time.sleep(0.5)
        response = ""
        while ser.in_waiting > 0:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        print(f"Response: {repr(response)}")
        print()
        
        # Test 6: UDS Read DID 0x0100 (transmission temp)
        print("Test 6: UDS Read DID 0x0100 (22 0100)")
        ser.write(b"220100\r")
        time.sleep(0.5)
        response = ""
        while ser.in_waiting > 0:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        print(f"Response: {repr(response)}")
        print()
        
        # Test 7: UDS Read DID 0x0101 (transmission pressure)
        print("Test 7: UDS Read DID 0x0101 (22 0101)")
        ser.write(b"220101\r")
        time.sleep(0.5)
        response = ""
        while ser.in_waiting > 0:
            response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
        print(f"Response: {repr(response)}")
        print()
        
        ser.close()
        print("✓ Test complete")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print()
    print("Make sure:")
    print("- Vehicle ignition is ON")
    print("- FORScan is closed")
    print("- ELM327 is connected to COM3")
    print()
    input("Press Enter to start test...")
    print()
    test_communication()
