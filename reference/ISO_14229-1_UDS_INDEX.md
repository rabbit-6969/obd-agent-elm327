# ISO 14229-1:2013(E) UDS Protocol - Knowledge Base Index

**Source:** ISO 14229-1:2013(E) - Unified Diagnostic Services (UDS)  
**Purpose:** Index of available UDS service documentation for Ford vehicle diagnostics

---

## Available Documentation

### ✅ Service 0x10: DiagnosticSessionControl
- **File:** `ISO_14229-1_UDS_Service_0x10_DiagnosticSessionControl.md`
- **Status:** Complete
- **Use Cases:** Enter extended diagnostic session to access additional DIDs and services
- **Sessions:** defaultSession (0x01), extendedDiagnosticSession (0x03), programmingSession (0x02)
- **Critical for:** Accessing hidden transmission DIDs, enabling actuation services

### ✅ Service 0x19: ReadDTCInformation
- **File:** `ISO_14229-1_UDS_Service_0x19_Extract.md`
- **Status:** Complete
- **Use Cases:** Reading diagnostic trouble codes from any module (HVAC, PCM, TCM, ABS, etc.)
- **Sub-functions:** 0x02 (reportDTCByStatusMask) documented

### ✅ Service 0x22: ReadDataByIdentifier
- **File:** `ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md`
- **Status:** Complete
- **Use Cases:** Read live data parameters by Data Identifier (DID)
- **Key Points:** 
  - DIDs are 2-byte identifiers (manufacturer-specific)
  - Can request multiple DIDs in one message
  - Data format is completely manufacturer-defined
  - Ford uses 0x0100-0x01FF range for transmission parameters

---

## Needed Documentation (Request from user when required)

### 🔲 Service 0x2F: InputOutputControlByIdentifier
- **Section:** 12.2 (pages 245-258)
- **Annex:** E.1 (page 374) - InputOutputControlParameter definitions
- **Purpose:** Direct control of outputs (solenoids, relays, actuators)
- **Use Cases:**
  - Actuate shift solenoids
  - Control HVAC blend doors
  - Test relays and outputs
- **Request when:** User wants to actuate or control vehicle components

### 🔲 Service 0x31: RoutineControl
- **Section:** 13.2 (pages 260-269)
- **Annex:** F.1 (page 375) - RoutineIdentifier definitions
- **Purpose:** Execute pre-programmed test routines
- **Use Cases:**
  - Run transmission self-test
  - Execute ABS bleeding routine
  - Perform EVAP purge test
- **Request when:** User wants to run built-in diagnostic routines

### 🔲 Service 0x14: ClearDiagnosticInformation
- **Section:** 11.2 (pages 175-177)
- **Purpose:** Clear stored DTCs from module memory
- **Use Cases:** Clear codes after repairs
- **Request when:** User wants to clear diagnostic codes

### 🔲 Service 0x2E: WriteDataByIdentifier
- **Section:** 10.7 (pages 162-166)
- **Purpose:** Write configuration data to module
- **Use Cases:** 
  - Configure module settings
  - Calibrate sensors
  - Update configuration parameters
- **Request when:** User wants to modify module configuration

### 🔲 Service 0x27: SecurityAccess
- **Section:** 9.4 (pages 47-52)
- **Annex:** I (pages 379-383) - Security access state chart
- **Purpose:** Unlock protected functions with seed/key authentication
- **Use Cases:** Required for programming, some actuations, protected data access
- **Request when:** Module returns "securityAccessDenied" error

### 🔲 Service 0x3E: TesterPresent
- **Section:** 9.6 (pages 58-60)
- **Purpose:** Keep diagnostic session active
- **Use Cases:** Prevent timeout during long operations
- **Request when:** Implementing extended diagnostic sessions

### 🔲 Service 0x11: ECUReset
- **Section:** 9.3 (pages 43-46)
- **Purpose:** Reset/reboot ECU module
- **Use Cases:** Apply configuration changes, recover from errors
- **Request when:** User needs to reset a module

---

## Supporting Documentation Needed

### 🔲 Annex A: Negative Response Codes
- **Section:** Annex A (pages 325-332)
- **Purpose:** Complete list of error codes and their meanings
- **Request when:** Need to interpret error responses

### 🔲 Annex D: DTC Status and Format Definitions
- **Section:** Annex D (pages 353-372)
- **Purpose:** DTC status bits, severity, format identifiers
- **Partial:** D.2 (status bits) already documented in Service 0x19 extract
- **Request when:** Need complete DTC format specifications

### 🔲 Annex C: Data Identifier Definitions
- **Section:** Annex C (pages 337-352)
- **Purpose:** Standard DID ranges and definitions
- **Request when:** Working with Service 0x22 or 0x2E

---

## Usage Instructions

When implementing a new UDS feature:

1. Check this index to see if documentation exists
2. If marked ✅, read the existing file
3. If marked 🔲, request the specific section from the user
4. After receiving content, create new file: `ISO_14229-1_UDS_Service_0x[XX]_[Name].md`
5. Update this index to mark as ✅ and add file reference

---

## Request Template

When requesting documentation from user:

```
To implement [feature], I need the ISO 14229-1 documentation for:

Service 0x[XX]: [ServiceName]
Section: [section number]
Pages: [page range]

This will allow me to implement [specific capability] for your [vehicle/module].

Please paste the content from that section.
```

---

## Current Implementation Status

- ✅ Read DTCs (Service 0x19)
- ✅ Enter diagnostic sessions (Service 0x10)
- ✅ Read live parameters (Service 0x22)
- ⏳ Actuate components (Service 0x2F or 0x31) - **Need documentation**
- ⏳ Clear DTCs (Service 0x14) - **Need documentation**

---

## Notes

- All UDS services use request/response pattern
- Positive response = Request SID + 0x40 (e.g., 0x22 → 0x62)
- Negative response = 0x7F [SID] [NRC]
- Multi-frame responses use ISO-TP flow control
- Some services require extended diagnostic session (0x10 03)
- Some services require security access (0x27)

