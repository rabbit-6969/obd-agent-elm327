#!/usr/bin/env python3
"""
Test script to pull all available HVAC information from vehicle
"""

from toolkit.vehicle_communication.elm327_base import ELM327Base
import time

adapter = ELM327Base('COM3')
adapter.connect()

print('=== HVAC Information Gathering ===\n')

# Test various PIDs that might return HVAC-related data
test_commands = [
    ('0100', 'Supported PIDs 01-20'),
    ('0120', 'Supported PIDs 21-40'),
    ('0140', 'Supported PIDs 41-60'),
    ('0105', 'Engine Coolant Temperature'),
    ('010F', 'Intake Air Temperature'),
    ('0142', 'Control Module Voltage'),
    ('0146', 'Ambient Air Temperature'),
    ('015C', 'Engine Oil Temperature'),
    ('2101', 'Mode 21 - Live Data'),
    ('2102', 'Mode 21 - Freeze Frame'),
    ('2201', 'Mode 22 - Read Data by ID'),
    ('1901', 'Mode 19 01 - DTC Count'),
    ('1902FF', 'Mode 19 02 FF - DTC by Status'),
    ('190A', 'Mode 19 0A - Supported DTCs'),
]

results = {}
for cmd, desc in test_commands:
    print(f'Testing {cmd} ({desc})...')
    try:
        resp = adapter.send_obd_command(cmd)
        if resp:
            results[cmd] = {'desc': desc, 'response': resp}
            if len(resp) > 60:
                print(f'  ✓ Response: {resp[:60]}...')
            else:
                print(f'  ✓ Response: {resp}')
        else:
            print(f'  ✗ No response')
    except Exception as e:
        print(f'  ✗ Error: {e}')
    time.sleep(0.3)

print('\n=== Summary of Successful Reads ===')
for cmd, data in results.items():
    print(f'\n{cmd}: {data["desc"]}')
    print(f'  Response: {data["response"]}')

adapter.disconnect()
print('\n=== Complete ===')
