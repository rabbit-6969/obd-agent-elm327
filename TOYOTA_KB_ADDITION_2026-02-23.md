# Toyota Knowledge Base Addition - February 23, 2026

## Issue Identified

Created Toyota FJ Cruiser ABS DTC reader (`read_fj_cruiser_abs_dtcs.py`) and guide (`FJ_CRUISER_ABS_DTC_GUIDE.md`), but **failed to create proper knowledge base documentation** following the established dual-format design.

## Root Cause

**Inconsistent thinking**: Treated Toyota as "quick standalone script" rather than applying the same systematic knowledge base approach used for Ford Escape.

## Resolution

Created complete Toyota FJ Cruiser 2008 knowledge base following the dual-format design:

### 1. Technical Data (.dat) - Machine-Optimized
**File**: `knowledge_base/Toyota_FJ_Cruiser_2008_technical.dat` (v1.0)

- Compact format for fast parsing (< 50ms)
- ABS module (0x7B0/0x7B8) with UDS Service 0x19 commands
- PCM module (0x7E0/0x7E8) with standard OBD-II commands
- Toyota 3-byte DTC format parsing rules
- DTC status byte bit mappings (ISO 14229-1)
- Response parsing patterns
- Real vehicle test responses

### 2. Vehicle Profile (.yaml) - Human-Readable
**File**: `knowledge_base/Toyota_FJ_Cruiser_2008_profile.yaml`

- Complete vehicle information (2008 FJ Cruiser, 1GR-FE V6 4.0L)
- Module descriptions (ABS, PCM) with part numbers
- Common issues and diagnostic procedures
- DTC descriptions (C1551A, C1201) with repair hints
- Repair procedures (ABS DTC reading/clearing)
- Technical notes explaining UDS vs OBD-II
- DTC status byte interpretation guide
- Related vehicles (4Runner, Tacoma, GX470, Sequoia, Tundra)

### 3. Manufacturer Services (.yaml) - Protocol Reference
**File**: `knowledge_base/Toyota_UDS_Services.yaml`

- Complete UDS services reference for Toyota/Lexus
- Service 0x19 (ReadDTCInformation) with all sub-functions:
  - 0x02: reportDTCByStatusMask
  - 0x0A: reportSupportedDTC
  - 0x04: reportDTCSnapshotIdentification
  - 0x06: reportDTCExtDataRecordByDTCNumber
- Service 0x14 (ClearDiagnosticInformation) with group masks
- Service 0x22 (ReadDataByIdentifier)
- Toyota 3-byte DTC format specification with examples
- DTC status byte (8 bits) detailed breakdown
- Negative Response Codes (NRC) reference
- Toyota/Lexus module addressing (PCM, ABS, SRS, BCM, TCM)
- Python implementation examples

## Commit Details

**Commit**: `2e9c539`
**Message**: "feat: Add Toyota FJ Cruiser 2008 knowledge base"
**Files**: 3 files changed, 656 insertions(+)
**Push**: Successfully pushed to main branch

## Consistency Achieved

The knowledge base now follows the same structure across manufacturers:

### Ford Escape 2008
- `Ford_Escape_2008_technical.dat` (v2.1)
- `Ford_Escape_2008_profile.yaml`
- `Ford_UDS_Services_Complete.yaml`

### Toyota FJ Cruiser 2008
- `Toyota_FJ_Cruiser_2008_technical.dat` (v1.0)
- `Toyota_FJ_Cruiser_2008_profile.yaml`
- `Toyota_UDS_Services.yaml`

Both follow the dual-format design:
- **Technical .dat**: Machine-optimized, compact, fast parsing
- **Profile .yaml**: Human-readable, rich context, repair hints
- **Services .yaml**: Manufacturer-specific protocol documentation

## Lesson Learned

When creating tools for new vehicles, always ask:
1. Does this need knowledge base documentation?
2. Am I following the established pattern?
3. Is this consistent with existing vehicles?

The answer for Toyota was clearly **YES** to all three, but I initially treated it as a one-off script instead of properly integrating it into the knowledge base system.

## Data Sources

- ISO 14229-1 UDS specification
- Toyota diagnostic procedures
- Real vehicle testing (FJ Cruiser 2008)
- Industry-standard Toyota/Lexus addressing (0x7B0/0x7B8 for ABS)
