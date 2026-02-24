# AI Vehicle Diagnostic Agent - User Guide

## Introduction

The AI Vehicle Diagnostic Agent is an intelligent diagnostic system that helps you diagnose vehicle issues through natural language queries. It learns from each diagnostic session and becomes smarter over time.

## Quick Start

### Prerequisites

1. **Hardware:**
   - ELM327 OBD2 adapter (USB or Bluetooth)
   - Vehicle with OBD2 port (1996+ for US vehicles)

2. **Software:**
   - Python 3.8 or higher
   - Required packages (see Installation)

### Installation

1. Clone or download the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Connect your ELM327 adapter to your computer
4. Identify the COM port (Windows: COM3, Linux: /dev/ttyUSB0)

### First Run

1. Start the agent:
```bash
python main.py --port COM3
```

2. The agent will initialize and present an interactive prompt:
```
🔧 >
```

3. Try your first query:
```
🔧 > check HVAC codes
```

## Basic Usage

### Natural Language Queries

The agent understands natural language. Here are common query patterns:

**Reading Diagnostic Codes:**
- "check HVAC codes"
- "read DTC from ABS"
- "scan all modules"
- "what errors does my car have"

**Clearing Codes:**
- "clear codes"
- "clear HVAC errors"
- "reset diagnostic codes"

**Vehicle Information:**
- "read VIN"
- "what vehicle is this"
- "identify my car"

**Module-Specific:**
- "check transmission"
- "scan ABS module"
- "read PCM data"

### Interactive Commands

Special commands available in interactive mode:

- `help` - Show available commands
- `status` - Show agent status
- `vehicle` - Show current vehicle info
- `modules` - List known modules
- `history` - Show session history
- `exit` or `quit` - Exit the agent

## Configuration

### Configuration File

The agent uses `config/agent_config.yaml` for configuration:

```yaml
ai_backend:
  primary: "claude"
  fallback: ["openai", "ollama"]

vehicle:
  port: "COM3"

web_research:
  mode: "ai_assisted"
  enabled: true

safety:
  require_confirmation: true
  allow_bypass: false
```

### Environment Variables

Set API keys as environment variables:

```bash
# Windows
set ANTHROPIC_API_KEY=your_key_here
set OPENAI_API_KEY=your_key_here

# Linux/Mac
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
```

### Command-Line Options

Override configuration with command-line arguments:

```bash
# Specify COM port
python main.py --port COM3

# Use custom configuration
python main.py --config my_config.yaml

# Disable web research
python main.py --port COM3 --no-web-research

# Single query mode
python main.py --port COM3 --query "check HVAC codes"

# Enable debug logging
python main.py --port COM3 --log-level DEBUG
```

## How It Works

### Learning System

The agent uses a closed-loop feedback system:

1. **First Time:** When you ask about a module it doesn't know, it will:
   - Search online for procedures
   - Ask you to confirm before sending commands
   - Document successful procedures

2. **Next Time:** The agent remembers and executes instantly!

### Web Research Modes

**AI-Assisted Mode (Default):**
- Agent searches automatically using AI backend
- Fastest and most convenient
- Requires AI API key

**User Fallback Mode:**
- Agent asks you to search manually
- You paste search results
- No API keys required
- Works offline (after initial setup)

### Knowledge Base

The agent maintains a knowledge base in `knowledge_base/`:

- **Technical Data (.dat):** Compact format for fast parsing
- **Vehicle Profiles (.yaml):** Human-readable DTC descriptions
- **Module Registry (.json):** Discovered modules and addresses

## Example Sessions

### Session 1: First HVAC Diagnostic

```
🔧 > check HVAC codes

🔍 Searching for Ford Escape 2008 HVAC diagnostic procedure...

📖 Manual Consultation Required
I couldn't find procedures online. If you have a service manual, please provide:
1. Module CAN Address
2. Diagnostic Command
3. Expected Response Format

[User provides: Address: 0x7A0, Command: 03, Response: 43 XX XX]

⚠️  Command Confirmation Required
This is a newly constructed command. Do you want to proceed? (yes/no)

[User confirms: yes]

✅ Command Successful!
Found 1 DTC: P1632 (HVAC Mix Door Actuator Circuit - Stuck)

This procedure has been documented for future use!
```

### Session 2: Same Diagnostic (Instant!)

```
🔧 > check HVAC codes

✅ Found 1 DTC: P1632 (HVAC Mix Door Actuator Circuit - Stuck)

[Instant result - no searching or confirmation needed]
```

### Session 3: Clearing Codes

```
🔧 > clear HVAC codes

⚠️  This will clear diagnostic codes. Continue? (yes/no)

[User confirms: yes]

✅ Codes cleared successfully!
```

## Safety Precautions

### Danger Levels

The agent classifies operations by danger level:

- **SAFE:** Read-only operations (read DTC, read VIN)
  - No confirmation required
  
- **CAUTION:** Write operations (clear DTC)
  - Simple confirmation required
  
- **WARNING:** Actuations (EVAP purge, blend door)
  - Detailed confirmation required
  
- **DANGER:** Critical systems (ABS, airbag)
  - Multi-step confirmation required
  - Safety preconditions checked

### Best Practices

1. **Vehicle State:**
   - Park vehicle safely
   - Engage parking brake
   - Turn off engine for most diagnostics
   - Keep ignition ON (engine OFF) for diagnostics

2. **Confirmation:**
   - Always read confirmation prompts carefully
   - Understand what the command will do
   - When in doubt, decline and research more

3. **Documentation:**
   - Session logs are saved in `logs/`
   - Review logs if something unexpected happens
   - Share logs when asking for help

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to ELM327"

**Solutions:**
1. Check COM port is correct:
   ```bash
   # Windows: Device Manager > Ports
   # Linux: ls /dev/ttyUSB*
   ```
2. Verify ELM327 is powered on
3. Ensure vehicle ignition is ON
4. Try different baud rate in config

### No Response from Module

**Problem:** "No response from module"

**Solutions:**
1. Verify module exists in your vehicle
2. Check module address is correct
3. Try standard OBD2 address (7E0) first
4. Some modules require specific diagnostic mode

### Web Research Fails

**Problem:** "No procedures found online"

**Solutions:**
1. Use manual consultation mode
2. Check service manual for your vehicle
3. Try related vehicle models
4. Search vehicle-specific forums

### Incorrect DTC Descriptions

**Problem:** DTC code shown but description is wrong

**Solutions:**
1. Update vehicle profile in `knowledge_base/`
2. Add correct description to YAML file
3. Manufacturer-specific codes may vary

## Advanced Features

### Multi-Vehicle Support

The agent supports multiple vehicles:

```bash
# Specify vehicle
python main.py --port COM3 --vehicle Ford_Escape_2008

# Switch vehicles in session
🔧 > read VIN
[Agent identifies vehicle automatically]
```

### Module Discovery

Discover unknown modules:

```bash
🔧 > scan all modules
[Agent scans CAN bus and identifies active modules]
```

### Event-Driven Capture

Identify CAN IDs for specific actions:

```bash
🔧 > capture event "press brake pedal"
[Agent captures CAN traffic during action]
```

### Script Generation

Generate custom scripts for research:

```bash
🔧 > generate script to parse DTC database
[Agent creates and executes Python script]
```

## Diagnostic Reports

After each session, the agent can generate reports:

```bash
🔧 > generate report
```

Reports include:
- Vehicle information
- Modules scanned
- DTCs found
- Commands executed
- Recommendations
- Links to resources

Export formats:
- Markdown (.md)
- JSON (.json)

## Getting Help

### Built-in Help

```bash
🔧 > help
```

### Log Files

Check logs for detailed information:
- `logs/agent.log` - Agent operations
- `logs/session_YYYYMMDD_HHMMSS.jsonl` - Session audit trail

### Community Support

- GitHub Issues: Report bugs or request features
- Discussions: Ask questions and share experiences
- Wiki: Additional documentation and guides

## Tips for Best Results

1. **Be Specific:** "check HVAC codes" is better than "check codes"
2. **Use Module Names:** HVAC, ABS, PCM, TCM, BCM, etc.
3. **Confirm Carefully:** Read confirmation prompts before accepting
4. **Document Findings:** The agent learns from successful procedures
5. **Start Simple:** Try standard OBD2 before manufacturer-specific
6. **Keep Updated:** Update knowledge base with new findings

## Limitations

- **Phase 1 Focus:** Optimized for Ford Escape 2008, but supports other vehicles
- **Read-Only Bias:** Prioritizes safe read operations
- **Manual Consultation:** Some procedures require service manual
- **Module Support:** Not all modules respond to standard commands
- **Manufacturer Variations:** Protocols vary by manufacturer

## Next Steps

- Read [Developer Guide](DEVELOPER_GUIDE.md) to extend the agent
- Explore [Toolkit Documentation](../toolkit/README.md) for script details
- Check [Knowledge Base Format](../knowledge_base/README.md) for data structure
- Review example configurations in `examples/`

## Safety Disclaimer

This tool is for diagnostic purposes only. Always:
- Follow vehicle manufacturer guidelines
- Consult qualified technicians for repairs
- Understand commands before executing
- Use at your own risk

The agent includes safety mechanisms, but you are responsible for all actions taken with your vehicle.
