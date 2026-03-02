---
name: contract-development
description: 当用户询问"创建契约"、"定义数据规范"、"添加输入输出校验"、"实现契约校验"、"设计工作流契约"，或提及 contract-desc、contract-validator、JSON Schema、三层校验、边界校验时，应使用此技能。
version: 1.0.0
---

# 契约开发指南

## 概述

契约定义工作流节点间的数据规范和校验规则。cc-wf-factory 采用**边界校验策略**和**三层校验架构**。

### 边界校验策略

只在数据进入和离开的边界进行校验，不做冗余的中间校验：

```
用户输入 ──[工作流输入校验]──→ 节点A ──[节点A输出校验]──→ 节点B ──[节点B输出校验]──→ 最终输出
              ↑                           ↑                           ↑
           外部边界                    节点边界                    节点边界
```

**为什么不校验节点输入？**
- 节点B的输入 = 节点A的输出（已通过输出校验）
- 在封闭的工作流系统中，节点输入校验是冗余的

### 三层校验架构

| 校验层 | 字段 | 执行者 | 适用场景 |
|--------|------|--------|----------|
| 结构校验 | `schema` | contract-validator.py | 类型、必需字段、枚举值 |
| 自定义校验 | `validator_script` | contract-validator.py | 跨字段校验、外部查询 |
| 语义校验 | `semantic_check` | Claude (prompt hook) | 内容质量、语义一致性 |

## 契约文件结构

每个契约是一个独立的 YAML 文件，位于 `.claude/contracts/` 目录：

```yaml
# .claude/contracts/{contract-name}.yaml

# 元信息（必需）
name: analysis-result
description: 分析节点的输出规范

# 第一层：结构校验 - JSON Schema（可选）
schema:
  type: object
  required:
    - summary
    - issues
  properties:
    summary:
      type: string
      minLength: 20
    issues:
      type: array
      items:
        type: object
        required: [file, severity, message]
        properties:
          file: { type: string }
          severity: { type: string, enum: [info, warning, error] }
          message: { type: string }

# 第二层：自定义校验脚本（可选）
validator_script: validators/analysis-result-validator.py

# 第三层：语义校验 prompt（可选）
semantic_check: |
  检查 summary 是否准确概括了 issues 中的问题数量和严重程度。
  检查每个 issue 的 message 是否具体、可操作。

# 示例数据（用于文档和测试）
examples:
  valid:
    summary: "分析了 15 个文件，发现 3 个问题"
    issues:
      - { file: "src/main.py", severity: "warning", message: "函数过长，建议拆分" }
  invalid:
    summary: "OK"
    issues: "none"
```

## 契约类型

### 纯结构校验（结构化数据）

```yaml
name: api-response
description: API 响应格式规范
schema:
  type: object
  required: [status, data]
  properties:
    status:
      type: string
      enum: [success, error]
    data:
      type: object
```

### 纯语义校验（非结构化输出）

```yaml
name: design-report
description: 设计报告输出规范
semantic_check: |
  检查报告是否包含概述、设计方案、实现计划等章节。
  检查方案是否具有可行性，逻辑是否清晰。
```

### 混合校验

同时使用 `schema` 和 `semantic_check`，先结构后语义。

## 校验触发机制

### 节点输出校验

由 node-builder 在节点 frontmatter 中配置 Stop hook：

```yaml
# .claude/agents/{node-name}.md frontmatter
hooks:
  Stop:
    - hooks:
        # 结构校验（command hook）
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py --contract {contract-name} --node {node-name}"
        # 语义校验（prompt hook，从契约的 semantic_check 生成）
        - type: prompt
          prompt: |
            检查输出是否符合以下要求：
            {semantic_check 内容}
            返回 JSON: {"ok": true} 或 {"ok": false, "reason": "原因"}

output_contract: {contract-name}
```

### 工作流输入校验

由 cc-settings-builder 在 settings.json 中配置 UserPromptSubmit hook：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/wf-state.py --workflow {workflow-name}"
          },
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py --workflow {workflow-name} --contract {input-contract}"
          }
        ]
      }
    ]
  }
}
```

## 自定义校验脚本

当业务规则超出 JSON Schema 能力时，创建自定义校验器：

```python
#!/usr/bin/env python3
"""validators/analysis-result-validator.py"""
import json
import sys
from typing import Any

def validate(data: dict[str, Any]) -> tuple[bool, list[dict]]:
    """
    自定义校验逻辑

    Returns:
        (is_valid, errors)
    """
    errors = []

    # 示例：跨字段校验
    if data.get("summary") and data.get("issues"):
        issue_count = len(data["issues"])
        if str(issue_count) not in data["summary"]:
            errors.append({
                "field": "summary",
                "message": f"摘要应提及问题数量 ({issue_count})"
            })

    return len(errors) == 0, errors

if __name__ == "__main__":
    data = json.load(sys.stdin)
    valid, errors = validate(data)
    result = {"valid": valid}
    if not valid:
        result["errors"] = errors
    print(json.dumps(result))
```

## Schema 设计指南

### 类型定义

| 类型 | YAML | 说明 |
|------|------|------|
| 字符串 | `type: string` | 文本数据 |
| 数值 | `type: number` | 浮点数 |
| 整数 | `type: integer` | 整数 |
| 布尔 | `type: boolean` | true/false |
| 数组 | `type: array` | 列表 |
| 对象 | `type: object` | 键值对 |

### 常用约束

```yaml
# 字符串约束
minLength: 1
maxLength: 100
pattern: "^[a-z]+$"

# 数值约束
minimum: 0
maximum: 100

# 数组约束
minItems: 1
maxItems: 10
uniqueItems: true

# 对象约束
required: [field1, field2]
additionalProperties: false
```

## 文件组织

```
.claude/
├── contracts/
│   ├── {contract-name}.yaml      # 契约定义
│   └── validators/
│       └── {contract-name}-validator.py  # 自定义校验器（可选）
└── hooks/
    ├── contract-validator.py     # 全局契约校验脚本
    ├── wf-state.py               # 状态治理脚本
    └── wf_output_extractor.py    # 输出提取工具
```

## 快速参考

### 何时使用各校验层

| 场景 | schema | validator_script | semantic_check |
|------|--------|------------------|----------------|
| 类型检查 | O | | |
| 必需字段 | O | | |
| 枚举值 | O | | |
| 字符串模式 | O | | |
| 跨字段校验 | | O | |
| 外部数据查询 | | O | |
| 内容质量评估 | | | O |
| 非结构化输出 | | | O |

### 校验失败处理

| 事件 | 失败处理 |
|------|----------|
| UserPromptSubmit | `exit(2)` 阻止执行，用户修正后重新提交 |
| SubagentStop | JSON `{"decision": "block"}` 阻止节点结束，要求修正输出 |
| Stop | JSON `{"decision": "block"}` 阻止工作流结束 |

## 参考资料

- **`references/patterns.md`** - 常见契约模式
- **`references/validation-strategies.md`** - 校验策略详解
- **`examples/simple-contract.yaml`** - 基础契约示例
- **`examples/validator-script.py`** - 完整校验脚本示例
