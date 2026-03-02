"""Pydantic Contract Example.

This module demonstrates how to define contracts using Pydantic models.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime


class TaskMetadata(BaseModel):
    """Metadata for a task."""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: str = "1.0"


class TaskItem(BaseModel):
    """Individual item in a task."""
    id: str = Field(..., description="Item identifier")
    name: str = Field(..., min_length=1, description="Item name")
    value: float = Field(default=0.0, ge=0, description="Item value")


class TaskContract(BaseModel):
    """Contract for task input validation.

    Example usage:
        data = {"task_id": "TASK-001", "action": "create", "items": [...]}
        contract = TaskContract(**data)
    """
    task_id: str = Field(..., pattern=r"^[A-Z]+-[0-9]+$")
    action: Literal["create", "read", "update", "delete"]
    items: List[TaskItem] = Field(default_factory=list)
    metadata: Optional[TaskMetadata] = None

    @field_validator('items')
    @classmethod
    def validate_items(cls, v, info):
        """Ensure items are valid for the action type."""
        if info.data.get('action') == 'create' and len(v) == 0:
            raise ValueError('Create action requires at least one item')
        return v

    class Config:
        """Pydantic configuration."""
        extra = 'forbid'  # Reject unknown fields


def validate(data: dict) -> tuple[bool, str]:
    """Validate data against TaskContract.

    Args:
        data: Dictionary to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        TaskContract(**data)
        return True, ""
    except Exception as e:
        return False, str(e)


if __name__ == '__main__':
    # Test validation
    test_data = {
        "task_id": "TASK-001",
        "action": "create",
        "items": [{"id": "1", "name": "Test", "value": 10.0}]
    }
    valid, error = validate(test_data)
    print(f"Valid: {valid}, Error: {error}")
