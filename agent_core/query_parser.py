"""
Natural Language Query Parser

Extracts structured intent from user queries for vehicle diagnostics.
"""

import re
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class Action(Enum):
    """Diagnostic actions"""
    CHECK = "check"
    READ = "read"
    CLEAR = "clear"
    SCAN = "scan"
    TEST = "test"
    ACTUATE = "actuate"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Structured intent extracted from query"""
    action: Action
    module: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    raw_query: str = ""
    confidence: float = 1.0
    ambiguous: bool = False
    clarification_needed: List[str] = None
    
    def __post_init__(self):
        if self.clarification_needed is None:
            self.clarification_needed = []
    
    def __repr__(self):
        parts = [f"Intent(action={self.action.value}"]
        if self.module:
            parts.append(f"module={self.module}")
        if self.vehicle_make:
            parts.append(f"vehicle={self.vehicle_make} {self.vehicle_model} {self.vehicle_year}")
        return ", ".join(parts) + ")"


class QueryParser:
    """
    Parse natural language queries into structured intents
    
    Examples:
    - "check hvac codes on my vehicle" → Action.CHECK, module=HVAC
    - "read DTC from ABS" → Action.READ, module=ABS
    - "scan my 2008 Ford Escape" → Action.SCAN, vehicle info
    - "clear codes" → Action.CLEAR, ambiguous (no module)
    """
    
    # Action keywords mapping
    ACTION_KEYWORDS = {
        Action.CHECK: ["check", "inspect", "look", "show", "display", "what", "any"],
        Action.READ: ["read", "get", "retrieve", "pull", "fetch"],
        Action.CLEAR: ["clear", "erase", "delete", "remove", "reset"],
        Action.SCAN: ["scan", "diagnose", "diagnostic", "full scan"],
        Action.TEST: ["test", "verify", "validate"],
        Action.ACTUATE: ["actuate", "activate", "trigger", "move", "operate"]
    }
    
    # Module name variations
    MODULE_KEYWORDS = {
        "HVAC": ["hvac", "climate", "ac", "air conditioning", "heater", "heating", "ventilation"],
        "ABS": ["abs", "anti-lock", "antilock", "brake", "brakes"],
        "PCM": ["pcm", "powertrain", "engine", "ecu", "ecm"],
        "BCM": ["bcm", "body", "body control"],
        "IPC": ["ipc", "instrument", "cluster", "dashboard", "gauges"],
        "TCM": ["tcm", "transmission"],
        "SRS": ["srs", "airbag", "airbags", "safety"]
    }
    
    # Common DTC-related terms
    DTC_TERMS = ["dtc", "code", "codes", "trouble code", "fault", "error"]
    
    # Vehicle make patterns
    MAKES = ["ford", "chevrolet", "chevy", "toyota", "honda", "nissan", "mazda", 
             "mercury", "lincoln", "dodge", "chrysler", "jeep", "gm"]
    
    def __init__(self):
        self.last_vehicle_info = {}
    
    def parse(self, query: str) -> ParsedIntent:
        """
        Parse natural language query into structured intent
        
        Args:
            query: User's natural language query
            
        Returns:
            ParsedIntent object with extracted information
        """
        query_lower = query.lower().strip()
        
        intent = ParsedIntent(
            action=Action.UNKNOWN,
            raw_query=query
        )
        
        # Extract action
        intent.action = self._extract_action(query_lower)
        
        # Extract module
        intent.module = self._extract_module(query_lower)
        
        # Extract vehicle information
        make, model, year = self._extract_vehicle_info(query_lower)
        intent.vehicle_make = make
        intent.vehicle_model = model
        intent.vehicle_year = year
        
        # Check for ambiguity
        intent.ambiguous, intent.clarification_needed = self._check_ambiguity(intent)
        
        # Calculate confidence
        intent.confidence = self._calculate_confidence(intent)
        
        return intent
    
    def _extract_action(self, query: str) -> Action:
        """
        Extract action from query
        
        Args:
            query: Lowercase query string
            
        Returns:
            Action enum value
        """
        # Check for action keywords
        for action, keywords in self.ACTION_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query):
                    return action
        
        # Default: if query mentions DTCs/codes, assume READ
        for term in self.DTC_TERMS:
            if term in query:
                return Action.READ
        
        return Action.UNKNOWN
    
    def _extract_module(self, query: str) -> Optional[str]:
        """
        Extract module name from query
        
        Args:
            query: Lowercase query string
            
        Returns:
            Module name or None
        """
        for module, keywords in self.MODULE_KEYWORDS.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query):
                    return module
        
        return None
    
    def _extract_vehicle_info(self, query: str) -> tuple[Optional[str], Optional[str], Optional[int]]:
        """
        Extract vehicle make, model, and year from query
        
        Args:
            query: Lowercase query string
            
        Returns:
            Tuple of (make, model, year)
        """
        make = None
        model = None
        year = None
        
        # Extract make
        for m in self.MAKES:
            pattern = r'\b' + re.escape(m) + r'\b'
            if re.search(pattern, query):
                make = m.title()
                break
        
        # Extract year (4-digit number between 1990-2030)
        year_match = re.search(r'\b(19[9]\d|20[0-3]\d)\b', query)
        if year_match:
            year = int(year_match.group(1))
        
        # Extract model (common models)
        models = {
            "escape": "Escape",
            "fusion": "Fusion",
            "focus": "Focus",
            "f-150": "F-150",
            "f150": "F-150",
            "mustang": "Mustang",
            "explorer": "Explorer",
            "edge": "Edge",
            "mariner": "Mariner",
            "tribute": "Tribute"
        }
        
        for model_key, model_name in models.items():
            pattern = r'\b' + re.escape(model_key) + r'\b'
            if re.search(pattern, query):
                model = model_name
                break
        
        return make, model, year
    
    def _check_ambiguity(self, intent: ParsedIntent) -> tuple[bool, List[str]]:
        """
        Check if intent is ambiguous and needs clarification
        
        Args:
            intent: ParsedIntent object
            
        Returns:
            Tuple of (is_ambiguous, clarification_questions)
        """
        clarifications = []
        
        # Check if action is unknown
        if intent.action == Action.UNKNOWN:
            clarifications.append("What would you like to do? (check, read, clear, scan, test)")
        
        # Check if module is missing for actions that need it
        if intent.action in [Action.CHECK, Action.READ, Action.CLEAR, Action.ACTUATE]:
            if not intent.module:
                clarifications.append("Which module? (HVAC, ABS, PCM, BCM, etc.)")
        
        # Check if vehicle info is missing for scan
        if intent.action == Action.SCAN:
            if not intent.vehicle_make or not intent.vehicle_model or not intent.vehicle_year:
                missing = []
                if not intent.vehicle_make:
                    missing.append("make")
                if not intent.vehicle_model:
                    missing.append("model")
                if not intent.vehicle_year:
                    missing.append("year")
                clarifications.append(f"What is your vehicle's {', '.join(missing)}?")
        
        is_ambiguous = len(clarifications) > 0
        return is_ambiguous, clarifications
    
    def _calculate_confidence(self, intent: ParsedIntent) -> float:
        """
        Calculate confidence score for parsed intent
        
        Args:
            intent: ParsedIntent object
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 1.0
        
        # Reduce confidence if action is unknown
        if intent.action == Action.UNKNOWN:
            confidence *= 0.3
        
        # Reduce confidence if ambiguous
        if intent.ambiguous:
            confidence *= 0.6
        
        # Increase confidence if module is specified
        if intent.module:
            confidence = min(1.0, confidence + 0.2)
        
        # Increase confidence if vehicle info is complete
        if intent.vehicle_make and intent.vehicle_model and intent.vehicle_year:
            confidence = min(1.0, confidence + 0.1)
        
        return round(confidence, 2)
    
    def generate_clarification_prompt(self, intent: ParsedIntent) -> str:
        """
        Generate user-friendly clarification prompt
        
        Args:
            intent: ParsedIntent object with clarification needs
            
        Returns:
            Clarification prompt string
        """
        if not intent.ambiguous:
            return ""
        
        prompt = "I need some clarification:\n"
        for i, question in enumerate(intent.clarification_needed, 1):
            prompt += f"{i}. {question}\n"
        
        return prompt.strip()


if __name__ == '__main__':
    # Test query parser
    parser = QueryParser()
    
    test_queries = [
        "check hvac codes on my vehicle",
        "read DTC from ABS",
        "scan my 2008 Ford Escape",
        "clear codes",
        "test HVAC blend door actuator",
        "what codes does my car have",
        "actuate HVAC door",
        "check engine light on my 2008 escape"
    ]
    
    print("Testing Query Parser:\n")
    for query in test_queries:
        intent = parser.parse(query)
        print(f"Query: \"{query}\"")
        print(f"  {intent}")
        print(f"  Confidence: {intent.confidence}")
        if intent.ambiguous:
            print(f"  Clarification needed:")
            for q in intent.clarification_needed:
                print(f"    - {q}")
        print()
