#!/usr/bin/env python3
"""
2007 Jeep Wrangler JK - CAN Bus Monitor for Gear & Gas Pedal

Monitors CAN bus for:
- Transmission gear position
- Gas pedal (accelerator) position
- Related powertrain data

Uses ATCRA filtering technique to capture specific CAN IDs.

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/jeep_can_monitor.py --port COM4 --duration 30
    
    Shift gears and press gas pedal to see changes.
    Press Ctrl+C to stop early.
"""

import serial
import time
import sys
from datetime import datetime
from collections import defaultdict

class ELM327:
    """ELM327 adapter interface"""
    
    def __init__(self, port='COM4', baudrate=38400, timeout=2):
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
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS1")  # Spaces ON (required for ATCRA)
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
    
    def start_monitor(self):
        """Start monitoring CAN bus"""
        # Clear any filters
        self.send_command("ATCRA")
        
        # Start monitoring all CAN traffic
        self.ser.reset_input_buffer()
        self.ser.write(b'ATMA\r')
        time.sleep(0.3)
    
    def stop_monitor(self):
        """Stop monitoring"""
        self.ser.write(b'\r')
        time.sleep(0.2)
        self.ser.reset_input_buffer()
        self.send_command("ATCRA")
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def monitor_can_bus(elm, duration=30):
    """Monitor CAN bus and identify gear/pedal signals"""
    print("=" * 80)
    print("Jeep Wrangler JK - CAN Bus Monitor")
    print("=" * 80)
    print()
    print("Monitoring CAN traffic for gear position and gas pedal...")
    print()
    print("INSTRUCTIONS:")
    print("  1. Keep vehicle in Park initially")
    print("  2. Press gas pedal slowly (0% → 50% → 100%)")
    print("  3. Release gas pedal")
    print("  4. Shift through gears: P → R → N → D → 2 → 1 → D → P")
    print("  5. Press gas pedal again in each gear")
    print()
    print("Press Ctrl+C to stop early")
    print()
    print("-" * 80)
    
    elm.start_monitor()
    
    buffer = ""
    start_time = time.time()
    
    # Track all CAN IDs and their data patterns
    can_data = defaultdict(lambda: {'count': 0, 'values': [], 'last_value': None})
    
    try:
        while (time.time() - start_time) < duration:
            if elm.ser.in_waiting:
                chunk = elm.ser.read(elm.ser.in_waiting).decode('ascii', errors='ignore')
                buffer += chunk
                
                while '\r' in buffer or '\n' in buffer:
                    if '\r' in buffer:
                        line, buffer = buffer.split('\r', 1)
                    else:
                        line, buffer = buffer.split('\n', 1)
                    
                    line = line.strip()
                    
                    if not line or line == '>' or 'BUFFER' in line or 'STOPPED' in line:
                        continue
                    
                    # Parse CAN message
                    parts = line.split()
                    if len(parts) >= 2 and len(parts[0]) == 3:
                        try:
                            can_id = int(parts[0], 16)
                            
                            # Extract data bytes
                            data_bytes = []
                            for p in parts[1:]:
                                if len(p) == 2:
                                    try:
                                        int(p, 16)
                                        data_bytes.append(p)
                                    except ValueError:
                                        break
                                else:
                                    break
                            
                            if data_bytes:
                                data_str = ' '.join(data_bytes)
                                
                                # Track this CAN ID
                                can_data[can_id]['count'] += 1
                                
                                # Store unique values
                                if data_str != can_data[can_id]['last_value']:
                                    can_data[can_id]['values'].append(data_str)
                                    can_data[can_id]['last_value'] = data_str
                        
                        except (ValueError, IndexError):
                            pass
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print()
        print("-" * 80)
        print("\nMonitoring stopped by user")
    
    finally:
        elm.stop_monitor()
    
    # Analyze results
    print()
    print("=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    # Sort by number of unique values (likely candidates for gear/pedal)
    sorted_ids = sorted(can_data.items(), 
                       key=lambda x: len(x[1]['values']), 
                       reverse=True)
    
    print(f"Captured {len(sorted_ids)} unique CAN IDs")
    print()
    
    # Show top candidates (most variable data)
    print("TOP CANDIDATES (Most Variable Data):")
    print("-" * 80)
    print(f"{'CAN ID':<10} {'Messages':<12} {'Unique Values':<15} {'Likely Signal'}")
    print("-" * 80)
    
    for can_id, data in sorted_ids[:20]:
        unique_count = len(data['values'])
        msg_count = data['count']
        
        # Guess what this might be
        likely_signal = guess_signal_type(can_id, unique_count, msg_count, data['values'])
        
        print(f"0x{can_id:03X}      {msg_count:<12} {unique_count:<15} {likely_signal}")
    
    print()
    
    # Show detailed data for top 5 candidates
    print("DETAILED DATA FOR TOP 5 CANDIDATES:")
    print("=" * 80)
    
    for i, (can_id, data) in enumerate(sorted_ids[:5], 1):
        print(f"\n{i}. CAN ID 0x{can_id:03X}")
        print(f"   Messages: {data['count']}")
        print(f"   Unique Values: {len(data['values'])}")
        print(f"   Sample Values:")
        
        # Show first 10 unique values
        for j, value in enumerate(data['values'][:10], 1):
            print(f"     {j:2}. {value}")
        
        if len(data['values']) > 10:
            print(f"     ... and {len(data['values']) - 10} more")
    
    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print()
    print("1. Identify which CAN ID contains gear position:")
    print("   - Look for CAN ID with ~6-8 unique values (P, R, N, D, 2, 1)")
    print("   - Values should change when you shifted gears")
    print()
    print("2. Identify which CAN ID contains gas pedal:")
    print("   - Look for CAN ID with many unique values (0-100%)")
    print("   - Values should correlate with pedal position")
    print()
    print("3. Create targeted monitor:")
    print("   - Use scripts/debug/targeted_can_monitor.py")
    print("   - Filter for specific CAN IDs identified above")
    print()

def guess_signal_type(can_id, unique_count, msg_count, values):
    """Guess what signal this CAN ID might contain"""
    
    # Gear position typically has 6-8 unique values
    if 5 <= unique_count <= 10:
        return "Possible Gear Position"
    
    # Gas pedal has many unique values
    elif unique_count > 50:
        return "Possible Gas Pedal / Analog Signal"
    
    # RPM/Speed have moderate unique values
    elif 20 <= unique_count <= 50:
        return "Possible RPM / Speed / Sensor"
    
    # Binary signals (on/off)
    elif unique_count == 2:
        return "Possible Binary Signal (On/Off)"
    
    # Counter or status
    elif unique_count < 5:
        return "Possible Counter / Status"
    
    # High frequency = likely important
    elif msg_count > 100:
        return "High Frequency Signal"
    
    else:
        return "Unknown"

def main(port='COM4', duration=30):
    """Main entry point"""
    print("=" * 80)
    print("2007 Jeep Wrangler JK - CAN Bus Monitor")
    print("=" * 80)
    print()
    
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        print()
        print("Troubleshooting:")
        print("  - Verify adapter is plugged into OBD-II port")
        print("  - Check COM port (use Device Manager)")
        print("  - Ensure vehicle ignition is in RUN position")
        print("  - Try unplugging and replugging adapter")
        return False
    
    print("✓ Connected to ELM327")
    print()
    
    try:
        monitor_can_bus(elm, duration=duration)
        return True
    
    finally:
        elm.close()
        print()
        print("✓ Disconnected")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor CAN bus for gear position and gas pedal'
    )
    parser.add_argument('--port', default='COM4', 
                       help='Serial port (default: COM4)')
    parser.add_argument('--duration', type=int, default=30,
                       help='Duration in seconds (default: 30)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration)
    sys.exit(0 if success else 1)
