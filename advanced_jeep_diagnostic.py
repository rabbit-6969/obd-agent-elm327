#!/usr/bin/env python3
"""
Advanced Jeep Wrangler Diagnostic - Direct Module Access
Attempts to read airbag codes and shifter position using UDS commands
"""

import serial
import time

class JeepAdvancedDiagnostic:
    def __init__(self, port="COM4", baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def connect(self):
        """Connect to ELM327 adapter"""
        print("=" * 60)
        print("Jeep Wrangler JK - Advanced Diagnostic")
        print("=" * 60)
        print(f"\nConnecting to {self.port}...")
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=3)
            time.sleep(2)  # Wait for ELM327 to initialize
            
            # Reset adapter
            self.send_command("ATZ")
            time.sleep(1)
            
            # Configure adapter
            self.send_command("ATE0")  # Echo off
            self.send_command("ATL0")  # Linefeeds off
            self.send_command("ATS0")  # Spaces off
            self.send_command("ATH1")  # Headers on
            self.send_command("ATSP6")  # Set protocol to ISO 15765-4 CAN (11 bit, 500 kbaud)
            
            print("✓ Connected and configured")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def send_command(self, cmd):
        """Send command to ELM327 and get response"""
        if not self.ser:
            return None
            
        try:
            self.ser.write((cmd + '\r').encode())
            time.sleep(0.1)
            
            response = b''
            while self.ser.in_waiting:
                response += self.ser.read(self.ser.in_waiting)
                time.sleep(0.05)
            
            return response.decode('utf-8', errors='ignore').strip()
            
        except Exception as e:
            print(f"Command error: {e}")
            return None
    
    def enter_extended_session(self, module_addr):
        """Try to enter extended diagnostic session"""
        print(f"  → Attempting extended diagnostic session...")
        
        # Set header to module
        self.send_command(f"ATSH{module_addr[2:]}")
        time.sleep(0.1)
        
        # UDS Service 0x10 (Diagnostic Session Control)
        # 0x10 0x03 = Extended Diagnostic Session
        response = self.send_command("1003")
        
        if response and "5003" in response:
            print(f"  ✓ Extended session activated")
            return True
        else:
            print(f"  ✗ Extended session not available")
            return False
    
    def read_airbag_dtcs(self):
        """Attempt to read DTCs from Airbag Control Module"""
        print("\n" + "=" * 60)
        print("AIRBAG CONTROL MODULE - DIRECT ACCESS ATTEMPT")
        print("=" * 60)
        
        # Common Jeep/Chrysler airbag module addresses
        acm_addresses = [
            ("0x738", "0x758", "Airbag Control Module (Primary)"),
            ("0x740", "0x760", "Airbag Control Module (Alt 1)"),
            ("0x741", "0x761", "Airbag Control Module (Alt 2)"),
        ]
        
        for req_addr, resp_addr, name in acm_addresses:
            print(f"\nTrying {name} at {req_addr}...")
            
            # Set header to airbag module
            self.send_command(f"ATSH{req_addr[2:]}")
            time.sleep(0.1)
            
            # Try to read DTCs using UDS Service 0x19 (Read DTC Information)
            # 0x19 0x02 0xFF = Read DTC by status mask (all DTCs)
            response = self.send_command("1902FF")
            
            if response and "NO DATA" not in response and "?" not in response:
                print(f"✓ Response from {name}:")
                print(f"  Raw: {response}")
                self.parse_dtc_response(response)
                
                # If we got a negative response indicating conditions not correct,
                # try entering extended session
                if "7F1922" in response.replace(" ", ""):
                    print(f"\n  Trying with extended diagnostic session...")
                    if self.enter_extended_session(req_addr):
                        time.sleep(0.2)
                        response2 = self.send_command("1902FF")
                        if response2:
                            print(f"  Response after extended session:")
                            print(f"  Raw: {response2}")
                            self.parse_dtc_response(response2)
                
                return True
            else:
                print(f"  No response from {req_addr}")
        
        print("\n⚠ Could not access airbag module directly")
        print("  This is normal for standard ELM327 adapters")
        print("  Recommendation: Use AlfaOBD for full airbag access")
        return False
    
    def read_shifter_position(self):
        """Attempt to read shifter position from TCM"""
        print("\n" + "=" * 60)
        print("TRANSMISSION CONTROL MODULE - SHIFTER POSITION")
        print("=" * 60)
        
        # Jeep/Chrysler TCM addresses
        tcm_addresses = [
            ("0x7E1", "0x7E9", "Transmission Control Module"),
            ("0x743", "0x763", "TCM (Alt)"),
        ]
        
        # Common PIDs for gear position
        gear_pids = [
            ("2212", "Gear Position (PID 0x12)"),
            ("22A4", "PRNDL Position (PID 0xA4)"),
            ("221234", "Gear Status (Multi-byte)"),
        ]
        
        for req_addr, resp_addr, tcm_name in tcm_addresses:
            print(f"\nTrying {tcm_name} at {req_addr}...")
            
            # Set header to TCM
            self.send_command(f"ATSH{req_addr[2:]}")
            time.sleep(0.1)
            
            for pid, pid_name in gear_pids:
                response = self.send_command(pid)
                
                if response and "NO DATA" not in response and "?" not in response:
                    print(f"✓ {pid_name}:")
                    print(f"  Raw: {response}")
                    self.parse_gear_response(response)
                    return True
                else:
                    print(f"  {pid_name}: No data")
        
        print("\n⚠ Could not read shifter position directly")
        print("  This is normal for standard ELM327 adapters")
        print("  Recommendation: Use AlfaOBD for transmission data")
        return False
    
    def parse_dtc_response(self, response):
        """Parse DTC response from module"""
        try:
            # Remove spaces and common ELM327 responses
            clean = response.replace(" ", "").replace(">", "").replace("\r", "").replace("\n", "")
            
            # Check for negative response (7F = Negative Response)
            if "7F" in clean[:4]:
                print("  ⚠ Negative response from module")
                # Parse negative response: 7F [service] [NRC]
                if len(clean) >= 8:
                    service = clean[4:6]
                    nrc = clean[6:8]
                    
                    nrc_codes = {
                        "11": "Service not supported",
                        "12": "Sub-function not supported",
                        "13": "Incorrect message length",
                        "22": "Conditions not correct",
                        "31": "Request out of range",
                        "78": "Response pending (wait)",
                    }
                    
                    nrc_desc = nrc_codes.get(nrc, f"Unknown error (0x{nrc})")
                    print(f"  Service 0x{service}: {nrc_desc}")
                    
                    if nrc == "78":
                        print("  → Module is processing, may need to wait longer")
                    elif nrc == "22":
                        print("  → Module may require special diagnostic session")
                        print("  → Try entering extended diagnostic session first")
                return
            
            # UDS response format: 59 02 [status] [DTC bytes]
            if "5902" in clean or "59" in clean:
                print("  ✓ Valid UDS response detected")
                
                # Extract DTC bytes (simplified parsing)
                # Full parsing would require detailed UDS knowledge
                print("  DTC data present - requires detailed parsing")
                print("  Recommendation: Use AlfaOBD for proper DTC interpretation")
            else:
                print("  Response format not recognized")
                print(f"  Raw hex: {clean}")
                
        except Exception as e:
            print(f"  Parse error: {e}")
    
    def parse_gear_response(self, response):
        """Parse gear position response"""
        try:
            clean = response.replace(" ", "").replace(">", "").replace("\r", "").replace("\n", "")
            
            # Try to extract gear value
            if len(clean) >= 4:
                # Typical response: 62 12 XX (where XX is gear value)
                gear_byte = clean[-2:]
                gear_value = int(gear_byte, 16)
                
                gear_map = {
                    0: "Park (P)",
                    1: "Reverse (R)",
                    2: "Neutral (N)",
                    3: "Drive (D)",
                    4: "4th Gear",
                    5: "3rd Gear",
                    6: "2nd Gear",
                    7: "1st Gear",
                }
                
                gear_name = gear_map.get(gear_value, f"Unknown ({gear_value})")
                print(f"  Shifter Position: {gear_name}")
                
        except Exception as e:
            print(f"  Parse error: {e}")
    
    def try_standard_dtc_read(self):
        """Try standard Mode 03 DTC read with different filters"""
        print("\n" + "=" * 60)
        print("STANDARD DTC READ - ALL MODULES")
        print("=" * 60)
        
        # Reset to auto protocol
        self.send_command("ATSP0")
        time.sleep(0.5)
        
        # Try Mode 03 (Read DTCs)
        print("\nReading stored DTCs...")
        response = self.send_command("03")
        
        if response and "43" in response:
            print("✓ DTCs found:")
            print(f"  {response}")
            self.parse_mode03_dtcs(response)
        else:
            print("  No DTCs in standard read")
    
    def parse_mode03_dtcs(self, response):
        """Parse Mode 03 DTC response"""
        try:
            # Mode 03 response format: 43 [count] [DTC bytes]
            clean = response.replace(" ", "").replace(">", "").replace("\r", "").replace("\n", "")
            
            if "43" in clean:
                # Extract DTCs (2 bytes per DTC)
                dtc_data = clean.split("43")[1]
                
                if len(dtc_data) > 2:
                    count = int(dtc_data[:2], 16)
                    print(f"  DTC Count: {count}")
                    
                    # Parse individual DTCs
                    dtc_bytes = dtc_data[2:]
                    for i in range(0, len(dtc_bytes), 4):
                        if i + 4 <= len(dtc_bytes):
                            dtc_code = self.decode_dtc(dtc_bytes[i:i+4])
                            print(f"  {dtc_code}")
                            
        except Exception as e:
            print(f"  Parse error: {e}")
    
    def decode_dtc(self, dtc_hex):
        """Decode DTC from hex bytes"""
        try:
            byte1 = int(dtc_hex[:2], 16)
            byte2 = int(dtc_hex[2:4], 16)
            
            # First 2 bits determine DTC type
            dtc_type = (byte1 >> 6) & 0x03
            type_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
            
            # Extract digits
            digit1 = (byte1 >> 4) & 0x03
            digit2 = byte1 & 0x0F
            digit3 = (byte2 >> 4) & 0x0F
            digit4 = byte2 & 0x0F
            
            code = f"{type_map[dtc_type]}{digit1}{digit2:X}{digit3:X}{digit4:X}"
            return code
            
        except:
            return f"Unknown ({dtc_hex})"
    
    def disconnect(self):
        """Close connection"""
        if self.ser:
            self.ser.close()
            print("\n✓ Disconnected")

def main():
    diag = JeepAdvancedDiagnostic("COM4")
    
    if not diag.connect():
        return
    
    try:
        # Try standard DTC read first
        diag.try_standard_dtc_read()
        
        # Try direct airbag module access
        diag.read_airbag_dtcs()
        
        # Try shifter position read
        diag.read_shifter_position()
        
        print("\n" + "=" * 60)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 60)
        print("\nNote: Limited success is expected with standard ELM327")
        print("For full access, use AlfaOBD: https://www.alfaobd.com/")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        diag.disconnect()

if __name__ == "__main__":
    main()
