#!/usr/bin/env python3
"""Contract Validator Script Example.

This script demonstrates how to implement a contract validator
that integrates with Claude Code hooks.
"""
import sys
import json
import yaml
from pathlib import Path
from typing import Tuple


def load_schema(schema_path: Path) -> dict:
    """Load schema from YAML or JSON file."""
    content = schema_path.read_text()
    if schema_path.suffix in ['.yaml', '.yml']:
        return yaml.safe_load(content)
    return json.loads(content)


def validate_type(value, expected_type: str) -> bool:
    """Validate value against expected type."""
    type_map = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict,
    }
    return isinstance(value, type_map.get(expected_type, object))


def validate_schema(data: dict, schema: dict) -> Tuple[bool, str]:
    """Validate data against schema definition."""
    errors = []
    schema_def = schema.get('schema', schema)

    # Check required fields
    required = schema_def.get('required', [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check property types
    properties = schema_def.get('properties', {})
    for field, value in data.items():
        if field in properties:
            prop_def = properties[field]
            expected_type = prop_def.get('type')
            if expected_type and not validate_type(value, expected_type):
                errors.append(
                    f"Field '{field}' expected {expected_type}, "
                    f"got {type(value).__name__}"
                )

    return len(errors) == 0, "; ".join(errors)


def main():
    """Main entry point for hook execution."""
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({
            "continue": False,
            "systemMessage": f"Invalid JSON input: {e}"
        }), file=sys.stderr)
        sys.exit(2)

    # Extract data to validate
    data = hook_input.get('tool_input', {})

    # Determine schema path
    script_dir = Path(__file__).parent
    schema_path = script_dir / 'simple-contract.yaml'

    if not schema_path.exists():
        print(json.dumps({"continue": True}))
        sys.exit(0)

    # Load and validate
    schema = load_schema(schema_path)
    valid, error = validate_schema(data, schema)

    if valid:
        print(json.dumps({"continue": True}))
        sys.exit(0)
    else:
        print(json.dumps({
            "continue": False,
            "systemMessage": f"Contract validation failed: {error}"
        }), file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
