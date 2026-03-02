# Command Frontmatter Hooks 使用指南

在 Claude Code 的自定义 slash command 中，可以通过 frontmatter 的 `hooks` 字段声明钩子，钩子仅在该 command 执行期间生效，执行结束后自动清理。

## 支持的事件

| 事件 | 触发时机 | 需要 matcher |
|:--|:--|:--|
| `PreToolUse` | 工具调用前 | 是 |
| `PostToolUse` | 工具调用后 | 是 |
| `Stop` | command 执行结束时 | 否 |

## 基本语法

```yaml
---
description: 我的命令
hooks:
  PreToolUse:
    - matcher: "ToolName"
      hooks:
        - type: command
          command: "your-script.sh"
  PostToolUse:
    - matcher: "ToolName"
      hooks:
        - type: command
          command: "your-script.sh"
  Stop:
    - hooks:
        - type: command
          command: "your-script.sh"
---
```

## Hook 类型

### command 类型

执行 bash 命令，通过 stdin 接收 JSON 输入，通过 exit code 和 stdout/stderr 控制行为。

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate.sh"
          timeout: 30  # 可选，单位秒
```

### prompt 类型

使用 LLM 进行智能判断（仅 Stop 事件最实用）。

```yaml
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: "检查任务是否全部完成。$ARGUMENTS"
```

## Matcher 语法

- 精确匹配：`"Bash"`、`"Write"`、`"Edit"`
- 正则匹配：`"Edit|Write"`、`"Notebook.*"`、`"mcp__.*"`
- 匹配所有：`"*"` 或留空

常用工具名：`Bash`、`Read`、`Write`、`Edit`、`Glob`、`Grep`、`Task`、`WebFetch`、`WebSearch`

## Exit Code 约定

| Exit Code | 含义 |
|:--|:--|
| 0 | 成功，stdout 可返回 JSON 进行高级控制 |
| 2 | 阻断，stderr 作为错误信息反馈给 Claude |
| 其他 | 非阻断错误，stderr 仅日志记录 |

## once 选项

设置 `once: true` 使 hook 仅触发一次，之后自动移除：

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/init-check.sh"
          once: true
```

## 实用示例

### 示例 1：部署前校验

```markdown
---
description: 部署到 staging 环境
allowed-tools: Bash(npm:*), Bash(git:*)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/scripts/validate-deploy.sh"
---

将当前分支部署到 staging 环境。
```

`validate-deploy.sh` 通过 exit code 2 + stderr 阻止危险命令：

```python
#!/usr/bin/env python3
import json, sys, re

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

blocked = [r"rm\s+-rf\s+/", r"DROP\s+TABLE", r"--force"]
for p in blocked:
    if re.search(p, cmd, re.IGNORECASE):
        print(f"命令被阻止: 匹配危险模式 '{p}'", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
```

### 示例 2：写文件后自动格式化

```markdown
---
description: 创建 React 组件
allowed-tools: Write, Edit
hooks:
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "$CLAUDE_PROJECT_DIR/scripts/auto-format.sh"
---

根据需求创建 React 组件。
```

`auto-format.sh` 从 stdin 读取文件路径并格式化：

```bash
#!/bin/bash
FILE_PATH=$(cat | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))")
if [[ "$FILE_PATH" == *.ts || "$FILE_PATH" == *.tsx ]]; then
  npx prettier --write "$FILE_PATH" 2>/dev/null
fi
exit 0
```

### 示例 3：智能完成检查

```markdown
---
description: 实现功能并确保测试通过
allowed-tools: Bash(*), Write, Edit, Read, Glob, Grep
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            检查 Claude 是否完成了所有任务：
            1. 功能代码已编写
            2. 测试已编写并通过
            3. 没有遗留的 TODO
            如果未完成，返回 {"ok": false, "reason": "说明原因"}
---

实现 $ARGUMENTS 功能，并编写对应的单元测试。
```

## 环境变量

hook command 中可使用：

- `$CLAUDE_PROJECT_DIR` — 项目根目录绝对路径
- stdin — JSON 格式的 hook 输入数据（包含 `tool_name`、`tool_input` 等）

## 注意事项

1. Command hooks 仅在该 command 执行期间生效，结束后自动清理
2. 多个匹配的 hooks 并行执行
3. 默认超时 60 秒，可通过 `timeout` 字段自定义
4. `once: true` 仅支持 command 和 skill，不支持 agent
5. hook 脚本需要有执行权限（`chmod +x`）
