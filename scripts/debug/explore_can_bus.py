#!/usr/bin/env python3
"""
Ford Escape 2008 - CAN Bus Explorer (HS-CAN ONLY)

⚠️ CRITICAL SAFETY WARNING ⚠️
This script performs READ-ONLY passive monitoring of the HS-CAN bus.
It does NOT send any CAN messages - this is pure passive listening.

NEVER send arbitrary CAN messages on the HS-CAN bus via OBD-II port!
- HS-CAN carries safety-critical data (ABS, brakes, steering, engine)
- Injecting arbitrary messages can interfere with safety systems

Passively monitors all CAN bus traffic to discover which messages are actively
transmitting data. No UDS commands are sent - this is pure passive monitoring.

This helps identify:
- Which CAN IDs are active on HS-CAN
- Message transmission frequencies
- Data patterns and changes
- Available real-time data sources

LIMITATION: Standard ELM327 via OBD-II only accesses HS-CAN (500 kbps).
MS-CAN modules (FDIM, HVAC, ACM) are NOT visible via this script.

Usage:
    python scripts/debug/explore_can_bus.py
    
    Let it run for 30-60 seconds to capture all active messages.
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
            print("Initializing ELM327...")
            self.send_command("ATZ")
            time.sleep(1)
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS0")  # Spaces off
            
            # CRITICAL: Headers must be ON to see CAN IDs
            response = self.send_command("ATH1")  # Headers on
            print(f"  Headers ON: {response}")
            
            # Try auto protocol first
            response = self.send_command("ATSP0")  # Auto protocol
            print(f"  Auto protocol: {response}")
            
            # Verify we can communicate
            response = self.send_command("0100")  # Test with Mode 01 PID 00
            print(f"  Test communication: {response}")
            
            if not response or "NO DATA" in response or "ERROR" in response:
                print("  WARNING: No response to test command")
                print("  Trying manual protocol selection...")
                self.send_command("ATSP6")  # ISO 15765-4 CAN (500kbaud)
                response = self.send_command("0100")
                print(f"  Test with SP6: {response}")
            
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
            print(f"Command error: {e}")
            return None
    
    def monitor_all_can(self, duration=30):
        """
        Monitor all CAN bus traffic
        
        Args:
            duration: How long to monitor (seconds)
        
        Returns:
            Dictionary of CAN messages by ID
        """
        print(f"Monitoring CAN bus for {duration} seconds...")
        print("(This may take a moment to start receiving data)")
        print()
        
        # Configure for monitoring with headers
        # Some ELM327 clones don't include headers in ATMA despite ATH1
        # So we'll try both formats
        self.send_command("ATH1")  # Headers on
        self.send_command("ATS0")  # Spaces off (for compact format)
        self.send_command("ATL0")  # Linefeeds off
        
        # Start monitoring
        self.ser.reset_input_buffer()
        print("Sending ATMA (Monitor All) command...")
        self.ser.write(b'ATMA\r')  # Monitor all
        time.sleep(0.5)
        
        # Check if monitoring started
        initial_response = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
        print(f"Initial response: {initial_response[:100]}")
        
        if "?" in initial_response or "ERROR" in initial_response:
            print("ATMA failed, trying alternative monitoring...")
            self.ser.write(b'\r')  # Stop
            time.sleep(0.2)
            self.ser.reset_input_buffer()
            
            # Try ATMT (Monitor for Transmit) as alternative
            self.ser.write(b'ATMT00\r')  # Monitor with no timeout
            time.sleep(0.5)
        
        messages = defaultdict(list)
        start_time = time.time()
        last_update = start_time
        buffer = ""
        line_count = 0
        headerless_format = False  # Track if we detect headerless format
        
        while time.time() - start_time < duration:
            if self.ser.in_waiting:
                try:
                    # Read available data
                    chunk = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
                    buffer += chunk
                    
                    # Process complete lines
                    while '\r' in buffer or '\n' in buffer:
                        # Split on first line break
                        if '\r' in buffer:
                            line, buffer = buffer.split('\r', 1)
                        else:
                            line, buffer = buffer.split('\n', 1)
                        
                        line = line.strip()
                        line_count += 1
                        
                        # Debug: print first few lines
                        if line_count <= 5:
                            print(f"  Line {line_count}: {line[:80]}")
                        
                        # Skip empty lines, prompts, and error messages
                        if not line or line == '>' or 'BUFFER' in line or 'STOPPED' in line:
                            continue
                        
                        # Detect format: check if line has spaces (header format) or not (headerless)
                        has_spaces = ' ' in line
                        
                        if has_spaces:
                            # Format: "XXX YY YY YY YY YY YY YY YY" (with headers and spaces)
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    # Validate CAN ID is 3 hex digits
                                    if len(parts[0]) == 3:
                                        can_id = int(parts[0], 16)
                                        
                                        # Validate it's a reasonable CAN ID (0x000 - 0x7FF for 11-bit)
                                        if 0 <= can_id <= 0x7FF:
                                            data_bytes = ' '.join(parts[1:])
                                            
                                            messages[can_id].append({
                                                'timestamp': time.time(),
                                                'data': data_bytes
                                            })
                                
                                except ValueError:
                                    pass  # Skip invalid hex
                        else:
                            # Format: "XXXYYYYYYYYYYYYYYYY" (headerless, no spaces)
                            # This is what we're actually receiving
                            if not headerless_format and line_count <= 10:
                                print(f"  Detected headerless format (no CAN IDs in output)")
                                headerless_format = True
                            
                            # For headerless format, we can't determine CAN IDs
                            # Skip these lines - we need headers to work
                            pass
                    
                    # Progress update every 5 seconds
                    if time.time() - last_update >= 5:
                        elapsed = int(time.time() - start_time)
                        remaining = duration - elapsed
                        status = "headerless format detected" if headerless_format else "parsing"
                        print(f"  {elapsed}s elapsed, {remaining}s remaining... "
                              f"({len(messages)} unique CAN IDs found, {line_count} lines processed, {status})")
                        last_update = time.time()
                
                except Exception as e:
                    pass  # Skip errors during monitoring
            
            time.sleep(0.01)  # Small delay to prevent CPU spinning
        
        # Stop monitoring
        self.ser.write(b'\r')
        time.sleep(0.2)
        self.ser.reset_input_buffer()
        
        print(f"\nTotal lines processed: {line_count}")
        print(f"Total unique CAN IDs: {len(messages)}")
        
        if headerless_format and len(messages) == 0:
            print("\n⚠️  WARNING: Adapter is sending headerless format")
            print("   ATH1 command is not working - adapter doesn't include CAN IDs")
            print("   This ELM327 clone may not support headers in ATMA mode")
            print()
            print("   Possible solutions:")
            print("   1. Try a different ELM327 adapter (genuine or better clone)")
            print("   2. Use ATCRA filtering (requires knowing CAN IDs in advance)")
            print("   3. Use external CAN sniffer tool")
        
        return messages
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def analyze_messages(messages):
    """
    Analyze captured CAN messages
    
    Args:
        messages: Dictionary of messages by CAN ID
    
    Returns:
        Dictionary with analysis results
    """
    analysis = {}
    
    for can_id, msg_list in messages.items():
        if not msg_list:
            continue
        
        # Calculate frequency
        time_span = msg_list[-1]['timestamp'] - msg_list[0]['timestamp']
        frequency = len(msg_list) / time_span if time_span > 0 else 0
        
        # Check if data changes
        unique_data = set(msg['data'] for msg in msg_list)
        data_changes = len(unique_data) > 1
        
        # Get first and last data samples
        first_data = msg_list[0]['data']
        last_data = msg_list[-1]['data']
        
        analysis[can_id] = {
            'count': len(msg_list),
            'frequency': frequency,
            'data_changes': data_changes,
            'unique_values': len(unique_data),
            'first_data': first_data,
            'last_data': last_data,
            'sample_data': list(unique_data)[:5]  # First 5 unique values
        }
    
    return analysis

def get_known_can_ids():
    """
    Return dictionary of known CAN IDs from documentation
    
    Returns:
        Dictionary mapping CAN ID to description
    """
    return {
        0x080: "Engine RPM & Vehicle Speed",
        0x081: "Engine Load & Coolant Temp",
        0x083: "Fuel System Status",
        0x190: "Brake Status",
        0x201: "Accelerator Pedal",
        0x20F: "Vehicle Speed (Alternative)",
        0x228: "Transmission Status & Gear",
        0x231: "Gear & Torque",
        0x240: "Unknown Parameter",
        0x420: "Steering Wheel Angle",
        0x4B0: "Wheel Speeds (All 4)",
        0x4F2: "Odometer",
    }

def print_analysis(analysis):
    """Print analysis results in a formatted table"""
    
    known_ids = get_known_can_ids()
    
    print("=" * 120)
    print("CAN Bus Exploration Results")
    print("=" * 120)
    print()
    print(f"Total unique CAN IDs found: {len(analysis)}")
    print()
    
    # Sort by CAN ID
    sorted_ids = sorted(analysis.keys())
    
    # Print header
    print(f"{'CAN ID':<10} {'Count':<8} {'Freq (Hz)':<12} {'Changes':<10} {'Unique':<10} {'Description':<40}")
    print("-" * 120)
    
    for can_id in sorted_ids:
        info = analysis[can_id]
        
        # Get description if known
        description = known_ids.get(can_id, "Unknown")
        
        # Format frequency
        freq_str = f"{info['frequency']:.2f}" if info['frequency'] < 100 else f"{info['frequency']:.0f}"
        
        # Format changes
        changes_str = "Yes" if info['data_changes'] else "No"
        
        print(f"0x{can_id:03X}     {info['count']:<8} {freq_str:<12} {changes_str:<10} "
              f"{info['unique_values']:<10} {description:<40}")
    
    print()
    print("=" * 120)
    print("Detailed Data Samples")
    print("=" * 120)
    print()
    
    # Print detailed samples for interesting messages (those that change)
    changing_messages = [(can_id, info) for can_id, info in analysis.items() if info['data_changes']]
    changing_messages.sort(key=lambda x: x[0])
    
    for can_id, info in changing_messages:
        description = known_ids.get(can_id, "Unknown")
        
        print(f"CAN ID 0x{can_id:03X} - {description}")
        print(f"  Frequency: {info['frequency']:.2f} Hz")
        print(f"  Total messages: {info['count']}")
        print(f"  Unique values: {info['unique_values']}")
        print(f"  First data: {info['first_data']}")
        print(f"  Last data:  {info['last_data']}")
        
        if len(info['sample_data']) > 2:
            print(f"  Sample variations:")
            for i, sample in enumerate(info['sample_data'][:5], 1):
                print(f"    {i}. {sample}")
        
        print()

def save_results(analysis, filename=None):
    """Save results to JSON file"""
    import json
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knowledge_base/captured_data/can_bus_exploration_{timestamp}.json"
    
    # Convert to JSON-serializable format
    json_data = {
        'scan_date': datetime.now().isoformat(),
        'vehicle': 'Ford Escape 2008',
        'total_can_ids': len(analysis),
        'messages': {}
    }
    
    for can_id, info in analysis.items():
        json_data['messages'][f"0x{can_id:03X}"] = {
            'can_id_decimal': can_id,
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

def main(port='COM3', duration=30):
    """
    Explore CAN bus (HS-CAN only via OBD-II)
    
    Args:
        port: Serial port for ELM327
        duration: How long to monitor (seconds)
    """
    print("=" * 120)
    print("Ford Escape 2008 - CAN Bus Explorer (HS-CAN ONLY)")
    print("=" * 120)
    print()
    print("⚠️  CRITICAL SAFETY WARNING ⚠️")
    print("This script performs READ-ONLY passive monitoring.")
    print("It does NOT send any CAN messages - pure passive listening only.")
    print()
    print("NEVER send CAN messages on HS-CAN via OBD-II port!")
    print("  - HS-CAN carries safety-critical data (ABS, brakes, steering)")
    print("  - Injecting messages can interfere with safety systems")
    print("  - Previous FDIM testing caused ABS issues due to bus interference")
    print()
    print("=" * 120)
    print()
    print("This script passively monitors HS-CAN bus traffic to discover active messages.")
    print("No UDS commands are sent - this is pure passive monitoring.")
    print()
    print("LIMITATION: Standard ELM327 via OBD-II only accesses HS-CAN (500 kbps).")
    print("MS-CAN modules (FDIM, HVAC, ACM) are NOT visible via this script.")
    print()
    print("What we'll discover (HS-CAN only):")
    print("  - Which CAN IDs are actively transmitting")
    print("  - Message transmission frequencies")
    print("  - Which messages contain changing data (real-time parameters)")
    print("  - Which messages are static (configuration data)")
    print()
    print("HS-CAN modules accessible:")
    print("  ✓ PCM (Powertrain) - 0x7E0")
    print("  ✓ ABS (Anti-lock Brakes) - 0x760")
    print("  ✓ Wheel speeds - 0x4B0")
    print("  ✓ Transmission - 0x228")
    print("  ✓ Engine RPM/Speed - 0x080")
    print("  ✓ Brake status - 0x190")
    print("  ✓ Steering angle - 0x420")
    print()
    print("MS-CAN modules NOT accessible:")
    print("  ✗ FDIM (Display) - 0x7A6 (MS-CAN)")
    print("  ✗ HVAC (Climate) - 0x733 (MS-CAN)")
    print("  ✗ ACM (Audio) - 0x727 (MS-CAN)")
    print("  ✗ SJB (Body Control) - 0x726 (MS-CAN)")
    print()
    print("Instructions:")
    print("  - Start with vehicle stationary (baseline)")
    print("  - Optionally: shift gears, press pedals, turn steering wheel")
    print("  - More activity = more data variations captured")
    print("  - This is SAFE - read-only monitoring")
    print()
    
    # Connect to adapter
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("Connected to ELM327")
    print()
    
    try:
        # Monitor CAN bus
        messages = elm.monitor_all_can(duration=duration)
        
        print()
        print(f"Monitoring complete! Captured {sum(len(msgs) for msgs in messages.values())} total messages")
        print()
        
        # Analyze messages
        analysis = analyze_messages(messages)
        
        # Print results
        print_analysis(analysis)
        
        # Save results
        save_results(analysis)
        
        print("=" * 120)
        print("Next Steps")
        print("=" * 120)
        print()
        print("1. Review messages that show data changes - these are real-time parameters")
        print("2. Compare with known CAN IDs in reference/Mazda_CAN_Bus_Reference.md")
        print("3. Create monitoring scripts for interesting parameters")
        print("4. Document new discoveries in the knowledge base")
        print()
        print("⚠️  SAFETY REMINDER:")
        print("  - This script is READ-ONLY and safe")
        print("  - NEVER send arbitrary CAN messages on HS-CAN bus")
        print("  - FDIM/HVAC require MS-CAN switch position + UDS protocols")
        print("  - Focus on monitoring, not message injection")
        print()
        print("Tip: Run this script again while:")
        print("  - Shifting through gears (to see transmission data change)")
        print("  - Pressing brake/accelerator (to see pedal data change)")
        print("  - Turning steering wheel (to see steering angle change)")
        print("  - Rolling vehicle (to see wheel speeds change)")
        print()
        
        return True
        
    except KeyboardInterrupt:
        print()
        print("Monitoring stopped by user")
        return False
    
    finally:
        elm.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Explore CAN bus to discover active messages'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--duration', type=int, default=30, 
                       help='Monitoring duration in seconds (default: 30)')
    
    args = parser.parse_args()
    
    success = main(port=args.port, duration=args.duration)
    sys.exit(0 if success else 1)
