# Captured Data

This directory contains real diagnostic session data captured from vehicles during testing and development.

## Purpose

According to the design document, this folder stores:
- **Captured data (JSON)**: Real diagnostic session logs
- Module scan results
- DID discovery results
- System exploration data

## File Naming Convention

Files follow the pattern: `{vehicle}_{module}_{action}_{timestamp}.json`

Examples:
- `ford_escape_abs_scan_20260221_171854.json` - ABS module scan from Ford Escape
- `ford_escape_module_scan_20260221_170355.json` - General module scan
- `discovered_dids_20260215_164211.json` - DID discovery results

## Usage

This data is used for:
1. **Testing** - Validating diagnostic procedures without vehicle access
2. **Development** - Understanding response formats and patterns
3. **Knowledge Building** - Extracting procedures to add to vehicle profiles
4. **Debugging** - Analyzing past diagnostic sessions

## Integration with Knowledge Base

Data from this folder can be processed and integrated into:
- `Ford_Escape_2008_profile.yaml` - Human-readable vehicle profile
- `Ford_Escape_2008_technical.dat` - Machine-optimized technical data
- `Ford_Escape_UDS_Commands.yaml` - UDS command definitions

## Maintenance

- Keep files organized by vehicle make/model
- Archive old data periodically
- Document any unusual findings in the main knowledge base
