# Claude Code 工作流设计说明

> 本文档定义了如何将 AI 工作流设计原则映射到 Claude Code 的执行机制上。

## 1. 概述

### 1.1 设计目标

将 `ai-workflow-design-principles.md` 中的 4 个核心概念映射到 Claude Code：

| 工作流概念 | Claude Code 机制 | 状态 |
|-----------|-----------------|------|
| **Contract** | YAML Schema + Python Validator | ✅ 已确定 |
| **Nodes** | SubAgent (`.claude/agents/*.md`) | ✅ 已确定 |
| **Flow** | 简洁 DSL (`flow.yaml`) | ✅ 已确定 |
| **Context** | 环境变量 + 上下文文件 | ✅ 已确定 |

### 1.2 核心原则

1. **Command 是工作流入口和执行器**：定义整个工作流的 Flow、Input、Output
2. **SubAgent 是节点执行器**：可选绑定 Skill，使用契约规范输入输出
3. **SubAgent 输出格式统一为 Markdown**：存储在 `$WORKDIR/.context/`，便于 Agent 间共享
4. **Hook 实现自动校验**：利用 Claude Code 原生 Hook 机制校验输入输出

---

## 2. Hook 校验体系

### 2.1 Hook 类型与职责

```
┌─────────────────────────────────────────────────────────────────┐
│                     工作流执行生命周期                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  UserPromptSubmit ──────────────────────────────────────────┐   │
│    • 校验工作流整体输入                                       │   │
│    • 检查必要环境变量                                         │   │
│    • 初始化工作目录                                           │   │
│                                                              ▼   │
│  PreToolUse (matcher: "Task") ──────────────────────────────┐   │
│    • 识别即将执行的 SubAgent                                 │   │
│    • 从 Agent 定义中提取输入契约                             │   │
│    • 校验输入文件是否符合契约                                 │   │
│    • 校验失败 → continue: false，阻止执行                    │   │
│                                                              ▼   │
│  SubagentStop ──────────────────────────────────────────────┐   │
│    • 遍历所有 Agent 的输出契约，匹配当前输出                  │   │
│    • 匹配成功 → 写入 target 路径（.context/*.md）            │   │
│    • 匹配失败 → continue: false，拒绝退出                    │   │
│                                                              ▼   │
│  Stop ──────────────────────────────────────────────────────    │
│    • 校验工作流整体输出                                          │
│    • 检查所有必要节点是否完成                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Hook 配置

```json
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": ".claude/hooks/workflow-input.py"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Task",
        "command": ".claude/hooks/subagent-input.py"
      }
    ],
    "SubagentStop": [
      {
        "command": ".claude/hooks/subagent-output.py"
      }
    ],
    "Stop": [
      {
        "command": ".claude/hooks/workflow-output.py"
      }
    ]
  }
}
```

---

## 3. SubAgent 定义

### 3.1 定义格式

SubAgent 定义文件位于 `.claude/agents/*.md`，使用扩展的 frontmatter 格式：

```markdown
---
name: <agent-name>
description: <agent-description>
tools: <Tool1, Tool2, ...>
model: inherit
skills: <skill-name>              # 可选，任务相关增强

input:
  contract: <ContractName>        # 输入契约名称
  context:                        # 上下文文件列表（Agent 需要读取的）
    - "$WORKDIR/.context/file1.md"
    - "$WORKDIR/.context/file2.md"

output:
  contract: <ContractName>        # 输出契约名称
  target: "$WORKDIR/.context/<agent-name>.md"  # 输出目标路径
---

<Agent System Prompt>
```

### 3.2 字段说明

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Agent 唯一标识符 |
| `description` | string | ✅ | Agent 功能描述 |
| `tools` | string | ✅ | 可用工具列表 |
| `model` | string | ❌ | 模型选择（默认 inherit） |
| `skills` | string | ❌ | 绑定的 Skill 名称 |
| `input.contract` | string | ✅ | 输入契约名称 |
| `input.context` | string[] | ❌ | 上下文文件路径列表 |
| `output.contract` | string | ✅ | 输出契约名称 |
| `output.target` | string | ✅ | 输出文件目标路径 |

### 3.3 示例

````markdown
---
name: data-processor
description: 处理收集的数据，生成分析结果
tools: Read, Write, Bash, Glob
model: inherit
skills: data-analysis

input:
  contract: ProcessorInput
  context:
    - "$WORKDIR/.context/collector-a.md"
    - "$WORKDIR/.context/collector-b.md"

output:
  contract: ProcessorOutput
  target: "$WORKDIR/.context/processor.md"
---

你是数据处理器。

## 任务

1. 读取上下文文件中的收集结果
2. 分析并处理数据
3. 按输出格式生成结果

## 上下文

从以下文件读取：
- `$WORKDIR/.context/collector-a.md`
- `$WORKDIR/.context/collector-b.md`

## 输出格式

必须使用以下格式：

```markdown
---
type: processor-output
agent: data-processor
timestamp: <ISO8601>
---

## 处理结果

...
```
````

---

## 4. Contract（契约）定义

### 4.1 契约文件格式

契约使用 YAML 格式定义，包含 JSON Schema 和校验器引用：

```yaml
# .claude/workflows/<workflow-name>/contracts/<contract-name>.yaml

name: ProcessorOutput
description: 数据处理器输出契约
version: "1.0"

# JSON Schema 定义
schema:
  type: object
  required:
    - header
    - content
  properties:
    header:
      type: object
      required:
        - type
        - agent
      properties:
        type:
          const: "processor-output"    # 唯一标识，用于匹配
        agent:
          const: "data-processor"
        timestamp:
          type: string
          format: date-time
    content:
      type: string
      minLength: 1

# Python 校验器入口
validator: validators/processor_output.py::validate

# 示例数据
examples:
  - path: examples/processor-output-sample.md
```

### 4.2 契约唯一性

为确保 SubagentStop 能正确匹配输出到契约，每个输出契约必须有**唯一标识符**：

```yaml
# 在 schema 中定义唯一标识
schema:
  properties:
    header:
      properties:
        type:
          const: "processor-output"    # 每个契约的 type 必须唯一
        agent:
          const: "data-processor"      # 对应的 Agent 名称
```

对应的 Markdown 输出必须包含 frontmatter：

```markdown
---
type: processor-output
agent: data-processor
timestamp: 2026-01-06T10:00:00Z
---

## 处理结果
...
```

### 4.3 校验器实现

```python
# .claude/workflows/<workflow-name>/validators/processor_output.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Header(BaseModel):
    type: str = Field(const="processor-output")
    agent: str = Field(const="data-processor")
    timestamp: Optional[datetime] = None

class ProcessorOutput(BaseModel):
    header: Header
    content: str = Field(min_length=1)

def validate(data: dict) -> tuple[bool, list[str]]:
    """
    校验输出数据

    Returns:
        (is_valid, error_messages)
    """
    try:
        ProcessorOutput(**data)
        return True, []
    except Exception as e:
        return False, [str(e)]
```

---

## 5. 输出格式规范

### 5.1 Markdown 输出结构

所有 SubAgent 输出统一使用 Markdown 格式，必须包含 frontmatter：

```markdown
---
type: <contract-type>           # 契约类型标识（必须）
agent: <agent-name>             # Agent 名称（必须）
timestamp: <ISO8601>            # 时间戳（建议）
---

## 标题

正文内容...
```

### 5.2 存储位置

```
$WORKDIR/
└── .context/                   # 中间输出目录
    ├── collector-a.md          # 各 Agent 的输出
    ├── collector-b.md
    ├── processor.md
    └── finalizer.md
```

### 5.3 SubagentStop 匹配流程

```python
def match_output_to_agent(output: str) -> Optional[AgentDef]:
    """
    遍历所有 Agent 的输出契约，找到匹配的

    1. 解析输出的 frontmatter
    2. 遍历 .claude/agents/*.md
    3. 对每个 Agent 的 output.contract，检查是否匹配
    4. 返回匹配的 Agent 定义，或 None
    """
    frontmatter = parse_frontmatter(output)
    if not frontmatter:
        return None

    output_type = frontmatter.get("type")
    output_agent = frontmatter.get("agent")

    for agent in load_all_agents():
        contract = load_contract(agent.output.contract)
        expected_type = get_contract_type(contract)

        if output_type == expected_type:
            return agent

    return None
```

---

## 6. 目录结构

```
.claude/
├── settings.json                    # Hook 配置
│
├── commands/
│   └── <workflow-name>.md           # 工作流入口 Command
│
├── agents/
│   ├── collector-a.md               # SubAgent 定义
│   ├── collector-b.md
│   ├── processor.md
│   └── finalizer.md
│
├── skills/
│   └── <skill-name>/                # 解决特定任务的 Skill（可选）
│       ├── SKILL.md
│       └── references/
│
├── hooks/
│   ├── workflow-input.py            # UserPromptSubmit
│   ├── subagent-input.py            # PreToolUse (Task)
│   ├── subagent-output.py           # SubagentStop
│   └── workflow-output.py           # Stop
│
└── workflows/
    └── <workflow-name>/
        ├── flow.yaml                # Flow 定义（简洁 DSL）
        ├── contracts/               # 契约定义
        │   ├── workflow-input.yaml
        │   ├── collector-a-output.yaml
        │   ├── processor-output.yaml
        │   └── workflow-output.yaml
        ├── validators/              # Python 校验器
        │   ├── __init__.py
        │   └── validators.py
        └── templates/               # 输出模板（可选）
            ├── collector-output.md
            └── processor-output.md
```

---

## 7. Skill 与契约的关系

### 7.1 职责区分

| 概念 | 职责 | 与 Agent 关系 |
|------|------|--------------|
| **Skill** | 任务增强，提供领域知识、参考文档、工具脚本 | 可选绑定，协助完成任务 |
| **Contract** | 数据规范，定义输入输出结构和校验规则 | 必须绑定，定义接口 |

### 7.2 Skill 结构

```
.claude/skills/<skill-name>/
├── SKILL.md                    # Skill 入口
├── references/                 # 领域知识（可选）
│   └── domain-guide.md
└── scripts/                    # 工具脚本（可选）
    └── utils.py
```

### 7.3 使用方式

- Agent 通过 `skills: <skill-name>` 引用 Skill
- Skill 提供的知识被注入到 Agent 的上下文中
- Skill 与契约无直接关系，契约在 Agent 定义中声明

---

## 8. Flow 表达规范

> 详细的 Flow DSL 语法请参考 `flow-dsl-syntax.md`。

### 8.1 简洁 DSL 语法

Flow 使用简洁的 DSL 语法定义，存储在 `flow.yaml` 文件中：

```yaml
# .claude/workflows/<workflow-name>/flow.yaml
name: my-workflow
version: "1.0"

# 状态定义（可选）
state:
  items: []
  result: null

# 流程定义
flow: |
  START >> fetch-data >> [validate, transform] >> process >> END
  process ?success >> finalize >> END
  process ?retry >> process
  process ?fail >> error-handler >> END
  batch-processor * $items[3] >> merge >> END

# 条件定义（复杂条件时使用）
conditions:
  process:
    success: "output.status == 'ok'"
    retry: "output.retry_count < 3"
    fail: "output.status == 'error'"

# 执行配置
execution:
  max_parallel: 3
  timeout: 3600
```

### 8.2 语法符号

| 符号 | 含义 | 示例 | 说明 |
|------|------|------|------|
| `>>` | 顺序依赖 | `a >> b >> c` | a 完成后执行 b，b 完成后执行 c |
| `[a, b]` | 并行组 | `x >> [a, b] >> y` | a 和 b 并行执行，全部完成后执行 y |
| `?label` | 条件分支 | `a ?ok >> b` | a 输出满足 ok 条件时执行 b |
| `* $var` | 循环迭代 | `a * $items` | 对 $items 中每个元素执行 a |
| `* $var[n]` | 并行循环 | `a * $items[3]` | 并行度为 3 的循环迭代 |
| `START` | 起始节点 | `START >> a` | 工作流入口 |
| `END` | 结束节点 | `a >> END` | 工作流出口 |

### 8.3 三种输出格式

Flow 定义可自动转换为三种格式，便于不同场景使用：

1. **Mermaid 图**：可视化
2. **结构化文本**：智能体理解
3. **DAG JSON**：程序处理

详见 `flow-dsl-syntax.md`。

---

## 9. 待定内容

> 以下内容尚未完成讨论，需要后续确定。

### 9.1 🔖 重试机制

**问题**：SubagentStop 校验失败后，如何控制重试？

**待讨论**：
- 最大重试次数如何配置？
- 重试时是否传递错误反馈？
- 达到最大重试后如何处理（跳过/终止）？

### 9.2 🔖 状态持久化

**问题**：工作流中断后如何恢复？

**待讨论**：
- 状态文件格式和位置
- 检查点保存时机
- 恢复命令设计

### 9.3 🔖 超时处理

**问题**：SubAgent 执行时间过长如何处理？

**待讨论**：
- 超时配置位置（Agent 定义 / 全局配置）
- 超时后的处理策略

---

## 10. 执行流程示例

```
用户: /my-workflow --workdir=/output

1. UserPromptSubmit Hook
   ├── 校验输入（command 参数、环境变量）
   ├── 创建 $WORKDIR/.context/ 目录
   └── 初始化工作流状态

2. Command 执行
   ├── 解析 Flow 定义
   └── 按顺序/并行调用 SubAgent

3. 对每个 SubAgent 调用:
   │
   ├── PreToolUse (Task) Hook
   │   ├── 识别目标 SubAgent
   │   ├── 加载输入契约
   │   ├── 校验输入文件
   │   └── 失败则阻止执行
   │
   ├── SubAgent 执行
   │   ├── 读取 context 文件
   │   ├── 执行任务
   │   └── 生成 Markdown 输出
   │
   └── SubagentStop Hook
       ├── 遍历契约匹配输出
       ├── 匹配成功 → 写入 .context/<agent>.md
       └── 匹配失败 → 阻止退出，要求重新输出

4. Stop Hook
   ├── 校验工作流整体输出
   ├── 检查所有必要节点完成
   └── 生成执行报告
```

---

## 11. 下一步

1. ✅ 完成核心设计（Contract、Nodes、Flow、Context）
2. ✅ 确定 Flow 表达方式（简洁 DSL + 三种输出格式）
3. 🔖 讨论并确定重试机制
4. 🔖 讨论并确定状态持久化方案
5. 🔖 讨论并确定超时处理
6. 实现 Flow DSL 解析器
7. 实现 Flow → Mermaid/结构化文本/DAG JSON 转换器
8. 创建示例工作流验证设计
