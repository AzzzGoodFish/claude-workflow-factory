---
description: Test plugin command hooks
allowed-tools: Bash(echo:*)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[PLUGIN HOOK] PreToolUse fired, PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}' >> /tmp/claude-plugin-hook-test.log"
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[PLUGIN HOOK] PostToolUse fired, PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}' >> /tmp/claude-plugin-hook-test.log"
  Stop:
    - hooks:
        - type: command
          command: "echo '[PLUGIN HOOK] Stop fired, PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}' >> /tmp/claude-plugin-hook-test.log"
---

Test command for plugin hooks. Run: echo "hello from plugin"
