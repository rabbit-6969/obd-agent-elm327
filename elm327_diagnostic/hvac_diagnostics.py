"""
HVAC (Heating, Ventilation, Air Conditioning) Diagnostics Module
Reads HVAC errors and DTCs (Diagnostic Trouble Codes) from Ford vehicles
"""

import logging
from typing import List, Dict, Optional
from elm327_adapter import ELM327Adapter

# Configure logging to suppress module name prefixes
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class HVACDiagnostics:
    """Reads HVAC errors and diagnostic trouble codes from vehicles"""
    
    # Ford HVAC related DTCs
    FORD_HVAC_CODES = {
        # Stuck/Faulty HVAC Actuator Codes
        "P1632": "HVAC Mix Door Actuator Circuit - Stuck",
        "P1633": "HVAC Mode Door Actuator Circuit - Stuck",
        "P1634": "HVAC Vent Door Actuator Circuit - Stuck",
        "P1635": "HVAC Blend Door Actuator - Stuck/Malfunction",
        "P1636": "HVAC Mode Door Actuator - Stuck/Malfunction",
        "P1638": "HVAC Recirculation Door Actuator - Stuck",
        "P1639": "HVAC Mix Door Actuator - Stuck Open",
        "P1640": "HVAC Mode Door Actuator - Stuck Position",
        "P1679": "HVAC Door Position Sensor Circuit Malfunction",
        "P1680": "HVAC Door Position Feedback Malfunction",
        
        # AC Compressor Codes
        "P0656": "Fuel Pump Control Module Output Driver Fault",
        "P0533": "A/C Refrigerant Charge Loss",
        "P0534": "A/C Refrigerant Charge Loss - Excessive",
        "P1456": "Evaporation System - Leak Detection Pump Error",
        "P1457": "Evaporation System - Leak Detection Pump Disabled",
        "P1460": "Cooling Fan Relay Control Circuit",
        
        # Blend Door/Mode Door Codes
        "P1473": "Cooling Fan Relay Control",
        "P1474": "Cooling Fan Relay Control Circuit",
        
        # Temperature Sensor Codes
        "P0117": "Engine Coolant Temperature Sensor Low Input",
        "P0118": "Engine Coolant Temperature Sensor High Input",
        "P0519": "Idle Air Control System Malfunction",
        
        # HVAC Control Module
        "P1677": "Cruise Control Deactivated - Clutch or Brake",
        # Manufacturer-specific / chassis codes
        "C7F19": "Ford manufacturer-specific chassis/HVAC code - consult Ford service manual or dealer for exact definition",
    }
    
    def __init__(self, adapter: ELM327Adapter):
        """
        Initialize HVAC diagnostics
        
        Args:
            adapter: ELM327Adapter instance
        """
        self.adapter = adapter
    
    def read_dtc_codes(self) -> Optional[List[Dict]]:
        """
        Read all Diagnostic Trouble Codes (DTCs) from vehicle
        
        Returns:
            List of DTC dictionaries with code and description, or None if error
        """
        try:
            logger.info("Reading DTC codes from vehicle...")
            
            # Command 19 = Read DTC codes
            response = self.adapter.send_obd_command("19")
            
            if not response:
                logger.warning("No DTC codes found")
                return []
            
            dtc_list = self._parse_dtc_response(response)
            
            if dtc_list:
                logger.info(f"Found {len(dtc_list)} DTC code(s)")
                for dtc in dtc_list:
                    logger.info(f"  {dtc['code']}: {dtc['description']}")
            
            return dtc_list
            
        except Exception as e:
            logger.error(f"Error reading DTC codes: {e}")
            return None
    
    def read_pending_dtc_codes(self) -> Optional[List[Dict]]:
        """
        Read Pending (intermittent) DTC codes
        
        Returns:
            List of pending DTC dictionaries
        """
        try:
            logger.info("Reading pending DTC codes...")
            
            # Command 07 = Read pending DTCs
            response = self.adapter.send_obd_command("07")
            
            if not response:
                logger.info("No pending DTC codes found")
                return []
            
            dtc_list = self._parse_dtc_response(response)
            return dtc_list
            
        except Exception as e:
            logger.error(f"Error reading pending DTCs: {e}")
            return None
    
    def _parse_dtc_response(self, response: str) -> List[Dict]:
        """
        Parse DTC codes from OBD-II response
        
        OBD-II response format for DTCs:
        Response header + DTC bytes (4 nibbles each)
        
        Args:
            response: Raw OBD-II response
            
        Returns:
            List of DTC dictionaries
        """
        try:
            # Remove spaces and convert to uppercase
            response = response.replace(" ", "").upper()
            
            dtc_list = []
            
            # Skip response header (first 2 bytes typically)
            if response.startswith("59"):  # Standard response header for mode 19
                response = response[2:]
            elif response.startswith("47"):  # Response header for mode 07
                response = response[2:]
            
            # Each DTC is 4 hex digits (2 bytes)
            for i in range(0, len(response), 4):
                if i + 3 < len(response):
                    dtc_hex = response[i:i+4]
                    dtc_code = self._hex_to_dtc_code(dtc_hex)
                    
                    if dtc_code:
                        description = self.FORD_HVAC_CODES.get(dtc_code)
                        if not description:
                            description = f"Unknown DTC code (raw: {dtc_hex}) - consult Ford service manual or dealer"
                        
                        dtc_list.append({
                            'code': dtc_code,
                            'hex': dtc_hex,
                            'description': description
                        })
            
            return dtc_list
            
        except Exception as e:
            logger.error(f"Error parsing DTC response: {e}")
            return []
    
    def _hex_to_dtc_code(self, hex_code: str) -> Optional[str]:
        """
        Convert hex DTC bytes to standard DTC code format
        
        DTC format: P/C/B + 4 digits
        First byte determines type:
        00-3F = P (Powertrain)
        40-7F = C (Chassis)
        80-BF = B (Body)
        C0-FF = U (Network)
        
        Args:
            hex_code: 4-digit hex DTC code
            
        Returns:
            Standard DTC code (e.g., "P0633")
        """
        try:
            if len(hex_code) != 4:
                return None
            
            # Convert to integer
            dtc_int = int(hex_code, 16)
            
            # Extract first byte and determine type
            first_byte = (dtc_int >> 8) & 0xFF
            
            if first_byte < 0x40:
                dtc_type = 'P'
            elif first_byte < 0x80:
                dtc_type = 'C'
            elif first_byte < 0xC0:
                dtc_type = 'B'
            else:
                dtc_type = 'U'
            
            # Extract remaining 3 digits
            code_number = dtc_int & 0xFFFF
            dtc_code = f"{dtc_type}{code_number:04X}"
            
            return dtc_code
            
        except Exception as e:
            logger.error(f"Error converting hex to DTC: {e}")
            return None
    
    def clear_dtc_codes(self) -> bool:
        """
        Clear all DTC codes from vehicle
        
        Returns:
            True if successful
        """
        try:
            logger.warning("Clearing all DTC codes...")
            
            # Command 14 = Clear DTCs
            response = self.adapter.send_obd_command("14")
            
            if response:
                logger.info("DTC codes cleared successfully")
                return True
            else:
                logger.error("Failed to clear DTC codes")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing DTC codes: {e}")
            return False
    
    def get_hvac_module_info(self) -> Optional[Dict]:
        """
        Get detailed HVAC module information
        
        Returns:
            Dictionary with module serial, version, voltage, etc.
        """
        try:
            logger.info("Reading HVAC module information...")
            
            module_info = {
                'serial_number': self._read_module_serial(),
                'part_number': self._read_module_part_number(),
                'software_version': self._read_module_software_version(),
                'hardware_version': self._read_module_hardware_version(),
                'voltage_supply': self._read_module_voltage(),
                'current_draw': self._read_module_current(),
                'module_temperature': self._read_module_temperature(),
            }
            
            return module_info
            
        except Exception as e:
            logger.error(f"Error reading HVAC module info: {e}")
            return None
    
    def _read_module_serial(self) -> Optional[str]:
        """
        Read HVAC module serial number
        
        Returns:
            Serial number or None
        """
        try:
            # Service 1A = Read DLC Information (module data)
            # SubID 81 = Module Serial Number
            response = self.adapter.send_obd_command("1A81")
            
            if response:
                # Parse serial number from response
                serial = self._parse_module_data(response)
                if serial:
                    logger.info(f"Module Serial: {serial}")
                return serial
            return None
            
        except Exception as e:
            logger.error(f"Error reading module serial: {e}")
            return None
    
    def _read_module_part_number(self) -> Optional[str]:
        """
        Read HVAC module part number
        
        Returns:
            Part number or None
        """
        try:
            # Service 1A = Read DLC Information
            # SubID 82 = Module Part Number
            response = self.adapter.send_obd_command("1A82")
            
            if response:
                part_num = self._parse_module_data(response)
                if part_num:
                    logger.info(f"Module Part Number: {part_num}")
                return part_num
            return None
            
        except Exception as e:
            logger.error(f"Error reading module part number: {e}")
            return None
    
    def _read_module_software_version(self) -> Optional[str]:
        """
        Read HVAC module software/firmware version
        
        Returns:
            Software version or None
        """
        try:
            # Service 1A = Read DLC Information
            # SubID 83 = Software Version
            response = self.adapter.send_obd_command("1A83")
            
            if response:
                software_ver = self._parse_module_data(response)
                if software_ver:
                    logger.info(f"Software Version: {software_ver}")
                return software_ver
            return None
            
        except Exception as e:
            logger.error(f"Error reading software version: {e}")
            return None
    
    def _read_module_hardware_version(self) -> Optional[str]:
        """
        Read HVAC module hardware version
        
        Returns:
            Hardware version or None
        """
        try:
            # Service 1A = Read DLC Information
            # SubID 84 = Hardware Version
            response = self.adapter.send_obd_command("1A84")
            
            if response:
                hardware_ver = self._parse_module_data(response)
                if hardware_ver:
                    logger.info(f"Hardware Version: {hardware_ver}")
                return hardware_ver
            return None
            
        except Exception as e:
            logger.error(f"Error reading hardware version: {e}")
            return None
    
    def _read_module_voltage(self) -> Optional[str]:
        """
        Read HVAC module supply voltage
        
        Returns:
            Voltage in volts (e.g., "12.5V") or None
        """
        try:
            # OBD-II PID 42 = Control Module Voltage
            response = self.adapter.send_obd_command("0142")
            
            if response:
                # Parse hex response to voltage
                # Format: two bytes representing voltage (MSB, LSB)
                # Voltage = (A*256 + B)/1000 volts
                voltage = self._parse_voltage(response)
                if voltage:
                    logger.info(f"Module Voltage: {voltage}V")
                return voltage
            return None
            
        except Exception as e:
            logger.error(f"Error reading module voltage: {e}")
            return None
    
    def _read_module_current(self) -> Optional[str]:
        """
        Read HVAC module current draw
        
        Returns:
            Current in amps or None
        """
        try:
            # Some Ford modules report current via PID 4D or custom PIDs
            response = self.adapter.send_obd_command("014D")
            
            if response:
                current = self._parse_current(response)
                if current:
                    logger.info(f"Module Current: {current}A")
                return current
            return None
            
        except Exception as e:
            logger.error(f"Error reading module current: {e}")
            return None
    
    def _read_module_temperature(self) -> Optional[str]:
        """
        Read HVAC module internal temperature
        
        Returns:
            Temperature in Celsius or None
        """
        try:
            # OBD-II PID 3C = Catalyst Temperature (can indicate module temp)
            response = self.adapter.send_obd_command("013C")
            
            if response:
                temp = self._parse_temperature(response)
                if temp:
                    logger.info(f"Module Temperature: {temp}°C")
                return temp
            return None
            
        except Exception as e:
            logger.error(f"Error reading module temperature: {e}")
            return None
    
    def _parse_module_data(self, response: str) -> Optional[str]:
        """
        Parse module data (serial, part number, versions)
        
        Args:
            response: Raw response from adapter
            
        Returns:
            Parsed data string or None
        """
        try:
            response = response.replace(" ", "").upper()
            
            # Convert hex ASCII to string
            result = ""
            for i in range(0, len(response), 2):
                if i + 1 < len(response):
                    hex_pair = response[i:i+2]
                    try:
                        char_code = int(hex_pair, 16)
                        if 32 <= char_code <= 126:
                            result += chr(char_code)
                    except ValueError:
                        continue
            
            return result if result else None
            
        except Exception as e:
            logger.error(f"Error parsing module data: {e}")
            return None
    
    def _parse_voltage(self, response: str) -> Optional[str]:
        """
        Parse voltage from OBD-II response
        
        Args:
            response: Response containing voltage bytes
            
        Returns:
            Voltage string (e.g., "12.5V")
        """
        try:
            response = response.replace(" ", "").upper()
            
            if response.startswith("4142"):  # Response header for PID 42
                response = response[4:]
            
            if len(response) >= 4:
                # First two hex digits = MSB, next two = LSB
                msb = int(response[0:2], 16)
                lsb = int(response[2:4], 16)
                
                # Voltage calculation: (MSB*256 + LSB)/1000
                voltage = (msb * 256 + lsb) / 1000.0
                return f"{voltage:.1f}V"
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing voltage: {e}")
            return None
    
    def _parse_current(self, response: str) -> Optional[str]:
        """
        Parse current from OBD-II response
        
        Args:
            response: Response containing current bytes
            
        Returns:
            Current string (e.g., "5.2A")
        """
        try:
            response = response.replace(" ", "").upper()
            
            if response.startswith("414D"):  # Response header
                response = response[4:]
            
            if len(response) >= 4:
                msb = int(response[0:2], 16)
                lsb = int(response[2:4], 16)
                
                # Current = (MSB*256 + LSB)/100 amps
                current = (msb * 256 + lsb) / 100.0
                return f"{current:.1f}A"
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing current: {e}")
            return None
    
    def _parse_temperature(self, response: str) -> Optional[str]:
        """
        Parse temperature from OBD-II response
        
        Args:
            response: Response containing temperature bytes
            
        Returns:
            Temperature string (e.g., "45°C")
        """
        try:
            response = response.replace(" ", "").upper()
            
            if response.startswith("413C"):  # Response header
                response = response[4:]
            
            if len(response) >= 4:
                msb = int(response[0:2], 16)
                lsb = int(response[2:4], 16)
                
                # Temperature = (MSB*256 + LSB)/10 - 40 in Celsius
                temp = ((msb * 256 + lsb) / 10.0) - 40
                return f"{temp:.1f}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing temperature: {e}")
            return None
    
    def get_hvac_status(self) -> Optional[Dict]:
        """
        Get HVAC system status information
        
        Returns:
            Dictionary with HVAC status information
        """
        try:
            logger.info("Reading HVAC status...")
            
            hvac_status = {
                'ac_pressure_high': self._read_pid("10F"),  # AC Pressure (PSI)
                'ac_pressure_low': self._read_pid("110"),   # AC Pressure (PSI)
                'coolant_temp': self._read_pid("05"),       # Engine Coolant Temp
                'ambient_temp': self._read_pid("01"),       # Ambient Temp
            }
            
            return hvac_status
            
        except Exception as e:
            logger.error(f"Error reading HVAC status: {e}")
            return None
    
    def _read_pid(self, pid: str) -> Optional[str]:
        """
        Read a specific PID value
        
        Args:
            pid: PID code to read
            
        Returns:
            PID value or None
        """
        try:
            # Command 01 = Read data
            response = self.adapter.send_obd_command(f"01{pid}")
            return response
        except Exception as e:
            logger.error(f"Error reading PID {pid}: {e}")
            return None
