---
name: Settings Development
description: This skill should be used when the user asks to "create settings.json", "configure Claude Code settings", "set up hooks configuration", "configure MCP servers", "manage permissions", "create workflow settings", or mentions settings.json, hooks.json, .mcp.json, plugin configuration, or Claude Code project setup.
version: 0.1.0
---

# Settings Development for Claude Code Workflows

## Overview

Settings files configure Claude Code behavior including permissions, hooks, MCP servers, and environment variables. This skill covers creating and managing settings for workflow projects.

**Key files:**
- `settings.json` - Main configuration (permissions, hooks, env)
- `hooks/hooks.json` - Plugin hook definitions
- `.mcp.json` - MCP server configuration

## Configuration Scopes

| Scope | Location | Shared | Use Case |
|-------|----------|--------|----------|
| User | `~/.claude/settings.json` | No | Personal preferences |
| Project | `.claude/settings.json` | Yes | Team settings |
| Local | `.claude/settings.local.json` | No | Personal overrides |
| Managed | System directories | Yes | IT policies |

**Precedence (highest to lowest):**
1. Managed settings
2. Command line arguments
3. Local settings
4. Project settings
5. User settings

## Settings.json Structure

### Basic Template

```json
{
  "permissions": {
    "allow": [],
    "deny": []
  },
  "hooks": {},
  "env": {}
}
```

### Permission Configuration

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ],
    "additionalDirectories": ["../docs/"],
    "defaultMode": "acceptEdits"
  }
}
```

### Hook Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/validate.py",
            "timeout": 30
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
            "command": "python3 .claude/hooks/contract-validator.py --event PostToolUse"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Verify task completion before stopping."
          }
        ]
      }
    ]
  }
}
```

### Environment Variables

```json
{
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "PROJECT_ENV": "development"
  }
}
```

## Plugin hooks.json Format

Plugin hooks use a wrapper format in `hooks/hooks.json`:

```json
{
  "description": "Workflow validation hooks",
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

**Key difference:** Plugin hooks require the `{"hooks": {...}}` wrapper.

## MCP Server Configuration

### Project MCP (.mcp.json)

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    }
  }
}
```

### Enabling MCP Servers

In settings.json:
```json
{
  "enableAllProjectMcpServers": true
}
```

Or selectively:
```json
{
  "enabledMcpjsonServers": ["memory", "github"],
  "disabledMcpjsonServers": ["filesystem"]
}
```

## Workflow Settings Template

For cc-wf projects, combine all configurations:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 .claude/hooks/*)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./secrets/**)"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/wf-state.py --event UserPromptSubmit"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/contract-validator.py --event PreToolUse"
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
            "command": "python3 .claude/hooks/wf-state.py --event PostToolUse"
          },
          {
            "type": "command",
            "command": "python3 .claude/hooks/contract-validator.py --event PostToolUse"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/wf-state.py --event Stop"
          },
          {
            "type": "command",
            "command": "python3 .claude/hooks/contract-validator.py --event Stop"
          }
        ]
      }
    ]
  },
  "env": {
    "WF_STATE_FILE": ".context/state.yaml"
  }
}
```

## Hook Events Reference

| Event | When | Use For |
|-------|------|---------|
| PreToolUse | Before tool | Validation, blocking |
| PostToolUse | After tool | Logging, feedback |
| UserPromptSubmit | User input | Context injection |
| Stop | Agent stopping | Completion check |
| SubagentStop | Subagent done | Task validation |
| SessionStart | Session begins | Context loading |
| SessionEnd | Session ends | Cleanup |

## Quick Reference

### Available Settings Keys

| Key | Description |
|-----|-------------|
| `permissions` | Tool permissions (allow/deny) |
| `hooks` | Hook configurations |
| `env` | Environment variables |
| `model` | Override default model |
| `enableAllProjectMcpServers` | Auto-approve MCP servers |
| `enabledPlugins` | Plugin enable/disable |

### Permission Patterns

```
Bash(command)      - Exact command
Bash(prefix:*)     - Prefix match
Read(path)         - Exact file
Read(dir/**)       - Directory recursive
Write|Edit         - Multiple tools
```

## Additional Resources

### Reference Files

- **`references/settings-schema.md`** - Complete settings schema
- **`references/hook-patterns.md`** - Common hook patterns

### Example Files

- **`examples/workflow-settings.json`** - Complete workflow settings
- **`examples/plugin-hooks.json`** - Plugin hooks example

## Implementation Workflow

To create workflow settings:

1. **Identify requirements**: Hooks, permissions, MCP servers
2. **Create settings.json**: Start with basic template
3. **Configure hooks**: Add workflow state and contract validation
4. **Set permissions**: Allow workflow scripts, deny sensitive files
5. **Add MCP servers**: If needed for workflow
6. **Test configuration**: Verify hooks execute correctly
7. **Document**: Add comments in separate README

Focus on minimal configuration that enables workflow execution while maintaining security through proper permission rules.
