---
name: resource-analysis
description: This skill should be used when the user asks to "analyze reference materials", "extract workflow elements", "parse API documentation", "identify workflow entities", "extract data structures from documents", or needs to extract workflow design elements from user-provided materials such as API docs, requirements documents, process diagrams, or existing code.
---

# Resource Analysis for Workflow Design

Provides methodology for analyzing user-provided reference materials to extract workflow design elements.

## Purpose

Extract actionable workflow design elements from various resource types:
- API documentation
- Requirements documents
- Process descriptions
- Existing code/scripts
- Database schemas
- Business rules

## Element Extraction Framework

### Target Elements

| Element Type | What to Look For | Used In |
|--------------|------------------|---------|
| **Entities** | Nouns, data objects, resources | Contract design |
| **Actions** | Verbs, operations, transformations | Node identification |
| **Flows** | Sequences, dependencies, conditions | Flow design |
| **Data Structures** | Fields, types, constraints | Schema definition |
| **Rules** | Validations, business logic, constraints | Validator design |

### Extraction Process

```
1. Identify Resource Type
   ├── API Documentation → Focus on endpoints, request/response schemas
   ├── Requirements → Focus on user stories, acceptance criteria
   ├── Process Description → Focus on steps, decisions, actors
   ├── Code/Scripts → Focus on functions, data transformations
   └── Database Schema → Focus on tables, relationships, constraints

2. Extract Raw Elements
   ├── List all entities mentioned
   ├── List all actions/operations
   ├── Identify data flows
   └── Note constraints and rules

3. Map to Workflow Concepts
   ├── Entities → Potential data contracts
   ├── Actions → Potential workflow nodes
   ├── Flows → Execution order and conditions
   └── Rules → Validation logic

4. Organize Output
   ├── Group related elements
   ├── Identify dependencies
   └── Highlight ambiguities for user confirmation
```

## Resource Type Analysis

### API Documentation

**Key patterns to identify:**

| Pattern | Workflow Element | Example |
|---------|------------------|---------|
| Endpoints | Potential nodes | `POST /reviews` → create-review node |
| Request body | Input contract | JSON schema → Contract schema |
| Response body | Output contract | JSON schema → Contract schema |
| Status codes | Condition branches | `200 OK`, `400 Bad Request` → ?success, ?error |
| Authentication | Context requirement | API key → Environment variable |

**Extraction template:**

```markdown
## From API: [Endpoint Name]

### Identified Entity
- Name: [entity name]
- Operations: [CRUD operations available]

### Potential Node
- Name: [suggested node name]
- Input: [request structure]
- Output: [response structure]

### Constraints
- [validation rules from API spec]
```

### Requirements Document

**Key patterns to identify:**

| Pattern | Workflow Element | Example |
|---------|------------------|---------|
| "User can..." | Node trigger | User can submit review → submission node |
| "System should..." | Node action | System validates → validation node |
| "When...then..." | Conditional flow | When valid, proceed → ?valid branch |
| "Must have..." | Required field | Must have score → required in schema |
| "Before...after..." | Sequential dependency | Before publish, review → a >> b |

**Extraction template:**

```markdown
## From Requirement: [Requirement ID/Name]

### User Story
[Original user story text]

### Extracted Workflow Steps
1. [Step from story] → [suggested node]
2. [Step from story] → [suggested node]

### Data Requirements
- [Required field]: [type] - [constraint]

### Business Rules
- [Rule description] → [validation logic]
```

### Process Description

**Key patterns to identify:**

| Pattern | Workflow Element | Example |
|---------|------------------|---------|
| Sequential steps | Flow order | Step 1, Step 2 → a >> b |
| Decision points | Conditional branch | If approved → ?approved |
| Parallel activities | Parallel group | Meanwhile → [a, b] |
| Loops | Iteration | For each item → * $items |
| Actors | Node responsibility | Reviewer checks → reviewer node |

**Extraction template:**

```markdown
## From Process: [Process Name]

### Process Flow
```
[Original process description or diagram]
```

### Suggested Flow DSL
```yaml
flow: |
  START >> [extracted flow] >> END
```

### Identified Roles/Actors
- [Actor] → [node responsibility]

### Decision Points
- [Decision] → [condition expression]
```

### Existing Code/Scripts

**Key patterns to identify:**

| Pattern | Workflow Element | Example |
|---------|------------------|---------|
| Functions | Potential nodes | `def process_data()` → processor node |
| Input parameters | Input contract | Function args → Schema fields |
| Return values | Output contract | Return type → Schema |
| Conditionals | Branch conditions | `if status == 'ok'` → ?ok |
| Loops | Iteration | `for item in items` → * $items |
| Error handling | Error branches | `try/except` → ?error |

**Extraction template:**

```markdown
## From Code: [File/Function Name]

### Function Analysis
- Name: [function name]
- Purpose: [what it does]
- Input: [parameters with types]
- Output: [return type]

### Suggested Node
```yaml
name: [suggested name]
input:
  contract: [derived from parameters]
output:
  contract: [derived from return]
```

### Logic to Preserve
- [Key business logic that should be in prompt or validator]
```

## Output Format

### Element Extraction Report

```markdown
---
type: resource-analysis
agent: wf-resource-analyzer
timestamp: [ISO8601]
source: [resource path/name]
---

## Resource Overview

**Type**: [API Doc | Requirements | Process | Code | Schema]
**Source**: [file path or URL]
**Summary**: [brief description of what was analyzed]

## Extracted Workflow Elements

### Entities Identified

| Entity | Description | Suggested Contract |
|--------|-------------|-------------------|
| [name] | [what it represents] | [contract name] |

### Actions/Operations Identified

| Action | Input | Output | Suggested Node |
|--------|-------|--------|----------------|
| [action] | [data] | [data] | [node name] |

### Process Flow Identified

**Sequence:**
1. [Step] → [node]
2. [Step] → [node]

**Conditions:**
- [Condition] → [branch label]

**Suggested Flow DSL:**
```yaml
flow: |
  [extracted flow]
```

### Data Structures Identified

**[Structure Name]:**
```yaml
type: object
properties:
  [field]:
    type: [type]
    [constraints]
```

### Validation Rules Identified

| Rule | Applies To | Validation Logic |
|------|------------|------------------|
| [rule name] | [entity/field] | [logic description] |

## Ambiguities and Questions

Items requiring user clarification:

1. **[Topic]**: [Question for user]
2. **[Topic]**: [Question for user]

## Recommendations

Based on analysis, suggested next steps:

1. [Recommendation]
2. [Recommendation]
```

## Best Practices

### 1. Be Comprehensive but Organized

Extract all relevant elements, but organize them clearly:
- Group by type (entities, actions, flows, data, rules)
- Show relationships between elements
- Highlight dependencies

### 2. Preserve Original Context

When extracting:
- Quote relevant original text
- Reference source locations
- Note assumptions made

### 3. Flag Ambiguities

Explicitly note:
- Missing information
- Unclear requirements
- Multiple interpretations
- Assumptions made

### 4. Suggest, Don't Dictate

Present extractions as suggestions:
- "Suggested node name: ..."
- "This could map to ..."
- "Consider whether ..."

### 5. Focus on Workflow-Relevant Elements

Prioritize elements that directly map to:
- Contracts (data structures)
- Nodes (execution units)
- Flow (execution order)
- Context (environment needs)
