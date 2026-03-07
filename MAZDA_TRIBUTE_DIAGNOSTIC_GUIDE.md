# Mazda Tribute Diagnostic Guide

## Platform Sharing with Ford Escape

The **Mazda Tribute** (especially 2008-2011 models) is badge-engineered from the Ford Escape and shares:

- ✓ Identical platform and architecture
- ✓ Same CAN bus communication protocols
- ✓ Same module addresses
- ✓ Same diagnostic protocols (UDS/OBD-II)
- ✓ Same DIDs and service support

**All Ford Escape diagnostic procedures, scripts, and knowledge base entries apply to Mazda Tribute.**

## Communication Protocols

### 2008+ Mazda Tribute
- **Primary**: ISO 15765-4 CAN (11-bit, 500 kbaud for powertrain)
- **Architecture**: Same as Ford Escape
  - HS-CAN: Powertrain modules (500 kbaud)
  - MS-CAN: Body/comfort modules (125 kbaud)

### Pre-2008 Models
May also use:
- SAE J1850 PWM
- ISO 9141-2

Check specific model year for protocol support.

### CAN Bus Message Reference

For detailed CAN bus message structures, see:
- **Ford Escape / Mazda Tribute CAN Reference**: `reference/Mazda_CAN_Bus_Reference.md`

This reference contains reverse-engineered CAN message IDs, byte layouts, and scaling factors for the Ford Escape 2008 / Mazda Tribute 2008 platform:
- RPM, vehicle speed, wheel speeds
- Steering angle, accelerator pedal, brake status
- Transmission gear, odometer
- Turn signals, lighting, HVAC status
- Trip computer data (fuel consumption, range)
- Head unit display messages

**Two Diagnostic Methods:**

1. **UDS Diagnostics (via OBD-II port)**:
   - Module addresses: 0x7E0 (PCM), 0x760 (ABS), 0x7A0 (HVAC)
   - Service 0x22 (Read Data by Identifier) for DIDs
   - Primary method for diagnostics and troubleshooting
   - See `knowledge_base/Ford_Escape_2008_profile.yaml`

2. **CAN Bus Monitoring (passive)**:
   - Broadcast messages: 0x00000201 (RPM/speed), 0x000004B0 (wheel speeds), etc.
   - Useful for data logging and custom dashboards
   - See `reference/Mazda_CAN_Bus_Reference.md`

Both systems coexist on the same vehicle and provide complementary data access methods.

## Module Addresses (2008+ Tribute)

**Identical to Ford Escape 2008:**

| Module | Request | Response | Notes |
|--------|---------|----------|-------|
| PCM (Powertrain) | 0x7E0 | 0x7E8 | Fully accessible via OBD-II |
| TCM (Transmission) | 0x7E0 | 0x7E8 | Integrated with PCM |
| ABS Module | 0x760 | 0x768 | Limited UDS support |
| HVAC Module | 0x7A0 | 0x7A8 | Requires FORScan |
| BCM (Body Control) | 0x726 | 0x72E | Requires FORScan |
| IPC (Instrument Cluster) | 0x733 | 0x73B | Requires FORScan |

## Using Ford Escape Scripts with Mazda Tribute

All scripts in this repository work with Mazda Tribute:

### ABS Module Diagnostics
```bash
# Test ABS communication
python scripts/debug/test_ford_abs_connection.py

# Scan for all ABS DIDs
python scripts/debug/scan_ford_abs_dids.py

# Test wheel speed sensors
python scripts/debug/test_wheel_speed_dids.py

# Extended DID scan
python scripts/debug/scan_ford_abs_extended.py
```

### Transmission Diagnostics
```bash
# Read transmission data
python toolkit/diagnostic_procedures/read_transmission_data.py

# Monitor transmission live
python toolkit/diagnostic_procedures/monitor_transmission_live.py

# Scan transmission DIDs
python toolkit/diagnostic_procedures/scan_transmission_dids.py
```

### Module Discovery
```bash
# Scan all Ford modules
python toolkit/diagnostic_procedures/scan_ford_modules.py

# Discover vehicle capabilities
python toolkit/diagnostic_procedures/discover_vehicle_capabilities.py
```

## Knowledge Base

Reference the Ford Escape 2008 knowledge base for Mazda Tribute:

- **Vehicle Profile**: `knowledge_base/Ford_Escape_2008_profile.yaml`
- **OBD-II PIDs**: `knowledge_base/Ford_Escape_OBDII_PIDs.yaml`
- **UDS Commands**: `knowledge_base/Ford_Escape_UDS_Commands.yaml`
- **Technical Data**: `knowledge_base/Ford_Escape_2008_technical.dat`

All information applies to Mazda Tribute.

## Confirmed Findings (Apply to Tribute)

### ABS Module (2026-03-05)
- **Address**: 0x760/0x768
- **Tester Present**: `3E 01` works, returns `7E`
- **Working DIDs**: 0x0200, 0x0202
- **Standard UDS DIDs**: NOT supported (normal for Ford/Mazda ABS)
- **DTC Reading**: Requires FORScan

### Transmission (PCM)
- **Address**: 0x7E0/0x7E8
- **Working DIDs**: 0x0100 (fluid temp), 0x0101 (line pressure)
- **Standard OBD-II**: Fully supported

### HVAC Module
- **Address**: 0x7A0/0x7A8
- **Standard OBD-II**: NOT supported
- **Requires**: FORScan or Ford IDS

## Common Issues (Same as Ford Escape)

### HVAC Blend Door Actuator
- **DTCs**: P1632, P1635
- **Symptoms**: Clicking noise, no temperature control
- **Location**: Behind glove box
- **Repair**: Same procedure as Ford Escape

### ABS Wheel Speed Sensors
- **DTCs**: C1234 (example)
- **Symptoms**: ABS light on, traction control disabled
- **Location**: At each wheel hub
- **Repair**: Same procedure as Ford Escape

### Transmission Issues
- **Common**: Shift solenoid failures, fluid temperature sensor
- **Diagnostics**: Same DIDs and procedures as Ford Escape

## FORScan Compatibility

FORScan works with Mazda Tribute:
- Use "Ford Escape" profile in FORScan
- All modules accessible
- Same extended PIDs
- Same actuator tests

## Creating Mazda Tribute Profile

If you want a dedicated Mazda Tribute profile:

1. Copy Ford Escape profile:
```bash
cp knowledge_base/Ford_Escape_2008_profile.yaml knowledge_base/Mazda_Tribute_2008_profile.yaml
```

2. Update vehicle information:
```yaml
vehicle:
  make: Mazda
  model: Tribute
  year: 2008
  notes: "Badge-engineered from Ford Escape. All Ford Escape procedures apply."
  platform_shared_with: "Ford Escape 2008"
```

3. Reference Ford Escape for all technical details

## Steering File Activation

The Ford-specific steering file (`.kiro/steering/ford-specific-guidance.md`) is automatically activated when working with Mazda Tribute files due to the pattern match: `*Mazda*Tribute*`

This provides:
- Ford/Mazda diagnostic protocols
- Module discovery procedures
- Platform sharing information
- Common issues and solutions

## Summary

**For Mazda Tribute diagnostics:**
1. Use all Ford Escape scripts and procedures
2. Reference Ford Escape knowledge base
3. Module addresses are identical
4. DIDs and services are identical
5. All findings documented for Ford Escape apply to Mazda Tribute

The only difference is the badge on the vehicle.
