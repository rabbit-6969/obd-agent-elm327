"""
Technical Data Format Parser

Fast parser for compact technical data format (.dat files).
Designed for < 50ms file parsing and < 5ms single lookup.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class ModuleInfo:
    """Vehicle module information"""
    name: str
    address: str
    protocol: str
    bus: str
    
    def __repr__(self):
        return f"Module({self.name}, addr={self.address}, proto={self.protocol}, bus={self.bus})"


@dataclass
class CommandDef:
    """OBD command definition"""
    id: str
    mode: str
    pid: Optional[str] = None
    data: Optional[str] = None
    response_pattern: str = ""
    
    def __repr__(self):
        parts = [f"Command({self.id}, mode={self.mode}"]
        if self.pid:
            parts.append(f"pid={self.pid}")
        if self.data:
            parts.append(f"data={self.data}")
        return ", ".join(parts) + ")"


@dataclass
class DTCRule:
    """DTC parsing rule"""
    code: str
    byte_range: str
    bit_range: str
    calculation: str
    
    def __repr__(self):
        return f"DTCRule({self.code}, bytes={self.byte_range}, bits={self.bit_range})"


@dataclass
class ResponseRule:
    """Response parsing rule"""
    cmd_id: str
    pattern: str
    extract: List[str] = field(default_factory=list)
    calculations: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return f"ResponseRule({self.cmd_id}, extract={self.extract})"


@dataclass
class BitMapping:
    """Bit field mapping"""
    field: str
    byte_pos: int
    bit_range: str
    meanings: Dict[str, str] = field(default_factory=dict)
    
    def __repr__(self):
        return f"BitMapping({self.field}, byte={self.byte_pos}, bit={self.bit_range})"


@dataclass
class TechnicalKnowledge:
    """Complete technical knowledge from .dat file"""
    modules: Dict[str, ModuleInfo] = field(default_factory=dict)
    commands: Dict[str, CommandDef] = field(default_factory=dict)
    dtc_rules: Dict[str, DTCRule] = field(default_factory=dict)
    response_rules: Dict[str, ResponseRule] = field(default_factory=dict)
    bit_mappings: Dict[str, BitMapping] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __repr__(self):
        return (f"TechnicalKnowledge("
                f"modules={len(self.modules)}, "
                f"commands={len(self.commands)}, "
                f"dtc_rules={len(self.dtc_rules)})")


class TechnicalParserError(Exception):
    """Technical data parsing error"""
    pass


class TechnicalDataParser:
    """
    Fast parser for technical data format
    
    Format examples:
    - Module: M:HVAC A:7A0 P:CAN B:HS
    - Command: C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
    - DTC: DTC:P1632 B:0-1 BITS:0-15 CALC:hex
    - Response: R:READ_DTC PATTERN:43([0-9A-F]{4})+ EXTRACT:dtc_hex
    - BitMap: BM:monitor_status BYTE:1 BIT:0 MEANING:0=incomplete,1=complete
    """
    
    # Regex patterns for parsing
    KEY_VALUE_PATTERN = re.compile(r'(\w+):([^\s]+)')
    
    def __init__(self):
        self.knowledge = TechnicalKnowledge()
    
    def parse_file(self, filepath: str) -> TechnicalKnowledge:
        """
        Parse entire technical data file
        
        Args:
            filepath: Path to .dat file
            
        Returns:
            TechnicalKnowledge object
            
        Raises:
            TechnicalParserError: If file cannot be parsed
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise TechnicalParserError(f"File not found: {filepath}")
        
        self.knowledge = TechnicalKnowledge()
        line_num = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line_num += 1
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        # Extract metadata from comments
                        if line.startswith('# Version:'):
                            self.knowledge.metadata['version'] = line.split(':', 1)[1].strip()
                        elif line.startswith('# Generated:'):
                            self.knowledge.metadata['generated'] = line.split(':', 1)[1].strip()
                        continue
                    
                    # Parse based on line type
                    try:
                        if line.startswith('M:'):
                            self._parse_module_line(line)
                        elif line.startswith('C:'):
                            self._parse_command_line(line)
                        elif line.startswith('DTC:'):
                            self._parse_dtc_line(line)
                        elif line.startswith('R:'):
                            self._parse_response_line(line)
                        elif line.startswith('BM:'):
                            self._parse_bitmapping_line(line)
                        else:
                            # Unknown line type, skip silently for forward compatibility
                            pass
                    except Exception as e:
                        raise TechnicalParserError(
                            f"Error parsing line {line_num}: {line}\n{str(e)}"
                        )
        
        except IOError as e:
            raise TechnicalParserError(f"Error reading file: {e}")
        
        return self.knowledge
    
    def _parse_key_values(self, line: str) -> Dict[str, str]:
        """
        Parse key:value pairs from line
        
        Args:
            line: Line with space-separated key:value pairs
            
        Returns:
            Dictionary of key-value pairs
        """
        matches = self.KEY_VALUE_PATTERN.findall(line)
        return {key: value for key, value in matches}
    
    def _parse_module_line(self, line: str):
        """
        Parse module definition line
        
        Format: M:HVAC A:7A0 P:CAN B:HS
        """
        kv = self._parse_key_values(line)
        
        if 'M' not in kv:
            raise TechnicalParserError("Module line missing M: field")
        if 'A' not in kv:
            raise TechnicalParserError("Module line missing A: field")
        
        module = ModuleInfo(
            name=kv['M'],
            address=kv['A'],
            protocol=kv.get('P', 'CAN'),
            bus=kv.get('B', 'HS')
        )
        
        self.knowledge.modules[module.name] = module
    
    def _parse_command_line(self, line: str):
        """
        Parse command definition line
        
        Format: C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
        Format: C:HVAC.READ_LIVE M:01 PID:05 R:41 05 [0-9A-F]{2}
        Format: C:HVAC.ACTUATE M:31 PID:01 D:FF R:71 01
        """
        kv = self._parse_key_values(line)
        
        if 'C' not in kv:
            raise TechnicalParserError("Command line missing C: field")
        if 'M' not in kv:
            raise TechnicalParserError("Command line missing M: field")
        
        # Extract response pattern (everything after R:)
        response_pattern = ""
        if 'R:' in line:
            response_pattern = line.split('R:', 1)[1].strip()
        
        command = CommandDef(
            id=kv['C'],
            mode=kv['M'],
            pid=kv.get('PID'),
            data=kv.get('D'),
            response_pattern=response_pattern
        )
        
        self.knowledge.commands[command.id] = command
    
    def _parse_dtc_line(self, line: str):
        """
        Parse DTC rule line
        
        Format: DTC:P1632 B:0-1 BITS:0-15 CALC:hex
        """
        kv = self._parse_key_values(line)
        
        if 'DTC' not in kv:
            raise TechnicalParserError("DTC line missing DTC: field")
        
        rule = DTCRule(
            code=kv['DTC'],
            byte_range=kv.get('B', '0-1'),
            bit_range=kv.get('BITS', '0-15'),
            calculation=kv.get('CALC', 'hex')
        )
        
        self.knowledge.dtc_rules[rule.code] = rule
    
    def _parse_response_line(self, line: str):
        """
        Parse response rule line
        
        Format: R:READ_DTC PATTERN:43([0-9A-F]{4})+ EXTRACT:dtc_hex
        Format: R:LIVE_TEMP PATTERN:41 05 ([0-9A-F]{2}) EXTRACT:temp_hex CALC:(hex-40)
        """
        kv = self._parse_key_values(line)
        
        if 'R' not in kv:
            raise TechnicalParserError("Response line missing R: field")
        
        # Extract fields that may contain commas
        extract_fields = []
        if 'EXTRACT' in kv:
            extract_fields = [f.strip() for f in kv['EXTRACT'].split(',')]
        
        calc_fields = []
        if 'CALC' in kv:
            calc_fields = [f.strip() for f in kv['CALC'].split(',')]
        
        rule = ResponseRule(
            cmd_id=kv['R'],
            pattern=kv.get('PATTERN', ''),
            extract=extract_fields,
            calculations=calc_fields
        )
        
        self.knowledge.response_rules[rule.cmd_id] = rule
    
    def _parse_bitmapping_line(self, line: str):
        """
        Parse bit mapping line
        
        Format: BM:monitor_status BYTE:1 BIT:0 MEANING:0=incomplete,1=complete
        """
        kv = self._parse_key_values(line)
        
        if 'BM' not in kv:
            raise TechnicalParserError("BitMapping line missing BM: field")
        
        # Parse meanings
        meanings = {}
        if 'MEANING' in kv:
            meaning_str = kv['MEANING']
            for pair in meaning_str.split(','):
                if '=' in pair:
                    val, desc = pair.split('=', 1)
                    meanings[val.strip()] = desc.strip()
        
        mapping = BitMapping(
            field=kv['BM'],
            byte_pos=int(kv.get('BYTE', '0')),
            bit_range=kv.get('BIT', '0'),
            meanings=meanings
        )
        
        self.knowledge.bit_mappings[mapping.field] = mapping
    
    def serialize_module(self, module: ModuleInfo) -> str:
        """
        Serialize module to compact format
        
        Args:
            module: ModuleInfo object
            
        Returns:
            Compact format string
        """
        return f"M:{module.name} A:{module.address} P:{module.protocol} B:{module.bus}"
    
    def serialize_command(self, command: CommandDef) -> str:
        """
        Serialize command to compact format
        
        Args:
            command: CommandDef object
            
        Returns:
            Compact format string
        """
        parts = [f"C:{command.id}", f"M:{command.mode}"]
        
        if command.pid:
            parts.append(f"PID:{command.pid}")
        if command.data:
            parts.append(f"D:{command.data}")
        if command.response_pattern:
            parts.append(f"R:{command.response_pattern}")
        
        return " ".join(parts)
    
    def serialize_dtc_rule(self, rule: DTCRule) -> str:
        """
        Serialize DTC rule to compact format
        
        Args:
            rule: DTCRule object
            
        Returns:
            Compact format string
        """
        return (f"DTC:{rule.code} B:{rule.byte_range} "
                f"BITS:{rule.bit_range} CALC:{rule.calculation}")
    
    def serialize_response_rule(self, rule: ResponseRule) -> str:
        """
        Serialize response rule to compact format
        
        Args:
            rule: ResponseRule object
            
        Returns:
            Compact format string
        """
        parts = [f"R:{rule.cmd_id}"]
        
        if rule.pattern:
            parts.append(f"PATTERN:{rule.pattern}")
        if rule.extract:
            parts.append(f"EXTRACT:{','.join(rule.extract)}")
        if rule.calculations:
            parts.append(f"CALC:{','.join(rule.calculations)}")
        
        return " ".join(parts)
    
    def serialize_bit_mapping(self, mapping: BitMapping) -> str:
        """
        Serialize bit mapping to compact format
        
        Args:
            mapping: BitMapping object
            
        Returns:
            Compact format string
        """
        meaning_str = ','.join(f"{k}={v}" for k, v in mapping.meanings.items())
        return (f"BM:{mapping.field} BYTE:{mapping.byte_pos} "
                f"BIT:{mapping.bit_range} MEANING:{meaning_str}")


def load_technical_data(filepath: str) -> TechnicalKnowledge:
    """
    Convenience function to load technical data
    
    Args:
        filepath: Path to .dat file
        
    Returns:
        TechnicalKnowledge object
    """
    parser = TechnicalDataParser()
    return parser.parse_file(filepath)


if __name__ == '__main__':
    # Test parser with example data
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            knowledge = load_technical_data(filepath)
            print(f"✓ Parsed {filepath}")
            print(f"  Modules: {len(knowledge.modules)}")
            print(f"  Commands: {len(knowledge.commands)}")
            print(f"  DTC Rules: {len(knowledge.dtc_rules)}")
            print(f"  Response Rules: {len(knowledge.response_rules)}")
            print(f"  Bit Mappings: {len(knowledge.bit_mappings)}")
            
            if knowledge.modules:
                print("\n  Sample modules:")
                for name, module in list(knowledge.modules.items())[:3]:
                    print(f"    {module}")
            
            if knowledge.commands:
                print("\n  Sample commands:")
                for cmd_id, command in list(knowledge.commands.items())[:3]:
                    print(f"    {command}")
        
        except TechnicalParserError as e:
            print(f"✗ Parse error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python technical_parser.py <file.dat>")
