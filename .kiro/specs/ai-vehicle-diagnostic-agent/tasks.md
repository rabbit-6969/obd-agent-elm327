# Implementation Plan: AI Vehicle Diagnostic Agent

## Overview

This implementation plan breaks down the AI Vehicle Diagnostic Agent into discrete coding tasks. The system will be built incrementally, starting with core infrastructure, then adding knowledge management, query parsing, web research, toolkit scripts, agent orchestration, and safety mechanisms. Each task builds on previous work, with testing integrated throughout.

**Phase 1 Focus**: Ford Escape 2008 HVAC diagnostics as reference implementation.

## Tasks

- [ ] 1. Project setup and configuration
  - [x] 1.1 Create project directory structure
    - Create directories: `agent_core/`, `toolkit/vehicle_communication/`, `toolkit/web_research/`, `toolkit/knowledge_management/`, `toolkit/diagnostic_procedures/`, `knowledge_base/`, `config/`, `tests/`, `logs/`
    - Create `__init__.py` files for Python package structure
    - _Requirements: 1.1, 15.1_
  
  - [x] 1.2 Implement configuration system
    - Create `config/agent_config.yaml` with AI backend, vehicle port, safety settings, web research mode
    - Create `config/config_loader.py` to load and validate YAML configuration
    - Support environment variables for API keys
    - _Requirements: 15.1, 15.4, 15.5_
  
  - [ ]* 1.3 Write unit tests for configuration loading
    - Test valid configuration loading
    - Test invalid configuration detection
    - Test environment variable substitution
    - _Requirements: 15.5_

- [x] 2. Knowledge document format implementation
  - [x] 2.1 Implement technical data format parser
    - Create `toolkit/knowledge_management/technical_parser.py`
    - Parse compact format: `M:HVAC A:7A0 P:CAN B:HS`
    - Parse command definitions: `C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}`
    - Extract module info, addresses, protocols, commands, response patterns
    - _Requirements: 4.1, 4.2, 4.5_
  
  - [ ]* 2.2 Write property test for technical data parser
    - **Property 1: Serialization round trip**
    - **Validates: Requirements 16.4**
    - For any valid technical data object, serializing to compact format then parsing should produce an equivalent object
  
  - [x] 2.3 Implement vehicle profile YAML handler
    - Create `toolkit/knowledge_management/profile_handler.py`
    - Load YAML vehicle profiles with DTC descriptions, common causes, repair hints
    - Support querying DTC descriptions by code
    - _Requirements: 4.1, 15.2_
  
  - [x] 2.4 Create Ford Escape 2008 knowledge base
    - Create `knowledge_base/Ford_Escape_2008_technical.dat` with HVAC module data
    - Create `knowledge_base/Ford_Escape_2008_profile.yaml` with DTC descriptions
    - Include HVAC module address (0x7A0), read DTC command (03), common DTCs (P1632, etc.)
    - _Requirements: 7.1, 7.4_
  
  - [ ]* 2.5 Write unit tests for knowledge base loading
    - Test loading Ford Escape 2008 technical data
    - Test querying DTC descriptions
    - Test handling missing data gracefully
    - _Requirements: 4.5, 7.1_

- [ ] 3. Query parser implementation
  - [x] 3.1 Implement natural language query parser
    - Create `agent_core/query_parser.py`
    - Extract action keywords: "check", "read", "clear", "scan", "test", "actuate"
    - Extract module names: "HVAC", "ABS", "PCM", "transmission", "BCM"
    - Extract vehicle info: make, model, year
    - Return structured `ParsedIntent` object with action, module, vehicle_info
    - _Requirements: 2.1, 2.2, 2.5_
  
  - [ ]* 3.2 Write property test for query parser
    - **Property 2: Action extraction consistency**
    - **Validates: Requirements 2.1**
    - For any query containing a valid action keyword, the parser should extract that action
  
  - [ ]* 3.3 Write property test for module extraction
    - **Property 3: Module extraction consistency**
    - **Validates: Requirements 2.2**
    - For any query containing a valid module name, the parser should extract that module
  
  - [x] 3.4 Implement ambiguity detection and clarification
    - Detect when query is missing action or module
    - Generate clarifying questions for user
    - Handle multi-turn clarification dialogue
    - _Requirements: 2.3, 2.4_
  
  - [ ]* 3.5 Write unit tests for query parsing
    - Test parsing "check hvac codes on my vehicle"
    - Test parsing "read DTC from ABS"
    - Test ambiguous query detection
    - Test clarification question generation
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Web research module implementation
  - [x] 5.1 Implement AI-assisted web search
    - Create `toolkit/web_research/ai_search.py`
    - Use AI backend's web search capability if available
    - Construct search queries: "{make} {model} {year} {module} {action} OBD2"
    - Extract command sequences from search results
    - _Requirements: 3.1, 3.2, 3.4_
  
  - [x] 5.2 Implement user fallback mode
    - Create `toolkit/web_research/user_fallback.py`
    - Generate search query and present to user
    - Accept user-pasted search results
    - Parse user-provided text for command sequences
    - _Requirements: 5.1, 5.2_
  
  - [ ]* 5.3 Write property test for command extraction
    - **Property 4: Command extraction from text**
    - **Validates: Requirements 3.4**
    - For any text containing valid OBD2 commands (hex format), the extractor should identify them
  
  - [x] 5.4 Implement Ford cross-reference search
    - Search related Ford models (Fusion, Focus) when Escape procedures not found
    - Prioritize same-era vehicles (2008-2012)
    - _Requirements: 3.3, 7.5_
  
  - [x] 5.5 Implement source prioritization
    - Rank sources: official manuals > repair databases > forums
    - Extract confidence scores from search results
    - _Requirements: 3.5_
  
  - [ ]* 5.6 Write unit tests for web research
    - Test search query construction
    - Test command extraction from sample text
    - Test source prioritization logic
    - _Requirements: 3.1, 3.2, 3.5_

- [ ] 6. Toolkit scripts - Vehicle communication
  - [x] 6.1 Extract ELM327 communication into toolkit script
    - Create `toolkit/vehicle_communication/elm327_base.py`
    - Extract core functionality from existing `elm327_adapter.py`
    - Implement send_command(), read_response(), initialize_adapter()
    - _Requirements: 1.2, 1.3_
  
  - [x] 6.2 Create read_dtc.py toolkit script
    - Create `toolkit/vehicle_communication/read_dtc.py`
    - Accept CLI args: --port, --module, --address
    - Send Mode 03 command, parse response
    - Return JSON: {"success": true, "dtcs": [{"code": "P1632", "raw": "16 32"}]}
    - _Requirements: 1.3, 6.2, 7.2_
  
  - [ ]* 6.3 Write property test for DTC parsing
    - **Property 5: DTC format validation**
    - **Validates: Requirements 16.1**
    - For any OBD2 DTC response, parsing should validate format before extracting codes
  
  - [x] 6.4 Create clear_dtc.py toolkit script
    - Create `toolkit/vehicle_communication/clear_dtc.py`
    - Accept CLI args: --port, --module
    - Send Mode 04 command, verify success
    - Return JSON: {"success": true, "cleared": true}
    - _Requirements: 1.3, 6.2_
  
  - [x]* 6.5 Create read_vin.py toolkit script
    - Create `toolkit/vehicle_communication/read_vin.py`
    - Extract functionality from existing `vin_reader.py`
    - Accept CLI arg: --port
    - Return JSON: {"success": true, "vin": "1FAHP551XX8156549"}
    - _Requirements: 1.2, 1.3, 2.4_
  
  - [x]* 6.6 Create can_explore.py toolkit script
    - Create `toolkit/vehicle_communication/can_explore.py`
    - Extract functionality from existing `can_bus_explorer.py`
    - Accept CLI args: --port, --duration
    - Capture CAN traffic, identify active module IDs
    - Return JSON: {"success": true, "modules": [{"id": "0x7A0", "frames": 45}]}
    - _Requirements: 1.2, 11.1, 11.2_
  
  - [ ]* 6.7 Write unit tests for toolkit scripts
    - Test read_dtc.py with mock ELM327 responses
    - Test clear_dtc.py success/failure cases
    - Test read_vin.py parsing
    - Test can_explore.py frame analysis
    - _Requirements: 1.3, 6.2, 11.1_

- [ ] 7. Toolkit scripts - Knowledge management
  - [x] 7.1 Create append_procedure.py toolkit script
    - Create `toolkit/knowledge_management/append_procedure.py`
    - Accept JSON input with module, commands, responses
    - Convert to compact format
    - Append to technical data file
    - _Requirements: 1.3, 4.4_
  
  - [x] 7.2 Create query_knowledge.py toolkit script
    - Create `toolkit/knowledge_management/query_knowledge.py`
    - Accept CLI args: --vehicle, --module, --action
    - Search technical data file for matching procedure
    - Return JSON with commands and expected responses
    - _Requirements: 1.3, 4.5_
  
  - [ ]* 7.3 Write property test for knowledge append
    - **Property 6: Knowledge persistence**
    - **Validates: Requirements 4.4**
    - For any valid procedure, appending then querying should retrieve the same procedure
  
  - [ ]* 7.4 Write unit tests for knowledge management
    - Test appending new procedure
    - Test querying existing procedure
    - Test handling missing procedures
    - _Requirements: 4.4, 4.5_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Agent core orchestration
  - [x] 9.1 Implement agent main loop
    - Create `agent_core/agent.py`
    - Implement main loop: receive query → parse → plan → execute → report
    - Integrate query parser, knowledge lookup, toolkit executor
    - _Requirements: 6.1_
  
  - [x] 9.2 Implement toolkit executor
    - Create `agent_core/toolkit_executor.py`
    - Execute toolkit scripts as subprocesses
    - Parse JSON output from scripts
    - Handle script failures gracefully
    - _Requirements: 1.3, 8.3, 8.4_
  
  - [x] 9.3 Implement diagnostic workflow orchestration
    - Create `agent_core/diagnostic_workflow.py`
    - Implement workflow: identify module → find procedure → execute → parse → present
    - Try standard OBD2 first, fall back to manufacturer-specific
    - _Requirements: 6.1, 6.2, 6.3_
  
  - [x] 9.4 Implement closed-loop feedback system
    - After successful diagnostic, document procedure in knowledge base
    - Track success/failure rates for procedures
    - Prioritize high-success procedures in future sessions
    - _Requirements: 4.4, 6.5_
  
  - [ ]* 9.5 Write unit tests for agent orchestration
    - Test main loop with mock query
    - Test toolkit executor with mock scripts
    - Test workflow orchestration
    - Test feedback loop documentation
    - _Requirements: 6.1, 6.5_

- [ ] 10. AI backend integration
  - [x] 10.1 Implement AI backend interface
    - Create `agent_core/ai_backend.py`
    - Define abstract interface: generate_response(), web_search()
    - _Requirements: 13.1, 13.2, 13.3, 13.4_
  
  - [ ]* 10.2 Implement OpenAI backend
    - Create `agent_core/backends/openai_backend.py`
    - Implement OpenAI API calls
    - Handle API key from environment
    - _Requirements: 13.1_
  
  - [x] 10.3 Implement Claude backend
    - Create `agent_core/backends/claude_backend.py`
    - Implement Anthropic API calls
    - Handle API key from environment
    - _Requirements: 13.2_
  
  - [ ]* 10.4 Implement Ollama backend
    - Create `agent_core/backends/ollama_backend.py`
    - Implement local model calls via Ollama API
    - No API key required
    - _Requirements: 13.3_
  
  - [x] 10.5 Implement backend fallback logic
    - Try primary backend, fall back to secondary if it fails
    - Load backend priority from configuration
    - Provide informative error messages
    - _Requirements: 13.4, 13.5_
  
  - [ ]* 10.6 Write unit tests for AI backends
    - Test OpenAI backend with mock API
    - Test Claude backend with mock API
    - Test Ollama backend with mock API
    - Test fallback logic
    - _Requirements: 13.4, 13.5_

- [ ]* 11. Safety mechanisms
  - [ ]* 11.1 Implement danger classification system
    - Create `agent_core/safety.py`
    - Define danger levels: SAFE, CAUTION, WARNING, DANGER
    - Classify operations by danger level
    - _Requirements: 12.1, 12.2, 12.4_
  
  - [ ]* 11.2 Implement confirmation workflows
    - Implement simple confirmation for CAUTION operations
    - Implement detailed confirmation for WARNING operations
    - Implement multi-step confirmation for DANGER operations
    - _Requirements: 12.1, 12.3_
  
  - [ ]* 11.3 Implement safety preconditions
    - Check vehicle state before dangerous operations
    - Require parking brake engaged for movement-causing operations
    - Refuse to bypass safety checks
    - _Requirements: 12.3, 12.5_
  
  - [ ]* 11.4 Write property test for safety confirmations
    - **Property 7: Dangerous operations require confirmation**
    - **Validates: Requirements 12.1**
    - For any operation classified as CAUTION or higher, execution should require user confirmation
  
  - [ ]* 11.5 Write unit tests for safety mechanisms
    - Test danger classification
    - Test confirmation workflows
    - Test safety precondition checks
    - Test bypass refusal
    - _Requirements: 12.1, 12.2, 12.3, 12.5_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 13. Actuation command support
  - [ ]* 13.1 Create actuate.py toolkit script
    - Create `toolkit/vehicle_communication/actuate.py`
    - Accept CLI args: --port, --module, --actuation-type
    - Support EVAP purge, ABS bleeding, HVAC door movement
    - Monitor for error responses during actuation
    - _Requirements: 10.1, 10.3, 10.4_
  
  - [ ]* 13.2 Integrate actuation with safety system
    - Classify actuations by danger level
    - Require appropriate confirmations before execution
    - Document successful actuations in knowledge base
    - _Requirements: 10.2, 10.5_
  
  - [ ]* 13.3 Write unit tests for actuation
    - Test EVAP purge actuation
    - Test HVAC door actuation
    - Test error handling during actuation
    - Test safety integration
    - _Requirements: 10.1, 10.4, 10.5_

- [ ] 14. Session logging and audit trail
  - [x] 14.1 Implement session logger
    - Create `agent_core/session_logger.py`
    - Log queries, parsed intents, commands, responses, confirmations
    - Use JSONL format for structured logging
    - Include timestamps for all events
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_
  
  - [ ]* 14.2 Write property test for logging completeness
    - **Property 8: All operations are logged**
    - **Validates: Requirements 14.1, 14.2, 14.3, 14.4**
    - For any agent operation, the session log should contain a corresponding entry
  
  - [ ]* 14.3 Write unit tests for session logging
    - Test query logging
    - Test command logging
    - Test confirmation logging
    - Test JSONL format
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ] 15. Diagnostic report generation
  - [x] 15.1 Implement report generator
    - Create `agent_core/report_generator.py`
    - Generate report with vehicle info, modules scanned, DTCs found
    - Include timestamps, commands executed, raw responses
    - Add AI-generated interpretation and recommendations
    - _Requirements: 11.1, 11.2, 11.3_
  
  - [x] 15.2 Implement report export formats
    - Export to markdown format
    - Export to JSON format
    - Include links to web resources found during session
    - _Requirements: 11.4, 11.5_
  
  - [ ]* 15.3 Write unit tests for report generation
    - Test markdown export
    - Test JSON export
    - Test report content completeness
    - _Requirements: 11.1, 11.2, 11.4_

- [ ] 16. Error handling and recovery
  - [x] 16.1 Implement error recovery strategies
    - Create `agent_core/error_handler.py`
    - Implement fallback strategies for command failures
    - Suggest alternative approaches when operations fail
    - _Requirements: 17.1, 17.2_
  
  - [x] 16.2 Implement graceful degradation
    - Fall back to user manual consultation when web research fails
    - Provide degraded mode when AI backend unavailable
    - Never crash or exit unexpectedly
    - _Requirements: 17.3, 17.4, 17.5_
  
  - [ ]* 16.3 Write property test for error handling
    - **Property 9: No uncaught exceptions**
    - **Validates: Requirements 17.5**
    - For any operation that can fail, errors should be caught and reported gracefully
  
  - [ ]* 16.4 Write unit tests for error handling
    - Test command failure recovery
    - Test CAN bus failure suggestions
    - Test web research fallback
    - Test AI backend unavailability
    - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Vehicle profile management
  - [x] 18.1 Implement vehicle profile loader
    - Create `agent_core/vehicle_profile.py`
    - Load vehicle profiles from YAML configuration
    - Support defining new vehicles without code changes
    - _Requirements: 9.1, 9.2, 15.3_
  
  - [x] 18.2 Implement multi-manufacturer support
    - Create pluggable protocol handlers for different manufacturers
    - Support Ford, GM, Toyota, Honda protocols
    - Maintain separate knowledge documents per vehicle
    - _Requirements: 9.3, 9.4, 9.5_
  
  - [ ]* 18.3 Write unit tests for vehicle profiles
    - Test loading Ford profile
    - Test creating new vehicle profile
    - Test manufacturer-specific protocol selection
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 19. Module discovery and registry
  - [x] 19.1 Implement module registry
    - Create `agent_core/module_registry.py`
    - Maintain registry of known module addresses for each vehicle
    - Add newly discovered modules to registry
    - _Requirements: 6.4, 6.5, 11.4_
  
  - [x] 19.2 Implement CAN ID correlation
    - Correlate discovered CAN IDs with module types using web research
    - Update module registry with correlations
    - _Requirements: 11.3_
  
  - [x] 19.3 Implement event-driven capture
    - Accept user description of action (e.g., "press brake pedal")
    - Capture CAN traffic during action
    - Identify relevant CAN IDs
    - _Requirements: 11.5_
  
  - [ ]* 19.4 Write unit tests for module discovery
    - Test module registry operations
    - Test CAN ID correlation
    - Test event-driven capture
    - _Requirements: 6.4, 6.5, 11.3, 11.5_

- [ ] 20. Script generation and execution
  - [x] 20.1 Implement script generator
    - Create `agent_core/script_generator.py`
    - Generate Python scripts for web scraping, data parsing, CAN analysis
    - Use templates for common script patterns
    - _Requirements: 8.1, 8.2_
  
  - [x] 20.2 Implement sandboxed script executor
    - Create `agent_core/script_executor.py`
    - Execute generated scripts in restricted environment
    - Limit file system and network access
    - Parse script output and incorporate into session
    - _Requirements: 8.3, 8.4_
  
  - [x] 20.3 Implement script persistence
    - Save successful scripts to knowledge base
    - Reuse scripts for similar tasks
    - _Requirements: 8.5_
  
  - [ ]* 20.4 Write unit tests for script generation
    - Test web scraping script generation
    - Test data parsing script generation
    - Test sandboxed execution
    - Test script persistence
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [ ] 21. Interactive clarification system
  - [x] 21.1 Implement manual consultation workflow
    - Create `agent_core/manual_consultation.py`
    - Ask user for service manual information when web research fails
    - Guide user on what information to look for
    - Parse user-provided manual information
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [x] 21.2 Implement command confirmation workflow
    - Require user confirmation before sending newly constructed commands
    - Show command details and expected behavior
    - Document confirmed working procedures
    - _Requirements: 5.4, 5.5_
  
  - [ ]* 21.3 Write unit tests for manual consultation
    - Test manual consultation prompts
    - Test parsing user-provided information
    - Test command confirmation workflow
    - Test procedure documentation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 22. Toolkit registry and documentation
  - [x] 22.1 Create toolkit registry
    - Create `toolkit/toolkit_registry.json`
    - Map diagnostic tasks to toolkit scripts
    - Include script descriptions, inputs, outputs
    - _Requirements: 1.4_
  
  - [x] 22.2 Generate toolkit documentation
    - Create `toolkit/README.md` with overview of all scripts
    - Document each script's purpose, CLI interface, examples
    - Include troubleshooting guide
    - _Requirements: 1.5_
  
  - [ ]* 22.3 Write unit tests for toolkit registry
    - Test registry loading
    - Test task-to-script mapping
    - _Requirements: 1.4_

- [ ] 23. Final integration and testing
  - [x] 23.1 Create main entry point
    - Create `main.py` as CLI entry point
    - Parse command-line arguments
    - Initialize agent with configuration
    - Start interactive session
    - _Requirements: 15.1_
  
  - [x] 23.2 Implement interactive session loop
    - Accept user queries in loop
    - Display results with formatting
    - Handle exit commands gracefully
    - _Requirements: 2.1, 11.1_
  
  - [ ]* 23.3 Write integration tests
    - Test end-to-end diagnostic workflow with Ford Escape HVAC
    - Test web research fallback to user mode
    - Test closed-loop learning (execute → document → reuse)
    - Test safety confirmation workflows
    - _Requirements: 6.1, 7.1, 12.1_

- [ ] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 25. Documentation and examples
  - [x] 25.1 Create user documentation
    - Create `docs/USER_GUIDE.md` with installation, configuration, usage
    - Include example diagnostic sessions
    - Document safety precautions
    - _Requirements: 12.2, 15.1_
  
  - [x] 25.2 Create developer documentation
    - Create `docs/DEVELOPER_GUIDE.md` with architecture overview
    - Document how to add new vehicles, modules, toolkit scripts
    - Include testing guidelines
    - _Requirements: 1.5, 9.1, 15.3_
  
  - [x] 25.3 Create example configurations
    - Create `examples/ford_escape_2008.yaml` with complete vehicle profile
    - Create `examples/agent_config_openai.yaml` for OpenAI backend
    - Create `examples/agent_config_ollama.yaml` for local models
    - _Requirements: 15.1, 15.3_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and error conditions
- Phase 1 focuses on Ford Escape 2008 HVAC as reference implementation
- All toolkit scripts follow standard CLI interface: JSON in → JSON out
- Safety mechanisms are integrated throughout, not bolted on at the end
- Closed-loop feedback system ensures continuous learning and improvement
