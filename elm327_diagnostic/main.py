"""
Main program for ELM327 OBD-II diagnostics
Connects to car, reads VIN, and retrieves HVAC errors
Optimized for 2008 Ford Escape
"""

import sys
import logging
from typing import Optional
from elm327_adapter import ELM327Adapter
from vin_reader import VINReader
from hvac_diagnostics import HVACDiagnostics
from can_bus_explorer import CANBusExplorer
from ui_formatter import UIFormatter
from com_port_detector import COMPortDetector

# Configure logging - minimal format for cleaner UI
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)
ui = UIFormatter()


class DiagnosticTool:
    """Main diagnostic tool for vehicle OBD-II communication"""
    
    def __init__(self, port: str = "COM3"):
        """
        Initialize diagnostic tool
        
        Args:
            port: Serial port for ELM327 adapter
        """
        self.port = port
        self.adapter = ELM327Adapter(port)
        self.vin_reader = None
        self.hvac_diagnostics = None
        self.can_explorer = None
        self.vehicle_info = {
            'vin': None,
            'dtc_codes': [],
            'pending_codes': [],
            'module_info': {},
            'hvac_status': {},
            'can_modules': []
        }
    
    def connect(self) -> bool:
        """
        Connect to vehicle via ELM327 adapter
        
        Returns:
            True if connection successful
        """
        print(ui.header("ELM327 OBD-II Diagnostic Tool - Ford Escape 2008"))
        
        print(f"\nAttempting to connect to adapter on {self.port}...")
        
        if not self.adapter.connect():
            print(ui.failure("Failed to connect to ELM327 adapter"))
            print("\nWould you like to select a different COM port? (y/n): ", end="")
            choice = input().strip().lower()
            
            if choice == 'y':
                if self.select_and_connect_port():
                    return True
            
            return False
        
        # Initialize readers
        self.vin_reader = VINReader(self.adapter)
        self.hvac_diagnostics = HVACDiagnostics(self.adapter)
        self.can_explorer = CANBusExplorer(self.adapter)
        
        print(ui.success("Connected to ELM327 adapter successfully\n"))
        return True
    
    def select_and_connect_port(self) -> bool:
        """
        Let user select a COM port from available options
        
        Returns:
            True if successfully connected to selected port
        """
        print("\n" + ui.header("SELECT COM PORT"))
        
        print("\nScanning for available COM ports...")
        ports = COMPortDetector.get_accessible_ports()
        
        if not ports:
            print(ui.warning("No accessible COM ports found"))
            print(ui.info("Check that your ELM327 adapter is connected", indent=2))
            return False
        
        print(ui.success(f"Found {len(ports)} accessible port(s):\n", indent=2))
        
        for i, (port_name, port_desc) in enumerate(ports, 1):
            print(f"  {i}. {port_name:<6} - {port_desc}")
        
        print()
        while True:
            try:
                choice = input("Select port number (or 'c' to cancel): ").strip()
                
                if choice.lower() == 'c':
                    print("Cancelled")
                    return False
                
                idx = int(choice) - 1
                if 0 <= idx < len(ports):
                    selected_port = ports[idx][0]
                    print(f"\nAttempting to connect to {selected_port}...")
                    
                    # Create new adapter with selected port
                    self.port = selected_port
                    self.adapter = ELM327Adapter(selected_port)
                    
                    if self.adapter.connect():
                        # Initialize readers
                        self.vin_reader = VINReader(self.adapter)
                        self.hvac_diagnostics = HVACDiagnostics(self.adapter)
                        self.can_explorer = CANBusExplorer(self.adapter)
                        
                        print(ui.success(f"Successfully connected to {selected_port}\n"))
                        return True
                    else:
                        print(ui.failure(f"Failed to connect to {selected_port}"))
                        print("Try another port? (y/n): ", end="")
                        if input().strip().lower() != 'y':
                            return False
                else:
                    print(ui.failure("Invalid selection"))
            
            except ValueError:
                print(ui.failure("Please enter a valid number"))
    
    def verify_vehicle(self) -> bool:
        """
        Verify if a vehicle is connected
        Checks ECU voltage, 5V reference, vehicle communication, and emissions readiness
        
        Returns:
            True if vehicle is connected and responding
        """
        print(ui.header("VEHICLE DETECTION"))
        
        verification = self.adapter.verify_vehicle_connection()
        
        print()
        print(ui.info("Voltage Readings:", indent=2))
        
        # ECU Voltage reading
        if verification['ecu_voltage'] is not None:
            ecu_voltage_display = ui.success(f"ECU Voltage: {verification['ecu_voltage']:.1f}V", indent=4)
        else:
            ecu_voltage_display = ui.info("ECU Voltage: Unable to read", indent=4)
        print(ecu_voltage_display)
        
        # 5V Reference reading
        if verification['ref_5v'] is not None:
            ref_5v_display = ui.success(f"5V Reference: {verification['ref_5v']:.1f}V", indent=4)
        else:
            ref_5v_display = ui.info("5V Reference: Not available", indent=4)
        print(ref_5v_display)
        
        print()
        print(ui.info("Power Status:", indent=2))
        if verification['has_voltage']:
            print(ui.success("Power: ✓ Valid voltage detected", indent=4))
        else:
            print(ui.failure("Power: ✗ No/Low voltage", indent=4))
        
        print()

        print(ui.info("Vehicle Communication:", indent=2))
        
        if verification['protocol_detected']:
            print(ui.success("Protocol: Detected", indent=4))
        else:
            print(ui.failure("Protocol: Not detected", indent=4))
        
        if verification['connected']:
            print(ui.success("Vehicle: Responding", indent=4))
        else:
            print(ui.failure("Vehicle: Not responding", indent=4))
        
        # Get emissions readiness status if vehicle is connected
        print()
        print(ui.info("Emissions Monitoring:", indent=2))
        
        if verification['connected']:
            emissions = self.adapter.get_emission_readiness_status()
            
            # Monitor readiness
            if emissions['monitors_ready']:
                print(ui.success(f"Monitors: ✓ ALL READY ({emissions['completion_percent']}%)", indent=4))
            else:
                print(ui.info(f"Monitors: {emissions['completion_percent']}% Complete", indent=4))
            
            # Time since DTC clear
            if emissions['time_since_clear'] is not None:
                print(ui.info(f"Running Time: {emissions['time_formatted']} since DTC reset", indent=4))
            else:
                print(ui.info(f"Running Time: Unknown", indent=4))
            
            # Pending DTCs
            if emissions['pending_dtc']:
                print(ui.failure("Status: ✗ Pending DTC codes detected", indent=4))
            else:
                print(ui.success("Status: ✓ No pending codes", indent=4))
            
            print()
            print(ui.info("Emission Test Readiness:", indent=2))
            
            # Final verdict on emission test passage
            if emissions['pass_emission_test']:
                print(ui.success(emissions['message'], indent=4))
            else:
                print(ui.warning(emissions['message'], indent=4))
        else:
            print(ui.warning("Unable to read emissions data - vehicle not responding", indent=4))
        
        print()
        if verification['has_voltage'] and verification['connected']:
            print(ui.success(verification['message'], indent=2))
            return True
        else:
            print(ui.warning(verification['message'], indent=2))
            return False
    
    def run_full_diagnostic(self, use_high_can: bool = True) -> bool:
        """
        Run full diagnostic sequence
        
        Args:
            use_high_can: Use High CAN (True) or Low CAN (False)
            
        Returns:
            True if diagnostic completed
        """
        try:
            # Set CAN bus mode
            print("\nSetting up CAN bus...")
            if not self.adapter.set_can_bus(use_high_can):
                print(ui.failure("Failed to set CAN bus"))
                return False
            
            # Read VIN
            print(ui.header("READING VEHICLE IDENTIFICATION NUMBER (VIN)"))
            vin = self.vin_reader.read_vin()
            
            if vin:
                self.vehicle_info['vin'] = vin
                print(ui.success(f"VIN: {vin}", indent=2))
                
                # Validate VIN format
                if self.vin_reader.validate_vin(vin):
                    print(ui.success("VIN validation: PASSED", indent=2))
                else:
                    print(ui.warning("VIN validation: FAILED", indent=2))
            else:
                print(ui.failure("Failed to read VIN", indent=2))
            
            # Read DTC codes
            print(ui.header("READING DIAGNOSTIC TROUBLE CODES (DTCs)"))
            dtc_codes = self.hvac_diagnostics.read_dtc_codes()
            
            if dtc_codes:
                self.vehicle_info['dtc_codes'] = dtc_codes
                print(ui.success(f"Found {len(dtc_codes)} active DTC code(s):", indent=2))
                for i, dtc in enumerate(dtc_codes, 1):
                    print(f"  {i}. {dtc['code']}: {dtc['description']}")
            else:
                print(ui.success("No active DTC codes found", indent=2))
            
            # Read pending codes
            print(ui.header("READING PENDING CODES"))
            pending_codes = self.hvac_diagnostics.read_pending_dtc_codes()
            
            if pending_codes:
                self.vehicle_info['pending_codes'] = pending_codes
                print(ui.success(f"Found {len(pending_codes)} pending DTC code(s):", indent=2))
                for i, dtc in enumerate(pending_codes, 1):
                    print(f"  {i}. {dtc['code']}: {dtc['description']}")
            else:
                print(ui.success("No pending codes found", indent=2))
            
            # Read HVAC module information
            print(ui.header("READING HVAC MODULE INFORMATION"))
            module_info = self.hvac_diagnostics.get_hvac_module_info()
            
            if module_info:
                self.vehicle_info['module_info'] = module_info
                print(ui.success("HVAC Module Details:", indent=2))
                for key, value in module_info.items():
                    if value:
                        print(ui.info(f"{key.replace('_', ' ').title()}: {value}", indent=4))
            else:
                print(ui.warning("Could not read HVAC module information", indent=2))
            
            # Read HVAC status
            print(ui.header("READING HVAC STATUS"))
            hvac_status = self.hvac_diagnostics.get_hvac_status()
            
            if hvac_status:
                self.vehicle_info['hvac_status'] = hvac_status
                print(ui.success("HVAC Status:", indent=2))
                for key, value in hvac_status.items():
                    print(ui.info(f"{key}: {value}", indent=4))
            else:
                print(ui.warning("Could not read HVAC status", indent=2))
            
            return True
            
        except Exception as e:
            print(ui.failure(f"Error during diagnostic: {e}"))
            return False
    
    def run_can_bus_exploration(self, duration: int = 30) -> bool:
        """
        Run basic CAN bus exploration to discover all modules
        Passive monitoring - just listen to traffic
        
        Args:
            duration: Capture duration in seconds
            
        Returns:
            True if exploration completed
        """
        try:
            print(ui.header("CAN BUS EXPLORER - BASIC MODULE DISCOVERY"))
            print(f"Capturing CAN bus traffic for {duration} seconds...")
            print("This passively discovers all active modules on the vehicle\n")
            
            # Start monitoring
            frames = self.can_explorer.start_monitoring(duration=duration)
            
            if not frames:
                print(ui.warning("No frames captured"))
                return False
            
            # Discover modules
            modules = self.can_explorer.discover_modules()
            self.vehicle_info['can_modules'] = modules
            
            print(ui.success(f"Discovered {len(modules)} active modules:\n", indent=2))
            for module in modules:
                print(f"  ID: {module['id']} - {module['name']}")
                print(f"    Sample Data: {module['sample_data']}")
            
            # Print summary
            self.can_explorer.print_summary()
            
            # Export data
            export_file = "can_capture.txt"
            if self.can_explorer.export_frames_to_text(export_file):
                print(ui.success(f"Capture data exported to: {export_file}", indent=2))
            
            return True
            
        except Exception as e:
            print(ui.failure(f"Error during CAN bus exploration: {e}"))
            return False
    
    def run_can_bus_exploration_both_modes(self, duration: int = 20) -> bool:
        """
        Run CAN bus exploration on both HIGH and LOW CAN modes
        
        Args:
            duration: Capture duration per mode in seconds
            
        Returns:
            True if exploration completed
        """
        try:
            all_modules = []
            
            # Try HIGH CAN first
            print(ui.header("CAN BUS SNIFFER - HIGH CAN MODE"))
            self.prompt_switch_can_mode("HIGH")
            
            print(f"Capturing HIGH CAN traffic for {duration} seconds...")
            frames_high = self.can_explorer.start_monitoring(duration=duration)
            
            if frames_high:
                modules_high = self.can_explorer.discover_modules()
                print(ui.success(f"Found {len(modules_high)} modules on HIGH CAN", indent=2))
                all_modules.extend(modules_high)
            else:
                print(ui.warning("No traffic captured on HIGH CAN"))
            
            # Try LOW CAN
            choice = input("\nCapture LOW CAN mode? (y/n): ").strip().lower()
            
            if choice == 'y':
                print(ui.header("CAN BUS SNIFFER - LOW CAN MODE"))
                self.prompt_switch_can_mode("LOW")
                
                print(f"Capturing LOW CAN traffic for {duration} seconds...")
                frames_low = self.can_explorer.start_monitoring(duration=duration)
                
                if frames_low:
                    modules_low = self.can_explorer.discover_modules()
                    print(ui.success(f"Found {len(modules_low)} modules on LOW CAN", indent=2))
                    all_modules.extend(modules_low)
                else:
                    print(ui.warning("No traffic captured on LOW CAN"))
            
            # Display combined results
            print(ui.header("COMBINED MODULE DISCOVERY"))
            
            # Remove duplicates
            unique_modules = {}
            for module in all_modules:
                if module['id'] not in unique_modules:
                    unique_modules[module['id']] = module
            
            print(ui.success(f"Total Unique Modules Found: {len(unique_modules)}", indent=2))
            print()
            for module_id, module in sorted(unique_modules.items()):
                print(ui.info(f"{module_id}: {module['name']}", indent=4))
            
            return True
            
        except Exception as e:
            print(ui.failure(f"Error during dual-mode CAN exploration: {e}"))
            return False
    
    def print_summary(self):
        """Print diagnostic summary"""
        print(ui.header("DIAGNOSTIC SUMMARY"))
        
        if self.vehicle_info['vin']:
            print(ui.info(f"VIN: {self.vehicle_info['vin']}", indent=2))
        
        active_codes = len(self.vehicle_info['dtc_codes'])
        pending_codes = len(self.vehicle_info['pending_codes'])
        
        print(ui.info(f"Active Codes: {active_codes}", indent=2))
        print(ui.info(f"Pending Codes: {pending_codes}", indent=2))
        
        if active_codes + pending_codes == 0:
            print(ui.success("Status: NO ERRORS FOUND", indent=2))
        else:
            print(ui.warning(f"Status: ERRORS DETECTED ({active_codes + pending_codes} total)", indent=2))
    
    def disconnect(self):
        """Disconnect from adapter"""
        self.adapter.disconnect()
        print("\nDiagnostic session complete\n")
    
    def prompt_switch_can_mode(self, mode: str):
        """
        Prompt user to flip CAN switch to specified mode
        
        Args:
            mode: "HIGH" or "LOW"
        """
        print(ui.header(f"ACTION REQUIRED: Flip CAN switch to {mode} mode", width=50))
        can_speed = "500 kbps" if mode == "HIGH" else "125 kbps"
        print(ui.info(f"Current setting: {mode} CAN ({can_speed})", indent=2))
        input("\nPress ENTER after flipping the switch and connecting adapter...")
        print("Continuing...\n")
    
    def run_full_diagnostic_both_modes(self) -> bool:
        """
        Run full diagnostic on both HIGH and LOW CAN modes
        
        Returns:
            True if diagnostic completed
        """
        try:
            results = {'high_can': None, 'low_can': None}
            
            # Try HIGH CAN first
            print(ui.header("STARTING HVAC DIAGNOSTICS - HIGH CAN MODE"))
            self.prompt_switch_can_mode("HIGH")
            
            if self.run_full_diagnostic(use_high_can=True):
                results['high_can'] = self.vehicle_info.copy()
                print(ui.success("HIGH CAN diagnostic complete", indent=2))
            else:
                print(ui.failure("HIGH CAN diagnostic failed", indent=2))
            
            # Ask if user wants to try LOW CAN
            choice = input("\nTry LOW CAN mode? (y/n): ").strip().lower()
            
            if choice == 'y':
                print(ui.header("STARTING HVAC DIAGNOSTICS - LOW CAN MODE"))
                self.prompt_switch_can_mode("LOW")
                
                if self.run_full_diagnostic(use_high_can=False):
                    results['low_can'] = self.vehicle_info.copy()
                    print(ui.success("LOW CAN diagnostic complete", indent=2))
                else:
                    print(ui.failure("LOW CAN diagnostic failed", indent=2))
            
            # Display combined summary
            print(ui.header("DIAGNOSTIC SUMMARY - BOTH MODES"))
            
            if results['high_can']:
                print(ui.info("HIGH CAN Results:", indent=2))
                print(ui.info(f"VIN: {results['high_can'].get('vin', 'Not found')}", indent=4))
                print(ui.info(f"Active Codes: {len(results['high_can'].get('dtc_codes', []))}", indent=4))
                print(ui.info(f"Pending Codes: {len(results['high_can'].get('pending_codes', []))}", indent=4))
            
            if results['low_can']:
                print(ui.info("LOW CAN Results:", indent=2))
                print(ui.info(f"VIN: {results['low_can'].get('vin', 'Not found')}", indent=4))
                print(ui.info(f"Active Codes: {len(results['low_can'].get('dtc_codes', []))}", indent=4))
                print(ui.info(f"Pending Codes: {len(results['low_can'].get('pending_codes', []))}", indent=4))
            
            return True
            
        except Exception as e:
            print(ui.failure(f"Error during dual-mode diagnostic: {e}"))
            return False


def main():
    """Main entry point"""
    
    # Configuration for 2008 Ford Escape
    PORT = "COM3"  # Change to appropriate port
    USE_HIGH_CAN = True  # Ford Escape typically uses High CAN
    
    tool = DiagnosticTool(PORT)
    
    try:
        # Connect to adapter
        if not tool.connect():
            print(ui.failure("Failed to connect to ELM327 adapter"))
            print("\nCheck the following:")
            print(ui.info(f"  1. COM port is correct (current: {PORT})", indent=3))
            print(ui.info("  2. ELM327 adapter is powered on", indent=3))
            print(ui.info("  3. Adapter is connected to vehicle OBD-II port", indent=3))
            return 1
        
        # Main menu loop
        while True:
            menu_items = [
                "1. Check ELM327 Adapter Settings",
                "2. Test Vehicle Connection",
                "3. Detect Vehicle (check voltage and VIN)",
                "4. Full HVAC Diagnostics (VIN, DTC codes, module info)",
                "",
                "PASSIVE CAN BUS MONITORING:",
                "  5. CAN Bus Explorer - Discover all modules (basic sniffer)",
                "  6. Both HVAC diagnostics and CAN explorer",
                "  7. CAN Bus Explorer - Test Both CAN Modes",
                "",
                "PROACTIVE EVENT CAPTURE:",
                "  8. Event Capture - Map actions to CAN messages",
                "",
                "ACTUATIONS:",
                "  11. Send Custom OBD/UDS Command (Actuate)",
                "  12. Preset Actuations (safe presets, e.g. HVAC, ABS bleed template)",
                "",
                "HVAC DIAGNOSTICS:",
                "  9. HVAC Diagnostics - Test Both CAN Modes",
                "",
                "DEBUGGING & LOGS:",
                "  10. View OBD-II Traffic Log (for debugging)",
                "  11. Send Custom OBD/UDS Command (Actuate)",
                "  12. Preset Actuations (safe presets, e.g. HVAC, ABS bleed template)",
                "",
                "0. Exit",
            ]
            
            print(ui.menu(menu_items, "ELM327 OBD-II DIAGNOSTIC TOOL"))
            choice = input("Select option (0-12): ").strip()
            
            if choice == "0":
                print("\nExiting diagnostic tool...")
                return 0
            
            elif choice == "1":
                # Check adapter settings
                tool.adapter.display_settings()
            
            elif choice == "2":
                # Test vehicle connection
                print("\nTesting connection to vehicle...")
                if tool.adapter.test_vehicle_connection():
                    print(ui.success("Vehicle connection test PASSED"))
                else:
                    print(ui.failure("Vehicle connection test FAILED"))
                    print(ui.info("Check the following:", indent=2))
                    print(ui.info("- ELM327 is connected to OBD-II port", indent=4))
                    print(ui.info("- Vehicle is in RUN position", indent=4))
                    print(ui.info("- Try changing CAN bus mode (High/Low)", indent=4))
            
            elif choice == "3":
                # Detect vehicle - check voltage and communication
                tool.verify_vehicle()
            
            elif choice == "4":
                # Run full HVAC diagnostics
                if tool.run_full_diagnostic(use_high_can=USE_HIGH_CAN):
                    tool.print_summary()
                else:
                    print(ui.failure("Diagnostic failed"))
            
            elif choice == "5":
                # Basic CAN bus explorer - passive sniffer
                if tool.run_can_bus_exploration(duration=30):
                    print(ui.success("CAN bus exploration complete"))
                else:
                    print(ui.failure("CAN bus exploration failed"))
            
            elif choice == "6":
                # HVAC diagnostics + CAN bus explorer
                if tool.run_full_diagnostic(use_high_can=USE_HIGH_CAN):
                    tool.print_summary()
                    
                    if tool.run_can_bus_exploration(duration=30):
                        print(ui.success("All diagnostics complete"))
                else:
                    print(ui.failure("Diagnostic failed"))
            
            elif choice == "7":
                # CAN bus explorer on both CAN modes
                if tool.run_can_bus_exploration_both_modes(duration=20):
                    print(ui.success("CAN bus explorer (both modes) complete"))
                else:
                    print(ui.failure("CAN bus explorer failed"))
            
            elif choice == "8":
                # Proactive event capture
                if tool.can_explorer.start_event_capture():
                    print(ui.success("Event capture session complete"))
                else:
                    print(ui.warning("No events were captured"))
            
            elif choice == "9":
                # HVAC diagnostics on both CAN modes
                if tool.run_full_diagnostic_both_modes():
                    print(ui.success("HVAC diagnostics (both modes) complete"))
                else:
                    print(ui.failure("HVAC diagnostics failed"))
            
            elif choice == "10":
                # View OBD-II traffic log
                log_file = tool.adapter.get_traffic_log_file()
                print(ui.header("OBD-II TRAFFIC LOG"))
                print()
                print(ui.info(f"Traffic Log File: {log_file}", indent=2))
                print()
                
                # Display last 50 lines of log
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        
                    if not lines:
                        print(ui.info("No traffic data yet", indent=2))
                    else:
                        # Show last 50 lines
                        display_lines = lines[-50:] if len(lines) > 50 else lines
                        print(ui.info(f"Showing last {len(display_lines)} lines:", indent=2))
                        print()
                        for line in display_lines:
                            print(f"  {line.rstrip()}")
                        
                        print()
                        print(ui.success(f"Total log lines: {len(lines)}", indent=2))
                        print(ui.info(f"Use this log file for debugging and creating test cases", indent=2))
                
                except FileNotFoundError:
                    print(ui.failure(f"Log file not found: {log_file}", indent=2))
                except Exception as e:
                    print(ui.failure(f"Error reading log file: {e}", indent=2))
            
            elif choice == "11":
                # Send custom OBD/UDS command to actuate modules (dangerous)
                print(ui.header("CUSTOM COMMAND (ACTUATE) - WARNING"))
                print(ui.warning("This will send raw OBD/UDS commands to vehicle modules. Incorrect commands may actuate systems or cause unsafe states."))
                print(ui.info("Only proceed if you understand the command and have safety precautions in place (parking brake, transmission in park, area clear)."))
                cmd = input("\nEnter OBD/UDS command (hex bytes or standard PID, e.g. '2E0100' or '03' or '0902'): ").strip()
                if not cmd:
                    print(ui.failure("No command entered"))
                else:
                    confirm = input("Confirm send command? Type 'yes' to proceed: ").strip().lower()
                    if confirm != 'yes':
                        print(ui.info("Command cancelled"))
                    else:
                        try:
                            # Send the command raw (user responsible for format)
                            resp = tool.adapter.send_obd_command(cmd.replace(' ', ''))
                            if resp:
                                print(ui.success("Command sent - response received:"))
                                print(resp)
                            else:
                                print(ui.warning("No response or command failed - check log and vehicle state"))
                        except Exception as e:
                            print(ui.failure(f"Error sending command: {e}"))

            elif choice == "12":
                # Preset actuation commands (safe templates)
                print(ui.header("PRESET ACTUATIONS - TEMPLATES"))
                presets = [
                    ("1", "HVAC: Toggle recirculation (safe)"),
                    ("2", "HVAC: Fan speed step (safe)"),
                    ("3", "ABS: Bleed template (DANGEROUS - read details)")
                ]
                for k, desc in presets:
                    print(f"  {k}. {desc}")

                sel = input("Select preset (or 'c' to cancel): ").strip()
                if sel.lower() == 'c' or not sel:
                    print(ui.info("Cancelled"))
                elif sel == '1':
                    # Example safe HVAC recirc toggle (user must confirm)
                    print(ui.info("HVAC Recirculation - toggle (safe preset)."))
                    confirm = input("Type 'yes' to send HVAC recirc toggle: ").strip().lower()
                    if confirm == 'yes':
                        # Placeholder command - user should replace with verified PID/UDS
                        cmd = input("Enter HVAC recirc command (hex) to send (or leave empty to cancel): ").strip()
                        if cmd:
                            resp = tool.adapter.send_obd_command(cmd)
                            print(ui.info(f"Response: {resp}"))
                        else:
                            print(ui.info("No command provided - cancelled"))
                    else:
                        print(ui.info("Cancelled - confirmation not provided"))

                elif sel == '2':
                    print(ui.info("HVAC Fan Step - safe preset."))
                    confirm = input("Type 'yes' to send HVAC fan step command: ").strip().lower()
                    if confirm == 'yes':
                        cmd = input("Enter HVAC fan step command (hex) to send (or leave empty to cancel): ").strip()
                        if cmd:
                            resp = tool.adapter.send_obd_command(cmd)
                            print(ui.info(f"Response: {resp}"))
                        else:
                            print(ui.info("No command provided - cancelled"))
                    else:
                        print(ui.info("Cancelled - confirmation not provided"))

                elif sel == '3':
                    # ABS bleed template - extremely cautious flow
                    print(ui.header("ABS BLEED - TEMPLATE"))
                    print(ui.warning("ABS bleeding is vehicle- and manufacturer-specific and can be hazardous."))
                    print(ui.info("This template will only show the command sequence unless you explicitly choose to execute."))
                    # Example template sequence (placeholders) - DO NOT RUN unless you know exact commands
                    abs_sequence = [
                        "-- Enter ABS bleed mode: 0x31 0x01 <subparams> (vendor-specific)",
                        "-- Pump activation command: 0x2E 0xF1 0x90 <params> (vendor-specific)",
                        "-- Exit ABS bleed mode: 0x31 0x02 <subparams> (vendor-specific)"
                    ]
                    print(ui.info("ABS bleed template (example placeholders):", indent=2))
                    for line in abs_sequence:
                        print(ui.info(line, indent=4))

                    action = input("\nType 'dry' to only show commands, 'exec' to execute sequence, or 'c' to cancel: ").strip().lower()
                    if action == 'c' or not action:
                        print(ui.info("Cancelled"))
                    elif action == 'dry':
                        print(ui.success("Dry-run: no commands were sent."))
                    elif action == 'exec':
                        print(ui.warning("You chose to EXECUTE the ABS bleed template."))
                        confirm = input("Type EXACTLY 'EXECUTE ABS BLEED' to proceed: ").strip()
                        if confirm != 'EXECUTE ABS BLEED':
                            print(ui.failure("Confirmation mismatch - aborted."))
                        else:
                            print(ui.warning("Sending commands - be prepared to stop vehicle immediately if unsafe."))
                            # In this implementation we treat the sequence as placeholder; ask user for actual commands
                            for idx, placeholder in enumerate(abs_sequence, 1):
                                cmd = input(f"Enter command #{idx} (hex) for: '{placeholder}' (or leave empty to skip): ").strip()
                                if cmd:
                                    try:
                                        resp = tool.adapter.send_obd_command(cmd)
                                        print(ui.info(f"Response: {resp}"))
                                    except Exception as e:
                                        print(ui.failure(f"Error sending command: {e}"))
                                else:
                                    print(ui.info("Skipped"))
                            print(ui.success("ABS bleed sequence complete (commands sent as provided)."))
                    else:
                        print(ui.failure("Unknown action - cancelled"))
                else:
                    print(ui.failure("Invalid preset selection"))
            
            else:
                print(ui.failure("Invalid option - please select 0-12"))
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    
    except Exception as e:
        print(ui.failure(f"Unexpected error: {e}"))
        return 1
    
    finally:
        tool.disconnect()


if __name__ == "__main__":
    sys.exit(main())
