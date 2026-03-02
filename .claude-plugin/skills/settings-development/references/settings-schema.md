# Settings Schema Reference

## Complete settings.json Schema

```json
{
  "apiKeyHelper": "string - Script to generate auth value",
  "cleanupPeriodDays": "number - Session cleanup period (default: 30)",
  "companyAnnouncements": ["string array - Startup announcements"],
  "env": {"key": "value - Environment variables"},
  "attribution": {
    "commit": "string - Git commit attribution",
    "pr": "string - PR description attribution"
  },
  "permissions": {
    "allow": ["string array - Allowed tool patterns"],
    "ask": ["string array - Ask confirmation patterns"],
    "deny": ["string array - Denied tool patterns"],
    "additionalDirectories": ["string array - Extra working dirs"],
    "defaultMode": "string - Default permission mode",
    "disableBypassPermissionsMode": "string - Disable bypass mode"
  },
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [],
    "UserPromptSubmit": [],
    "Stop": [],
    "SubagentStop": [],
    "SessionStart": [],
    "SessionEnd": [],
    "PreCompact": [],
    "Notification": []
  },
  "sandbox": {
    "enabled": "boolean - Enable bash sandboxing",
    "autoAllowBashIfSandboxed": "boolean - Auto-approve sandboxed bash",
    "excludedCommands": ["string array - Commands outside sandbox"],
    "allowUnsandboxedCommands": "boolean - Allow escape hatch",
    "network": {
      "allowUnixSockets": ["string array - Allowed socket paths"],
      "allowLocalBinding": "boolean - Allow localhost binding",
      "httpProxyPort": "number - HTTP proxy port",
      "socksProxyPort": "number - SOCKS5 proxy port"
    }
  },
  "model": "string - Override default model",
  "enableAllProjectMcpServers": "boolean - Auto-approve MCP servers",
  "enabledMcpjsonServers": ["string array - Approved MCP servers"],
  "disabledMcpjsonServers": ["string array - Rejected MCP servers"],
  "enabledPlugins": {"plugin@marketplace": "boolean"},
  "extraKnownMarketplaces": {"name": {"source": {...}}}
}
```

## Hook Entry Schema

```json
{
  "matcher": "string - Tool name pattern (regex supported)",
  "hooks": [
    {
      "type": "command|prompt",
      "command": "string - Bash command (for type: command)",
      "prompt": "string - LLM prompt (for type: prompt)",
      "timeout": "number - Timeout in ms (optional)"
    }
  ]
}
```

## Permission Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `Bash(npm run lint)` | Exact command |
| `Bash(npm run:*)` | Prefix match |
| `Read(./.env)` | Exact file |
| `Read(./.env.*)` | Glob pattern |
| `Read(./secrets/**)` | Recursive glob |
| `Write\|Edit` | Multiple tools |
| `mcp__.*` | Regex pattern |

## Environment Variables in Hooks

Available in command hooks:
- `$CLAUDE_PROJECT_DIR` - Project root
- `$CLAUDE_PLUGIN_ROOT` - Plugin directory
- `$CLAUDE_ENV_FILE` - SessionStart only: persist env vars
