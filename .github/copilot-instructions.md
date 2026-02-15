# ELM327 OBD-II Diagnostic Tool - Development Guide

## Project Overview
Python application for reading vehicle diagnostics from a 2008 Ford Escape using an ELM327 OBD-II adapter. Supports both High and Low CAN bus modes for complete diagnostics.

## Project Status
✅ Project created and configured

## Setup Checklist

- [x] Verify copilot-instructions.md file created
- [x] Scaffold the Project
- [x] Customize the Project
- [x] Install Required Extensions
- [x] Compile the Project
- [x] Documentation Complete

## Architecture

### Core Modules

1. **elm327_adapter.py** - ELM327 Communication Layer
   - Serial port initialization and configuration
   - AT command interface for adapter control
   - CAN bus mode switching (High/Low)
   - Response parsing and error handling

2. **vin_reader.py** - Vehicle Identification
   - OBD-II Service 09 (Vehicle Info) implementation
   - VIN extraction from multi-frame responses
   - VIN format validation
   - Automatic CAN bus mode fallback

3. **hvac_diagnostics.py** - HVAC System Diagnostics
   - DTC code reading (modes 19, 07)
   - OBD-II response parsing
   - Ford HVAC code database
   - Pending code detection
   - Code clearing functionality

4. **main.py** - Main Application
   - Diagnostic workflow orchestration
   - User interface and logging
   - Summary reporting
   - Error handling and recovery

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure serial port in `elm327_diagnostic/main.py`:
   ```python
   PORT = "COM3"  # Update to your port
   USE_HIGH_CAN = True
   ```

3. Connect ELM327 adapter to vehicle OBD-II port

4. Run diagnostic:
   ```bash
   python elm327_diagnostic/main.py
   ```

## Development Guidelines

### Adding New Diagnostic Modules
1. Create new class inheriting from appropriate reader/diagnostic pattern
2. Use `ELM327Adapter` for serial communication
3. Implement OBD-II command formatting and response parsing
4. Add comprehensive logging with logger statements

### Extending Ford Vehicle Support
- Modify `FORD_HVAC_CODES` dictionary in hvac_diagnostics.py
- Add vehicle-specific PID definitions
- Create new protocol handlers as needed

### Testing
- Always have serial port configured before testing
- Verify adapter initialization with AT commands
- Test both CAN bus modes for compatibility
- Validate response parsing with real vehicle data

## Dependencies

- **pyserial 3.5** - Serial port communication
- **Python 3.7+** - Core language runtime

## File Structure

```
obd/
├── elm327_diagnostic/
│   ├── __init__.py
│   ├── elm327_adapter.py
│   ├── vin_reader.py
│   ├── hvac_diagnostics.py
│   └── main.py
├── requirements.txt
├── README.md
└── .github/
    └── copilot-instructions.md
```

## Troubleshooting Guide

### Connection Issues
- Verify COM port with Device Manager
- Ensure adapter is powered and initialized
- Check vehicle is in RUN state (not OFF)

### No Data Response
- Confirm CAN bus mode (use auto-fallback feature)
- Verify vehicle supports CAN protocol
- Check adapter protocol selection (SP6 for CAN)

### VIN Reading Fails
- Try alternate CAN bus mode
- Allow 2-3 second timeout for multi-frame response
- Verify OBD-II response parsing logic

## Next Steps for Enhancement

1. Add Engine diagnostics module
2. Implement real-time sensor data streaming (Mode 01)
3. Create GUI interface with tkinter or PyQt
4. Add data logging to CSV/JSON
5. Support for multiple vehicle makes/models
6. Implement freeze frame data reading
7. Add I/M readiness status checking

## Performance Considerations

- Serial timeout set to 2.0 seconds (adjustable)
- 0.5 second delay between multi-frame requests
- Response parsing uses string matching for reliability
- No multi-threaded communication currently

## Security Notes

- Handle vehicle diagnostics responsibly
- Ensure authorization before accessing vehicle data
- Clear DTCs only when appropriate
- Document all diagnostic actions

## References

- OBD-II Protocol: ISO 14230-4
- Ford CAN Messaging: UDS (Unified Diagnostic Services)
- ELM327 Command Set: Official ELM Electronics documentation
