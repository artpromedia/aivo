#!/usr/bin/env python3
"""
Fix OpenAPI specification issues found by Spectral linting.
This script addresses common OpenAPI validation issues:
- Missing operation descriptions
- Missing operationIds
- Missing tags
- Missing parameter descriptions
- Invalid UUID examples
- Server URL pointing to example.com
"""

import yaml
import os
import re
import uuid
from pathlib import Path

def generate_operation_id(method, path):
    """Generate a reasonable operationId from method and path."""
    # Remove path parameters and clean up
    clean_path = re.sub(r'\{[^}]+\}', 'By', path)
    clean_path = re.sub(r'[^a-zA-Z0-9]', ' ', clean_path)

    # Convert to camelCase
    words = clean_path.split()
    words = [w for w in words if w]  # Remove empty strings

    if not words:
        return f"{method}Root"

    # First word lowercase, rest title case
    operation_id = method.lower() + ''.join(word.capitalize() for word in words)
    return operation_id

def generate_description(method, path):
    """Generate a reasonable description from method and path."""
    action_map = {
        'get': 'Retrieve',
        'post': 'Create',
        'put': 'Update',
        'delete': 'Delete',
        'patch': 'Partially update'
    }

    # Extract resource from path
    path_parts = [p for p in path.split('/') if p and not p.startswith('{')]
    if path_parts:
        resource = path_parts[-1].replace('-', ' ').title()
        action = action_map.get(method.lower(), method.upper())

        if method.lower() == 'get' and '{' in path:
            return f"{action} a specific {resource.rstrip('s')}"
        elif method.lower() == 'get':
            return f"{action} all {resource}"
        elif method.lower() == 'post':
            return f"{action} a new {resource.rstrip('s')}"
        elif method.lower() in ['put', 'patch']:
            return f"{action} a {resource.rstrip('s')}"
        elif method.lower() == 'delete':
            return f"{action} a {resource.rstrip('s')}"

    return f"{method.upper()} operation for {path}"

def fix_uuid_examples(data):
    """Fix invalid UUID examples in schema properties."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'example' and isinstance(value, str):
                # Check if this should be a UUID (based on format or parent context)
                parent_has_uuid_format = False
                if 'format' in data and data['format'] == 'uuid':
                    parent_has_uuid_format = True

                # Try to identify if it's meant to be a UUID but isn't valid
                if parent_has_uuid_format or (len(value) > 10 and not is_valid_uuid(value)):
                    try:
                        # Generate a valid UUID
                        data[key] = str(uuid.uuid4())
                    except:
                        pass
            elif isinstance(value, (dict, list)):
                fix_uuid_examples(value)
    elif isinstance(data, list):
        for item in data:
            fix_uuid_examples(item)

def is_valid_uuid(value):
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except:
        return False

def ensure_global_tags(spec, operation_tags):
    """Ensure all operation tags are defined in global tags."""
    if 'tags' not in spec:
        spec['tags'] = []

    existing_tags = {tag['name'] for tag in spec['tags'] if isinstance(tag, dict) and 'name' in tag}

    for tag_name in operation_tags:
        if tag_name not in existing_tags:
            spec['tags'].append({
                'name': tag_name,
                'description': f"{tag_name.title()} operations"
            })

def infer_tags_from_path(path):
    """Infer reasonable tags from the API path."""
    path_parts = [p for p in path.split('/') if p and not p.startswith('{')]
    if path_parts:
        # Use the first meaningful path segment as tag
        return [path_parts[0].replace('-', '_')]
    return ['api']

def fix_openapi_file(file_path):
    """Fix OpenAPI issues in a single file."""
    print(f"Processing {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        spec = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  ❌ YAML parsing error: {e}")
        return False

    if not isinstance(spec, dict):
        print(f"  ❌ Invalid OpenAPI structure")
        return False

    changes_made = False
    all_operation_tags = set()

    # Fix server URLs pointing to example.com
    if 'servers' in spec and isinstance(spec['servers'], list):
        for server in spec['servers']:
            if isinstance(server, dict) and 'url' in server:
                if 'example.com' in server['url']:
                    server['url'] = server['url'].replace('example.com', 'api.aivo.com')
                    changes_made = True
                    print(f"  ✅ Fixed server URL")

    # Process paths
    if 'paths' in spec and isinstance(spec['paths'], dict):
        for path, path_obj in spec['paths'].items():
            if not isinstance(path_obj, dict):
                continue

            for method, operation in path_obj.items():
                if method.startswith('x-') or not isinstance(operation, dict):
                    continue

                # Add missing description
                if 'description' not in operation or not operation['description']:
                    operation['description'] = generate_description(method, path)
                    changes_made = True
                    print(f"  ✅ Added description for {method.upper()} {path}")

                # Add missing operationId
                if 'operationId' not in operation:
                    operation['operationId'] = generate_operation_id(method, path)
                    changes_made = True
                    print(f"  ✅ Added operationId for {method.upper()} {path}")

                # Add missing tags
                if 'tags' not in operation or not operation['tags']:
                    operation['tags'] = infer_tags_from_path(path)
                    changes_made = True
                    print(f"  ✅ Added tags for {method.upper()} {path}")

                # Collect all tags for global tags section
                if 'tags' in operation:
                    all_operation_tags.update(operation['tags'])

                # Add missing parameter descriptions
                if 'parameters' in operation and isinstance(operation['parameters'], list):
                    for param in operation['parameters']:
                        if isinstance(param, dict) and 'description' not in param:
                            param_name = param.get('name', 'parameter')
                            param_type = param.get('in', 'query')
                            param['description'] = f"The {param_name} {param_type} parameter"
                            changes_made = True
                            print(f"  ✅ Added parameter description for {param_name}")

    # Ensure global tags are defined
    if all_operation_tags:
        original_tags_count = len(spec.get('tags', []))
        ensure_global_tags(spec, all_operation_tags)
        new_tags_count = len(spec.get('tags', []))
        if new_tags_count > original_tags_count:
            changes_made = True
            print(f"  ✅ Added {new_tags_count - original_tags_count} global tag definitions")

    # Fix UUID examples in components/schemas
    if 'components' in spec and 'schemas' in spec['components']:
        old_content = yaml.dump(spec['components']['schemas'])
        fix_uuid_examples(spec['components']['schemas'])
        new_content = yaml.dump(spec['components']['schemas'])
        if old_content != new_content:
            changes_made = True
            print(f"  ✅ Fixed UUID examples in schemas")

    # Write back if changes were made
    if changes_made:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            print(f"  ✅ Successfully updated {file_path}")
            return True
        except Exception as e:
            print(f"  ❌ Error writing file: {e}")
            return False
    else:
        print(f"  ℹ️  No changes needed for {file_path}")
        return True

def main():
    yaml_dir = Path("docs/api/rest")
    if not yaml_dir.exists():
        print(f"Directory {yaml_dir} not found!")
        return

    yaml_files = list(yaml_dir.glob("*.yaml")) + list(yaml_dir.glob("*.yml"))

    if not yaml_files:
        print(f"No YAML files found in {yaml_dir}")
        return

    print(f"Found {len(yaml_files)} YAML files to process")

    success_count = 0
    for yaml_file in yaml_files:
        if fix_openapi_file(yaml_file):
            success_count += 1
        print()  # Empty line between files

    print(f"Processed {success_count}/{len(yaml_files)} files successfully")

if __name__ == "__main__":
    main()
