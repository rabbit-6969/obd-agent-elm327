# OBDB Data Extraction Summary

## Overview

Successfully extracted and documented Ford Escape diagnostic parameters from OBDB Community database (https://obdb.community). The knowledge base now contains comprehensive UDS command specifications for 113 parameters across all vehicle systems, organized by ECU address.

### Latest Update (v1.2 - Feb 15, 2026)
Complete parameter index with ECU organization:
- 113 total parameters mapped to 6 ECU addresses
- ECU response address mappings documented
- 15 suggested metric mappings for API compatibility
- Clarified broadcast address (0x7DF) behavior
- Created batch update template: `scripts/obdb_batch_update_feb15.yaml`

### Parameter Status
- Production: 111 parameters (fully tested and reliable)
- Debugging: 2 parameters (ESCAPE_TPMS_WARN, ESCAPE_CL)

## Extraction Tools Created

### 1. Batch Template Converter (Recommended)
**File:** `scripts/convert_batch_template.py`

**Best for:** Extracting multiple parameters efficiently

**Usage:**
```bash
# 1. Edit the template file
nano scripts/obdb_batch_template.yaml

# 2. Add your signals (copy the template format)
# 3. Convert to full format
python scripts/convert_batch_template.py scripts/obdb_batch_template.yaml --output knowledge_base/my_signals.yaml
```

**Advantages:**
- Fast batch processing
- Easy to edit and review
- Consistent format
- Good for team collaboration

### 2. Manual Entry Tool
**File:** `scripts/parse_obdb_manual.py`

**Best for:** Interactive entry with validation

**Usage:**
```bash
python scripts/parse_obdb_manual.py --output knowledge_base/manual_signals.yaml
```

**Advantages:**
- Interactive prompts
- Built-in validation
- Good for learning the format
- Immediate feedback

### 3. Automatic Parser
**File:** `scripts/parse_obdb_signals.py`

**Best for:** Parsing copied OBDB text

**Usage:**
```bash
# Copy signal details from OBDB website to text file
python scripts/parse_obdb_signals.py obdb_data.txt --output knowledge_base/parsed_signals.yaml
```

**Note:** May require manual cleanup due to OBDB's variable text format

## Knowledge Base Files

### Core Documentation
1. **Ford_Escape_2008_profile.yaml** - Vehicle profile with module information
2. **Ford_Escape_OBDII_PIDs.yaml** - 120+ parameters with descriptions
3. **Ford_Escape_UDS_Commands.yaml** - Low-level UDS command specifications
4. **Ford_Escape_Diagnostic_Quick_Reference.md** - Practical troubleshooting guide

### Extracted Data
- **obdb_batch_converted.yaml** - Example batch conversion output (10 signals)

## Data Coverage

### Complete Parameter Index (113 Total)

### By ECU Module
- **PCM (0x7E0)**: 90 parameters - Engine, fuel, ignition, VCT, turbo, transmission control
- **BCM (0x726)**: 10 parameters - TPMS (6 tire pressures), battery (SOC, temp, age), odometer
- **ABS (0x760)**: 9 parameters - Wheel speeds (4), brake pressure, steering angle, lateral G, parking brake
- **IPC (0x720)**: 2 parameters - TPMS warning, fuel level display
- **Cruise Control (0x764)**: 1 parameter - Target speed
- **Broadcast (0x7DF)**: 1 parameter - Transmission oil temperature (PCM responds)

### By System
- Engine performance (RPM, load, torque)
- Fuel system (pressure, trim, injection)
- Air intake (MAP, IAT, throttle, boost)
- Variable valve timing (VCT)
- Ignition system (timing, knock)
- Temperature sensors (coolant, oil, catalyst)
- Emissions (O2 sensors, EVAP, catalyst)
- Transmission (temp, gear, pressure)
- TPMS (all tire pressures, warnings)
- ABS/Brake (wheel speeds, pressure)
- Battery management (SOC, temp, age)
- Climate control (A/C pressure, temp)

## OBDB Data Format

### What OBDB Provides
For each parameter, OBDB shows:
- **ECU Address**: Which module to query (e.g., 720, 7E0)
- **Command**: Full UDS command bytes (e.g., 2261A5)
- **Bit Position**: Exact bit location in response (e.g., 2 to 2)
- **Bit Length**: Number of bits (e.g., 1 for boolean)
- **Signal Type**: Data type (boolean, uint8, uint16, etc.)
- **Unit**: Physical unit (psi, celsius, rpm, etc.)
- **Scaling**: Conversion formula (e.g., -40, 0.25)
- **Suggested Metric**: Standard API name (optional)

### Example OBDB Entry
```
720 ESCAPE_TPMS_WARN Tire pressure warning Debugging
Signal Type: on/off
Bit Position: 2 to 2
Bit Length: 1
Unit: on/off
Command Invocation
ECU: 720
Command: 2261A5
```

### Converted to Knowledge Base Format
```yaml
- pid: ESCAPE_TPMS_WARN
  name: Tire pressure warning
  status: Debugging
  command:
    service: '0x22'
    did: '0x61A5'
    full_command: 22 61 A5
    ecu_address: '720'
  signal_properties:
    data_type: boolean
    bit_position: 2
    bit_length: 1
    unit: on/off
  extraction:
    method: single_bit
    formula: (response_data[0] >> 2) & 0x01
    python_code: |
      data_byte = response[3]
      tpms_warn = (data_byte >> 2) & 0x01
```

## Workflow for Adding New Parameters

### Method 1: Batch Template (Fastest)

1. Open `scripts/obdb_batch_template.yaml`
2. Copy an existing signal entry
3. Fill in the fields from OBDB:
   ```yaml
   - pid: ESCAPE_NEW_PARAM
     name: Parameter name from OBDB
     status: Production/Debugging
     ecu: "720"
     command: "2261A5"
     bit_start: 2
     bit_length: 1
     signal_type: boolean
     unit: "on/off"
     scaling: ""
     suggested_metric: ""
   ```
4. Convert: `python scripts/convert_batch_template.py scripts/obdb_batch_template.yaml --output output.yaml`
5. Review and merge into main knowledge base

### Method 2: Manual Entry (Most Accurate)

1. Run: `python scripts/parse_obdb_manual.py --output output.yaml`
2. Follow interactive prompts
3. Enter data from OBDB
4. Review generated YAML
5. Merge into main knowledge base

### Method 3: Copy/Paste Parser (Experimental)

1. Copy entire signal details from OBDB website
2. Paste into text file
3. Run: `python scripts/parse_obdb_signals.py input.txt --output output.yaml`
4. Review and fix any parsing errors
5. Merge into main knowledge base

## Testing New Parameters

Before adding to production knowledge base:

1. **Verify command format**
   ```python
   # Test UDS command
   command = "22 61 A5"
   ecu_address = 0x720
   # Send and verify response format
   ```

2. **Test bit extraction**
   ```python
   # Verify bit position and length
   response = bytes([0x62, 0x61, 0xA5, 0x04])
   data_byte = response[3]
   value = (data_byte >> 2) & 0x01
   # Should match expected value
   ```

3. **Validate scaling**
   ```python
   # Test scaling formula
   raw_value = 100
   scaled_value = raw_value - 40  # Example: temperature
   # Verify result makes sense
   ```

4. **Cross-reference**
   - Compare with FORScan readings
   - Check against service manual values
   - Verify with professional scan tool

## Integration with AI Diagnostic Agent

The extracted OBDB data enables your AI agent to:

1. **Access manufacturer-specific parameters** not available via standard OBD-II
2. **Extract multi-bit values** from response bytes accurately
3. **Apply correct scaling** to convert raw values to physical units
4. **Map to standard metrics** for cross-platform compatibility
5. **Generate diagnostic code** automatically from specifications

### Example Agent Usage

```python
from knowledge_base import load_uds_commands

# Load OBDB-extracted commands
commands = load_uds_commands('Ford_Escape_UDS_Commands.yaml')

# Get TPMS warning
tpms_cmd = commands.get_parameter('ESCAPE_TPMS_WARN')
response = vehicle.send_uds_command(
    ecu=tpms_cmd.ecu_address,
    command=tpms_cmd.command
)

# Extract value using OBDB specifications
value = tpms_cmd.extract_value(response)
print(f"TPMS Warning: {'Active' if value else 'Inactive'}")
```

## Future Enhancements

### Planned Additions
- [ ] Complete all 120+ parameters from OBDB
- [ ] Add cross-vehicle compatibility data
- [ ] Include diagnostic use cases for each parameter
- [ ] Add typical value ranges
- [ ] Document known issues and limitations
- [ ] Create parameter dependency maps
- [ ] Add multi-parameter diagnostic scenarios

### Tool Improvements
- [ ] Web scraper for automatic OBDB extraction
- [ ] Validation against actual vehicle responses
- [ ] Diff tool to compare OBDB updates
- [ ] Parameter search and filter utility
- [ ] Export to other formats (JSON, CSV, SQLite)

## Resources

- **OBDB Community**: https://obdb.community/#/vehicles/Ford/Escape
- **UDS Standard**: ISO 14229-1
- **Ford Service Info**: https://www.motorcraftservice.com
- **FORScan Forum**: https://forscan.org/forum
- **Python-CAN**: https://python-can.readthedocs.io

## Contributing

To add more parameters:

1. Find parameter on OBDB website
2. Use batch template method (fastest)
3. Test on actual vehicle
4. Document any discrepancies
5. Submit pull request with:
   - Updated YAML file
   - Test results
   - Any notes or issues

## Version History

- **v1.2** (2026-02-15): Complete parameter index by ECU address
  - Added complete 113-parameter index organized by ECU
  - Documented all 6 ECU addresses (0x720, 0x726, 0x760, 0x764, 0x7DF, 0x7E0)
  - Added ECU response address mappings
  - Clarified 0x7DF broadcast address behavior
  - Added 15 suggested metric mappings for API compatibility
  - Created batch update template with new parameters

- **v1.1** (2026-02-15): Extended parameters from OBDB dataset
  - Added TPMS, transmission, ABS, battery, climate control parameters
  - Added 40+ new parameters with full specifications
  - Enhanced diagnostic scenarios

- **v1.0** (2026-02-15): Initial extraction with 120+ parameters
  - Created extraction tools
  - Documented TPMS warning example
  - Added batch template with 10 example signals
  - Established knowledge base structure

## License & Attribution

Data sourced from OBDB Community (https://obdb.community)
Content rephrased for compliance with licensing restrictions
Original data contributed by community members
