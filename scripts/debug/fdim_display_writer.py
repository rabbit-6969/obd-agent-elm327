#!/usr/bin/env python3
"""
Ford Escape 2008 - FDIM Display Writer

Writes custom text to the factory FDIM (Front Display Interface Module) display.
The FDIM acts as a slave on the CAN bus and can display custom messages.

Features:
- Write custom text to factory display
- Continuous message transmission (required for persistence)
- Configurable update interval
- Support for different FDIM CAN IDs

Usage:
    python scripts/debug/fdim_display_writer.py --text "HELLO WORLD"
    python scripts/debug/fdim_display_writer.py --text "GEAR: D3" --duration 30
    python scripts/debug/fdim_display_writer.py --text "DIAGNOSTIC" --id 0x417

Safety Warning:
    Custom displays can be distracting while driving. Always test in a safe
    environment (parked vehicle) first. Comply with local laws regarding
    vehicle displays and driver distraction.
"""

import serial
import time
import sys
import argparse
from datetime import datetime

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
            self.send_command("ATH0")  # Headers off for sending
            self.send_command("ATSP6")  # ISO 15765-4 CAN (500kbaud)
            
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
    
    def close(self):
        """Close connection"""
        if self.ser:
            self.ser.close()

class FDIMDisplay:
    """Ford FDIM Display Controller"""
    
    def __init__(self, elm, display_id=0x415, header=0x02):
        """
        Initialize FDIM display controller
        
        Args:
            elm: ELM327 instance
            display_id: CAN ID for FDIM (0x415 or 0x417)
            header: Header byte for messages (typically 0x02)
        """
        self.elm = elm
        self.display_id = display_id
        self.header = header
        self.running = False
        self.max_length = 16  # Maximum display width
    
    def setup(self):
        """Setup CAN transmission for FDIM"""
        # Set CAN ID for transmission
        result = self.elm.send_command(f"ATSH{self.display_id:03X}")
        return result is not None
    
    def format_message(self, text):
        """
        Format text message for FDIM display
        
        Args:
            text: Text to display
        
        Returns:
            Hex string ready to send
        """
        # Truncate if too long
        text = text[:self.max_length]
        
        # Pad with spaces if too short (optional, for consistent width)
        # text = text.ljust(self.max_length)
        
        # Convert to hex bytes
        hex_bytes = [f"{self.header:02X}"]
        for char in text:
            hex_bytes.append(f"{ord(char):02X}")
        
        return ' '.join(hex_bytes)
    
    def write_text(self, text, duration=None, interval=0.5):
        """
        Write text to FDIM display
        
        Args:
            text: Text to display (max 16 characters)
            duration: How long to display (seconds), None = continuous
            interval: Update interval in seconds (default 0.5)
        
        Returns:
            True if successful, False otherwise
        """
        message = self.format_message(text)
        
        print(f"Writing to FDIM display (ID: 0x{self.display_id:03X}):")
        print(f"  Text: '{text}'")
        print(f"  Message: {message}")
        print(f"  Interval: {interval}s")
        if duration:
            print(f"  Duration: {duration}s")
        else:
            print(f"  Duration: Continuous (press Ctrl+C to stop)")
        print()
        
        self.running = True
        start_time = time.time()
        update_count = 0
        
        try:
            while self.running:
                # Send message
                response = self.elm.send_command(message)
                update_count += 1
                
                # Print status every 10 updates
                if update_count % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"  Updates sent: {update_count} (elapsed: {elapsed:.1f}s)")
                
                # Wait for next update
                time.sleep(interval)
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break
            
            print()
            print(f"Display complete. Total updates: {update_count}")
            return True
        
        except KeyboardInterrupt:
            print()
            print(f"Stopped by user. Total updates: {update_count}")
            return True
        
        except Exception as e:
            print(f"Error writing to display: {e}")
            return False
        
        finally:
            self.running = False
    
    def stop(self):
        """Stop writing to display"""
        self.running = False

def main(port='COM3', text='TEST', duration=None, display_id=0x415, 
         header=0x02, interval=0.5):
    """
    Write text to FDIM display
    
    Args:
        port: Serial port for ELM327
        text: Text to display
        duration: How long to display (seconds), None = continuous
        display_id: CAN ID for FDIM (0x415 or 0x417)
        header: Header byte (typically 0x02)
        interval: Update interval in seconds
    """
    print("=" * 80)
    print("Ford Escape 2008 - FDIM Display Writer")
    print("=" * 80)
    print()
    print("This script writes custom text to the factory FDIM display.")
    print()
    print("SAFETY WARNING:")
    print("  - Custom displays can be distracting while driving")
    print("  - Always test in a safe environment (parked vehicle) first")
    print("  - Comply with local laws regarding vehicle displays")
    print()
    print("Technical Details:")
    print("  - FDIM acts as a slave on the CAN bus")
    print("  - Messages must be sent continuously (every 500ms)")
    print("  - Display will timeout and revert to default if updates stop")
    print()
    
    # Connect to adapter
    elm = ELM327(port=port)
    
    if not elm.connect():
        print("Failed to connect to ELM327")
        return False
    
    print("Connected to ELM327")
    print()
    
    # Create FDIM display controller
    display = FDIMDisplay(elm, display_id=display_id, header=header)
    
    if not display.setup():
        print("Failed to setup FDIM display")
        elm.close()
        return False
    
    print("FDIM display ready")
    print()
    
    try:
        # Write text to display
        success = display.write_text(text, duration=duration, interval=interval)
        
        print()
        print("=" * 80)
        print("FDIM Display Writer Complete")
        print("=" * 80)
        print()
        
        if success:
            print("Text was successfully written to the display.")
            print()
            print("Note: The display will revert to default after ~1-2 seconds")
            print("      once updates stop.")
        else:
            print("Failed to write text to display.")
        
        print()
        
        return success
    
    finally:
        elm.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Write custom text to Ford FDIM display',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Display "HELLO WORLD" continuously
  python scripts/debug/fdim_display_writer.py --text "HELLO WORLD"
  
  # Display "DIAGNOSTIC" for 30 seconds
  python scripts/debug/fdim_display_writer.py --text "DIAGNOSTIC" --duration 30
  
  # Try alternative FDIM ID
  python scripts/debug/fdim_display_writer.py --text "TEST" --id 0x417
  
  # Use faster update rate (250ms)
  python scripts/debug/fdim_display_writer.py --text "FAST UPDATE" --interval 0.25

Safety Warning:
  Custom displays can be distracting while driving. Always test in a safe
  environment (parked vehicle) first. Comply with local laws regarding
  vehicle displays and driver distraction.
        """
    )
    
    parser.add_argument('--port', default='COM3', 
                       help='Serial port (default: COM3)')
    parser.add_argument('--text', default='TEST', 
                       help='Text to display (max 16 characters, default: TEST)')
    parser.add_argument('--duration', type=float, default=None,
                       help='Display duration in seconds (default: continuous)')
    parser.add_argument('--id', type=lambda x: int(x, 0), default=0x415,
                       dest='display_id',
                       help='FDIM CAN ID in hex (default: 0x415, try 0x417)')
    parser.add_argument('--header', type=lambda x: int(x, 0), default=0x02,
                       help='Header byte in hex (default: 0x02)')
    parser.add_argument('--interval', type=float, default=0.5,
                       help='Update interval in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    success = main(
        port=args.port,
        text=args.text,
        duration=args.duration,
        display_id=args.display_id,
        header=args.header,
        interval=args.interval
    )
    
    sys.exit(0 if success else 1)
