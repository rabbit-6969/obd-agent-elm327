#!/usr/bin/env python3
"""
Test HVAC module on MS-CAN (Medium Speed CAN - 125 kbps)
This is likely where Ford body/comfort modules communicate
"""

from toolkit.vehicle_communication.elm327_base import ELM327Base
import time

adapter = ELM327Base('COM3')
adapter.connect()

print('=== Testing HVAC on MS-CAN (125 kbps) ===\n')

# Try different CAN protocols
protocols = [
    ('6', 'ISO 15765-4 CAN (11 bit ID, 500 kbps) - HS-CAN'),
    ('7', 'ISO 15765-4 CAN (29 bit ID, 500 kbps)'),
    ('8', 'ISO 15765-4 CAN (11 bit ID, 250 kbps) - MS-CAN'),
    ('9', 'ISO 15765-4 CAN (29 bit ID, 250 kbps)'),
    ('A', 'SAE J1939 CAN (29 bit ID, 250 kbps)'),
    ('B', 'USER1 CAN (11 bit ID, 125 kbps) - Possible MS-CAN'),
    ('C', 'USER2 CAN (11 bit ID, 50 kbps)'),
]

for proto, desc in protocols:
    print(f'\n--- Testing Protocol {proto}: {desc} ---')
    
    # Set protocol
    resp = adapter.send_command(f'AT SP{proto}')
    print(f'Set protocol: {resp}')
    time.sleep(0.5)
    
    # Set HVAC header
    adapter.set_header('7A0')
    print('Set header to 7A0 (HVAC)')
    
    # Try a few commands
    test_cmds = [
        ('3E00', 'UDS Tester Present'),
        ('1003', 'UDS Start Diagnostic Session'),
        ('03', 'Read DTCs'),
        ('2201', 'Read Data by ID'),
    ]
    
    for cmd, cmd_desc in test_cmds:
        print(f'  Testing {cmd} ({cmd_desc})...', end=' ')
        resp = adapter.send_obd_command(cmd)
        if resp:
            print(f'✓ {resp}')
            # If we get a response, try more commands
            if not resp.startswith('NO DATA'):
                print(f'    SUCCESS! HVAC responded on protocol {proto}!')
                break
        else:
            print('✗')
        time.sleep(0.2)

print('\n\n=== Manual Protocol Test ===')
print('If switch is on your adapter, try:')
print('1. Flip switch to LOW/MS-CAN position')
print('2. Run this script again')
print('3. Or manually set: AT SP8 (for 250 kbps MS-CAN)')

adapter.disconnect()
print('\n=== Test Complete ===')
