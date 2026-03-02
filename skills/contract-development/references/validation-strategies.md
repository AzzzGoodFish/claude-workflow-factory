# Validation Strategies

## Strategy 1: Schema-Only Validation

Use JSON Schema or YAML Schema for simple validation:

```python
import jsonschema

def validate_with_jsonschema(data: dict, schema: dict) -> tuple[bool, str]:
    try:
        jsonschema.validate(data, schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, e.message
```

**Best for:** Simple type checking, required fields, basic constraints.

## Strategy 2: Pydantic Validation

Use Pydantic for complex Python objects:

```python
from pydantic import BaseModel, ValidationError

def validate_with_pydantic(data: dict, model: type) -> tuple[bool, str]:
    try:
        model(**data)
        return True, ""
    except ValidationError as e:
        return False, str(e)
```

**Best for:** Nested objects, type coercion, custom validators.

## Strategy 3: Custom Script Validation

Use Python scripts for business logic:

```python
def validate_custom(data: dict) -> tuple[bool, str]:
    errors = []

    # Business rule: amount must match items total
    if 'amount' in data and 'items' in data:
        total = sum(item.get('price', 0) for item in data['items'])
        if data['amount'] != total:
            errors.append(f"Amount {data['amount']} != items total {total}")

    return len(errors) == 0, "; ".join(errors)
```

**Best for:** Complex business rules, cross-field validation.

## Strategy 4: Layered Validation

Combine multiple strategies:

```python
def validate_layered(data: dict, schema: dict, model: type) -> tuple[bool, str]:
    # Layer 1: Schema validation
    valid, error = validate_with_jsonschema(data, schema)
    if not valid:
        return False, f"Schema error: {error}"

    # Layer 2: Type validation
    valid, error = validate_with_pydantic(data, model)
    if not valid:
        return False, f"Type error: {error}"

    # Layer 3: Business rules
    valid, error = validate_custom(data)
    if not valid:
        return False, f"Business rule error: {error}"

    return True, ""
```

## Choosing a Strategy

| Scenario | Recommended Strategy |
|----------|---------------------|
| Simple field validation | Schema-Only |
| Complex nested objects | Pydantic |
| Business logic rules | Custom Script |
| High-stakes validation | Layered |
