# AI Vehicle Diagnostic Agent

An intelligent, AI-powered vehicle diagnostic system that combines OBD-II/UDS communication with natural language processing, web research, and continuous learning capabilities.

## 🚀 Project Status

**Phase 1 (In Progress)**: Core infrastructure and Ford Escape 2008 HVAC diagnostics

### ✅ Completed Components

- **Project Setup**: Directory structure, configuration system
- **Knowledge Management**: Technical data parser, vehicle profile handler, Ford Escape 2008 knowledge base
- **Query Parser**: Natural language query parsing with ambiguity detection
- **Web Research**: AI-assisted search, user fallback mode, Ford cross-reference search
- **Vehicle Communication**: ELM327 base, read_dtc.py, clear_dtc.py toolkit scripts
- **Agent Core**: Main agent loop, toolkit executor, diagnostic workflow, closed-loop feedback system

### 🔄 In Progress

- Toolkit scripts: read_vin.py, can_explore.py
- Knowledge management scripts: append_procedure.py, query_knowledge.py
- AI backend integration (OpenAI, Claude, Ollama)
- Safety mechanisms and confirmation workflows

See [.kiro/specs/ai-vehicle-diagnostic-agent/tasks.md](.kiro/specs/ai-vehicle-diagnostic-agent/tasks.md) for detailed task tracking.

## ✨ Key Features

### Current Capabilities
- **Natural Language Interface**: Ask diagnostic questions in plain English
- **Multi-Vehicle Support**: Ford Escape 2008, Toyota FJ Cruiser 2008 (expandable)
- **ELM327 Communication**: Full OBD-II and UDS protocol support
- **Knowledge Base**: Structured vehicle-specific diagnostic data
- **Web Research**: AI-powered search for unknown procedures
- **Closed-Loop Learning**: Documents successful diagnostics for future reuse
- **Professional UI**: Color-coded status indicators and clean output

### Planned Features
- AI backend integration for intelligent query interpretation
- Safety confirmation workflows for dangerous operations
- Session logging and audit trails
- Diagnostic report generation
- Module discovery and registry
- Script generation for custom diagnostics

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

### Project Documentation
- 📋 [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current project status and progress
- 🎯 [NEXT_STEPS_AI_AGENT.md](NEXT_STEPS_AI_AGENT.md) - Roadmap and next steps
- 📊 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project organization

### Specification Documents
- 📖 [Requirements](.kiro/specs/ai-vehicle-diagnostic-agent/requirements.md) - Feature requirements
- 🏗️ [Design](.kiro/specs/ai-vehicle-diagnostic-agent/design.md) - System design
- ✅ [Tasks](.kiro/specs/ai-vehicle-diagnostic-agent/tasks.md) - Implementation tasks

### Knowledge Base
- 🚗 [Ford Escape 2008](knowledge_base/Ford_Escape_2008_profile.yaml) - Vehicle profile
- 🔧 [Ford UDS Services](knowledge_base/Ford_UDS_Services_Complete.yaml) - UDS command reference
- 📚 [Knowledge Base README](knowledge_base/README.md) - Knowledge organization

### UI Documentation
- 📖 [UI_PREVIEW.md](UI_PREVIEW.md) - Visual examples of the UI
- 📚 [UI_REFERENCE.md](UI_REFERENCE.md) - UI formatter API reference
- 📊 [BEFORE_AFTER.md](BEFORE_AFTER.md) - UI improvements comparison

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

## Architecture

### Agent Core (`agent_core/`)
- **agent.py** - Main agent loop and orchestration
- **query_parser.py** - Natural language query parsing
- **diagnostic_workflow.py** - Diagnostic workflow orchestration
- **toolkit_executor.py** - Toolkit script execution
- **feedback_system.py** - Closed-loop learning system

### Toolkit Scripts (`toolkit/`)
- **vehicle_communication/** - ELM327 communication, DTC reading/clearing
- **web_research/** - AI-assisted search, user fallback mode
- **knowledge_management/** - Technical data parser, profile handler

### Knowledge Base (`knowledge_base/`)
- Vehicle profiles (YAML)
- Technical data (compact format)
- UDS command definitions
- DTC descriptions and repair hints

### Legacy Diagnostic Tools (`elm327_diagnostic/`)
- **elm327_adapter.py** - Low-level adapter communication
- **vin_reader.py** - VIN extraction and validation
- **hvac_diagnostics.py** - HVAC system diagnostics
- **main.py** - Standalone diagnostic tool

## Extending the System

### Adding New Vehicles
1. Create vehicle profile YAML in `knowledge_base/`
2. Add technical data file with module addresses and commands
3. Document DTC codes and common issues

### Adding New Toolkit Scripts
1. Create script in appropriate `toolkit/` subdirectory
2. Follow JSON input/output convention
3. Register in toolkit registry
4. Add to agent's available tools

### Adding New Diagnostic Procedures
1. Document procedure in knowledge base
2. Test with vehicle
3. System learns and reuses automatically

## Limitations

- Read-only access (no module programming or flashing)
- Some vehicles may require authentication or special initialization
- Data interpretation depends on OBD-II specification compliance
- CAN bus mode auto-detection not available on all adapters

## License

Use at your own risk. Ensure you have proper authorization before accessing vehicle diagnostics.

## Contributing

This project follows a spec-driven development methodology. See the specification documents in `.kiro/specs/ai-vehicle-diagnostic-agent/` for detailed requirements, design, and implementation tasks.

## References

- [OBD-II Standard](https://en.wikipedia.org/wiki/On-board_diagnostics)
- [ISO 14229-1 UDS](reference/ISO_14229-1_UDS_INDEX.md) - Unified Diagnostic Services
- [ELM327 Command Reference](https://www.elmelectronics.com/)
- [Ford Vehicle Communications](https://owner.ford.com/)

## GitHub Issues

Track implementation progress on [GitHub Issues](https://github.com/rabbit-6969/obd-agent-elm327/issues)
