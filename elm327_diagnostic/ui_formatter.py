"""
UI Formatting module for improved console output
Provides clean, readable formatting for diagnostic tool
"""

import os
import sys
from typing import List, Dict, Optional


class UIFormatter:
    """Console UI formatting utilities"""
    
    # ANSI Color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'DIM': '\033[2m',
        'CYAN': '\033[36m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'RED': '\033[31m',
        'MAGENTA': '\033[35m',
        'WHITE': '\033[37m',
    }
    
    # Symbols
    SYMBOLS = {
        'SUCCESS': '✓',
        'FAILURE': '✗',
        'WARNING': '⚠',
        'INFO': 'ℹ',
        'ARROW': '→',
        'BULLET': '•',
    }
    
    @staticmethod
    def _supports_colors() -> bool:
        """Check if terminal supports colors"""
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and os.name != 'nt'
    
    @staticmethod
    def _colorize(text: str, color: str) -> str:
        """Apply color to text if supported"""
        if not UIFormatter._supports_colors():
            return text
        
        color_code = UIFormatter.COLORS.get(color, '')
        reset_code = UIFormatter.COLORS['RESET']
        return f"{color_code}{text}{reset_code}"
    
    @staticmethod
    def header(title: str, width: int = 60) -> str:
        """Create a formatted header"""
        border = "=" * width
        padded = f" {title} ".center(width, "=")
        return f"\n{padded}"
    
    @staticmethod
    def subheader(title: str, width: int = 60) -> str:
        """Create a formatted subheader"""
        border = "-" * width
        return f"\n{title}\n{border}"
    
    @staticmethod
    def success(message: str, indent: int = 0) -> str:
        """Format success message"""
        prefix = UIFormatter._colorize(f"{UIFormatter.SYMBOLS['SUCCESS']}", 'GREEN')
        indent_str = " " * indent
        return f"{indent_str}{prefix} {message}"
    
    @staticmethod
    def failure(message: str, indent: int = 0) -> str:
        """Format failure message"""
        prefix = UIFormatter._colorize(f"{UIFormatter.SYMBOLS['FAILURE']}", 'RED')
        indent_str = " " * indent
        return f"{indent_str}{prefix} {message}"
    
    @staticmethod
    def warning(message: str, indent: int = 0) -> str:
        """Format warning message"""
        prefix = UIFormatter._colorize(f"{UIFormatter.SYMBOLS['WARNING']}", 'YELLOW')
        indent_str = " " * indent
        return f"{indent_str}{prefix} {message}"
    
    @staticmethod
    def info(message: str, indent: int = 0) -> str:
        """Format info message"""
        indent_str = " " * indent
        return f"{indent_str}{message}"
    
    @staticmethod
    def section_title(title: str) -> str:
        """Create a section title"""
        return UIFormatter._colorize(title, 'CYAN')
    
    @staticmethod
    def menu(options: List[str], title: str = "MAIN MENU") -> str:
        """Format a menu"""
        output = UIFormatter.header(title)
        for option in options:
            output += f"\n{option}"
        output += f"\n{'=' * 60}\n"
        return output
    
    @staticmethod
    def table(headers: List[str], rows: List[List[str]], col_widths: Optional[List[int]] = None) -> str:
        """Format a table"""
        if not col_widths:
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Header
        header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        separator = "-" * len(header_row)
        
        output = f"\n{header_row}\n{separator}"
        
        # Rows
        for row in rows:
            row_str = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
            output += f"\n{row_str}"
        
        return output
    
    @staticmethod
    def key_value_pair(key: str, value: str, indent: int = 2) -> str:
        """Format a key-value pair"""
        indent_str = " " * indent
        return f"{indent_str}{key}: {value}"
    
    @staticmethod
    def list_items(items: List[str], symbol: str = 'BULLET', indent: int = 2) -> str:
        """Format a list of items"""
        sym = UIFormatter.SYMBOLS.get(symbol, '•')
        indent_str = " " * indent
        return "\n".join(f"{indent_str}{sym} {item}" for item in items)
    
    @staticmethod
    def progress_bar(current: int, total: int, width: int = 40) -> str:
        """Create a progress bar"""
        if total == 0:
            percentage = 0
        else:
            percentage = int((current / total) * 100)
        
        filled = int((current / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {percentage}%"
    
    @staticmethod
    def box(message: str, style: str = 'single') -> str:
        """Draw a box around message"""
        lines = message.split('\n')
        max_len = max(len(line) for line in lines)
        
        if style == 'single':
            top_left, top_right = '┌', '┐'
            bottom_left, bottom_right = '└', '┘'
            horizontal = '─'
            vertical = '│'
        else:
            top_left, top_right = '╔', '╗'
            bottom_left, bottom_right = '╚', '╝'
            horizontal = '═'
            vertical = '║'
        
        output = f"{top_left}{horizontal * (max_len + 2)}{top_right}\n"
        for line in lines:
            output += f"{vertical} {line.ljust(max_len)} {vertical}\n"
        output += f"{bottom_left}{horizontal * (max_len + 2)}{bottom_right}"
        
        return output


class LogFormatter:
    """Custom logging formatter for cleaner output"""
    
    @staticmethod
    def format_log_message(level: str, message: str, include_timestamp: bool = False) -> str:
        """Format a log message cleanly"""
        ui = UIFormatter()
        
        if level == 'INFO':
            return message
        elif level == 'SUCCESS':
            return ui.success(message)
        elif level == 'ERROR':
            return ui.failure(message)
        elif level == 'WARNING':
            return ui.warning(message)
        else:
            return message
