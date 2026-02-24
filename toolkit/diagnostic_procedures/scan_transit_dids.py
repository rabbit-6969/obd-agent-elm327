"""
Scan Transit-style DID ranges on 2008 Escape

Based on 2018 Transit data, test if 2008 Escape has any DIDs in ranges
that newer Fords use.
"""

import serial
import time
import sys

COM_PORT = "COM3"
BAUDRATE = 38400

# DID ranges from 2018 Transit that might exist in 2008 Escape
TRANSIT_RANGES = [
    (0x0300, 0x03FF, "Engine/Powertrain (Transit style)"),
    (0x0400, 0x04FF, "Sensors (Transit style)"),
    (0x0500, 0x05FF, "Electrical (Transit style)"),
    (0x0600, 0x06FF, "Learned values (Transit style)"),
    (0x0700, 0x07FF, "Fault status (Transit style)"),
    (0x0900, 0x09FF, "Control outputs (Transit style)"),
    (0x1100, 0x11FF, "EVAP/Emissions (Transit style)"),
    (0x1200, 0x12FF, "Sensors 2 (Transit style)"),
    (0x1500, 0x15FF, "Vehicle speed (Transit style)"),
    (0x1600, 0x16FF, "Misfire data (Transit style)"),
    (0x1E00, 0x1EFF, "Transmission (Transit style) - MOST LIKELY"),
    (0x3000, 0x30FF, "Switches (Transit style)"),
    (0xA400, 0xA4FF, "Key/Security (Transit style)"),
    (0xC100, 0xC1FF, "Security 2 (Transit style)"),
    (0xD000, 0xD0FF, "Module info (Transit style)"),
    (0xD100, 0xD1FF, "Module info 2 (Transit style)"),
    (0xDD00, 0xDDFF, "Distance/time (Transit style)"),
    (0xF400, 0xF4FF, "Standard OBD (Transit style)"),
    (0xFD00, 0xFDFF, "Manufacturer specific (Transit style)"),
]


def test_transit_ranges():
    print("="*70)
    print("Testing Transit-style DID Ranges on 2008 Escape")
    print("="*70)
    print("\nBased on 2018 Transit data, testing if 2008 Escape has")
    print("any DIDs in the same ranges that newer Fords use.\n")
    
    print("Make sure:")
    print("- Vehicle ignition is ON")
    print("- FORScan is closed\n")
    input("Press Enter to start...")
    print()
    
    try:
        # Connect
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=2.0)
        time.sleep(2)
        
        # Initialize
        ser.write(b"ATZ\r")
        time.sleep(1)
        ser.read(ser.in_waiting)
        
        ser.write(b"ATE0\r")
        time.sleep(0.3)
        ser.read(ser.in_waiting)
        
        ser.write(b"ATSP0\r")
        time.sleep(0.3)
        ser.read(ser.in_waiting)
        
        print("✓ Connected\n")
        
        found_dids = []
        
        for start, end, description in TRANSIT_RANGES:
            print(f"\n{'='*70}")
            print(f"Testing: {description}")
            print(f"Range: 0x{start:04X} - 0x{end:04X}")
            print(f"{'='*70}\n")
            
            found_in_range = 0
            total = end - start + 1
            
            for did in range(start, end + 1):
                progress = ((did - start + 1) / total) * 100
                sys.stdout.write(f"\r  Progress: {progress:.1f}% | DID 0x{did:04X} | Found: {found_in_range}  ")
                sys.stdout.flush()
                
                # Send command
                cmd = f"22{did:04X}\r"
                ser.write(cmd.encode())
                time.sleep(0.5)
                
                response = ""
                while ser.in_waiting > 0:
                    response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    time.sleep(0.1)
                
                response = response.strip()
                
                # Check for positive response
                if response and response.startswith('62'):
                    found_in_range += 1
                    print(f"\n  ✓ Found DID 0x{did:04X}: {response}")
                    found_dids.append({
                        'did': did,
                        'response': response,
                        'range': description
                    })
            
            print(f"\n\n  Found {found_in_range} DIDs in this range")
            
            # Ask to continue
            if TRANSIT_RANGES.index((start, end, description)) < len(TRANSIT_RANGES) - 1:
                print("\n\nContinue to next range? (Enter=yes, Ctrl+C=stop): ", end="")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\n\nStopped")
                    break
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\nTotal DIDs found: {len(found_dids)}")
        
        if found_dids:
            print("\nDiscovered DIDs:")
            for item in found_dids:
                print(f"  • 0x{item['did']:04X}: {item['response']}")
                print(f"    Range: {item['range']}")
        else:
            print("\n✗ No additional DIDs found")
            print("\nConclusion: 2008 Escape does not use Transit-style DID ranges")
            print("The 2 DIDs we found (0x0100, 0x0101) are all that's accessible")
        
        ser.close()
        print("\n✓ Disconnected")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_transit_ranges()
