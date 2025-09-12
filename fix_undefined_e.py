#!/usr/bin/env python3
"""Fix undefined 'e' references by removing incorrect 'from e' clauses."""

import subprocess


def fix_undefined_e_references(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Remove ' from e' where there's no exception variable 'e' in scope
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            if " from e" in line and "raise HTTPException" in line:
                # Check if we're in an except block with 'as e'
                in_except_block = False

                # Look backwards to find if we're in an except block
                for j in range(i - 1, max(0, i - 20), -1):
                    prev_line = lines[j].strip()
                    if prev_line.startswith("except ") and " as e:" in prev_line:
                        in_except_block = True
                        break
                    elif prev_line.startswith(("def ", "class ", "try:", "@")):
                        break

                if not in_except_block:
                    # Remove the ' from e' part
                    line = line.replace(" from e", "")

            fixed_lines.append(line)

        content = "\n".join(fixed_lines)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False


def main():
    # Find all Python files that have F821 errors
    result = subprocess.run(["python", "-m", "ruff", "check", "."], capture_output=True, text=True)

    f821_files = set()
    for line in result.stdout.split("\n"):
        if "F821" in line and "Undefined name `e`" in line:
            file_path = line.split(":")[0]
            f821_files.add(file_path)

    fixed_count = 0
    for file_path in f821_files:
        if fix_undefined_e_references(file_path):
            fixed_count += 1
            print(f"Fixed: {file_path}")

    print(f"Fixed undefined e references in {fixed_count} files")


if __name__ == "__main__":
    main()
