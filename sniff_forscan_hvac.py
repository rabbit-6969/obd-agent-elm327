#!/usr/bin/env python3
"""
COM Port Sniffer for FORScan HVAC Communication
Captures all traffic on COM3 to reverse-engineer Ford proprietary protocol
"""

import serial
import time
from datetime import datetime
import json

def sniff_com_port(port='COM3', baudrate=38400, duration=300):
    """
    Sniff COM port traffic
    
    Args:
        port: COM port to sniff (default COM3)
        baudrate: Baud rate (FORScan typically uses 38400 or 500000)
        duration: How long to sniff in seconds (default 5 minutes)
    """
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f'logs/forscan_sniff_{timestamp}.log'
    json_file = f'logs/forscan_sniff_{timestamp}.json'
    
    print('=' * 70)
    print('FORSCAN COM PORT SNIFFER')
    print('=' * 70)
    print(f'Port: {port}')
    print(f'Baudrate: {baudrate}')
    print(f'Duration: {duration} seconds')
    print(f'Log file: {log_file}')
    print(f'JSON file: {json_file}')
    print()
    print('INSTRUCTIONS:')
    print('1. Start this script')
    print('2. Open FORScan')
    print('3. Connect to vehicle')
    print('4. Navigate to HVAC module')
    print('5. Read DTCs or perform diagnostics')
    print('6. Script will capture all commands')
    print()
    print('Press Ctrl+C to stop early')
    print('=' * 70)
    print()
    
    captured_data = {
        'timestamp': timestamp,
        'port': port,
        'baudrate': baudrate,
        'duration': duration,
        'traffic': []
    }
    
    try:
        # Open serial port in read-only mode
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1
        )
        
        print(f'✓ Connected to {port} at {baudrate} baud')
        print('✓ Listening for traffic...')
        print()
        
        start_time = time.time()
        packet_count = 0
        
        with open(log_file, 'w') as f:
            f.write(f'FORScan COM Port Sniff - {timestamp}\n')
            f.write(f'Port: {port}, Baudrate: {baudrate}\n')
            f.write('=' * 70 + '\n\n')
            
            while (time.time() - start_time) < duration:
                # Read available data
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    
                    if data:
                        packet_count += 1
                        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        hex_data = ' '.join(f'{b:02X}' for b in data)
                        ascii_data = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
                        
                        # Log to file
                        f.write(f'[{current_time}] Packet #{packet_count}\n')
                        f.write(f'HEX:   {hex_data}\n')
                        f.write(f'ASCII: {ascii_data}\n')
                        f.write(f'Bytes: {len(data)}\n')
                        f.write('-' * 70 + '\n')
                        f.flush()
                        
                        # Print to console
                        print(f'[{current_time}] Packet #{packet_count}')
                        print(f'HEX:   {hex_data}')
                        print(f'ASCII: {ascii_data}')
                        print()
                        
                        # Store in JSON
                        captured_data['traffic'].append({
                            'timestamp': current_time,
                            'packet_number': packet_count,
                            'hex': hex_data,
                            'ascii': ascii_data,
                            'bytes': len(data),
                            'raw_bytes': list(data)
                        })
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
        
        ser.close()
        
    except serial.SerialException as e:
        print(f'\n✗ Error: {e}')
        print('\nNote: FORScan must be closed for this script to access COM3')
        print('Alternative: Use a COM port splitter/monitor tool')
        return
    
    except KeyboardInterrupt:
        print('\n\n✓ Stopped by user')
    
    finally:
        # Save JSON data
        with open(json_file, 'w') as f:
            json.dump(captured_data, f, indent=2)
        
        print()
        print('=' * 70)
        print('CAPTURE COMPLETE')
        print('=' * 70)
        print(f'Packets captured: {packet_count}')
        print(f'Duration: {time.time() - start_time:.1f} seconds')
        print(f'Log file: {log_file}')
        print(f'JSON file: {json_file}')
        print()
        
        if packet_count > 0:
            print('✓ Traffic captured successfully!')
            print('\nNext steps:')
            print('1. Analyze captured commands')
            print('2. Identify HVAC-specific patterns')
            print('3. Implement in ELM327 adapter')
        else:
            print('⚠ No traffic captured')
            print('Make sure FORScan was actively communicating during capture')

if __name__ == '__main__':
    import sys
    
    # Default parameters
    port = 'COM3'
    baudrate = 38400  # Try 38400 first, then 500000 if no data
    duration = 300  # 5 minutes
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        port = sys.argv[1]
    if len(sys.argv) > 2:
        baudrate = int(sys.argv[2])
    if len(sys.argv) > 3:
        duration = int(sys.argv[3])
    
    print('\nNOTE: This script cannot run while FORScan is connected!')
    print('You need a COM port splitter/monitor tool to sniff live traffic.')
    print()
    print('Recommended approach:')
    print('1. Use FORScan\'s built-in logging feature')
    print('2. Or use a COM port monitor tool like:')
    print('   - Device Monitoring Studio')
    print('   - Serial Port Monitor')
    print('   - Portmon (free from Microsoft)')
    print()
    print('Alternative: Capture ELM327 responses after FORScan commands')
    print()
    
    response = input('Continue anyway? (y/n): ')
    if response.lower() == 'y':
        sniff_com_port(port, baudrate, duration)
    else:
        print('Cancelled.')
