#!/usr/bin/env python3
"""
Extended Ford Escape 2008 ABS Module DID Scanner

Scans broader DID ranges to find all accessible parameters.
Tests multiple DID ranges that Ford might use.
"""

import serial
import time
import sys
import json
from datetime import datetime

class SimpleELM327:
    """Simplified ELM327 adapter"""
    
    def __init__(self, port='COM3', baudrate=38400, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
    
    def connect(self):
        """Connect to ELM327 adapter"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)
            
            # Reset and configure
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")
            self.send_command("ATSP0")
            
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, command):
        """Send command and get response"""
        if not self.ser:
            return None
        
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            self.ser.write((command + '\r').encode())
            
            response = b''
            start_time = time.time()
            
            while time.time() - start_time < self.timeout:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting)
                    response += chunk
                    
                    if b'>' in response:
                        break
                
                time.sleep(0.05)
            
            response_str = response.decode('ascii', errors='ignore')
            response_str = response_str.replace('\r', '').replace('\n', ' ')
            response_str = response_str.replace('>', '').strip()
            
            return response_str
        
        except Exception as e:
            return None
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def parse_did_response(response, did):
    """Parse DID response"""
    if not response:
        return None, "NO_RESPONSE"
    
    # Check for negative response
    if '7F 22' in response:
        parts = response.split()
        if len(parts) >= 3:
            nrc = parts[2]
            return None, f"NRC_{nrc}"
    
    # Check for positive response
    if f'62 {did}' in response:
        data = response.replace(f'62 {did}', '').strip()
        return data, "SUCCESS"
    
    return None, "INVALID"

def scan_did_range(elm, start, end, description):
    """Scan a range of DIDs"""
    print(f"\n{'='*80}")
    print(f"Scanning {description}: 0x{start:04X} - 0x{end:04X}")
    print(f"{'='*80}\n")
    
    working_dids = {}
    failed_count = 0
    
    for did_int in range(start, end + 1):
        did_hex = f"{did_int:04X}"
        did_formatted = f"{did_hex[:2]} {did_hex[2:]}"
        command = f"22 {did_formatted}"
        
        response = elm.send_command(command)
        data, status = parse_did_response(response, did_formatted)
        
        if status == "SUCCESS":
            print(f"✓ DID 0x{did_hex}: {data}")
            working_dids[did_hex] = {
                'raw': data,
                'decimal': int(data.replace(' ', ''), 16) if data else None
            }
        else:
            failed_count += 1
            # Only print first few failures to avoid spam
            if failed_count <= 3:
                print(f"✗ DID 0x{did_hex}: {status}")
            elif failed_count == 4:
                print(f"  ... (suppressing further failures)")
        
        time.sleep(0.05)  # Small delay
    
    print(f"\nFound {len(working_dids)} working DIDs in this range")
    return working_dids

def extended_scan(port='COM3'):
    """Extended DID scan across multiple ranges"""
    
    print("=" * 80)
    print("Ford Escape 2008 - ABS Module Extended DID Scanner")
    print("=" * 80)
    print()
    print("This will scan multiple DID ranges to find all accessible parameters.")
    print("This may take 10-15 minutes...")
    print()
    input("Press Enter to start...")
    print()
    
    elm = SimpleELM327(port=port)
    
    try:
        if not elm.connect():
            print("❌ Failed to connect")
            return False
        
        print("✓ Connected to ELM327")
        
        # Set header for ABS module
        elm.send_command("AT SH 760")
        time.sleep(0.1)
        
        print("✓ Set CAN header to ABS module (0x760)")
        
        # Test communication
        response = elm.send_command("3E 01")
        if '7E' in response:
            print("✓ ABS module responding")
        else:
            print(f"⚠ Unexpected response: {response}")
        
        all_working_dids = {}
        
        # Scan multiple ranges
        ranges_to_scan = [
            (0x0000, 0x00FF, "Low Range (0x0000-0x00FF)"),
            (0x0100, 0x01FF, "Module Info Range (0x0100-0x01FF)"),
            (0x0200, 0x02FF, "Sensor Data Range (0x0200-0x02FF)"),
            (0x0300, 0x03FF, "Extended Range 1 (0x0300-0x03FF)"),
            (0x1000, 0x10FF, "Extended Range 2 (0x1000-0x10FF)"),
            (0x2000, 0x20FF, "Extended Range 3 (0x2000-0x20FF)"),
            (0xF000, 0xF0FF, "High Range 1 (0xF000-0xF0FF)"),
            (0xF100, 0xF1FF, "UDS Standard Range (0xF100-0xF1FF)"),
        ]
        
        for start, end, desc in ranges_to_scan:
            working = scan_did_range(elm, start, end, desc)
            all_working_dids.update(working)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knowledge_base/captured_data/ford_escape_abs_extended_scan_{timestamp}.json"
        
        results = {
            'scan_date': datetime.now().isoformat(),
            'vehicle': 'Ford Escape 2008',
            'module': 'ABS (0x760)',
            'working_dids': all_working_dids,
            'total_found': len(all_working_dids)
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print()
        print("=" * 80)
        print("EXTENDED SCAN COMPLETE")
        print("=" * 80)
        print()
        print(f"✓ Total working DIDs found: {len(all_working_dids)}")
        print(f"✓ Results saved to: {filename}")
        print()
        
        if all_working_dids:
            print("WORKING DIDs:")
            print("-" * 80)
            for did, data in sorted(all_working_dids.items()):
                print(f"  0x{did}: {data['raw']} (decimal: {data['decimal']})")
            print()
        else:
            print("⚠ No additional DIDs found beyond 0x0200 and 0x0202")
            print()
            print("This suggests the ABS module has very limited UDS support.")
            print("You may need FORScan or Ford IDS for full diagnostics.")
        
        return True
    
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        elm.close()
        print("Connection closed.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extended DID scan for Ford Escape 2008 ABS module'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    
    args = parser.parse_args()
    
    success = extended_scan(port=args.port)
    sys.exit(0 if success else 1)
