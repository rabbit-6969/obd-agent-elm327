# AI Agent Steering Files

This directory contains steering files that guide the AI diagnostic agent's behavior. Steering files provide context-specific instructions that are automatically included based on the situation.

## What Are Steering Files?

Steering files are markdown documents with YAML front-matter that control when they're included in the agent's context. They provide:
- Manufacturer-specific guidance
- Safety protocols
- Troubleshooting procedures
- Communication guidelines
- Knowledge management practices

## Inclusion Types

### Auto-Inclusion (Always Active)

Files with `inclusion: auto` are always included in the agent's context.

**Current auto-included files**:
- `vehicle-diagnostics-core.md` - Core principles and workflows
- `safety-protocols.md` - Safety classification and confirmation procedures
- `communication-troubleshooting.md` - Systematic troubleshooting approach
- `knowledge-base-management.md` - How to maintain the knowledge base
- `user-interaction-guidelines.md` - Communication best practices

### File-Match Inclusion (Conditional)

Files with `inclusion: fileMatch` are included when specific files are in context.

**Current file-match files**:
- `toyota-specific-guidance.md` - Included when working with Toyota/Lexus/Scion vehicles
  - Pattern: `*Toyota*|*Lexus*|*Scion*`
- `ford-specific-guidance.md` - Included when working with Ford/Lincoln/Mercury/Mazda Tribute vehicles
  - Pattern: `*Ford*|*Lincoln*|*Mercury*|*Mazda*Tribute*`
- `nissan-infiniti-specific-guidance.md` - Included when working with Nissan/Infiniti/Datsun vehicles
  - Pattern: `*Nissan*|*Infiniti*|*Datsun*`
- `jeep-chrysler-specific-guidance.md` - Included when working with Jeep/Chrysler/Dodge/Ram/Fiat vehicles
  - Pattern: `*Jeep*|*Chrysler*|*Dodge*|*Ram*|*Fiat*`

### Manual Inclusion (On-Demand)

Files with `inclusion: manual` are only included when explicitly referenced by the user (e.g., via `#` context key in chat).

**Currently no manual-inclusion files** - all guidance is either always active or conditionally active.

## File Descriptions

### Core Instructions

**`vehicle-diagnostics-core.md`**
- Core principles (safety, learning, graceful degradation)
- Knowledge base structure and search hierarchy
- **ELM327 adapter limitations**: ATMA header bug and ATCRA workaround
- Module discovery protocol (CAN scanning, Tester Present, VIN reading)
- Manufacturer-specific behaviors overview
- Safety classifications
- Error handling strategy
- Toolkit scripts overview
- Web research protocol
- Continuous learning approach

### Manufacturer-Specific Guidance

**`toyota-specific-guidance.md`**
- Critical Toyota behaviors ("no response" is often normal)
- Response ID calculation (Request + 0x08)
- Protocol versions (UDS vs KWP2000)
- Common CAN addresses for documented models
- ABS module diagnostics (intermittent faults, extended session)
- DTC reading strategies
- Common Toyota DIDs
- Troubleshooting "no response"
- Platform sharing information
- Documentation references

**`ford-specific-guidance.md`**
- Ford-specific behaviors (always respond when healthy)
- Response ID calculation
- Common CAN addresses for documented models
- Extended diagnostic session requirements
- DTC reading methods
- Common Ford DIDs
- Transmission diagnostics
- HVAC diagnostics
- Module discovery approach
- FORScan compatibility
- Platform sharing information (Mazda Tribute, Mercury Mariner)

**`nissan-infiniti-specific-guidance.md`**
- Multi-protocol architecture (ISO-9141, ISO-14230, CAN, UART)
- Critical timing requirements for ISO-9141 (100ms inter-request delays)
- ISO-14230 Fast Init procedure
- Module addresses and Fast Init indicators (ABS clicking)
- Protocol selection strategy
- Common issues and solutions
- Platform sharing (350Z, G35, FX35)
- ELM327 configuration for each protocol

**`jeep-chrysler-specific-guidance.md`**
- Critical understanding: Most restrictive OBD-II implementation
- Proprietary protocol architecture (CCD/SCI bus)
- AlfaOBD requirement (essential, not optional)
- Module-specific behaviors (PCM, TCM, Airbag, BCM, IPC)
- VIN reading limitations (often unreliable)
- CAN bus monitoring challenges
- Extended diagnostic session and security access
- Standard OBD-II limitations (~20% access)
- Communication style (direct about limitations)
- Documentation standards
- Platform sharing (Jeep, Chrysler, Dodge, Ram, Fiat)

### Safety and Protocols

**`safety-protocols.md`**
- Four-level safety classification system:
  - SAFE: Read-only operations (no confirmation)
  - CAUTION: Data modification (simple confirmation)
  - WARNING: Component actuation (detailed confirmation)
  - DANGER: Critical systems (multi-step confirmation)
- Confirmation procedures for each level
- Operations that never execute without confirmation
- Logging requirements
- Error handling during operations
- Special cases (intermittent faults, module discovery, live monitoring)
- User override handling
- Post-operation documentation

**`communication-troubleshooting.md`**
- "No Response" diagnosis tree (8-step systematic approach)
- Manufacturer-specific troubleshooting
- Common error responses and their meanings
- Adapter-specific issues and workarounds
- **ELM327 ATMA header bug**: ATH1 returns OK but headers not included in ATMA output
- **ATCRA workaround**: Use targeted monitoring for affected adapters
- Logging and documentation during troubleshooting
- When to ask user for help
- Success criteria

### Knowledge Management

**`knowledge-base-management.md`**
- When to update knowledge base
- File types and their purposes:
  - Vehicle profiles (YAML)
  - Technical data (DAT)
  - CAN databases (KCD)
  - Captured data (JSON)
- Update workflow
- Documentation standards
- Maintenance and validation
- Platform sharing
- User contributions
- Learning loop progression
- Quality over quantity principle

### User Interaction

**`user-interaction-guidelines.md`**
- Communication style (clear, concise, progressive disclosure)
- Understanding user intent (common query patterns)
- Presenting results (DTCs, live data, module discovery)
- Error communication
- Progress updates for long operations
- Asking for confirmation (safety vs simple)
- Providing recommendations
- Documentation for user
- Tone and personality
- Handling frustration

## How to Use These Files

### For AI Agent

The agent automatically:
1. Loads all `auto` inclusion files at startup
2. Loads `fileMatch` files when relevant files are in context
3. Uses the guidance to inform decisions and responses
4. Follows protocols and procedures defined in steering files

### For Developers

When adding new guidance:

1. **Create new steering file**:
   ```markdown
   ---
   inclusion: auto|fileMatch|manual
   fileMatchPattern: "pattern" # if fileMatch
   ---
   
   # Title
   
   Content...
   ```

2. **Choose inclusion type**:
   - `auto`: Always needed (core principles, safety)
   - `fileMatch`: Context-specific (manufacturer guidance)
   - `manual`: Reference material (rarely used)

3. **Document in this README**

4. **Test with relevant scenarios**

### For Users

Users don't interact with steering files directly. They work behind the scenes to guide the agent's behavior. However, users can:
- Reference this README to understand agent behavior
- Suggest improvements to guidance
- Report when agent doesn't follow protocols

## Maintenance

### Regular Review

Periodically review steering files for:
- Accuracy (matches real-world behavior)
- Completeness (covers common scenarios)
- Clarity (easy for agent to understand)
- Consistency (no conflicting guidance)

### Updates

Update steering files when:
- New manufacturer behaviors discovered
- New safety protocols needed
- Troubleshooting procedures improved
- User interaction patterns change
- Knowledge base structure evolves

### Version Control

All steering files should be:
- Version controlled (Git)
- Reviewed before changes
- Tested after updates
- Documented in commit messages

## Design Principles

### 1. Specificity Over Generality

**Bad**: "Handle errors appropriately"
**Good**: "When module doesn't respond, try these 8 steps in order..."

### 2. Examples Over Descriptions

**Bad**: "Use proper formatting"
**Good**: "Format like this: `C1234 - Description`"

### 3. Context Over Rules

**Bad**: "Always confirm before clearing DTCs"
**Good**: "Clearing DTCs is CAUTION level - requires simple confirmation because it modifies stored data but doesn't affect vehicle operation"

### 4. Learning Over Rigidity

**Bad**: "Only use these exact commands"
**Good**: "Try these commands first, but document alternatives that work"

## Future Enhancements

Potential additions:
- Manufacturer-specific files for other brands (GM, Chrysler, Honda, etc.)
- System-specific guidance (transmission, HVAC, ABS, etc.)
- Advanced diagnostic procedures
- Repair procedure guidance
- Parts identification assistance
- Adapter compatibility matrix (which adapters work best for which tasks)

## Known Issues and Workarounds

### ELM327 ATMA Header Bug

**Issue**: Many cheap ELM327 clones don't include CAN IDs in ATMA (Monitor All) output despite ATH1 returning OK.

**Impact**: CAN bus exploration scripts capture data but can't parse CAN IDs.

**Detection**: Run `scripts/debug/diagnose_can_monitoring.py` to test your adapter.

**Workaround**: Use `scripts/debug/targeted_can_monitor.py` which uses ATCRA filtering.

**Documentation**: See `reference/ELM327_ATMA_Header_Bug.md` for full details.

**Recommendation**: For extensive CAN work, use quality adapters (Vgate iCar Pro, OBDLink).

## Contributing

When contributing steering files:
1. Follow existing format and style
2. Include specific, actionable guidance
3. Provide examples
4. Test with real scenarios
5. Document in this README
6. Update design document if needed

## Questions?

For questions about steering files:
- Check design document: `.kiro/specs/ai-vehicle-diagnostic-agent/design.md`
- Review existing steering files for examples
- Test with agent to see behavior
- Consult with project maintainers
