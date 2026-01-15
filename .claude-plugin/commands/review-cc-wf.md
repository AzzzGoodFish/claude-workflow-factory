---
description: 审查 Claude Code 工作流（结构/功能/运行时校验）
argument-hint: "[workflow-dir] [--mode structure|function|runtime] [--log log-path]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - AskUserQuestion
  - TodoWrite
---

# 审查 Claude Code 工作流

你是工作流审查专家，负责校验工作流组件的规范性、功能完整性，并支持运行时问题定位。

## 参数解析

从 `$ARGUMENTS` 解析：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| workflow-dir | 工作流目录路径 | `.claude/` |
| --mode | 校验模式：structure / function / runtime | structure |
| --log | 运行日志路径（runtime 模式需要） | - |

解析示例：
- `/review-cc-wf` → 目录 `.claude/`，模式 `structure`
- `/review-cc-wf .claude/ --mode function` → 目录 `.claude/`，模式 `function`
- `/review-cc-wf --mode runtime --log .context/state.md` → 模式 `runtime`，日志路径指定

---

## 审查流程

### 步骤 1: 初始化

1. 解析参数，确定工作流目录和审查模式

2. 使用 TodoWrite 创建任务列表（根据模式）：
   - structure 模式：各组件类型的规范检查
   - function 模式：功能完整性检查
   - runtime 模式：日志分析和问题定位

3. 使用 Glob 扫描工作流目录，确认目录存在

4. 初始化审查报告结构：
   ```
   errors: []      # 必须修复的问题
   warnings: []    # 建议修复的问题
   passed: []      # 通过的检查项
   ```

---

### 步骤 2: 执行审查

根据 `--mode` 参数执行不同的审查逻辑：

#### 模式 A: 结构规范校验 (--mode structure)

检查各组件是否符合 Claude Code 规范。

**Skill 校验**：
```
检查路径: {workflow-dir}/skills/*/SKILL.md
```

| 检查项 | 规则 | 级别 |
|--------|------|------|
| frontmatter 完整性 | 必须有 name, description | error |
| description 格式 | 必须包含 "This skill should be used when" | error |
| 触发短语 | description 中有具体的触发短语 | warning |
| 正文词数 | 建议 1,500-2,000 词 | warning |
| 祈使句风格 | 正文使用动词开头的指令形式 | warning |

**Agent 校验**：
```
检查路径: {workflow-dir}/agents/*.md
```

| 检查项 | 规则 | 级别 |
|--------|------|------|
| frontmatter 完整性 | 必须有 name, description, model, color | error |
| name 格式 | 3-50 字符，小写+连字符 | error |
| description 格式 | 必须包含 "Use this agent when" | error |
| 触发示例 | 必须有 2-4 个 `<example>` 块 | error |
| tools 配置 | 如有 tools 字段，必须是有效数组 | error |
| 系统提示词 | 必须有结构化的系统提示词 | warning |

**Command 校验**：
```
检查路径: {workflow-dir}/commands/*.md
```

| 检查项 | 规则 | 级别 |
|--------|------|------|
| frontmatter 完整性 | 必须有 description | error |
| allowed-tools | 如有，必须是有效数组 | error |
| argument-hint | 如有参数，应有 argument-hint | warning |
| 正文结构 | 应有清晰的执行指令 | warning |

**Contract 校验**：
```
检查路径: {workflow-dir}/contracts/*.yaml 或 *.json
```

| 检查项 | 规则 | 级别 |
|--------|------|------|
| Schema 格式 | 必须是有效的 YAML/JSON | error |
| type 字段 | 必须有 type 定义 | error |
| properties 定义 | 对象类型必须有 properties | warning |
| 示例数据 | 应有配套的 .md 说明文档 | warning |

**Hook Script 校验**：
```
检查路径: {workflow-dir}/hooks/*.py
```

| 检查项 | 规则 | 级别 |
|--------|------|------|
| Python 语法 | 必须是有效的 Python 代码 | error |
| stdin 读取 | 应使用 json.load(sys.stdin) | warning |
| stdout 输出 | 应输出 JSON 格式 | warning |
| 异常处理 | 应有 try-except 处理 | warning |

**settings.json 校验**：
```
检查路径: {workflow-dir}/settings.json 或 settings.local.json
```

| 检查项 | 规则 | 级别 |
|--------|------|------|
| JSON 格式 | 必须是有效的 JSON | error |
| hooks 配置 | 如有 hooks，格式必须正确 | error |
| 路径引用 | 应使用 ${CLAUDE_PROJECT_ROOT} | warning |

---

#### 模式 B: 功能完整性校验 (--mode function)

检查工作流是否满足功能需求。

**步骤**：

1. **读取设计文档**
   ```
   设计目录: .context/design/
   - 00-requirements.md
   - 01-skills-design.md
   - 02-nodes-design.md
   - 03-contracts-design.md
   - 04-flow-design.md
   ```

2. **节点覆盖检查**
   - 从 `02-nodes-design.md` 提取声明的节点列表
   - 检查 `{workflow-dir}/agents/` 中是否都有对应文件
   - 报告缺失的节点

3. **技能绑定检查**
   - 从节点文件中提取绑定的技能引用（@skills/...）
   - 检查 `{workflow-dir}/skills/` 中是否存在
   - 报告缺失的技能

4. **契约匹配检查**
   - 从节点设计中提取输入/输出契约引用
   - 检查 `{workflow-dir}/contracts/` 中是否存在
   - 检查 `contracts/mapping.yaml` 配置是否完整
   - 报告缺失或配置错误的契约

5. **流程完整性检查**
   - 检查是否有入口 Command（`{workflow-dir}/commands/`）
   - 检查 Command 中是否引用了所有节点
   - 报告流程断点

6. **依赖关系检查**
   - 分析节点间的数据依赖
   - 检查是否有循环依赖
   - 报告依赖问题

---

#### 模式 C: 运行时问题定位 (--mode runtime)

分析工作流执行日志，定位问题根因。

**前提条件**：
- 必须提供 `--log` 参数指定状态文件或日志路径
- 通常是 `.context/state.md` 或 transcript 文件

**步骤**：

1. **读取状态文件**
   ```
   默认路径: .context/state.md
   ```

2. **解析执行状态**
   - 工作流状态（running/completed/failed）
   - 各节点执行状态
   - 失败节点识别

3. **失败分析**
   - 识别失败的节点
   - 分类错误类型：
     - 契约校验失败
     - 执行错误
     - 超时
     - 其他

4. **上下文分析**
   - 分析失败时的输入数据
   - 检查前序节点的输出
   - 识别数据问题

5. **生成修复建议**
   - 根据错误类型给出具体建议
   - 指出需要修改的文件和位置

---

### 步骤 3: 生成审查报告

生成 Markdown 格式的审查报告：

```markdown
# 工作流审查报告

## 概览
- **工作流**: {workflow-name}
- **审查模式**: {mode}
- **审查时间**: {timestamp}
- **工作流目录**: {workflow-dir}
- **总体结果**: {✅ 通过 / ⚠️ 有警告 / ❌ 有错误}

## 审查统计
- 检查项: {total}
- 通过: {passed}
- 警告: {warnings}
- 错误: {errors}

## 发现问题

### ❌ 错误 (必须修复)

{如果有错误，按以下格式列出}

1. **{file-path} - {issue-title}**
   - 位置: {location}
   - 问题: {description}
   - 修复: {suggestion}

### ⚠️ 警告 (建议修复)

{如果有警告，按以下格式列出}

1. **{file-path} - {issue-title}**
   - 位置: {location}
   - 问题: {description}
   - 修复: {suggestion}

## 通过的检查项

{列出通过的检查项摘要}

## 下一步建议

{根据审查结果给出建议}
```

---

### 步骤 4: 展示结果

1. 将审查报告写入 `.context/review-report.md`

2. 向用户展示报告摘要：
   - 总体结果
   - 错误数量和关键错误
   - 警告数量

3. 如果有错误，使用 AskUserQuestion 询问：
   - 是否需要详细说明某个问题？
   - 是否需要帮助修复？

---

## 检查规则详解

### Skill 检查规则

```python
# frontmatter 必需字段
required_fields = ["name", "description"]

# description 格式
valid_patterns = [
    r"This skill should be used when",
    r"Use this skill when",
    r"This skill provides",
]

# 正文词数范围
word_count_range = (1500, 2000)  # 警告级别
```

### Agent 检查规则

```python
# frontmatter 必需字段
required_fields = ["name", "description", "model", "color"]

# name 格式
name_pattern = r"^[a-z][a-z0-9-]{1,48}[a-z0-9]$"

# description 格式
description_pattern = r"Use this agent when"

# 触发示例数量
example_count_range = (2, 4)
```

### Contract 检查规则

```python
# 必需字段（JSON Schema）
required_fields = ["type"]

# 对象类型必需字段
object_required = ["properties"]

# 数组类型必需字段
array_required = ["items"]
```

---

## 错误处理

- **目录不存在**：报错并退出
- **文件解析失败**：记录为错误，继续检查其他文件
- **设计文档缺失**：在 function 模式下警告，无法完成完整性检查

---

## 注意事项

1. **使用 TodoWrite 跟踪审查进度**
2. **按组件类型分批检查，便于定位问题**
3. **错误和警告分级清晰**
4. **修复建议必须具体可操作**
5. **支持增量审查（只检查指定文件）**
