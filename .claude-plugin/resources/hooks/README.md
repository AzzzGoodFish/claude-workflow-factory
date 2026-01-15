# Hook 资源文件

此目录包含 cc-wf-factory 生成工作流时使用的 Hook 脚本模板。

## 文件说明

### contract-validator.py

全局契约校验脚本，由 `cc-settings-builder` Agent 复制到用户工作流的 `.claude/hooks/` 目录。

**功能**：
- PreToolUse (Task): 校验节点输入数据
- PostToolUse (Task): 校验节点输出数据

**依赖**：
- Python 3.8+
- pyyaml
- jsonschema

**使用方式**：
1. `cc-settings-builder` 将此文件复制到 `.claude/hooks/contract-validator.py`
2. 配置 `settings.json` 中的 Hook 配置
3. 用户工作流运行时自动触发契约校验

## 配置示例

生成的 `settings.json` 中的 Hook 配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PROJECT_ROOT}/.claude/hooks/contract-validator.py",
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
            "command": "python ${CLAUDE_PROJECT_ROOT}/.claude/hooks/contract-validator.py",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```
