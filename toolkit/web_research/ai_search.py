#!/usr/bin/env python3
"""
AI-Assisted Web Search Module
Uses AI backend's web search capability to find diagnostic procedures

This module constructs search queries and extracts relevant information
from search results without requiring API keys by default.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a single search result"""
    title: str
    url: str
    snippet: str
    source_type: str  # 'manual', 'database', 'forum', 'unknown'
    confidence: float  # 0.0 to 1.0


@dataclass
class ExtractedCommand:
    """Represents an extracted OBD2/UDS command"""
    command_hex: str
    description: str
    context: str
    confidence: float


class AIAssistedSearch:
    """
    AI-assisted web search for diagnostic procedures
    Uses AI backend's web search if available, otherwise prompts user
    """
    
    def __init__(self, ai_backend=None):
        """
        Initialize search module
        
        Args:
            ai_backend: Optional AI backend with web_search() capability
        """
        self.ai_backend = ai_backend
        
        # Source priority for ranking
        self.source_priority = {
            'manual': 1.0,      # Official service manuals
            'database': 0.8,    # Repair databases (AllData, Mitchell)
            'forum': 0.5,       # Forums and community posts
            'unknown': 0.3      # Unknown sources
        }
    
    def construct_search_query(
        self,
        make: str,
        model: str,
        year: int,
        module: str,
        action: str
    ) -> str:
        """
        Construct optimized search query for diagnostic procedures
        
        Args:
            make: Vehicle make (e.g., "Ford")
            model: Vehicle model (e.g., "Escape")
            year: Vehicle year (e.g., 2008)
            module: Target module (e.g., "HVAC", "transmission")
            action: Diagnostic action (e.g., "read DTC", "clear codes")
        
        Returns:
            Optimized search query string
        """
        # Base query
        query = f"{year} {make} {model} {module} {action} OBD2"
        
        # Add technical terms for better results
        if "DTC" in action or "code" in action.lower():
            query += " diagnostic trouble code"
        
        if "transmission" in module.lower():
            query += " TCM PCM"
        
        # Add protocol hints
        query += " CAN UDS"
        
        return query
    
    def construct_ford_cross_reference_queries(
        self,
        model: str,
        year: int,
        module: str,
        action: str
    ) -> List[str]:
        """
        Construct queries for related Ford models
        
        Args:
            model: Original model (e.g., "Escape")
            year: Vehicle year
            module: Target module
            action: Diagnostic action
        
        Returns:
            List of cross-reference search queries
        """
        # Related Ford models by era
        ford_relatives = {
            'Escape': ['Fusion', 'Focus', 'Mazda Tribute'],
            'Fusion': ['Escape', 'Milan', 'Mazda 6'],
            'Focus': ['Escape', 'C-Max'],
            'F-150': ['F-250', 'F-350', 'Expedition'],
            'Explorer': ['Mountaineer', 'Aviator']
        }
        
        queries = []
        relatives = ford_relatives.get(model, [])
        
        for relative in relatives:
            # Same year first
            query = f"{year} Ford {relative} {module} {action} OBD2"
            queries.append(query)
            
            # +/- 2 years
            for year_offset in [-2, -1, 1, 2]:
                alt_year = year + year_offset
                if 2005 <= alt_year <= 2012:  # Same era
                    query = f"{alt_year} Ford {relative} {module} {action} OBD2"
                    queries.append(query)
        
        return queries
    
    def classify_source(self, url: str, title: str) -> str:
        """
        Classify source type based on URL and title
        
        Args:
            url: Source URL
            title: Page title
        
        Returns:
            Source type: 'manual', 'database', 'forum', 'unknown'
        """
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Official manuals
        if any(domain in url_lower for domain in [
            'motorcraft', 'ford.com', 'service-manual',
            'workshop-manual', 'repair-manual'
        ]):
            return 'manual'
        
        # Repair databases
        if any(domain in url_lower for domain in [
            'alldata', 'mitchell', 'identifix', 'prodemand',
            'autozone', 'rockauto'
        ]):
            return 'database'
        
        # Forums
        if any(domain in url_lower for domain in [
            'forum', 'reddit', 'stack', 'community',
            'discussion', 'board'
        ]):
            return 'forum'
        
        # Check title for manual indicators
        if any(term in title_lower for term in [
            'service manual', 'workshop manual', 'repair manual',
            'technical service bulletin', 'tsb'
        ]):
            return 'manual'
        
        return 'unknown'
    
    def extract_commands_from_text(self, text: str) -> List[ExtractedCommand]:
        """
        Extract OBD2/UDS commands from text
        
        Args:
            text: Text to search for commands
        
        Returns:
            List of extracted commands
        """
        commands = []
        
        # Pattern for hex commands (various formats)
        patterns = [
            # Standard hex: 22 1E 1C or 221E1C
            r'(?:0x)?([0-9A-Fa-f]{2}(?:\s+[0-9A-Fa-f]{2}){1,7})',
            # With separators: 22-1E-1C or 22:1E:1C
            r'([0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){1,7})',
            # Continuous: 221E1C (2-16 hex digits)
            r'(?:0x)?([0-9A-Fa-f]{4,16})(?!\w)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                command_hex = match.group(1).replace(' ', '').replace('-', '').replace(':', '')
                
                # Validate command length (2-16 hex digits)
                if len(command_hex) < 4 or len(command_hex) > 16:
                    continue
                
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                # Extract description from context
                description = self._extract_description(context, command_hex)
                
                # Calculate confidence based on context
                confidence = self._calculate_command_confidence(context)
                
                commands.append(ExtractedCommand(
                    command_hex=command_hex,
                    description=description,
                    context=context,
                    confidence=confidence
                ))
        
        # Deduplicate and sort by confidence
        unique_commands = {}
        for cmd in commands:
            if cmd.command_hex not in unique_commands or \
               cmd.confidence > unique_commands[cmd.command_hex].confidence:
                unique_commands[cmd.command_hex] = cmd
        
        return sorted(unique_commands.values(), key=lambda x: x.confidence, reverse=True)
    
    def _extract_description(self, context: str, command_hex: str) -> str:
        """Extract description from context"""
        # Look for common description patterns
        patterns = [
            r'(?:reads?|gets?|retrieves?)\s+([^.,:;]+)',
            r'(?:for|to)\s+([^.,:;]+)',
            r'([^.,:;]+)\s+(?:command|request|query)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 10 and len(desc) < 100:
                    return desc
        
        return "Unknown command"
    
    def _calculate_command_confidence(self, context: str) -> float:
        """Calculate confidence score based on context"""
        confidence = 0.5  # Base confidence
        
        context_lower = context.lower()
        
        # Positive indicators
        if any(term in context_lower for term in [
            'service', 'diagnostic', 'obd', 'uds', 'can'
        ]):
            confidence += 0.2
        
        if any(term in context_lower for term in [
            'read', 'write', 'request', 'response', 'command'
        ]):
            confidence += 0.1
        
        if any(term in context_lower for term in [
            'mode', 'pid', 'did', 'sid'
        ]):
            confidence += 0.1
        
        # Negative indicators
        if any(term in context_lower for term in [
            'example', 'sample', 'test', 'dummy'
        ]):
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank search results by relevance and source quality
        
        Args:
            results: List of search results
        
        Returns:
            Sorted list of results (best first)
        """
        def score_result(result: SearchResult) -> float:
            # Base score from source type
            score = self.source_priority.get(result.source_type, 0.3)
            
            # Boost for confidence
            score *= result.confidence
            
            # Boost for specific keywords in title/snippet
            text = (result.title + ' ' + result.snippet).lower()
            
            if 'service manual' in text or 'workshop manual' in text:
                score *= 1.5
            
            if 'obd' in text or 'diagnostic' in text:
                score *= 1.2
            
            if 'ford' in text:
                score *= 1.1
            
            return score
        
        return sorted(results, key=score_result, reverse=True)
    
    async def search(
        self,
        make: str,
        model: str,
        year: int,
        module: str,
        action: str,
        include_cross_reference: bool = True
    ) -> Tuple[List[SearchResult], List[ExtractedCommand]]:
        """
        Perform AI-assisted search for diagnostic procedures
        
        Args:
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            module: Target module
            action: Diagnostic action
            include_cross_reference: Include related Ford models
        
        Returns:
            Tuple of (search_results, extracted_commands)
        """
        # Construct primary query
        primary_query = self.construct_search_query(make, model, year, module, action)
        
        # Construct cross-reference queries if Ford
        cross_ref_queries = []
        if include_cross_reference and make.lower() == 'ford':
            cross_ref_queries = self.construct_ford_cross_reference_queries(
                model, year, module, action
            )
        
        # Perform search (implementation depends on AI backend)
        if self.ai_backend and hasattr(self.ai_backend, 'web_search'):
            # Use AI backend's web search
            results = await self._search_with_ai_backend(
                primary_query, cross_ref_queries
            )
        else:
            # Fallback: return empty results (user will be prompted)
            results = []
        
        # Extract commands from results
        all_commands = []
        for result in results:
            commands = self.extract_commands_from_text(result.snippet)
            all_commands.extend(commands)
        
        # Rank results
        ranked_results = self.rank_results(results)
        
        return ranked_results, all_commands
    
    async def _search_with_ai_backend(
        self,
        primary_query: str,
        cross_ref_queries: List[str]
    ) -> List[SearchResult]:
        """
        Perform search using AI backend
        
        Args:
            primary_query: Primary search query
            cross_ref_queries: Cross-reference queries
        
        Returns:
            List of search results
        """
        results = []
        
        # Search primary query
        try:
            primary_results = await self.ai_backend.web_search(primary_query)
            for item in primary_results:
                source_type = self.classify_source(item.get('url', ''), item.get('title', ''))
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('snippet', ''),
                    source_type=source_type,
                    confidence=0.8  # Primary query gets high confidence
                ))
        except Exception as e:
            print(f"Primary search failed: {e}")
        
        # Search cross-reference queries (limit to top 2)
        for query in cross_ref_queries[:2]:
            try:
                cross_results = await self.ai_backend.web_search(query)
                for item in cross_results[:3]:  # Top 3 from each cross-ref
                    source_type = self.classify_source(item.get('url', ''), item.get('title', ''))
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', ''),
                        source_type=source_type,
                        confidence=0.6  # Cross-ref gets lower confidence
                    ))
            except Exception as e:
                print(f"Cross-reference search failed: {e}")
                continue
        
        return results


def main():
    """Example usage"""
    search = AIAssistedSearch()
    
    # Example: Extract commands from text
    sample_text = """
    To read transmission temperature, send command 22 1E 1C to the PCM.
    The response will be 62 1E 1C followed by the temperature data.
    For turbine speed, use 221E14.
    """
    
    commands = search.extract_commands_from_text(sample_text)
    
    print("Extracted Commands:")
    for cmd in commands:
        print(f"  {cmd.command_hex}: {cmd.description} (confidence: {cmd.confidence:.2f})")


if __name__ == "__main__":
    main()
