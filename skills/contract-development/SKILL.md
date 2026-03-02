---
name: Contract Development
description: This skill should be used when the user asks to "create a contract", "define data schema", "add input/output validation", "implement contract validation", "design workflow contracts", or mentions contract-desc, contract-validator, Pydantic schema, YAML schema, or data validation for Claude Code workflows.
version: 0.1.0
---

# Contract Development for Claude Code Workflows

## Overview

Contracts define data specifications and validation rules for workflow nodes. A contract consists of two parts:
- **contract-desc**: Schema definition (YAML/JSON/Pydantic)
- **contract-validator**: Validation script (optional, for complex rules)

Contracts ensure data consistency between workflow nodes and enable early error detection.

## Contract Types

### Schema-Only Contracts

Use when validation is straightforward schema matching:

```yaml
# contracts/node-input.yaml
type: object
required:
  - task_id
  - input_data
properties:
  task_id:
    type: string
    pattern: "^[A-Z]+-[0-9]+$"
  input_data:
    type: object
```

### Schema + Validator Contracts

Use when validation requires complex logic:

```
contracts/
├── node-input.yaml      # Schema definition
└── node-input.py        # Custom validation logic
```

## Contract Schema Formats

### YAML Schema (Recommended)

```yaml
# contracts/example-contract.yaml
name: ExampleContract
version: "1.0"
description: Contract for example node input

schema:
  type: object
  required:
    - id
    - data
  properties:
    id:
      type: string
      description: Unique identifier
    data:
      type: object
      properties:
        name:
          type: string
          minLength: 1
        value:
          type: number
          minimum: 0
```

### JSON Schema

```json
{
  "name": "ExampleContract",
  "version": "1.0",
  "schema": {
    "type": "object",
    "required": ["id", "data"],
    "properties": {
      "id": {"type": "string"},
      "data": {"type": "object"}
    }
  }
}
```

### Pydantic Schema

```python
# contracts/example_contract.py
from pydantic import BaseModel, Field
from typing import Optional

class ExampleContract(BaseModel):
    id: str = Field(..., description="Unique identifier")
    data: dict = Field(..., description="Data payload")
    metadata: Optional[dict] = None
```

## Contract Validator Scripts

### Basic Validator Structure

```python
#!/usr/bin/env python3
"""Contract validator for node input/output."""
import sys
import json
import yaml
from pathlib import Path

def load_schema(schema_path: Path) -> dict:
    """Load schema from YAML or JSON file."""
    content = schema_path.read_text()
    if schema_path.suffix in ['.yaml', '.yml']:
        return yaml.safe_load(content)
    return json.loads(content)

def validate(data: dict, schema: dict) -> tuple[bool, str]:
    """Validate data against schema."""
    # Implementation depends on schema format
    # Return (True, "") on success
    # Return (False, "error message") on failure
    pass

def main():
    # Read input from stdin (hook input format)
    hook_input = json.loads(sys.stdin.read())

    # Extract data to validate
    data = hook_input.get('tool_input', {})

    # Load and validate against schema
    schema_path = Path(__file__).parent / 'schema.yaml'
    schema = load_schema(schema_path)

    valid, error = validate(data, schema)

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
```

### Validation with Pydantic

```python
#!/usr/bin/env python3
from pydantic import ValidationError
from .schema import ExampleContract

def validate_with_pydantic(data: dict) -> tuple[bool, str]:
    try:
        ExampleContract(**data)
        return True, ""
    except ValidationError as e:
        return False, str(e)
```

## Integration with Hooks

### Hook Configuration

Contracts integrate with the global `contract-validator.py` hook:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/contract-validator.py --event PreToolUse"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/contract-validator.py --event PostToolUse"
          }
        ]
      }
    ]
  }
}
```

### Contract Discovery

The global validator discovers contracts by:
1. Parsing hook input to identify current node
2. Looking up contract in `contracts/` directory
3. Matching by node name convention: `{node-name}-input.yaml`, `{node-name}-output.yaml`

## Contract Design Principles

### Single Responsibility

Each contract validates one data boundary:
- Node input contract
- Node output contract
- Workflow final output contract

### Explicit Over Implicit

Define all required fields explicitly:

```yaml
# Good: Explicit requirements
required:
  - task_id
  - status
  - result

# Avoid: Implicit assumptions
# (no required fields defined)
```

### Fail Fast

Validate early, provide clear error messages:

```python
def validate(data):
    errors = []
    if 'id' not in data:
        errors.append("Missing required field: id")
    if 'type' in data and data['type'] not in VALID_TYPES:
        errors.append(f"Invalid type: {data['type']}")
    return len(errors) == 0, "; ".join(errors)
```

## Contract File Organization

```
workflow-project/
├── contracts/
│   ├── README.md              # Contract documentation
│   ├── node1-input.yaml       # Node 1 input schema
│   ├── node1-output.yaml      # Node 1 output schema
│   ├── node2-input.yaml       # Node 2 input schema
│   ├── node2-output.py        # Node 2 output (Pydantic)
│   └── workflow-output.yaml   # Final workflow output
└── hooks/
    └── contract-validator.py  # Global validator
```

## Quick Reference

### Schema Field Types

| Type | YAML | JSON Schema | Pydantic |
|------|------|-------------|----------|
| String | `type: string` | `"type": "string"` | `str` |
| Number | `type: number` | `"type": "number"` | `float` |
| Integer | `type: integer` | `"type": "integer"` | `int` |
| Boolean | `type: boolean` | `"type": "boolean"` | `bool` |
| Array | `type: array` | `"type": "array"` | `list` |
| Object | `type: object` | `"type": "object"` | `dict` |

### Common Constraints

```yaml
# String constraints
minLength: 1
maxLength: 100
pattern: "^[a-z]+$"

# Number constraints
minimum: 0
maximum: 100
exclusiveMinimum: 0

# Array constraints
minItems: 1
maxItems: 10
uniqueItems: true

# Object constraints
additionalProperties: false
```

## Additional Resources

### Reference Files

- **`references/patterns.md`** - Common contract patterns
- **`references/validation-strategies.md`** - Validation implementation strategies

### Example Files

- **`examples/simple-contract.yaml`** - Basic YAML schema
- **`examples/pydantic-contract.py`** - Pydantic model example
- **`examples/validator-script.py`** - Complete validator script

## Implementation Workflow

To create a contract:

1. **Identify data boundary**: Input or output of which node?
2. **Define schema**: Choose format (YAML/JSON/Pydantic)
3. **Specify constraints**: Required fields, types, validation rules
4. **Create validator** (if needed): For complex validation logic
5. **Register with hooks**: Configure in hooks.json
6. **Test validation**: Verify with sample data
7. **Document**: Add to contracts/README.md

Focus on clear schema definitions and explicit validation rules. Use Pydantic for complex nested structures or when Python type hints improve clarity.
