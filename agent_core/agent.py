"""
AI Vehicle Diagnostic Agent - Main Orchestration

Main agent loop that coordinates query parsing, knowledge lookup,
toolkit execution, and result presentation.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_core.query_parser import QueryParser, ParsedIntent, Action
from agent_core.toolkit_executor import ToolkitExecutor, ToolkitExecutionError
from toolkit.knowledge_management.technical_parser import load_technical_data, TechnicalKnowledge
from toolkit.knowledge_management.profile_handler import load_vehicle_profile, VehicleProfile
from config.config_loader import load_config, AgentConfig


class DiagnosticAgent:
    """
    Main AI Vehicle Diagnostic Agent
    
    Orchestrates the diagnostic workflow:
    1. Parse user query
    2. Look up knowledge
    3. Execute toolkit scripts
    4. Present results
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize diagnostic agent
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.query_parser = QueryParser()
        self.toolkit_executor = ToolkitExecutor()
        self.technical_knowledge: Optional[TechnicalKnowledge] = None
        self.vehicle_profile: Optional[VehicleProfile] = None
        
        # Session state
        self.current_vehicle = None
        self.session_history = []
        
        print("AI Vehicle Diagnostic Agent initialized")
        print(f"Primary AI backend: {self.config.ai_backend.primary}")
        print(f"Vehicle port: {self.config.vehicle.port}")
    
    def load_vehicle_knowledge(self, make: str, model: str, year: int) -> bool:
        """
        Load knowledge base for specific vehicle
        
        Args:
            make: Vehicle make (e.g., "Ford")
            model: Vehicle model (e.g., "Escape")
            year: Vehicle year (e.g., 2008)
            
        Returns:
            True if knowledge loaded successfully
        """
        try:
            # Construct file paths
            vehicle_name = f"{make}_{model}_{year}"
            technical_path = Path(self.config.knowledge_base.path) / f"{vehicle_name}_technical.dat"
            profile_path = Path(self.config.knowledge_base.path) / f"{vehicle_name}_profile.yaml"
            
            # Load technical data
            if technical_path.exists():
                self.technical_knowledge = load_technical_data(str(technical_path))
                print(f"✓ Loaded technical data: {len(self.technical_knowledge.commands)} commands")
            else:
                print(f"⚠ No technical data found for {vehicle_name}")
            
            # Load vehicle profile
            if profile_path.exists():
                self.vehicle_profile = load_vehicle_profile(str(profile_path))
                print(f"✓ Loaded vehicle profile: {len(self.vehicle_profile.dtc_descriptions)} DTCs")
            else:
                print(f"⚠ No vehicle profile found for {vehicle_name}")
            
            # Update current vehicle
            self.current_vehicle = {
                'make': make,
                'model': model,
                'year': year
            }
            
            return True
        
        except Exception as e:
            print(f"✗ Error loading vehicle knowledge: {e}")
            return False
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process user query through the diagnostic workflow
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with results
        """
        result = {
            'query': query,
            'intent': None,
            'success': False,
            'response': None,
            'error': None
        }
        
        try:
            # Step 1: Parse query
            intent = self.query_parser.parse(query)
            result['intent'] = intent
            
            print(f"\n📝 Query: {query}")
            print(f"🎯 Intent: {intent}")
            
            # Step 2: Check for ambiguity
            if intent.ambiguous:
                clarification = self.query_parser.generate_clarification_prompt(intent)
                result['response'] = clarification
                result['needs_clarification'] = True
                return result
            
            # Step 3: Load vehicle knowledge if needed
            if intent.vehicle_make and intent.vehicle_model and intent.vehicle_year:
                if not self.current_vehicle or \
                   self.current_vehicle['make'] != intent.vehicle_make or \
                   self.current_vehicle['model'] != intent.vehicle_model or \
                   self.current_vehicle['year'] != intent.vehicle_year:
                    self.load_vehicle_knowledge(
                        intent.vehicle_make,
                        intent.vehicle_model,
                        intent.vehicle_year
                    )
            
            # Step 4: Execute action
            if intent.action == Action.CHECK or intent.action == Action.READ:
                result = self._handle_read_dtc(intent, result)
            elif intent.action == Action.CLEAR:
                result = self._handle_clear_dtc(intent, result)
            elif intent.action == Action.SCAN:
                result = self._handle_scan(intent, result)
            elif intent.action == Action.TEST:
                result = self._handle_test(intent, result)
            elif intent.action == Action.ACTUATE:
                result = self._handle_actuate(intent, result)
            else:
                result['error'] = f"Action not yet implemented: {intent.action}"
            
            # Add to session history
            self.session_history.append(result)
            
            return result
        
        except Exception as e:
            result['error'] = f"Error processing query: {e}"
            return result
    
    def _handle_read_dtc(self, intent: ParsedIntent, result: Dict) -> Dict:
        """Handle READ/CHECK DTC action"""
        print(f"\n🔍 Reading DTCs from {intent.module or 'vehicle'}...")
        
        # Look up module address from technical knowledge
        address = None
        if intent.module and self.technical_knowledge:
            module_info = self.technical_knowledge.modules.get(intent.module)
            if module_info:
                address = module_info.address
                print(f"   Module address: {address}")
        
        try:
            # Execute read_dtc toolkit script
            dtc_result = self.toolkit_executor.read_dtc(
                port=self.config.vehicle.port,
                module=intent.module,
                address=address
            )
            
            # Process results
            if dtc_result.get('success'):
                dtcs = dtc_result.get('dtcs', [])
                count = dtc_result.get('count', 0)
                
                if count > 0:
                    # Format DTC list with descriptions from profile
                    dtc_list = []
                    for dtc in dtcs:
                        code = dtc['code']
                        description = "No description available"
                        
                        # Look up description from vehicle profile
                        if self.vehicle_profile:
                            dtc_info = self.vehicle_profile.dtc_descriptions.get(code)
                            if dtc_info:
                                description = dtc_info.get('description', description)
                        
                        dtc_list.append(f"{code}: {description}")
                    
                    result['success'] = True
                    result['response'] = f"Found {count} DTC(s):\n" + "\n".join(f"  • {dtc}" for dtc in dtc_list)
                else:
                    result['success'] = True
                    result['response'] = "No DTCs found - system is clear"
                
                result['dtcs'] = dtcs
                result['count'] = count
            else:
                result['error'] = dtc_result.get('error', 'Unknown error reading DTCs')
            
            result['action'] = 'read_dtc'
            result['module'] = intent.module
            result['address'] = address
            
        except ToolkitExecutionError as e:
            result['error'] = f"Failed to read DTCs: {e}"
        
        return result
    
    def _handle_clear_dtc(self, intent: ParsedIntent, result: Dict) -> Dict:
        """Handle CLEAR DTC action"""
        print(f"\n🗑️  Clearing DTCs from {intent.module or 'vehicle'}...")
        
        # Look up module address
        address = None
        if intent.module and self.technical_knowledge:
            module_info = self.technical_knowledge.modules.get(intent.module)
            if module_info:
                address = module_info.address
        
        # Check if confirmation is required (dangerous operation)
        if self.config.safety.confirmation_mode != 'none':
            print("⚠️  WARNING: Clearing DTCs will reset emissions monitors!")
            confirmation = input("Are you sure you want to clear DTCs? (yes/no): ")
            if confirmation.lower() not in ['yes', 'y']:
                result['success'] = False
                result['response'] = "Operation cancelled by user"
                result['cancelled'] = True
                return result
        
        try:
            # Execute clear_dtc toolkit script
            clear_result = self.toolkit_executor.clear_dtc(
                port=self.config.vehicle.port,
                module=intent.module,
                address=address
            )
            
            # Process results
            if clear_result.get('success') and clear_result.get('cleared'):
                result['success'] = True
                result['response'] = (
                    f"Successfully cleared DTCs from {intent.module or 'vehicle'}\n"
                    "Note: Emissions monitors have been reset. "
                    "Drive vehicle normally to allow monitors to complete."
                )
            else:
                result['error'] = clear_result.get('error', 'Failed to clear DTCs')
            
            result['action'] = 'clear_dtc'
            result['module'] = intent.module
            result['address'] = address
            result['requires_confirmation'] = True
            
        except ToolkitExecutionError as e:
            result['error'] = f"Failed to clear DTCs: {e}"
        
        return result
    
    def _handle_scan(self, intent: ParsedIntent, result: Dict) -> Dict:
        """Handle SCAN action"""
        print(f"\n🔎 Scanning vehicle...")
        
        result['success'] = True
        result['response'] = "Full vehicle scan not yet implemented"
        result['action'] = 'scan'
        
        return result
    
    def _handle_test(self, intent: ParsedIntent, result: Dict) -> Dict:
        """Handle TEST action"""
        print(f"\n🧪 Testing {intent.module or 'component'}...")
        
        result['success'] = True
        result['response'] = "Component testing not yet implemented"
        result['action'] = 'test'
        
        return result
    
    def _handle_actuate(self, intent: ParsedIntent, result: Dict) -> Dict:
        """Handle ACTUATE action"""
        print(f"\n⚙️  Actuating {intent.module or 'component'}...")
        
        result['success'] = True
        result['response'] = "Actuation not yet implemented"
        result['action'] = 'actuate'
        result['requires_confirmation'] = True
        
        return result
    
    def run_interactive(self):
        """
        Run agent in interactive mode
        
        Accepts user queries in a loop until exit
        """
        print("\n" + "=" * 60)
        print("AI Vehicle Diagnostic Agent - Interactive Mode")
        print("=" * 60)
        print("\nCommands:")
        print("  - Type your diagnostic query")
        print("  - 'load <make> <model> <year>' - Load vehicle knowledge")
        print("  - 'exit' or 'quit' - Exit agent")
        print("\n" + "=" * 60 + "\n")
        
        while True:
            try:
                # Get user input
                query = input("\n🚗 Query: ").strip()
                
                if not query:
                    continue
                
                # Check for exit
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\nGoodbye!")
                    break
                
                # Check for load command
                if query.lower().startswith('load '):
                    parts = query.split()
                    if len(parts) == 4:
                        _, make, model, year = parts
                        self.load_vehicle_knowledge(make, model, int(year))
                    else:
                        print("Usage: load <make> <model> <year>")
                    continue
                
                # Process query
                result = self.process_query(query)
                
                # Display result
                print("\n" + "-" * 60)
                if result.get('needs_clarification'):
                    print("❓ " + result['response'])
                elif result['success']:
                    print("✓ " + result['response'])
                else:
                    print("✗ Error: " + (result.get('error') or 'Unknown error'))
                print("-" * 60)
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n✗ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AI Vehicle Diagnostic Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--vehicle',
        nargs=3,
        metavar=('MAKE', 'MODEL', 'YEAR'),
        help='Pre-load vehicle knowledge (e.g., Ford Escape 2008)'
    )
    
    parser.add_argument(
        '--query',
        help='Single query mode (non-interactive)'
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = DiagnosticAgent(args.config)
    
    # Pre-load vehicle if specified
    if args.vehicle:
        make, model, year = args.vehicle
        agent.load_vehicle_knowledge(make, model, int(year))
    
    # Single query mode
    if args.query:
        result = agent.process_query(args.query)
        if result['success']:
            print(result['response'])
            sys.exit(0)
        else:
            print(f"Error: {result.get('error')}", file=sys.stderr)
            sys.exit(1)
    
    # Interactive mode
    agent.run_interactive()


if __name__ == '__main__':
    main()
