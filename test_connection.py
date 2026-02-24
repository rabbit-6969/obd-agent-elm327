#!/usr/bin/env python3
"""Quick connection test for COM4 and COM5"""

import obd

print("Testing COM4...")
try:
    conn = obd.OBD("COM4")
    if conn.is_connected():
        print(f"✓ COM4 works! Protocol: {conn.protocol_name()}")
        conn.close()
    else:
        print("✗ COM4 failed")
except Exception as e:
    print(f"✗ COM4 error: {e}")

print("\nTesting COM5...")
try:
    conn = obd.OBD("COM5")
    if conn.is_connected():
        print(f"✓ COM5 works! Protocol: {conn.protocol_name()}")
        conn.close()
    else:
        print("✗ COM5 failed")
except Exception as e:
    print(f"✗ COM5 error: {e}")

print("\nUse the working COM port with the main diagnostic script.")
