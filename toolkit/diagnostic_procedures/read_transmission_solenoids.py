#!/usr/bin/env python3
"""
Ford Escape 2008 - Transmission Solenoid State Reader
Reads real-time solenoid states using UDS commands via HS-CAN adapter

Requirements:
- ELM327-compatible adapter with HS-CAN switch (e.g., OBDLink EX, ELS27)
- Adapter switch must be set to HS-CAN position
- python-can and can-isotp libraries

Based on FORScan reverse-engineered Ford-specific DIDs
"""

import can
import isotp
import time
from typing import Optional, Dict, List

class FordTransmissionSolenoidReader:
    """
    Reads transmission solenoid states from Ford Escape 2008 TCM
    using UDS commands over ISO-TP (CAN)
    """
    
    # TCM CAN addresses
    TCM_REQUEST_ID = 0x7E1   # Physical request to TCM
    TCM_RESPONSE_ID = 0x7E9  # Response from TCM
    
    # UDS Service IDs
    SID_DIAGNOSTIC_SESSION = 0x10
    SID_SECURITY_ACCESS = 0x27
    SID_READ_DATA_BY_ID = 0x22
    SID_IO_CONTROL = 0x2F
    SID_TESTER_PRESENT = 0x3E
    
    # Diagnostic Sessions
    SESSION_DEFAULT = 0x01
    SESSION_EXTENDED = 0x03
    
    # Ford-specific DIDs for transmission (reverse-engineered from FORScan)
    # Note: These are examples - actual DIDs may vary by TCM firmware
    DID_SOLENOID_COMMANDED = 0x1234  # Hypothetical - needs discovery
    DID_SOLENOID_ACTUAL = 0x1235     # Hypothetical - needs discovery
    DID_TRANSMISSION_STATUS = 0x1236  # Hypothetical - needs discovery
    
    def __init__(self, interface='socketcan', channel='can0', bitrate=500000):
        """
        Initialize connection to TCM
        
        Args:
            interface: CAN interface type (socketcan, pcan, etc.)
            channel: CAN channel (can0, PCAN_USBBUS1, etc.)
            bitrate: CAN bitrate (500000 for HS-CAN)
        """
        self.interface = interface
        self.channel = channel
        self.bitrate = bitrate
        self.bus = None
        self.isotp_socket = None
        self.in_extended_session = False
        
    def connect(self) -> bool:
        """
        Connect to CAN bus and setup ISO-TP communication
        
        Returns:
            True if connection successful
        """
        try:
            print("=" * 60)
            print("Ford Escape 2008 - Transmission Solenoid Reader")
            print("=" * 60)
            print("\n⚠ IMPORTANT: Ensure HS-CAN switch is in HS position!")
            input("Press Enter when switch is set to HS-CAN...")
            
            print(f"\nConnecting to CAN bus...")
            print(f"  Interface: {self.interface}")
            print(f"  Channel: {self.channel}")
            print(f"  Bitrate: {self.bitrate} bps")
            
            # Create CAN bus
            self.bus = can.interface.Bus(
                channel=self.channel,
                bustype=self.interface,
                bitrate=self.bitrate
            )
            
            # Setup ISO-TP socket for TCM communication
            isotp_params = isotp.params.LinkLayerProtocol.CAN()
            isotp_params.tx_data_length = 8
            isotp_params.tx_padding = 0x00
            
            addr = isotp.Address(
                isotp.AddressingMode.Normal_11bits,
                txid=self.TCM_REQUEST_ID,
                rxid=self.TCM_RESPONSE_ID
            )
            
            self.isotp_socket = isotp.socket.socket(
                isotp.socket.AF_CAN,
                isotp.socket.SOCK_DGRAM,
                isotp.socket.CAN_ISOTP
            )
            
            self.isotp_socket.bind((self.channel, addr))
            self.isotp_socket.settimeout(2.0)
            
            print("✓ Connected to TCM")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def send_uds_request(self, data: bytes, timeout: float = 2.0) -> Optional[bytes]:
        """
        Send UDS request and receive response
        
        Args:
            data: UDS request bytes
            timeout: Response timeout in seconds
            
        Returns:
            Response bytes or None if timeout/error
        """
        try:
            self.isotp_socket.send(data)
            self.isotp_socket.settimeout(timeout)
            response = self.isotp_socket.recv()
            return response
        except Exception as e:
            print(f"  Communication error: {e}")
            return None
    
    def enter_extended_session(self) -> bool:
        """
        Enter extended diagnostic session (required for advanced diagnostics)
        
        Returns:
            True if session entered successfully
        """
        print("\n→ Entering extended diagnostic session...")
        
        request = bytes([self.SID_DIAGNOSTIC_SESSION, self.SESSION_EXTENDED])
        response = self.send_uds_request(request)
        
        if response and len(response) >= 2:
            if response[0] == (self.SID_DIAGNOSTIC_SESSION + 0x40):
                print("  ✓ Extended session active")
                self.in_extended_session = True
                return True
            elif response[0] == 0x7F:
                nrc = response[2] if len(response) > 2 else 0
                print(f"  ✗ Negative response: NRC 0x{nrc:02X}")
                return False
        
        print("  ✗ No valid response")
        return False
    
    def send_tester_present(self):
        """
        Send tester present message to keep session alive
        """
        request = bytes([self.SID_TESTER_PRESENT, 0x00])
        self.send_uds_request(request, timeout=0.5)
    
    def read_data_by_identifier(self, did: int) -> Optional[bytes]:
        """
        Read data using UDS ReadDataByIdentifier service
        
        Args:
            did: Data Identifier (16-bit)
            
        Returns:
            Data bytes or None if error
        """
        did_msb = (did >> 8) & 0xFF
        did_lsb = did & 0xFF
        
        request = bytes([self.SID_READ_DATA_BY_ID, did_msb, did_lsb])
        response = self.send_uds_request(request)
        
        if response and len(response) >= 3:
            if response[0] == (self.SID_READ_DATA_BY_ID + 0x40):
                # Verify DID echo
                if response[1] == did_msb and response[2] == did_lsb:
                    return response[3:]  # Return data portion
            elif response[0] == 0x7F:
                nrc = response[2] if len(response) > 2 else 0
                print(f"  ✗ DID 0x{did:04X}: NRC 0x{nrc:02X}")
                return None
        
        return None
    
    def discover_solenoid_dids(self) -> List[int]:
        """
        Attempt to discover valid DIDs for solenoid data
        Scans common Ford DID ranges
        
        Returns:
            List of valid DIDs found
        """
        print("\n" + "=" * 60)
        print("DISCOVERING SOLENOID DIDs")
        print("=" * 60)
        print("\nScanning Ford-specific DID ranges...")
        print("(This may take several minutes)")
        
        valid_dids = []
        
        # Common Ford DID ranges for transmission data
        did_ranges = [
            (0x1000, 0x1100),  # Transmission parameters
            (0x2000, 0x2100),  # Actuator states
            (0xF000, 0xF100),  # System info
        ]
        
        for start, end in did_ranges:
            print(f"\nScanning range 0x{start:04X} - 0x{end:04X}...")
            
            for did in range(start, end):
                # Send tester present every 10 DIDs to keep session alive
                if did % 10 == 0:
                    self.send_tester_present()
                
                data = self.read_data_by_identifier(did)
                if data is not None:
                    print(f"  ✓ Found DID 0x{did:04X}: {data.hex()}")
                    valid_dids.append(did)
                
                time.sleep(0.05)  # Small delay between requests
        
        print(f"\n✓ Discovery complete: {len(valid_dids)} DIDs found")
        return valid_dids
    
    def read_solenoid_states(self) -> Dict[str, any]:
        """
        Read transmission solenoid states
        
        Returns:
            Dictionary with solenoid state data
        """
        print("\n" + "=" * 60)
        print("READING SOLENOID STATES")
        print("=" * 60)
        
        results = {}
        
        # Try known DIDs (these are hypothetical - need discovery)
        dids_to_try = {
            0x1234: "Solenoid Commanded State",
            0x1235: "Solenoid Actual State",
            0x1236: "Transmission Status",
        }
        
        for did, description in dids_to_try.items():
            print(f"\nReading {description} (DID 0x{did:04X})...")
            data = self.read_data_by_identifier(did)
            
            if data:
                print(f"  ✓ Data: {data.hex()}")
                results[description] = data
            else:
                print(f"  ✗ Not available")
        
        return results
    
    def parse_solenoid_data(self, data: bytes) -> Dict[str, bool]:
        """
        Parse solenoid state data
        
        Args:
            data: Raw solenoid state bytes
            
        Returns:
            Dictionary mapping solenoid names to states (True=ON, False=OFF)
        """
        # CD4E transmission has 4 solenoids: SS1, SS2, SS3, EPC
        # Parsing depends on actual data format from TCM
        
        if len(data) < 1:
            return {}
        
        # Example parsing (actual format may differ)
        byte0 = data[0]
        
        solenoids = {
            "Shift Solenoid 1 (SS1)": bool(byte0 & 0x01),
            "Shift Solenoid 2 (SS2)": bool(byte0 & 0x02),
            "Shift Solenoid 3 (SS3)": bool(byte0 & 0x04),
            "EPC Solenoid": bool(byte0 & 0x08),
        }
        
        return solenoids
    
    def disconnect(self):
        """Close connections"""
        if self.isotp_socket:
            self.isotp_socket.close()
        if self.bus:
            self.bus.shutdown()
        print("\n✓ Disconnected")

def main():
    """Main execution"""
    
    # For Windows with ELM327 adapter, use python-can with serial interface
    # You may need to adjust interface and channel for your setup
    reader = FordTransmissionSolenoidReader(
        interface='socketcan',  # Change to 'pcan' or other if needed
        channel='can0',         # Change to your CAN channel
        bitrate=500000          # HS-CAN bitrate
    )
    
    if not reader.connect():
        return
    
    try:
        # Enter extended diagnostic session
        if not reader.enter_extended_session():
            print("\n⚠ Could not enter extended session")
            print("  Some DIDs may not be accessible")
        
        # Option 1: Discover DIDs (run once to find valid DIDs)
        print("\nDo you want to discover solenoid DIDs? (y/n)")
        if input().lower() == 'y':
            valid_dids = reader.discover_solenoid_dids()
            
            if valid_dids:
                print("\nValid DIDs found:")
                for did in valid_dids:
                    print(f"  0x{did:04X}")
        
        # Option 2: Read known DIDs
        else:
            results = reader.read_solenoid_states()
            
            if results:
                print("\n" + "=" * 60)
                print("SOLENOID STATE SUMMARY")
                print("=" * 60)
                
                for name, data in results.items():
                    print(f"\n{name}:")
                    solenoids = reader.parse_solenoid_data(data)
                    for sol_name, state in solenoids.items():
                        state_str = "ON" if state else "OFF"
                        print(f"  {sol_name}: {state_str}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reader.disconnect()

if __name__ == "__main__":
    main()
