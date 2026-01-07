<div align="center">

# CC Workflow Factory

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-orange.svg)](https://claude.ai)

**English | [中文](README_CN.md)**

<p>
  <strong>Interactive workflow building wizard for Claude Code</strong><br>
  <em>Create standardized AI workflows following best design principles</em>
</p>

</div>

---

## 🌟 Overview

CC Workflow Factory is an interactive wizard plugin for Claude Code that guides users through creating standardized, well-structured AI workflows. Through multi-turn conversations, it helps you design robust workflows with proper contracts, nodes, and flow orchestration.

## ✨ Features

| Phase | Description |
|-------|-------------|
| 📋 **Requirement Analysis** | Analyze reference materials or conduct research |
| 🔧 **Node Design** | Identify and define workflow nodes |
| 🔀 **Flow Orchestration** | Design execution order, parallelism, branching, error handling |
| 📝 **Contract Definition** | Design data structures and validation rules |
| 🚀 **Workflow Generation** | Output complete workflow directory structure |

## 📦 Installation

```bash
# Test with --plugin-dir parameter
claude --plugin-dir /path/to/cc-wf-factory

# Or copy to Claude Code plugins directory
cp -r cc-wf-factory ~/.claude/plugins/
```

## 🚀 Usage

```bash
# Start workflow factory with a goal
/cc-wf-factory I want to create a code review workflow

# Or start without parameters
/cc-wf-factory
```

## 📊 Interactive Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Iterative Workflow Building                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. User describes goal / provides reference materials               │
│                                                                      │
│  2. Analyze materials (wf-resource-analyzer)                         │
│     or research suggestions (wf-researcher)                          │
│                                                                      │
│  3. Confirm / modify node design                                     │
│                                                                      │
│  4. Design flow orchestration (wf-flow-designer)                     │
│                                                                      │
│  5. Design data contracts (wf-contract-designer)                     │
│                                                                      │
│  6. Generate workflow (wf-generator)                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🧩 Components

### Commands

| Name | Description |
|------|-------------|
| `cc-wf-factory` | Workflow building wizard entry point |

### Skills

| Name | Description |
|------|-------------|
| `workflow-design` | Workflow design knowledge (Contract, Node, Flow, Context) |
| `resource-analysis` | Material analysis methodology for extracting workflow design elements |

### Agents

| Name | Description |
|------|-------------|
| `wf-resource-analyzer` | Analyzes user-provided reference materials |
| `wf-researcher` | Workflow research, provides solution recommendations |
| `wf-contract-designer` | Designs data contracts |
| `wf-flow-designer` | Designs flow orchestration |
| `wf-generator` | Generates complete workflow |

### Hooks

| Event | Description |
|-------|-------------|
| `UserPromptSubmit` | Analyzes user input type, provides contextual hints |

## 📁 Generated Workflow Structure

```
.claude/
├── commands/
│   └── <workflow-name>.md           # Workflow entry point
├── agents/
│   └── <node-name>.md               # Node SubAgents
├── hooks/
│   └── [Hook configurations]
└── workflows/
    └── <workflow-name>/
        ├── flow.yaml                # Flow DSL
        ├── contracts/               # Contract definitions
        └── validators/              # Python validators
```

## 📐 Design Documents

During workflow design, intermediate documents are saved in:

```
$WORKDIR/.wf-factory/
├── design/
│   ├── overview.md         # Workflow overview
│   ├── nodes.md            # Node definitions
│   ├── flow.md             # Flow orchestration
│   ├── contracts.md        # Contract definitions
│   └── validators.md       # Validator specifications
└── resources/              # User reference materials
```

## 🎯 Design Principles

This plugin is built on the following design principles:

| Principle | Description |
|-----------|-------------|
| **Contract** | Data structure specifications and validation |
| **Nodes** | Execution units implemented by SubAgents |
| **Flow** | Execution control rules |
| **Context** | Environment information and shared state |

See reference documents in `skills/workflow-design/references/`.

## 📖 Flow DSL Syntax

```yaml
# Sequential execution
START >> step-a >> step-b >> END

# Parallel execution
START >> [collect-a, collect-b] >> merge >> END

# Conditional branching
analyze ?issues >> fix >> END
analyze ?clean >> approve >> END

# Loop iteration
processor * $items[3] >> merge >> END
```

## 📄 License

MIT
