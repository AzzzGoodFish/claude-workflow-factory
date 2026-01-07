---
name: workflow-design
description: 当用户询问"工作流设计"、"Contract 定义"、"Node 设计"、"Flow DSL"、"SubAgent 工作流"、"工作流校验"，或需要关于 AI 工作流架构、数据契约、节点编排、Claude Code 工作流实现模式的指导时使用此 Skill。
---

# 工作流设计知识

提供基于 4 个核心概念设计 AI 驱动工作流的指导：Contract、Node、Flow 和 Context。

## 核心概念概览

AI 工作流由 4 个基本概念组成：

| 概念 | 回答的问题 | Claude Code 映射 |
|------|-----------|-----------------|
| **Contract** | 数据长什么样？如何校验？ | YAML Schema + Python Validator |
| **Node** | 谁执行？输入输出是什么？ | SubAgent (`.claude/agents/*.md`) |
| **Flow** | 什么顺序？出错怎么办？ | DSL (`flow.yaml`) |
| **Context** | 需要什么环境信息？ | 环境变量 + context 文件 |

## Contract 设计

Contract 定义数据结构规范和校验规则。

### Contract 组件

| 组件 | 用途 | 是否必需 |
|------|------|---------|
| Schema | 数据结构定义（JSON Schema） | 是 |
| Validator | 运行时校验函数 | 是 |
| Examples | 用于测试/prompt 的示例数据 | 推荐 |

### Contract 文件格式

```yaml
name: ContractName
description: 契约用途
version: "1.0"

schema:
  type: object
  required: [field1, field2]
  properties:
    field1:
      type: string
    field2:
      type: integer

validator: validators/contract_name.py::validate

examples:
  - path: examples/sample.json
```

### 校验时机

| 时机 | 触发点 | 校验内容 | 失败处理 |
|------|--------|---------|---------|
| 输入校验 | 节点执行前 | 输入 Contract | 阻止执行 |
| 输出校验 | 节点执行后 | 输出 Contract | 触发重试或错误处理 |

## Node 设计

Node 是工作流执行单元，在 Claude Code 中实现为 SubAgent。

### Node 定义格式

```markdown
---
name: node-name
description: 节点用途
tools: Read, Write, Bash, Glob

input:
  contract: InputContractName
  context:
    - "$WORKDIR/.context/dependency.md"

output:
  contract: OutputContractName
  target: "$WORKDIR/.context/node-name.md"
---

<System Prompt>
```

### 设计原则

1. **单一职责** - 每个节点只做一件事
2. **显式 I/O** - 通过 Contract 定义，无隐式依赖
3. **可独立测试** - 给定输入可验证输出
4. **幂等性** - 相同输入产生相同输出（尽可能）

### 输出格式

所有 SubAgent 输出使用带 frontmatter 的 Markdown：

```markdown
---
type: contract-type
agent: agent-name
timestamp: 2026-01-07T10:00:00Z
---

## 内容

...
```

## Flow 设计

Flow 使用简洁的 DSL 定义执行控制规则。

### DSL 语法

| 符号 | 含义 | 示例 |
|------|------|------|
| `>>` | 顺序执行 | `a >> b >> c` |
| `[a, b]` | 并行组 | `x >> [a, b] >> y` |
| `?label` | 条件分支 | `a ?ok >> b` |
| `* $var` | 循环迭代 | `a * $items` |
| `* $var[n]` | 并行循环 | `a * $items[3]` |
| `START` | 入口点 | `START >> a` |
| `END` | 出口点 | `a >> END` |

### Flow 文件格式

```yaml
name: workflow-name
version: "1.0"

flow: |
  START >> fetch-data >> [validate, transform] >> process >> END
  process ?success >> finalize >> END
  process ?fail >> error-handler >> END

conditions:
  process:
    success: "output.status == 'ok'"
    fail: "output.status == 'error'"

execution:
  max_parallel: 3
  timeout: 3600
```

### 常见模式

**顺序执行:**
```yaml
flow: |
  START >> step-a >> step-b >> step-c >> END
```

**并行执行:**
```yaml
flow: |
  START >> [collect-a, collect-b] >> merge >> END
```

**条件分支:**
```yaml
flow: |
  START >> analyze >> END
  analyze ?issues >> fix >> END
  analyze ?clean >> approve >> END
```

**循环迭代:**
```yaml
flow: |
  START >> processor * $files[3] >> merge >> END
```

## Context 设计

Context 定义环境信息和共享状态。

### Context 组件

| 组件 | 用途 | 是否必需 |
|------|------|---------|
| 环境变量 | 执行参数 | 是 |
| 共享状态 | 节点间传递的状态 | 可选 |
| 存储布局 | 中间产物位置 | 是 |

### 存储布局约定

```
$WORKDIR/
└── .context/                # 中间输出
    ├── node-a.md
    ├── node-b.md
    └── ...
```

## AI 工作流特殊考量

### 与传统工作流的区别

| 方面 | 传统工作流 | AI 工作流 |
|------|-----------|----------|
| 输出确定性 | 确定性 | 非确定性 |
| 校验必要性 | 可选 | 必需 |
| 错误类型 | 异常 | 格式错误、语义错误、幻觉 |
| 重试策略 | 简单重试 | 带反馈重试 |

### AI 特有设计要点

1. **校验器必不可少** - 永远不要信任 AI 输出
2. **带反馈重试** - 将校验错误传回 Agent
3. **示例驱动** - 在 prompt 中提供清晰的输出示例
4. **渐进式细化** - 将复杂任务拆分为简单节点

## 扩展资源

### 参考文件

详细模式和语法请参阅：
- **`references/ai-workflow-principles.md`** - 完整设计原则
- **`references/cc-workflow-mapping.md`** - Claude Code 实现细节
- **`references/flow-dsl-syntax.md`** - 完整 Flow DSL 参考

### 快速决策指南

**何时拆分节点：**
- 任务需要多种不同技能
- 输出需要不同的校验规则
- 需要并行执行能力

**何时使用 Contract：**
- 数据在节点间流动
- 需要校验 AI 输出
- 需要一致的数据结构

**何时使用条件流程：**
- 根据输出走不同路径
- 需要错误处理
- 需要质量门控
