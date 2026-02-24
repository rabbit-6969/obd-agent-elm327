# 2007 Jeep Wrangler JK Diagnostic Guide

Complete guide for reading airbag errors and shifter position using Vgate iCar Pro BLE 4.0.

## Quick Start

### 1. Install Requirements

```bash
pip install obd
pip install pyserial
```

### 2. Setup Bluetooth Connection

**Windows:**
1. Pair Vgate adapter in Bluetooth settings
2. Note the COM port (e.g., COM5)
3. Adapter PIN is usually: `1234` or `0000`

**Mac/Linux:**
1. Pair adapter: `bluetoothctl` → `pair XX:XX:XX:XX:XX:XX`
2. Note device path (e.g., `/dev/rfcomm0`)

### 3. Connect to Vehicle

1. Plug Vgate adapter into OBD-II port (under dashboard, driver side)
2. Turn ignition to ON (engine can be off)
3. Wait for adapter LED to blink (ready)
4. Run diagnostic script:

```bash
python jeep_wrangler_diagnostics.py
```

## What You'll Get

### Airbag Module DTCs
- All stored airbag fault codes
- Code descriptions
- Severity levels
- B-codes (Body system, includes airbag)

### Shifter Position
- Current gear selection (if available)
- Transmission parameters
- Alternative data if direct reading not supported

## Important Notes

### Airbag Module Access

⚠️ **Standard OBD-II Limitation:**
- Most consumer OBD-II adapters (including Vgate) have LIMITED access to airbag module
- Standard OBD-II primarily focuses on emissions-related systems
- Airbag module uses separate diagnostic protocols

**What You CAN Read:**
- Generic DTCs that include airbag codes (B-codes)
- Some airbag-related faults if they affect other systems
- Basic airbag warning light status

**What You CANNOT Read (without manufacturer tool):**
- Detailed airbag deployment history
- Individual sensor status
- Airbag module internal diagnostics
- Crash data recorder information

### Shifter Position Access

⚠️ **Manufacturer-Specific Data:**
- Shifter position is NOT a standard OBD-II parameter
- Jeep uses proprietary PIDs for transmission data
- May require Chrysler/Jeep-specific diagnostic tool

**Alternatives:**
- Monitor transmission-related parameters (RPM, speed, load)
- Infer gear from vehicle behavior
- Use Jeep-specific tools (see below)

## Alternative Tools for Full Access

### For Complete Airbag Diagnostics:

1. **Chrysler wiTECH** (Official Dealer Tool)
   - Full airbag module access
   - Crash data retrieval
   - Component testing
   - Cost: $$$$ (dealer only)

2. **AlfaOBD** (Enthusiast Tool)
   - Works with ELM327 adapters
   - Chrysler/Jeep/Dodge specific
   - Airbag module access
   - Cost: ~$50 (one-time)
   - Download: https://www.alfaobd.com/

3. **JScan** (Mobile App)
   - Works with OBDLink adapters
   - Jeep-specific diagnostics
   - Airbag module support
   - Cost: ~$30/year
   - iOS/Android available

### For Shifter Position:

1. **AlfaOBD** - Best option for Jeep/Chrysler
2. **Torque Pro** - May work with custom PIDs
3. **Car Scanner ELM OBD2** - Has Jeep profiles

## Using AlfaOBD (Recommended)

### Setup:
1. Download AlfaOBD from official website
2. Install on Windows laptop
3. Connect Vgate adapter via Bluetooth
4. Launch AlfaOBD

### Reading Airbag Codes:
1. Select "Jeep" → "Wrangler" → "2007"
2. Go to "Body" → "Airbag Control Module (ACM)"
3. Click "Read Errors"
4. View detailed fault codes with descriptions

### Reading Shifter Position:
1. Go to "Powertrain" → "Transmission Control Module (TCM)"
2. Select "Live Data"
3. Find "Gear Position" or "PRNDL Position"
4. Monitor in real-time

## Manual OBD-II Commands

If you want to try manual commands with your Vgate adapter:

### Read All DTCs (Mode 03)
```
AT Z          # Reset adapter
AT E1         # Echo on
AT H1         # Headers on
AT SP 0       # Auto protocol
03            # Read DTCs
```

### Read Airbag Module Directly (if supported)
```
AT SH 738     # Set header to Airbag module (example)
19 02 AF      # Read DTCs by status
```

### Read Transmission Data
```
AT SH 7E1     # Set header to TCM
22 1234       # Read data (PID varies)
```

## Jeep Wrangler JK (2007) Specific Info

### OBD-II Port Location
- Under dashboard, left of steering column
- Above brake pedal area
- 16-pin connector

### CAN Bus Protocol
- ISO 15765-4 CAN (500 kbaud)
- 11-bit identifiers
- Standard OBD-II protocol

### Module Addresses (CAN)
- **PCM** (Powertrain): 0x7E0 / 0x7E8
- **TCM** (Transmission): 0x7E1 / 0x7E9
- **ACM** (Airbag): 0x738 / 0x758 (approximate)
- **BCM** (Body): 0x726 / 0x72E (approximate)

### Common Airbag DTCs

| Code | Description |
|------|-------------|
| B0001 | Driver airbag circuit fault |
| B0002 | Passenger airbag circuit fault |
| B0010 | Driver seat belt pretensioner fault |
| B0011 | Passenger seat belt pretensioner fault |
| B0020 | Side airbag circuit fault |
| B0100 | Airbag control module fault |
| B1000 | Airbag warning lamp circuit fault |

### Transmission Gear Positions

**Automatic (42RLE):**
- P - Park
- R - Reverse
- N - Neutral
- D - Drive
- 2 - Second gear
- 1 - First gear

**Manual (NSG370):**
- 1-6 - Forward gears
- R - Reverse
- N - Neutral

## Troubleshooting

### Adapter Won't Connect
1. Check Bluetooth pairing
2. Verify adapter is in OBD-II port
3. Turn ignition to ON
4. Try unplugging/replugging adapter
5. Check adapter LED (should blink)

### No Airbag Data
- Normal for standard OBD-II adapters
- Airbag module requires special access
- Use AlfaOBD or dealer tool
- Check if airbag warning light is on

### No Shifter Position
- Not available via standard OBD-II
- Use AlfaOBD for Jeep-specific access
- Monitor transmission parameters instead
- Check if vehicle is in motion

### Connection Drops
- Bluetooth interference
- Low adapter battery (if wireless)
- Vehicle battery voltage low
- Try moving closer to vehicle

## Python Script Usage

### Basic Usage
```bash
python jeep_wrangler_diagnostics.py
```

### Custom Port (if auto-detect fails)
```python
# Edit script, line ~30:
self.connection = obd.OBD("/dev/rfcomm0")  # Linux/Mac
# or
self.connection = obd.OBD("COM5")  # Windows
```

### Read Only DTCs
```python
diag = JeepWranglerDiagnostics()
diag.connect()
diag.read_all_dtcs()
diag.disconnect()
```

### Monitor Live Data
```python
diag = JeepWranglerDiagnostics()
diag.connect()
diag.monitor_live_data(duration=60)  # 60 seconds
diag.disconnect()
```

## Expected Output

### Successful Connection
```
============================================================
Jeep Wrangler JK (2007) Diagnostic Tool
============================================================

Connecting to vehicle...
✓ Connected successfully!
  Protocol: ISO 15765-4 (CAN 11/500)
  Port: /dev/rfcomm0

============================================================
VEHICLE INFORMATION
============================================================
  VIN: 1J4GA59167L123456
  Adapter Version: ELM327 v2.1
  Battery Voltage: 12.4 V

============================================================
ALL DIAGNOSTIC TROUBLE CODES
============================================================
Found 2 DTC(s):

BODY CODES (Airbag, Lighting, etc.):
  B0001: Driver Airbag Circuit Resistance High
  B1000: Airbag Warning Lamp Circuit Open

============================================================
TRANSMISSION SHIFTER POSITION
============================================================
⚠ Shifter position not available via standard OBD-II

  Available Transmission Data:
    Engine RPM: 0 RPM
    Vehicle Speed: 0 km/h
    Throttle Position: 0.0 %
    Engine Load: 0.0 %
```

## Safety Warnings

⚠️ **IMPORTANT:**

1. **Airbag System**: Never attempt repairs without proper training
2. **Electrical Safety**: Disconnect battery before airbag work
3. **Diagnostic Only**: This tool is for reading codes, not repairs
4. **Professional Help**: Airbag issues require qualified technician
5. **No Liability**: Use at your own risk

## Additional Resources

- **Jeep Wrangler JK Forum**: https://www.jk-forum.com/
- **AlfaOBD Support**: https://www.alfaobd.com/forum/
- **OBD-II Basics**: https://www.obdii.com/
- **Python OBD Library**: https://python-obd.readthedocs.io/

## Support

For issues with:
- **Script**: Check Python version (3.7+), reinstall obd library
- **Adapter**: Verify Bluetooth pairing, check LED status
- **Vehicle**: Ensure ignition ON, check battery voltage
- **Airbag Access**: Use AlfaOBD or dealer tool for full access

## License

This diagnostic tool is provided as-is for educational purposes.
Always consult professional technicians for vehicle repairs.
