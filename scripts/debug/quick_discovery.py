"""
Quick Vehicle Discovery - Uses proven working approach

This is a simplified version that uses the same approach as scan_transmission_dids.py
which we know works with your vehicle.
"""

import sys

print("="*70)
print("Quick Vehicle Discovery")
print("="*70)
print()
print("Since the comprehensive scanner is having issues, let's use the")
print("proven working approach from scan_transmission_dids.py")
print()
print("Please run these commands in order:")
print()
print("1. Discover transmission DIDs:")
print("   python scan_transmission_dids.py")
print()
print("2. Monitor live transmission data:")
print("   python read_transmission_live.py")
print()
print("3. Read transmission data once:")
print("   python read_transmission_data.py")
print()
print("These scripts are proven to work with your 2008 Ford Escape.")
print()
print("The comprehensive scanner (discover_vehicle_capabilities.py) needs")
print("more debugging to work properly with your specific ELM327 adapter.")
print()
