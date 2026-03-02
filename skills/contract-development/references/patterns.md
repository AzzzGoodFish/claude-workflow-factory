# Contract Patterns

## Pattern 1: Input Validation Contract

Validate node input before processing:

```yaml
name: TaskInputContract
version: "1.0"
schema:
  type: object
  required:
    - task_id
    - action
  properties:
    task_id:
      type: string
      pattern: "^[A-Z]+-[0-9]+$"
    action:
      type: string
      enum: ["create", "update", "delete"]
    payload:
      type: object
```

## Pattern 2: Output Validation Contract

Validate node output after processing:

```yaml
name: TaskOutputContract
version: "1.0"
schema:
  type: object
  required:
    - status
    - result
  properties:
    status:
      type: string
      enum: ["success", "failure", "pending"]
    result:
      type: object
    error:
      type: string
```

## Pattern 3: Workflow State Contract

Track workflow execution state:

```yaml
name: WorkflowStateContract
version: "1.0"
schema:
  type: object
  required:
    - workflow_id
    - current_node
    - status
  properties:
    workflow_id:
      type: string
    current_node:
      type: string
    status:
      type: string
      enum: ["running", "completed", "failed", "paused"]
    completed_nodes:
      type: array
      items:
        type: string
    context:
      type: object
```

## Pattern 4: Nested Object Contract

Handle complex nested structures:

```yaml
name: NestedDataContract
version: "1.0"
schema:
  type: object
  required:
    - metadata
    - items
  properties:
    metadata:
      type: object
      required:
        - created_at
        - version
      properties:
        created_at:
          type: string
          format: date-time
        version:
          type: string
    items:
      type: array
      minItems: 1
      items:
        type: object
        required:
          - id
          - name
        properties:
          id:
            type: string
          name:
            type: string
```

## Pattern 5: Conditional Validation

Different validation based on type:

```python
from pydantic import BaseModel, validator
from typing import Union, Literal

class CreateAction(BaseModel):
    action: Literal["create"]
    name: str
    template: str

class UpdateAction(BaseModel):
    action: Literal["update"]
    id: str
    changes: dict

class DeleteAction(BaseModel):
    action: Literal["delete"]
    id: str
    force: bool = False

ActionContract = Union[CreateAction, UpdateAction, DeleteAction]
```

## Pattern 6: Cross-Field Validation

Validate relationships between fields:

```python
from pydantic import BaseModel, root_validator

class DateRangeContract(BaseModel):
    start_date: str
    end_date: str

    @root_validator
    def validate_date_range(cls, values):
        start = values.get('start_date')
        end = values.get('end_date')
        if start and end and start > end:
            raise ValueError('start_date must be before end_date')
        return values
```
