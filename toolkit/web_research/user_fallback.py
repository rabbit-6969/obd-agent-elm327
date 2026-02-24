#!/usr/bin/env python3
"""
User Fallback Mode for Web Research
When AI backend web search is unavailable, prompt user to search manually

This module generates search queries and helps users paste results back
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from .ai_search import AIAssistedSearch, ExtractedCommand


@dataclass
class UserSearchSession:
    """Represents a user search session"""
    query: str
    user_provided_text: str
    extracted_commands: List[ExtractedCommand]
    urls_found: List[str]


class UserFallbackSearch:
    """
    User fallback mode for web research
    Prompts user to search manually and paste results
    """
    
    def __init__(self):
        """Initialize user fallback search"""
        self.ai_search = AIAssistedSearch()
        self.session_history: List[UserSearchSession] = []
    
    def generate_search_instructions(
        self,
        make: str,
        model: str,
        year: int,
        module: str,
        action: str
    ) -> str:
        """
        Generate user-friendly search instructions
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            module: Target module
            action: Diagnostic action
        
        Returns:
            Formatted instructions for user
        """
        # Generate primary query
        query = self.ai_search.construct_search_query(
            make, model, year, module, action
        )
        
        # Generate instructions
        instructions = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    WEB RESEARCH NEEDED                               ║
╚══════════════════════════════════════════════════════════════════════╝

I need your help to find diagnostic information for:
  Vehicle: {year} {make} {model}
  Module: {module}
  Action: {action}

STEP 1: Search Google
────────────────────────────────────────────────────────────────────────
Copy and paste this search query into Google:

  {query}

STEP 2: Look for These Sources (in order of preference)
────────────────────────────────────────────────────────────────────────
  1. Official service manuals (best)
  2. Repair databases (AllData, Mitchell, etc.)
  3. Technical forums (FordTechMazdaVolvo, etc.)
  4. Community posts (Reddit, StackExchange)

STEP 3: Copy Relevant Information
────────────────────────────────────────────────────────────────────────
Look for:
  • OBD2/UDS command sequences (hex codes like "22 1E 1C")
  • Module addresses (like "0x7E0" or "7E0")
  • Response formats
  • Step-by-step procedures

STEP 4: Paste Results Below
────────────────────────────────────────────────────────────────────────
Copy the relevant text from the web pages and paste it here.
Include URLs if possible.

Type 'done' when finished, or 'skip' to try a different approach.
"""
        return instructions
    
    def generate_cross_reference_instructions(
        self,
        model: str,
        year: int,
        module: str,
        action: str
    ) -> str:
        """
        Generate instructions for cross-reference search
        
        Args:
            model: Original model
            year: Vehicle year
            module: Target module
            action: Diagnostic action
        
        Returns:
            Formatted cross-reference instructions
        """
        # Get cross-reference queries
        queries = self.ai_search.construct_ford_cross_reference_queries(
            model, year, module, action
        )
        
        if not queries:
            return ""
        
        instructions = f"""
╔══════════════════════════════════════════════════════════════════════╗
║              TRY RELATED FORD MODELS                                 ║
╚══════════════════════════════════════════════════════════════════════╝

The {model} shares components with other Ford vehicles.
Try searching for these related models:

"""
        for i, query in enumerate(queries[:3], 1):
            instructions += f"  {i}. {query}\n"
        
        instructions += """
These vehicles often use the same diagnostic procedures.

"""
        return instructions
    
    def parse_user_input(self, user_text: str) -> UserSearchSession:
        """
        Parse user-provided search results
        
        Args:
            user_text: Text pasted by user
        
        Returns:
            UserSearchSession with extracted information
        """
        # Extract URLs
        urls = self._extract_urls(user_text)
        
        # Extract commands using AI search module
        commands = self.ai_search.extract_commands_from_text(user_text)
        
        # Create session
        session = UserSearchSession(
            query="",  # Will be set by caller
            user_provided_text=user_text,
            extracted_commands=commands,
            urls_found=urls
        )
        
        self.session_history.append(session)
        
        return session
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        # Pattern for URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        
        urls = re.findall(url_pattern, text)
        
        # Deduplicate
        return list(set(urls))
    
    def format_extracted_results(self, session: UserSearchSession) -> str:
        """
        Format extracted results for display
        
        Args:
            session: User search session
        
        Returns:
            Formatted results string
        """
        output = """
╔══════════════════════════════════════════════════════════════════════╗
║                    EXTRACTION RESULTS                                ║
╚══════════════════════════════════════════════════════════════════════╝

"""
        
        # Show extracted commands
        if session.extracted_commands:
            output += "Found Commands:\n"
            output += "─" * 70 + "\n"
            
            for i, cmd in enumerate(session.extracted_commands, 1):
                output += f"\n{i}. Command: {cmd.command_hex}\n"
                output += f"   Description: {cmd.description}\n"
                output += f"   Confidence: {cmd.confidence:.0%}\n"
                output += f"   Context: {cmd.context[:100]}...\n"
        else:
            output += "⚠ No commands found in the provided text.\n"
            output += "  Try including more technical details or hex codes.\n"
        
        # Show URLs
        if session.urls_found:
            output += "\n" + "─" * 70 + "\n"
            output += "Sources:\n"
            for url in session.urls_found:
                output += f"  • {url}\n"
        
        output += "\n" + "═" * 70 + "\n"
        
        return output
    
    def prompt_for_confirmation(self, commands: List[ExtractedCommand]) -> str:
        """
        Generate confirmation prompt for extracted commands
        
        Args:
            commands: List of extracted commands
        
        Returns:
            Confirmation prompt
        """
        if not commands:
            return "No commands found. Would you like to try a different search? (yes/no): "
        
        prompt = """
I found the commands above. Would you like me to:
  1. Use these commands
  2. Search for more information
  3. Skip this and try a different approach

Enter choice (1/2/3): """
        
        return prompt
    
    def interactive_search_session(
        self,
        make: str,
        model: str,
        year: int,
        module: str,
        action: str
    ) -> Optional[UserSearchSession]:
        """
        Run interactive search session with user
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            module: Target module
            action: Diagnostic action
        
        Returns:
            UserSearchSession if successful, None if skipped
        """
        # Generate and show instructions
        instructions = self.generate_search_instructions(
            make, model, year, module, action
        )
        print(instructions)
        
        # Collect user input
        print("\nPaste your search results below (type 'done' on a new line when finished):")
        print("─" * 70)
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().lower() == 'done':
                    break
                elif line.strip().lower() == 'skip':
                    print("\n⚠ Skipping web research.")
                    return None
                lines.append(line)
            except EOFError:
                break
        
        user_text = '\n'.join(lines)
        
        if not user_text.strip():
            print("\n⚠ No text provided.")
            
            # Offer cross-reference search
            cross_ref = self.generate_cross_reference_instructions(
                model, year, module, action
            )
            if cross_ref:
                print(cross_ref)
                retry = input("Try cross-reference search? (yes/no): ").strip().lower()
                if retry == 'yes':
                    return self.interactive_search_session(
                        make, model, year, module, action
                    )
            
            return None
        
        # Parse user input
        session = self.parse_user_input(user_text)
        session.query = self.ai_search.construct_search_query(
            make, model, year, module, action
        )
        
        # Show results
        results = self.format_extracted_results(session)
        print(results)
        
        # Confirm with user
        if session.extracted_commands:
            choice = input(self.prompt_for_confirmation(session.extracted_commands)).strip()
            
            if choice == '1':
                return session
            elif choice == '2':
                print("\nLet's search for more information...")
                return self.interactive_search_session(
                    make, model, year, module, action
                )
            else:
                print("\n⚠ Skipping web research.")
                return None
        else:
            # No commands found, offer to try again
            retry = input("Try a different search? (yes/no): ").strip().lower()
            if retry == 'yes':
                return self.interactive_search_session(
                    make, model, year, module, action
                )
            return None
    
    def get_session_history(self) -> List[UserSearchSession]:
        """Get all search sessions from this instance"""
        return self.session_history


def main():
    """Example usage"""
    fallback = UserFallbackSearch()
    
    # Example: Interactive session
    print("Example: User Fallback Search")
    print("=" * 70)
    
    # Simulate user search
    session = fallback.interactive_search_session(
        make="Ford",
        model="Escape",
        year=2008,
        module="transmission",
        action="read temperature"
    )
    
    if session:
        print("\n✓ Search session completed successfully")
        print(f"  Found {len(session.extracted_commands)} commands")
        print(f"  Found {len(session.urls_found)} URLs")
    else:
        print("\n⚠ Search session cancelled")


if __name__ == "__main__":
    main()
