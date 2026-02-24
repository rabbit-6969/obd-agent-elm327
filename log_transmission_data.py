#!/usr/bin/env python3
"""
Ford Escape 2008 - Transmission Data Logger
Logs transmission data to CSV file for analysis

Logs:
- Timestamp
- ATF Temperature
- Turbine Speed
- Output Speed
- Gear Ratio
- Estimated Gear

Author: AI Diagnostic Agent
"""

import serial
import time
import csv
from datetime import datetime
from typing import Dict, Optional
import sys
import os


class TransmissionLogger:
    """Transmission data logger"""
    
    # Known working DIDs
    DID_ATF_TEMP = 0x221E1C
    DID_TURBINE_SPEED = 0x221E14
    DID_OUTPUT_SPEED = 0x221E16
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        """Initialize logger"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.running = False
        self.log_file = None
        self.csv_writer = None
        
        # Statistics
        self.samples_logged = 0
        self.errors = 0
    
    def connect(self) -> bool:
        """Connect to ELM327 adapter"""
        try:
            print(f"Connecting to {self.port}...")
            self.connection = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)
            
            # Initialize ELM327
            self._send_command("ATZ")
            time.sleep(1)
            self._send_command("ATE0")
            self._send_command("ATL0")
            self._send_command("ATS0")
            self._send_command("ATH1")
            self._send_command("ATSP6")
            self._send_command("ATCAF0")
            
            print("✓ Connected and configured")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def _send_command(self, cmd: str) -> str:
        """Send command to ELM327"""
        if not self.connection:
            return ""
        
        self.connection.write((cmd + '\r').encode())
        time.sleep(0.1)
        
        response = b''
        while self.connection.in_waiting:
            response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.05)
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def read_did(self, did: int) -> Optional[bytes]:
        """Read a DID from PCM"""
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        cmd = f"7E0 03 22 {did_msb:02X} {did_lsb:02X}"
        response = self._send_command(cmd)
        
        time.sleep(0.1)
        
        if '7E8' in response and '62' in response:
            parts = response.replace(' ', '').replace('\r', '').replace('\n', '')
            idx = parts.find('62')
            if idx != -1:
                data_start = idx + 2 + 4
                data_hex = parts[data_start:]
                try:
                    return bytes.fromhex(data_hex)
                except:
                    pass
        
        return None
    
    def read_all_data(self) -> Dict:
        """Read all transmission data"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'atf_temp_c': None,
            'atf_temp_f': None,
            'turbine_rpm': None,
            'output_rpm': None,
            'gear_ratio': None,
            'estimated_gear': None
        }
        
        # Read ATF temperature
        temp_data = self.read_did(self.DID_ATF_TEMP)
        if temp_data and len(temp_data) >= 1:
            temp_c = temp_data[0] - 40
            temp_f = (temp_c * 9/5) + 32
            data['atf_temp_c'] = temp_c
            data['atf_temp_f'] = temp_f
        
        # Read turbine speed
        turbine_data = self.read_did(self.DID_TURBINE_SPEED)
        if turbine_data and len(turbine_data) >= 2:
            turbine_rpm = (turbine_data[0] << 8) | turbine_data[1]
            data['turbine_rpm'] = turbine_rpm
        
        # Read output speed
        output_data = self.read_did(self.DID_OUTPUT_SPEED)
        if output_data and len(output_data) >= 2:
            output_rpm = (output_data[0] << 8) | output_data[1]
            data['output_rpm'] = output_rpm
        
        # Calculate gear ratio
        if data['turbine_rpm'] and data['output_rpm'] and data['output_rpm'] > 0:
            ratio = data['turbine_rpm'] / data['output_rpm']
            data['gear_ratio'] = ratio
            data['estimated_gear'] = self._estimate_gear(ratio)
        
        return data
    
    def _estimate_gear(self, ratio: float) -> str:
        """Estimate current gear from ratio"""
        gear_ratios = {
            'P/N': (0.0, 0.1),
            '1st': (2.2, 2.7),
            '2nd': (1.3, 1.6),
            '3rd': (0.9, 1.1),
            '4th': (0.6, 0.8)
        }
        
        for gear, (min_ratio, max_ratio) in gear_ratios.items():
            if min_ratio <= ratio <= max_ratio:
                return gear
        
        return 'Unknown'
    
    def create_log_file(self, filename: Optional[str] = None) -> bool:
        """Create CSV log file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transmission_log_{timestamp}.csv"
        
        try:
            self.log_file = open(filename, 'w', newline='')
            self.csv_writer = csv.DictWriter(
                self.log_file,
                fieldnames=[
                    'timestamp',
                    'atf_temp_c',
                    'atf_temp_f',
                    'turbine_rpm',
                    'output_rpm',
                    'gear_ratio',
                    'estimated_gear'
                ]
            )
            self.csv_writer.writeheader()
            
            print(f"✓ Created log file: {filename}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create log file: {e}")
            return False
    
    def log_sample(self):
        """Log a single data sample"""
        try:
            data = self.read_all_data()
            
            if self.csv_writer:
                self.csv_writer.writerow(data)
                self.log_file.flush()  # Ensure data is written
                self.samples_logged += 1
                
                # Display progress
                print(f"\rSamples logged: {self.samples_logged} | "
                      f"Temp: {data['atf_temp_c']:.1f}°C | "
                      f"Turbine: {data['turbine_rpm']} RPM | "
                      f"Output: {data['output_rpm']} RPM | "
                      f"Gear: {data['estimated_gear']}", end='')
            
        except Exception as e:
            self.errors += 1
            print(f"\n⚠ Error logging sample: {e}")
    
    def logging_loop(self, interval: float = 1.0, duration: Optional[float] = None):
        """Main logging loop"""
        self.running = True
        start_time = time.time()
        
        print("\nStarting data logging...")
        print(f"Update interval: {interval} seconds")
        if duration:
            print(f"Duration: {duration} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                self.log_sample()
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    print("\n\n✓ Logging duration reached")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✓ Logging stopped by user")
            self.running = False
        
        # Print statistics
        print(f"\nLogging Statistics:")
        print(f"  Samples logged: {self.samples_logged}")
        print(f"  Errors: {self.errors}")
        print(f"  Duration: {time.time() - start_time:.1f} seconds")
    
    def close_log_file(self):
        """Close log file"""
        if self.log_file:
            self.log_file.close()
            print("✓ Log file closed")
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("✓ Disconnected")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ford Escape 2008 - Transmission Data Logger'
    )
    parser.add_argument(
        '--port',
        default='COM3',
        help='Serial port (default: COM3)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=1.0,
        help='Logging interval in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help='Logging duration in seconds (default: unlimited)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output CSV filename (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    # Create logger
    logger = TransmissionLogger(port=args.port)
    
    # Connect
    if not logger.connect():
        sys.exit(1)
    
    # Create log file
    if not logger.create_log_file(args.output):
        logger.disconnect()
        sys.exit(1)
    
    # Start logging
    try:
        logger.logging_loop(interval=args.interval, duration=args.duration)
    finally:
        logger.close_log_file()
        logger.disconnect()


if __name__ == "__main__":
    main()
