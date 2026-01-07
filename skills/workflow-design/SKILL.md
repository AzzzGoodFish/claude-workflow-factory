---
name: workflow-design
description: This skill should be used when the user asks about "workflow design", "Contract definition", "Node design", "Flow DSL", "SubAgent workflow", "workflow validation", or needs guidance on AI workflow architecture, data contracts, node orchestration, or Claude Code workflow implementation patterns.
---

# Workflow Design Knowledge

Provides guidance for designing AI-driven workflows based on the 4 core concepts: Contract, Nodes, Flow, and Context.

## Core Concepts Overview

AI workflows consist of 4 fundamental concepts:

| Concept | Question Answered | Claude Code Mapping |
|---------|-------------------|---------------------|
| **Contract** | What does data look like? How to validate? | YAML Schema + Python Validator |
| **Nodes** | Who executes? What are inputs/outputs? | SubAgent (`.claude/agents/*.md`) |
| **Flow** | In what order? What if errors? | DSL (`flow.yaml`) |
| **Context** | What environment info needed? | Environment variables + context files |

## Contract Design

Contracts define data structure specifications and validation rules.

### Contract Components

| Component | Purpose | Required |
|-----------|---------|----------|
| Schema | Data structure definition (JSON Schema) | Yes |
| Validator | Runtime validation function | Yes |
| Examples | Sample data for testing/prompts | Recommended |

### Contract File Format

```yaml
name: ContractName
description: Contract purpose
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

### Validation Timing

| Timing | Trigger | Content | On Failure |
|--------|---------|---------|------------|
| Input validation | Before node execution | Input contract | Block execution |
| Output validation | After node execution | Output contract | Trigger retry or error handling |

## Node Design

Nodes are workflow execution units, implemented as SubAgents in Claude Code.

### Node Definition Format

```markdown
---
name: node-name
description: Node purpose
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

### Design Principles

1. **Single Responsibility** - Each node does one thing
2. **Explicit I/O** - Define through contracts, no implicit dependencies
3. **Independently Testable** - Validate output given input
4. **Idempotent** - Same input produces same output (when possible)

### Output Format

All SubAgent outputs use Markdown with frontmatter:

```markdown
---
type: contract-type
agent: agent-name
timestamp: 2026-01-07T10:00:00Z
---

## Content

...
```

## Flow Design

Flow defines execution control rules using a concise DSL.

### DSL Syntax

| Symbol | Meaning | Example |
|--------|---------|---------|
| `>>` | Sequential | `a >> b >> c` |
| `[a, b]` | Parallel group | `x >> [a, b] >> y` |
| `?label` | Conditional branch | `a ?ok >> b` |
| `* $var` | Loop iteration | `a * $items` |
| `* $var[n]` | Parallel loop | `a * $items[3]` |
| `START` | Entry point | `START >> a` |
| `END` | Exit point | `a >> END` |

### Flow File Format

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

### Common Patterns

**Sequential execution:**
```yaml
flow: |
  START >> step-a >> step-b >> step-c >> END
```

**Parallel execution:**
```yaml
flow: |
  START >> [collect-a, collect-b] >> merge >> END
```

**Conditional branching:**
```yaml
flow: |
  START >> analyze >> END
  analyze ?issues >> fix >> END
  analyze ?clean >> approve >> END
```

**Loop iteration:**
```yaml
flow: |
  START >> processor * $files[3] >> merge >> END
```

## Context Design

Context defines environment information and shared state.

### Context Components

| Component | Purpose | Required |
|-----------|---------|----------|
| Environment variables | Execution parameters | Yes |
| Shared state | State passed between nodes | Optional |
| Storage layout | Intermediate artifact locations | Yes |

### Storage Layout Convention

```
$WORKDIR/
└── .context/                # Intermediate outputs
    ├── node-a.md
    ├── node-b.md
    └── ...
```

## AI Workflow Special Considerations

### Differences from Traditional Workflows

| Aspect | Traditional | AI Workflow |
|--------|-------------|-------------|
| Output determinism | Deterministic | Non-deterministic |
| Validation necessity | Optional | Required |
| Error types | Exceptions | Format errors, semantic errors, hallucinations |
| Retry strategy | Simple retry | Retry with feedback |

### AI-Specific Design Points

1. **Validators are mandatory** - Never trust AI output
2. **Retry with feedback** - Pass validation errors back to Agent
3. **Example-driven** - Provide clear output examples in prompts
4. **Progressive refinement** - Split complex tasks into simple nodes

## Additional Resources

### Reference Files

For detailed patterns and syntax, consult:
- **`references/ai-workflow-principles.md`** - Complete design principles
- **`references/cc-workflow-mapping.md`** - Claude Code implementation details
- **`references/flow-dsl-syntax.md`** - Complete Flow DSL reference

### Quick Decision Guide

**When to split nodes:**
- Task requires multiple distinct skills
- Output needs different validation rules
- Want parallel execution capability

**When to use contracts:**
- Data flows between nodes
- Need to validate AI output
- Want consistent data structure

**When to use conditional flow:**
- Different paths based on output
- Error handling needed
- Quality gates required
