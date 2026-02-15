# ISO 14229-1 UDS Service 0x31: RoutineControl

**Source:** ISO 14229-1:2013(E) Section 13.2 (pages 260-269)  
**Service ID:** 0x31  
**Response ID:** 0x71 (0x31 + 0x40)

---

## Service Description

The RoutineControl service is used to execute a defined sequence of steps and obtain any relevant results. This service is used for complex operations that go beyond simple input/output control.

**Typical Use Cases:**
- Run self-tests (transmission self-test, ABS pump test, EVAP leak test)
- Erase memory
- Reset or learn adaptive data
- Run calibration procedures
- Execute predefined sequences (e.g., close convertible roof)
- Override normal control strategy with complex logic

**Key Difference from InputOutputControlByIdentifier:**
- Service 0x31: Complex sequences and tests
- Service 0x2F: Simple, static control

---

## Sub-Functions

| Sub-function | Value | Description |
|--------------|-------|-------------|
| startRoutine | 0x01 | Start the routine |
| stopRoutine | 0x02 | Stop the routine |
| requestRoutineResults | 0x03 | Get results after routine completes |

---

## Request Message Format

```
31 [sub-function] [RID_high] [RID_low] [options...]
```

### Routine Identifier (RID)

- 2-byte identifier (like DID, but for routines)
- Range: 0x0000-0xFFFF
- Manufacturer-specific (see Annex F.1)

---

## Examples

### Example 1: Start Transmission Self-Test (RID 0x0201)

```
Request:  31 01 02 01
Response: 71 01 02 01 32
```

**Breakdown:**
- `31` = Service ID
- `01` = startRoutine
- `02 01` = RID 0x0201 (transmission self-test)
- Response `32` = status (manufacturer-specific)

### Example 2: Stop Routine

```
Request:  31 02 02 01
Response: 71 02 02 01 30
```

**Breakdown:**
- `31` = Service ID
- `02` = stopRoutine
- `02 01` = RID 0x0201
- Response `30` = status

### Example 3: Request Results

```
Request:  31 03 02 01
Response: 71 03 02 01 30 33 ... 8F
```

**Breakdown:**
- `31` = Service ID
- `03` = requestRoutineResults
- `02 01` = RID 0x0201
- Response bytes = test results (manufacturer-specific)

### Example 4: Start Routine with Options (Transmission Calibration)

```
Request:  31 01 02 02 06 01
Response: 71 01 02 02 32 33 ... 8F
```

**Breakdown:**
- `31` = Service ID
- `01` = startRoutine
- `02 02` = RID 0x0202 (gear calibration)
- `06` = gear #6
- `01` = test mode (in-vehicle)

---

## Positive Response Format

```
71 [sub-function] [RID_high] [RID_low] [routineInfo] [status...]
```

- **routineInfo**: Optional byte indicating routine type
- **status**: Manufacturer-specific status/results data

---

## Negative Response Codes

| NRC | Mnemonic | Description |
|-----|----------|-------------|
| 0x12 | SFNS | sub-functionNotSupported - Sub-function not supported for this RID |
| 0x13 | IMLOIF | incorrectMessageLengthOrInvalidFormat |
| 0x22 | CNC | conditionsNotCorrect - Conditions not met |
| 0x24 | RSE | requestSequenceError - Wrong sequence (e.g., stop before start) |
| 0x31 | ROOR | requestOutOfRange - RID not supported or invalid options |
| 0x33 | SAD | securityAccessDenied - RID requires security access |
| 0x72 | GPF | generalProgrammingFailure - Memory access error |

---

## Routine Execution Methods

### Method A: Client-Controlled
1. Client starts routine
2. Routine runs
3. **Client must stop routine**
4. Client can request results

### Method B: Self-Terminating
1. Client starts routine
2. Routine runs
3. **Routine stops itself automatically**
4. Client can request results

---

## Usage for Transmission Diagnostics

### Discover Available Routines

Scan RID range (e.g., 0x0200-0x02FF for transmission):

```python
for rid in range(0x0200, 0x0300):
    send: f"31 01 {rid:04X}"
    if positive_response:
        print(f"Found routine: {rid:04X}")
```

### Run Transmission Self-Test

```python
# Start test
send: "31 01 0201"
receive: "71 01 0201 32"  # Started

# Wait for completion (or stop manually)
send: "31 02 0201"
receive: "71 02 0201 30"  # Stopped

# Get results
send: "31 03 0201"
receive: "71 03 0201 30 [test data...]"  # Results
```

---

## Important Notes

- Routines may require extended diagnostic session (Service 0x10)
- Routines may require security access (Service 0x27)
- Some routines require specific vehicle conditions
- Always check if routine needs to be stopped manually
- Routine results format is manufacturer-specific

---

## Safety Warnings

⚠️ **CAUTION:** Routines can perform significant vehicle operations
- May affect vehicle operation and safety
- Some routines erase memory or reset learned values
- Always ensure safe conditions before running routines
- Never run routines while vehicle is in motion
- Some routines may take several minutes to complete

---

## References

- ISO 14229-1:2013(E) Section 13.2 (pages 260-269)
- Annex F.1: RoutineIdentifier definitions (page 375)
- Service 0x10: DiagnosticSessionControl (may be required)
- Service 0x27: SecurityAccess (may be required)
