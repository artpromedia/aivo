#!/usr/bin/env python3
"""
YAML Fixer Script
Fixes common YAML linting issues in OpenAPI specification files.
"""

import yaml
import re
import os

def fix_yaml_file(filepath):
    """Fix common YAML issues in a file."""
    print(f"Processing {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Track changes
        original_content = content

        # Fix 1: Ensure consistent 2-space indentation
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                fixed_lines.append(line)
                continue

            # Calculate indentation level
            stripped = line.lstrip()
            if not stripped:
                fixed_lines.append('')
                continue

            # Count leading spaces
            leading_spaces = len(line) - len(stripped)

            # If indentation is not multiple of 2, fix it
            if leading_spaces % 2 != 0:
                # Round to nearest even number
                correct_spaces = ((leading_spaces + 1) // 2) * 2
                fixed_line = ' ' * correct_spaces + stripped
                fixed_lines.append(fixed_line)
                print(f"  Fixed indentation: '{line[:20]}...' -> '{fixed_line[:20]}...'")
            else:
                fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        # Fix 2: Ensure trailing newline
        if not content.endswith('\n'):
            content += '\n'

        # Fix 3: Remove trailing whitespace
        lines = content.split('\n')
        fixed_lines = [line.rstrip() for line in lines]
        content = '\n'.join(fixed_lines)

        # Fix 4: Validate YAML structure
        try:
            yaml.safe_load(content)
            print(f"  ✓ YAML is valid")
        except yaml.YAMLError as e:
            print(f"  ✗ YAML error: {e}")
            return False

        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Fixed and saved {filepath}")
        else:
            print(f"  ✓ No changes needed for {filepath}")

        return True

    except Exception as e:
        print(f"  ✗ Error processing {filepath}: {e}")
        return False

def main():
    """Fix all YAML files in docs/api/rest/."""
    yaml_files = [
        'docs/api/rest/event-collector.yaml',
        'docs/api/rest/ink.yaml',
        'docs/api/rest/lesson-registry.yaml',
        'docs/api/rest/notification.yaml',
        'docs/api/rest/problem-session.yaml',
        'docs/api/rest/search.yaml',
        'docs/api/rest/slp-sel.yaml'
    ]

    success_count = 0
    for yaml_file in yaml_files:
        if os.path.exists(yaml_file):
            if fix_yaml_file(yaml_file):
                success_count += 1
        else:
            print(f"File not found: {yaml_file}")

    print(f"\nProcessed {success_count}/{len(yaml_files)} files successfully")

if __name__ == "__main__":
    main()
