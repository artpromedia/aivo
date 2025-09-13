#!/usr/bin/env python3
"""
Fix remaining format validation issues in OpenAPI specifications.
This script specifically addresses:
- Date-time format examples
- Email format examples
- URI format examples
- Enum value examples
- Pattern matching issues
"""

import yaml
import re
from datetime import datetime, timezone
from pathlib import Path

def generate_valid_example(format_type, enum_values=None, pattern=None):
    """Generate valid examples for different formats."""

    if enum_values:
        return enum_values[0]  # Return first valid enum value

    if format_type == 'date-time':
        return datetime.now(timezone.utc).isoformat()
    elif format_type == 'email':
        return "user@example.com"
    elif format_type == 'uri':
        return "https://example.com"
    elif format_type == 'uuid':
        import uuid
        return str(uuid.uuid4())
    elif pattern and pattern == r'^\\d+\\.\\d+\\.\\d+$':
        return "1.0.0"

    return None

def fix_schema_examples(data, parent_key=None):
    """Recursively fix invalid examples in schema definitions."""
    changes_made = False

    if isinstance(data, dict):
        # Check if this is a property with format and example
        if 'format' in data and 'example' in data:
            format_type = data['format']
            current_example = data['example']
            enum_values = data.get('enum')
            pattern = data.get('pattern')

            new_example = generate_valid_example(format_type, enum_values, pattern)
            if new_example and new_example != current_example:
                data['example'] = new_example
                changes_made = True
                print(f"    ✅ Fixed {format_type} example: {current_example} → {new_example}")

        # Check for enum without format but with invalid example
        elif 'enum' in data and 'example' in data:
            enum_values = data['enum']
            current_example = data['example']
            if current_example not in enum_values:
                data['example'] = enum_values[0]
                changes_made = True
                print(f"    ✅ Fixed enum example: {current_example} → {enum_values[0]}")

        # Handle special case for array examples with UUIDs
        elif 'items' in data and 'example' in data and isinstance(data['example'], list):
            if 'format' in data['items'] and data['items']['format'] == 'uuid':
                import uuid
                new_examples = [str(uuid.uuid4()) for _ in data['example']]
                data['example'] = new_examples
                changes_made = True
                print(f"    ✅ Fixed UUID array examples")

        # Handle pattern matching
        elif 'pattern' in data and 'example' in data:
            pattern = data['pattern']
            if pattern == r'^\\d+\\.\\d+\\.\\d+$' or pattern == '^\\d+\\.\\d+\\.\\d+$':
                data['example'] = "1.0.0"
                changes_made = True
                print(f"    ✅ Fixed pattern example for version")

        # Recursively process nested objects
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                if fix_schema_examples(value, key):
                    changes_made = True

    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                if fix_schema_examples(item):
                    changes_made = True

    return changes_made

def fix_notification_issues(spec):
    """Fix specific issues in notification.yaml."""
    changes_made = False

    # Add missing contact info
    if 'info' in spec and 'contact' not in spec['info']:
        spec['info']['contact'] = {
            'name': 'Aivo API Support',
            'email': 'api-support@aivo.com',
            'url': 'https://aivo.com/support'
        }
        changes_made = True
        print(f"    ✅ Added contact information")

    # Fix WebSocket endpoint response
    if 'paths' in spec and '/ws/notify' in spec['paths']:
        ws_path = spec['paths']['/ws/notify']
        if 'get' in ws_path and 'responses' in ws_path['get']:
            responses = ws_path['get']['responses']

            # Add missing success response
            if '101' not in responses:
                responses['101'] = {
                    'description': 'Switching Protocols - WebSocket connection established',
                    'headers': {
                        'Upgrade': {
                            'description': 'Upgrade to WebSocket',
                            'schema': {'type': 'string', 'example': 'websocket'}
                        },
                        'Connection': {
                            'description': 'Connection upgrade',
                            'schema': {'type': 'string', 'example': 'Upgrade'}
                        }
                    }
                }
                changes_made = True
                print(f"    ✅ Added WebSocket success response")

    return changes_made

def fix_openapi_examples(file_path):
    """Fix format validation issues in a single OpenAPI file."""
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

    # Fix examples in components/schemas
    if 'components' in spec and 'schemas' in spec['components']:
        if fix_schema_examples(spec['components']['schemas']):
            changes_made = True

    # Fix notification-specific issues
    if file_path.name == 'notification.yaml':
        if fix_notification_issues(spec):
            changes_made = True

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
        print(f"  ℹ️  No format issues found in {file_path}")
        return True

def main():
    yaml_dir = Path("docs/api/rest")
    if not yaml_dir.exists():
        print(f"Directory {yaml_dir} not found!")
        return

    # Focus on files with known format issues
    target_files = [
        'admin-portal.yaml',
        'auth.yaml',
        'enrollment.yaml',
        'event-collector.yaml',
        'learner.yaml',
        'orchestrator.yaml',
        'payments.yaml',
        'problem-session.yaml',
        'slp-sel.yaml',
        'subject-brain.yaml',
        'tenant.yaml',
        'notification.yaml',
        'edge-bundler.yaml'
    ]

    yaml_files = [yaml_dir / filename for filename in target_files if (yaml_dir / filename).exists()]

    if not yaml_files:
        print(f"No target YAML files found in {yaml_dir}")
        return

    print(f"Found {len(yaml_files)} YAML files to process")

    success_count = 0
    for yaml_file in yaml_files:
        if fix_openapi_examples(yaml_file):
            success_count += 1
        print()  # Empty line between files

    print(f"Processed {success_count}/{len(yaml_files)} files successfully")

if __name__ == "__main__":
    main()
