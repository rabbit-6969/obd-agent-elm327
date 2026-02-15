# ELM327 OBD-II Diagnostic Tool

A Python application for reading vehicle diagnostics from a 2008 Ford Escape using an ELM327 OBD-II adapter.

## ✨ New: Professional UI

The diagnostic tool now features a **clean, modern, and professional user interface** with:
- Color-coded status indicators (✓ Success, ✗ Failure, ⚠ Warning)
- Well-organized output with clear visual hierarchy
- No verbose logger prefixes - clean and readable
- Professional appearance suitable for any environment

See [UI_PREVIEW.md](UI_PREVIEW.md) for visual examples!

## Features

- **ELM327 Adapter Communication**: Serial communication with ELM327 OBD-II adapter
- **VIN Reading**: Extract Vehicle Identification Number from the vehicle
- **DTC Code Reading**: Read active and pending Diagnostic Trouble Codes (DTCs)
- **HVAC Diagnostics**: Get HVAC system status and error codes
- **CAN Bus Support**: Support for both High CAN (500k) and Low CAN (125k) bus modes
- **Error Handling**: Comprehensive logging and error reporting

## Hardware Requirements

- **ELM327 OBD-II Adapter**: With CAN bus support
- **Hi/Low CAN Switch**: For switching between CAN bus modes
- **Serial Connection**: USB to Serial or native serial port

## Software Requirements

- Python 3.7+
- `pyserial` library for serial communication

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Verify your ELM327 adapter is connected to your computer
3. Identify the COM port (Windows) or /dev/ttyUSB device (Linux/Mac)

## Configuration

Edit `elm327_diagnostic/main.py` and update:

```python
PORT = "COM3"  # Change to your adapter's COM port
USE_HIGH_CAN = True  # True for High CAN, False for Low CAN
```

### Finding Your COM Port

**Windows:**
- Device Manager → Ports (COM & LPT)
- Look for "USB Serial Port" or similar

**Linux:**
- `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`

**Mac:**
- `ls /dev/tty.usbserial*`

## Usage

Run the diagnostic tool:

```bash
python elm327_diagnostic/main.py
```

The tool will:
1. Connect to the ELM327 adapter
2. Set up the CAN bus mode
3. Read the vehicle VIN
4. Retrieve active DTC codes
5. Retrieve pending (intermittent) DTC codes
6. Display HVAC system status
7. Print a diagnostic summary

## Documentation

- 📖 [UI_PREVIEW.md](UI_PREVIEW.md) - Visual examples of the new UI
- 📚 [UI_REFERENCE.md](UI_REFERENCE.md) - Complete UI formatter API reference
- 📊 [BEFORE_AFTER.md](BEFORE_AFTER.md) - Side-by-side comparison of improvements
- ✨ [UI_IMPROVEMENTS.md](UI_IMPROVEMENTS.md) - Overview of UI enhancements
- 📝 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details
- ✅ [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) - Implementation checklist

## Example Output

```
===== ELM327 OBD-II Diagnostic Tool - Ford Escape 2008 =====

Attempting to connect to adapter on COM3...
✓ Connected to ELM327 adapter successfully

===== READING VEHICLE IDENTIFICATION NUMBER (VIN) =====

✓ VIN: 1FMYU04146KE12345
✓ VIN validation: PASSED

===== READING DIAGNOSTIC TROUBLE CODES (DTCs) =====
============================================================
✓ Found 2 active DTC code(s):
  1. P0456: Evaporation System - Leak Detection Pump Error
  2. P1473: Cooling Fan Relay Control

============================================================
DIAGNOSTIC SUMMARY
============================================================
VIN: 1FMYU04146KE12345
Active Codes: 2
Pending Codes: 0
Status: ⚠ ERRORS DETECTED
============================================================
```

## Troubleshooting

### "Failed to connect to adapter"
- Check COM port is correct
- Verify ELM327 adapter is powered on and connected
- Adapter should be connected to vehicle's OBD-II port (usually under dashboard)
- Check USB cable connection

### "NO DATA" or "UNABLE TO CONNECT"
- Vehicle must be running (or key in ON position)
- Try switching CAN bus mode (High vs Low)
- Check that ELM327 adapter is properly initialized
- Vehicle must support the requested protocol

### "No response for VIN"
- Try toggling CAN bus mode (the tool auto-tries both)
- Some vehicles may require specific initialization commands
- Ensure vehicle is powered on

## CAN Bus Modes

**High CAN (500kbps)** - Standard for modern Ford vehicles
- 2008 Ford Escape typically uses High CAN
- Primary diagnostic channel

**Low CAN (125kbps)** - Infotainment/comfort systems
- HVAC module may be on Low CAN
- Used as fallback if High CAN fails

## Ford Escape 2008 Specific Notes

- Vehicle uses CAN 2.0b protocol
- Standard OBD-II port under dashboard on driver side
- VIN can be retrieved via Service 09, PID 02
- HVAC errors typically appear as P14xx and P15xx codes
- Module communication may require brief delays between commands

## OBD-II Commands Used

| Command | Description |
|---------|-------------|
| AT Z | Reset adapter |
| AT E0 | Disable echo |
| AT L0 | Disable linefeeds |
| AT I | Get adapter info |
| AT SP6 | Select CAN protocol |
| 0902 | Read VIN |
| 19 | Read DTC codes |
| 07 | Read pending codes |
| 14 | Clear DTC codes |

## Common Ford HVAC DTC Codes

- **P0533** - A/C Refrigerant Charge Loss
- **P1456** - Evaporation System - Leak Detection Pump Error
- **P1457** - Evaporation System - Leak Detection Pump Disabled
- **P1460** - Cooling Fan Relay Control Circuit
- **P1473** - Cooling Fan Relay Control
- **P1474** - Cooling Fan Relay Control Circuit

## Module Architecture

- **elm327_adapter.py** - Low-level adapter communication and AT commands
- **vin_reader.py** - VIN extraction and validation
- **hvac_diagnostics.py** - HVAC system diagnostics and DTC parsing
- **main.py** - Main program flow and user interface

## Extending the Tool

To add more diagnostic capabilities:

1. Add new methods to `HVACDiagnostics` class
2. Create new reader modules for other systems (Engine, Transmission, etc.)
3. Implement custom OBD-II commands for vehicle-specific diagnostics

## Limitations

- Read-only access (no module programming or flashing)
- Some vehicles may require authentication or special initialization
- Data interpretation depends on OBD-II specification compliance
- CAN bus mode auto-detection not available on all adapters

## License

Use at your own risk. Ensure you have proper authorization before accessing vehicle diagnostics.

## References

- [OBD-II Standard](https://en.wikipedia.org/wiki/On-board_diagnostics)
- [ELM327 Command Reference](https://www.elmelectronics.com/)
- [Ford Vehicle Communications](https://owner.ford.com/)
