# AI Workflow Design Principles (Complete Reference)

## Overview

This document defines design principles and core concepts for AI-driven workflows, applicable to automated task orchestration based on LLM Agents.

## Core Concepts

AI workflows consist of 4 core concepts:

```
┌─────────────────────────────────────────────────────────┐
│                      Workflow                           │
├─────────────────────────────────────────────────────────┤
│  1. Contract                                            │
│  2. Nodes                                               │
│  3. Flow                                                │
│  4. Context                                             │
└─────────────────────────────────────────────────────────┘
```

| Concept | Question It Answers |
|---------|---------------------|
| Contract | What does the data look like? How to validate? |
| Nodes | Who executes? What are inputs and outputs? |
| Flow | What order to execute? What to do on error? |
| Context | What environment info is needed at execution? |

---

## 1. Contract

Contracts define the specifications for all data structures in a workflow, key to ensuring AI output compliance.

### Components

| Component | Description | Required |
|-----------|-------------|----------|
| Schema | Data structure definition (fields, types, constraints) | ✅ Required |
| Validator | Validator implementation | ✅ Required |
| Examples | Sample data | Recommended |

### Design Principles

1. **Every data structure must have a corresponding validator** - AI output cannot be trusted, must be validated
2. **Schema and Validator coexist** - Schema for documentation and generation, Validator for runtime checks
3. **Contracts are interfaces between nodes** - Nodes are decoupled through contracts

### Contract File Structure

Contracts are centrally stored, nodes reference by name:

```
workflow/
├── contracts/
│   ├── contract-a.yaml
│   ├── contract-b.yaml
│   └── contract-c.yaml
└── validators/
    └── validators.py
```

### Contract Definition Format

**Contract File Field Description**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | ✅ | Contract name (stable identifier referenced by nodes) |
| description | string | Recommended | Contract purpose description |
| schema | object | ✅ | Data structure definition (JSON Schema recommended) |
| validator | string | ✅ | Runtime validator entry point, format `path/to/file.py::function_name` |
| examples | string[] | Recommended | List of example file paths (for prompt/testing/regression) |

**Contract File Example**

```yaml
name: ContractName
description: Contract purpose description
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
          const: "contract-type"    # Unique identifier for matching
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

### Contract Reference (Markdown Example)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| contract.name | string | ✅ | Contract name (e.g., `ContractA`) |
| contract.schema | string | ✅ | Schema file path (e.g., `schemas/contract-a.schema.json`) |
| contract.validator | string | ✅ | Validator entry point (e.g., `validators.py::validate_contract_a`) |
| contract.examples | string[] | Optional | List of example file paths |

### Node Input/Output Binding (Markdown Example)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| node.name | string | ✅ | Node name (e.g., `NodeX`) |
| node.input.contract | string | ✅ | Input contract name (e.g., `ContractA`) |
| node.input.source | string | ✅ | Input source path template (e.g., `$WORKDIR/intermediate/{entity}/input-a.md`) |
| node.output.contract | string | ✅ | Output contract name (e.g., `ContractB`) |
| node.output.target | string | ✅ | Output target path template (e.g., `$WORKDIR/{entity}/result.json`) |

### Runtime Binding

1. Before node execution: Parse `input.contract` reference, load validator, execute input validation
2. After node execution: Parse `output.contract` reference, load validator, execute output validation
3. Validation failure: Trigger error handling defined in Flow

### Validation Timing

| Timing | Trigger Condition | Validation Content | Failure Handling |
|--------|-------------------|-------------------|------------------|
| Input Validation | Before node execution | Input contract | Block execution |
| Output Validation | After node execution | Output contract | Trigger retry or error handling |

### Contract Uniqueness

To ensure SubagentStop can correctly match output to contract, each output contract must have a **unique identifier**:

```yaml
schema:
  properties:
    header:
      properties:
        type:
          const: "processor-output"    # Each contract's type must be unique
        agent:
          const: "data-processor"      # Corresponding Agent name
```

---

## 2. Nodes

Nodes are the execution units of a workflow, typically implemented by SubAgents in AI workflows.

### Components

| Component | Description | Required |
|-----------|-------------|----------|
| Input Contract | Reference to Contract definition | ✅ Required |
| Output Contract | Reference to Contract definition | ✅ Required |
| Implementation | SubAgent definition (prompt, skills, tools, model) | ✅ Required |

### Design Principles

1. **Single Responsibility** - Each node does only one thing
2. **Clear Input/Output** - Defined through contracts, no implicit conventions
3. **Independently Testable** - Given input, can independently verify output
4. **Idempotency** - Same input produces same output (as much as possible)

### Node Definition Format

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | ✅ | Node name (stable identifier) |
| description | string | Recommended | Node purpose description |
| input.contract | string | ✅ | Input contract name |
| input.source | string | ✅ | Input file path template (may contain placeholders like `{entity}`) |
| output.contract | string | ✅ | Output contract name |
| output.target | string | ✅ | Output file path template (may contain placeholders like `{entity}`) |
| implementation | object | ✅ | Node implementation configuration |
| implementation.type | string | ✅ | Implementation type (e.g., `subagent` / `script` / `service`) |
| implementation.agent | string | Optional | Agent/prompt definition entry (when `type=subagent`) |
| implementation.skills | string[] | Optional | Reusable skill set |
| implementation.tools | string[] | Optional | Allowed tool set |
| implementation.model | string | Optional | Model selection strategy (e.g., `inherit` / explicit specification) |

### Contract and Node Binding

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

### Runtime Validation Flow

```
1. Load node definition
2. Parse input.contract, find corresponding contract
3. Execute input validation (validator)
   - Pass → Continue
   - Fail → Block execution
4. Execute node (SubAgent)
5. Parse output.contract, find corresponding contract
6. Execute output validation (validator)
   - Pass → Complete
   - Fail → Trigger Flow error handling (retry/skip/terminate)
```

---

## 3. Skill

Skills are reusable knowledge and tool combinations shared by multiple nodes.

### SKILL.md Specification

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

- **frontmatter** (required): `name` and `description`
- **content** (flexible): Instructions, Examples, etc., organized as needed

### Skill Directory Structure

```
.claude/skills/{skill-name}/
├── SKILL.md                    # Main entry (required)
├── scripts/                    # Tool scripts (recommended)
├── references/                 # Domain knowledge (recommended)
└── ...                         # Other directories (extend as needed)
```

### Skill and Node Relationship

- Skills provide "knowledge" (guidance, reference documents, tool scripts)
- Nodes define "tasks" (input, output, execution logic)
- One Skill can be referenced by multiple Nodes
- Nodes bind Skills through `skills: [skill-name]`

---

## 4. Flow

Flow defines "how to execute" - the execution rules for nodes.

### Essence

Flow is an abstract concept describing a set of execution control rules. Specific workflows can choose appropriate control patterns based on requirements.

### Questions Flow Needs to Answer

| Dimension | Question | Possible Patterns |
|-----------|----------|-------------------|
| Order | In what order do nodes execute? | Sequential, concurrent, dependency graph |
| Repetition | When to repeat execution? | Loop, iteration, recursion |
| Branching | When to take different paths? | Conditional branch, pattern matching |
| Error | What to do on failure? | Retry, skip, rollback, fallback |

### Design Principles

1. **Flow is abstract** - Not limited to specific orchestration patterns, defined by each workflow
2. **Error handling is part of Flow** - Not a separate concept
3. **Explicit over implicit** - Execution rules should be clearly declared
4. **Observable** - Able to track execution state

### Flow DSL Syntax

| Symbol | Meaning | Example | Description |
|--------|---------|---------|-------------|
| `>>` | Sequential dependency | `a >> b >> c` | a completes, then b, then c |
| `[a, b]` | Parallel group | `x >> [a, b] >> y` | a and b execute in parallel, y waits for all |
| `?label` | Conditional branch | `a ?ok >> b` | Execute b when a output satisfies ok condition |
| `* $var` | Loop iteration | `a * $items` | Execute a for each item in $items |
| `* $var[n]` | Parallel loop | `a * $items[3]` | Parallel iteration with degree 3 |
| `START` | Entry point | `START >> a` | Workflow entry |
| `END` | Exit point | `a >> END` | Workflow exit |

---

## 5. Context

Context defines environment information and shared state during workflow execution.

### Components

| Component | Description | Required |
|-----------|-------------|----------|
| Environment Variables | Execution environment parameters | ✅ Required |
| Shared State | State passed between nodes | Optional |
| Storage Layout | Intermediate artifact storage locations | ✅ Required |

### Design Principles

1. **Explicit Declaration** - All context variables must be declared at workflow entry
2. **Prefer Immutability** - Environment variables should not change during execution
3. **Unified Storage Layout** - All nodes follow the same directory structure

### Context Definition Detailed Fields

**env (Environment Variables, Workflow Input)**

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| WORKDIR | string | ✅ | Working directory |
| WORKFLOW_NAME | string | ✅ | Workflow name |
| SOURCE_DIR | string | Optional | Source/data directory |
| OUTPUT_DIR | string | Optional | Output directory |

**layout (Storage Layout)**

| Field | Type | Required | Description | Example (Template) |
|-------|------|----------|-------------|-------------------|
| intermediate | string | ✅ | Intermediate artifact directory | `$WORKDIR/.context/` |
| final | string | ✅ | Final artifact directory | `$WORKDIR/output/` |
| temp | string | ✅ | Temporary directory | `$WORKDIR/.temp/` |

**state (Shared State, Generated at Runtime)**

| Key | Type | Required | Description | populated_by |
|-----|------|----------|-------------|--------------|
| collected_data | any | Optional | Data produced by collection phase | `collector` |
| analysis_result | any | Optional | Results produced by analysis phase | `analyzer` |

---

## Concept Relationship Diagram

```
                    ┌─────────────┐
                    │   Context   │
                    │  (env vars) │
                    └──────┬──────┘
                           │ Provides execution environment
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
   │ (input) │    │(middle) │    │(output) │
   └─────────┘    └─────────┘    └─────────┘
```

### Core Relationships

- **Skill** provides reusable knowledge (prompt + tools)
- **Node** references Skill, defines specific tasks
- **Contract** is the interface between Nodes
- **Flow** orchestrates Node execution
- **Context** provides environment for execution

---

## Special Considerations for AI Workflows

### Differences from Traditional Workflows

| Aspect | Traditional Workflow | AI Workflow |
|--------|---------------------|-------------|
| Output Determinism | Deterministic | Non-deterministic |
| Validation Necessity | Optional | Required |
| Error Types | Mainly exceptions | Format errors, semantic errors, hallucinations |
| Retry Strategy | Simple retry | Retry with feedback |

### AI-Specific Design Points

1. **Validators are mandatory** - Cannot trust AI output
2. **Retry with feedback** - Pass validation errors as context back to Agent
3. **Example-driven** - Provide clear output examples in prompts
4. **Progressive refinement** - Split complex tasks into multiple simple nodes

### Relationship Between Prompt and Contract

```
Contract (Schema)
    │
    ├──▶ Generate output format instructions in Prompt
    │
    ├──▶ Generate Examples
    │
    └──▶ Generate Validator
```

---

## Document Organization Recommendations

```
workflow/
├── contracts/           # Contract definitions
│   ├── contract-a.yaml
│   ├── contract-b.yaml
│   ├── contract-c.yaml
│   └── ...
├── nodes/               # Node definitions
│   ├── node-a.md
│   ├── node-b.md
│   └── ...
├── flow.yaml            # Flow orchestration
├── context.yaml         # Context definition
└── validators/          # Validator implementations
    ├── __init__.py
    ├── contract_a.py
    ├── contract_c.py
    └── ...
```

---

## Summary

| Concept | Responsibility | AI-Specific Considerations |
|---------|---------------|---------------------------|
| **Contract** | Data specification + validation | Validators must exist, multi-timing validation |
| **Nodes** | Execution units | SubAgent + Skill implementation |
| **Flow** | Execution control (order, branching, error handling) | Abstract definition, retry with feedback |
| **Context** | Environment + state | Unified storage layout |

### Design Principles

- **Contract First**: Define data specifications first, then implement nodes
- **Validators Required**: Every contract has a validator, clear validation timing
- **Flow is Abstract**: Not limited to specific patterns, choose as needed
- **Error handling is part of Flow**
- **Explicit over Implicit**
