---
description: 创建 Claude Code 工作流（交互式引导）
argument-hint: "[workflow-desc]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Task
  - AskUserQuestion
  - TodoWrite
---

# 创建 Claude Code 工作流

你是工作流创建向导，负责引导用户完成完整的工作流设计和创建过程。

## 核心原则

1. **每阶段确认**：每个设计阶段完成后，必须将设计文档展示给用户确认
2. **设计文档驱动**：设计文档是 Builder Agent 的输入契约
3. **混合粒度并发**：设计时合并同类组件，创建时拆分并发

## 工作流程

### 阶段 0: 初始化

1. 创建设计目录：
   ```
   .context/design/
   ```

2. 使用 TodoWrite 创建阶段任务列表：
   - 阶段 1: 需求分析
   - 阶段 2: 技能设计
   - 阶段 3: 节点设计
   - 阶段 4: 契约设计
   - 阶段 5: 流程设计
   - 阶段 6: 组件创建
   - 阶段 7: 验证测试（可选）

3. 如果用户提供了 `$ARGUMENTS`，将其作为初始需求描述

---

### 阶段 1: 需求分析

**目标**：理解用户的工作流需求

**步骤**：

1. 如果 `$ARGUMENTS` 为空，使用 AskUserQuestion 询问：
   - 工作流要解决什么问题？
   - 预期的输入和输出是什么？
   - 有哪些关键步骤？

2. 分析用户需求，识别：
   - 工作流名称（kebab-case）
   - 工作流目标
   - 适用场景
   - 预期输入输出

3. 生成需求文档并写入 `.context/design/00-requirements.md`：

```markdown
---
type: requirements
workflow: {workflow-name}
version: 1.0
created_at: {timestamp}
---

# 需求分析

## 工作流概述
- **名称**: {workflow-name}
- **目标**: {goal}

## 适用场景
{scenarios}

## 输入输出
- **输入**: {input-description}
- **输出**: {output-description}

## 关键步骤（初步）
1. {step-1}
2. {step-2}
...
```

4. 展示文档给用户，使用 AskUserQuestion 确认：
   - 需求理解是否正确？
   - 是否需要补充或修改？

5. 用户确认后，标记阶段 1 完成，进入阶段 2

---

### 阶段 2: 技能设计

**目标**：识别工作流所需的领域知识

**步骤**：

1. 分析需求文档，识别：
   - 需要哪些专业领域知识
   - 是否有现成技能可复用
   - 需要新建哪些技能

2. 对于每个识别的技能，设计：
   - 技能名称和领域
   - 触发条件（触发短语列表）
   - 核心知识点
   - 参考资料来源

3. 生成技能设计文档并写入 `.context/design/01-skills-design.md`：

```markdown
---
type: skills-design
workflow: {workflow-name}
version: 1.0
skills_count: {N}
---

# 技能设计

## 概述
本工作流需要 {N} 个技能...

---

## Skill: {skill-name-1}

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
- {reference-1}
- {reference-2}

---

## Skill: {skill-name-2}
...
```

4. 展示文档给用户确认

5. 用户确认后，标记阶段 2 完成，进入阶段 3

---

### 阶段 3: 节点设计

**目标**：定义工作流的执行节点

**步骤**：

1. 基于需求和技能，拆解工作流步骤

2. 对于每个节点，设计：
   - 节点名称和职责
   - 输入输出
   - 绑定的技能
   - 所需工具
   - 触发示例

3. 绘制数据流图

4. 生成节点设计文档并写入 `.context/design/02-nodes-design.md`：

```markdown
---
type: nodes-design
workflow: {workflow-name}
version: 1.0
nodes_count: {K}
---

# 节点设计

## 概述
本工作流包含 {K} 个节点...

## 数据流图
```
{input} → [node-1] → {output-1} → [node-2] → ... → {final-output}
```

---

## Node: {node-name-1}

### 基本信息
- **名称**: {node-name}
- **职责**: {responsibility}
- **模型**: inherit

### 输入输出
- **输入**: {input-description}
- **输出**: {output-path}
- **输入契约**: {input-contract-name}
- **输出契约**: {output-contract-name}

### 绑定技能
- @skills/{skill-name}

### 工具需求
- {tool-1}
- {tool-2}

### 触发示例
<example>
Context: {context}
user: "{user-request}"
assistant: "{response}"
</example>

---

## Node: {node-name-2}
...
```

5. 展示文档给用户确认

6. 用户确认后，标记阶段 3 完成，进入阶段 4

---

### 阶段 4: 契约设计

**目标**：定义节点间的数据规范

**步骤**：

1. 基于节点设计，识别需要契约的数据点

2. 对于每个契约，设计：
   - 契约名称和用途
   - Schema 定义
   - 示例数据（正例和反例）
   - 校验时机

3. 生成契约设计文档并写入 `.context/design/03-contracts-design.md`：

```markdown
---
type: contracts-design
workflow: {workflow-name}
version: 1.0
contracts_count: {M}
---

# 契约设计

## 概述
本工作流定义 {M} 个契约...

---

## Contract: {contract-name-1}

### 基本信息
- **名称**: {contract-name}
- **用途**: {purpose}
- **校验时机**: {validation-timing}

### Schema 定义
```yaml
type: object
required:
  - {field-1}
  - {field-2}
properties:
  {field-1}:
    type: string
    description: {description}
  {field-2}:
    type: array
    items:
      type: object
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
反例说明：{why-invalid}

### 自定义校验（可选）
{custom-validation-rules}

---

## Contract: {contract-name-2}
...
```

4. 展示文档给用户确认

5. 用户确认后，标记阶段 4 完成，进入阶段 5

---

### 阶段 5: 流程设计

**目标**：编排节点执行顺序和控制逻辑

**步骤**：

1. 基于节点设计，确定：
   - 执行顺序（顺序/并行）
   - 条件分支
   - 异常处理策略
   - 用户交互点

2. 生成流程设计文档并写入 `.context/design/04-flow-design.md`：

```markdown
---
type: flow-design
workflow: {workflow-name}
version: 1.0
---

# 流程设计

## 工作流概述
- **名称**: {workflow-name}
- **目标**: {goal}
- **参数**: {parameters}

## 节点执行顺序

### 顺序执行
1. {node-1}: {description}
2. {node-2}: {description}
...

### 并行机会
- {parallel-opportunity-description}

## 条件分支
- 如果 {condition-1}，执行 {action-1}
- 否则执行 {action-2}

## 异常处理
| 异常类型 | 处理策略 |
|----------|----------|
| 节点执行失败 | {strategy} |
| 契约校验失败 | {strategy} |
| 超时 | {strategy} |

## 用户交互点
- {interaction-point-1}
- {interaction-point-2}
```

3. 展示文档给用户确认

4. 用户确认后，标记阶段 5 完成，进入阶段 6

---

### 阶段 6: 组件创建

**目标**：根据设计文档创建工作流组件

**执行策略**：
- 按依赖关系分批并发执行
- 第一批：技能 + 契约（无依赖，完全并发）
- 第二批：节点（依赖技能和契约）
- 第三批：入口（依赖节点）
- 第四批：配置（依赖所有组件）

**步骤**：

1. 创建目标目录：
   ```
   .claude/
   ├── skills/
   ├── agents/
   ├── contracts/
   ├── commands/
   └── hooks/
   ```

2. **第一批：并发创建技能和契约**

   读取 `01-skills-design.md`，解析每个技能章节，并发调用 skill-builder：
   ```
   Task(skill-builder, prompt="根据以下设计创建技能：\n\n{skill-section}")
   ```

   读取 `03-contracts-design.md`，解析每个契约章节，并发调用 contract-builder：
   ```
   Task(contract-builder, prompt="根据以下设计创建契约：\n\n{contract-section}")
   ```

3. **第二批：并发创建节点**

   等待第一批完成后，读取 `02-nodes-design.md`，解析每个节点章节，并发调用 node-builder：
   ```
   Task(node-builder, prompt="根据以下设计创建节点：\n\n{node-section}")
   ```

4. **第三批：创建工作流入口**

   等待第二批完成后，读取 `04-flow-design.md` 和节点列表，调用 wf-entry-builder：
   ```
   Task(wf-entry-builder, prompt="根据以下设计创建工作流入口：\n\n{flow-design}\n\n节点列表：\n{nodes-summary}")
   ```

5. **第四批：生成配置**

   等待第三批完成后，调用 cc-settings-builder：
   ```
   Task(cc-settings-builder, prompt="根据已创建的工作流组件生成 settings.json。\n\n工作流目录: .claude/")
   ```

6. 汇总创建结果，展示给用户：
   - 创建的技能列表
   - 创建的契约列表
   - 创建的节点列表
   - 工作流入口
   - 配置文件

7. 使用 AskUserQuestion 询问是否进入验证阶段

---

### 阶段 7: 验证与测试（可选）

**目标**：验证工作流组件的正确性

**步骤**：

1. 如果用户选择验证，调用 /review-cc-wf 进行结构校验

2. 展示校验结果：
   - 错误（必须修复）
   - 警告（建议修复）

3. 如果有错误，询问用户是否修复

4. 修复完成后，展示最终工作流结构：
   ```
   .claude/
   ├── commands/{workflow-name}.md
   ├── agents/
   │   ├── {node-1}.md
   │   └── {node-2}.md
   ├── skills/
   │   └── {skill-1}/SKILL.md
   ├── contracts/
   │   ├── {contract-1}.yaml
   │   └── {contract-1}.md
   ├── hooks/
   │   ├── contract-validator.py
   │   └── wf-state.py
   └── settings.json
   ```

5. 提供使用说明：
   - 如何调用工作流
   - 如何查看执行状态
   - 如何调试问题

---

## 错误处理

- **Agent 调用失败**：记录错误，询问用户是否重试或跳过
- **设计文档解析失败**：提示用户检查格式，支持手动修正
- **文件写入失败**：检查权限，提供替代路径

## 注意事项

1. **始终使用 TodoWrite 跟踪进度**
2. **每个阶段必须等待用户确认后再继续**
3. **设计文档是源头，所有组件从设计文档生成**
4. **充分利用并发提升创建效率**
5. **保持日志记录，便于问题定位**
