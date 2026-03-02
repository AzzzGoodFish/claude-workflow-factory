# 工作流映射方法论

## 概述

本文档提供将用户工作流需求（抽象概念）映射为 Claude Code 具体实现的方法论，包括映射原则、流程、规范和参考资料。

## 目录

1. [映射方法论](#1-映射方法论)
2. [技能映射](#2-技能映射)
3. [契约映射](#3-契约映射)
4. [节点映射](#4-节点映射)
5. [工作流 DSL 映射](#5-工作流-dsl-映射)
6. [映射实施指南](#6-映射实施指南)
7. [工作流状态治理](#7-工作流状态治理)

---

## 1. 映射方法论

### 1.1 映射原则

**单一职责原则**
- 一个 Skill 专注一个领域
- 一个 Subagent 执行一个节点任务
- command 处理输入输出，负责解析 flow，执行调度

**契约优先原则**
- 先定义数据规范，再设计节点
- 契约可选，并非所有节点需要绑定契约
- 通过 Hook 强制执行契约校验

### 1.2 映射流程

```
用户需求
    ↓
需求分析（识别：目标、节点、技能、契约、流程）
    ↓
要素映射（按顺序）
    ├─→ 技能映射 → cc-wf-skill (Skill)
    ├─→ 契约映射 → contract-desc(YMAL/Json/Pydantic Schema) + contract-validator (Hook Script)
    ├─→ 节点映射 → cc-wf-node (Subagent)
    └─→ 流程映射 → cc-wf-entry (Command)
    ↓
实现验证（测试工作流执行）
    ↓
迭代优化
```

### 1.3 映射依赖关系

**依赖说明**：
- **契约 → 节点**：节点需要引用契约来约束输入输出
- **节点 → 流程**：流程需要知道有哪些节点可调用
- **技能 → 节点**：节点需要绑定技能

**并行映射**：
- 多个独立技能可并行映射
- 多个独立契约可并行映射
- 多个无依赖的节点可并行映射

### 1.4 cc-wf-factory 总体需求

1. 开发一个入口 command：create-cc-wf，用于交互式与用户确认需求，必须参考资料 skills/command-development 保证设计规范
2. 开发 skill-builder agent，绑定 skills/skill-development 技能，用于执行用户技能需求到 cc-wf-skill 的映射
3. 开发标准化的 validator 脚本 contract-validator.py，该脚本全局唯一，在 PostToolUse(Task)、PostToolUse(Task)、Stop 时执行，根据 hook_event_name 参数判断校验类型，通过解析 hook input 得出当前节点类型，匹配工作流的契约规范文件和校验脚本然后执行校验，PostToolUse 检查节点输入，PostToolUse 检查节点输出，Stop 检查工作流输出
4. 开发 contract-builder agent，绑定 skills/contract-development 技能，用于执行用户契约需求到 contract-desc + contract-validator 的映射
5. 开发 node-builder agent，绑定 skills/agent-development 技能，用于执行用户工作流节点需求到 cc-wf-node 的映射
6. 开发 wf-entry-builder agent，绑定 skills/command-development 技能，用于执行用户工作流 DSL 到 cc-wf-entry 的映射
7. 开发一个 cc-settings-builder agent，绑定 skills/settings-develop 技能，用于将用户提供的 mcp、hook，cc-wf 的 hook，配置为一份标准化的 settings.json，参考资料：docs/ref-claude-code-settings.md
8. 开发一个工作流状态治理 hook 脚本 wf-state.py，在 UserPromptSubmit、PostToolUse(Task)、PostToolUse(Task)、Stop 时执行，通过解析 hook input 识别工作流是否启动、当前执行节点等信息，自动维护工作目录下的工作流执行状态文件
9. 开发一个 review command：review-cc-wf，用于校验 cc-wf-skill、contract-desc、contract-validator、cc-wf-node、cc-wf-entry 是否符合基本规范，用于校验用户 cc-wf 是否符合用户基本需求，用于根据用户工作流执行效果反馈，去定位 cc-wf 中存在的问题

---

## 2. 技能映射

### 2.1 映射目标
- 产物：cc-wf-skill (Skill)
- 定义：封装领域知识为可复用模块

### 2.2 映射方法
- 输入：技能名称、领域知识、使用场景、用户资料
- 输出：SKILL.md 文件、可选捆绑资源
- 执行步骤：分析、调研、确认、创建、测试

### 2.3 映射规范
- Frontmatter 规范
- SKILL.md 正文规范
- 捆绑资源组织规范

### 2.4 参考资料
- `@skills/skill-development`
- Claude Code 官方文档

### 2.5 cc-wf-factory 需求

- 对应 1.4-2

---

## 3. 契约映射

### 3.1 映射目标
- 产物：contract-desc（必需）、contract-validator Hook（可选）
- 定义：将数据规范和验证规则转换为可执行契约

### 3.2 映射方法
- 输入：数据结构定义、验证规则、校验方式、失败处理策略
- 输出：契约文档、Hook 配置（可选）、校验脚本（可选）
- 执行步骤：分析需求、设计文档、确定校验方式、实现校验器、配置 Hook、测试

### 3.3 映射规范
- 契约文档规范
- Hook 配置规范
- 校验器实现规范

### 3.4 参考资料
- `@skills/hook-development`
- `@skills/contract-development`（待创建）

### 3.5 cc-wf-factory 需求

- 对应 1.4-3 和 1.4-4


---

## 4. 节点映射

### 4.1 映射目标
- 产物：cc-wf-node (Subagent)
- 定义：将工作流节点转换为独立执行的 Subagent

### 4.2 映射方法
- 输入：节点名称和职责、绑定技能、输入输出来源、契约引用、工具集
- 输出：Subagent 文件
- 执行步骤：分析职责、确定技能、确定契约、设计 Frontmatter、编写提示词、测试

### 4.3 映射规范
- Frontmatter 规范
- 系统提示词模板

### 4.4 参考资料
- `@skills/agent-development`
- `templates/workflow-node.md`（待创建）

### 4.5 cc-wf-factory 需求

- 对应 1.4-5

---

## 5. 工作流 DSL 映射

### 5.1 映射目标
- 产物：cc-wf-entry (Command)
- 定义：将工作流定义转换为可执行的 Command，作为入口和主调度器

### 5.2 映射方法
- 输入：工作流名称和目标、参数、节点列表、执行逻辑、输入输出
- 输出：Command 文件
- 执行步骤：设计 Frontmatter、转换为 DSL、嵌入解释器、编写调度逻辑、测试

### 5.3 映射规范
- Frontmatter 规范
- 工作流 DSL 标准形式
- 工作流 DSL 解释器模板

### 5.4 参考资料
- `@skills/command-development`
- `templates/workflow-dsl-interpreter.md`（待创建）

### 5.5 cc-wf-factory 需求

- 对应 1.4-6

---

## 6. 映射实施指南

### 6.1 映射顺序建议
- 推荐顺序：技能 → 契约 → 节点 → 流程
- 原因：依赖关系决定顺序
- 并行优化：独立要素可并行映射

### 6.2 映射检查清单
- 技能映射检查
- 契约映射检查
- 节点映射检查
- 流程映射检查

---

## 7. 工作流状态治理

### 7.1 概述
- 定义和目标
- 实现方式（Hook）
- 特点（自动化、透明、统一）

### 7.2 状态模型
- 工作流状态
- 节点状态
- 状态数据结构

### 7.3 Hook 设计
- SessionStart Hook
- PreToolUse Hook (Task)
- PostToolUse Hook (Task)
- Stop Hook

### 7.4 状态存储
- 存储位置和结构
- 文件格式

### 7.5 核心能力
- 状态查询
- 断点续传
- 异常恢复
- 执行追溯

### 7.6 实现清单
- 必需的 Hook
- 必需的脚本
- 必需的 Command

### 7.7 配置选项
- 全局配置
- 工作流级别配置

---

## 附录

### A. 术语对照表

| 抽象概念 | Claude Code 实现 | 术语 |
|---------|-----------------|------|
| 工作流 | - | cc-wf |
| 技能 | Skill | cc-wf-skill |
| 契约（描述） | Markdown 文档、Yaml/Json Schema | contract-desc |
| 契约（校验） | Hook(Pydantic、python Script) | contract-validator |
| 节点 | Subagent | cc-wf-node |
| 流程入口 | Command | cc-wf-entry |
| 上下文 | 文件系统 | context |

### B. cc-wf 文件组织结构

```
workflow-project/
├── commands/
│   └── workflow-name.md          # cc-wf-entry
├── agents/
│   ├── node1.md                  # cc-wf-node
│   └── node2.md                  # cc-wf-node
├── skills/
│   ├── skill1/
│   │   └── SKILL.md              # cc-wf-skill
│   └── skill2/
│       └── SKILL.md              # cc-wf-skill
├── contracts/
│   ├── input-contract.md         # contract-desc
│   └── output-contract.md        # contract-desc
├── hooks/
│   ├── wf-state.py               # 全局唯一的工作流状态治理脚本
│   ├── contract-validator.py     # 全局唯一的契约检查脚本
│   ├── node-input-validator.py   # -> contract-validator.py 
│   ├── node-output-validator.py  # -> contract-validator.py 
│   ├── wf-output-validator.py    # -> contract-validator.py 
│   ├── node1-input-schema.yaml   # contract-schema
|   ├── node2-validator.py        # contract-validator
│   └── node2-output.yaml         # contract-schema
└── settings.json                 # 配置了 mcp、hook 等
```

### B. cc-wf 运行时结构
work-dir/                # 工作目录
├──.claude/              # cc-wf
│  ├── commands/  
│  ├── agents/
│  ├── skills/
│  ├── contracts/
│  ├── hooks/
│  └── settings.json
├──.context              # 中间产物文件
│  ├──node1/
│  ├──node2/
│  └──state.yaml         # 通过 hook 脚本自动维护的节点状态
└── ...                  # 工作区文件