#!/usr/bin/env python3
"""Fix malformed 'from e' syntax across all Python files."""

import os
import re


def fix_malformed_from_e(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix patterns like: {str(e)} -> {str(e)}
        content = re.sub(r"\{str\(e\) from e\}", r"{str(e)}", content)

        # Fix patterns like: detail=str(e)) from e -> detail=str(e)) from e
        content = re.sub(r"detail=str\(e\) from e\)", r"detail=str(e)) from e", content)

        # Fix patterns like: {str(e)}, -> {str(e)},
        content = re.sub(r"\{str\(e\) from e\},", r"{str(e)},", content)

        # Fix patterns like: "message: {str(e)}" -> "message: {str(e)}"
        content = re.sub(r'\{str\(e\) from e\}"', r'{str(e)}"', content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    return False


def main():
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    fixed_count = 0
    for file_path in python_files:
        if fix_malformed_from_e(file_path):
            fixed_count += 1
            print(f"Fixed: {file_path}")

    print(f"Fixed malformed from e syntax in {fixed_count} files")


if __name__ == "__main__":
    main()
