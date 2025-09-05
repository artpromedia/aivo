#!/usr/bin/env python3
"""
Script to automatically fix long lines in Python files.
This script reads Python files and applies intelligent line wrapping
to fix lines that exceed the specified character limit.

Usage:
    python fix_long_lines.py <file_or_directory> [max_length]
    python fix_long_lines.py app/services/ 79
    python fix_long_lines.py buffer_service.py
    python fix_long_lines.py app --scan 79
"""

import sys
from pathlib import Path
from typing import List, Tuple


class LineWrapper:
    """Handles intelligent line wrapping for Python code."""
    
    def __init__(self, max_length: int = 79):
        self.max_length = max_length
        self.fixes_applied = []
    
    def fix_long_lines(self, file_path: str) -> bool:
        """Fix long lines in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_lines = lines[:]
            modified = False
            new_lines = []
            
            for i, line in enumerate(lines, 1):
                line_length = len(line.rstrip())
                if line_length > self.max_length:
                    print(f"  Line {i}: {line_length} chars -> fixing...")
                    
                    # Skip lines with explicit noqa: E501 (allow long lines)
                    if '# noqa: E501' in line:
                        print(f"    Skipping line {i} - noqa: E501")
                        new_lines.append(line)
                        continue
                    
                    fixed_lines = self._wrap_line(line, i)
                    if fixed_lines != [line]:
                        modified = True
                        new_lines.extend(fixed_lines)
                        self.fixes_applied.append(f"Line {i}: wrapped")
                    else:
                        new_lines.append(line)
                        print(f"    Could not automatically fix line {i}")
                else:
                    new_lines.append(line)
            
            if modified:
                # Backup original file
                backup_path = file_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.writelines(original_lines)
                
                # Write fixed version
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                print(f"✓ Fixed {len(self.fixes_applied)} lines in {file_path}")
                print(f"  Backup saved as {backup_path}")
                return True
            else:
                print(f"- No long lines to fix in {file_path}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            return False
    
    def _wrap_line(self, line: str, line_num: int) -> List[str]:
        """Wrap a single long line using various strategies."""
        stripped = line.rstrip()
        indent = len(line) - len(line.lstrip())
        
        # Strategy 1: Assignment statements (but not comparisons)
        # Only exclude comparison operators outside of strings
        has_assignment = False
        if '=' in stripped:
            # Check if = is part of assignment (not comparison)
            in_string = False
            quote_char = None
            for i, char in enumerate(stripped):
                if char in ['"', "'"] and (i == 0 or stripped[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                elif not in_string and char == '=':
                    # Check if it's not part of ==, !=, <=, >=
                    if (i > 0 and stripped[i-1] in '!<>'):
                        continue
                    if (i + 1 < len(stripped) and stripped[i+1] == '='):
                        continue
                    has_assignment = True
                    break
        
        if has_assignment:
            result = self._wrap_assignment(line, indent)
            if result != [line]:
                return result
        
        # Strategy 2: Function calls
        if '(' in stripped and ')' in stripped:
            result = self._wrap_function_call(line, indent)
            if result != [line]:
                return result
        
        # Strategy 3: Conditional statements
        if any(stripped.strip().startswith(kw) for kw in ['if ', 'elif ', 'while ']):
            result = self._wrap_conditional(line, indent)
            if result != [line]:
                return result
        
        # Strategy 4: Import statements
        if stripped.strip().startswith(('import ', 'from ')):
            result = self._wrap_import(line, indent)
            if result != [line]:
                return result
        
        # If no strategy worked, return original
        return [line]
    
    def _wrap_assignment(self, line: str, indent: int) -> List[str]:
        """Wrap assignment statements."""
        stripped = line.strip()
        
        # Find the assignment operator
        eq_pos = -1
        for i, char in enumerate(stripped):
            if (char == '=' and 
                (i == 0 or stripped[i-1] not in '!<>=') and 
                (i + 1 >= len(stripped) or stripped[i+1] != '=')):
                eq_pos = i
                break
        
        if eq_pos != -1:
            var_part = stripped[:eq_pos].strip()
            value_part = stripped[eq_pos + 1:].strip()
            
            # If the total line is too long, wrap it
            if len(var_part) + len(value_part) + 3 > self.max_length:
                # Special case for dictionary key assignments
                if var_part.startswith('self._') and '[' in var_part and ']' in var_part:
                    # Dictionary assignment - keep on one line if possible
                    if len(var_part) < self.max_length - 15:
                        return [
                            ' ' * indent + var_part + ' = (\n',
                            ' ' * (indent + 4) + value_part + '\n',
                            ' ' * indent + ')\n'
                        ]
                elif len(var_part) < self.max_length - 10:  # Variable name not too long
                    return [
                        ' ' * indent + var_part + ' = (\n',
                        ' ' * (indent + 4) + value_part + '\n',
                        ' ' * indent + ')\n'
                    ]
        
        return [line]
    
    def _wrap_function_call(self, line: str, indent: int) -> List[str]:
        """Wrap function calls."""
        stripped = line.strip()
        
        # Find parentheses
        paren_start = stripped.find('(')
        paren_end = stripped.rfind(')')
        
        if paren_start != -1 and paren_end != -1 and paren_end > paren_start:
            func_start = stripped[:paren_start + 1]
            args = stripped[paren_start + 1:paren_end]
            func_end = stripped[paren_end:]
            
            # If there are arguments to split
            if ',' in args and len(args) > 20:
                arg_list = self._split_arguments(args)
                if len(arg_list) > 1:
                    result = [' ' * indent + func_start + '\n']
                    for i, arg in enumerate(arg_list):
                        comma = ',' if i < len(arg_list) - 1 else ''
                        result.append(' ' * (indent + 4) + arg.strip() + comma + '\n')
                    result.append(' ' * indent + func_end + '\n')
                    return result
        
        return [line]
    
    def _wrap_conditional(self, line: str, indent: int) -> List[str]:
        """Wrap conditional statements."""
        stripped = line.strip()
        
        # Handle long conditionals with 'and' or 'or'
        if ' and ' in stripped or ' or ' in stripped:
            operators = []
            
            # Find logical operators
            for op in [' and ', ' or ']:
                pos = stripped.find(op)
                if pos != -1:
                    operators.append((op, pos))
            
            if operators:
                # Sort by position
                operators.sort(key=lambda x: x[1])
                op, pos = operators[0]  # Use first operator
                
                left_part = stripped[:pos].strip()
                right_part = stripped[pos + len(op):].strip()
                
                if len(left_part) + len(right_part) + len(op) > self.max_length:
                    return [
                        ' ' * indent + left_part + '\n',
                        ' ' * (indent + 4) + op.strip() + ' ' + right_part + '\n'
                    ]
        
        return [line]
    
    def _wrap_import(self, line: str, indent: int) -> List[str]:
        """Wrap import statements."""
        stripped = line.strip()
        
        if stripped.startswith('from ') and ' import ' in stripped:
            parts = stripped.split(' import ', 1)
            if len(parts) == 2:
                from_part = parts[0]
                import_part = parts[1]
                
                if ',' in import_part and len(import_part) > 30:
                    imports = [imp.strip() for imp in import_part.split(',')]
                    result = [' ' * indent + from_part + ' import (\n']
                    for i, imp in enumerate(imports):
                        comma = ',' if i < len(imports) - 1 else ''
                        result.append(' ' * (indent + 4) + imp + comma + '\n')
                    result.append(' ' * indent + ')\n')
                    return result
        
        return [line]
    
    def _split_arguments(self, args_str: str) -> List[str]:
        """Split function arguments respecting nested parentheses."""
        args = []
        current_arg = ""
        depth = 0
        in_string = False
        quote_char = None
        
        for char in args_str:
            if char in ['"', "'"] and not in_string:
                in_string = True
                quote_char = char
            elif char == quote_char and in_string:
                in_string = False
                quote_char = None
            elif not in_string:
                if char in ['(', '[', '{']:
                    depth += 1
                elif char in [')', ']', '}']:
                    depth -= 1
                elif char == ',' and depth == 0:
                    args.append(current_arg.strip())
                    current_arg = ""
                    continue
            
            current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args


def scan_for_long_lines(directory: str, max_length: int = 79) -> List[Tuple[str, int, int]]:
    """Scan directory for Python files with long lines."""
    long_lines = []
    
    for py_file in Path(directory).rglob('*.py'):
        try:
            with open(py_file, encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line_length = len(line.rstrip())
                    if line_length > max_length:
                        long_lines.append((str(py_file), line_num, line_length))
        except Exception as e:
            print(f"⚠ Error reading {py_file}: {e}")
    
    return long_lines


def main():
    """Main function to run the line wrapping script."""
    if len(sys.argv) < 2:
        print("Usage: python fix_long_lines.py <file_or_directory> [options]")
        print("")
        print("Examples:")
        print("  python fix_long_lines.py app/services/buffer_service.py 79")
        print("  python fix_long_lines.py app/ 79")
        print("  python fix_long_lines.py app --scan")
        print("")
        print("Options:")
        print("  --scan    Scan for long lines without fixing")
        sys.exit(1)
    
    target = sys.argv[1]
    
    # Check for scan mode
    if '--scan' in sys.argv:
        max_length = 79
        # Look for numeric arguments
        for arg in sys.argv:
            if arg.isdigit():
                max_length = int(arg)
        
        print(f"Scanning for lines longer than {max_length} characters...")
        long_lines = scan_for_long_lines(target, max_length)
        
        if long_lines:
            print(f"\nFound {len(long_lines)} long lines:")
            for file_path, line_num, length in long_lines:
                print(f"  {file_path}:{line_num} ({length} chars)")
        else:
            print("✓ No long lines found!")
        return
    
    # Regular fix mode
    max_length = 79
    for arg in sys.argv[2:]:
        if arg.isdigit():
            max_length = int(arg)
            break
    
    wrapper = LineWrapper(max_length)
    target_path = Path(target)
    
    if target_path.is_file():
        if target_path.suffix == '.py':
            print(f"Processing {target_path}...")
            wrapper.fix_long_lines(str(target_path))
        else:
            print(f"⚠ {target} is not a Python file")
    elif target_path.is_dir():
        python_files = list(target_path.rglob('*.py'))
        if not python_files:
            print(f"⚠ No Python files found in {target}")
            return
        
        print(f"Found {len(python_files)} Python files...")
        fixed_count = 0
        
        for py_file in python_files:
            print(f"\nProcessing {py_file}...")
            if wrapper.fix_long_lines(str(py_file)):
                fixed_count += 1
        
        print(f"\n✓ Processed {len(python_files)} files, fixed {fixed_count}")
    else:
        print(f"✗ {target} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    main()
