# Web Research Module - Implementation Summary

## Overview

Completed Task 5 from the AI Vehicle Diagnostic Agent spec: Web Research Module Implementation.

## What Was Implemented

### 1. AI-Assisted Web Search (`toolkit/web_research/ai_search.py`)

**Core Features:**
- Constructs optimized search queries for diagnostic procedures
- Extracts OBD2/UDS commands from text (hex patterns)
- Classifies sources by quality (manual > database > forum)
- Ranks search results by relevance and source quality
- Supports Ford cross-reference searches (related models)

**Key Classes:**
- `AIAssistedSearch`: Main search orchestrator
- `SearchResult`: Represents a search result with metadata
- `ExtractedCommand`: Represents an extracted OBD2/UDS command

**Search Query Construction:**
```python
# Example: "2008 Ford Escape transmission read temperature OBD2 TCM PCM CAN UDS"
query = search.construct_search_query(
    make="Ford",
    model="Escape", 
    year=2008,
    module="transmission",
    action="read temperature"
)
```

**Command Extraction:**
- Detects hex patterns: `22 1E 1C`, `221E1C`, `0x221E1C`
- Extracts context and descriptions
- Calculates confidence scores
- Deduplicates and ranks by confidence

**Source Classification:**
- `manual`: Official service manuals (priority 1.0)
- `database`: Repair databases like AllData (priority 0.8)
- `forum`: Community forums (priority 0.5)
- `unknown`: Unknown sources (priority 0.3)

**Ford Cross-Reference:**
- Searches related Ford models from same era
- Example: Escape → Fusion, Focus, Mazda Tribute
- Includes ±2 year range (2005-2012 era)

### 2. User Fallback Mode (`toolkit/web_research/user_fallback.py`)

**Core Features:**
- Generates user-friendly search instructions
- Prompts user to search manually and paste results
- Parses user-provided text for commands
- Extracts URLs from pasted content
- Interactive session management

**Key Classes:**
- `UserFallbackSearch`: Manages user interaction
- `UserSearchSession`: Stores session data

**User Workflow:**
1. System generates search query and instructions
2. User searches Google manually
3. User pastes relevant text from web pages
4. System extracts commands and URLs
5. System displays results and asks for confirmation

**Example Output:**
```
╔══════════════════════════════════════════════════════════════════════╗
║                    WEB RESEARCH NEEDED                               ║
╚══════════════════════════════════════════════════════════════════════╝

I need your help to find diagnostic information for:
  Vehicle: 2008 Ford Escape
  Module: transmission
  Action: read temperature

STEP 1: Search Google
────────────────────────────────────────────────────────────────────────
Copy and paste this search query into Google:

  2008 Ford Escape transmission read temperature OBD2 TCM PCM CAN UDS

STEP 2: Look for These Sources (in order of preference)
────────────────────────────────────────────────────────────────────────
  1. Official service manuals (best)
  2. Repair databases (AllData, Mitchell, etc.)
  3. Technical forums (FordTechMazdaVolvo, etc.)
  4. Community posts (Reddit, StackExchange)
```

## Requirements Satisfied

### Requirement 3: Web Research for Unknown Procedures
- ✓ 3.1: Search for manufacturer service manuals and repair guides
- ✓ 3.2: Use vehicle make/model/year and module name as search terms
- ✓ 3.3: Search related Ford models from same era
- ✓ 3.4: Extract OBD2/UDS command sequences from search results
- ✓ 3.5: Prioritize official manufacturer documentation over forum posts

### Requirement 5: Interactive Clarification and Manual Consultation
- ✓ 5.1: Ask user if they have access to service manual
- ✓ 5.2: Guide user on what information to look for

## Usage Examples

### Example 1: AI-Assisted Search (with AI backend)

```python
from toolkit.web_research.ai_search import AIAssistedSearch

search = AIAssistedSearch(ai_backend=my_ai_backend)

# Perform search
results, commands = await search.search(
    make="Ford",
    model="Escape",
    year=2008,
    module="transmission",
    action="read temperature",
    include_cross_reference=True
)

# Display results
for result in results:
    print(f"{result.title} ({result.source_type})")
    print(f"  {result.url}")

# Display extracted commands
for cmd in commands:
    print(f"Command: {cmd.command_hex}")
    print(f"  {cmd.description} (confidence: {cmd.confidence:.0%})")
```

### Example 2: User Fallback Mode (no AI backend)

```python
from toolkit.web_research.user_fallback import UserFallbackSearch

fallback = UserFallbackSearch()

# Interactive session with user
session = fallback.interactive_search_session(
    make="Ford",
    model="Escape",
    year=2008,
    module="transmission",
    action="read temperature"
)

if session:
    # User provided results
    for cmd in session.extracted_commands:
        print(f"Found: {cmd.command_hex} - {cmd.description}")
```

### Example 3: Extract Commands from Text

```python
from toolkit.web_research.ai_search import AIAssistedSearch

search = AIAssistedSearch()

text = """
To read transmission temperature, send command 22 1E 1C to the PCM.
The response will be 62 1E 1C followed by the temperature data.
For turbine speed, use 221E14.
"""

commands = search.extract_commands_from_text(text)

for cmd in commands:
    print(f"{cmd.command_hex}: {cmd.description}")
    print(f"  Confidence: {cmd.confidence:.0%}")
    print(f"  Context: {cmd.context}")
```

## Integration with Agent Core

The web research module integrates with the agent core workflow:

```
User Query → Query Parser → Knowledge Lookup
                                    ↓ (not found)
                            Web Research Module
                                    ↓
                        AI Search or User Fallback
                                    ↓
                        Extract Commands & Procedures
                                    ↓
                        Document in Knowledge Base
                                    ↓
                        Execute Diagnostic Commands
```

## Design Decisions

### 1. No API Keys Required by Default
- AI backend web search is optional
- Falls back to user manual search
- User can paste results from any browser
- No Google Custom Search API needed

### 2. Flexible Command Extraction
- Supports multiple hex formats
- Handles various separators (space, dash, colon)
- Validates command length
- Extracts context for better understanding

### 3. Source Quality Ranking
- Prioritizes official documentation
- Boosts results with relevant keywords
- Considers source type and confidence
- Returns best results first

### 4. Ford-Specific Optimizations
- Cross-references related Ford models
- Searches same-era vehicles (2005-2012)
- Includes platform-sharing models (Mazda Tribute)
- Prioritizes same year, then ±2 years

## Testing

### Manual Testing
Run the example scripts:
```bash
# Test AI search
python toolkit/web_research/ai_search.py

# Test user fallback
python toolkit/web_research/user_fallback.py
```

### Unit Tests (Optional - Task 5.6)
- Test search query construction
- Test command extraction from sample text
- Test source prioritization logic
- Test Ford cross-reference generation

## Next Steps

1. **Integrate with Agent Core** (Task 9)
   - Connect web research to agent main loop
   - Use in diagnostic workflow

2. **Add to Toolkit Registry** (Task 22)
   - Register web research scripts
   - Document usage in toolkit README

3. **Test with Real Searches**
   - Try finding HVAC procedures
   - Try finding transmission procedures
   - Validate command extraction accuracy

4. **Enhance Command Extraction**
   - Add more hex patterns
   - Improve description extraction
   - Better confidence scoring

## Files Created

- `toolkit/web_research/__init__.py` - Package init
- `toolkit/web_research/ai_search.py` - AI-assisted search (370 lines)
- `toolkit/web_research/user_fallback.py` - User fallback mode (380 lines)
- `WEB_RESEARCH_MODULE_SUMMARY.md` - This file

## Dependencies

- Python 3.7+
- `re` (standard library)
- `dataclasses` (standard library)
- `typing` (standard library)
- AI backend (optional, for web search capability)

## Notes

- The module is designed to work with or without an AI backend
- User fallback mode provides full functionality without API keys
- Command extraction is robust and handles various formats
- Source prioritization ensures best results are shown first
- Ford cross-reference improves success rate for Ford vehicles

## Conclusion

Task 5 (Web Research Module) is complete. The implementation provides:
- AI-assisted web search with command extraction
- User fallback mode for manual searching
- Ford cross-reference for related models
- Source quality ranking
- No API keys required by default

The module is ready for integration with the agent core and can be tested independently.
