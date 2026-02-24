"""
AI Vehicle Diagnostic Agent - Main Entry Point

Command-line interface for the AI diagnostic agent.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add agent_core to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_core.agent import DiagnosticAgent
from config.config_loader import load_config


def setup_logging(log_level: str = "INFO"):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='AI Vehicle Diagnostic Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive session
  python main.py --port COM3
  
  # Use specific configuration
  python main.py --config my_config.yaml --port COM3
  
  # Enable debug logging
  python main.py --port COM3 --log-level DEBUG
  
  # Single query mode
  python main.py --port COM3 --query "check HVAC codes"
"""
    )
    
    parser.add_argument(
        '--port',
        type=str,
        help='COM port for ELM327 adapter (e.g., COM3, /dev/ttyUSB0)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/agent_config.yaml',
        help='Path to configuration file (default: config/agent_config.yaml)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Single query to execute (non-interactive mode)'
    )
    
    parser.add_argument(
        '--vehicle',
        type=str,
        help='Vehicle identifier (e.g., Ford_Escape_2008)'
    )
    
    parser.add_argument(
        '--no-web-research',
        action='store_true',
        help='Disable web research (manual consultation only)'
    )
    
    return parser.parse_args()


def print_banner():
    """Print welcome banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        AI Vehicle Diagnostic Agent                        ║
║        Intelligent OBD2/UDS Diagnostics                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help information"""
    help_text = """
Available Commands:
  help              - Show this help message
  exit, quit        - Exit the agent
  status            - Show agent status
  vehicle           - Show current vehicle info
  modules           - List known modules
  history           - Show session history
  
Diagnostic Queries:
  "check HVAC codes"
  "read DTC from ABS"
  "clear codes"
  "scan all modules"
  "read VIN"
  
Type your query in natural language and press Enter.
"""
    print(help_text)


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Print banner
    print_banner()
    
    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = load_config(args.config)
        
        # Override config with command-line args
        if args.port:
            config['vehicle']['port'] = args.port
        
        if args.no_web_research:
            config['web_research']['enabled'] = False
        
        # Initialize agent
        logger.info("Initializing diagnostic agent...")
        agent = DiagnosticAgent(config)
        
        # Set vehicle if specified
        if args.vehicle:
            logger.info(f"Setting vehicle: {args.vehicle}")
            # Parse vehicle identifier (e.g., Ford_Escape_2008)
            parts = args.vehicle.split('_')
            if len(parts) >= 3:
                agent.set_vehicle(parts[0], parts[1], int(parts[2]))
        
        # Single query mode
        if args.query:
            logger.info(f"Executing query: {args.query}")
            result = agent.process_query(args.query)
            print("\n" + "="*60)
            print("RESULT")
            print("="*60)
            print(result)
            return 0
        
        # Interactive mode
        print("\nAgent initialized successfully!")
        print("Type 'help' for available commands or enter a diagnostic query.")
        print("Type 'exit' to quit.\n")
        
        # Interactive session loop
        while True:
            try:
                # Get user input
                query = input("🔧 > ").strip()
                
                if not query:
                    continue
                
                # Handle commands
                if query.lower() in ['exit', 'quit']:
                    print("\nGoodbye!")
                    break
                
                elif query.lower() == 'help':
                    print_help()
                    continue
                
                elif query.lower() == 'status':
                    status = agent.get_status()
                    print(f"\nAgent Status: {status}")
                    continue
                
                elif query.lower() == 'vehicle':
                    vehicle_info = agent.get_vehicle_info()
                    if vehicle_info:
                        print(f"\nCurrent Vehicle: {vehicle_info}")
                    else:
                        print("\nNo vehicle set. Use 'read VIN' to identify vehicle.")
                    continue
                
                elif query.lower() == 'modules':
                    modules = agent.list_modules()
                    print(f"\nKnown Modules: {modules}")
                    continue
                
                elif query.lower() == 'history':
                    history = agent.get_session_history()
                    print(f"\nSession History:\n{history}")
                    continue
                
                # Process diagnostic query
                print()  # Blank line
                result = agent.process_query(query)
                print(f"\n{result}\n")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
                continue
            
            except Exception as e:
                logger.error(f"Error processing query: {e}", exc_info=True)
                print(f"\n❌ Error: {e}\n")
                continue
    
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        print(f"\n❌ Error: Configuration file not found: {args.config}")
        print("   Create a configuration file or specify a different path with --config")
        return 1
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
