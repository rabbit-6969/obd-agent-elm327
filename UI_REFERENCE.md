# UI Formatter - Quick Reference Guide

## Usage Examples

### Import
```python
from ui_formatter import UIFormatter

ui = UIFormatter()
```

### Headers & Sections

```python
# Large header for main sections
print(ui.header("VEHICLE DIAGNOSTICS"))
# Output:
# =========== VEHICLE DIAGNOSTICS ===========

# Subheader with dashes
print(ui.subheader("Connection Status"))
# Output:
# Connection Status
# ─────────────────
```

### Status Messages

```python
# Success message (green with ✓)
print(ui.success("VIN read successfully"))
# Output: ✓ VIN read successfully

# Failure message (red with ✗)
print(ui.failure("Failed to connect"))
# Output: ✗ Failed to connect

# Warning message (yellow with ⚠)
print(ui.warning("Timeout occurred"))
# Output: ⚠ Timeout occurred

# Info message
print(ui.info("Processing diagnostic data"))
# Output: Processing diagnostic data
```

### Indentation

All messages support `indent` parameter:

```python
print(ui.success("Item 1", indent=0))
print(ui.success("Item 2", indent=2))
print(ui.success("Sub-item", indent=4))

# Output:
# ✓ Item 1
#   ✓ Item 2
#     ✓ Sub-item
```

### Key-Value Pairs

```python
print(ui.key_value_pair("VIN", "1FAHP551XX8156549", indent=2))
print(ui.key_value_pair("Status", "Active", indent=2))
print(ui.key_value_pair("Code", "P0400", indent=4))

# Output:
#   VIN: 1FAHP551XX8156549
#   Status: Active
#     Code: P0400
```

### Lists

```python
items = [
    "Check COM port is correct",
    "Ensure ELM327 is powered on",
    "Connect to OBD-II port",
    "Vehicle must be in RUN state"
]
print(ui.list_items(items, indent=2))

# Output:
#   • Check COM port is correct
#   • Ensure ELM327 is powered on
#   • Connect to OBD-II port
#   • Vehicle must be in RUN state
```

### Menus

```python
menu_items = [
    "1. Check Adapter Settings",
    "2. Test Vehicle Connection",
    "3. Run Full Diagnostics",
    "",
    "0. Exit"
]
print(ui.menu(menu_items, "MAIN MENU"))

# Output:
# ============= MAIN MENU =============
#
# 1. Check Adapter Settings
# 2. Test Vehicle Connection
# 3. Run Full Diagnostics
#
# 0. Exit
#
# =====================================
```

### Tables

```python
headers = ["Code", "Description", "Status"]
rows = [
    ["P0400", "EGR System Flow", "Active"],
    ["P0401", "EGR Flow Insufficient", "Active"],
    ["P0500", "Vehicle Speed Error", "Pending"]
]

print(ui.table(headers, rows))

# Output:
# Code | Description             | Status
# ────────────────────────────────────────
# P0400 | EGR System Flow          | Active
# P0401 | EGR Flow Insufficient    | Active
# P0500 | Vehicle Speed Error      | Pending
```

### Progress Bar

```python
print(ui.progress_bar(current=7, total=10))
print(ui.progress_bar(current=2, total=10))

# Output:
# [███████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 70%
# [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 20%
```

### Boxes

```python
print(ui.box("Error: Connection Failed\nCheck adapter power"))

# Output:
# ┌────────────────────────────────┐
# │ Error: Connection Failed       │
# │ Check adapter power            │
# └────────────────────────────────┘

# With double-line style:
print(ui.box("Warning!", style='double'))

# Output:
# ╔════════════╗
# ║ Warning!   ║
# ╚════════════╝
```

### Formatted Titles

```python
print(ui.section_title("DIAGNOSTIC RESULTS"))
# Output: DIAGNOSTIC RESULTS (in cyan)
```

## Symbols Reference

Available symbols for use:
- `SUCCESS` = '✓'
- `FAILURE` = '✗'
- `WARNING` = '⚠'
- `INFO` = 'ℹ'
- `ARROW` = '→'
- `BULLET` = '•'

Access with: `ui.SYMBOLS['SUCCESS']`

## Color Support

Colors are automatically applied when terminal supports them:
- `RESET` - Reset formatting
- `BOLD` - Bold text
- `DIM` - Dimmed text
- `CYAN` - Cyan color
- `GREEN` - Green color
- `YELLOW` - Yellow color
- `RED` - Red color
- `MAGENTA` - Magenta color
- `WHITE` - White color

## Real-World Example

```python
def run_diagnostic():
    ui = UIFormatter()
    
    # Header
    print(ui.header("HVAC DIAGNOSTIC SYSTEM"))
    
    # Status
    print(ui.success("Connected to vehicle", indent=2))
    print(ui.success("Protocol initialized", indent=2))
    
    # Section
    print(ui.subheader("Reading Diagnostic Codes"))
    
    # Results
    print(ui.success("Found 2 active codes:", indent=2))
    codes = ["P0400: EGR System Flow", "P0401: EGR Flow Insufficient"]
    print(ui.list_items(codes, indent=4))
    
    # Summary
    print(ui.header("SUMMARY"))
    print(ui.key_value_pair("Status", "Codes Found", indent=2))
    print(ui.key_value_pair("Action", "See technician", indent=2))
```

## Tips & Best Practices

1. **Use consistent indentation** for nested items
2. **Use headers** to separate major sections
3. **Use icons** to show status at a glance
4. **Use lists** for multiple related items
5. **Use key-value pairs** for diagnostic data
6. **Avoid excessive nesting** (max 3-4 levels)
7. **Use color-coded messages** for quick scanning
8. **Keep lines readable** (max ~80 characters)

## Terminal Compatibility

- ✅ Windows 10+ with ANSI support
- ✅ Windows 11
- ✅ Linux (all major distros)
- ✅ macOS
- ✅ Falls back gracefully on unsupported terminals (no colors, but still readable)
