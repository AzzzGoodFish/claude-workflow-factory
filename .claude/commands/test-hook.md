---
description: Test command hooks in frontmatter
allowed-tools: Bash(echo:*)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[HOOK FIRED] PreToolUse Bash hook triggered at '$(date) >> /tmp/claude-hook-test.log"
  PostToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "echo '[HOOK FIRED] PostToolUse Bash hook triggered at '$(date) >> /tmp/claude-hook-test.log"
  Stop:
    - hooks:
        - type: command
          command: "echo '[HOOK FIRED] Stop hook triggered at '$(date) >> /tmp/claude-hook-test.log"
---

This is a test command to verify hooks declared in command frontmatter work correctly.

Please run: echo "hello from test-hook command"

After running the command, read /tmp/claude-hook-test.log to check if hooks fired.
