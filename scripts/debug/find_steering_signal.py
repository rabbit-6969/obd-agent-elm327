#!/usr/bin/env python3
"""
Ford Escape 2008 - Find Steering Angle Signal

Captures CAN traffic while you turn the steering wheel, then analyzes
which CAN IDs changed to identify the steering angle signal.

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/find_steering_signal.py
    
    1. Script will capture baseline (wheel stationary) for 10 seconds
    2. Then prompt you to turn the wheel
    3. Captures data while you turn the wheel for 10 seconds
    4. Analyzes which CAN IDs changed
"""

import serial
import time
import sys
from datetime import datetime
from collections import defaultdict

class ELM327:
    """ELM327 adapter interface"""
    
    def __init__(self, port='COM3', baudrate=38400, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
    
    def connect(self):
        """Connect and initialize ELM327"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)
            
            # Initialize adapter
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")
            self.send_command("ATL0")
            self.send_command("ATS1")  # Spaces ON
            self.send_command("ATH1")  # Headers ON
            self.send_command("ATSP0")  # Auto protocol
            
            # Test communication
            response = self.send_command("0100")
            if not response or "NO DATA" in response:
                return False
            
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
    
    def monitor_can_id(self, can_id, duration=10):
        """Monitor specific CAN ID and collect all unique messages"""
        can_id_hex = f"{can_id:03X}"
        self.send_command(f"ATCRA{can_id_hex}")
        
        self.ser.reset_input_buffer()
        self.ser.write(b'ATMA\r')
        time.sleep(0.3)
        
        messages = []
        start_time = time.time()
        buffer = ""
        
        while time.time() - start_time < duration:
            if self.ser.in_waiting:
                chunk = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
                buffer += chunk
                
                while '\r' in buffer or '\n' in buffer:
                    if '\r' in buffer:
                        line, buffer = buffer.split('\r', 1)
                    else:
                        line, buffer = buffer.split('\n', 1)
                    
                    line = line.strip()
                    
                    if not line or line == '>' or 'BUFFER' in line or 'STOPPED' in line:
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2 and len(parts[0]) == 3:
                        try:
                            msg_can_id = int(parts[0], 16)
                            # Remove <DATA ERROR
                            data_parts = [p for p in parts[1:] if 'DATA' not in p and 'ERROR' not in p and '<' not in p]
                            data_bytes = ' '.join(data_parts)
                            
                            messages.append({
                                'timestamp': time.time(),
                                'can_id': msg_can_id,
                                'data': data_bytes
                            })
                        except ValueError:
                            pass
            
            time.sleep(0.01)
        
        # Stop monitoring
        self.ser.write(b'\r')
        time.sleep(0.2)
        self.ser.reset_input_buffer()
        self.send_command("ATCRA")
        
        return messages
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def get_unique_values(messages):
    """Get set of unique data values from messages"""
    return set(msg['data'] for msg in messages)

def main(port='COM3'):
    """Find steering angle signal"""
    print("=" * 80)
    print("Ford Escape 2008 - Find Steering Angle Signal")
    print("=" * 80)
    print()
    
    # Connect
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("✓ Connected to ELM327")
    print()
    
    # Known CAN IDs to check
    can_ids = [
        (0x080, "Engine RPM & Vehicle Speed"),
        (0x190, "Brake Status"),
        (0x201, "Accelerator Pedal"),
        (0x228, "Transmission Status"),
        (0x231, "Gear & Torque"),
        (0x240, "Unknown Parameter"),
        (0x420, "Unknown (Counter)"),
        (0x4B0, "Wheel Speeds"),
        (0x4DA, "Steering Angle (Expected)"),
        (0x4F2, "Odometer"),
    ]
    
    try:
        # Phase 1: Baseline (wheel stationary)
        print("PHASE 1: Baseline Capture")
        print("-" * 80)
        print("Keep steering wheel STATIONARY")
        print("Capturing for 10 seconds...")
        print()
        
        baseline = {}
        for can_id, desc in can_ids:
            print(f"  Monitoring 0x{can_id:03X} ({desc})...", end='', flush=True)
            messages = elm.monitor_can_id(can_id, duration=10)
            
            if messages:
                baseline[can_id] = get_unique_values(messages)
                print(f" {len(messages)} msgs, {len(baseline[can_id])} unique")
            else:
                baseline[can_id] = set()
                print(" no data")
        
        print()
        print("=" * 80)
        print("PHASE 2: Steering Movement Capture")
        print("-" * 80)
        print()
        input("Press ENTER, then TURN THE STEERING WHEEL back and forth...")
        print()
        print("Capturing for 10 seconds while you turn the wheel...")
        print()
        
        movement = {}
        for can_id, desc in can_ids:
            print(f"  Monitoring 0x{can_id:03X} ({desc})...", end='', flush=True)
            messages = elm.monitor_can_id(can_id, duration=10)
            
            if messages:
                movement[can_id] = get_unique_values(messages)
                print(f" {len(messages)} msgs, {len(movement[can_id])} unique")
            else:
                movement[can_id] = set()
                print(" no data")
        
        print()
        print("=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        print()
        
        # Find CAN IDs with significant changes
        candidates = []
        
        for can_id in baseline.keys():
            baseline_count = len(baseline[can_id])
            movement_count = len(movement[can_id])
            
            # Check if new unique values appeared during movement
            new_values = movement[can_id] - baseline[can_id]
            
            if len(new_values) > 0:
                desc = dict(can_ids).get(can_id, "Unknown")
                candidates.append({
                    'can_id': can_id,
                    'description': desc,
                    'baseline_unique': baseline_count,
                    'movement_unique': movement_count,
                    'new_values': len(new_values),
                    'sample_baseline': list(baseline[can_id])[:3] if baseline[can_id] else [],
                    'sample_movement': list(movement[can_id])[:3] if movement[can_id] else [],
                    'sample_new': list(new_values)[:3]
                })
        
        if not candidates:
            print("⚠️  No CAN IDs showed changes during steering movement")
            print()
            print("Possible causes:")
            print("  - Steering angle only transmits when wheel is actively moving")
            print("  - Signal is on MS-CAN (try switching adapter to MS-CAN position)")
            print("  - Your vehicle doesn't transmit steering angle on CAN bus")
            print("  - Need to monitor different CAN IDs")
            print()
            return False
        
        print(f"Found {len(candidates)} CAN ID(s) that changed during steering:")
        print()
        
        for candidate in candidates:
            print(f"CAN ID 0x{candidate['can_id']:03X} - {candidate['description']}")
            print(f"  Baseline unique values: {candidate['baseline_unique']}")
            print(f"  Movement unique values: {candidate['movement_unique']}")
            print(f"  New values during movement: {candidate['new_values']}")
            
            if candidate['sample_baseline']:
                print(f"  Sample baseline: {candidate['sample_baseline'][0]}")
            
            if candidate['sample_new']:
                print(f"  Sample new: {candidate['sample_new'][0]}")
            
            print()
        
        print("=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print()
        
        # Recommend most likely candidate
        best = max(candidates, key=lambda x: x['new_values'])
        print(f"Most likely steering angle signal: CAN ID 0x{best['can_id']:03X}")
        print(f"  {best['new_values']} new unique values appeared during movement")
        print()
        
        return True
        
    except KeyboardInterrupt:
        print("\nStopped by user")
        return False
    
    finally:
        elm.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Find steering angle signal by comparing stationary vs movement'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    
    args = parser.parse_args()
    
    success = main(port=args.port)
    sys.exit(0 if success else 1)
