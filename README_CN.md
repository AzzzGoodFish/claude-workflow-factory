<div align="center">

# CC Workflow Factory

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-orange.svg)](https://claude.ai)

**[English](README.md) | 中文**

<p>
  <strong>Claude Code 工作流工厂</strong><br>
  <em>将工作流需求转换为 Claude Code 实现</em>
</p>

</div>

---

## 概述

CC Workflow Factory 是一个 Claude Code 插件，将用户的工作流需求转换为标准化的 Claude Code 实现。通过交互式的 7 阶段流程，生成完整的工作流组件，包括 Skills、Agents、Commands 和 Hooks。

## 功能特性

| 阶段 | 说明 |
|------|------|
| 1. **初始化** | 解析工作流描述，创建设计文档结构 |
| 2. **需求分析** | 分析需求，识别工作流元素 |
| 3. **技能设计** | 设计并创建工作流技能 |
| 4. **节点设计** | 设计工作流节点及其契约 |
| 5. **契约生成** | 生成契约 Schema 和校验器 |
| 6. **流程编排** | 设计流程编排，创建入口命令 |
| 7. **构建验证** | 生成 settings.json，验证所有组件 |

## 安装

```bash
# 使用 --plugin-dir 参数测试
claude --plugin-dir /path/to/cc-wf-factory/.claude-plugin

# 或复制到 Claude Code 插件目录
cp -r cc-wf-factory/.claude-plugin ~/.claude/plugins/cc-wf-factory
```

## 使用方法

```bash
# 创建新工作流（交互式）
/create-cc-wf

# 带描述创建
/create-cc-wf 我想创建一个代码审查工作流

# 审查现有工作流
/review-cc-wf ./my-workflow --mode structure
/review-cc-wf ./my-workflow --mode function
/review-cc-wf ./my-workflow --mode runtime --log ./logs/
```

## 组件

### 命令 (Commands)

| 名称 | 说明 |
|------|------|
| `create-cc-wf` | 交互式工作流创建向导 |
| `review-cc-wf` | 工作流验证（结构/功能/运行时） |

### 代理 (Agents/Builders)

| 名称 | 说明 |
|------|------|
| `skill-builder` | 根据设计文档创建 Skill 组件 |
| `contract-builder` | 创建契约 Schema 和文档 |
| `node-builder` | 创建工作流节点 Agent |
| `wf-entry-builder` | 创建工作流入口 Command |
| `cc-settings-builder` | 生成 settings.json 配置 |

### Hook 模板

| 名称 | 说明 |
|------|------|
| `contract-validator.py` | 校验节点输入/输出是否符合契约 |
| `wf-state.py` | 管理工作流执行状态 |

## 生成的工作流结构

```
target-project/
├── .claude/
│   ├── commands/
│   │   └── <workflow-name>.md      # 工作流入口命令
│   ├── agents/
│   │   └── <node-name>.md          # 节点 Agent
│   ├── skills/
│   │   └── <skill-name>/           # 工作流技能
│   ├── contracts/
│   │   ├── <contract>.yaml         # 契约 Schema
│   │   └── mapping.yaml            # 节点-契约映射
│   └── hooks/
│       ├── contract-validator.py   # 契约校验
│       └── wf-state.py             # 状态管理
├── .context/
│   └── state.md                    # 运行时状态文件
└── settings.json                   # Claude Code 配置
```

## 工作流抽象

本插件将工作流概念映射到 Claude Code 组件：

| 工作流概念 | Claude Code 实现 |
|-----------|-----------------|
| **Skill (技能)** | `.claude/skills/*/SKILL.md` |
| **Contract (契约)** | `.claude/contracts/*.yaml` + Hook |
| **Context (上下文)** | `.context/` 文件系统 |
| **Node (节点)** | `.claude/agents/*.md` (Subagent) |
| **Flow (流程)** | `.claude/commands/*.md` (Command) |

## 设计文档

工作流创建过程中，设计文档生成在：

```
target-project/.wf-design/
├── skills.yaml       # 技能定义
├── nodes.yaml        # 节点定义
├── contracts.yaml    # 契约定义
└── flow.yaml         # 流程编排
```

## 许可证

MIT
