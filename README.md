<div align="center">

# CC Workflow Factory

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-orange.svg)](https://claude.ai)

**English | [中文](README_CN.md)**

<p>
  <strong>Claude Code Workflow Factory</strong><br>
  <em>Transform workflow requirements into Claude Code implementations</em>
</p>

</div>

---

## Overview

CC Workflow Factory is a Claude Code plugin that transforms user workflow requirements into standardized Claude Code implementations. Through an interactive 7-phase process, it generates complete workflow components including Skills, Agents, Commands, and Hooks.

## Features

| Phase | Description |
|-------|-------------|
| 1. **Initialize** | Parse workflow description, create design document structure |
| 2. **Requirements** | Analyze requirements, identify workflow elements |
| 3. **Skills** | Design and create workflow skills |
| 4. **Nodes** | Design workflow nodes and their contracts |
| 5. **Contracts** | Generate contract schemas and validators |
| 6. **Flow** | Design flow orchestration, create entry command |
| 7. **Build & Verify** | Generate settings.json, validate all components |

## Installation

```bash
# Test with --plugin-dir parameter
claude --plugin-dir /path/to/cc-wf-factory/.claude-plugin

# Or copy to Claude Code plugins directory
cp -r cc-wf-factory/.claude-plugin ~/.claude/plugins/cc-wf-factory
```

## Usage

```bash
# Create a new workflow (interactive)
/create-cc-wf

# Create with description
/create-cc-wf I want to create a code review workflow

# Review an existing workflow
/review-cc-wf ./my-workflow --mode structure
/review-cc-wf ./my-workflow --mode function
/review-cc-wf ./my-workflow --mode runtime --log ./logs/
```

## Components

### Commands

| Name | Description |
|------|-------------|
| `create-cc-wf` | Interactive workflow creation wizard |
| `review-cc-wf` | Workflow validation (structure/function/runtime) |

### Agents (Builders)

| Name | Description |
|------|-------------|
| `skill-builder` | Creates Skill components from design documents |
| `contract-builder` | Creates Contract schemas and documentation |
| `node-builder` | Creates workflow Node agents |
| `wf-entry-builder` | Creates workflow entry Commands |
| `cc-settings-builder` | Generates settings.json configuration |

### Hook Templates

| Name | Description |
|------|-------------|
| `contract-validator.py` | Validates node inputs/outputs against contracts |
| `wf-state.py` | Manages workflow execution state |

## Generated Workflow Structure

```
target-project/
├── .claude/
│   ├── commands/
│   │   └── <workflow-name>.md      # Workflow entry command
│   ├── agents/
│   │   └── <node-name>.md          # Node agents
│   ├── skills/
│   │   └── <skill-name>/           # Workflow skills
│   ├── contracts/
│   │   ├── <contract>.yaml         # Contract schemas
│   │   └── mapping.yaml            # Node-contract mapping
│   └── hooks/
│       ├── contract-validator.py   # Contract validation
│       └── wf-state.py             # State management
├── .context/
│   └── state.md                    # Runtime state file
└── settings.json                   # Claude Code settings
```

## Workflow Abstraction

This plugin maps workflow concepts to Claude Code components:

| Workflow Concept | Claude Code Implementation |
|------------------|---------------------------|
| **Skill** | `.claude/skills/*/SKILL.md` |
| **Contract** | `.claude/contracts/*.yaml` + Hook |
| **Context** | `.context/` filesystem |
| **Node** | `.claude/agents/*.md` (Subagent) |
| **Flow** | `.claude/commands/*.md` (Command) |

## Design Documents

During workflow creation, design documents are generated in:

```
target-project/.wf-design/
├── skills.yaml       # Skill definitions
├── nodes.yaml        # Node definitions
├── contracts.yaml    # Contract definitions
└── flow.yaml         # Flow orchestration
```

## License

MIT
