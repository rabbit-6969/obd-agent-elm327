# Toolkit Scripts

This directory contains standalone Python scripts that the AI Vehicle Diagnostic Agent uses to interact with vehicles and perform research. Each script follows a standard CLI interface: JSON in → JSON out.

## Overview

The toolkit is organized into three categories:

1. **Vehicle Communication** - Direct interaction with vehicles via ELM327
2. **Web Research** - Finding diagnostic procedures online
3. **Knowledge Management** - Storing and retrieving learned procedures

## Script Categories

### Vehicle Communication

Scripts for communicating with vehicles through OBD2/UDS protocols.

#### read_dtc.py
Read diagnostic trouble codes from vehicle modules.

**Usage:**
```bash
python toolkit/vehicle_communication/read_dtc.py --port COM3 --module HVAC
```

**Inputs:**
- `--port` (required): COM port for ELM327 adapter
- `--module` (optional): Module name (HVAC, ABS, PCM, etc.)
- `--address` (optional): Module CAN address (hex)

**Output:**
```json
{
  "success": true,
  "dtcs": [
    {"code": "P1632", "raw": "16 32"}
  ]
}
```

#### clear_dtc.py
Clear diagnostic trouble codes from vehicle.

**Usage:**
```bash
python toolkit/vehicle_communication/clear_dtc.py --port COM3
```

**Inputs:**
- `--port` (required): COM port for ELM327 adapter
- `--module` (optional): Specific module to clear

**Output:**
```json
{
  "success": true,
  "cleared": true
}
```

#### read_vin.py
Read vehicle identification number.

**Usage:**
```bash
python toolkit/vehicle_communication/read_vin.py --port COM3
```

**Inputs:**
- `--port` (required): COM port for ELM327 adapter

**Output:**
```json
{
  "success": true,
  "vin": "1FAHP551XX8156549"
}
```

### Web Research

Scripts for researching diagnostic procedures when they're not in the knowledge base.

#### ai_search.py
AI-assisted web search for diagnostic procedures.

**Usage:**
```bash
python toolkit/web_research/ai_search.py --query "Ford Escape 2008 HVAC DTC"
```

**Inputs:**
- `--query` (required): Search query
- `--vehicle` (optional): Vehicle make/model/year

**Output:**
```json
{
  "success": true,
  "results": [
    {
      "source": "https://example.com/manual",
      "commands": ["03"],
      "confidence": 0.9
    }
  ]
}
```

#### user_fallback.py
User fallback mode when automated search fails.

**Usage:**
```bash
python toolkit/web_research/user_fallback.py --query "Ford HVAC diagnostics"
```

**Inputs:**
- `--query` (required): Search query to present to user

**Output:**
```json
{
  "success": true,
  "commands": ["03", "04"],
  "user_provided": true
}
```

### Knowledge Management

Scripts for managing the diagnostic knowledge base.

#### append_procedure.py
Append successful diagnostic procedure to knowledge base.

**Usage:**
```bash
python toolkit/knowledge_management/append_procedure.py \
  --vehicle Ford_Escape_2008 \
  --module HVAC \
  --procedure '{"address": "7A0", "command": "03"}'
```

**Inputs:**
- `--vehicle` (required): Vehicle identifier
- `--module` (required): Module name
- `--procedure` (required): Procedure details as JSON

**Output:**
```json
{
  "success": true,
  "saved_to": "knowledge_base/Ford_Escape_2008_technical.dat"
}
```

#### query_knowledge.py
Query knowledge base for diagnostic procedures.

**Usage:**
```bash
python toolkit/knowledge_management/query_knowledge.py \
  --vehicle Ford_Escape_2008 \
  --module HVAC \
  --action read_dtc
```

**Inputs:**
- `--vehicle` (required): Vehicle identifier
- `--module` (required): Module name
- `--action` (optional): Diagnostic action

**Output:**
```json
{
  "success": true,
  "procedure": {
    "address": "7A0",
    "command": "03",
    "response_pattern": "43[0-9A-F]{4,}"
  }
}
```

## Standard Interface

All toolkit scripts follow this standard:

### Input
- Command-line arguments for parameters
- JSON input via stdin (optional)

### Output
- JSON to stdout
- Always includes `"success": true/false`
- Error details in `"error"` field if failed

### Error Handling
Scripts return non-zero exit codes on failure and include error details in JSON output.

## Task Mappings

Common diagnostic tasks map to toolkit scripts:

| Task | Scripts |
|------|---------|
| Read diagnostic codes | `read_dtc.py` |
| Clear diagnostic codes | `clear_dtc.py` |
| Identify vehicle | `read_vin.py` |
| Research procedure | `ai_search.py`, `user_fallback.py` |
| Save procedure | `append_procedure.py` |
| Lookup procedure | `query_knowledge.py` |

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to ELM327"

**Solutions:**
1. Check COM port is correct
2. Verify ELM327 is powered on
3. Ensure vehicle ignition is on
4. Try different baud rate (38400, 115200)

### No Response from Module

**Problem:** "No response from module"

**Solutions:**
1. Verify module address is correct
2. Check vehicle is in correct diagnostic mode
3. Try standard OBD2 address (7E0) first
4. Ensure CAN bus is active

### Invalid DTC Format

**Problem:** "Failed to parse DTC response"

**Solutions:**
1. Check response format matches expected pattern
2. Verify command is correct for module
3. Try Mode 03 for standard OBD2
4. Check for manufacturer-specific format

### Web Research Fails

**Problem:** "No procedures found online"

**Solutions:**
1. Use `user_fallback.py` for manual search
2. Check service manual for vehicle
3. Try related vehicle models (same manufacturer/era)
4. Consult vehicle-specific forums

## Adding New Scripts

To add a new toolkit script:

1. Create script in appropriate category directory
2. Follow standard CLI interface (JSON in/out)
3. Add entry to `toolkit_registry.json`
4. Update this README with usage examples
5. Test script independently before integration

## Examples

### Complete Diagnostic Workflow

```bash
# 1. Read VIN to identify vehicle
python toolkit/vehicle_communication/read_vin.py --port COM3

# 2. Query knowledge base for HVAC procedure
python toolkit/knowledge_management/query_knowledge.py \
  --vehicle Ford_Escape_2008 --module HVAC --action read_dtc

# 3. If not found, search online
python toolkit/web_research/ai_search.py \
  --query "Ford Escape 2008 HVAC read DTC"

# 4. Read DTCs from HVAC
python toolkit/vehicle_communication/read_dtc.py \
  --port COM3 --module HVAC --address 7A0

# 5. Save successful procedure
python toolkit/knowledge_management/append_procedure.py \
  --vehicle Ford_Escape_2008 --module HVAC \
  --procedure '{"address": "7A0", "command": "03", "response": "43 16 32"}'
```

### Testing Scripts

Each script includes a test mode:

```bash
# Test with mock data
python toolkit/vehicle_communication/read_dtc.py --test

# Validate without executing
python toolkit/vehicle_communication/read_dtc.py --validate --port COM3
```

## Registry

The `toolkit_registry.json` file contains:
- Script metadata (path, description, inputs/outputs)
- Task-to-script mappings
- Category organization

The agent uses this registry to discover and execute appropriate scripts for each diagnostic task.

## See Also

- [Agent Core Documentation](../agent_core/README.md)
- [Knowledge Base Format](../knowledge_base/README.md)
- [User Guide](../docs/USER_GUIDE.md)
