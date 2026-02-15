#!/usr/bin/env python3
"""
Generate GitHub issues from tasks.md

Usage:
    python scripts/generate_github_issues.py

This script reads .kiro/specs/ai-vehicle-diagnostic-agent/tasks.md
and generates GitHub issue markdown files in .github/issues/
"""

import re
import os
from pathlib import Path

def parse_tasks_md(filepath):
    """Parse tasks.md and extract task information"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tasks = []
    current_task = None
    current_subtask = None
    
    lines = content.split('\n')
    for line in lines:
        # Main task: - [ ] 1. Task name
        main_task_match = re.match(r'^- \[ \] (\d+)\. (.+)$', line)
        if main_task_match:
            if current_task:
                tasks.append(current_task)
            
            task_num = main_task_match.group(1)
            task_name = main_task_match.group(2)
            current_task = {
                'number': task_num,
                'name': task_name,
                'subtasks': [],
                'description': '',
                'requirements': []
            }
            current_subtask = None
            continue
        
        # Subtask: - [ ] 1.1 Subtask name
        subtask_match = re.match(r'^  - \[ \](\*)? (\d+\.\d+) (.+)$', line)
        if subtask_match and current_task:
            optional = subtask_match.group(1) == '*'
            subtask_num = subtask_match.group(2)
            subtask_name = subtask_match.group(3)
            current_subtask = {
                'number': subtask_num,
                'name': subtask_name,
                'optional': optional,
                'description': [],
                'requirements': []
            }
            current_task['subtasks'].append(current_subtask)
            continue
        
        # Description line (indented under subtask)
        if line.startswith('    ') and current_subtask:
            desc_line = line.strip()
            if desc_line.startswith('_Requirements:'):
                # Extract requirements
                reqs = desc_line.replace('_Requirements:', '').replace('_', '').strip()
                current_subtask['requirements'] = [r.strip() for r in reqs.split(',')]
            elif desc_line and not desc_line.startswith('-'):
                current_subtask['description'].append(desc_line)
    
    if current_task:
        tasks.append(current_task)
    
    return tasks

def generate_issue_markdown(task, subtask=None):
    """Generate GitHub issue markdown for a task or subtask"""
    if subtask:
        title = f"[AI-AGENT] {subtask['number']} {subtask['name']}"
        number = subtask['number']
        name = subtask['name']
        description = '\n'.join(subtask['description'])
        requirements = subtask['requirements']
        optional = subtask['optional']
    else:
        title = f"[AI-AGENT] {task['number']}. {task['name']}"
        number = task['number']
        name = task['name']
        description = task['description']
        requirements = task['requirements']
        optional = False
    
    # Build issue content
    content = f"""---
title: "{title}"
labels: ai-agent, enhancement{', optional' if optional else ''}
---

## Task {number}: {name}

### Description

{description if description else 'See tasks.md for details'}

### Requirements

"""
    
    if requirements:
        for req in requirements:
            content += f"- Requirements {req}\n"
    else:
        content += "- See tasks.md\n"
    
    content += """
### Acceptance Criteria

"""
    
    if subtask:
        content += f"- [ ] {subtask['name']}\n"
        if subtask['description']:
            for desc in subtask['description']:
                content += f"- [ ] {desc}\n"
    else:
        content += f"- [ ] Complete all subtasks for task {number}\n"
        for st in task['subtasks']:
            content += f"- [ ] {st['number']} {st['name']}\n"
    
    content += """
### Testing

- [ ] Unit tests written and passing
"""
    
    if 'property test' in name.lower() or (subtask and 'property test' in subtask['name'].lower()):
        content += "- [ ] Property-based tests written and passing\n"
    
    content += """
### Dependencies

"""
    
    if subtask:
        parent_num = subtask['number'].split('.')[0]
        content += f"- Depends on: Task {parent_num} setup\n"
    else:
        prev_num = int(number) - 1
        if prev_num > 0:
            content += f"- Depends on: Task {prev_num} completion\n"
    
    content += """
### Definition of Done

- [ ] Code implemented and follows project standards
- [ ] Tests written and passing
- [ ] Documentation updated (if applicable)
- [ ] Task marked as complete in tasks.md
"""
    
    return content

def main():
    """Main function"""
    # Parse tasks.md
    tasks_file = Path('.kiro/specs/ai-vehicle-diagnostic-agent/tasks.md')
    if not tasks_file.exists():
        print(f"Error: {tasks_file} not found")
        return
    
    print(f"Parsing {tasks_file}...")
    tasks = parse_tasks_md(tasks_file)
    print(f"Found {len(tasks)} main tasks")
    
    # Create output directory
    output_dir = Path('.github/issues')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate issue files
    issue_count = 0
    for task in tasks:
        # Generate main task issue
        task_file = output_dir / f"task-{task['number'].zfill(2)}.md"
        with open(task_file, 'w', encoding='utf-8') as f:
            f.write(generate_issue_markdown(task))
        print(f"Generated: {task_file}")
        issue_count += 1
        
        # Generate subtask issues
        for subtask in task['subtasks']:
            subtask_num = subtask['number'].replace('.', '-')
            subtask_file = output_dir / f"task-{subtask_num}.md"
            with open(subtask_file, 'w', encoding='utf-8') as f:
                f.write(generate_issue_markdown(task, subtask))
            print(f"Generated: {subtask_file}")
            issue_count += 1
    
    print(f"\n✓ Generated {issue_count} GitHub issue files in {output_dir}")
    print("\nTo create issues on GitHub:")
    print("1. Go to your GitHub repository")
    print("2. Click 'Issues' → 'New Issue'")
    print("3. Copy/paste content from each .md file in .github/issues/")
    print("\nOr use GitHub CLI:")
    print("  gh issue create --title \"[AI-AGENT] Task X\" --body-file .github/issues/task-XX.md")

if __name__ == '__main__':
    main()
