#!/usr/bin/env python3
"""
Toyota FJ Cruiser 2008 - ABS DTC Reader
Read Diagnostic Trouble Codes from ABS module using UDS Service 0x19

Toyota/Lexus ABS modules typically use:
- Address: 0x7B0 (request) / 0x7B8 (response)
- Protocol: ISO 15765-4 CAN (500 kbps)
- Service: 0x19 (ReadDTCInformation)

Author: AI Diagnostic Agent
"""

import serial
import time
from datetime import datetime
from typing import List, Tuple, Optional

class FJCruiserABSDTCReader:
    """Read DTCs from FJ Cruiser ABS module using UDS"""
    
    def __init__(self, port: str = 'COM3', baudrate: int = 38400):
        """Initialize DTC reader"""
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        
        # Toyota ABS addressing (typical)
        self.abs_request = 0x7B0
        self.abs_response = 0x7B8
        
        # DTC status masks
        self.dtc_status_bits = {
            0x01: "testFailed",
            0x02: "testFailedThisOperationCycle",
            0x04: "pendingDTC",
            0x08: "confirmedDTC",
            0x10: "testNotCompletedSinceLastClear",
            0x20: "testFailedSinceLastClear",
            0x40: "testNotCompletedThisOperationCycle",
            0x80: "warningIndicatorRequested"
        }
    
    def connect(self) -> bool:
        """Connect to ELM327 adapter"""
        try:
            print("=" * 70)
            print("Toyota FJ Cruiser 2008 - ABS DTC Reader")
            print("=" * 70)
            print("\nConnecting to ELM327...")
            
            self.connection = serial.Serial(self.port, self.baudrate, timeout=3)
            time.sleep(2)
            
            # Initialize ELM327
            print("Initializing adapter...")
            self._send_command("ATZ")  # Reset
            time.sleep(1)
            self._send_command("ATE0")  # Echo off
            self._send_command("ATL0")  # Linefeeds off
            self._send_command("ATS0")  # Spaces off
            self._send_command("ATH1")  # Headers on
            self._send_command("ATSP6")  # ISO 15765-4 CAN (11 bit, 500 kbps)
            self._send_command("ATCAF0")  # CAN Auto Formatting off
            
            # Set header to ABS request address
            self._send_command(f"ATSH {self.abs_request:03X}")
            
            # Set flow control
            self._send_command(f"ATFCSH {self.abs_response:03X}")
            self._send_command("ATFCSD 30 00 00")
            
            print(f"✓ Connected")
            print(f"  ABS Request:  0x{self.abs_request:03X}")
            print(f"  ABS Response: 0x{self.abs_response:03X}")
            
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
    
    def read_dtcs_by_status(self, status_mask: int = 0xFF) -> Tuple[bool, List[dict]]:
        """
        Read DTCs using UDS Service 0x19 Sub-function 0x02
        
        Args:
            status_mask: DTC status mask (0xFF = all DTCs)
            
        Returns:
            (success, list of DTCs)
        """
        # UDS Service 0x19 Sub-function 0x02: reportDTCByStatusMask
        cmd = f"19 02 {status_mask:02X}"
        
        print(f"\nSending: {cmd}")
        response = self._send_command(cmd)
        
        # Wait for response
        time.sleep(0.3)
        
        if not response:
            return False, []
        
        # Clean response
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Look for positive response (59 = 0x19 + 0x40)
        if '59' not in response:
            print(f"No positive response. Raw: {response}")
            
            # Check for negative response
            if '7F' in response:
                idx = response.find('7F')
                if idx != -1:
                    nrc = response[idx+4:idx+6]
                    print(f"Negative Response Code: 0x{nrc}")
                    nrc_meanings = {
                        '11': 'serviceNotSupported',
                        '12': 'subFunctionNotSupported',
                        '13': 'incorrectMessageLength',
                        '22': 'conditionsNotCorrect',
                        '31': 'requestOutOfRange'
                    }
                    if nrc in nrc_meanings:
                        print(f"  Meaning: {nrc_meanings[nrc]}")
            
            return False, []
        
        # Parse response
        idx = response.find('59')
        if idx == -1:
            return False, []
        
        # Response format: 59 02 [AVAILABILITY_MASK] [DTC_HIGH] [DTC_MID] [DTC_LOW] [STATUS] ...
        data = response[idx+4:]  # Skip 59 02
        
        if len(data) < 2:
            print("No DTCs found (empty response)")
            return True, []
        
        # First byte is availability mask (skip it)
        data = data[2:]
        
        # Parse DTCs (4 bytes each: 3 bytes DTC + 1 byte status)
        dtcs = []
        i = 0
        while i + 8 <= len(data):
            dtc_bytes = data[i:i+6]  # 3 bytes (6 hex chars)
            status_byte = data[i+6:i+8]  # 1 byte (2 hex chars)
            
            if dtc_bytes and status_byte:
                dtc_code = self._decode_dtc(dtc_bytes)
                status = int(status_byte, 16)
                
                dtcs.append({
                    'code': dtc_code,
                    'status': status,
                    'status_bits': self._decode_status(status),
                    'raw': dtc_bytes + status_byte
                })
            
            i += 8
        
        return True, dtcs
    
    def _decode_dtc(self, dtc_hex: str) -> str:
        """
        Decode 3-byte DTC to standard format (e.g., C1234)
        
        Format: [HIGH_BYTE] [MID_BYTE] [LOW_BYTE]
        HIGH_BYTE bits 7-6: DTC type (00=P, 01=C, 10=B, 11=U)
        HIGH_BYTE bits 5-4: First digit
        HIGH_BYTE bits 3-0 + MID_BYTE + LOW_BYTE: Remaining digits
        """
        if len(dtc_hex) != 6:
            return "INVALID"
        
        try:
            high = int(dtc_hex[0:2], 16)
            mid = int(dtc_hex[2:4], 16)
            low = int(dtc_hex[4:6], 16)
            
            # DTC type from bits 7-6
            dtc_type_bits = (high >> 6) & 0x03
            dtc_types = ['P', 'C', 'B', 'U']
            dtc_type = dtc_types[dtc_type_bits]
            
            # First digit from bits 5-4
            first_digit = (high >> 4) & 0x03
            
            # Remaining digits from bits 3-0 of high + mid + low
            second_digit = high & 0x0F
            third_digit = (mid >> 4) & 0x0F
            fourth_digit = mid & 0x0F
            fifth_digit = (low >> 4) & 0x0F
            
            # Some Toyota DTCs use different format
            # Try standard format first
            dtc_code = f"{dtc_type}{first_digit}{second_digit:X}{third_digit:X}{fourth_digit:X}"
            
            return dtc_code
            
        except:
            return f"RAW_{dtc_hex}"
    
    def _decode_status(self, status: int) -> dict:
        """Decode DTC status byte"""
        status_flags = {}
        for bit, name in self.dtc_status_bits.items():
            status_flags[name] = bool(status & bit)
        return status_flags
    
    def read_supported_dtcs(self) -> Tuple[bool, List[str]]:
        """
        Read supported DTCs using UDS Service 0x19 Sub-function 0x0A
        """
        cmd = "19 0A"
        
        print(f"\nReading supported DTCs...")
        response = self._send_command(cmd)
        time.sleep(0.3)
        
        if not response or '59' not in response:
            print("Sub-function 0x0A not supported")
            return False, []
        
        # Parse similar to read_dtcs_by_status
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        idx = response.find('59')
        data = response[idx+4:]
        
        dtcs = []
        i = 0
        while i + 6 <= len(data):
            dtc_bytes = data[i:i+6]
            dtc_code = self._decode_dtc(dtc_bytes)
            dtcs.append(dtc_code)
            i += 6
        
        return True, dtcs
    
    def clear_dtcs(self) -> bool:
        """
        Clear DTCs using UDS Service 0x14
        WARNING: This will clear all DTCs from ABS module!
        """
        print("\n⚠ WARNING: This will clear ALL DTCs from ABS module!")
        confirm = input("Type 'YES' to confirm: ").strip()
        
        if confirm != 'YES':
            print("Cancelled")
            return False
        
        # UDS Service 0x14: ClearDiagnosticInformation
        # Parameter: 0xFFFFFF (all DTCs)
        cmd = "14 FF FF FF"
        
        print(f"\nClearing DTCs...")
        response = self._send_command(cmd)
        time.sleep(0.3)
        
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 54 (0x14 + 0x40)
        if '54' in response:
            print("✓ DTCs cleared successfully")
            return True
        else:
            print("✗ Failed to clear DTCs")
            return False
    
    def print_dtcs(self, dtcs: List[dict]):
        """Print DTCs in readable format"""
        if not dtcs:
            print("\n✓ No DTCs found - ABS system OK")
            return
        
        print(f"\n{'=' * 70}")
        print(f"FOUND {len(dtcs)} DTC(s)")
        print(f"{'=' * 70}\n")
        
        for i, dtc in enumerate(dtcs, 1):
            print(f"{i}. DTC: {dtc['code']}")
            print(f"   Status: 0x{dtc['status']:02X}")
            print(f"   Flags:")
            
            for flag, value in dtc['status_bits'].items():
                if value:
                    symbol = "✓" if flag in ['confirmedDTC', 'testFailed'] else "•"
                    print(f"     {symbol} {flag}")
            
            print(f"   Raw: {dtc['raw']}")
            print()
    
    def disconnect(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
        print("✓ Disconnected")

def main():
    """Main execution"""
    reader = FJCruiserABSDTCReader(port='COM3')
    
    if not reader.connect():
        return
    
    try:
        print("\n" + "=" * 70)
        print("OPTIONS")
        print("=" * 70)
        print("\n1. Read all DTCs")
        print("2. Read confirmed DTCs only")
        print("3. Read pending DTCs only")
        print("4. Read supported DTCs")
        print("5. Clear DTCs")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            # Read all DTCs (status mask 0xFF)
            success, dtcs = reader.read_dtcs_by_status(0xFF)
            if success:
                reader.print_dtcs(dtcs)
                
        elif choice == '2':
            # Read confirmed DTCs only (bit 3 = 0x08)
            success, dtcs = reader.read_dtcs_by_status(0x08)
            if success:
                reader.print_dtcs(dtcs)
                
        elif choice == '3':
            # Read pending DTCs only (bit 2 = 0x04)
            success, dtcs = reader.read_dtcs_by_status(0x04)
            if success:
                reader.print_dtcs(dtcs)
                
        elif choice == '4':
            # Read supported DTCs
            success, dtcs = reader.read_supported_dtcs()
            if success:
                print(f"\nSupported DTCs: {len(dtcs)}")
                for dtc in dtcs:
                    print(f"  - {dtc}")
                    
        elif choice == '5':
            # Clear DTCs
            reader.clear_dtcs()
            
        else:
            print("Invalid choice")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
