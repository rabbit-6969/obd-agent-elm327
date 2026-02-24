# OBDB Extraction Quick Start

## 30-Second Start

```bash
# 1. Edit template with your signals
nano scripts/obdb_batch_template.yaml

# 2. Convert to full format
python scripts/convert_batch_template.py scripts/obdb_batch_template.yaml --output my_signals.yaml

# 3. Done! Review my_signals.yaml
```

## Adding One Signal from OBDB

1. Go to https://obdb.community/#/vehicles/Ford/Escape
2. Click on a parameter (e.g., ESCAPE_RPM)
3. Copy these values:
   - ECU: `7E0`
   - Command: `220C`
   - Bit Position: `0 to 15`
   - Bit Length: `16`
   - Signal Type: `uint16`
   - Unit: `rpm`
   - Scaling: `0.25`

4. Add to `scripts/obdb_batch_template.yaml`:
```yaml
  - pid: ESCAPE_RPM
    name: Engine speed
    status: Production
    ecu: "7E0"
    command: "220C"
    bit_start: 0
    bit_length: 16
    signal_type: uint16
    unit: "rpm"
    scaling: "0.25"
    suggested_metric: ""
```

5. Convert:
```bash
python scripts/convert_batch_template.py scripts/obdb_batch_template.yaml --output rpm_signal.yaml
```

## Common Signal Types

| OBDB Type | Bit Length | Example |
|-----------|------------|---------|
| boolean / on/off | 1 | TPMS warning |
| uint8 | 8 | Coolant temp |
| uint16 | 16 | Engine RPM |
| int8 | 8 | Fuel trim |
| int16 | 16 | Signed values |

## Common Scaling Formulas

| Formula | Meaning | Example |
|---------|---------|---------|
| `-40` | Subtract 40 | Temperature (°C) |
| `0.25` | Multiply by 0.25 | RPM / 4 |
| `(x-128)*100/128` | Fuel trim % | STFT/LTFT |
| `0.363` | kPa to PSI | Tire pressure |
| `1` | No scaling | Direct value |

## ECU Addresses

| Address | Module | Common Parameters |
|---------|--------|-------------------|
| 7E0 | PCM | Engine, fuel, ignition |
| 726 | BCM | TPMS, battery, lights |
| 760 | ABS | Wheel speeds, brakes |
| 720 | IPC | Gauges, warnings |
| 7DF | Generic | Broadcast address |

## Troubleshooting

**Problem:** Command not working on vehicle
- Check ECU address is correct
- Verify command format (no spaces in template)
- Try with FORScan first to confirm

**Problem:** Wrong value extracted
- Verify bit position and length
- Check scaling formula
- Test with known good value

**Problem:** Parser errors
- Check YAML syntax (indentation matters!)
- Ensure all required fields present
- Use quotes around hex values

## Next Steps

1. Extract 5-10 parameters you need most
2. Test on actual vehicle
3. Add to main knowledge base
4. Document any issues found
5. Share improvements!

## Help

- Full docs: `scripts/obdb_parser_README.md`
- Examples: `scripts/obdb_batch_template.yaml`
- Summary: `knowledge_base/OBDB_EXTRACTION_SUMMARY.md`
