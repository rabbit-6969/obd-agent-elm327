"""
Diagnostic Workflow Orchestration

Implements the diagnostic workflow:
1. Identify module
2. Find procedure in knowledge base
3. Execute commands
4. Parse responses
5. Present results

Tries standard OBD-II first, falls back to manufacturer-specific protocols.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_core.toolkit_executor import ToolkitExecutor, ToolkitExecutionError
from toolkit.knowledge_management.technical_parser import TechnicalKnowledge, CommandDef
from toolkit.knowledge_management.profile_handler import VehicleProfile


class DiagnosticWorkflow:
    """
    Orchestrates diagnostic workflows
    
    Manages the complete diagnostic process from module identification
    through command execution to result presentation.
    """
    
    def __init__(
        self,
        toolkit_executor: ToolkitExecutor,
        technical_knowledge: Optional[TechnicalKnowledge] = None,
        vehicle_profile: Optional[VehicleProfile] = None
    ):
        """
        Initialize diagnostic workflow
        
        Args:
            toolkit_executor: Toolkit executor instance
            technical_knowledge: Technical knowledge base (optional)
            vehicle_profile: Vehicle profile (optional)
        """
        self.executor = toolkit_executor
        self.technical_knowledge = technical_knowledge
        self.vehicle_profile = vehicle_profile
    
    def identify_module(self, module_name: str) -> Optional[Dict[str, str]]:
        """
        Identify module and get its details
        
        Args:
            module_name: Module name (e.g., "HVAC", "PCM")
            
        Returns:
            Dictionary with module info or None if not found
        """
        if not self.technical_knowledge:
            return None
        
        module_info = self.technical_knowledge.modules.get(module_name)
        if not module_info:
            return None
        
        return {
            'name': module_info.name,
            'address': module_info.address,
            'protocol': module_info.protocol,
            'bus': module_info.bus
        }
    
    def find_procedure(
        self,
        module_name: str,
        action: str
    ) -> Optional[CommandDef]:
        """
        Find diagnostic procedure in knowledge base
        
        Args:
            module_name: Module name (e.g., "HVAC")
            action: Action to perform (e.g., "READ_DTC", "CLEAR_DTC")
            
        Returns:
            CommandDef object or None if not found
        """
        if not self.technical_knowledge:
            return None
        
        # Construct command ID
        command_id = f"{module_name}.{action}"
        
        # Look up command
        command = self.technical_knowledge.commands.get(command_id)
        return command
    
    def execute_diagnostic(
        self,
        port: str,
        module_name: str,
        action: str,
        use_standard_obd: bool = True
    ) -> Dict[str, Any]:
        """
        Execute diagnostic workflow
        
        Workflow:
        1. Identify module
        2. Find procedure
        3. Execute commands
        4. Parse responses
        5. Present results
        
        Args:
            port: Serial port for ELM327
            module_name: Module to diagnose
            action: Action to perform (READ_DTC, CLEAR_DTC, etc.)
            use_standard_obd: Try standard OBD-II first (default: True)
            
        Returns:
            Dictionary with diagnostic results
        """
        result = {
            'success': False,
            'module': module_name,
            'action': action,
            'protocol_used': None,
            'data': None,
            'error': None
        }
        
        try:
            # Step 1: Identify module
            module_info = self.identify_module(module_name)
            if not module_info:
                result['error'] = f"Module '{module_name}' not found in knowledge base"
                return result
            
            result['module_info'] = module_info
            
            # Step 2: Find procedure
            procedure = self.find_procedure(module_name, action)
            if not procedure:
                result['error'] = f"Procedure '{action}' not found for module '{module_name}'"
                return result
            
            result['procedure'] = {
                'id': procedure.id,
                'mode': procedure.mode,
                'pid': procedure.pid,
                'data': procedure.data
            }
            
            # Step 3: Execute commands
            if use_standard_obd:
                # Try standard OBD-II first
                exec_result = self._execute_standard_obd(
                    port,
                    module_info,
                    procedure,
                    action
                )
                
                if exec_result['success']:
                    result.update(exec_result)
                    result['protocol_used'] = 'standard_obd'
                    return result
                
                # Standard OBD failed, try manufacturer-specific
                result['standard_obd_failed'] = True
                result['standard_obd_error'] = exec_result.get('error')
            
            # Try manufacturer-specific protocol
            exec_result = self._execute_manufacturer_specific(
                port,
                module_info,
                procedure,
                action
            )
            
            if exec_result['success']:
                result.update(exec_result)
                result['protocol_used'] = 'manufacturer_specific'
            else:
                result['error'] = exec_result.get('error', 'All protocols failed')
            
            return result
        
        except Exception as e:
            result['error'] = f"Diagnostic workflow error: {e}"
            return result
    
    def _execute_standard_obd(
        self,
        port: str,
        module_info: Dict,
        procedure: CommandDef,
        action: str
    ) -> Dict[str, Any]:
        """
        Execute using standard OBD-II protocol
        
        Args:
            port: Serial port
            module_info: Module information
            procedure: Command definition
            action: Action to perform
            
        Returns:
            Execution result dictionary
        """
        result = {
            'success': False,
            'data': None,
            'error': None
        }
        
        try:
            # Map action to toolkit script
            if action == 'READ_DTC':
                exec_result = self.executor.read_dtc(
                    port=port,
                    module=module_info['name'],
                    address=module_info['address']
                )
            elif action == 'CLEAR_DTC':
                exec_result = self.executor.clear_dtc(
                    port=port,
                    module=module_info['name'],
                    address=module_info['address']
                )
            else:
                result['error'] = f"Action '{action}' not supported for standard OBD"
                return result
            
            # Check if execution succeeded
            if exec_result.get('success'):
                result['success'] = True
                result['data'] = exec_result
            else:
                result['error'] = exec_result.get('error', 'Unknown error')
            
            return result
        
        except ToolkitExecutionError as e:
            result['error'] = str(e)
            return result
    
    def _execute_manufacturer_specific(
        self,
        port: str,
        module_info: Dict,
        procedure: CommandDef,
        action: str
    ) -> Dict[str, Any]:
        """
        Execute using manufacturer-specific protocol
        
        Args:
            port: Serial port
            module_info: Module information
            procedure: Command definition
            action: Action to perform
            
        Returns:
            Execution result dictionary
        """
        result = {
            'success': False,
            'data': None,
            'error': 'Manufacturer-specific protocols not yet implemented'
        }
        
        # TODO: Implement manufacturer-specific protocol execution
        # This would use UDS (Unified Diagnostic Services) or other
        # manufacturer-specific protocols
        
        return result
    
    def parse_dtc_response(
        self,
        response: str,
        module_name: str
    ) -> List[Dict[str, str]]:
        """
        Parse DTC response and enrich with descriptions
        
        Args:
            response: Raw DTC response
            module_name: Module name for context
            
        Returns:
            List of DTC dictionaries with codes and descriptions
        """
        dtcs = []
        
        # TODO: Implement DTC parsing logic
        # This would parse the raw response and extract DTC codes
        
        # Enrich with descriptions from vehicle profile
        if self.vehicle_profile:
            for dtc in dtcs:
                code = dtc.get('code')
                if code:
                    dtc_info = self.vehicle_profile.dtc_descriptions.get(code)
                    if dtc_info:
                        dtc['description'] = dtc_info.description
                        dtc['severity'] = dtc_info.severity
                        dtc['common_causes'] = dtc_info.common_causes
        
        return dtcs
    
    def present_results(
        self,
        diagnostic_result: Dict[str, Any],
        format: str = 'text'
    ) -> str:
        """
        Present diagnostic results in human-readable format
        
        Args:
            diagnostic_result: Result from execute_diagnostic()
            format: Output format ('text', 'json', 'markdown')
            
        Returns:
            Formatted result string
        """
        if format == 'json':
            import json
            return json.dumps(diagnostic_result, indent=2)
        
        if format == 'markdown':
            return self._format_markdown(diagnostic_result)
        
        # Default: text format
        return self._format_text(diagnostic_result)
    
    def _format_text(self, result: Dict[str, Any]) -> str:
        """Format results as plain text"""
        lines = []
        
        lines.append(f"Module: {result['module']}")
        lines.append(f"Action: {result['action']}")
        
        if result['success']:
            lines.append(f"Status: ✓ Success")
            lines.append(f"Protocol: {result['protocol_used']}")
            
            # Format data based on action
            data = result.get('data', {})
            if result['action'] == 'READ_DTC':
                dtcs = data.get('dtcs', [])
                count = data.get('count', 0)
                
                if count > 0:
                    lines.append(f"\nFound {count} DTC(s):")
                    for dtc in dtcs:
                        lines.append(f"  • {dtc.get('code')}: {dtc.get('description', 'No description')}")
                else:
                    lines.append("\nNo DTCs found")
            
            elif result['action'] == 'CLEAR_DTC':
                if data.get('cleared'):
                    lines.append("\nDTCs cleared successfully")
        else:
            lines.append(f"Status: ✗ Failed")
            lines.append(f"Error: {result.get('error')}")
        
        return "\n".join(lines)
    
    def _format_markdown(self, result: Dict[str, Any]) -> str:
        """Format results as markdown"""
        lines = []
        
        lines.append(f"# Diagnostic Results")
        lines.append(f"")
        lines.append(f"**Module:** {result['module']}")
        lines.append(f"**Action:** {result['action']}")
        
        if result['success']:
            lines.append(f"**Status:** ✓ Success")
            lines.append(f"**Protocol:** {result['protocol_used']}")
            
            # Format data
            data = result.get('data', {})
            if result['action'] == 'READ_DTC':
                dtcs = data.get('dtcs', [])
                count = data.get('count', 0)
                
                lines.append(f"")
                lines.append(f"## DTCs Found: {count}")
                
                if count > 0:
                    lines.append(f"")
                    for dtc in dtcs:
                        lines.append(f"- **{dtc.get('code')}**: {dtc.get('description', 'No description')}")
        else:
            lines.append(f"**Status:** ✗ Failed")
            lines.append(f"**Error:** {result.get('error')}")
        
        return "\n".join(lines)


def main():
    """Test diagnostic workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test diagnostic workflow')
    parser.add_argument('--port', default='COM3', help='Serial port')
    parser.add_argument('--module', required=True, help='Module name')
    parser.add_argument('--action', required=True, help='Action (READ_DTC, CLEAR_DTC)')
    parser.add_argument('--format', choices=['text', 'json', 'markdown'], default='text')
    
    args = parser.parse_args()
    
    # Initialize workflow
    executor = ToolkitExecutor()
    workflow = DiagnosticWorkflow(executor)
    
    # Execute diagnostic
    result = workflow.execute_diagnostic(
        port=args.port,
        module_name=args.module,
        action=args.action
    )
    
    # Present results
    output = workflow.present_results(result, format=args.format)
    print(output)
    
    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
