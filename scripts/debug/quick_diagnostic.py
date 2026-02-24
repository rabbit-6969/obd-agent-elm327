#!/usr/bin/env python3
"""
Quick Jeep Wrangler Diagnostic - Direct COM4 connection
Reads DTCs and basic data without freezing
"""

import obd
import time

print("=" * 60)
print("Jeep Wrangler JK (2007) - Quick Diagnostic")
print("=" * 60)

# Connect directly to COM4 with fast=False to prevent freezing
print("\nConnecting to COM4...")
try:
    connection = obd.OBD("COM4", fast=False, timeout=10)
    
    if not connection.is_connected():
        print("✗ Failed to connect")
        print("Try: Unplug adapter, wait 5 seconds, plug back in")
        exit(1)
    
    print(f"✓ Connected!")
    print(f"  Protocol: {connection.protocol_name()}")
    print(f"  Port: {connection.port_name()}")
    
    # Read DTCs
    print("\n" + "=" * 60)
    print("DIAGNOSTIC TROUBLE CODES")
    print("=" * 60)
    
    cmd = obd.commands.GET_DTC
    response = connection.query(cmd)
    
    if response.is_null():
        print("✗ No response from vehicle")
    else:
        dtcs = response.value
        
        if not dtcs or len(dtcs) == 0:
            print("✓ No DTCs found - All systems OK")
        else:
            print(f"\nFound {len(dtcs)} code(s):\n")
            
            for code, description in dtcs:
                print(f"  {code}: {description}")
                
                # Identify airbag codes
                if code.startswith('B'):
                    print(f"    → BODY/AIRBAG CODE")
            
            print("\n⚠ Airbag codes (B-codes) require immediate attention!")
    
    # Read basic vehicle data
    print("\n" + "=" * 60)
    print("VEHICLE DATA")
    print("=" * 60)
    
    # Try to read common parameters
    params = [
        (obd.commands.RPM, "Engine RPM"),
        (obd.commands.SPEED, "Vehicle Speed"),
        (obd.commands.COOLANT_TEMP, "Coolant Temp"),
        (obd.commands.THROTTLE_POS, "Throttle Position"),
    ]
    
    for cmd, name in params:
        try:
            response = connection.query(cmd)
            if not response.is_null():
                print(f"  {name}: {response.value}")
        except:
            pass
    
    # Try to read VIN
    print("\n" + "=" * 60)
    print("VEHICLE INFO")
    print("=" * 60)
    
    try:
        vin_response = connection.query(obd.commands.VIN)
        if not vin_response.is_null():
            print(f"  VIN: {vin_response.value}")
    except:
        print("  VIN: Not available")
    
    # Close connection
    connection.close()
    print("\n✓ Diagnostic complete")
    
except KeyboardInterrupt:
    print("\n\nInterrupted by user")
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Unplug adapter from vehicle")
    print("  2. Wait 10 seconds")
    print("  3. Plug adapter back in")
    print("  4. Wait for LED to blink")
    print("  5. Run script again")

print("\n" + "=" * 60)
