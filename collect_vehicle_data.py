#!/usr/bin/env python3
"""
Comprehensive Vehicle Data Collection Script
Collects all available data from all accessible modules for knowledge base and testing
"""

from toolkit.vehicle_communication.elm327_base import ELM327Base
import json
import time
from datetime import datetime

def collect_all_data():
    """Collect comprehensive vehicle data"""
    
    adapter = ELM327Base('COM3')
    adapter.connect()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    data = {
        'timestamp': timestamp,
        'vehicle': {
            'make': 'Ford',
            'model': 'Escape',
            'year': 2008
        },
        'adapter': {
            'version': None,
            'voltage': None
        },
        'modules': {},
        'supported_pids': {},
        'live_data': {},
        'dtcs': {},
        'freeze_frames': {},
        'monitor_status': {}
    }
    
    print('=' * 70)
    print('COMPREHENSIVE VEHICLE DATA COLLECTION')
    print('=' * 70)
    print(f'Timestamp: {timestamp}\n')
    
    # Get adapter info
    print('--- Adapter Information ---')
    version = adapter.send_command('AT I')
    voltage = adapter.get_voltage()
    data['adapter']['version'] = version
    data['adapter']['voltage'] = voltage
    print(f'Version: {version}')
    print(f'Voltage: {voltage}V\n')
    
    # Test vehicle connection
    print('--- Vehicle Connection Test ---')
    connected = adapter.test_connection()
    data['vehicle_connected'] = connected
    print(f'Connected: {connected}\n')
    
    # Collect supported PIDs
    print('--- Supported PIDs Discovery ---')
    pid_ranges = [
        ('0100', '01-20'),
        ('0120', '21-40'),
        ('0140', '41-60'),
        ('0160', '61-80'),
        ('0180', '81-A0'),
        ('01A0', 'A1-C0'),
        ('01C0', 'C1-E0'),
    ]
    
    for pid, range_desc in pid_ranges:
        print(f'Testing PID range {range_desc}...', end=' ')
        resp = adapter.send_obd_command(pid)
        if resp and resp != 'NO DATA':
            data['supported_pids'][range_desc] = resp
            print(f'✓ {resp}')
        else:
            print('✗')
        time.sleep(0.2)
    
    # Collect live data from all supported PIDs
    print('\n--- Live Data Collection ---')
    common_pids = {
        '0104': 'Calculated Engine Load',
        '0105': 'Engine Coolant Temperature',
        '0106': 'Short Term Fuel Trim Bank 1',
        '0107': 'Long Term Fuel Trim Bank 1',
        '010C': 'Engine RPM',
        '010D': 'Vehicle Speed',
        '010E': 'Timing Advance',
        '010F': 'Intake Air Temperature',
        '0110': 'MAF Air Flow Rate',
        '0111': 'Throttle Position',
        '0113': 'Oxygen Sensors Present',
        '011C': 'OBD Standards',
        '011F': 'Run Time Since Engine Start',
        '0121': 'Distance Traveled with MIL On',
        '012F': 'Fuel Tank Level Input',
        '0133': 'Absolute Barometric Pressure',
        '0142': 'Control Module Voltage',
        '0143': 'Absolute Load Value',
        '0145': 'Relative Throttle Position',
        '0146': 'Ambient Air Temperature',
        '014D': 'Time Run with MIL On',
        '014E': 'Time Since DTCs Cleared',
        '0151': 'Fuel Type',
    }
    
    for pid, desc in common_pids.items():
        print(f'{pid} ({desc})...', end=' ')
        resp = adapter.send_obd_command(pid)
        if resp and resp != 'NO DATA':
            data['live_data'][pid] = {
                'description': desc,
                'response': resp
            }
            print(f'✓ {resp}')
        else:
            print('✗')
        time.sleep(0.2)
    
    # Read DTCs (Mode 03)
    print('\n--- Diagnostic Trouble Codes (Mode 03) ---')
    dtc_resp = adapter.send_obd_command('03')
    if dtc_resp and dtc_resp != 'NO DATA':
        data['dtcs']['mode_03'] = dtc_resp
        print(f'Response: {dtc_resp}')
    else:
        print('No DTCs found')
    
    # Read Pending DTCs (Mode 07)
    print('\n--- Pending DTCs (Mode 07) ---')
    pending_resp = adapter.send_obd_command('07')
    if pending_resp and pending_resp != 'NO DATA':
        data['dtcs']['mode_07'] = pending_resp
        print(f'Response: {pending_resp}')
    else:
        print('No pending DTCs')
    
    # Read Permanent DTCs (Mode 0A)
    print('\n--- Permanent DTCs (Mode 0A) ---')
    perm_resp = adapter.send_obd_command('0A')
    if perm_resp and perm_resp != 'NO DATA':
        data['dtcs']['mode_0A'] = perm_resp
        print(f'Response: {perm_resp}')
    else:
        print('No permanent DTCs')
    
    # Monitor Status
    print('\n--- Monitor Status (Mode 01 PID 01) ---')
    monitor_resp = adapter.send_obd_command('0101')
    if monitor_resp:
        data['monitor_status']['response'] = monitor_resp
        print(f'Response: {monitor_resp}')
    
    # Freeze Frame Data (Mode 02)
    print('\n--- Freeze Frame Data (Mode 02) ---')
    freeze_resp = adapter.send_obd_command('0200')
    if freeze_resp and freeze_resp != 'NO DATA':
        data['freeze_frames']['mode_02'] = freeze_resp
        print(f'Response: {freeze_resp}')
    else:
        print('No freeze frame data')
    
    # Vehicle Info (Mode 09)
    print('\n--- Vehicle Information (Mode 09) ---')
    vin_pids = {
        '0900': 'Supported PIDs',
        '0902': 'VIN',
        '0904': 'Calibration ID',
        '0906': 'Calibration Verification Numbers',
        '090A': 'ECU Name',
    }
    
    for pid, desc in vin_pids.items():
        print(f'{pid} ({desc})...', end=' ')
        resp = adapter.send_obd_command(pid)
        if resp and resp != 'NO DATA':
            data['vehicle_info'] = data.get('vehicle_info', {})
            data['vehicle_info'][pid] = {
                'description': desc,
                'response': resp
            }
            print(f'✓ {resp[:60]}...' if len(resp) > 60 else f'✓ {resp}')
        else:
            print('✗')
        time.sleep(0.2)
    
    # Test different module addresses
    print('\n--- Module Address Testing ---')
    module_addresses = {
        '7E0': 'PCM (Powertrain Control Module)',
        '7E8': 'PCM Response',
        '7E1': 'Transmission',
        '7E9': 'Transmission Response',
        '7A0': 'HVAC',
        '7A8': 'HVAC Response',
        '760': 'ABS',
        '768': 'ABS Response',
        '726': 'BCM (Body Control Module)',
        '72E': 'BCM Response',
        '733': 'IPC (Instrument Panel Cluster)',
        '73B': 'IPC Response',
    }
    
    for addr, desc in module_addresses.items():
        print(f'Testing {addr} ({desc})...', end=' ')
        adapter.set_header(addr)
        time.sleep(0.2)
        resp = adapter.send_obd_command('03')  # Try reading DTCs
        if resp and resp != 'NO DATA' and not resp.startswith('CAN ERROR'):
            data['modules'][addr] = {
                'description': desc,
                'accessible': True,
                'test_response': resp
            }
            print(f'✓ Accessible - {resp}')
        else:
            data['modules'][addr] = {
                'description': desc,
                'accessible': False,
                'test_response': resp if resp else 'No response'
            }
            print(f'✗ {resp if resp else "No response"}')
        time.sleep(0.3)
    
    # Reset to default
    adapter.send_command('AT SH')
    
    adapter.disconnect()
    
    # Save data to JSON file
    filename = f'knowledge_base/vehicle_data_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print('\n' + '=' * 70)
    print('DATA COLLECTION COMPLETE')
    print('=' * 70)
    print(f'Data saved to: {filename}')
    print(f'Total modules tested: {len(data["modules"])}')
    print(f'Accessible modules: {sum(1 for m in data["modules"].values() if m["accessible"])}')
    print(f'Live data points: {len(data["live_data"])}')
    print(f'Supported PID ranges: {len(data["supported_pids"])}')
    
    return data, filename

if __name__ == '__main__':
    try:
        data, filename = collect_all_data()
        print('\n✓ Collection successful!')
        print(f'✓ Data file: {filename}')
    except Exception as e:
        print(f'\n✗ Error during collection: {e}')
        import traceback
        traceback.print_exc()
