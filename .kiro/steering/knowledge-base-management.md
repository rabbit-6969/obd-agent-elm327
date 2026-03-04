---
inclusion: auto
---

# Knowledge Base Management

Your knowledge base is your memory. Maintain it carefully to become smarter over time.

## When to Update Knowledge Base

Update after:
1. **Successful diagnostic procedure** - Document what worked
2. **Module discovery** - Add new module to vehicle profile
3. **New DID discovered** - Add to vehicle profile with description
4. **Manufacturer behavior learned** - Document in vehicle profile
5. **Troubleshooting success** - Document the solution
6. **User provides information** - Add to appropriate file

## File Types and Purposes

### Vehicle Profiles (YAML)

**Location**: `knowledge_base/[Manufacturer]_[Model]_[Year]_profile.yaml`

**Contains**:
- Vehicle specifications
- Module addresses (CAN IDs)
- DTC descriptions
- Common issues
- Repair hints
- Known behaviors
- Official documentation links

**Update when**:
- Discover new module
- Learn new DTC meaning
- Find common issue
- User provides repair manual link

**Example**:
```yaml
vehicle:
  make: Toyota
  model: FJ Cruiser
  year: 2008

modules:
  abs:
    can_id_request: 0x7B0
    can_id_response: 0x7B8
    notes: "May not respond when no DTCs present (normal behavior)"

dtc_descriptions:
  C1234:
    description: "Wheel Speed Sensor Circuit Malfunction"
    common_causes:
      - "Sensor connector corrosion"
      - "Damaged wiring"
      - "Failed sensor"
```

### Technical Data (DAT)

**Location**: `knowledge_base/[Manufacturer]_[Model]_[Year]_technical.dat`

**Contains**:
- Ultra-compact command sequences
- Response patterns
- Module addresses
- Protocol details

**Format**: Machine-optimized, not human-readable

**Update when**:
- Document successful command sequence
- Add new module address
- Record response pattern

**Example**:
```
M:ABS A:7B0 P:CAN B:HS
C:ABS.READ_DTC M:19 02 FF R:59 02[0-9A-F]{4,}
C:ABS.TESTER_PRESENT M:3E 00 R:7E
```

### CAN Databases (KCD)

**Location**: `knowledge_base/[Manufacturer]_[Model]_[Year]_canbus.kcd`

**Contains**:
- Signal definitions
- Message IDs
- Bit mappings
- Scaling factors

**Update when**:
- User provides CAN database
- Discover new signals through OBDB or other sources
- Document live data parameters

### Captured Data (JSON)

**Location**: `knowledge_base/captured_data/[description]_[timestamp].json`

**Contains**:
- Real diagnostic session logs
- Commands sent and responses received
- Timestamps
- Context information

**Update when**:
- Complete diagnostic session
- Capture interesting data
- Document successful procedure

**Example**:
```json
{
  "vehicle": "Ford_Escape_2008",
  "module": "ABS",
  "timestamp": "2026-02-21T17:18:54",
  "commands": [
    {
      "request": "19 02 FF",
      "response": "59 02 C1 23 4 C5 67 8",
      "dtcs": ["C1234", "C5678"]
    }
  ]
}
```

## Update Workflow

### 1. Identify What to Document

After successful operation, ask yourself:
- Was this a new procedure?
- Did I learn something new about this vehicle?
- Did I discover a new module or DID?
- Did I find a workaround for a problem?

### 2. Choose Appropriate File

- **New vehicle**: Create new profile
- **New module on existing vehicle**: Update profile
- **New command sequence**: Update technical data
- **Session log**: Create captured data file
- **CAN signals**: Update or create KCD file

### 3. Update File

Use appropriate toolkit script:
- `toolkit/knowledge_management/append_procedure.py`
- `toolkit/knowledge_management/profile_handler.py`
- Or directly edit YAML files (they're human-readable)

### 4. Verify Update

After updating:
- Verify file is valid (YAML syntax, etc.)
- Test that information can be retrieved
- Confirm it will help in future sessions

## Documentation Standards

### Be Specific

**Bad**: "Module doesn't respond sometimes"
**Good**: "ABS module at 0x7B0 doesn't respond to Service 0x19 when no DTCs present (normal Toyota behavior)"

### Include Context

**Bad**: "Use 3E 00"
**Good**: "Use Tester Present 3E 00 (not 3E 01) for this module"

### Document Workarounds

When you find a workaround, document:
1. What the problem was
2. What the workaround is
3. Why it works
4. When to use it

**Example**:
```yaml
known_issues:
  - issue: "ABS module no response to Service 0x19"
    workaround: "Try Service 0x19 0x01 (DTC count) first"
    reason: "Module responds to count request more reliably"
    when: "When ABS light is ON but Service 0x19 0x02 times out"
```

### Link Related Information

When documenting, link to:
- Official repair manuals
- Related vehicles (platform sharing)
- Reference documentation
- Similar issues on other modules

## Maintenance

### Regular Cleanup

Periodically review knowledge base:
- Remove duplicate information
- Consolidate related entries
- Update outdated information
- Improve documentation clarity

### Validation

Verify information is:
- Accurate (matches real vehicle behavior)
- Complete (includes all necessary details)
- Accessible (easy to find and understand)
- Useful (helps with diagnostics)

## Platform Sharing

When you learn something about one vehicle, check for related vehicles:

**Toyota**:
- FJ Cruiser = 4Runner (same platform)
- Lexus GX470 = 4Runner (luxury version)
- Scion FR-S = Toyota 86 = Subaru BRZ

**Ford**:
- Escape = Mazda Tribute = Mercury Mariner
- Focus = Mazda 3 (some years)

**Action**: Document findings for all related vehicles.

## User Contributions

When user provides information:
1. **Thank them**
2. **Verify information if possible**
3. **Document in appropriate file**
4. **Confirm documentation with user**

**Example**:
```
User: "The repair manual says the ABS module is at 0x750"
Agent: "Thank you! I'll update the vehicle profile with this information.
        I've documented that the ABS module uses 0x750/0x758 for this model.
        This will help with future diagnostics."
```

## Learning Loop

The knowledge base enables continuous learning:

**First time**: 
- Ask user for help
- Research online
- Try different approaches
- Takes 2-5 minutes

**Second time**:
- Look up in knowledge base
- Execute documented procedure
- Takes 10 seconds

**Third time**:
- Cached in memory
- Instant execution
- Takes 1 second

Your goal is to move every procedure from "first time" to "third time" as quickly as possible.

## Quality Over Quantity

Better to have:
- 10 well-documented vehicles
- With complete, accurate information
- That works reliably

Than:
- 100 partially documented vehicles
- With incomplete or inaccurate information
- That requires troubleshooting every time

Focus on quality documentation that actually helps.

## Backup and Version Control

Knowledge base should be:
- Version controlled (Git)
- Backed up regularly
- Shareable across installations
- Portable

This allows:
- Rollback if mistakes made
- Sharing knowledge with other users
- Collaborative improvement
- Recovery from data loss
