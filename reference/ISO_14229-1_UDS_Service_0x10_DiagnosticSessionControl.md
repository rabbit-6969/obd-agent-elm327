# ISO 14229-1 UDS Service 0x10: DiagnosticSessionControl

**Source:** ISO 14229-1:2013(E) Section 9.2 (pages 36-42)  
**Service ID:** 0x10  
**Response ID:** 0x50 (0x10 + 0x40)

---

## Service Description

The DiagnosticSessionControl service is used to enable different diagnostic sessions in the server(s). A diagnostic session enables a specific set of diagnostic services and/or functionality in the server(s).

### Key Concepts

- There shall always be exactly one diagnostic session active in a server
- A server shall always start the **default diagnostic session** when powered up
- The set of diagnostic services in a non-default session is a **superset** of the functionality provided in the defaultSession
- Non-default sessions require **TesterPresent (0x3E)** to keep them active (timeout handling)

---

## Diagnostic Session Types

### Standard Sessions

| Session Type | Sub-function | Mnemonic | Description |
|--------------|--------------|----------|-------------|
| **defaultSession** | 0x01 | DS | Default diagnostic session (no timeout, basic functionality) |
| **programmingSession** | 0x02 | PRGS | Memory programming session (requires ECU reset to exit) |
| **extendedDiagnosticSession** | 0x03 | EXTDS | Extended diagnostics (adjustments, additional services) |
| **safetySystemDiagnosticSession** | 0x04 | SSDS | Safety system diagnostics (e.g., airbag) |

### Custom Sessions

| Range | Purpose |
|-------|---------|
| 0x40 - 0x5F | Vehicle manufacturer specific |
| 0x60 - 0x7E | System supplier specific |

---

## Request Message Format

```
10 [diagnosticSessionType]
```

### Example: Enter Extended Diagnostic Session

```
Request:  10 03
Response: 50 03 [P2_high] [P2_low] [P2*_high] [P2*_low]
```

**Request breakdown:**
- `10` = Service ID (DiagnosticSessionControl)
- `03` = Sub-function (extendedDiagnosticSession)

---

## Positive Response Message Format

```
50 [diagnosticSessionType] [P2Server_max_high] [P2Server_max_low] [P2*Server_max_high] [P2*Server_max_low]
```

### Response Parameters

| Parameter | Bytes | Description | Resolution | Range |
|-----------|-------|-------------|------------|-------|
| diagnosticSessionType | 1 | Echo of requested session type | - | 0x01-0xFF |
| P2Server_max | 2 | Default timeout for server response | 1 ms | 0-65,535 ms |
| P2*Server_max | 2 | Enhanced timeout (when NRC 0x78 sent) | 10 ms | 0-655,350 ms |

### Example Response

```
Response: 50 03 00 32 01 F4
```

**Response breakdown:**
- `50` = Positive response (0x10 + 0x40)
- `03` = extendedDiagnosticSession
- `00 32` = P2Server_max = 0x0032 = 50 ms
- `01 F4` = P2*Server_max = 0x01F4 = 500 (× 10 ms) = 5,000 ms

---

## Services Allowed by Session Type

### Default Session (0x01)
- DiagnosticSessionControl (0x10) ✓
- ECUReset (0x11) ✓
- TesterPresent (0x3E) ✓
- ReadDataByIdentifier (0x22) ✓ (unsecured DIDs only)
- ClearDiagnosticInformation (0x14) ✓
- ReadDTCInformation (0x19) ✓
- ResponseOnEvent (0x86) ✓ (implementation specific)

### Non-Default Sessions (0x02, 0x03, 0x04, etc.)
All services from default session PLUS:
- SecurityAccess (0x27) ✓
- CommunicationControl (0x28) ✓
- AccessTimingParameter (0x83) ✓
- SecuredDataTransmission (0x84) ✓
- ControlDTCSetting (0x85) ✓
- LinkControl (0x87) ✓
- ReadMemoryByAddress (0x23) ✓
- ReadDataByPeriodicIdentifier (0x2A) ✓
- DynamicallyDefineDataIdentifier (0x2C) ✓
- WriteDataByIdentifier (0x2E) ✓ (secured DIDs)
- WriteMemoryByAddress (0x3D) ✓
- **InputOutputControlByIdentifier (0x2F)** ✓ (REQUIRED FOR ACTUATION)
- **RoutineControl (0x31)** ✓ (REQUIRED FOR TEST ROUTINES)
- RequestDownload (0x34) ✓
- RequestUpload (0x35) ✓
- TransferData (0x36) ✓
- RequestTransferExit (0x37) ✓
- RequestFileTransfer (0x38) ✓

---

## Session Transition Behavior

### Transition Rules

1. **defaultSession → defaultSession**: Re-initialize completely, reset all settings
2. **defaultSession → other session**: Stop ResponseOnEvent events only
3. **other session → other session**: Stop events, re-lock security, maintain other active functions
4. **other session → defaultSession**: Stop all events, re-lock security, terminate non-default functionality

### Important Notes

- When transitioning to a new session, the positive response is sent BEFORE the new timing parameters become active
- If the server cannot start the requested session, it sends a negative response and continues the current session
- Non-default sessions require **TesterPresent (0x3E)** messages to prevent timeout

---

## Negative Response Codes

| NRC | Mnemonic | Description |
|-----|----------|-------------|
| 0x12 | SFNS | sub-functionNotSupported - Session type not supported |
| 0x13 | IMLOIF | incorrectMessageLengthOrInvalidFormat - Wrong message length |
| 0x22 | CNC | conditionsNotCorrect - Criteria not met (e.g., vehicle moving) |

---

## Usage for Transmission Diagnostics

### To Access Additional Transmission DIDs

1. **Enter Extended Diagnostic Session:**
   ```
   Send: 10 03
   Expect: 50 03 [timing parameters]
   ```

2. **Scan for DIDs again:**
   - Many manufacturers hide advanced DIDs behind extended session
   - Gear position, solenoid states, shaft speeds likely require this

3. **Keep session alive:**
   - Send TesterPresent (0x3E) every 2-3 seconds
   - Format: `3E 00` or `3E 80` (suppress response)

4. **Access actuation services:**
   - InputOutputControlByIdentifier (0x2F) - control solenoids
   - RoutineControl (0x31) - run test routines

### Example Workflow

```
1. Send: 10 03              (enter extended session)
2. Receive: 50 03 ...       (session active)
3. Send: 22 0102            (try gear position DID)
4. Receive: 62 01 02 XX     (success! gear position data)
5. Send: 3E 00              (keep session alive)
6. Receive: 7E 00           (session still active)
7. Send: 2F 0103 03 01      (actuate solenoid A)
8. Receive: 6F 0103 03      (solenoid actuated)
```

---

## Implementation Notes

- **extendedDiagnosticSession (0x03)** is the most common for diagnostics and adjustments
- **programmingSession (0x02)** is for ECU reprogramming (use with caution!)
- Some sessions may require specific conditions (vehicle stationary, engine off, etc.)
- Ford may use manufacturer-specific sessions (0x40-0x5F range)
- Always return to defaultSession when done: `10 01`

---

## References

- ISO 14229-1:2013(E) Section 9.2 (pages 36-42)
- ISO 14229-2 for data link layer timing details
- Table 23: Services allowed during default and non-default diagnostic session
- Figure 7: Server diagnostic session state diagram
