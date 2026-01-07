# Claude Code Workflow Design Guide

> This document defines how to map AI workflow design principles to Claude Code execution mechanisms.

## 1. Overview

### 1.1 Design Goals

Map the 4 core concepts from `ai-workflow-design-principles.md` to Claude Code:

| Workflow Concept | Claude Code Mechanism | Status |
|-----------------|----------------------|--------|
| **Contract** | YAML Schema + Python Validator | ✅ Confirmed |
| **Nodes** | SubAgent (`.claude/agents/*.md`) | ✅ Confirmed |
| **Flow** | Concise DSL (`flow.yaml`) | ✅ Confirmed |
| **Context** | Environment Variables + Context Files | ✅ Confirmed |

### 1.2 Core Principles

1. **Command is the workflow entry and executor**: Defines the entire workflow's Flow, Input, Output
2. **SubAgent is the node executor**: Optionally binds Skills, uses contracts to standardize input/output
3. **SubAgent output format unified as Markdown**: Stored in `$WORKDIR/.context/`, facilitating inter-Agent sharing
4. **Hooks implement automatic validation**: Leverages Claude Code native Hook mechanism to validate input/output

---

## 2. Hook Validation System

### 2.1 Hook Types and Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                     Workflow Execution Lifecycle                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  UserPromptSubmit ──────────────────────────────────────────┐   │
│    • Validate overall workflow input                         │   │
│    • Check required environment variables                    │   │
│    • Initialize working directory                            │   │
│                                                              ▼   │
│  PreToolUse (matcher: "Task") ──────────────────────────────┐   │
│    • Identify SubAgent about to execute                     │   │
│    • Extract input contract from Agent definition           │   │
│    • Validate input file against contract                   │   │
│    • Validation failure → continue: false, block execution  │   │
│                                                              ▼   │
│  SubagentStop ──────────────────────────────────────────────┐   │
│    • Iterate all Agent output contracts, match current output│   │
│    • Match success → write to target path (.context/*.md)   │   │
│    • Match failure → continue: false, reject exit           │   │
│                                                              ▼   │
│  Stop ──────────────────────────────────────────────────────    │
│    • Validate overall workflow output                           │
│    • Check all required nodes completed                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Hook Configuration

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

## 3. SubAgent Definition

### 3.1 Definition Format

SubAgent definition files are located at `.claude/agents/*.md`, using extended frontmatter format:

```markdown
---
name: <agent-name>
description: <agent-description>
tools: <Tool1, Tool2, ...>
model: inherit
skills: <skill-name>              # Optional, task-related enhancement

input:
  contract: <ContractName>        # Input contract name
  context:                        # Context file list (files Agent needs to read)
    - "$WORKDIR/.context/file1.md"
    - "$WORKDIR/.context/file2.md"

output:
  contract: <ContractName>        # Output contract name
  target: "$WORKDIR/.context/<agent-name>.md"  # Output target path
---

<Agent System Prompt>
```

### 3.2 Field Description

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Agent unique identifier |
| `description` | string | ✅ | Agent function description |
| `tools` | string | ✅ | Available tool list |
| `model` | string | ❌ | Model selection (default inherit) |
| `skills` | string | ❌ | Bound Skill name |
| `input.contract` | string | ✅ | Input contract name |
| `input.context` | string[] | ❌ | Context file path list |
| `output.contract` | string | ✅ | Output contract name |
| `output.target` | string | ✅ | Output file target path |

### 3.3 Example

````markdown
---
name: data-processor
description: Process collected data and generate analysis results
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

You are a data processor.

## Task

1. Read collection results from context files
2. Analyze and process data
3. Generate results in output format

## Context

Read from the following files:
- `$WORKDIR/.context/collector-a.md`
- `$WORKDIR/.context/collector-b.md`

## Output Format

Must use the following format:

```markdown
---
type: processor-output
agent: data-processor
timestamp: <ISO8601>
---

## Processing Results

...
```
````

---

## 4. Contract Definition

### 4.1 Contract File Format

Contracts are defined in YAML format, containing JSON Schema and validator references:

```yaml
# .claude/workflows/<workflow-name>/contracts/<contract-name>.yaml

name: ProcessorOutput
description: Data processor output contract
version: "1.0"

# JSON Schema definition
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
          const: "processor-output"    # Unique identifier for matching
        agent:
          const: "data-processor"
        timestamp:
          type: string
          format: date-time
    content:
      type: string
      minLength: 1

# Python validator entry point
validator: validators/processor_output.py::validate

# Example data
examples:
  - path: examples/processor-output-sample.md
```

### 4.2 Contract Uniqueness

To ensure SubagentStop can correctly match output to contract, each output contract must have a **unique identifier**:

```yaml
# Define unique identifier in schema
schema:
  properties:
    header:
      properties:
        type:
          const: "processor-output"    # Each contract's type must be unique
        agent:
          const: "data-processor"      # Corresponding Agent name
```

Corresponding Markdown output must contain frontmatter:

```markdown
---
type: processor-output
agent: data-processor
timestamp: 2026-01-06T10:00:00Z
---

## Processing Results
...
```

### 4.3 Validator Implementation

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
    Validate output data

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

## 5. Output Format Specification

### 5.1 Markdown Output Structure

All SubAgent outputs use unified Markdown format, must contain frontmatter:

```markdown
---
type: <contract-type>           # Contract type identifier (required)
agent: <agent-name>             # Agent name (required)
timestamp: <ISO8601>            # Timestamp (recommended)
---

## Title

Body content...
```

### 5.2 Storage Location

```
$WORKDIR/
└── .context/                   # Intermediate output directory
    ├── collector-a.md          # Each Agent's output
    ├── collector-b.md
    ├── processor.md
    └── finalizer.md
```

### 5.3 SubagentStop Matching Flow

```python
def match_output_to_agent(output: str) -> Optional[AgentDef]:
    """
    Iterate all Agent output contracts to find match

    1. Parse output frontmatter
    2. Iterate .claude/agents/*.md
    3. For each Agent's output.contract, check if matches
    4. Return matching Agent definition, or None
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

## 6. Directory Structure

```
.claude/
├── settings.json                    # Hook configuration
│
├── commands/
│   └── <workflow-name>.md           # Workflow entry Command
│
├── agents/
│   ├── collector-a.md               # SubAgent definitions
│   ├── collector-b.md
│   ├── processor.md
│   └── finalizer.md
│
├── skills/
│   └── <skill-name>/                # Skills for specific tasks (optional)
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
        ├── flow.yaml                # Flow definition (concise DSL)
        ├── contracts/               # Contract definitions
        │   ├── workflow-input.yaml
        │   ├── collector-a-output.yaml
        │   ├── processor-output.yaml
        │   └── workflow-output.yaml
        ├── validators/              # Python validators
        │   ├── __init__.py
        │   └── validators.py
        └── templates/               # Output templates (optional)
            ├── collector-output.md
            └── processor-output.md
```

---

## 7. Skill and Contract Relationship

### 7.1 Responsibility Distinction

| Concept | Responsibility | Relationship with Agent |
|---------|---------------|------------------------|
| **Skill** | Task enhancement, provides domain knowledge, reference docs, tool scripts | Optional binding, assists in completing tasks |
| **Contract** | Data specification, defines input/output structure and validation rules | Required binding, defines interface |

### 7.2 Skill Structure

```
.claude/skills/<skill-name>/
├── SKILL.md                    # Skill entry
├── references/                 # Domain knowledge (optional)
│   └── domain-guide.md
└── scripts/                    # Tool scripts (optional)
    └── utils.py
```

### 7.3 Usage

- Agent references Skill through `skills: <skill-name>`
- Knowledge provided by Skill is injected into Agent's context
- Skills have no direct relationship with contracts, contracts are declared in Agent definition

---

## 8. Flow Expression Specification

> For detailed Flow DSL syntax, see `flow-dsl-syntax.md`.

### 8.1 Concise DSL Syntax

Flow uses concise DSL syntax, stored in `flow.yaml` file:

```yaml
# .claude/workflows/<workflow-name>/flow.yaml
name: my-workflow
version: "1.0"

# State definition (optional)
state:
  items: []
  result: null

# Flow definition
flow: |
  START >> fetch-data >> [validate, transform] >> process >> END
  process ?success >> finalize >> END
  process ?retry >> process
  process ?fail >> error-handler >> END
  batch-processor * $items[3] >> merge >> END

# Condition definitions (for complex conditions)
conditions:
  process:
    success: "output.status == 'ok'"
    retry: "output.retry_count < 3"
    fail: "output.status == 'error'"

# Execution configuration
execution:
  max_parallel: 3
  timeout: 3600
```

### 8.2 Syntax Symbols

| Symbol | Meaning | Example | Description |
|--------|---------|---------|-------------|
| `>>` | Sequential dependency | `a >> b >> c` | a completes, then b, then c |
| `[a, b]` | Parallel group | `x >> [a, b] >> y` | a and b execute in parallel, y waits for all |
| `?label` | Conditional branch | `a ?ok >> b` | Execute b when a output satisfies ok condition |
| `* $var` | Loop iteration | `a * $items` | Execute a for each item in $items |
| `* $var[n]` | Parallel loop | `a * $items[3]` | Parallel iteration with degree 3 |
| `START` | Entry point | `START >> a` | Workflow entry |
| `END` | Exit point | `a >> END` | Workflow exit |

### 8.3 Three Output Formats

Flow definitions can automatically convert to three formats for different scenarios:

1. **Mermaid Diagram**: Visualization
2. **Structured Text**: Agent understanding
3. **DAG JSON**: Programmatic processing

See `flow-dsl-syntax.md` for details.

---

## 9. To Be Determined

> The following content is not yet finalized and needs future discussion.

### 9.1 🔖 Retry Mechanism

**Issue**: How to control retries after SubagentStop validation failure?

**To Discuss**:
- How to configure maximum retry count?
- Should error feedback be passed during retry?
- What to do after reaching max retries (skip/terminate)?

### 9.2 🔖 State Persistence

**Issue**: How to recover after workflow interruption?

**To Discuss**:
- State file format and location
- Checkpoint save timing
- Recovery command design

### 9.3 🔖 Timeout Handling

**Issue**: What to do when SubAgent execution takes too long?

**To Discuss**:
- Timeout configuration location (Agent definition / global config)
- Timeout handling strategy

---

## 10. Execution Flow Example

```
User: /my-workflow --workdir=/output

1. UserPromptSubmit Hook
   ├── Validate input (command arguments, environment variables)
   ├── Create $WORKDIR/.context/ directory
   └── Initialize workflow state

2. Command Execution
   ├── Parse Flow definition
   └── Call SubAgents in order/parallel

3. For each SubAgent call:
   │
   ├── PreToolUse (Task) Hook
   │   ├── Identify target SubAgent
   │   ├── Load input contract
   │   ├── Validate input files
   │   └── Block execution on failure
   │
   ├── SubAgent Execution
   │   ├── Read context files
   │   ├── Execute task
   │   └── Generate Markdown output
   │
   └── SubagentStop Hook
       ├── Iterate contracts to match output
       ├── Match success → write to .context/<agent>.md
       └── Match failure → block exit, require re-output

4. Stop Hook
   ├── Validate overall workflow output
   ├── Check all required nodes completed
   └── Generate execution report
```

---

## 11. Next Steps

1. ✅ Complete core design (Contract, Nodes, Flow, Context)
2. ✅ Determine Flow expression (concise DSL + three output formats)
3. 🔖 Discuss and determine retry mechanism
4. 🔖 Discuss and determine state persistence solution
5. 🔖 Discuss and determine timeout handling
6. Implement Flow DSL parser
7. Implement Flow → Mermaid/Structured Text/DAG JSON converter
8. Create example workflow to validate design
