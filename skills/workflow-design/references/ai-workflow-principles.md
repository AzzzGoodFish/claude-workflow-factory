# AI 工作流设计原则（完整参考）

## 概述

本文档定义了 AI 驱动工作流的设计原则和核心概念，适用于基于 LLM Agent 的自动化任务编排。

## 核心概念

AI 工作流由 4 个核心概念组成：

```
┌─────────────────────────────────────────────────────────┐
│                      Workflow                           │
├─────────────────────────────────────────────────────────┤
│  1. Contract (契约)                                      │
│  2. Nodes (节点)                                         │
│  3. Flow (流程)                                          │
│  4. Context (上下文)                                     │
└─────────────────────────────────────────────────────────┘
```

| 概念 | 回答的问题 |
|------|-----------|
| Contract | 数据长什么样？如何验证？ |
| Nodes | 谁来执行？输入输出是什么？ |
| Flow | 按什么顺序执行？出错怎么办？ |
| Context | 执行时需要什么环境信息？ |

---

## 1. Contract（契约）

契约定义了工作流中所有数据结构的规范，是确保 AI 输出合规性的关键。

### 组成要素

| 要素 | 说明 | 必要性 |
|------|------|--------|
| Schema | 数据结构定义（字段、类型、约束） | ✅ 必须 |
| Validator | 校验器实现 | ✅ 必须 |
| Examples | 示例数据 | 建议 |

### 设计原则

1. **每个数据结构都必须有对应的校验器** - AI 输出不可信，必须验证
2. **Schema 和 Validator 共存** - Schema 用于文档和生成，Validator 用于运行时检查
3. **契约是节点间的接口** - 节点通过契约解耦

### 契约文件结构

契约集中存放，节点通过名称引用：

```
workflow/
├── contracts/
│   ├── contract-a.yaml
│   ├── contract-b.yaml
│   └── contract-c.yaml
└── validators/
    └── validators.py
```

### 契约定义格式

**契约文件字段说明**

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| name | string | ✅ | 契约名称（被节点引用的稳定标识） |
| description | string | 建议 | 契约用途说明 |
| schema | object | ✅ | 数据结构定义（建议采用 JSON Schema 表达） |
| validator | string | ✅ | 运行时校验器入口，格式 `path/to/file.py::function_name` |
| examples | string[] | 建议 | 示例文件路径列表（用于 prompt/测试/回归） |

**契约文件示例**

```yaml
name: ContractName
description: 契约用途说明
version: "1.0"

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
          const: "contract-type"    # 唯一标识，用于匹配
        agent:
          const: "agent-name"
        timestamp:
          type: string
          format: date-time
    content:
      type: string
      minLength: 1

validator: validators/contract_name.py::validate

examples:
  - path: examples/sample.md
```

### 契约引用（Markdown 示范）

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| contract.name | string | ✅ | 契约名称（如 `ContractA`） |
| contract.schema | string | ✅ | schema 文件路径（如 `schemas/contract-a.schema.json`） |
| contract.validator | string | ✅ | 校验器入口（如 `validators.py::validate_contract_a`） |
| contract.examples | string[] | 可选 | 示例文件路径列表 |

### 节点输入输出绑定（Markdown 示范）

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| node.name | string | ✅ | 节点名称（如 `NodeX`） |
| node.input.contract | string | ✅ | 输入契约名（如 `ContractA`） |
| node.input.source | string | ✅ | 输入来源路径模板（如 `$WORKDIR/intermediate/{entity}/input-a.md`） |
| node.output.contract | string | ✅ | 输出契约名（如 `ContractB`） |
| node.output.target | string | ✅ | 输出目标路径模板（如 `$WORKDIR/{entity}/result.json`） |

### 运行时绑定

1. 节点执行前：解析 `input.contract` 引用，加载校验器，执行输入校验
2. 节点执行后：解析 `output.contract` 引用，加载校验器，执行输出校验
3. 校验失败：触发 Flow 定义的错误处理

### 校验时机

| 时机 | 触发条件 | 校验内容 | 失败处理 |
|------|---------|---------|---------|
| 输入校验 | 节点执行前 | 输入契约 | 阻止执行 |
| 输出校验 | 节点执行后 | 输出契约 | 触发重试或错误处理 |

### 契约唯一性

为确保 SubagentStop 能正确匹配输出到契约，每个输出契约必须有**唯一标识符**：

```yaml
schema:
  properties:
    header:
      properties:
        type:
          const: "processor-output"    # 每个契约的 type 必须唯一
        agent:
          const: "data-processor"      # 对应的 Agent 名称
```

---

## 2. Nodes（节点）

节点是工作流的执行单元，在 AI 工作流中通常由 SubAgent 实现。

### 组成要素

| 要素 | 说明 | 必要性 |
|------|------|--------|
| 输入契约 | 引用 Contract 定义 | ✅ 必须 |
| 输出契约 | 引用 Contract 定义 | ✅ 必须 |
| 实现 | SubAgent 定义（prompt、skills、tools、model） | ✅ 必须 |

### 设计原则

1. **单一职责** - 每个节点只做一件事
2. **输入输出明确** - 通过契约定义，不依赖隐式约定
3. **可独立测试** - 给定输入，能独立验证输出
4. **幂等性** - 相同输入产生相同输出（尽可能）

### 节点定义格式

| 字段 | 类型 | 必须 | 说明 |
|------|------|------|------|
| name | string | ✅ | 节点名称（稳定标识） |
| description | string | 建议 | 节点用途说明 |
| input.contract | string | ✅ | 输入契约名称 |
| input.source | string | ✅ | 输入文件路径模板（可包含占位符，如 `{entity}`） |
| output.contract | string | ✅ | 输出契约名称 |
| output.target | string | ✅ | 输出文件路径模板（可包含占位符，如 `{entity}`） |
| implementation | object | ✅ | 节点实现配置 |
| implementation.type | string | ✅ | 实现类型（如 `subagent` / `script` / `service`） |
| implementation.agent | string | 可选 | agent/prompt 定义入口（当 `type=subagent`） |
| implementation.skills | string[] | 可选 | 复用能力集合 |
| implementation.tools | string[] | 可选 | 允许使用的工具集合 |
| implementation.model | string | 可选 | 模型选择策略（如 `inherit` / 显式指定） |

### 契约与节点的绑定

```
contracts/                      nodes/
├── ContractA.yaml              ├── node-x.yaml
├── ContractB.yaml              │     input:
├── ContractC.yaml         ◄────│       - contract: ContractA
└── ContractD.yaml         ◄────│       - contract: ContractB
                                │     output:
                                │       - contract: ContractC
                                │       - contract: ContractD
```

### 运行时校验流程

```
1. 加载节点定义
2. 解析 input.contract，找到对应契约
3. 执行输入校验（validator）
   - 通过 → 继续
   - 失败 → 阻止执行
4. 执行节点（SubAgent）
5. 解析 output.contract，找到对应契约
6. 执行输出校验（validator）
   - 通过 → 完成
   - 失败 → 触发 Flow 错误处理（重试/跳过/终止）
```

---

## 3. Skill（技能）

Skill 是可复用的知识和工具组合，供多个节点共享。

### SKILL.md 规范

```markdown
---
name: your-skill-name
description: Brief description of what this Skill does and when to use it
---

# Your Skill Name

## Instructions
Provide clear, step-by-step guidance for Claude.

## Examples
Show concrete examples of using this Skill.
```

- **frontmatter**（必须）：`name` 和 `description`
- **内容**（灵活）：Instructions、Examples 等，按需组织

### Skill 目录结构

```
.claude/skills/{skill-name}/
├── SKILL.md                    # 主入口（必须）
├── scripts/                    # 工具脚本（推荐）
├── references/                 # 领域知识（推荐）
└── ...                         # 其他目录（按需扩展）
```

### Skill 与 Node 的关系

- Skill 提供"知识"（指导、参考文档、工具脚本）
- Node 定义"任务"（输入、输出、执行逻辑）
- 一个 Skill 可被多个 Node 引用
- Node 通过 `skills: [skill-name]` 绑定 Skill

---

## 4. Flow（流程）

Flow 定义"如何执行"——节点的执行规则。

### 本质

Flow 是一个抽象概念，描述执行控制的规则集合。具体工作流可根据需求选择适合的控制模式。

### Flow 需要回答的问题

| 维度 | 问题 | 可能的模式 |
|------|------|-----------|
| 顺序 | 节点按什么顺序执行？ | 顺序、并发、依赖图 |
| 重复 | 何时需要重复执行？ | 循环、迭代、递归 |
| 分支 | 何时走不同路径？ | 条件分支、模式匹配 |
| 错误 | 失败时怎么办？ | 重试、跳过、回滚、降级 |

### 设计原则

1. **Flow 是抽象的** - 不限定具体编排模式，由各工作流自行定义
2. **错误处理是 Flow 的一部分** - 不是独立概念
3. **显式优于隐式** - 执行规则应明确声明
4. **可观测** - 能追踪执行状态

### Flow DSL 语法

| 符号 | 含义 | 示例 | 说明 |
|------|------|------|------|
| `>>` | 顺序依赖 | `a >> b >> c` | a 完成后执行 b，b 完成后执行 c |
| `[a, b]` | 并行组 | `x >> [a, b] >> y` | a 和 b 并行执行，全部完成后执行 y |
| `?label` | 条件分支 | `a ?ok >> b` | a 输出满足 ok 条件时执行 b |
| `* $var` | 循环迭代 | `a * $items` | 对 $items 中每个元素执行 a |
| `* $var[n]` | 并行循环 | `a * $items[3]` | 并行度为 3 的循环迭代 |
| `START` | 起始节点 | `START >> a` | 工作流入口 |
| `END` | 结束节点 | `a >> END` | 工作流出口 |

---

## 5. Context（上下文）

上下文定义工作流执行时的环境信息和共享状态。

### 组成要素

| 要素 | 说明 | 必要性 |
|------|------|--------|
| 环境变量 | 执行环境参数 | ✅ 必须 |
| 共享状态 | 节点间传递的状态 | 可选 |
| 存储布局 | 中间产物存储位置 | ✅ 必须 |

### 设计原则

1. **显式声明** - 所有上下文变量必须在工作流入口声明
2. **不可变优先** - 环境变量在执行期间不应改变
3. **存储布局统一** - 所有节点遵循相同的目录结构

### 上下文定义详细字段

**env（环境变量，工作流输入）**

| 变量名 | 类型 | 必须 | 说明 |
|-------|------|------|------|
| WORKDIR | string | ✅ | 工作目录 |
| WORKFLOW_NAME | string | ✅ | 工作流名称 |
| SOURCE_DIR | string | 可选 | 源码/数据所在目录 |
| OUTPUT_DIR | string | 可选 | 输出目录 |

**layout（存储布局）**

| 字段 | 类型 | 必须 | 说明 | 示例（模板） |
|------|------|------|------|--------------|
| intermediate | string | ✅ | 中间产物目录 | `$WORKDIR/.context/` |
| final | string | ✅ | 最终产物目录 | `$WORKDIR/output/` |
| temp | string | ✅ | 临时目录 | `$WORKDIR/.temp/` |

**state（共享状态，运行时生成）**

| 键 | 类型 | 必须 | 说明 | populated_by |
|----|------|------|------|--------------|
| collected_data | any | 可选 | 收集阶段产出的数据 | `collector` |
| analysis_result | any | 可选 | 分析阶段产出的结果 | `analyzer` |

---

## 概念关系图

```
                    ┌─────────────┐
                    │   Context   │
                    │  (环境变量)  │
                    └──────┬──────┘
                           │ 提供执行环境
                           ▼
┌─────────────────────────────────────────────────────┐
│                       Flow                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│  │ Stage 1 │───▶│ Stage 2 │───▶│ Stage 3 │        │
│  └────┬────┘    └────┬────┘    └────┬────┘        │
│       │              │              │              │
│  ┌────┴────┐    ┌────┴────┐    ┌────┴────┐        │
│  │  Nodes  │    │  Nodes  │    │  Nodes  │        │
│  └────┬────┘    └────┬────┘    └────┬────┘        │
└───────┼──────────────┼──────────────┼──────────────┘
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │Contract │    │Contract │    │Contract │
   │ (输入)  │    │ (中间)  │    │ (输出)  │
   └─────────┘    └─────────┘    └─────────┘
```

### 核心关系

- **Skill** 提供可复用的知识（prompt + 工具）
- **Node** 引用 Skill，定义具体任务
- **Contract** 是 Node 间的接口
- **Flow** 编排 Node 的执行
- **Context** 为执行提供环境

---

## AI 工作流的特殊考量

### 与传统工作流的区别

| 方面 | 传统工作流 | AI 工作流 |
|------|-----------|----------|
| 输出确定性 | 确定性 | 非确定性 |
| 校验必要性 | 可选 | 必须 |
| 错误类型 | 主要是异常 | 格式错误、语义错误、幻觉 |
| 重试策略 | 简单重试 | 带反馈重试 |

### AI 特有的设计要点

1. **校验器是强制的** - 不能信任 AI 输出
2. **带反馈重试** - 将校验错误作为上下文反馈给 Agent
3. **示例驱动** - 在 prompt 中提供清晰的输出示例
4. **渐进式细化** - 复杂任务拆分为多个简单节点

### Prompt 与 Contract 的关系

```
Contract (Schema)
    │
    ├──▶ 生成 Prompt 中的输出格式说明
    │
    ├──▶ 生成 Examples
    │
    └──▶ 生成 Validator
```

---

## 文档组织建议

```
workflow/
├── contracts/           # 契约定义
│   ├── contract-a.yaml
│   ├── contract-b.yaml
│   ├── contract-c.yaml
│   └── ...
├── nodes/               # 节点定义
│   ├── node-a.md
│   ├── node-b.md
│   └── ...
├── flow.yaml            # 流程编排
├── context.yaml         # 上下文定义
└── validators/          # 校验器实现
    ├── __init__.py
    ├── contract_a.py
    ├── contract_c.py
    └── ...
```

---

## 总结

| 概念 | 职责 | AI 特有考量 |
|------|------|------------|
| **Contract** | 数据规范 + 校验 | 校验器必须存在，多时机校验 |
| **Nodes** | 执行单元 | SubAgent + Skill 实现 |
| **Flow** | 执行控制（顺序、分支、错误处理） | 抽象定义，带反馈重试 |
| **Context** | 环境 + 状态 | 存储布局统一 |

### 设计原则

- **契约先行**：先定义数据规范，再实现节点
- **校验必备**：每个契约都有校验器，明确校验时机
- **Flow 是抽象的**：不限定具体模式，按需选用
- **错误处理是 Flow 的一部分**
- **显式优于隐式**
