# Adventures in Automotive Networks and Control Units

**Authors**: 
- Chris Valasek, Director of Vehicle Security Research for IOActive (chris.valasek@ioactive.com)
- Charlie Miller, Security Researcher for Twitter (cmiller@openrce.org)

**Year**: 2014

**Source**: IOActive Research Paper

**Copyright**: ©2014 IOActive, Inc.

## Overview

This seminal research paper documents comprehensive security research on automotive CAN bus networks and Electronic Control Units (ECUs), with detailed analysis of the 2010 Ford Escape and Toyota Prius.

## Key Topics Covered

### Electronic Control Units (ECUs)
- ECU architecture and functionality
- Communication protocols between ECUs
- Security implications of ECU design

### CAN Bus Communication

**Normal CAN Packets**:
- Standard CAN message structure
- Message IDs and data formats
- Broadcast communication patterns

**Diagnostic Packets**:
- ISO-TP (ISO 15765-2) transport protocol
- ISO 14229 (UDS - Unified Diagnostic Services)
- ISO 14230 (KWP2000 - Keyword Protocol 2000)

### ISO 14229 Services Documented

1. **DiagnosticSessionControl (0x10)**: Switching between diagnostic modes
2. **SecurityAccess (0x27)**: Seed/key authentication for protected functions
3. **InputOutputControl (0x2F)**: Direct control of I/O signals
4. **InputOutputControlByLocalIdentifier**: Local I/O control
5. **RoutineControl (0x31)**: Executing diagnostic routines
6. **RequestDownload (0x34)**: Firmware download procedures

### Vehicle-Specific Research

#### 2010 Ford Escape
- Complete ECU mapping (Appendix A)
- CAN ID details (Appendix B)
- SecurityAccess implementation
- Firmware extraction from PAM (Parking Assist Module)
- HC12X assembly analysis
- Code execution via CAN bus
- Demonstrated attacks:
  - Speedometer manipulation
  - Odometer modification
  - Navigation system control
  - Steering control
  - Brake engagement/disengagement
  - Engine kill
  - Lighting control

#### Toyota Prius
- Techstream utility analysis
- SecurityAccess implementation
- ECM reprogramming procedures
- Calibration file analysis
- Demonstrated attacks:
  - Speedometer manipulation
  - Braking control
  - Acceleration control
  - Steering control
  - Engine kill
  - Lighting control
  - Horn control
  - Seat belt motor engagement
  - Door lock/unlock
  - Fuel gauge manipulation

### Tools and Techniques

**EcomCat**: CAN bus communication tool
- Output capabilities
- Input handling
- Continuous send functionality

**Ecomcat_api**: Python API for CAN communication
- Normal CAN packet injection
- Diagnostic packet handling

**PyEcom**: Python library for CAN bus interaction

### Attack Methodologies

**Via Normal CAN Packets**:
- Direct message injection
- Message spoofing
- Continuous message flooding

**Via Diagnostic Packets**:
- SecurityAccess bypass techniques
- Routine control exploitation
- Firmware modification
- Code execution

### Security Considerations

**Problems and Pitfalls**:
- Timing issues
- Message conflicts
- ECU state management
- Safety implications

**Attack Detection**:
- Anomaly detection methods
- Message validation
- Intrusion detection systems

## Relevance to This Project

### Ford Escape 2008 Applicability

The 2010 Ford Escape research directly applies to the 2008 model year:
- Same CD2 platform architecture
- Similar ECU configuration
- Compatible CAN bus structure
- Same diagnostic protocols (ISO 14229/UDS)

**Key Findings for Ford Escape 2008**:
- Module addresses documented in Appendix A
- CAN message IDs in Appendix B
- SecurityAccess seed/key algorithms
- Firmware structure and modification techniques
- Diagnostic service implementations

### Toyota Prius Research

Provides valuable insights for Toyota diagnostic procedures:
- SecurityAccess implementation patterns
- Techstream utility reverse engineering
- Calibration file formats
- Reprogramming procedures

### General Automotive Security

**Universal Lessons**:
- ISO-TP multi-frame handling
- UDS service implementation patterns
- SecurityAccess common approaches
- Firmware extraction techniques
- Attack surface analysis

## Application to Diagnostic Work

### Safe Diagnostic Practices

**What to Learn**:
- Proper ISO-TP implementation
- UDS service usage patterns
- SecurityAccess understanding (for read-only analysis)
- ECU communication protocols

**What to Avoid**:
- Unauthorized firmware modification
- Safety-critical system manipulation
- SecurityAccess bypass attempts
- Malicious code injection

### Legitimate Diagnostic Uses

**Read-Only Operations**:
- Understanding ECU architecture
- Mapping diagnostic services
- Identifying available DIDs
- Analyzing CAN message structures

**Authorized Modifications**:
- Manufacturer-approved reprogramming
- Calibration updates with proper tools
- DTC clearing (with user consent)
- Routine control (with safety checks)

## Key Takeaways for This Project

### Ford Escape 2008 Diagnostics

1. **ECU Mapping**: Use Appendix A as reference for module discovery
2. **CAN IDs**: Reference Appendix B for message identification
3. **UDS Services**: Understand which services are available per module
4. **SecurityAccess**: Document that certain functions require authentication
5. **Safety**: Never attempt unauthorized control of safety-critical systems

### Toyota Diagnostics

1. **Techstream Compatibility**: Understand Toyota's diagnostic approach
2. **SecurityAccess**: Document Toyota's seed/key implementation
3. **Calibration Files**: Reference format for understanding ECM data
4. **Service Patterns**: Learn Toyota-specific UDS implementations

### General Best Practices

1. **Read-Only Focus**: Prioritize diagnostic reading over modification
2. **Safety First**: Never manipulate brakes, steering, or engine without explicit user consent
3. **Documentation**: Use research to understand protocols, not replicate attacks
4. **Transparency**: Always inform users of capabilities and limitations

## References in This Project

This research paper informs:
- `knowledge_base/Ford_Escape_2008_profile.yaml` - ECU addresses
- `FORD_ESCAPE_COMPLETE_DID_GUIDE.md` - UDS service documentation
- `.kiro/steering/ford-specific-guidance.md` - Ford diagnostic procedures
- `.kiro/steering/toyota-specific-guidance.md` - Toyota diagnostic procedures
- `.kiro/steering/safety-protocols.md` - Safety classifications

## Ethical Considerations

**This research is referenced for**:
- Understanding automotive protocols
- Improving diagnostic capabilities
- Documenting legitimate service procedures
- Enhancing vehicle maintenance tools

**This research is NOT used for**:
- Unauthorized vehicle modification
- Safety system manipulation
- Security bypass
- Malicious activities

## Citation

Valasek, C., & Miller, C. (2014). *Adventures in Automotive Networks and Control Units*. IOActive, Inc.

## Additional Resources

**Related IOActive Research**:
- Remote exploitation of automotive systems
- Wireless attack surfaces
- Infotainment system security

**Industry Response**:
- Automotive cybersecurity standards
- Secure gateway implementations
- Intrusion detection systems

## Appendices Referenced

### Appendix A: Diagnostic ECU Map

**2010 Ford Escape Module Mapping** (from Valasek & Miller research):

| Module | Address | Bus | ISO 14230 | Running Diag Session | Running Security | Prog Mode Diag Session | Prog Mode Security | Got Key | Programmable (Ford) |
|--------|---------|-----|-----------|---------------------|------------------|----------------------|-------------------|---------|-------------------|
| **PAM** (Parking Assist) | 0x736 | HS | No | Yes | NR | Yes | Yes | Yes | Yes |
| **PCM** (Powertrain) | 0x7E0 | HS | No | No | No | Yes | Yes | Yes | Yes |
| **PSCM** (Power Steering) | 0x730 | HS | Yes | Yes | Yes | Yes | Yes | No :( | Yes |
| **ABS** (Anti-lock Brakes) | 0x760 | HS | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **APIM** (Accessory Protocol Interface) | 0x7D0 | HS | No | Yes | NR | Yes | NR | NR | Yes |
| **RCM** (Restraint Control) | 0x737 | HS | No | Yes | Yes/NR | Yes | Yes/NR | Yes | Yes |
| **OCSM** (Occupant Classification) | 0x765 | HS | No | No | Yes | No | Yes | Yes | No |
| **IC** (Instrument Cluster) | 0x720 | MS | Yes | No | No | No | No | Yes | Yes |
| **SJB** (Smart Junction Box) | 0x726 | MS | No | NR | NR | NR | NR | Yes | Yes |
| **FDIM** (Front Display Interface) | 0x7A6 | MS | Yes | NR | NR | NR | NR | Yes | Yes |
| **ACM** (Audio Control) | 0x727 | MS | Yes | NR | NR | NR | NR | Yes | Yes |
| **GPSM** (GPS Module) | 0x701 | MS | No | NR | NR | NR | NR | NR | No |
| **HVAC** (Climate Control) | 0x733 | MS | Yes | NR | NR | NR | NR | Yes | No |
| **4x4** (Transfer Case) | 0x761 | ? | NR | NR | NR | NR | NR | NR | No |
| **FCIM** (Front Controls Interface) | 0x7A7 | ? | NR | NR | NR | NR | NR | NR | No |

**Legend**:
- **HS**: High-Speed CAN (500 kbps)
- **MS**: Medium-Speed CAN (125 kbps)
- **NR**: No Response / Not Recorded
- **Yes/NR**: Inconsistent response
- **No :(**: Failed to obtain key despite trying

**Key Findings**:
- Most HS-CAN modules support diagnostic sessions and SecurityAccess
- MS-CAN modules have limited diagnostic capabilities
- PCM (0x7E0) is programmable but doesn't support ISO 14230
- ABS (0x760) has full diagnostic support including SecurityAccess
- PSCM (0x730) supports diagnostics but SecurityAccess key was not obtained
- HVAC (0x733) on MS-CAN has limited diagnostic support

**Applicability to 2008 Ford Escape**:
- Module addresses are likely identical or very similar
- Same CD2 platform architecture
- Diagnostic capabilities should be comparable
- Use this as reference for module discovery

### Appendix B: CAN ID Details
- Comprehensive CAN message ID documentation
- Message purposes and data formats
- Transmission frequencies and priorities

**Note**: Full Appendix B details are documented in `reference/Mazda_CAN_Bus_Reference.md` for the Ford CD2 platform.

## Disclaimer

This reference is provided for educational and legitimate diagnostic purposes only. The techniques described in the original research paper should only be applied to vehicles you own or have explicit authorization to diagnose. Always prioritize safety and follow applicable laws and regulations.

**Safety Warning**: Never attempt to control safety-critical vehicle systems (brakes, steering, engine, airbags) without proper training, authorization, and safety precautions. Improper manipulation of these systems can result in serious injury or death.
