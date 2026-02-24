# Ford Escape 2008 - ABS Module Scanner Guide

## Overview

The ABS (Anti-lock Braking System) module is on HS-CAN, same as the PCM. You've already discovered 2 working DIDs (0x0200, 0x0202) - this scanner will find more.

## Quick Start

```bash
python scan_abs_module.py
```

**Switch Position:** HS-CAN (same as PCM scanning)

## What We Know

From FORScan discovery:
- Part Number: 8L84-2C219-CH
- Calibration: 8L84-2C219-CH
- Strategy: 8L84-2D053-CF
- Software: 2006-12-11
- Status: Accessible, no DTCs

From previous UDS scanning:
- DID 0x0200: Responds (unknown data)
- DID 0x0202: Responds (unknown data)

## Scan Modes

### 1. Quick Scan (1 minute)
Tests the 2 confirmed working DIDs:
- 0x0200: ABS Parameter 1
- 0x0202: ABS Parameter 2

**Use this** to verify ABS communication.

### 2. Focused Scan (10-15 minutes)
Scans typical ABS DID ranges:
- 0x0000-0x000F: Basic info
- 0x0080-0x008F: Calibration IDs
- 0x0200-0x020F: ABS status (known range)
- 0x0210-0x021F: Wheel speed sensors
- 0x0220-0x022F: Brake pressure
- 0x0230-0x023F: ABS control
- 0xF100-0xF1FF: Module identification

### 3. Full Scan (30-40 minutes)
Comprehensive scan:
- 0x0000-0x00FF: Basic info & calibration
- 0x0200-0x02FF: ABS system data
- 0x0300-0x03FF: Extended ABS data
- 0xF000-0xF0FF: Diagnostic data
- 0xF100-0xF1FF: Module identification

### 4. Custom Range
Specify your own start/end DIDs.

## Expected ABS Data

### Wheel Speed Sensors
- Individual wheel speeds (FL, FR, RL, RR)
- Typically in km/h or counts
- Used for ABS activation

### Brake Pressure
- Master cylinder pressure
- Individual wheel pressures
- Brake pedal position

### ABS Status
- System active/inactive
- Fault flags
- Valve states
- Pump status

### Module Info
- Part numbers
- Software versions
- Calibration IDs
- Manufacturing data

## ABS Addressing

- Request: 0x760
- Response: 0x768
- Bus: HS-CAN (500 kbps)
- Protocol: ISO 15765-4 CAN (11 bit)

## Typical ABS DID Ranges

Based on Ford ABS systems:

**0x0000-0x00FF: Basic Information**
- VIN
- Part numbers
- Calibration data

**0x0200-0x02FF: ABS System Data**
- Wheel speeds
- Brake pressures
- System status
- Sensor data

**0x0300-0x03FF: Extended Data**
- Advanced diagnostics
- Engineering data
- Test modes

**0xF000-0xF0FF: Diagnostic Counters**
- ABS activation counts
- Fault history
- System statistics

**0xF100-0xF1FF: Module Identification**
- Part numbers
- Software versions
- Hardware IDs
- Manufacturing dates

## Decoding ABS Data

### Wheel Speed Format
Typically 2 bytes per wheel:
```python
# Example: 0x0210 might be FL wheel speed
raw = int(data[0:4], 16)  # First 2 bytes
speed_kmh = raw * 0.0625  # Typical scaling
```

### Brake Pressure Format
Usually 2 bytes:
```python
raw = int(data[0:4], 16)
pressure_bar = raw * 0.1  # Typical scaling
```

### Status Flags
Often bit-encoded:
```python
status = int(data[0:2], 16)
abs_active = (status & 0x01) != 0
fault = (status & 0x02) != 0
```

## Comparison with PCM

| Feature | PCM | ABS |
|---------|-----|-----|
| Bus | HS-CAN | HS-CAN |
| Request | 0x7E0 | 0x760 |
| Response | 0x7E8 | 0x768 |
| Known DIDs | 4 | 2 |
| Data Type | Engine/Trans | Brakes/Wheels |

## Safety Notes

- Read-only operations (UDS 0x22)
- No brake system modifications
- No actuator tests
- Safe on running vehicle
- Will not affect braking

## Troubleshooting

### "NO_RESPONSE" for all DIDs
- Check switch is in HS-CAN position
- Verify vehicle is on (ignition)
- Try PCM first to verify connection
- ABS may need vehicle running

### Known DIDs work, others don't
- Normal - many DIDs may not be supported
- Focus on ranges that respond
- Some DIDs may be security-locked

### Different data each read
- Normal for dynamic data (wheel speeds)
- Wheels must be rotating to see speed
- Brake pedal affects pressure readings

## Use Cases

### 1. Wheel Speed Monitoring
Find wheel speed DIDs, monitor while driving:
```bash
# Find wheel speed DIDs
python scan_abs_module.py
# Select mode 2 (Focused)
# Look for DIDs in 0x0210-0x021F range
```

### 2. Brake System Diagnostics
Check brake pressure sensors:
```bash
# Scan brake pressure range
python scan_abs_module.py
# Select mode 4 (Custom)
# Range: 0220 to 022F
```

### 3. ABS Activation History
Find diagnostic counters:
```bash
# Scan diagnostic range
python scan_abs_module.py
# Select mode 4 (Custom)
# Range: F000 to F0FF
```

## Next Steps After Scanning

### If DIDs Found
1. Document in knowledge base
2. Decode data formats
3. Create monitoring tools
4. Test with vehicle movement

### If Few DIDs Found
1. Try extended diagnostic session
2. Check security requirements
3. Compare with FORScan capabilities
4. Focus on working DIDs

## Integration with Other Modules

ABS data complements:
- PCM: Vehicle speed validation
- IC: Speedometer display
- PSCM: Steering assist coordination

## Output Files

Results saved to:
```
ford_escape_abs_scan_YYYYMMDD_HHMMSS.json
```

Contains:
- Vehicle info
- Module details (part number, addresses)
- Discovered DIDs with data
- Scan timestamp

## Example Output

```
Ford Escape 2008 - ABS Module Scanner
======================================================================

⚠ IMPORTANT: Set adapter switch to HS-CAN position!

Connecting to COM3...
Initializing ELM327 for HS-CAN...
✓ Connected and configured for HS-CAN
  Request address: 0x760
  Response address: 0x768

Testing ABS communication...
✓ ABS responding!

======================================================================
QUICK SCAN - Known ABS DIDs
======================================================================

  ✓ 0x0200 (ABS Parameter 1): 1A2B3C4D
  ✓ 0x0202 (ABS Parameter 2): 5E6F7A8B

SCAN SUMMARY
======================================================================

Total Available DIDs: 2
Total Security Locked: 0
Total Discovered: 2

Available DIDs:
  0x0200: ABS Parameter 1 (4 bytes)
  0x0202: ABS Parameter 2 (4 bytes)

✓ Results saved to: ford_escape_abs_scan_20260221_144530.json
✓ Disconnected
```

## Related Files

- `scan_ford_modules.py` - PCM scanner
- `scan_media_module.py` - ACM scanner (MS-CAN)
- `FORD_CAN_BUS_ARCHITECTURE.md` - CAN bus details
- `FORSCAN_MODULE_DISCOVERY.md` - ABS info from FORScan
- `knowledge_base/Ford_Escape_UDS_Commands.yaml` - DID database

## Recommended Scan Strategy

1. Start with Quick Scan to verify communication
2. Run Focused Scan to find common DIDs
3. Analyze results and identify interesting ranges
4. Use Custom Range to explore specific areas
5. Document findings in knowledge base
6. Create monitoring tools for useful DIDs

## Success Criteria

Scan is successful if:
- ABS responds to communication test
- Known DIDs (0x0200, 0x0202) are readable
- Additional DIDs discovered in typical ranges
- Data appears consistent and meaningful

Even finding a few new DIDs provides valuable diagnostic capability.
