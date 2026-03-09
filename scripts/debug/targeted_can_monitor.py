#!/usr/bin/env python3
"""
Ford Escape 2008 - Targeted CAN Bus Monitor

Uses ATCRA (CAN Receive Address) filtering to monitor specific CAN IDs.
This workaround is needed because some ELM327 clones don't include headers
in ATMA (Monitor All) output, even when ATH1 is set.

With ATCRA filtering, the adapter properly includes headers in the output.

⚠️ SAFETY: This is READ-ONLY passive monitoring - no messages are sent.

Usage:
    python scripts/debug/targeted_can_monitor.py
    
    Monitors known CAN IDs sequentially for 5 seconds each.
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
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS1")  # Spaces ON (required for ATCRA parsing)
            self.send_command("ATH1")  # Headers on
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
    
    def monitor_can_id(self, can_id, duration=5):
        """
        Monitor a specific CAN ID using ATCRA filtering
        
        Args:
            can_id: CAN ID to monitor (integer, e.g., 0x080)
            duration: How long to monitor (seconds)
        
        Returns:
            List of captured messages
        """
        # Set CAN Receive Address filter
        can_id_hex = f"{can_id:03X}"
        self.send_command(f"ATCRA{can_id_hex}")
        
        # Ensure headers are on
        self.send_command("ATH1")
        
        # Start monitoring
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
                
                # Process complete lines
                while '\r' in buffer or '\n' in buffer:
                    if '\r' in buffer:
                        line, buffer = buffer.split('\r', 1)
                    else:
                        line, buffer = buffer.split('\n', 1)
                    
                    line = line.strip()
                    
                    # Skip empty lines and prompts
                    if not line or line == '>' or 'BUFFER' in line or 'STOPPED' in line:
                        continue
                    
                    # Parse message
                    # Expected format with ATCRA: "XXX YY YY YY YY YY YY YY YY"
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            if len(parts[0]) == 3:
                                msg_can_id = int(parts[0], 16)
                                data_bytes = ' '.join(parts[1:])
                                
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
        
        # Clear filter
        self.send_command("ATCRA")
        
        return messages
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def get_target_can_ids():
    """
    Return list of known CAN IDs to monitor
    
    Returns:
        List of tuples: (can_id, description)
    """
    return [
        (0x080, "Engine RPM & Vehicle Speed"),
        (0x081, "Engine Load & Coolant Temp"),
        (0x083, "Fuel System Status"),
        (0x190, "Brake Status"),
        (0x201, "Accelerator Pedal"),
        (0x20F, "Vehicle Speed (Alternative)"),
        (0x228, "Transmission Status & Gear"),
        (0x231, "Gear & Torque"),
        (0x240, "Unknown Parameter"),
        (0x420, "Steering Wheel Angle"),
        (0x4B0, "Wheel Speeds (All 4)"),
        (0x4F2, "Odometer"),
    ]

def analyze_messages(messages_by_id):
    """Analyze captured messages"""
    analysis = {}
    
    for can_id, msg_list in messages_by_id.items():
        if not msg_list:
            continue
        
        # Calculate frequency
        time_span = msg_list[-1]['timestamp'] - msg_list[0]['timestamp']
        frequency = len(msg_list) / time_span if time_span > 0 else 0
        
        # Check if data changes
        unique_data = set(msg['data'] for msg in msg_list)
        data_changes = len(unique_data) > 1
        
        analysis[can_id] = {
            'count': len(msg_list),
            'frequency': frequency,
            'data_changes': data_changes,
            'unique_values': len(unique_data),
            'first_data': msg_list[0]['data'],
            'last_data': msg_list[-1]['data'],
            'sample_data': list(unique_data)[:5]
        }
    
    return analysis

def main(port='COM3', duration_per_id=5):
    """
    Monitor known CAN IDs using targeted filtering
    
    Args:
        port: Serial port for ELM327
        duration_per_id: How long to monitor each CAN ID (seconds)
    """
    print("=" * 80)
    print("Ford Escape 2008 - Targeted CAN Bus Monitor")
    print("=" * 80)
    print()
    print("This script uses ATCRA filtering to monitor specific CAN IDs.")
    print("This workaround is needed because ATMA doesn't include headers on some adapters.")
    print()
    print("⚠️  READ-ONLY monitoring - no messages are sent")
    print()
    
    # Connect
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("Connected to ELM327")
    print()
    
    # Get target CAN IDs
    targets = get_target_can_ids()
    
    print(f"Will monitor {len(targets)} known CAN IDs")
    print(f"Duration per ID: {duration_per_id} seconds")
    print(f"Total time: ~{len(targets) * duration_per_id} seconds")
    print()
    
    # Monitor each CAN ID
    all_messages = defaultdict(list)
    
    try:
        for i, (can_id, description) in enumerate(targets, 1):
            print(f"[{i}/{len(targets)}] Monitoring 0x{can_id:03X} - {description}...", end='', flush=True)
            
            messages = elm.monitor_can_id(can_id, duration=duration_per_id)
            
            if messages:
                all_messages[can_id].extend(messages)
                print(f" {len(messages)} messages")
            else:
                print(" no data")
        
        print()
        print("=" * 80)
        print("Monitoring Complete")
        print("=" * 80)
        print()
        
        # Analyze results
        analysis = analyze_messages(all_messages)
        
        if not analysis:
            print("⚠️  No CAN messages captured")
            print()
            print("Possible causes:")
            print("  - Vehicle not in RUN mode or engine not running")
            print("  - Adapter not properly connected")
            print("  - ATCRA filtering not supported by this adapter")
            print()
            return False
        
        # Print results
        print(f"Successfully captured data from {len(analysis)} CAN IDs")
        print()
        print(f"{'CAN ID':<10} {'Count':<8} {'Freq (Hz)':<12} {'Changes':<10} {'Description':<40}")
        print("-" * 80)
        
        target_dict = dict(targets)
        
        for can_id in sorted(analysis.keys()):
            info = analysis[can_id]
            description = target_dict.get(can_id, "Unknown")
            
            freq_str = f"{info['frequency']:.2f}" if info['frequency'] < 100 else f"{info['frequency']:.0f}"
            changes_str = "Yes" if info['data_changes'] else "No"
            
            print(f"0x{can_id:03X}     {info['count']:<8} {freq_str:<12} {changes_str:<10} {description:<40}")
        
        print()
        print("=" * 80)
        print("Detailed Data Samples")
        print("=" * 80)
        print()
        
        # Show details for messages that change
        for can_id in sorted(analysis.keys()):
            info = analysis[can_id]
            if info['data_changes']:
                description = target_dict.get(can_id, "Unknown")
                
                print(f"CAN ID 0x{can_id:03X} - {description}")
                print(f"  Frequency: {info['frequency']:.2f} Hz")
                print(f"  Total messages: {info['count']}")
                print(f"  Unique values: {info['unique_values']}")
                print(f"  First: {info['first_data']}")
                print(f"  Last:  {info['last_data']}")
                
                if len(info['sample_data']) > 2:
                    print(f"  Samples:")
                    for sample in info['sample_data'][:5]:
                        print(f"    {sample}")
                
                print()
        
        # Save results
        save_results(analysis, target_dict)
        
        return True
        
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        return False
    
    finally:
        elm.close()

def save_results(analysis, descriptions):
    """Save results to JSON file"""
    import json
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"knowledge_base/captured_data/targeted_can_monitor_{timestamp}.json"
    
    json_data = {
        'scan_date': datetime.now().isoformat(),
        'vehicle': 'Ford Escape 2008',
        'method': 'ATCRA targeted monitoring',
        'total_can_ids': len(analysis),
        'messages': {}
    }
    
    for can_id, info in analysis.items():
        json_data['messages'][f"0x{can_id:03X}"] = {
            'can_id_decimal': can_id,
            'description': descriptions.get(can_id, "Unknown"),
            'count': info['count'],
            'frequency_hz': round(info['frequency'], 2),
            'data_changes': info['data_changes'],
            'unique_values': info['unique_values'],
            'first_data': info['first_data'],
            'last_data': info['last_data'],
            'sample_data': info['sample_data']
        }
    
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"Results saved to: {filename}")
    print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Monitor specific CAN IDs using ATCRA filtering'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--duration', type=int, default=5,
                       help='Duration per CAN ID in seconds (default: 5)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration_per_id=args.duration)
    sys.exit(0 if success else 1)
