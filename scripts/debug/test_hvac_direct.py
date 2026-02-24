#!/usr/bin/env python3
"""
Test script to directly communicate with HVAC module at address 7A0
"""

from toolkit.vehicle_communication.elm327_base import ELM327Base
import time

adapter = ELM327Base('COM3')
adapter.connect()

print('=== Direct HVAC Module Communication Test ===\n')
print('Setting CAN header to 7A0 (HVAC module)...')

# Set CAN header to HVAC module address
success = adapter.set_header('7A0')
if success:
    print('✓ CAN header set to 7A0\n')
else:
    print('✗ Failed to set CAN header\n')

# Test various commands directly to HVAC module
test_commands = [
    ('01', 'Tester Present / Keep Alive'),
    ('03', 'Mode 03 - Read DTCs'),
    ('04', 'Mode 04 - Clear DTCs'),
    ('07', 'Mode 07 - Read Pending DTCs'),
    ('09', 'Mode 09 - Vehicle Info'),
    ('0A', 'Mode 0A - Permanent DTCs'),
    ('19', 'Mode 19 - UDS Read DTCs'),
    ('1901', 'Mode 19 01 - DTC Count'),
    ('1902FF', 'Mode 19 02 FF - DTC by Status'),
    ('21', 'Mode 21 - Manufacturer Specific'),
    ('22', 'Mode 22 - Read Data by ID'),
    ('2201', 'Mode 22 01 - Read Data ID 01'),
    ('2202', 'Mode 22 02 - Read Data ID 02'),
    ('3E00', 'UDS Tester Present'),
    ('1003', 'UDS Start Diagnostic Session'),
    ('1001', 'UDS Default Session'),
    ('1002', 'UDS Programming Session'),
    ('1081', 'UDS Extended Session'),
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

print('\n=== Summary of HVAC Module Responses ===')
if results:
    for cmd, data in results.items():
        print(f'\n{cmd}: {data["desc"]}')
        print(f'  Response: {data["response"]}')
        
        # Decode negative responses
        resp = data["response"].replace(' ', '').upper()
        if resp.startswith('7F'):
            nrc = resp[4:6] if len(resp) >= 6 else '??'
            nrc_meanings = {
                '11': 'Service Not Supported',
                '12': 'Sub-Function Not Supported',
                '13': 'Incorrect Message Length',
                '22': 'Conditions Not Correct',
                '31': 'Request Out Of Range',
                '33': 'Security Access Denied',
                '78': 'Response Pending',
            }
            print(f'  → Negative Response Code: {nrc} ({nrc_meanings.get(nrc, "Unknown")})')
else:
    print('No responses received from HVAC module')

# Reset to default (no specific header)
print('\n\nResetting CAN header to default...')
adapter.send_command('AT SH')
print('✓ Reset complete')

adapter.disconnect()
print('\n=== Test Complete ===')
