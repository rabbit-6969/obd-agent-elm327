"""
Capture FORScan commands for PCM Transmission Functions

This script monitors COM port traffic while you interact with FORScan
to capture the exact UDS commands used for:
- Reading transmission DTCs
- Reading transmission parameters (temp, pressure, gear, etc.)
- Actuating shift solenoids
- Running transmission self-tests

NOTE: 2008 Ford Escape uses PCM (Powertrain Control Module) for both
engine and transmission control. There is no separate TCM.

Usage:
1. Start this script: python capture_forscan_transmission.py
2. In FORScan, connect to PCM module
3. Navigate to transmission-related functions:
   - Read DTCs (look for transmission codes P07xx, P17xx)
   - Read live data (fluid temp, line pressure, gear position)
   - Actuate shift solenoids (if available in Active Tests)
   - Run self-tests
4. Script will log all traffic to file
5. Press Ctrl+C when done

Output: logs/forscan_pcm_transmission_[timestamp].log
"""

import serial
import time
import sys
from datetime import datetime
import os

# Configuration
COM_PORT = "COM3"  # Change if your ELM327 is on different port
BAUDRATE = 38400
LOG_DIR = "logs"

def setup_logging():
    """Create logs directory and log file"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"forscan_pcm_transmission_{timestamp}.log")
    return open(log_file, 'w', encoding='utf-8')

def parse_uds_command(data):
    """Parse and annotate UDS commands"""
    if not data:
        return None
    
    # Remove spaces and convert to uppercase
    clean = data.replace(' ', '').upper()
    
    if len(clean) < 2:
        return None
    
    service = clean[0:2]
    
    annotations = {
        '10': 'DiagnosticSessionControl',
        '11': 'ECUReset',
        '14': 'ClearDiagnosticInformation',
        '19': 'ReadDTCInformation',
        '22': 'ReadDataByIdentifier',
        '27': 'SecurityAccess',
        '2E': 'WriteDataByIdentifier',
        '2F': 'InputOutputControlByIdentifier',
        '31': 'RoutineControl',
        '3E': 'TesterPresent',
        '50': 'Response: DiagnosticSessionControl',
        '51': 'Response: ECUReset',
        '54': 'Response: ClearDiagnosticInformation',
        '59': 'Response: ReadDTCInformation',
        '62': 'Response: ReadDataByIdentifier',
        '67': 'Response: SecurityAccess',
        '6E': 'Response: WriteDataByIdentifier',
        '6F': 'Response: InputOutputControlByIdentifier',
        '71': 'Response: RoutineControl',
        '7E': 'Response: TesterPresent',
        '7F': 'NegativeResponse'
    }
    
    annotation = annotations.get(service, 'Unknown')
    
    # Additional parsing for specific services
    if service == '19' and len(clean) >= 4:
        subfunction = clean[2:4]
        subfunctions = {
            '01': 'reportNumberOfDTCByStatusMask',
            '02': 'reportDTCByStatusMask',
            '03': 'reportDTCSnapshotIdentification',
            '04': 'reportDTCSnapshotRecordByDTCNumber',
            '06': 'reportDTCExtendedDataRecordByDTCNumber',
            '0A': 'reportSupportedDTC'
        }
        annotation += f" - {subfunctions.get(subfunction, 'unknown subfunction')}"
    
    elif service == '22' and len(clean) >= 6:
        did = clean[2:6]
        annotation += f" - DID: 0x{did}"
        
        # Common transmission DIDs
        common_dids = {
            '0100': 'Transmission Fluid Temperature',
            '0101': 'Line Pressure',
            '0102': 'Current Gear',
            '0103': 'Shift Solenoid A Status',
            '0104': 'Shift Solenoid B Status',
            '0105': 'Shift Solenoid C Status',
            '0106': 'Shift Solenoid D Status',
            '0107': 'Torque Converter Clutch Status',
            '0108': 'Input Shaft Speed',
            '0109': 'Output Shaft Speed',
            '010A': 'Turbine Speed'
        }
        if did in common_dids:
            annotation += f" ({common_dids[did]})"
    
    elif service == '2F' and len(clean) >= 8:
        did = clean[2:6]
        control = clean[6:8]
        annotation += f" - DID: 0x{did}, Control: 0x{control}"
        
        control_types = {
            '00': 'returnControlToECU',
            '01': 'resetToDefault',
            '02': 'freezeCurrentState',
            '03': 'shortTermAdjustment'
        }
        annotation += f" ({control_types.get(control, 'unknown')})"
    
    elif service == '31' and len(clean) >= 8:
        subfunction = clean[2:4]
        routine_id = clean[4:8]
        annotation += f" - Routine: 0x{routine_id}"
        
        subfunctions = {
            '01': 'startRoutine',
            '02': 'stopRoutine',
            '03': 'requestRoutineResults'
        }
        annotation += f" ({subfunctions.get(subfunction, 'unknown')})"
        
        # Common transmission routines
        common_routines = {
            '0001': 'Shift Solenoid Test',
            '0002': 'Line Pressure Test',
            '0003': 'TCC Test',
            '0004': 'Transmission Self-Test'
        }
        if routine_id in common_routines:
            annotation += f" - {common_routines[routine_id]}"
    
    elif service == '7F':
        if len(clean) >= 6:
            failed_service = clean[2:4]
            nrc = clean[4:6]
            
            nrc_meanings = {
                '11': 'serviceNotSupported',
                '12': 'subFunctionNotSupported',
                '13': 'incorrectMessageLengthOrInvalidFormat',
                '22': 'conditionsNotCorrect',
                '24': 'requestSequenceError',
                '31': 'requestOutOfRange',
                '33': 'securityAccessDenied',
                '35': 'invalidKey',
                '36': 'exceedNumberOfAttempts',
                '37': 'requiredTimeDelayNotExpired',
                '78': 'requestCorrectlyReceived-ResponsePending'
            }
            
            annotation += f" - Service: 0x{failed_service}, NRC: 0x{nrc} ({nrc_meanings.get(nrc, 'unknown')})"
    
    return annotation

def monitor_port(log_file):
    """Monitor COM port and log all traffic"""
    print(f"Opening {COM_PORT} at {BAUDRATE} baud...")
    print("Waiting for FORScan traffic...")
    print("\nActions to perform in FORScan:")
    print("1. Connect to PCM (Powertrain Control Module)")
    print("2. Read DTCs (look for transmission codes: P07xx, P17xx)")
    print("3. Navigate to transmission section in live data:")
    print("   - Transmission fluid temperature")
    print("   - Line pressure")
    print("   - Current gear position")
    print("   - Shift solenoid states (SSA, SSB, SSC, SSD)")
    print("   - Torque converter clutch")
    print("4. Try Active Tests / Actuations:")
    print("   - Shift solenoid tests")
    print("   - TCC (Torque Converter Clutch) test")
    print("5. Run any transmission self-tests or routines")
    print("\nPress Ctrl+C when done\n")
    
    try:
        ser = serial.Serial(
            port=COM_PORT,
            baudrate=BAUDRATE,
            timeout=0.1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )
        
        buffer = ""
        last_activity = time.time()
        
        while True:
            if ser.in_waiting > 0:
                byte_data = ser.read(ser.in_waiting)
                try:
                    text = byte_data.decode('utf-8', errors='ignore')
                    buffer += text
                    
                    # Process complete lines
                    while '\r' in buffer or '\n' in buffer:
                        if '\r' in buffer:
                            line, buffer = buffer.split('\r', 1)
                        else:
                            line, buffer = buffer.split('\n', 1)
                        
                        line = line.strip()
                        if line and line != '>':
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            
                            # Parse UDS command
                            annotation = parse_uds_command(line)
                            
                            # Log to file
                            if annotation:
                                log_entry = f"[{timestamp}] {line:40s} # {annotation}\n"
                                print(f"[{timestamp}] {line:40s} # {annotation}")
                            else:
                                log_entry = f"[{timestamp}] {line}\n"
                                print(f"[{timestamp}] {line}")
                            
                            log_file.write(log_entry)
                            log_file.flush()
                            
                            last_activity = time.time()
                
                except Exception as e:
                    print(f"Error decoding: {e}")
            
            # Show activity indicator
            if time.time() - last_activity > 5:
                sys.stdout.write('.')
                sys.stdout.flush()
                last_activity = time.time()
            
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nCapture stopped by user")
    except serial.SerialException as e:
        print(f"\nError: {e}")
        print(f"Make sure {COM_PORT} is correct and not in use by FORScan")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

def main():
    """Main entry point"""
    print("=" * 70)
    print("FORScan PCM Transmission Command Capture")
    print("=" * 70)
    print()
    print("NOTE: 2008 Ford Escape uses PCM for transmission control")
    print("      (No separate TCM module)")
    print()
    
    log_file = setup_logging()
    print(f"Logging to: {log_file.name}\n")
    
    # Write header to log file
    log_file.write("=" * 70 + "\n")
    log_file.write("FORScan Transmission Command Capture\n")
    log_file.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_file.write(f"Port: {COM_PORT} @ {BAUDRATE} baud\n")
    log_file.write("=" * 70 + "\n\n")
    log_file.flush()
    
    try:
        monitor_port(log_file)
    finally:
        log_file.write("\n" + "=" * 70 + "\n")
        log_file.write(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("=" * 70 + "\n")
        log_file.close()
        print(f"\nLog saved to: {log_file.name}")

if __name__ == '__main__':
    main()
