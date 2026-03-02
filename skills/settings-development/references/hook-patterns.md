# Hook Patterns Reference

## Pattern 1: Workflow State Tracking

Track workflow execution state across nodes:

```json
{
  "UserPromptSubmit": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/wf-state.py --event UserPromptSubmit"
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
          "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/wf-state.py --event PostToolUse"
        }
      ]
    }
  ]
}
```

## Pattern 2: Contract Validation

Validate node input/output against contracts:

```json
{
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
```

## Pattern 3: Completion Verification

Verify task completion before stopping:

```json
{
  "Stop": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Verify: 1) All tasks completed 2) Tests passed 3) No errors. Return 'approve' or 'block' with reason."
        }
      ]
    }
  ]
}
```

## Pattern 4: Context Loading

Load project context at session start:

```json
{
  "SessionStart": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/load-context.sh",
          "timeout": 10
        }
      ]
    }
  ]
}
```
