#!/usr/bin/env python3
"""
Final HVAC test with MS-CAN switch flipped
"""

from toolkit.vehicle_communication.elm327_base import ELM327Base
import time

adapter = ELM327Base('COM3')
adapter.connect()

print('=== HVAC Communication Test - MS-CAN (Switch Flipped) ===\n')

# Set protocol to MS-CAN (250 kbps, 11-bit)
print('Setting protocol to 8 (MS-CAN 250 kbps)...')
adapter.send_command('AT SP8')
time.sleep(0.5)

# Set HVAC header
print('Setting header to 7A0 (HVAC module)...')
adapter.set_header('7A0')
time.sleep(0.5)

print('\n--- Testing HVAC Commands ---\n')

# Test commands
commands = [
    ('3E00', 'UDS Tester Present'),
    ('1003', 'UDS Start Diagnostic Session'),
    ('03', 'OBD Mode 03 - Read DTCs'),
    ('07', 'OBD Mode 07 - Pending DTCs'),
    ('19', 'UDS Mode 19 - Read DTCs'),
    ('1902FF', 'UDS Read DTCs by Status'),
    ('2201', 'Read Data by ID 01'),
]

results = {}
for cmd, desc in commands:
    print(f'{cmd} ({desc})...', end=' ')
    resp = adapter.send_obd_command(cmd)
    if resp and resp != 'NO DATA' and not resp.startswith('CAN ERROR'):
        print(f'✓ {resp}')
        results[cmd] = resp
    else:
        status = resp if resp else 'No response'
        print(f'✗ {status}')
    time.sleep(0.3)

print('\n--- Summary ---')
if results:
    print(f'✓ HVAC module responding! Got {len(results)} successful responses')
    for cmd, resp in results.items():
        print(f'  {cmd}: {resp}')
else:
    print('✗ No successful responses from HVAC')

adapter.disconnect()
print('\n=== Test Complete ===')
