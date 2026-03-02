# cc-wf-factory 需求描述文档

## 概述

本文档详细描述 cc-wf-factory 的各组件需求，包括功能定义、输入输出、交互流程、技术规范等。

### 目标用户

cc-wf-factory 面向两类用户：
- **Claude Code 插件开发者**：熟悉 Claude Code 能力，希望快速构建工作流
- **业务用户**：不熟悉 Claude Code 内部机制，仅描述业务流程需求

系统通过完全引导式交互，支持两种用户类型。

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层                               │
├─────────────────────────────────────────────────────────────────┤
│  /create-cc-wf (入口 Command)    /review-cc-wf (校验 Command)    │
└───────────────────────────────────────────────────────────────┬─┘
                                                                │
                               ↓ 调度                            │
┌─────────────────────────────────────────────────────────────────┐
│                         构建器层 (Agents)                        │
├─────────────────────────────────────────────────────────────────┤
│  skill-builder │ contract-builder │ node-builder │ wf-entry-builder │ cc-settings-builder │
└───────────────────────────────────────────────────────────────┬─┘
                                                                │
                               ↓ 输出                            │
┌─────────────────────────────────────────────────────────────────┐
│                         运行时层 (Hooks)                         │
├─────────────────────────────────────────────────────────────────┤
│  contract-validator.py  │  wf-state.py  │  wf_output_extractor.py │
│  (契约校验)              │  (状态治理)    │  (输出提取 - 共享库)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. create-cc-wf (Command)

### 1.1 功能定义

**用途**：工作流创建的统一入口，通过完全引导式交互收集用户需求，调度各 Builder Agent 完成工作流组件的创建。

**类型**：Command（用户显式调用）

### 1.2 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| workflow-desc | string | 否 | 工作流描述信息，未提供则交互询问 |

### 1.3 交互流程

采用**完全引导式**流程，每阶段生成设计文档并与用户确认后再进入下一阶段：

```
┌─────────────────────────────────────────────────────────────────┐
│                        设计阶段 (Design)                         │
│         每阶段输出设计文档 → 用户确认 → 进入下一阶段              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段 1: 需求分析                                                │
│  ├── 收集：工作流名称、目标、场景、输入输出                       │
│  ├── 输出：.context/design/00-requirements.md                   │
│  └── 确认：用户确认需求理解正确                                  │
│                           ↓                                     │
│  阶段 2: 技能设计                                                │
│  ├── 分析：识别所需领域知识，检查可复用技能                       │
│  ├── 输出：.context/design/01-skills-design.md                  │
│  │         (包含所有技能的设计，每个技能一个章节)                 │
│  └── 确认：用户确认技能列表和设计                                │
│                           ↓                                     │
│  阶段 3: 契约设计                                                │
│  ├── 分析：定义节点间数据规范，确定校验策略                       │
│  ├── 输出：.context/design/02-contracts-design.md               │
│  │         (包含所有契约的设计，每个契约一个章节)                 │
│  └── 确认：用户确认数据规范和校验规则                            │
│                           ↓                                     │
│  阶段 4: 节点设计                                                │
│  ├── 分析：拆解工作流步骤，定义节点职责和数据流                   │
│  ├── 输出：.context/design/03-nodes-design.md                   │
│  │         (包含所有节点的设计，每个节点一个章节)                 │
│  └── 确认：用户确认节点划分和职责                                │
│                           ↓                                     │
│  阶段 5: 流程设计                                                │
│  ├── 编排：确定执行顺序、条件分支、异常处理                       │
│  ├── 输出：.context/design/04-flow-design.md                    │
│  └── 确认：用户确认流程逻辑                                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                        创建阶段 (Build)                          │
│          读取设计文档 → 拆分任务 → 并发调用 Builder Agents        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  阶段 6: 组件创建（分批并发）                                    │
│  │                                                              │
│  │  第一批（并发）                                               │
│  │  ┌─ 读取 01-skills-design.md ─┐                              │
│  │  │  拆分为 N 个技能任务        │                              │
│  │  │  并发调用 skill-builder     │ ──→ .claude/skills/{name}/SKILL.md │
│  │  └────────────────────────────┘                              │
│  │  ┌─ 读取 02-contracts-design.md ─┐                           │
│  │  │  拆分为 M 个契约任务           │                           │
│  │  │  并发调用 contract-builder     │ ──→ .claude/contracts/{name}.yaml │
│  │  └──────────────────────────────┘                            │
│  │                                                              │
│  │  第二批（依赖第一批）                                         │
│  │  ┌─ 读取 03-nodes-design.md ─┐                               │
│  │  │  拆分为 K 个节点任务       │                               │
│  │  │  并发调用 node-builder     │ ──→ .claude/agents/{name}.md  │
│  │  └────────────────────────────┘                              │
│  │                                                              │
│  │  第三批（依赖第二批）                                         │
│  │  ┌─ 读取 04-flow-design.md ─┐                                │
│  │  │  调用 wf-entry-builder    │ ──→ .claude/commands/{workflow}.md │
│  │  └───────────────────────────┘                               │
│  │                                                              │
│  │  第四批（依赖前三批）                                         │
│  │  ┌─ 汇总所有配置 ─┐                                           │
│  │  │  调用 cc-settings-builder │ ──→ .claude/settings.json     │
│  │  └─────────────────────────┘                                 │
│  │                                                              │
│  └── 确认：展示创建结果，用户确认                                │
│                                                                 │
│  阶段 7: 验证与测试（可选）                                       │
│  ├── 运行结构校验                                                │
│  ├── 执行基础功能测试                                            │
│  └── 生成测试报告                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 设计文档规范

每个设计阶段输出的文档采用统一格式，便于 Builder Agent 解析：

#### 1.4.1 技能设计文档 (01-skills-design.md)

```markdown
---
type: skills-design
workflow: workflow-name
version: 1.0
skills_count: 2
---

# 技能设计

## 概述
本工作流需要 2 个技能...

---

## Skill: code-analysis

### 基本信息
- **名称**: code-analysis
- **领域**: 代码质量分析
- **复用**: 无（新建）

### 触发条件
- "分析代码质量"
- "检查代码规范"
- "code review"

### 核心知识点
1. 代码复杂度评估方法
2. 常见代码坏味道识别
3. 重构建议生成

### 参考资料
- docs/code-standards.md
- 外部：Clean Code 原则

---

## Skill: report-generation

### 基本信息
- **名称**: report-generation
- **领域**: 报告生成
- **复用**: 可复用现有 @skills/markdown-report

### 触发条件
- "生成报告"
- "输出分析结果"

### 核心知识点
（复用现有技能，无需额外知识点）
```

#### 1.4.2 契约设计文档 (02-contracts-design.md)

````markdown
---
type: contracts-design
workflow: workflow-name
version: 1.0
contracts_count: 2
---

# 契约设计

## 概述
本工作流定义 2 个契约...

---

## Contract: analysis-result

### 基本信息
- **名称**: analysis-result
- **用途**: analyzer 节点的输出规范
- **校验时机**: SubagentStop (analyzer)

### Schema 定义
```yaml
type: object
required:
  - summary
  - issues
properties:
  summary:
    type: string
    description: 分析摘要
    minLength: 20
  issues:
    type: array
    items:
      type: object
      required: [file, line, severity, message]
      properties:
        file:
          type: string
        line:
          type: integer
        severity:
          type: string
          enum: [info, warning, error]
        message:
          type: string
```

### 示例数据

**正例**:
```json
{
  "summary": "分析了 15 个文件，发现 3 个问题",
  "issues": [
    {"file": "src/main.py", "line": 42, "severity": "warning", "message": "函数过长"}
  ]
}
```

**反例**:
```json
{
  "summary": "OK",
  "issues": "none"
}
```
反例说明：summary 过短，issues 应为数组

### 自定义校验（可选）
无

---

## Contract: final-report
...
````

#### 1.4.3 节点设计文档 (03-nodes-design.md)

```markdown
---
type: nodes-design
workflow: workflow-name
version: 1.0
nodes_count: 3
---

# 节点设计

## 概述
本工作流包含 3 个节点...

## 数据流图
```
用户输入 → [analyzer] → analysis.json → [processor] → result.json → [reporter] → report.md
```

---

## Node: analyzer

### 基本信息
- **名称**: analyzer
- **职责**: 分析输入代码，识别问题
- **模型**: inherit

### 输入输出
- **输入依赖**:
  - params: .context/params.md
- **输出**: .context/outputs/analyzer.json
- **输出契约**: analysis-result

### 绑定技能
- @skills/code-analysis

### 工具需求
- Read（读取代码文件）
- Grep（搜索模式）
- Write（输出结果）

### 触发示例
<example>
Context: 工作流执行到分析阶段
user: "开始分析 src/ 目录的代码"
assistant: "我将分析 src/ 目录下的所有代码文件..."
</example>

---

## Node: processor
...
```

#### 1.4.4 流程设计文档 (04-flow-design.md)

```markdown
---
type: flow-design
workflow: workflow-name
version: 1.0
---

# 流程设计

## 工作流概述
- **名称**: {workflow-name}
- **目标**: {workflow-goal}
- **参数**: {param-1} (必需), {param-2} (可选, 默认 {default-value})
- **输入契约**: {input-contract}（可选，校验用户输入参数）
- **输出契约**: {output-contract}（可选，校验工作流最终输出）

## 节点执行顺序

### 顺序执行
1. analyzer: 分析代码
2. processor: 处理分析结果
3. reporter: 生成报告

### 并行机会
- analyzer 和 processor 之间存在数据依赖，无法并行
- 如果有多个独立的分析任务，可以并行执行多个 analyzer 实例

## 条件分支
- 如果 analyzer 发现严重问题 (severity=error)，跳过 processor，直接生成紧急报告

## 异常处理
| 异常类型 | 处理策略 |
|----------|----------|
| 节点执行失败 | 记录错误，询问用户是否重试 |
| 契约校验失败 | 返回错误信息，要求节点修正输出 |
| 超时 | 终止当前节点，记录状态，支持续传 |

## 用户交互点
- 阶段开始前：确认参数
- 发现严重问题时：询问是否继续
- 完成后：展示报告摘要
```

### 1.5 并发创建策略

**混合粒度原则**：
- **设计阶段**：同类组件合并为一个设计文档，便于整体审视一致性
- **创建阶段**：拆分为独立任务，并发调用 Builder Agent

**并发规则**：
```
第一批（可完全并发）:
├── skill-builder × N（每个技能独立）
└── contract-builder × M（每个契约独立）

第二批（依赖第一批完成）:
└── node-builder × K（节点引用技能和契约）

第三批（依赖第二批完成）:
└── wf-entry-builder × 1（引用所有节点）

第四批（依赖前三批完成）:
└── cc-settings-builder × 1（汇总所有配置）
```

**依赖关系**：
- 技能和契约无互相依赖，可完全并发
- 节点依赖技能（绑定）和契约（引用），需等技能和契约创建完成
- 入口依赖所有节点（调度）
- 配置依赖所有组件（汇总 Hook 配置）

### 1.6 输出

创建完整的工作流目录结构：

```
.claude/
├── commands/
│   └── {workflow-name}.md     # cc-wf-entry
├── agents/
│   └── {node-name}.md         # cc-wf-node (多个)
├── skills/
│   └── {skill-name}/
│       └── SKILL.md           # cc-wf-skill (多个)
├── contracts/
│   └── {contract-name}.yaml   # contract-desc (多个)
├── hooks/
│   ├── contract-validator.py  # 契约校验脚本（由 cc-settings-builder 从插件复制）
│   ├── wf-state.py            # 状态治理脚本（由 cc-settings-builder 从插件复制）
│   └── wf_output_extractor.py # 输出提取工具（共享库，由上述两脚本导入）
└── settings.json              # Claude Code 配置（仅用户自定义）
```

```
.context/
├── params.json                # 工作流参数（初始化写入）
├── params.md                  # 工作流参数（可读）
├── state.md                   # 工作流状态
└── outputs/
    ├── {node-name}.json       # 节点输出（原始）
    └── {node-name}.md         # 节点输出（可读）
```

### 1.7 技术规范

- **allowed-tools**: `Read, Write, Edit, Glob, Grep, Task, AskUserQuestion, TodoWrite`
- **调用 Agent**: skill-builder, contract-builder, node-builder, wf-entry-builder, cc-settings-builder

### 1.8 设计要点

1. **会话管理**：create-cc-wf 作为主调度器，通过 Task 工具调用各 Builder Agent，避免单会话上下文过载
2. **进度追踪**：使用 TodoWrite 跟踪整体进度，每个阶段完成后更新状态
3. **错误处理**：任一 Agent 失败时，记录错误并询问用户是否重试或跳过
4. **增量创建**：支持在已有工作流基础上添加组件

---

## 2. skill-builder (Agent)

### 2.1 功能定义

**用途**：根据技能设计文档创建 cc-wf-skill (Skill)。

**类型**：Subagent（主智能体通过 Task 调用，也支持 @ 语法直接引用）

### 2.2 输入

**输入来源**：`01-skills-design.md` 中的单个技能章节

```markdown
## Skill: {skill-name}

### 基本信息
- **名称**: {skill-name}
- **领域**: {domain}
- **复用**: {reuse-info}

### 触发条件
- "{trigger-phrase-1}"
- "{trigger-phrase-2}"

### 核心知识点
1. {knowledge-point-1}
2. {knowledge-point-2}

### 参考资料
- {reference-path-1}
- {reference-path-2}
```

**调用方式**：
```
Task(skill-builder, prompt="根据以下设计创建技能：\n\n{skill-section-content}")
```

### 2.3 输出

```
.claude/skills/{skill-name}/
├── SKILL.md           # 主文件（YAML frontmatter + 正文）
├── references/        # 详细参考资料（可选）
├── examples/          # 示例代码（可选）
└── scripts/           # 工具脚本（可选）
```

**SKILL.md 结构**：
```yaml
---
name: skill-name
description: This skill should be used when [触发条件]...
version: 1.0.0
---

# 核心指导

[祈使句形式的领域知识，1,500-2,000 词]

## 关键概念

## 基本流程

## 快速参考

## 资源指引
```

### 2.4 技术规范

- **model**: inherit（继承主智能体模型）
- **tools**: `Read, Write, Edit, Glob, Grep`
- **绑定技能**: `@skills/skill-development`

### 2.5 设计要点

1. **触发条件设计**：description 必须包含具体的触发短语，使用第三人称
2. **渐进式披露**：核心内容在 SKILL.md（<2k 词），详细内容在 references/
3. **祈使句风格**：正文使用动词开头的指令形式
4. **资料整合**：自动读取用户提供的参考资料，提炼核心知识

---

## 3. contract-validator.py (Hook Script)

### 3.1 功能定义

**用途**：契约校验脚本，验证工作流和节点的输入输出是否符合契约规范。负责**结构校验**（JSON Schema）和**自定义校验**（validator_script），语义校验由节点内部 prompt hook 处理。

**配置位置**：
- **工作流级配置**
  - settings.json：工作流输入校验（UserPromptSubmit）
  - wf-entry frontmatter：工作流输出校验（Stop）
- **节点级配置**（节点 agent frontmatter）：节点输出校验（Stop → SubagentStop）

#### 校验设计理念

契约校验采用**边界校验**策略，只在数据进入和离开的边界进行校验：

```
用户输入 ──[工作流输入校验]──→ 节点A ──[节点A输出校验]──→ 节点B ──[节点B输出校验]──→ 最终输出
              ↑                           ↑                           ↑
           外部边界                    节点边界                    节点边界
```

**为什么不需要节点输入校验？**

在封闭的工作流系统中：
- 节点B的输入 = 节点A的输出（已通过输出校验）
- 如果每个节点的输出都校验了，下游节点的输入自然合规
- 节点输入校验是**冗余**的

**校验层次**：

| 校验点 | 目的 | 触发事件 |
|--------|------|----------|
| 工作流输入 | 防止外部脏数据进入 | UserPromptSubmit |
| 节点输出 | 确保每个节点产出合规 | SubagentStop（节点 Stop hook 转换） |
| 工作流输出 | 最终输出校验（可选） | Stop |

### 3.2 触发时机

| Hook 事件 | 配置位置 | 校验类型 | 说明 |
|-----------|----------|----------|------|
| UserPromptSubmit | settings.json | 工作流输入校验 | 匹配工作流启动命令，校验输入契约 |
| Stop | wf-entry frontmatter | 工作流输出校验 | 工作流有输出契约时，结束时校验 |
| Stop -> SubagentStop | 节点 frontmatter | 节点输出校验 | 节点有输出契约时，校验失败阻止退出 |

> **注**：节点 frontmatter 中的 Stop hook 会自动转换为 SubagentStop 事件，输入格式包含 `agent_id` 和 `agent_transcript_path`。

> **hooks 生命周期**：节点 frontmatter 中的 hooks **仅在该节点活动期间有效**，节点完成后自动清理，不影响其他节点。

### 3.3 输入

脚本通过 **命令行参数** 和 **stdin JSON** 接收输入。

#### 命令行参数

根据不同场景传递不同参数：

**工作流输入校验（UserPromptSubmit）**：
```bash
python contract-validator.py --workflow <workflow-name> --contract <contract-name>
```

**节点输出校验（SubagentStop）**：
```bash
python contract-validator.py --contract <contract-name> --node <node-name>
```

| 参数 | 说明 |
|------|------|
| `--workflow` | 工作流名称，用于匹配 prompt 中的命令（如 `/<workflow-name>`） |
| `--contract` | 契约名称，用于加载契约文件 |
| `--node` | 节点名称，用于错误信息和日志 |

> **命令匹配逻辑**：当提供 `--workflow` 参数时，脚本检查 stdin 的 `prompt` 是否匹配 `/*{workflow}*` 模式（即 prompt 以 `/` 开头且包含工作流名称），不匹配则直接 exit(0) 跳过校验。

#### stdin JSON

**公共字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | string | 会话 ID |
| `transcript_path` | string | 会话记录文件路径（JSONL 格式），可读取完整对话历史 |
| `cwd` | string | Hook 被调用时的当前工作目录 |
| `permission_mode` | string | 权限模式：`default` / `plan` / `acceptEdits` / `bypassPermissions` |
| `hook_event_name` | string | 事件名称：`UserPromptSubmit` / `PreToolUse` / `SubagentStop` / `Stop` |

**事件特有字段**：

| 事件 | 特有字段 |
|------|----------|
| UserPromptSubmit | `prompt` |
| PreToolUse | `tool_name`, `tool_input`, `tool_use_id` |
| PostToolUse | `tool_name`, `tool_input`, `tool_response`, `tool_use_id` |
| SubagentStop | `stop_hook_active`, `agent_id`, `agent_transcript_path` |
| Stop | `stop_hook_active` |

**Task 工具的 tool_input 结构**（wf-state.py 使用）：

```json
{
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "node-name",
    "prompt": "执行节点任务",
    "description": "任务描述"
  }
}
```

**Task 工具的 tool_response 结构**（PostToolUse）：

```json
{
  "tool_response": "节点返回的最后一条消息内容"
}
```

#### 数据获取方式汇总

| 事件 | 契约来源 | 校验数据 |
|------|----------|----------|
| UserPromptSubmit | 工作流入口配置 | `.context/params.json`（wf-state.py 先行写入） |
| SubagentStop | 命令行参数 `--contract` | `agent_transcript_path` |
| Stop | 工作流入口配置 | `transcript_path` |

**环境变量**：`CLAUDE_PROJECT_DIR`（项目根目录绝对路径）

### 3.4 输出

契约校验后决定是否允许继续执行。

| 退出码 | 行为 |
|--------|------|
| 0 | 通过，允许继续（stdout 可包含 JSON 进行结构化控制） |
| 2 | 阻止，stderr 作为错误消息（JSON 不处理） |

**校验失败时的处理**：

| 事件 | 阻止方式 | 失败处理 |
|------|----------|----------|
| UserPromptSubmit | `exit(2)` + stderr | 拦截不合规输入，用户根据提示修正后重新提交 |
| SubagentStop | `exit(0)` + JSON | 阻止节点结束，节点根据错误修正输出后重试 |
| Stop | `exit(0)` + JSON | 阻止工作流结束，主调度根据错误补全输出后重试 |

> SubagentStop/Stop 的 JSON 格式：`{"decision": "block", "reason": "错误信息"}`


### 3.5 契约定位流程

不同事件的契约定位方式不同：

| 事件 | 契约定位方式 | 校验数据来源 |
|------|-------------|--------------|
| UserPromptSubmit | 命令行参数 `--contract` 直接提供（由 cc-settings-builder 根据流程设计生成） | `.context/params.json`（由 wf-state.py 先行写入） |
| SubagentStop | 命令行参数 `--contract` 直接提供 | `agent_transcript_path` |
| Stop | 命令行参数 `--contract` 直接提供（由 wf-entry-builder 根据流程设计生成） | `transcript_path` |

**SubagentStop 的简化流程**：

```
1. 从命令行参数获取契约名称
   └── --contract <contract-name>

2. 加载契约 schema
    └── 读取 $CLAUDE_PROJECT_DIR/.claude/contracts/{contract-name}.yaml

3. 提取并校验输出
   ├── 从 agent_transcript_path 读取最后一条 assistant 消息
   ├── 从消息中提取 JSON 数据（见下方提取规则）
   └── 用 schema 校验提取的 JSON
```

**数据提取规则**（由 `wf_output_extractor.py` 统一实现）：
1. 优先匹配 ` ```json ... ``` ` 代码块（取最后一个），提取代码块内容
2. 若无代码块，尝试将整条消息解析为 JSON
3. 两者都失败则报错"无法提取结构化输出"

> 由于节点 frontmatter 的 Stop hook 由 node-builder 生成，契约名称在生成时就已确定并写入命令行参数，无需运行时解析 transcript。
>
> **注**：contract-validator.py 通过 `from wf_output_extractor import extract_from_transcript` 调用提取逻辑，确保与 wf-state.py 的提取行为一致。

### 3.6 工作流程

```
1. 从 stdin 读取 JSON，解析 hook_event_name
2. 根据事件类型获取校验数据：
   ├── UserPromptSubmit → 读取 .context/params.json（wf-state.py 已写入）
   ├── SubagentStop → 从 agent_transcript_path 提取最后一条 assistant 消息
   └── Stop → 从 transcript_path 提取最后一条 assistant 消息
3. 加载契约文件，按顺序执行校验：
   ├── schema 存在？→ JSON Schema 结构校验
   └── validator_script 存在？→ 执行自定义 Python 脚本
4. 输出结果：全部通过 exit(0)，任一失败 exit(2)/JSON
```

> **注**：语义校验（`semantic_check`）不由本脚本处理，而是由 node-builder 生成为节点级 prompt hook，详见 [4.3 契约文件结构](#43-输出) 和 [5.3 输出](#53-输出)。

### 3.7 技术规范

- **语言**: Python 3.8+
- **依赖**: pydantic, pyyaml, jsonschema
- **超时**: 30 秒

### 3.8 设计要点

1. **失败即阻止**：
   - UserPromptSubmit: `exit(2)` 阻止执行
   - SubagentStop/Stop: JSON `"decision": "block"` 阻止结束并要求修正
2. **清晰的错误信息**：包含具体字段、期望值、实际值、修复建议
3. **契约文件映射**：通过节点/工作流名称自动查找对应契约
4. **分层校验**：schema → validator_script，按需执行（语义校验由节点级 prompt hook 处理）

---

## 4. contract-builder (Agent)

### 4.1 功能定义

**用途**：根据契约设计文档创建 contract-desc（契约描述文件）和可选的 contract-validator（自定义校验器）。

**类型**：Subagent

### 4.2 输入

**输入来源**：`02-contracts-design.md` 中的单个契约章节

````markdown
## Contract: {contract-name}

### 基本信息
- **名称**: {contract-name}
- **用途**: {purpose}
- **校验时机**: {validation-timing}

### Schema 定义
```yaml
{schema-definition}
```

### 示例数据

**正例**:
```json
{valid-example}
```

**反例**:
```json
{invalid-example}
```

### 自定义校验（可选）
{custom-validation-rules}
````

**调用方式**：
```
Task(contract-builder, prompt="根据以下设计创建契约：\n\n{contract-section-content}")
```

### 4.3 输出

```
.claude/contracts/
└── {contract-name}.yaml       # 契约定义文件
```

**契约文件结构**：

```yaml
# .claude/contracts/analysis-result.yaml

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
      description: 分析摘要
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

**字段说明**：

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 是 | 契约名称，用于引用 |
| `description` | 是 | 契约描述 |
| `schema` | 否 | JSON Schema，用于结构校验（由 contract-validator.py 执行） |
| `validator_script` | 否 | 自定义 Python 校验脚本路径（由 contract-validator.py 执行） |
| `semantic_check` | 否 | 语义校验 prompt，**由 node-builder 生成为节点级 prompt hook** |
| `examples` | 否 | 正例/反例，用于测试和文档 |

> **校验分工**：
> - `schema` 和 `validator_script` 由 contract-validator.py 在运行时执行
> - `semantic_check` 由 node-builder 读取，生成为节点 frontmatter 中的 prompt hook，利用 Claude Code 原生机制执行

**不同类型契约示例**：

```yaml
# 纯结构校验（结构化数据）
name: api-response
schema:
  type: object
  required: [status, data]
  ...

# 纯语义校验（非结构化输出，如 Markdown 报告）
name: design-report
description: 设计报告输出规范
semantic_check: |
  检查报告是否包含概述、设计方案、实现计划等章节。
  检查方案是否具有可行性，逻辑是否清晰。

# 混合校验
name: analysis-result
schema: { ... }
semantic_check: |
  检查 summary 是否准确概括了 issues...
```

**校验执行机制**：

| 校验层 | 执行者 | 触发时机 |
|--------|--------|----------|
| `schema` | contract-validator.py | 节点 Stop hook (command) |
| `validator_script` | contract-validator.py | 节点 Stop hook (command) |
| `semantic_check` | Claude Code 原生 | 节点 Stop hook (prompt) |

> 结构校验和语义校验都配置在节点 frontmatter 的 Stop hook 中，按顺序执行。任一失败即阻止节点结束。


### 4.4 技术规范

- **model**: inherit
- **tools**: `Read, Write, Edit, Glob`
- **绑定技能**: `@skills/contract-development`（待创建）

### 4.5 设计要点

1. **Schema 优先**：优先使用声明式 Schema，复杂业务规则才用自定义校验器
2. **示例驱动**：每个契约必须包含至少 2 个示例（正例和反例）
3. **文档清晰**：契约说明文档要解释每个字段的业务含义

---

## 5. node-builder (Agent)

### 5.1 功能定义

**用途**：根据节点设计文档创建 cc-wf-node (Subagent)。

**类型**：Subagent

### 5.2 输入

**输入来源**：`03-nodes-design.md` 中的单个节点章节

```markdown
## Node: {node-name}

### 基本信息
- **名称**: {node-name}
- **职责**: {responsibility}
- **模型**: {model}

### 输入输出
- **输入依赖**:
  - params: .context/params.md
  - {prev-node}: .context/outputs/{prev-node}.md
- **输出**: {output-path}
- **输出契约**: {output-contract}

### 绑定技能
- @skills/{skill-name}

### 工具需求
- {tool-1}
- {tool-2}

### 触发示例
<example>
Context: {context}
user: "{user-request}"
assistant: "{assistant-response}"
</example>
```

**调用方式**：
```
Task(node-builder, prompt="根据以下设计创建节点：\n\n{node-section-content}")
```

### 5.3 输出

```
.claude/agents/{node-name}.md
```

**文件结构**：
```yaml
---
name: node-identifier
description: Use this agent when [触发条件].
model: inherit
color: blue
tools: Read, Write, Edit, Glob, Grep

# 绑定技能（从节点设计文档读取，逗号分隔）
skills: {skill-name-1}, {skill-name-2}

# 契约校验 hooks（当有 output_contract 时生成）
hooks:
  Stop:
    - hooks:
        # 结构校验（command hook）
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py --contract {output_contract} --node {node-name}"
        # 语义校验（prompt hook，从契约的 semantic_check 生成）
        - type: prompt
          prompt: |
            检查输出是否符合以下要求：
            [从契约的 semantic_check 字段读取]

            输入数据: $ARGUMENTS

            返回 JSON: {"ok": true} 或 {"ok": false, "reason": "原因"}

# 契约配置（供 contract-validator.py 解析）
output_contract: {contract-name}  # 可选，无输出契约时省略
---

You are [角色描述]...

## 数据读取

在开始工作前，读取以下数据：

- **工作流参数**: [workflow-params.md](.context/params.md)
- **前序节点输出**: [step1-output.md](.context/outputs/step1.md)

> 使用 Read 工具读取上述文件，验证数据后再执行业务逻辑。

## 职责

1. [职责1]
2. [职责2]

## 流程

1. 读取输入数据（见上方链接）
2. [业务步骤1]
3. [业务步骤2]
4. 输出结果（由 wf-state.py 自动提取并写入 `.context/` 目录）

## 输出格式

（仅当节点定义了 output_contract 时生成此章节）

节点必须在最后一条消息中包含结构化输出，使用 JSON 代码块标记：

\`\`\`json
{
  "field1": "value1",
  "field2": "value2"
}
\`\`\`

> 可以在代码块前后添加解释性文本，提取脚本会自动识别 \`\`\`json\`\`\` 代码块。

（若节点无 output_contract，则省略此章节，输出格式自由）
```

**数据引用模式**：

节点系统提示使用 Markdown 链接引用数据文件，Claude 启动后会读取这些文件：

```markdown
- [input.md](.context/outputs/prev-node.md)
```

| 引用类型 | 路径格式 |
|---------|---------|
| 工作流参数 | `.context/params.md` |
| 节点输出 | `.context/outputs/{node-name}.md` |
| 节点日志 | `.context/logs/{node-name}.log`（可选） |

> **注**：node-builder 直接使用节点设计文档中 `输入依赖` 字段的结构化路径生成引用。

**输出格式章节生成规则**：

| 条件 | 生成内容 |
|------|----------|
| 有 `output_contract` | 生成"输出格式"章节，要求使用 ` ```json ``` ` 代码块输出结构化数据 |
| 无 `output_contract` | 不生成"输出格式"章节，节点输出格式自由 |

**hooks 生成规则**：

| 条件 | 生成的 hook |
|------|-------------|
| 有 `output_contract` | 生成 `Stop` hook，包含带参数的 command hook |
| 契约有 `semantic_check` | 在 `Stop` hook 中追加 prompt hook |
| 无 `output_contract` | 不生成 `Stop` hook |

**command hook 参数**：

| 参数 | 值来源 |
|------|--------|
| `--contract` | 节点的 `output_contract` 字段值 |
| `--node` | 节点名称（agent 文件名，不含扩展名） |

> **注**：Stop hook 在 subagent frontmatter 中会自动转换为 SubagentStop 事件。

> **hooks 隔离性**：每个节点的 hooks 独立运行，互不干扰。节点 A 的 Stop hook 只校验节点 A 的输出，不会触发节点 B、C 的校验。

### 5.4 技术规范

- **model**: inherit
- **tools**: `Read, Write, Edit, Glob, Grep`
- **绑定技能**: `@skills/agent-development`

### 5.5 设计要点

1. **单一职责**：一个节点完成一个明确的任务
2. **契约意识**：系统提示词中明确说明输出契约要求
3. **强触发示例**：description 包含 2-4 个具体的触发示例
4. **最小权限**：只授予完成任务必需的工具
5. **按需生成 hooks**：只有定义了 output_contract 的节点才生成 Stop hook
6. **按需生成输出格式章节**：只有定义了 output_contract 的节点才在系统提示中生成"输出格式"章节，要求使用 JSON 代码块；无契约的节点输出格式自由

---

## 6. wf-entry-builder (Agent)

### 6.1 功能定义

**用途**：根据流程设计文档创建 cc-wf-entry (Command)，作为工作流的入口和主调度器，cc-wf-entry 只负责调度节点执行，不能参与节点内部的业务逻辑。

**类型**：Subagent

### 6.2 输入

**输入来源**：`04-flow-design.md` 完整文档 + `03-nodes-design.md` 节点列表

> wf-entry-builder 从流程设计文档读取 `输入契约` 和 `输出契约` 字段（如有），输出契约用于生成 Stop hook 中的契约校验配置。

```markdown
---
type: flow-design
workflow: {workflow-name}
version: 1.0
---

# 流程设计

## 工作流概述
- **名称**: {workflow-name}
- **目标**: {workflow-goal}
- **参数**: {parameters}

## 节点执行顺序
{execution-order}

## 条件分支
{conditional-logic}

## 异常处理
{error-handling}

## 用户交互点
{user-interaction-points}
```

**调用方式**：
```
Task(wf-entry-builder, prompt="根据以下设计创建工作流入口：\n\n{flow-design-content}\n\n节点列表：\n{nodes-summary}")
```

### 6.3 输出

```
.claude/commands/{workflow-name}.md
```

**文件结构**：
```yaml
---
name: workflow-name
description: 工作流简短描述
argument-hint: "[参数说明]"
allowed-tools: Read, Write, Task, AskUserQuestion, TodoWrite, Bash(mkdir:*), Bash(echo:*)

# 状态追踪 hooks（监听节点调用）
hooks:
  PreToolUse:
    - matcher: "Task"
      hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/wf-state.py"
  PostToolUse:
    - matcher: "Task"
      hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/wf-state.py"
  Stop:
    - hooks:
        # 工作流完成状态记录
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/wf-state.py"
        # 工作流输出校验（仅当流程设计指定了输出契约时生成）
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py --contract <output-contract> --workflow <workflow-name>"
---

# 工作流名称

## 工作流初始化

> 目录创建和参数写入由 `wf-state.py` 在 UserPromptSubmit 时自动完成，无需 Claude 手动执行。
>
> 初始化后的文件结构：
> - `.context/params.json` - 原始参数（JSON 格式）
> - `.context/params.md` - 可读参数（Markdown 格式）
> - `.context/state.md` - 工作流状态

## 目标
[工作流目标描述]

## 节点定义
| 节点 | Agent | 职责 | 输入源 | 输出 |
|------|-------|------|--------|------|
| step1 | @agents/analyzer | 分析输入 | 用户参数 | .context/outputs/step1.json |
| step2 | @agents/processor | 处理数据 | step1 输出 | .context/outputs/step2.json |

> **节点输入方式**：节点根据自身输入契约从 `.context/` 读取数据，主调度不传递业务数据。

## 流程控制

### 执行顺序
1. step1: 分析阶段
2. step2: 处理阶段（依赖 step1）

### 并行执行
- step2a 和 step2b 无依赖关系，可并行执行
- 使用多个 Task 调用在同一消息中发起并行节点

### 条件分支
- 如果 step1.issue_count > 10，执行 step2a
- 否则执行 step2b

### 异常处理
- 节点失败：记录错误，询问用户是否重试
- 契约校验失败：节点 Stop hook 会阻止完成，需修正后重试

## 调度指令

执行此工作流时，按以下步骤操作：

### 1. 检查断点恢复

```
状态文件路径: .context/state.md
```

- 检查状态文件是否存在
- **若存在**：读取状态，识别 `next_node`，从断点继续执行
- **若不存在**：新执行，进入初始化阶段

### 2. 初始化（自动）

> 目录创建、参数写入、状态初始化由 `wf-state.py` 在 UserPromptSubmit 时自动完成。

Claude 只需读取 `.context/params.md` 了解参数，使用 TodoWrite 创建任务列表，然后开始执行节点。

### 3. 执行节点

**串行节点**：
```
Task(step1-agent, prompt="执行 step1 节点")
```

**并行节点**（在同一消息中发起多个 Task）：
```
Task(step2a-agent, prompt="执行 step2a 节点")
Task(step2b-agent, prompt="执行 step2b 节点")
```

**数据流**：
- 主调度**不传递业务数据**，只发调度指令
- 节点系统提示中包含数据引用路径（如 `.context/outputs/prev-node.md`）
- 节点启动后通过 Read 工具读取引用的文件（.md 格式，便于理解）
- 节点输出后，wf-state.py 在 PostToolUse 时从 `tool_response` 直接获取并写入 `.context/`

**状态追踪**：
- PreToolUse/PostToolUse hooks 自动调用 wf-state.py 记录节点状态
- 每个节点完成后更新 TodoWrite

### 4. 完成处理

- 检查所有节点状态
- 生成最终报告（可选）
- 状态文件标记为 `completed`
```

### 6.4 技术规范

- **model**: inherit
- **tools**: `Read, Write, Edit, Glob, Grep`
- **绑定技能**: `@skills/command-development`

### 6.5 设计要点

1. **为智能体编写**：Command 正文是给 Claude 的调度指令，不是给用户的说明
2. **DSL 可读性**：使用 Markdown 表格和列表描述流程，便于智能体理解
3. **状态管理**：利用 TodoWrite 跟踪执行进度
4. **错误恢复**：明确异常处理策略，支持重试和回退

---

## 7. cc-settings-builder (Agent)

### 7.1 功能定义

**用途**：根据用户的 mcp 工具需求配置 settings.json，并复制运行时 hooks 脚本到项目。

**类型**：Subagent

### 7.2 输入

**输入来源**：用户可选的 MCP 配置 + `04-flow-design.md`（读取输入契约配置）

> cc-settings-builder 从流程设计文档读取 `输入契约` 字段（如有），生成 settings.json 中的 UserPromptSubmit hook。

**调用方式**：
```
Task(cc-settings-builder, prompt="生成 .claude/settings.json。\n\n用户 MCP 配置（可选）: {user-mcp-config}\n\n流程设计: {flow-design-content}")
```

### 7.3 输出

```
.claude/
├── settings.json
└── hooks/
    ├── contract-validator.py  # 从插件复制
    ├── wf-state.py            # 从插件复制
    └── wf_output_extractor.py # 从插件复制（共享库）
```

> cc-settings-builder 从 `${CLAUDE_PLUGIN_ROOT}/resources/hooks/` 复制运行时脚本到项目的 `.claude/hooks/` 目录。三个脚本需一起复制，因为 `contract-validator.py` 和 `wf-state.py` 都依赖 `wf_output_extractor.py`。

**文件结构**（当流程设计指定了输入契约时）：

> **注**：UserPromptSubmit 事件不支持 matcher，脚本需要在内部检查 `prompt` 是否匹配 `/*{workflow}*` 模式，不匹配则直接 exit(0) 跳过。

```json
{
  "mcpServers": {
    "example-server": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"]
    }
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/wf-state.py --workflow <workflow-name>"
          },
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py --workflow <workflow-name> --contract <input-contract>"
          }
        ]
      }
    ]
  }
}
```

### 7.4 技术规范

- **model**: inherit
- **tools**: `Read, Write, Edit, Glob`

---

## 8. wf-state.py (Hook Script)

### 8.1 功能定义

**用途**：工作流状态治理脚本，自动维护工作流执行状态文件，转换节点输出为上下文的文件，支持进度追踪和断点续传。

**类型**：Hook Script

### 8.2 触发时机

| Hook 事件 | 动作 | 说明 |
|-----------|------|------|
| UserPromptSubmit | 初始化工作流（目录、参数、状态） | 脚本内部检查 prompt 是否匹配 `/*{workflow}*` 模式，不匹配则 exit(0) 跳过 |
| PreToolUse (Task) | 记录节点开始 | 从 tool_input 获取节点名称，配置在 wf-entry 的 frontmatter |
| PostToolUse (Task) | 记录节点完成/失败，转换节点输出为上下文文件 | tool_result 已写入，可获取完整结果，配置在 command 的 frontmatter |
| Stop | 记录工作流完成 | 更新整体状态，计算执行时长，配置在 command 的 frontmatter |

> **注**：command 的 frontmatter hook 目前只有 PreToolUse、PostToolUse、Stop 三种类型可用。

### 8.3 输入

输入格式同 [3.3 输入](#33-输入)，各事件用途：

| 事件 | 用途 |
|------|------|
| UserPromptSubmit | 检查 `prompt` 是否匹配 `/*{workflow}*` 模式，匹配则执行完整初始化（见 8.5 节第 5 点），不匹配则 exit(0) |
| PreToolUse | 从 `tool_input.subagent_type` 获取节点名，记录开始 |
| PostToolUse | 从 `tool_input.subagent_type` 获取节点名，从 `tool_response` 提取输出并写入 `.context/`，记录节点完成 |
| Stop | 记录工作流完成，计算时长 |

**命令行参数**：

```bash
python wf-state.py --workflow <workflow-name>
```

| 参数 | 说明 |
|------|------|
| `--workflow` | 工作流名称，用于 UserPromptSubmit 时匹配命令 |

> 仅 UserPromptSubmit 事件需要 `--workflow` 参数进行命令匹配，其他事件（PreToolUse/PostToolUse/Stop）由 wf-entry frontmatter 配置，已隐式绑定工作流。

### 8.4 输出

状态文件位置：`.context/state.md`

**设计原则**：
- **断点恢复**：记录 `session_id`，依赖 Claude Code 原生会话恢复能力
- **外部可见性**：外界可读取状态文件了解工作流进度
- **输出提取**：记录节点输出文件路径，方便外部读取

**文件格式**（Markdown + YAML frontmatter）：
```yaml
---
workflow: workflow-name
session_id: abc123-def456      # 断点恢复的关键
status: running | completed | failed | paused
started_at: 2024-01-15T10:30:00Z
updated_at: 2024-01-15T10:35:00Z
completed_at: null
current_node: step2
progress: 1/4

# 节点输出引用（供外部提取）
outputs:
  step1: .context/outputs/step1.json
---

# 工作流执行状态

## 执行概览
- **工作流**: workflow-name
- **会话**: abc123-def456
- **状态**: 🔄 运行中
- **进度**: 1/4 节点完成
- **当前节点**: step2

## 节点状态

| 节点 | 状态 | 开始时间 | 完成时间 | 输出 |
|------|------|----------|----------|------|
| step1 | ✅ 完成 | 10:30:00 | 10:32:15 | [查看](.context/outputs/step1.json) |
| step2 | 🔄 执行中 | 10:32:20 | - | - |
| step3 | ⏳ 待执行 | - | - | - |
| step4 | ⏳ 待执行 | - | - | - |

## 执行日志

### step1 - 分析阶段
- **开始**: 10:30:00
- **结束**: 10:32:15
- **结果**: 成功
- **摘要**: 分析了 10 个文件，发现 5 个问题

### step2 - 处理阶段
- **开始**: 10:32:20
- **状态**: 执行中
```

### 8.5 支持功能

1. **基础状态跟踪**
   - 记录工作流启动、各节点开始/完成、工作流完成
   - 计算各阶段耗时

2. **断点续传**
   - 记录 `session_id`，依赖 Claude Code 原生会话恢复
   - 恢复时通过 `session_id` 找到 transcript，继续执行

3. **外部可见性**
   - 外部工具/用户可读取状态文件了解进度
   - 支持构建监控仪表盘、告警等

4. **节点输出提取与写入**
   - 在 PostToolUse 时从 stdin 的 `tool_response` 直接获取节点输出（无需读取 transcript）
   - **数据提取**：调用 `from wf_output_extractor import extract_from_tool_response`，与 contract-validator.py 使用相同的提取逻辑
   - **写入规则**：
     - `.context/outputs/{node-name}.json`：提取的 JSON 数据（若 `json_data` 为 None 则不写入）
     - `.context/outputs/{node-name}.md`：`raw_text` 原始内容（便于后续节点理解）
   - 记录输出文件路径到状态文件的 `outputs` 映射

5. **工作流初始化**（UserPromptSubmit 时执行）
   - 从 stdin 的 `prompt` 字段解析用户输入参数
   - **参数格式**: `--<arg-name> <arg-value>` 或 `--<arg-name>=<arg-value>`
   - 创建 `.context/` 目录结构（含 `outputs/` 子目录）
   - 写入参数文件：
     - `.context/params.json`：原始 JSON 格式
     - `.context/params.md`：人类可读的 Markdown 格式
   - 初始化 `.context/state.md` 状态文件
   - **params.md 格式示例**：
     ```markdown
     # 工作流参数

     | 参数 | 值 |
     |------|-----|
     | target_dir | src/ |
     | output_format | json |
     ```
   - 节点通过读取 `params.md` 获取工作流参数，保持与节点输出（`.md` 格式）的一致性

---

## 9. wf_output_extractor.py (共享库)

### 9.1 功能定义

**用途**：从 transcript 文件或 tool_response 文本中提取节点的结构化输出。作为共享库供 `contract-validator.py` 和 `wf-state.py` 导入使用，确保提取逻辑一致。

**类型**：Python 模块（也支持命令行独立使用）

### 9.2 设计背景

`contract-validator.py` 和 `wf-state.py` 都需要从节点输出中提取结构化数据：

| 脚本 | 触发事件 | 数据来源 | 目的 |
|------|----------|----------|------|
| contract-validator.py | SubagentStop | `agent_transcript_path` | 校验输出是否合规 |
| wf-state.py | PostToolUse | `tool_response` | 写入 `.context/outputs/` |

为避免重复实现和潜在的不一致性，将提取逻辑抽取为独立模块。

### 9.3 API 接口

```python
from wf_output_extractor import (
    extract_from_transcript,   # SubagentStop 场景
    extract_from_tool_response # PostToolUse 场景
)

# 返回 ExtractionResult 数据类
@dataclass
class ExtractionResult:
    success: bool              # 提取是否成功
    json_data: Any | None      # 提取的 JSON 数据（若有）
    raw_text: str              # 原始文本内容
    error: str | None          # 错误信息（若失败）
    source: str                # 数据来源标识
```

**使用示例**：

```python
# contract-validator.py 中
result = extract_from_transcript(agent_transcript_path)
if result.json_data is None:
    return {"decision": "block", "reason": "无法提取结构化输出"}
# 用 result.json_data 进行 schema 校验

# wf-state.py 中
result = extract_from_tool_response(tool_response)
if result.json_data is not None:
    write_json(f".context/outputs/{node}.json", result.json_data)
write_text(f".context/outputs/{node}.md", result.raw_text)
```

### 9.4 提取规则

提取规则（按优先级）：

| 优先级 | 规则 | source 标识 |
|--------|------|-------------|
| 1 | 匹配 ` ```json ... ``` ` 代码块（取最后一个） | `json_code_block` |
| 2 | 尝试将整条消息解析为 JSON | `raw_json` |
| 3 | 返回原始文本（`json_data = None`） | `plain_text` |

### 9.5 Transcript 文件格式

Transcript 文件为 JSONL 格式，每行一个 JSON 对象：

```json
{
  "type": "user" | "assistant",
  "agentId": "agent-id",
  "message": {
    "role": "user" | "assistant",
    "content": [
      {"type": "text", "text": "消息文本内容"},
      {"type": "tool_use", "name": "ToolName", "input": {...}}
    ]
  },
  "uuid": "message-uuid",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**提取最后一条 assistant 消息的步骤**：
1. 逐行解析 JSONL
2. 过滤 `type == "assistant"` 的行
3. 取最后一条
4. 从 `message.content` 数组中提取 `type == "text"` 的项
5. 拼接所有 `text` 字段

### 9.6 命令行用法

```bash
# 从 transcript 提取
python wf_output_extractor.py --transcript <path>

# 从文本提取
python wf_output_extractor.py --text "..."

# 从 stdin 读取
echo "..." | python wf_output_extractor.py --stdin

# 只输出 JSON 部分（用于管道）
python wf_output_extractor.py --transcript <path> --json-only

# 只输出原始文本
python wf_output_extractor.py --transcript <path> --raw-only
```

### 9.7 技术规范

- **语言**: Python 3.8+
- **依赖**: 无外部依赖（仅使用标准库）
- **位置**: `${CLAUDE_PLUGIN_ROOT}/resources/hooks/wf_output_extractor.py`

---

## 10. review-cc-wf (Command)

### 10.1 功能定义

**用途**：校验工作流组件的规范性、功能完整性，并支持运行时问题定位。

**类型**：Command

### 10.2 输入

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| workflow-dir | string | 否 | 工作流目录，默认当前目录 |
| --mode | enum | 否 | 校验模式：structure / function / runtime |
| --log | string | 否 | 运行日志路径（runtime 模式需要） |

### 10.3 审查范围

#### 10.3.1 结构规范校验（--mode structure）

检查各组件是否符合 Claude Code 规范：

| 组件类型 | 校验项 |
|----------|--------|
| Skill | frontmatter 字段、description 触发短语、正文词数、祈使句风格 |
| Agent | frontmatter 字段、触发示例数量、系统提示词结构、tools 配置 |
| Command | frontmatter 字段、allowed-tools、正文结构 |
| Contract | Schema 格式、必需字段、示例数据 |
| Hook Script | 语法正确、输入输出格式、超时配置 |
| settings.json | JSON 格式、MCP 配置 |

#### 10.3.2 功能完整性校验（--mode function）

检查工作流是否满足用户需求：

| 校验项 | 说明 |
|--------|------|
| 节点覆盖 | 所有声明的节点都有对应的 Agent |
| 技能绑定 | 节点引用的技能都存在 |
| 契约匹配 | 节点输入输出契约正确配置 |
| 流程完整 | 入口到出口的路径完整 |
| 依赖关系 | 节点间数据依赖正确 |

#### 10.3.3 运行时问题定位（--mode runtime）

分析工作流执行日志，定位问题根因：

| 分析项 | 说明 |
|--------|------|
| 失败节点 | 识别哪个节点失败 |
| 错误类型 | 分类错误（契约校验、执行错误、超时等） |
| 上下文分析 | 分析失败时的输入数据和状态 |
| 修复建议 | 给出具体的修复建议 |

### 10.4 输出

生成审查报告：

```markdown
# 工作流审查报告

## 概览
- **工作流**: workflow-name
- **审查模式**: structure / function / runtime
- **审查时间**: 2024-01-15 10:30:00
- **总体结果**: ✅ 通过 / ⚠️ 有警告 / ❌ 有错误

## 发现问题

### ❌ 错误 (必须修复)

1. **agents/analyzer.md - 缺少触发示例**
   - 位置: frontmatter.description
   - 问题: description 中没有 <example> 块
   - 修复: 添加 2-4 个触发示例

### ⚠️ 警告 (建议修复)

1. **skills/analysis/SKILL.md - 正文过长**
   - 位置: 正文
   - 问题: 正文 3,500 词，建议 <2,000 词
   - 修复: 将详细内容移至 references/

## 审查统计
- 检查项: 25
- 通过: 22
- 警告: 2
- 错误: 1
```

### 10.5 技术规范

- **allowed-tools**: `Read, Glob, Grep, Bash, Task, AskUserQuestion, TodoWrite`
- **绑定技能**: `@skills/command-development`, `@skills/agent-development`, `@skills/skill-development`

### 10.6 设计要点

1. **分级报告**：错误必须修复，警告建议修复
2. **具体定位**：指出问题的具体文件和位置
3. **可操作建议**：给出具体的修复步骤
4. **增量校验**：支持只校验变更的文件

---

## 附录

### A. 术语对照表

| 术语 | 说明 |
|------|------|
| cc-wf | Claude Code Workflow |
| cc-wf-skill | 工作流技能（对应 Claude Code Skill） |
| cc-wf-node | 工作流节点（对应 Claude Code Subagent） |
| cc-wf-entry | 工作流入口（对应 Claude Code Command） |
| contract-desc | 契约描述文件（Schema） |
| contract-validator | 契约校验器（Hook Script） |

### B. 依赖关系图

```
create-cc-wf (Command)
    │
    ├─→ skill-builder (Agent) ──→ cc-wf-skill
    │
    ├─→ contract-builder (Agent) ──→ contract-desc
    │                              └→ contract-validator (可选)
    │
    ├─→ node-builder (Agent) ──→ cc-wf-node
    │
    ├─→ wf-entry-builder (Agent) ──→ cc-wf-entry
    │
    └─→ cc-settings-builder (Agent) ──→ .claude/settings.json
                                        └→ MCP/user config
```

### C. 待创建的依赖技能

| 技能 | 用途 | 优先级 |
|------|------|--------|
| contract-development | 契约设计最佳实践 | 高 |
| settings-development | settings.json 配置指南 | 中 |

### D. 参考资料

- `docs/01-workflow-abstraction.md` - 工作流抽象设计理念
- `docs/02-claude-code-capability.md` - Claude Code 核心能力
- `docs/03-claude-code-capability-mapping.md` - 能力映射关系
- `docs/04-workflow-mapping-methodology.md` - 映射方法论
- `skills/skill-development/` - Skill 开发指南
- `skills/command-development/` - Command 开发指南
- `skills/agent-development/` - Agent 开发指南
- `skills/hook-development/` - Hook 开发指南
- `docs/ref` - 最新的 Claude Code 官方文档，包括 command、skill、subagent、hook、setting 等使用说明
