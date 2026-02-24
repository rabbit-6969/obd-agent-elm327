# OBDB Signal Parser

This script extracts UDS command details from OBDB community data and generates structured YAML documentation for your knowledge base.

## Installation

```bash
pip install pyyaml
```

## Usage

### Step 1: Copy OBDB Signal Data

1. Go to https://obdb.community/#/vehicles/Ford/Escape
2. Click on a parameter (e.g., ESCAPE_TPMS_WARN)
3. Copy the entire signal details section including:
   - Parameter ID and name
   - ECU address
   - Command invocation
   - Bit position and length
   - Signal type and unit

### Step 2: Save to Text File

Paste the copied data into a text file (e.g., `obdb_signals.txt`)

Example format:
```
720ESCAPE_TPMS_WARNTire pressure warningDebugging——
Signal Details
Tire pressure warning
ESCAPE_TPMS_WARN
Debugging
Signal Properties
Signal Type:offonBit Position:2 to 2Bit Length:1Scaling:Unit: offon
Command Invocation
ECU:720Command:2261A5
```

### Step 3: Run Parser

```bash
# Output to console
python scripts/parse_obdb_signals.py obdb_signals.txt

# Output to file
python scripts/parse_obdb_signals.py obdb_signals.txt --output knowledge_base/obdb_extracted.yaml
```

## Output Format

The script generates YAML entries with:

- **PID**: Parameter identifier (e.g., ESCAPE_TPMS_WARN)
- **Command details**: Service, DID, ECU address
- **Signal properties**: Data type, bit position, length
- **Extraction formula**: How to extract the value from response bytes
- **Python code**: Ready-to-use extraction code

Example output:
```yaml
obdb_extracted_parameters:
  description: Parameters extracted from OBDB community database
  extraction_date: 2026-02-15
  source: https://obdb.community
  parameters:
    - pid: ESCAPE_TPMS_WARN
      name: Tire pressure warning
      description: Tire pressure warning
      status: Debugging
      command:
        service: '0x22'
        did: '0x61A5'
        full_command: 22 61 A5
        ecu_address: '720'
      response:
        format: 62 61 A5 [DATA...]
        data_length: Variable
      signal_properties:
        signal_type: offon
        data_type: boolean
        bit_position: 2
        bit_length: 1
        byte_index: 0
        unit: offon
      extraction:
        method: single_bit
        formula: (response_data[0] >> 2) & 0x01
        python_code: |
          # Extract ESCAPE_TPMS_WARN
          data_byte = response[3]  # Skip header bytes
          escape_tpms_warn = (data_byte >> 2) & 0x01
          # Result: 0 or 1
```

## Batch Processing

To extract multiple parameters at once:

1. Copy all parameter details from OBDB into one text file
2. Separate each parameter with a blank line
3. Run the parser on the combined file

```bash
python scripts/parse_obdb_signals.py all_signals.txt --output knowledge_base/ford_escape_obdb_complete.yaml
```

## Integration with Knowledge Base

After generating the YAML file:

1. Review the extracted data for accuracy
2. Merge with existing `Ford_Escape_UDS_Commands.yaml`
3. Add any missing details (diagnostic use, interpretation, etc.)
4. Test commands on actual vehicle to verify

## Supported Signal Types

The parser handles:
- **Boolean flags** (1 bit): on/off, true/false
- **Multi-bit values** (2-8 bits): Small integers, enums
- **Byte values** (8 bits): uint8, int8
- **Word values** (16 bits): uint16, int16
- **Multi-byte values**: Requires manual adjustment

## Troubleshooting

### No signals found
- Check that input file contains OBDB signal details
- Ensure format matches expected pattern (ECU, Command, Bit Position)
- Try copying data again from OBDB website

### Incorrect bit extraction
- Verify bit position and length in OBDB
- Check if signal spans multiple bytes
- Test extraction code on actual vehicle response

### Missing fields
- Some OBDB entries may not have all fields
- Manually add missing information after extraction
- Cross-reference with other sources (FORScan, service manuals)

## Example Workflow

```bash
# 1. Extract TPMS parameters
python scripts/parse_obdb_signals.py tpms_signals.txt --output tpms_extracted.yaml

# 2. Extract transmission parameters
python scripts/parse_obdb_signals.py trans_signals.txt --output trans_extracted.yaml

# 3. Combine into main knowledge base
cat tpms_extracted.yaml trans_extracted.yaml >> knowledge_base/Ford_Escape_UDS_Commands.yaml

# 4. Test on vehicle
python test_uds_commands.py --verify tpms_extracted.yaml
```

## Tips

- Start with simple boolean flags (1-bit signals) to verify parser works
- Test extracted commands on vehicle before adding to production knowledge base
- Document any discrepancies between OBDB data and actual vehicle behavior
- Keep original OBDB text files for reference
- Version control your knowledge base to track changes

## Contributing

If you find issues with the parser or have improvements:
1. Document the issue with example input/output
2. Test your fix on multiple signal types
3. Update this README with any new features

## Resources

- OBDB Community: https://obdb.community
- UDS Standard: ISO 14229-1
- Ford Service Information: https://www.motorcraftservice.com
- FORScan Forum: https://forscan.org/forum
