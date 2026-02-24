# 2008 Ford Escape 2.3L - PCM Architecture and UDS Implementation

## Critical Architecture Facts

### PCM-Integrated Transmission Control
- **NO separate TCM** - transmission is controlled by the PCM
- CD4E transmission control logic is embedded in PCM firmware
- All transmission DIDs are accessed via PCM (CAN ID 0x7E0/0x7E8)

### UDS-Style Protocol Support
- Ford's proprietary "UDS-like" implementation (pre-ISO 14229 standardization)
- Supports key UDS services:
  - `0x22` ReadDataByIdentifier
  - `0x2E` WriteDataByIdentifier (limited)
  - `0x27` SecurityAccess
  - `0x10` DiagnosticSessionControl
- Uses ISO-TP over CAN (11-bit identifiers)
- Response times: 5-30ms typical

## CAN Addressing

### PCM Communication
- **Request ID**: `0x7E0` (not 0x7E1 for TCM!)
- **Response ID**: `0x7E8` (not 0x7E9 for TCM!)
- **Bus**: HS-CAN (500 Kbps)
- **Protocol**: ISO 15765-4 (ISO-TP)

## Ford DID Ranges (2008 Escape PCM)

### Public DIDs (No Security Required)
| Range | Purpose | Examples |
|-------|---------|----------|
| 0x0000-0x00FF | Basic info, VIN, calibration | VIN, part numbers |
| 0x1000-0x1FFF | Engine data | RPM, load, timing |
| 0x2000-0x2FFF | Transmission data (CD4E) | ATF temp, gear, speeds |
| 0xF000-0xF3FF | Engineering data | Diagnostic counters |

### Security-Locked DIDs
| Range | Purpose | Security Level |
|-------|---------|----------------|
| 0xF400-0xF7FF | Calibration blocks | Level 1 |
| 0xF800-0xFFFF | Protected data | Level 1 |
| Solenoid states | EPC, SS1, SS2, SS3, TCC | Level 1 |
| Line pressure | Actual/commanded | Level 1 |
| Adaptation tables | Shift points, pressures | Level 1 |

## Known Transmission DIDs

### Confirmed Working (Public Access)
| DID | Parameter | Data Format | Notes |
|-----|-----------|-------------|-------|
| 0x221E1C | ATF Temperature | 2 bytes, signed | °C, offset varies |
| 0x221E10 | ATF Temperature (alt) | 2 bytes, signed | Alternative address |
| 0x221E14 | Turbine Speed | 2 bytes, unsigned | RPM |
| 0x221E16 | Output Shaft Speed | 2 bytes, unsigned | RPM |

### Likely Available (Needs Discovery)
| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| Current Gear | 0x2000-0x20FF | 1 byte: 0=P, 1=R, 2=N, 3=D, 4=2, 5=1 |
| Shift in Progress | 0x2000-0x20FF | Boolean flag |
| TCC Status | 0x2000-0x20FF | Locked/unlocked/slipping |
| Transmission Range | 0x2000-0x20FF | PRNDL position |

### Security-Locked (Requires 0x27)
| Parameter | Typical Range | Notes |
|-----------|---------------|-------|
| EPC Duty Cycle | 0x2000-0x2FFF | 0-100% |
| Shift Solenoid A State | 0x2000-0x2FFF | ON/OFF |
| Shift Solenoid B State | 0x2000-0x2FFF | ON/OFF |
| Shift Solenoid C State | 0x2000-0x2FFF | ON/OFF |
| TCC Duty Cycle | 0x2000-0x2FFF | 0-100% |
| Line Pressure Commanded | 0x2000-0x2FFF | PSI or kPa |
| Line Pressure Actual | 0x2000-0x2FFF | PSI or kPa |

## CD4E Transmission Solenoids

### Solenoid Functions
1. **SS1** (Shift Solenoid 1): Controls 1-2 and 3-4 shifts
2. **SS2** (Shift Solenoid 2): Controls 2-3 shifts
3. **SS3** (Shift Solenoid 3): Controls torque converter lockup
4. **EPC** (Electronic Pressure Control): Line pressure control (PWM)

### Gear Logic Table
| Gear | SS1 | SS2 | SS3 | EPC |
|------|-----|-----|-----|-----|
| P/N | OFF | OFF | OFF | Low |
| 1st | ON | OFF | OFF | High |
| 2nd | OFF | OFF | OFF | Med |
| 3rd | OFF | ON | OFF | Med |
| 4th | OFF | ON | ON | Low |
| Rev | ON | ON | OFF | High |

## Security Access (0x27)

### Seed/Key Algorithm
Ford uses proprietary security algorithms:
1. **Request Seed**: `27 01`
2. **PCM Returns Seed**: `67 01 [4 bytes seed]`
3. **Compute Key**: Proprietary algorithm (not published)
4. **Send Key**: `27 02 [4 bytes key]`
5. **Access Granted**: `67 02` (or denied: `7F 27 35`)

### Security Levels
- **Level 1**: Basic protected data (solenoids, pressures)
- **Level 2**: Calibration write access
- **Level 3**: Programming mode

### Known Security Algorithms
- Ford uses different algorithms per model year and PCM strategy
- 2008 Escape likely uses "Ford Algorithm 1" or "Ford Algorithm 2"
- FORScan has reverse-engineered these algorithms
- Community tools exist but are not publicly documented

## Response Timing

### Typical Response Times
| Operation | Time (ms) | Notes |
|-----------|-----------|-------|
| Simple 0x22 DID read | 5-15 | Single frame |
| Multi-frame response | 15-30 | ISO-TP segmentation |
| Busy PCM (engine running) | 15-30 | Higher bus load |
| Negative response | 5-10 | Quick rejection |
| SecurityAccess seed | 10-20 | Seed generation |
| SecurityAccess key | 10-20 | Key validation |

### Rate Limiting
- PCM can handle ~40-60 requests/second
- Exceeding this triggers `0x78` (Response Pending)
- Add 50-100ms delay between requests for stability

## DID Discovery Strategy

### Brute Force Approach
1. **Scan Priority Ranges First**:
   - 0x2000-0x2FFF (transmission data)
   - 0x1000-0x1FFF (engine data)
   - 0xF000-0xF3FF (engineering data)

2. **Full Scan** (if needed):
   - 0x0000-0xFFFF (all possible DIDs)
   - ~65,000 requests at 50ms each = ~55 minutes
   - Can be optimized with parallel requests

3. **Response Analysis**:
   - `0x62` = Positive response (DID exists)
   - `0x7F 22 31` = Request out of range (DID doesn't exist)
   - `0x7F 22 33` = Security access denied (DID exists but locked)

### Multi-Frame Detection
- Responses >7 bytes use ISO-TP multi-frame
- First frame: `10 [length] [data...]`
- Flow control: `30 00 00` (continue sending)
- Consecutive frames: `2X [data...]`

## Tools and Interfaces

### Compatible Adapters
Your ELM327 v1.5 with HS-CAN switch works, but has limitations:
- ✓ Can read public DIDs
- ✓ Can enter extended session
- ✗ Too slow for brute-force scanning
- ✗ No native ISO-TP multi-frame support
- ✗ Cannot do SecurityAccess (no seed/key algorithm)

### Recommended for Full Access
- **CANtact** / **ValueCAN**: Native CAN interface
- **Python + python-can + isotp**: Full control
- **FORScan**: Has security algorithms built-in

## Implementation Notes

### Adapter Switch Position
- **HS-CAN**: For PCM communication (transmission included)
- **MS-CAN**: For BCM, HVAC, body modules

### Session Management
- Extended session timeout: ~5 seconds
- Send TesterPresent (`0x3E 0x00`) every 2-3 seconds
- Re-enter session if timeout occurs

### Safety Considerations
- Read-only operations are safe
- Write operations require security access
- Never write to unknown DIDs
- Keep vehicle stationary during diagnostics
- Maintain adequate battery voltage

## References
- ISO 15765-4 (ISO-TP over CAN)
- Ford workshop manuals (2008 Escape)
- FORScan community documentation
- Reverse-engineered DID databases
