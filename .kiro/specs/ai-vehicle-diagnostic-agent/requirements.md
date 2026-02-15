# Requirements Document

## Introduction

The AI Vehicle Diagnostic Agent system provides a toolkit of Python scripts that enable an AI agent to autonomously interact with vehicles through OBD2 ports. The toolkit includes scripts for vehicle communication (via ELM327), web research for diagnostic procedures, knowledge documentation, and diagnostic execution. The AI agent uses these tools in a closed-loop feedback system: it executes diagnostics, documents findings, and uses that documentation to improve future diagnostic sessions. The system is initially focused on 2008 Ford Escape and similar-era Ford vehicles as Phase 1, but designed to be flexible and extensible to any vehicle manufacturer and model through the same toolkit approach.

## Glossary

- **Agent**: The AI system that uses the toolkit scripts to perform diagnostics
- **Toolkit**: Collection of Python scripts that the Agent can execute to interact with vehicles and perform research
- **Tool_Script**: Individual Python script in the toolkit that performs a specific function (e.g., read_dtc.py, search_procedure.py)
- **OBD2**: On-Board Diagnostics II, standardized vehicle diagnostic protocol
- **ELM327**: OBD2 adapter hardware for vehicle communication
- **DTC**: Diagnostic Trouble Code, standardized error codes from vehicle modules
- **CAN_Bus**: Controller Area Network, vehicle internal communication network
- **Module**: Electronic control unit in the vehicle (e.g., HVAC, ABS, transmission, PCM)
- **Knowledge_Document**: Persistent markdown file storing learned diagnostic procedures for specific vehicle/module combinations
- **Natural_Language_Query**: User input in conversational language (e.g., "check DTC in HVAC of my vehicle")
- **Command_Sequence**: Ordered list of OBD2/UDS commands to send to ELM327 to accomplish a diagnostic task
- **Vehicle_Profile**: Configuration defining make, model, year, and known module addresses for a specific vehicle
- **Closed_Loop_Feedback**: Process where the Agent executes diagnostics, documents findings, and uses documentation to improve future sessions

## Requirements

### Requirement 1: Toolkit Script Organization

**User Story:** As an AI agent, I want a well-organized toolkit of Python scripts, so that I can execute specific diagnostic tasks by calling the appropriate script.

#### Acceptance Criteria

1. THE Toolkit SHALL organize scripts into categories: vehicle_communication, web_research, knowledge_management, and diagnostic_procedures
2. THE Toolkit SHALL extract existing functionality from elm327_adapter.py, vin_reader.py, hvac_diagnostics.py, and can_bus_explorer.py into standalone Tool_Scripts
3. EACH Tool_Script SHALL have a clear command-line interface accepting inputs as arguments and returning outputs as JSON
4. THE Toolkit SHALL include a registry file (toolkit_registry.json) mapping diagnostic tasks to Tool_Scripts
5. THE Toolkit SHALL include documentation for each Tool_Script describing purpose, inputs, outputs, and usage examples

### Requirement 2: Natural Language Query Interpretation

**User Story:** As a technician, I want to describe what I need in plain language like "check DTC in HVAC of my vehicle", so that I don't need to know specific commands.

#### Acceptance Criteria

1. WHEN a user provides a natural language query, THE Query_Parser SHALL extract the action (e.g., "check DTC", "read", "clear", "actuate")
2. WHEN a query mentions a module name, THE Query_Parser SHALL identify the target module (e.g., "HVAC", "ABS", "PCM", "transmission")
3. WHEN a query is ambiguous or missing information, THE Agent SHALL ask clarifying questions to the user
4. WHEN the vehicle make/model/year is not known, THE Agent SHALL ask the user or attempt to read VIN
5. THE Query_Parser SHALL support common diagnostic phrases including "check errors", "read codes", "clear codes", "scan", "test", and actuation commands

### Requirement 3: Web Research for Unknown Procedures

**User Story:** As a technician, I want the agent to search the internet for diagnostic procedures it doesn't know, so that I can diagnose any module without pre-programmed knowledge.

#### Acceptance Criteria

1. WHEN a diagnostic procedure is not in the Knowledge_Document, THE Web_Researcher SHALL search for manufacturer service manuals and repair guides
2. WHEN searching, THE Web_Researcher SHALL use vehicle make/model/year and module name as search terms
3. WHEN searching for Ford vehicles, THE Web_Researcher SHALL also search related Ford models from the same era (e.g., Ford Fusion for Ford Escape 2008)
4. THE Web_Researcher SHALL extract OBD2/UDS command sequences from search results
5. WHEN multiple sources are found, THE Web_Researcher SHALL prioritize official manufacturer documentation over forum posts

### Requirement 4: Knowledge Documentation and Persistence

**User Story:** As an AI agent, I want diagnostic information stored in a tight, efficient format, so that I can read it quickly without consuming excessive memory.

#### Acceptance Criteria

1. THE Knowledge_Document SHALL use a compact format for storing module addresses, OBD2/UDS commands, and technical specifications
2. THE Knowledge_Document SHALL use abbreviations and symbols to minimize file size (e.g., "M:HVAC A:0x7A0 C:03 R:43..." for module, address, command, response)
3. THE Knowledge_Document SHALL include a README file explaining the tight format, symbols, and how humans can read it
4. WHEN a diagnostic procedure is successfully executed, THE Agent SHALL append the procedure to the Knowledge_Document in the compact format
5. WHEN retrieving procedures, THE Agent SHALL parse the compact format and extract relevant information within 500ms

### Requirement 5: Interactive Clarification and Manual Consultation

**User Story:** As a technician, I want the agent to ask me for information from service manuals when needed, so that we can work together to figure out unknown procedures.

#### Acceptance Criteria

1. WHEN the Web_Researcher cannot find a procedure, THE Agent SHALL ask the user if they have access to a service manual
2. WHEN the user has a manual, THE Agent SHALL guide them on what information to look for (e.g., "Look for HVAC module address and DTC read command")
3. WHEN the user provides manual information, THE Agent SHALL parse it and construct the appropriate Command_Sequence
4. THE Agent SHALL ask the user to confirm before sending any newly constructed commands to the vehicle
5. WHEN a procedure is confirmed working, THE Agent SHALL document it in the Knowledge_Document

### Requirement 6: Generic Module Diagnostic Framework

**User Story:** As a developer, I want the agent to use a generic framework for module diagnostics, so that any module can be diagnosed using the same approach.

#### Acceptance Criteria

1. THE Agent SHALL support a generic diagnostic workflow: identify module → find procedure → execute commands → parse responses → present results
2. WHEN diagnosing any module, THE Agent SHALL attempt standard OBD2 commands first (Mode 03 for DTCs, Mode 01 for live data)
3. WHEN standard commands fail, THE Agent SHALL search for manufacturer-specific UDS commands
4. THE Agent SHALL maintain a registry of known module addresses for Ford vehicles (e.g., HVAC, ABS, PCM, BCM)
5. WHEN a new module is encountered, THE Agent SHALL add it to the registry after successful communication

### Requirement 7: Ford-Specific Diagnostic Support

**User Story:** As a technician working on Ford vehicles, I want the agent to have built-in knowledge of Ford diagnostic protocols, so that common Ford diagnostics work immediately.

#### Acceptance Criteria

1. THE Agent SHALL include pre-documented procedures for 2008 Ford Escape HVAC diagnostics as Phase 1 reference implementation
2. THE Agent SHALL support Ford-specific DTC code formats (P, C, B, U codes with Ford definitions)
3. WHEN diagnosing Ford vehicles, THE Agent SHALL check both High CAN (500kbps) and Low CAN (125kbps) if initial attempts fail
4. THE Agent SHALL recognize common Ford module names and their typical CAN addresses
5. THE Agent SHALL support cross-referencing Ford Escape procedures with Ford Fusion and similar-era Ford models

### Requirement 8: Python Script Generation and Execution

**User Story:** As a technician, I want the agent to write and run Python scripts for research and data analysis, so that complex tasks can be automated.

#### Acceptance Criteria

1. WHEN research or data retrieval is needed, THE Script_Generator SHALL create Python scripts to accomplish the task
2. THE Script_Generator SHALL create scripts for web scraping service manuals, parsing DTC databases, and analyzing CAN bus logs
3. THE Script_Executor SHALL run generated scripts in a sandboxed environment with restricted file system and network access
4. WHEN a script completes, THE Agent SHALL parse the output and incorporate findings into the diagnostic session
5. THE Agent SHALL save successful scripts to the Knowledge_Document for reuse

### Requirement 9: Vehicle Flexibility and Multi-Manufacturer Support

**User Story:** As a developer, I want the agent to support any vehicle manufacturer, so that it's not limited to Ford vehicles.

#### Acceptance Criteria

1. THE Agent SHALL support defining new Vehicle_Profiles through configuration files without code changes
2. WHEN a new vehicle make/model is encountered, THE Agent SHALL create a new Vehicle_Profile and populate it through research
3. THE Agent SHALL support manufacturer-specific diagnostic protocols (Ford, GM, Toyota, Honda, etc.) through pluggable protocol handlers
4. WHEN diagnosing a non-Ford vehicle, THE Agent SHALL search for manufacturer-specific service information
5. THE Agent SHALL maintain separate Knowledge_Documents for each vehicle make/model/year combination

### Requirement 10: Actuation Command Support

**User Story:** As a technician, I want to command the agent to actuate vehicle components like "purge EVAP valve" or "start ABS bleeding", so that I can perform active tests.

#### Acceptance Criteria

1. WHEN an actuation command is requested, THE Agent SHALL search for the appropriate UDS command sequence
2. WHEN an actuation is potentially dangerous, THE Agent SHALL warn the user and require explicit confirmation
3. THE Agent SHALL support common actuations including EVAP purge, ABS bleeding, HVAC door movement, and fuel pump activation
4. WHEN executing actuations, THE Agent SHALL monitor for error responses and stop if errors occur
5. THE Agent SHALL document successful actuation procedures in the Knowledge_Document

### Requirement 11: CAN Bus Exploration and Module Discovery

**User Story:** As a technician, I want the agent to explore the CAN bus and discover active modules, so that I know what's available to diagnose.

#### Acceptance Criteria

1. WHEN CAN bus exploration is requested, THE Agent SHALL use the existing can_bus_explorer.py to capture traffic
2. THE Agent SHALL identify active modules by analyzing CAN frame IDs
3. THE Agent SHALL attempt to correlate CAN IDs with known module types using web research
4. WHEN a module is discovered, THE Agent SHALL add it to the vehicle's module registry
5. THE Agent SHALL support event-driven capture where the user describes an action and the agent captures corresponding CAN traffic

### Requirement 11: Diagnostic Report Generation

**User Story:** As a technician, I want the agent to generate a diagnostic report after each session, so that I have documentation for repairs.

#### Acceptance Criteria

1. WHEN a diagnostic session completes, THE Agent SHALL generate a report with vehicle info, modules scanned, DTCs found, and recommendations
2. THE Report SHALL include timestamps, command sequences executed, and raw responses received
3. THE Report SHALL include AI-generated interpretation of findings and suggested next steps
4. THE Report SHALL be exportable in markdown and JSON formats
5. THE Report SHALL include links to relevant web resources found during the session

### Requirement 12: Safety and Confirmation for Dangerous Operations

**User Story:** As a safety officer, I want the agent to require confirmation before dangerous operations, so that vehicles and technicians remain safe.

#### Acceptance Criteria

1. WHEN an actuation command is requested, THE Agent SHALL require explicit user confirmation before execution
2. THE Agent SHALL warn about potential dangers for operations like ABS bleeding, airbag tests, and fuel system actuations
3. WHEN a command could cause vehicle movement, THE Agent SHALL instruct the user to ensure the vehicle is in park with parking brake engaged
4. THE Agent SHALL maintain a list of known dangerous commands and their safety precautions
5. WHEN a user attempts to bypass safety checks, THE Agent SHALL refuse and log the attempt

### Requirement 13: Multi-Backend AI Support

**User Story:** As a developer, I want the agent to support multiple AI backends, so that users can choose their preferred AI provider.

#### Acceptance Criteria

1. THE Agent SHALL support OpenAI API as a backend
2. THE Agent SHALL support Anthropic Claude API as a backend  
3. THE Agent SHALL support local models via Ollama or similar frameworks
4. WHEN switching backends, THE Agent SHALL maintain consistent query interpretation and research capabilities
5. THE Agent SHALL gracefully handle backend failures and provide informative error messages

### Requirement 14: Session Logging and Audit Trail

**User Story:** As a compliance officer, I want all agent interactions logged, so that we have an audit trail for diagnostics.

#### Acceptance Criteria

1. THE Agent SHALL log all natural language queries and their parsed interpretations
2. THE Agent SHALL log all OBD2/UDS commands sent to the vehicle with timestamps and responses
3. THE Agent SHALL log all web searches performed and key information extracted
4. THE Agent SHALL log all user confirmations for dangerous operations
5. THE Log SHALL be stored in JSONL format for analysis and replay

### Requirement 15: Configuration and Extensibility

**User Story:** As a developer, I want the agent to be configurable, so that I can adapt it to different vehicles and use cases.

#### Acceptance Criteria

1. THE Agent SHALL load configuration from a YAML file specifying AI backend, COM port, and safety settings
2. THE Agent SHALL support loading custom DTC definitions from external JSON files
3. THE Agent SHALL support adding new vehicle makes/models through configuration without code changes
4. WHEN configuration changes, THE Agent SHALL reload settings without requiring a restart
5. THE Agent SHALL validate configuration on startup and report errors clearly

### Requirement 16: Parsing and Serialization

**User Story:** As a developer, I want the agent to reliably parse OBD2 responses and serialize diagnostic data, so that data integrity is maintained.

#### Acceptance Criteria

1. WHEN parsing OBD2 responses, THE Agent SHALL validate response format against expected patterns
2. WHEN serializing diagnostic data, THE Agent SHALL use JSON format with proper escaping
3. THE Agent SHALL include a pretty printer for diagnostic data to enable human-readable output
4. FOR ALL valid diagnostic data objects, serializing then deserializing SHALL produce an equivalent object (round-trip property)
5. WHEN parsing fails, THE Agent SHALL log the raw response and provide a descriptive error message

### Requirement 17: Error Handling and Recovery

**User Story:** As a technician, I want the agent to handle errors gracefully, so that one failure doesn't stop the entire diagnostic session.

#### Acceptance Criteria

1. WHEN a command fails, THE Agent SHALL log the error and suggest alternative approaches
2. WHEN CAN bus communication fails, THE Agent SHALL suggest checking connections and trying different CAN modes
3. WHEN web research fails, THE Agent SHALL fall back to asking the user for manual information
4. WHEN the AI backend is unavailable, THE Agent SHALL provide a degraded mode with basic command execution
5. THE Agent SHALL never crash or exit unexpectedly; all errors SHALL be caught and reported to the user

