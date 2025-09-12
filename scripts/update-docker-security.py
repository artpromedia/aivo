#!/usr/bin/env python3
"""
Script to update Python Dockerfiles with security improvements:
- Pin base image by digest
- Add security updates
- Use cache mounts for pip
- Set proper environment variables
- Use fixed UID for non-root user
"""

import os
import re
import sys
from pathlib import Path

# Security-hardened Python base image with digest
SECURE_BASE_IMAGE = "python:3.11-slim-bookworm@sha256:edaf703dce209d351e2c8f64a2e93b73f0f3d0f2e7b7c8b0e1b2e6a5dd77a5f4"

# Security improvements template
SECURITY_TEMPLATE = """# BEFORE: python:3.11-slim (floating) or alpine with many unfixed CVEs
# AFTER: pin by digest; bookworm slim
FROM {base_image}

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Security updates
RUN apt-get update \\
 && apt-get upgrade -y --no-install-recommends \\
{system_deps} && rm -rf /var/lib/apt/lists/*

# Keep pip/setuptools current (often fixes CVEs in resolvers/wheels)
RUN python -m pip install --upgrade pip setuptools wheel
"""

def find_python_dockerfiles(root_dir):
    """Find all Dockerfiles that use Python base images."""
    dockerfiles = []

    for dockerfile_path in Path(root_dir).rglob("Dockerfile*"):
        try:
            with open(dockerfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if re.search(r'FROM\s+python:', content, re.IGNORECASE):
                    dockerfiles.append(dockerfile_path)
        except Exception as e:
            print(f"Error reading {dockerfile_path}: {e}")

    return dockerfiles

def extract_system_dependencies(content):
    """Extract system dependencies from apt-get install commands."""
    deps = []

    # Find apt-get install patterns
    apt_patterns = [
        r'apt-get install -y[^\\n]*([^\\n]+)',
        r'apt-get install -y --no-install-recommends[^\\n]*([^\\n]+)'
    ]

    for pattern in apt_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            # Clean up the dependencies
            clean_deps = re.sub(r'[\\\s&]+', ' ', match).strip()
            if clean_deps and clean_deps not in ['rm -rf /var/lib/apt/lists/*']:
                deps.extend([dep.strip() for dep in clean_deps.split() if dep.strip()])

    return list(set(deps))  # Remove duplicates

def update_dockerfile(dockerfile_path):
    """Update a Dockerfile with security improvements."""
    try:
        with open(dockerfile_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        print(f"\\nProcessing: {dockerfile_path}")

        # Check if already updated
        if SECURE_BASE_IMAGE in original_content:
            print("  ✅ Already updated with secure base image")
            return True

        # Extract system dependencies
        system_deps = extract_system_dependencies(original_content)

        # Build system dependencies line
        if system_deps:
            deps_line = f" && apt-get install -y --no-install-recommends {' '.join(system_deps)} \\"
        else:
            deps_line = " \\"

        # Create the security template
        security_header = SECURITY_TEMPLATE.format(
            base_image=SECURE_BASE_IMAGE,
            system_deps=deps_line
        )

        # Replace FROM line and add security improvements
        updated_content = re.sub(
            r'(#.*\\n)*FROM\\s+python:[^\\n]+',
            security_header.strip(),
            original_content,
            flags=re.MULTILINE
        )

        # Update pip install commands to use cache mounts
        updated_content = re.sub(
            r'RUN\\s+pip install',
            'RUN --mount=type=cache,target=/root/.cache/pip \\\\\\n    pip install',
            updated_content
        )

        # Ensure non-root user has fixed UID
        updated_content = re.sub(
            r'RUN useradd --create-home --shell /bin/bash (\\w+)',
            r'RUN useradd --create-home --shell /bin/bash --uid 10001 \\1',
            updated_content
        )

        # Add USER directive if missing
        if 'USER ' not in updated_content and 'useradd' in updated_content:
            updated_content = re.sub(
                r'(RUN useradd[^\\n]+\\n)',
                r'\\1USER 10001\\n',
                updated_content
            )

        # Write the updated content
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  ✅ Updated successfully")
        print(f"     - Pinned base image by digest")
        print(f"     - Added security updates")
        print(f"     - Added pip cache mount")
        if system_deps:
            print(f"     - System deps: {', '.join(system_deps)}")

        return True

    except Exception as e:
        print(f"  ❌ Error updating {dockerfile_path}: {e}")
        return False

def main():
    """Main function to update all Python Dockerfiles."""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = "."

    print(f"Searching for Python Dockerfiles in: {os.path.abspath(root_dir)}")

    dockerfiles = find_python_dockerfiles(root_dir)

    if not dockerfiles:
        print("No Python Dockerfiles found.")
        return

    print(f"\\nFound {len(dockerfiles)} Python Dockerfiles:")
    for dockerfile in dockerfiles:
        print(f"  - {dockerfile}")

    print("\\n" + "="*60)
    print("UPDATING DOCKERFILES WITH SECURITY IMPROVEMENTS")
    print("="*60)

    success_count = 0
    for dockerfile in dockerfiles:
        if update_dockerfile(dockerfile):
            success_count += 1

    print(f"\\n" + "="*60)
    print(f"SUMMARY: {success_count}/{len(dockerfiles)} Dockerfiles updated successfully")
    print("="*60)

    print(f"\\n🔒 Security improvements applied:")
    print(f"   - Base image pinned by digest: {SECURE_BASE_IMAGE}")
    print(f"   - Security updates added")
    print(f"   - Pip cache mounts enabled")
    print(f"   - Fixed UID (10001) for non-root users")
    print(f"   - Environment variables optimized")

if __name__ == "__main__":
    main()
