"""
ELM327 OBD-II Adapter Communication Module
Handles serial communication with ELM327 adapter
"""

import serial
import time
from typing import Optional, List
import logging
from datetime import datetime
import os
import json

# Configure logging to suppress module name prefixes
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configure OBD traffic logger for debugging
obd_traffic_logger = logging.getLogger('obd_traffic')
obd_traffic_logger.setLevel(logging.DEBUG)
obd_traffic_logger.propagate = False  # Don't propagate to console/root logger

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Add file handler for OBD traffic (file only, no console output)
traffic_log_file = os.path.join('logs', f'obd_traffic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
traffic_handler = logging.FileHandler(traffic_log_file)
traffic_handler.setLevel(logging.DEBUG)
traffic_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
traffic_handler.setFormatter(traffic_formatter)
obd_traffic_logger.addHandler(traffic_handler)

# Parsed events JSONL file (for test fixtures / parsed output)
parsed_events_file = os.path.join('logs', f'parsed_events_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl')
# create empty file
with open(parsed_events_file, 'w', encoding='utf-8') as _f:
    pass

def _append_parsed_event(event: dict):
    """Append a parsed event (json) to the parsed events JSONL file."""
    try:
        with open(parsed_events_file, 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + '\n')
    except Exception as e:
        obd_traffic_logger.error(f"[PARSE-LOG-ERROR] Failed to append parsed event: {e}")


class ELM327Adapter:
    """Communication interface for ELM327 OBD-II adapter"""
    
    def __init__(self, port: str, baudrate: int = 38400, timeout: float = 2.0):
        """
        Initialize ELM327 adapter connection
        
        Args:
            port: Serial port (e.g., 'COM3', '/dev/ttyUSB0')
            baudrate: Serial communication speed (default 38400)
            timeout: Read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.traffic_log_file = traffic_log_file  # Store log file path for later retrieval
        
    def connect(self) -> bool:
        """
        Establish connection to ELM327 adapter
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            time.sleep(2)  # Wait for adapter to initialize
            
            # Initialize adapter
            if not self._send_command("AT Z"):  # Reset
                logger.error("Failed to reset adapter")
                return False
            
            if not self._send_command("AT E0"):  # Disable echo
                logger.error("Failed to disable echo")
                return False
            
            if not self._send_command("AT L0"):  # Disable linefeeds
                logger.error("Failed to disable linefeeds")
                return False
            
            # Get adapter version
            version = self._send_command("AT I")
            logger.info(f"Connected to ELM327: {version}")
            
            return True
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Close connection to adapter"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("Disconnected from adapter")
    
    def get_traffic_log_file(self) -> str:
        """
        Get the path to the OBD traffic log file for this session
        
        Returns:
            Absolute path to the traffic log file
        """
        return self.traffic_log_file
    
    def _send_command(self, command: str) -> Optional[str]:
        """
        Send AT command to adapter
        
        Args:
            command: AT command to send
            
        Returns:
            Response from adapter or None if error
        """
        try:
            # Log outgoing AT command
            obd_traffic_logger.debug(f"[TX] AT COMMAND: {command}")
            # Persist parsed TX event
            try:
                _append_parsed_event({
                    'timestamp': datetime.now().isoformat(),
                    'direction': 'TX',
                    'type': 'AT',
                    'command': command,
                    'raw': None
                })
            except Exception:
                pass

            self.serial_conn.write((command + "\r").encode())
            time.sleep(0.1)
            
            response = self._read_response(is_at_command=True, command=command)
            return response
            
        except serial.SerialException as e:
            logger.error(f"Serial error sending command '{command}': {e}")
            obd_traffic_logger.error(f"[ERROR] Serial error on AT command '{command}': {e}")
            return None
    
    def _read_response(self, is_at_command: bool = False, command: str = "") -> Optional[str]:
        """
        Read response from adapter until prompt
        
        Args:
            is_at_command: Whether this is an AT command response
            command: The command that was sent (for logging)
            
        Returns:
            Response string without prompts
        """
        response = ""
        prompt = ">"
        raw_data = ""
        
        try:
            while True:
                if self.serial_conn.in_waiting > 0:
                    byte_data = self.serial_conn.read()
                    char = byte_data.decode('utf-8', errors='ignore')
                    response += char
                    raw_data += char
                    
                    if response.endswith(prompt):
                        break
                else:
                    time.sleep(0.01)
                    
                # Timeout protection
                if len(response) > 1000:
                    break
                    
            # Clean response
            clean_response = response.replace(prompt, "").strip()
            
            # Log raw response with escape sequences visible
            log_label = "[AT RESPONSE]" if is_at_command else "[OBD RESPONSE]"
            raw_hex = ' '.join(f'{ord(c):02X}' for c in raw_data)
            obd_traffic_logger.debug(f"[RX] {log_label} Raw: {repr(raw_data[:100])} (HEX: {raw_hex[:60]}...)")
            obd_traffic_logger.debug(f"[RX] {log_label} Cleaned: {clean_response}")

            # Persist parsed RX event
            try:
                _append_parsed_event({
                    'timestamp': datetime.now().isoformat(),
                    'direction': 'RX',
                    'type': 'AT' if is_at_command else 'OBD',
                    'command': command,
                    'raw': raw_hex,
                    'clean': clean_response
                })
            except Exception:
                pass

            return clean_response if clean_response else None
            
        except Exception as e:
            logger.error(f"Error reading response: {e}")
            obd_traffic_logger.error(f"[ERROR] Error reading response: {e}")
            return None
    
    def set_can_bus(self, use_high: bool = True) -> bool:
        """
        Set CAN bus mode (High or Low)
        
        Args:
            use_high: True for High CAN, False for Low CAN
            
        Returns:
            True if successful
        """
        mode = "1" if use_high else "3"  # 1=High CAN 500k, 3=Low CAN 125k
        
        # Set protocol to CAN
        if not self._send_command(f"AT SP6"):  # Protocol 6 = CAN (29-bit IDs)
            logger.error("Failed to set CAN protocol")
            return False
        
        # Set CAN bus speed
        if not self._send_command(f"AT CRA {mode}"):
            logger.error(f"Failed to set CAN bus mode")
            return False
        
        logger.info(f"CAN bus set to {'High' if use_high else 'Low'} speed")
        return True
    
    def send_obd_command(self, command: str) -> Optional[str]:
        """
        Send OBD-II command and get response
        
        Args:
            command: OBD-II command (e.g., "0902" for VIN)
            
        Returns:
            Raw response from vehicle
        """
        try:
            # Parse OBD command for logging
            mode = command[:2] if len(command) >= 2 else "??"
            pid = command[2:] if len(command) > 2 else ""
            obd_traffic_logger.debug(f"[TX] OBD COMMAND: {command} (Mode: {mode}, PID: {pid})")
            # Persist parsed TX event
            try:
                _append_parsed_event({
                    'timestamp': datetime.now().isoformat(),
                    'direction': 'TX',
                    'type': 'OBD',
                    'command': command,
                    'raw': None
                })
            except Exception:
                pass

            self.serial_conn.write((command + "\r").encode())
            time.sleep(0.5)  # Wait for response
            
            response = self._read_response(is_at_command=False, command=command)
            
            # Log response status
            if response:
                obd_traffic_logger.debug(f"[RX] OBD Response received: {response[:80]}..." if len(response) > 80 else f"[RX] OBD Response: {response}")
            elif response == "NO DATA":
                obd_traffic_logger.info(f"[RX] No data from vehicle for command {command}")
            elif response == "?":
                obd_traffic_logger.warning(f"[RX] Invalid OBD command: {command}")
            else:
                obd_traffic_logger.warning(f"[RX] Unable to connect for command {command}")
            
            if response and response != "NO DATA" and response != "?" and response != "UNABLE TO CONNECT":
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error sending OBD command: {e}")
            obd_traffic_logger.error(f"[ERROR] Exception sending OBD command {command}: {e}")
            return None
    
    def get_adapter_settings(self) -> Optional[dict]:
        """
        Get detailed ELM327 adapter settings
        
        Returns:
            Dictionary with adapter settings or None
        """
        try:
            logger.info("Reading ELM327 adapter settings...")
            
            settings = {
                'adapter_id': self._send_command("AT I"),
                'version': self._send_command("AT I"),
                'voltage': self._send_command("AT RV"),
                'protocol': self._get_protocol(),
                'can_mode': self._get_can_mode(),
                'echo': self._send_command("AT TE"),
                'linefeeds': self._send_command("AT TL"),
                'timeout': self._send_command("AT ST"),
                'data_format': self._send_command("AT D1"),
                'vehicle_connected': self._send_command("AT DPN"),
            }
            
            return settings
            
        except Exception as e:
            logger.error(f"Error reading adapter settings: {e}")
            return None
    
    def _get_protocol(self) -> Optional[str]:
        """Get current OBD protocol"""
        try:
            response = self._send_command("AT DP")
            return response
        except Exception as e:
            logger.error(f"Error reading protocol: {e}")
            return None
    
    def _get_can_mode(self) -> Optional[str]:
        """Get current CAN bus mode"""
        try:
            response = self._send_command("AT CRA")
            return response
        except Exception as e:
            logger.error(f"Error reading CAN mode: {e}")
            return None
    
    def test_vehicle_connection(self) -> bool:
        """
        Test if vehicle is connected and responding
        
        Returns:
            True if vehicle is responding
        """
        try:
            logger.info("Testing vehicle connection...")
            
            # Try to read supported PIDs (mode 1, PID 00)
            response = self.send_obd_command("0100")
            
            if response and response != "NO DATA" and response != "?" and response != "UNABLE TO CONNECT":
                logger.info("✓ Vehicle is responding")
                return True
            else:
                logger.warning("✗ Vehicle is not responding")
                return False
                
        except Exception as e:
            logger.error(f"Error testing vehicle connection: {e}")
            return False
    
    def get_voltage(self) -> Optional[float]:
        """
        Get current voltage reading from adapter (OBD pin 16)
        Note: This reads ECU voltage through OBD protocol, not direct 12V
        
        Returns:
            Voltage value as float, or None if error
        """
        try:
            voltage_str = self._send_command("AT RV")
            if voltage_str:
                # Clean up response - remove command echo and any control characters
                voltage_str = voltage_str.replace('\r', ' ').replace('\n', ' ').strip()
                # Remove any echoed command at start
                if voltage_str.startswith('AT'):
                    voltage_str = voltage_str[2:].strip()
                
                if 'V' in voltage_str:
                    # Parse voltage (format: "12.5V" or just "12.5")
                    voltage_value = voltage_str.replace('V', '').replace('Volts', '').strip()
                    # Remove any remaining non-numeric characters except decimal point
                    voltage_value = ''.join(c for c in voltage_value if c.isdigit() or c == '.')
                    if voltage_value:
                        return float(voltage_value)
        except Exception as e:
            logger.error(f"Error reading voltage: {e}")
        
        return None
    
    def get_5v_reference(self) -> Optional[float]:
        """
        Get 5V reference voltage from adapter
        Note: Some adapters provide 5V reference for diagnostics
        
        Returns:
            5V reference voltage as float, or None if error
        """
        try:
            # Some ELM327 adapters have 5V reference output
            voltage_str = self._send_command("AT CV")
            if voltage_str:
                # Clean up response - remove command echo and any control characters
                voltage_str = voltage_str.replace('\r', ' ').replace('\n', ' ').strip()
                # Remove any echoed command at start
                if voltage_str.startswith('AT'):
                    voltage_str = voltage_str[2:].strip()
                
                if 'V' in voltage_str:
                    voltage_value = voltage_str.replace('V', '').replace('Volts', '').strip()
                    # Remove any remaining non-numeric characters except decimal point
                    voltage_value = ''.join(c for c in voltage_value if c.isdigit() or c == '.')
                    if voltage_value:
                        return float(voltage_value)
                return float(voltage_value)
        except Exception as e:
            logger.error(f"Error reading 5V reference: {e}")
        
        return None
    
    def get_emissions_monitor_status(self) -> Optional[dict]:
        """
        Get OBD emissions monitor readiness status (Mode 01, PID 01)
        Indicates if emissions tests have completed since DTC reset
        
        Returns:
            Dictionary with monitor status or None if error
            {
                'ready': bool,              # All monitors ready
                'pending_dtc': bool,        # Pending DTC exists
                'monitors': {
                    'misfire': bool,
                    'fuel_system': bool,
                    'evap': bool,
                    'o2_sensor': bool,
                    'o2_heater': bool,
                    'cat_monitor': bool,
                    'nox_absorber': bool,
                    'nox_catalyst': bool
                }
            }
        """
        try:
            # OBD Mode 01, PID 01 - Monitor status
            response = self.send_obd_command("0101")
            
            if not response or response == "NO DATA":
                logger.warning("No emissions monitor data available")
                return None
            
            # Parse response (typically returns 8 bytes)
            # Bit flags indicate monitor readiness
            result = {
                'ready': False,
                'pending_dtc': False,
                'monitors': {}
            }
            
            # Remove spaces from response
            data = response.replace(" ", "").upper()
            
            if len(data) >= 8:
                # First byte after mode/PID
                try:
                    # Check for pending DTC (bit 2 of first byte)
                    first_byte = int(data[2:4], 16)
                    result['pending_dtc'] = bool(first_byte & 0x02)
                    
                    # Get second byte with monitor readiness flags
                    if len(data) >= 12:
                        second_byte = int(data[4:6], 16)
                        result['monitors'] = {
                            'misfire': not bool(second_byte & 0x01),
                            'fuel_system': not bool(second_byte & 0x02),
                            'evap': not bool(second_byte & 0x04),
                            'o2_sensor': not bool(second_byte & 0x08),
                            'o2_heater': not bool(second_byte & 0x10),
                            'cat_monitor': not bool(second_byte & 0x20),
                            'nox_absorber': not bool(second_byte & 0x40),
                            'nox_catalyst': not bool(second_byte & 0x80)
                        }
                        
                        # Ready if all monitors are 1 (NOT incomplete)
                        result['ready'] = all(result['monitors'].values()) and not result['pending_dtc']
                    
                except ValueError:
                    logger.warning("Could not parse monitor status")
                    return None
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading emissions monitor status: {e}")
            return None
    
    def get_time_since_dtc_clear(self) -> Optional[int]:
        """
        Get time (in seconds) engine has been running since DTCs were cleared
        OBD Mode 01, PID 4E
        
        Returns:
            Time in seconds since DTC clear, or None if error
        """
        try:
            # OBD Mode 01, PID 4E - Time since DTC clear
            response = self.send_obd_command("014E")
            
            if not response or response == "NO DATA":
                logger.warning("Could not read time since DTC clear")
                return None
            
            # Parse response (typically 2 bytes = 0-65535 seconds)
            data = response.replace(" ", "").upper()
            
            if len(data) >= 8:
                try:
                    # Extract the data portion (after mode/PID)
                    time_bytes = data[4:8]  # 2 bytes of data
                    seconds = int(time_bytes, 16)
                    return seconds
                except ValueError:
                    logger.warning("Could not parse DTC clear time")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading time since DTC clear: {e}")
            return None

    def read_stored_dtcs(self) -> List[str]:
        """
        Read stored DTCs (Mode 03) and return a list of decoded DTC strings.

        Returns:
            List of DTC strings (e.g., ['P0123', 'C0567']) or empty list if none/error
        """
        try:
            resp = self.send_obd_command("03")
            if not resp:
                return []
            # normalize and split into bytes
            parts = resp.replace('\r', ' ').replace('\n', ' ').strip().split()
            bytes_list: List[int] = []
            for p in parts:
                try:
                    bytes_list.append(int(p, 16))
                except Exception:
                    continue
            if not bytes_list:
                return []
            # If first byte is 0x43 (response code for Mode 03), skip it
            if bytes_list[0] == 0x43:
                data_bytes = bytes_list[1:]
            else:
                data_bytes = bytes_list
            dtcs: List[str] = []
            for i in range(0, len(data_bytes), 2):
                if i + 1 >= len(data_bytes):
                    break
                A = data_bytes[i]
                B = data_bytes[i + 1]
                if A == 0 and B == 0:
                    continue
                letter_map = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}
                letter = letter_map.get((A & 0xC0) >> 6, '?')
                code_num = ((A & 0x3F) << 8) | B
                dtc = f"{letter}{code_num:04X}"
                dtcs.append(dtc)
            return dtcs
        except Exception as e:
            logger.error(f"Error reading stored DTCs: {e}")
            return []
    
    def get_emission_readiness_status(self) -> dict:
        """
        Get comprehensive emissions readiness status and pass/fail assessment
        
        Returns:
            Dictionary with readiness info:
            {
                'monitors_ready': bool,
                'time_since_clear': int or None,      # seconds
                'time_formatted': str,
                'pending_dtc': bool,
                'completion_percent': int,
                'pass_emission_test': bool,
                'message': str
            }
        """
        result = {
            'monitors_ready': False,
            'time_since_clear': None,
            'time_formatted': 'Unknown',
            'pending_dtc': False,
            'completion_percent': 0,
            'pass_emission_test': False,
            'message': ''
        }
        
        try:
            # Read stored DTCs (Mode 03) using public helper
            try:
                stored_dtcs = self.read_stored_dtcs()
            except Exception:
                stored_dtcs = []
            result['stored_dtcs'] = stored_dtcs
            # Get monitor status
            monitors = self.get_emissions_monitor_status()
            if monitors:
                result['monitors_ready'] = monitors['ready']
                result['pending_dtc'] = monitors['pending_dtc']
                
                # Calculate completion percentage
                if monitors['monitors']:
                    ready_count = sum(1 for v in monitors['monitors'].values() if v)
                    total_count = len(monitors['monitors'])
                    result['completion_percent'] = int((ready_count / total_count) * 100)
            
            # Get time since clear
            time_seconds = self.get_time_since_dtc_clear()
            if time_seconds is not None:
                result['time_since_clear'] = time_seconds
                
                # Format time
                hours = time_seconds // 3600
                minutes = (time_seconds % 3600) // 60
                secs = time_seconds % 60
                result['time_formatted'] = f"{hours}h {minutes}m {secs}s"
            
            # Determine emission test passage
            # Vehicle typically needs:
            # 1. All monitors ready OR completed
            # 2. No pending DTCs
            # 3. Run time of at least 50-100 miles (varies by state)
            if result['monitors_ready'] and not result['pending_dtc']:
                result['pass_emission_test'] = True
                result['message'] = "✓ Vehicle READY for emission test (all monitors complete)"
            elif result['completion_percent'] >= 80 and not result['pending_dtc']:
                result['pass_emission_test'] = True
                result['message'] = f"✓ Vehicle LIKELY READY ({result['completion_percent']}% monitors complete, no pending codes)"
            elif result['completion_percent'] >= 50 and not result['pending_dtc']:
                result['pass_emission_test'] = False
                result['message'] = f"⚠ In Progress ({result['completion_percent']}% monitors complete) - Continue driving"
            elif result['pending_dtc']:
                result['pass_emission_test'] = False
                result['message'] = "✗ Pending DTC detected - Will FAIL emission test. Clear codes and drive vehicle."
            else:
                result['pass_emission_test'] = False
                result['message'] = "⚠ Monitors not ready - Continue normal driving (100+ miles typically needed)"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting emission readiness: {e}")
            result['message'] = f"Error reading emissions data: {e}"
            return result
    
    def verify_vehicle_connection(self) -> dict:
        """
        Verify if a vehicle is connected by checking voltages and protocol
        
        Returns:
            Dictionary with verification results:
            {
                'connected': bool,
                'ecu_voltage': float or None,
                'ref_5v': float or None,
                'has_voltage': bool,
                'protocol_detected': bool,
                'protocol': str or None,
                'message': str
            }
        """
        result = {
            'connected': False,
            'ecu_voltage': None,
            'ref_5v': None,
            'has_voltage': False,
            'protocol_detected': False,
            'protocol': None,
            'message': ''
        }
        
        try:
            # Check ECU voltage (from OBD protocol)
            ecu_voltage = self.get_voltage()
            result['ecu_voltage'] = ecu_voltage
            
            # Check 5V reference (adapter diagnostics)
            ref_5v = self.get_5v_reference()
            result['ref_5v'] = ref_5v
            
            # Determine if we have valid voltage
            if ecu_voltage is not None and ecu_voltage > 2.0:
                result['has_voltage'] = True
                logger.info(f"✓ ECU voltage detected: {ecu_voltage:.1f}V")
            elif ref_5v is not None and ref_5v > 1.0:
                result['has_voltage'] = True
                logger.info(f"✓ 5V reference detected: {ref_5v:.1f}V")
            else:
                logger.warning(f"⚠ No valid voltage detected (ECU: {ecu_voltage}, 5V: {ref_5v})")
                result['message'] = "No voltage detected from vehicle. Check OBD-II connection and vehicle power."
            
            if ecu_voltage is not None and ecu_voltage < 2.0:
                logger.warning(f"⚠ Low ECU voltage: {ecu_voltage:.1f}V")

                logger.warning("⚠ Could not read voltage")
                result['message'] = "Could not read adapter voltage"
            
            # Check if adapter detects vehicle
            vehicle_status = self.test_vehicle_connection()
            if vehicle_status:
                logger.info("✓ Vehicle communication detected")
                result['connected'] = True
                result['protocol_detected'] = True
            else:
                logger.warning("⚠ Vehicle communication not detected")
                if not result['message']:
                    result['message'] = "Adapter is working but no vehicle communication detected."
            
            # Try to get protocol
            protocol = self._get_protocol()
            result['protocol'] = protocol
            
            if protocol and protocol != "?":
                logger.info(f"✓ Protocol detected: {protocol}")
            
            # Final verdict
            if result['has_voltage'] and result['connected']:
                result['message'] = "✓ Vehicle is properly connected"
            elif result['has_voltage'] and not result['connected']:
                result['message'] = "⚠ Adapter has power but vehicle not responding. Check CAN bus connection."
            elif not result['has_voltage']:
                result['message'] = "✗ No power from vehicle. Check OBD-II port and vehicle ignition."
            
            return result
            
        except Exception as e:
            logger.error(f"Error verifying vehicle connection: {e}")
            result['message'] = f"Error checking vehicle: {e}"
            return result
    
    def display_settings(self):
        """Display adapter settings in formatted output"""
        settings = self.get_adapter_settings()
        
        if not settings:
            logger.error("Failed to read adapter settings")
            return
        
        logger.info("\n" + "=" * 60)
        logger.info("ELM327 ADAPTER SETTINGS")
        logger.info("=" * 60)
        
        logger.info(f"Adapter ID: {settings.get('adapter_id', 'N/A')}")
        logger.info(f"Voltage: {settings.get('voltage', 'N/A')}")
        logger.info(f"Protocol: {settings.get('protocol', 'N/A')}")
        logger.info(f"CAN Mode: {settings.get('can_mode', 'N/A')}")
        logger.info(f"Echo: {settings.get('echo', 'N/A')}")
        logger.info(f"Linefeeds: {settings.get('linefeeds', 'N/A')}")
        logger.info(f"Timeout: {settings.get('timeout', 'N/A')}")
        logger.info(f"Vehicle Connected: {settings.get('vehicle_connected', 'N/A')}")
        
        logger.info("\n" + "=" * 60)
