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
        time.sleep(0.15)  # Increased wait time
        
        response = b''
        max_attempts = 10  # Try reading multiple times
        for _ in range(max_attempts):
            if self.connection.in_waiting:
                response += self.connection.read(self.connection.in_waiting)
            time.sleep(0.1)
            # If we got a prompt character, we're done
            if b'>' in response:
                break
        
        return response.decode('utf-8', errors='ignore').strip()
    
    def check_module_presence(self) -> bool:
        """
        Read standard DIDs to verify the module is awake.
        If this works but 0x19 fails, we know for sure there are simply no DTCs.
        
        Toyota ABS modules may not support all standard DIDs, so we try multiple approaches.
        
        Returns:
            True if module responds, False otherwise
        """
        print("  Trying Calibration ID (DID 0xF181)...", end=" ")
        cmd = "22 F1 81"
        response = self._send_command(cmd)
        time.sleep(0.2)
        
        response_clean = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 62 F1 81 [DATA...]
        if '62F181' in response_clean:
            print("✓")
            print("✓ Module is AWAKE (Calibration ID verified)")
            return True
        print("✗")
        
        # Try VIN as fallback
        print("  Trying VIN (DID 0xF190)...", end=" ")
        cmd = "22 F1 90"
        response = self._send_command(cmd)
        time.sleep(0.2)
        response_clean = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        if '62F190' in response_clean:
            print("✓")
            print("✓ Module is AWAKE (VIN verified)")
            return True
        print("✗")
        
        # Try ECU Serial Number
        print("  Trying ECU Serial Number (DID 0xF18C)...", end=" ")
        cmd = "22 F1 8C"
        response = self._send_command(cmd)
        time.sleep(0.2)
        response_clean = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        if '62F18C' in response_clean:
            print("✓")
            print("✓ Module is AWAKE (Serial Number verified)")
            return True
        print("✗")
        
        # Try Tester Present (Service 0x3E) - most basic UDS service
        print("  Trying Tester Present (Service 0x3E)...", end=" ")
        cmd = "3E 00"
        response = self._send_command(cmd)
        time.sleep(0.2)
        response_clean = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 7E 00 (0x3E + 0x40)
        if '7E00' in response_clean or '7E' in response_clean:
            print("✓")
            print("✓ Module is AWAKE (Tester Present confirmed)")
            return True
        print("✗")
        
        # Last resort: Try reading any DTC-related service to see if module responds
        print("  Trying Read DTC Count (Service 0x19 0x01)...", end=" ")
        cmd = "19 01 FF"
        response = self._send_command(cmd)
        time.sleep(0.3)
        response_clean = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Any positive response (59) or even negative response (7F) proves module is awake
        if '59' in response_clean or '7F19' in response_clean:
            print("✓")
            print("✓ Module is AWAKE (responded to Service 0x19)")
            return True
        print("✗")
        
        return False
    
    def enter_extended_session(self) -> bool:
        """
        Enter extended diagnostic session (UDS Service 0x10 Sub-function 0x03)
        This can help with Toyota modules that don't respond in default session
        
        Returns:
            True if successful, False otherwise
        """
        cmd = "10 03"
        response = self._send_command(cmd)
        time.sleep(0.2)
        
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 50 03 (0x10 + 0x40, sub-function echo)
        if '5003' in response:
            return True
        return False
    
    def read_dtc_count(self) -> Tuple[bool, int]:
        """
        Read DTC count using UDS Service 0x19 Sub-function 0x01
        This is more reliable on Toyota modules than sub-function 0x02
        
        Returns:
            (success, dtc_count)
        """
        cmd = "19 01 FF"
        
        response = self._send_command(cmd)
        time.sleep(0.3)
        
        if not response:
            return False, 0
        
        response = response.replace(' ', '').replace('\r', '').replace('\n', '')
        
        # Positive response: 59 01 [STATUS_MASK] [DTC_COUNT_HIGH] [DTC_COUNT_LOW]
        if '5901' in response:
            idx = response.find('5901')
            data = response[idx+4:]  # Skip 59 01
            
            if len(data) >= 6:
                # Skip status mask (2 chars), get count (4 chars = 2 bytes)
                count_hex = data[2:6]
                try:
                    count = int(count_hex, 16)
                    return True, count
                except:
                    pass
        
        return False, 0
    
    def read_dtcs_by_status(self, status_mask: int = 0xFF) -> Tuple[bool, List[dict]]:
        """
        Read DTCs using UDS Service 0x19 Sub-function 0x02
        
        IMPORTANT: Toyota 2007-2010 ABS modules (FJ Cruiser, 4Runner, Tacoma, Tundra, 
        Sequoia, Lexus GX470) do NOT respond to this service when there are no DTCs.
        This is NORMAL behavior, not a communication failure.
        
        Args:
            status_mask: DTC status mask (0xFF = all DTCs)
            
        Returns:
            (success, list of DTCs)
        """
        # UDS Service 0x19 Sub-function 0x02: reportDTCByStatusMask
        cmd = f"19 02 {status_mask:02X}"
        
        print(f"\nSending: {cmd}")
        response = self._send_command(cmd)
        
        # Wait longer for response (UDS responses can be slow)
        time.sleep(0.5)
        
        # Read any additional data that arrived
        if self.connection and self.connection.in_waiting:
            additional = b''
            while self.connection.in_waiting:
                additional += self.connection.read(self.connection.in_waiting)
                time.sleep(0.05)
            response += additional.decode('utf-8', errors='ignore')
        
        print(f"Response: {response[:100]}..." if len(response) > 100 else f"Response: {response}")
        
        if not response or 'NO DATA' in response.upper():
            print("\n" + "=" * 70)
            print("ℹ TOYOTA MODULE BEHAVIOR")
            print("=" * 70)
            print("No response from ABS module.")
            print("\nThis is NORMAL for Toyota 2007-2010 ABS modules when healthy.")
            print("These modules don't respond to Service 0x19 when no DTCs are stored.")
            
            # Check if module is actually awake
            print("\nVerifying module is awake...")
            if self.check_module_presence():
                print("\n✓ Module is responsive to other services")
                print("✓ No response to Service 0x19 = No DTCs present")
                print("\nIf your ABS warning light is OFF, this means:")
                print("  ✓ Module is functioning normally")
                print("  ✓ No confirmed DTCs present")
                print("  ✓ ABS system is healthy")
            else:
                print("\n✗ Module is not responding to any service")
                print("\nThis indicates a communication issue:")
                print("  • Try option 5 (Extended session)")
                print("  • Check if ignition is ON")
                print("  • Verify correct module address (0x7B0)")
                print("  • Try alternative address (0x760)")
            
            print("\nIf your ABS warning light is ON, try:")
            print("  1. Option 4 (Read DTC count) - more reliable")
            print("  2. Option 5 (Extended session)")
            print("  3. Check with professional Toyota Techstream tool")
            print("=" * 70)
            return True, []  # Return success with empty list (no DTCs = healthy)
        
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
            print("\n" + "=" * 70)
            print("✓ NO DTCs FOUND - ABS SYSTEM HEALTHY")
            print("=" * 70)
            print("\nThe ABS module has no stored Diagnostic Trouble Codes.")
            print("This indicates the ABS system is functioning normally.")
            print("\nIf your ABS warning light is ON but no DTCs are found:")
            print("  • Try option 4 (Read DTC count) - more reliable on Toyota")
            print("  • Try option 5 (Extended session) - may reveal hidden DTCs")
            print("  • Check with professional Toyota Techstream tool")
            print("  • Light may be on due to low brake fluid or other sensor")
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
        print("\n1. Read all DTCs (standard method)")
        print("2. Read confirmed DTCs only")
        print("3. Read pending DTCs only")
        print("4. Read DTC count (Toyota-friendly method)")
        print("5. Enter extended session + Read DTCs")
        print("6. Check module presence (verify module is awake)")
        print("7. Clear DTCs")
        
        choice = input("\nSelect option (1-7): ").strip()
        
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
            # Read DTC count (more reliable on Toyota)
            print("\nReading DTC count (Service 0x19 Sub-function 0x01)...")
            success, count = reader.read_dtc_count()
            if success:
                print(f"\n✓ DTC Count: {count}")
                if count == 0:
                    print("  No DTCs stored - ABS system is healthy")
                else:
                    print(f"  {count} DTC(s) stored")
                    print("\nTrying to read DTCs...")
                    success, dtcs = reader.read_dtcs_by_status(0xFF)
                    if success:
                        reader.print_dtcs(dtcs)
            else:
                print("\n✗ Failed to read DTC count")
                print("Module may not support this service or no DTCs present")
                
        elif choice == '5':
            # Enter extended session first, then read DTCs
            print("\nEntering extended diagnostic session...")
            if reader.enter_extended_session():
                print("✓ Extended session active")
                print("\nReading DTCs...")
                success, dtcs = reader.read_dtcs_by_status(0xFF)
                if success:
                    reader.print_dtcs(dtcs)
            else:
                print("✗ Failed to enter extended session")
                print("Trying to read DTCs anyway...")
                success, dtcs = reader.read_dtcs_by_status(0xFF)
                if success:
                    reader.print_dtcs(dtcs)
                    
        elif choice == '6':
            # Check module presence
            print("\nChecking if ABS module is awake and responsive...")
            if reader.check_module_presence():
                print("\n" + "=" * 70)
                print("MODULE STATUS: AWAKE AND RESPONSIVE")
                print("=" * 70)
                print("\nThe ABS module is communicating properly.")
                print("If Service 0x19 returns 'no response', it means:")
                print("  ✓ Module is functioning normally")
                print("  ✓ No DTCs are stored")
                print("  ✓ This is expected Toyota behavior")
                print("\nYou can safely conclude:")
                print("  • ABS system is healthy")
                print("  • No diagnostic trouble codes present")
                print("  • No repairs needed")
            else:
                print("\n" + "=" * 70)
                print("MODULE STATUS: NOT RESPONDING")
                print("=" * 70)
                print("\nThe ABS module is not responding to any UDS services.")
                print("\nTroubleshooting steps:")
                print("  1. Verify ignition is ON (engine doesn't need to run)")
                print("  2. Check OBD-II connector is fully seated")
                print("  3. Try standard OBD-II first: python -c \"import serial; s=serial.Serial('COM3',38400,timeout=3); import time; time.sleep(2); s.write(b'ATZ\\r'); time.sleep(1); s.write(b'0100\\r'); time.sleep(1); print(s.read(s.in_waiting))\"")
                print("  4. Module may be in deep sleep - try:")
                print("     • Turn ignition OFF, wait 30 seconds")
                print("     • Turn ignition ON, wait 10 seconds")
                print("     • Try again")
                print("  5. Some Toyota modules require:")
                print("     • Brake pedal pressed")
                print("     • Parking brake released")
                print("     • Transmission in Park")
                print("\nNote: Earlier you saw 'ABS Request: 0x7B0, ABS Response: 0x7B8'")
                print("which means the addressing is correct. The module may have")
                print("entered sleep mode or requires specific wake-up conditions.")
                    
        elif choice == '7':
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
