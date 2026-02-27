#!/usr/bin/env python3
"""
Simple test to verify FJ Cruiser ABS communication
Tests both standard OBD-II and UDS protocols
"""

import serial
import time

def test_abs_communication(port='COM3'):
    """Test ABS module communication"""
    
    print("=" * 70)
    print("FJ Cruiser ABS Communication Test")
    print("=" * 70)
    
    try:
        # Connect
        print("\nConnecting...")
        conn = serial.Serial(port, 38400, timeout=3)
        time.sleep(2)
        
        def send_cmd(cmd):
            """Send command and get response"""
            conn.write((cmd + '\r').encode())
            time.sleep(0.2)
            response = b''
            for _ in range(15):  # Try reading for 1.5 seconds
                if conn.in_waiting:
                    response += conn.read(conn.in_waiting)
                time.sleep(0.1)
                if b'>' in response:
                    break
            return response.decode('utf-8', errors='ignore').strip()
        
        # Initialize
        print("Initializing ELM327...")
        send_cmd("ATZ")
        time.sleep(1)
        send_cmd("ATE0")
        send_cmd("ATL0")
        send_cmd("ATS0")
        send_cmd("ATH1")
        
        print("\n" + "=" * 70)
        print("TEST 1: Standard OBD-II Mode 03 (Read DTCs)")
        print("=" * 70)
        send_cmd("ATSP6")  # ISO 15765-4 CAN
        response = send_cmd("03")
        print(f"Command: 03")
        print(f"Response: {response}")
        
        print("\n" + "=" * 70)
        print("TEST 2: Enter Extended Diagnostic Session")
        print("=" * 70)
        send_cmd("ATSH 7B0")  # Set header to ABS request
        send_cmd("ATFCSH 7B8")  # Set flow control to ABS response
        send_cmd("ATFCSD 30 00 00")
        
        response = send_cmd("10 03")  # Extended diagnostic session
        print(f"Command: 10 03 (Enter extended session)")
        print(f"Response: {response}")
        
        print("\n" + "=" * 70)
        print("TEST 3: UDS Service 0x19 Sub-function 0x01 (Read DTC Count)")
        print("=" * 70)
        response = send_cmd("19 01 FF")
        print(f"Command: 19 01 FF (Read number of DTCs)")
        print(f"Response: {response}")
        print("Note: Toyota modules often respond to 0x19 0x01 even when 0x19 0x02 fails")
        
        print("\n" + "=" * 70)
        print("TEST 4: UDS Service 0x19 Sub-function 0x02 (Read DTCs)")
        print("=" * 70)
        response = send_cmd("19 02 FF")
        print(f"Command: 19 02 FF (Read all DTCs)")
        print(f"Response: {response}")
        
        # Try with just confirmed DTCs
        response = send_cmd("19 02 08")
        print(f"\nCommand: 19 02 08 (Read confirmed DTCs only)")
        print(f"Response: {response}")
        
        print("\n" + "=" * 70)
        print("TEST 5: Try Tester Present (keep session alive)")
        print("=" * 70)
        response = send_cmd("3E 00")
        print(f"Command: 3E 00 (Tester Present)")
        print(f"Response: {response}")
        
        # Try reading DTCs again after tester present
        response = send_cmd("19 02 FF")
        print(f"\nCommand: 19 02 FF (Read all DTCs after tester present)")
        print(f"Response: {response}")
        
        print("\n" + "=" * 70)
        print("TEST 6: Try Service 0x22 (Read Data by ID)")
        print("=" * 70)
        response = send_cmd("22 F1 00")  # Read VIN or similar
        print(f"Command: 22 F1 00 (Read DID)")
        print(f"Response: {response}")
        print("Note: If this works but 0x19 doesn't, module is responsive but has no DTCs")
        
        print("\n" + "=" * 70)
        print("CONCLUSION")
        print("=" * 70)
        print("Toyota 2008 ABS modules often don't respond to Service 0x19 when healthy.")
        print("If no response to 0x19 but response to other services = NO DTCs (normal)")
        print("If no response to ANY service = communication issue")
        
        conn.close()
        print("\n✓ Test complete")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_abs_communication()
