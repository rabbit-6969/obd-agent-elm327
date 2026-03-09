#!/usr/bin/env python3
"""
Ford Escape 2008 - FDIM Protocol Discovery

This script helps discover the correct FDIM display protocol by:
1. Monitoring CAN bus traffic while radio displays track names
2. Identifying which CAN IDs contain ASCII text
3. Analyzing message format and structure
4. Testing discovered patterns

Usage:
    Step 1: Monitor while radio is playing
    python scripts/debug/discover_fdim_protocol.py --mode monitor
    
    Step 2: Test discovered CAN IDs
    python scripts/debug/discover_fdim_protocol.py --mode test --id 0x415
"""

import serial
import time
import sys
import argparse
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
            self.send_command("ATS0")  # Spaces off
            self.send_command("ATH1")  # Headers on (CRITICAL)
            self.send_command("ATSP6")  # ISO 15765-4 CAN (500kbaud)
            self.send_command("ATCAF0")  # Turn off CAN auto-formatting
            
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
        """Monitor all CAN bus traffic"""
        print(f"Monitoring CAN bus for {duration} seconds...")
        print()
        
        # Start monitoring
        self.ser.reset_input_buffer()
        self.ser.write(b'ATMA\r')  # Monitor all
        
        messages = defaultdict(list)
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode('ascii', errors='ignore').strip()
                    
                    if line and len(line) >= 3:
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                can_id = int(parts[0], 16)
                                data_bytes = ' '.join(parts[1:])
                                
                                messages[can_id].append({
                                    'timestamp': time.time(),
                                    'data': data_bytes
                                })
                            except ValueError:
                                pass
                
                except Exception:
                    pass
        
        # Stop monitoring
        self.ser.write(b'\r')
        time.sleep(0.1)
        self.ser.reset_input_buffer()
        
        return messages
    
    def send_raw_can(self, can_id, data_bytes):
        """
        Send raw CAN message
        
        Args:
            can_id: CAN ID (e.g., 0x415)
            data_bytes: List of bytes to send
        
        Returns:
            Response from ELM327
        """
        # Set CAN ID for transmission
        self.send_command(f"ATSH{can_id:03X}")
        
        # Format data bytes
        hex_str = ' '.join(f"{b:02X}" for b in data_bytes)
        
        # Send message
        response = self.send_command(hex_str)
        
        return response
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

def contains_ascii_text(data_hex):
    """
    Check if data contains readable ASCII text
    
    Args:
        data_hex: String of hex bytes
    
    Returns:
        (bool, str) - (contains_text, decoded_text)
    """
    try:
        bytes_list = [int(b, 16) for b in data_hex.split()]
        
        # Try to decode as ASCII
        text = ''
        printable_count = 0
        
        for byte_val in bytes_list:
            if 32 <= byte_val <= 126:  # Printable ASCII range
                text += chr(byte_val)
                printable_count += 1
            else:
                text += '.'
        
        # Consider it text if >50% printable
        is_text = printable_count >= len(bytes_list) * 0.5
        
        return is_text, text
    
    except Exception:
        return False, ''

def analyze_for_fdim(messages):
    """
    Analyze captured messages to find FDIM candidates
    
    Args:
        messages: Dictionary of messages by CAN ID
    
    Returns:
        List of candidate CAN IDs with ASCII text
    """
    candidates = []
    
    print("=" * 80)
    print("Analyzing for FDIM Display Messages")
    print("=" * 80)
    print()
    print("Looking for CAN messages containing ASCII text...")
    print()
    
    for can_id, msg_list in sorted(messages.items()):
        if not msg_list:
            continue
        
        # Check if any messages contain ASCII text
        text_messages = []
        
        for msg in msg_list:
            is_text, decoded = contains_ascii_text(msg['data'])
            if is_text:
                text_messages.append({
                    'data': msg['data'],
                    'text': decoded
                })
        
        if text_messages:
            # This CAN ID contains ASCII text - likely FDIM!
            candidates.append({
                'can_id': can_id,
                'count': len(text_messages),
                'samples': text_messages[:5]  # First 5 samples
            })
    
    return candidates

def print_fdim_candidates(candidates):
    """Print FDIM candidate analysis"""
    
    if not candidates:
        print("No CAN messages with ASCII text found.")
        print()
        print("Troubleshooting:")
        print("  1. Make sure radio is playing and displaying track names")
        print("  2. Try changing tracks to generate more traffic")
        print("  3. Check if display is showing text (not just clock)")
        print("  4. Verify ELM327 is connected to correct CAN bus")
        print()
        return
    
    print(f"Found {len(candidates)} CAN ID(s) with ASCII text:")
    print()
    
    for candidate in candidates:
        can_id = candidate['can_id']
        print(f"CAN ID: 0x{can_id:03X}")
        print(f"  Messages with text: {candidate['count']}")
        print(f"  Sample messages:")
        
        for i, sample in enumerate(candidate['samples'], 1):
            print(f"    {i}. Hex: {sample['data']}")
            print(f"       Text: '{sample['text']}'")
        
        print()
    
    print("=" * 80)
    print("Recommendations")
    print("=" * 80)
    print()
    
    if len(candidates) == 1:
        can_id = candidates[0]['can_id']
        print(f"Single candidate found: 0x{can_id:03X}")
        print()
        print("Next steps:")
        print(f"  1. Test writing to this CAN ID:")
        print(f"     python scripts/debug/discover_fdim_protocol.py --mode test --id 0x{can_id:03X}")
        print()
    else:
        print(f"Multiple candidates found. Test each one:")
        for candidate in candidates:
            can_id = candidate['can_id']
            print(f"  python scripts/debug/discover_fdim_protocol.py --mode test --id 0x{can_id:03X}")
        print()

def test_fdim_write(elm, can_id, test_text="TEST"):
    """
    Test writing to FDIM display
    
    Args:
        elm: ELM327 instance
        can_id: CAN ID to test
        test_text: Text to display
    """
    print("=" * 80)
    print(f"Testing FDIM Write to CAN ID 0x{can_id:03X}")
    print("=" * 80)
    print()
    print(f"Test text: '{test_text}'")
    print()
    print("We'll try multiple message formats:")
    print("  1. Plain ASCII (no header)")
    print("  2. Header 0x02 + ASCII")
    print("  3. Header 0x03 + ASCII")
    print("  4. Header 0x10 + ASCII")
    print()
    
    # Convert text to bytes
    text_bytes = [ord(c) for c in test_text]
    
    # Test patterns
    patterns = [
        ("Plain ASCII", text_bytes),
        ("Header 0x02", [0x02] + text_bytes),
        ("Header 0x03", [0x03] + text_bytes),
        ("Header 0x10", [0x10] + text_bytes),
        ("Header 0x00", [0x00] + text_bytes),
        ("Header 0x01", [0x01] + text_bytes),
    ]
    
    for pattern_name, data_bytes in patterns:
        print(f"Testing: {pattern_name}")
        hex_str = ' '.join(f"{b:02X}" for b in data_bytes)
        print(f"  Message: {hex_str}")
        
        # Send message 10 times (5 seconds at 500ms interval)
        for i in range(10):
            response = elm.send_raw_can(can_id, data_bytes)
            time.sleep(0.5)
        
        print(f"  Sent 10 times over 5 seconds")
        print()
        
        # Ask user if it worked
        user_input = input(f"  Did '{test_text}' appear on the display? (y/n): ").strip().lower()
        
        if user_input == 'y':
            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print()
            print(f"Working configuration found:")
            print(f"  CAN ID: 0x{can_id:03X}")
            print(f"  Format: {pattern_name}")
            print(f"  Message: {hex_str}")
            print()
            return True
        
        print()
    
    print("=" * 80)
    print("No working configuration found")
    print("=" * 80)
    print()
    print("Possible reasons:")
    print("  1. Wrong CAN ID - try monitoring to find correct ID")
    print("  2. FDIM requires specific message length")
    print("  3. FDIM may be on MS-CAN (125kbps) instead of HS-CAN (500kbps)")
    print("  4. Display may require activation sequence first")
    print("  5. Your vehicle may not support FDIM control via CAN")
    print()
    
    return False

def mode_monitor(port, duration):
    """Monitor CAN bus to discover FDIM protocol"""
    
    print("=" * 80)
    print("Ford Escape 2008 - FDIM Protocol Discovery (Monitor Mode)")
    print("=" * 80)
    print()
    print("This will monitor CAN bus traffic to find FDIM display messages.")
    print()
    print("Instructions:")
    print("  1. Make sure radio is ON and playing")
    print("  2. Change tracks or stations to generate display updates")
    print("  3. Watch for track names or station info on display")
    print("  4. Let this script run for the full duration")
    print()
    print(f"Monitoring for {duration} seconds...")
    print()
    
    # Connect
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
        print(f"Captured {sum(len(msgs) for msgs in messages.values())} total messages")
        print()
        
        # Analyze for FDIM
        candidates = analyze_for_fdim(messages)
        
        # Print results
        print_fdim_candidates(candidates)
        
        return True
    
    finally:
        elm.close()

def mode_test(port, can_id, text):
    """Test writing to FDIM display"""
    
    # Connect
    elm = ELM327(port=port)
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("Connected to ELM327")
    print()
    
    try:
        # Test writing
        success = test_fdim_write(elm, can_id, text)
        return success
    
    finally:
        elm.close()

def mode_scan(port):
    """Scan common FDIM CAN IDs"""
    
    print("=" * 80)
    print("Ford Escape 2008 - FDIM CAN ID Scanner")
    print("=" * 80)
    print()
    print("Scanning common FDIM CAN IDs...")
    print()
    
    # Common FDIM IDs to test
    test_ids = [
        0x415, 0x416, 0x417, 0x418,  # Common FDIM IDs
        0x7A6,  # FDIM diagnostic ID (from Valasek & Miller)
        0x3B5, 0x3B6, 0x3B7,  # Alternative IDs
    ]
    
    # Connect
    elm = ELM327(port=port)
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("Connected to ELM327")
    print()
    
    try:
        for can_id in test_ids:
            print(f"Testing CAN ID 0x{can_id:03X}...")
            
            # Try sending simple test message
            test_bytes = [0x02, ord('T'), ord('E'), ord('S'), ord('T')]
            
            for i in range(5):
                elm.send_raw_can(can_id, test_bytes)
                time.sleep(0.5)
            
            user_input = input(f"  Did 'TEST' appear on display? (y/n): ").strip().lower()
            
            if user_input == 'y':
                print()
                print(f"SUCCESS! CAN ID 0x{can_id:03X} works!")
                print()
                return True
            
            print()
        
        print("No working CAN ID found in scan.")
        print()
        print("Try monitor mode to discover the actual FDIM CAN ID:")
        print("  python scripts/debug/discover_fdim_protocol.py --mode monitor")
        print()
        
        return False
    
    finally:
        elm.close()

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Discover FDIM display protocol',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  monitor - Monitor CAN bus to find FDIM messages (run while radio is playing)
  test    - Test writing to a specific CAN ID
  scan    - Scan common FDIM CAN IDs

Examples:
  # Monitor CAN bus while radio displays track names
  python scripts/debug/discover_fdim_protocol.py --mode monitor --duration 60
  
  # Test specific CAN ID
  python scripts/debug/discover_fdim_protocol.py --mode test --id 0x415 --text "HELLO"
  
  # Scan common FDIM IDs
  python scripts/debug/discover_fdim_protocol.py --mode scan

Workflow:
  1. Run in monitor mode while radio is playing
  2. Script will identify CAN IDs containing ASCII text
  3. Test identified CAN IDs using test mode
  4. Document working configuration
        """
    )
    
    parser.add_argument('--mode', choices=['monitor', 'test', 'scan'], 
                       default='monitor',
                       help='Operation mode (default: monitor)')
    parser.add_argument('--port', default='COM3', 
                       help='Serial port (default: COM3)')
    parser.add_argument('--duration', type=int, default=30,
                       help='Monitor duration in seconds (default: 30)')
    parser.add_argument('--id', type=lambda x: int(x, 0), default=0x415,
                       dest='can_id',
                       help='CAN ID to test (hex, default: 0x415)')
    parser.add_argument('--text', default='TEST',
                       help='Text to display in test mode (default: TEST)')
    
    args = parser.parse_args()
    
    if args.mode == 'monitor':
        success = mode_monitor(args.port, args.duration)
    elif args.mode == 'test':
        success = mode_test(args.port, args.can_id, args.text)
    elif args.mode == 'scan':
        success = mode_scan(args.port)
    else:
        print(f"Unknown mode: {args.mode}")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
