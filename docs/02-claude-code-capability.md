# Claude Code 核心能力

## 概述

本文档系统梳理 Claude Code 的核心能力，为理解和使用 Claude Code 提供详实的能力参考。

**参考资料来源**：本文档基于 plugin-dev 插件的官方技能文档整理，详细参考资料位于 `skills/` 目录：
- `skills/skill-development/` - Skill 开发指南
- `skills/command-development/` - Command 开发指南
- `skills/agent-development/` - Agent 开发指南
- `skills/hook-development/` - Hook 开发指南
- `skills/mcp-integration/` - MCP 集成指南

---

## 能力概览

| 能力 | 本质 | 文件格式 | 触发方式 |
|------|------|----------|----------|
| Skill | 可复用的领域知识 | Markdown + YAML frontmatter | 自动激活（基于描述匹配） |
| Command | 用户显式调用的指令 | Markdown + YAML frontmatter | 用户手动调用 `/command-name` |
| Subagent | 独立执行任务的子智能体 | Markdown + YAML frontmatter | 主智能体通过 Task 工具调用 |
| Hook | 事件驱动的拦截与处理 | JSON 配置 + 可选脚本 | 事件自动触发 |
| Tool | 内置的基础操作能力 | 内置 | 智能体直接调用 |
| MCP | 可扩展的外部工具 | JSON 配置 + 外部服务 | 智能体直接调用 |

---

## 1. Skill（技能）

> **参考资料**：`skills/skill-development/SKILL.md`

### 定义

Skill 是封装领域知识的可复用模块，为智能体提供"如何做好这件事"的知识指导。

### 核心特征

**自动激活**：
- Claude Code 根据任务上下文自动匹配并加载相关 Skill
- 无需用户或智能体显式调用
- 通过 `description` 字段中的触发短语进行匹配

**渐进式披露**：
- 三级加载机制：
  1. **元数据**（name + description）：始终在上下文中（~100 词）
  2. **SKILL.md 主体**：技能触发时加载（<5k 词）
  3. **捆绑资源**：按需加载（无限制）

**可组合性**：
- 多个 Skill 可同时激活
- 不同 Skill 可组合使用解决复杂问题

### 文件结构

```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter
│   │   ├── name: (必需)
│   │   ├── description: (必需，包含触发短语)
│   │   └── version: (可选)
│   └── Markdown 正文（祈使句形式）
└── 捆绑资源（可选）
    ├── scripts/          # 可执行脚本
    ├── references/       # 参考文档
    ├── examples/         # 示例代码
    └── assets/           # 输出资源
```

### 关键要素

**description 字段**（触发条件）：
- 使用第三人称："This skill should be used when..."
- 包含具体的触发短语：用户可能说的话
- 示例：
  ```yaml
  description: This skill should be used when the user asks to "create a hook", "add a PreToolUse hook", "validate tool use", or mentions hook events.
  ```

**SKILL.md 正文**（核心指导）：
- 使用祈使句/不定式形式（动词开头）
- 保持精简（1,500-2,000 词理想，<5k 词上限）
- 包含：核心概念、基本流程、快速参考、资源指引

**捆绑资源**（按需加载）：
- `scripts/`：可执行代码（Python/Bash 等），用于重复性任务
- `references/`：详细文档，智能体按需读取
- `examples/`：完整可运行的示例
- `assets/`：输出资源（模板、图标等）

### 设计原则

1. **强触发条件**：description 中包含明确的触发短语
2. **渐进式披露**：核心内容在 SKILL.md，详细内容在 references/
3. **祈使句风格**：正文使用动词开头的指令形式
4. **避免重复**：信息只存在于一处（SKILL.md 或 references/）

---

## 2. Command（命令）

> **参考资料**：`skills/command-development/SKILL.md`

### 定义

Command 是用户显式调用的指令，接收参数，向 Claude 注入上下文。

### 核心特征

**用户触发**：
- 用户通过 `/command-name` 显式调用
- 可接收参数：`/command-name arg1 arg2`
- 自然的用户交互起点

**上下文注入**：
- 向主智能体注入特定上下文
- 可包含执行指导、规范要求
- 可引用 Skill 获取领域知识

**工具限制**：
- 可通过 `allowed-tools` 限制可用工具
- 实现最小权限原则
- 提高安全性

### 文件结构

```markdown
---
name: command-name
description: 命令的简短描述
argument-hint: "[可选参数说明]"
allowed-tools: ["Read", "Write", "Task", "Bash"]
---

# 命令说明

这是给 Claude 的指令，不是给用户的说明。

## 执行步骤

1. 第一步
2. 第二步
3. 第三步

## 注意事项

- 注意点1
- 注意点2
```

### 关键要素

**frontmatter 字段**：
- `name`：命令标识符（kebab-case）
- `description`：简短描述（给用户看）
- `argument-hint`：参数提示
- `allowed-tools`：限制可用工具（最小权限原则）

**Markdown 正文**：
- **为 Claude 编写**，不是为用户编写
- 使用祈使句形式
- 包含执行步骤、注意事项、示例

### 设计原则

1. **为 Claude 编写**：指令是给智能体的，不是给用户的
2. **最小工具集**：只授予必要的工具权限
3. **清晰流程**：明确的步骤和决策点
4. **引用 Skill**：可引用相关 Skill 获取领域知识

---

## 3. Subagent（子智能体）

> **参考资料**：`skills/agent-development/SKILL.md`

### 定义

Subagent 是通过 Task 工具调用的独立智能体，有独立上下文和工具集。

### 核心特征

**专注性**：
- 专注单一任务
- 明确的输入输出
- 单一职责原则

**隔离性**：
- 独立上下文
- 不污染主智能体上下文
- 可限定工具集

**无状态**：
- 接收输入
- 产出输出
- 不关心全局状态

### 文件结构

```markdown
---
name: agent-identifier
description: Use this agent when [触发条件]. Examples:

<example>
Context: [场景描述]
user: "[用户请求]"
assistant: "[智能体响应]"
<commentary>
[为什么触发此智能体]
</commentary>
</example>

model: inherit
color: blue
tools: ["Read", "Write", "Grep"]
---

You are [角色描述]...

**Your Core Responsibilities:**
1. [职责1]
2. [职责2]

**Analysis Process:**
1. [步骤1]
2. [步骤2]

**Output Format:**
[输出格式说明]
```

### 关键要素

**frontmatter 字段**：
- `name`：智能体标识符（3-50 字符，小写，连字符）
- `description`：触发条件 + 示例（2-4 个 `<example>` 块）
- `model`：使用的模型（inherit/sonnet/opus/haiku）
- `color`：UI 标识颜色
- `tools`：限定可用工具（可选）

**系统提示词**（Markdown 正文）：
- 使用第二人称（"You are..."）
- 明确职责和流程
- 定义输出格式
- 处理边缘情况

### 设计原则

1. **强触发示例**：description 中包含 2-4 个具体示例
2. **清晰职责**：明确的任务边界
3. **标准化输出**：定义明确的输出格式
4. **最小权限**：只授予必要的工具

---

## 4. Hook（钩子）

> **参考资料**：`skills/hook-development/SKILL.md`

### 定义

Hook 是事件驱动的拦截机制，在工具调用前后自动触发。

### 核心特征

**不可见性**：
- 智能体无感知
- 适合做基础设施
- 不干扰正常流程

**强制性**：
- 自动触发
- 确保规则必被执行
- 无法绕过

**灵活性**：
- 支持 prompt（智能体语义校验）
- 支持 command（脚本校验）
- 可实现复杂逻辑

### 配置格式

**插件 hooks.json 格式**（带包装器）：
```json
{
  "description": "钩子说明（可选）",
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

**用户设置格式**（直接）：
```json
{
  "PreToolUse": [...],
  "PostToolUse": [...],
  "Stop": [...]
}
```

### Hook 类型

**Prompt-based Hook**（推荐）：
```json
{
  "type": "prompt",
  "prompt": "Evaluate if this tool use is appropriate: $TOOL_INPUT",
  "timeout": 30
}
```
- 使用 LLM 进行上下文感知的决策
- 灵活的评估逻辑
- 更好的边缘情况处理

**Command Hook**：
```json
{
  "type": "command",
  "command": "bash $CLAUDE_PLUGIN_ROOT/scripts/validate.sh",
  "timeout": 60
}
```
- 执行 bash 命令
- 确定性检查
- 性能关键场景

### Hook 事件

| 事件 | 触发时机 | 用途 |
|------|----------|------|
| PreToolUse | 工具调用前 | 验证、修改、拒绝 |
| PostToolUse | 工具调用后 | 反馈、日志、后处理 |
| UserPromptSubmit | 用户输入时 | 添加上下文、验证 |
| Stop | 主智能体停止前 | 完整性检查 |
| SubagentStop | 子智能体停止前 | 任务验证 |
| SessionStart | 会话开始时 | 加载上下文 |
| SessionEnd | 会话结束时 | 清理、日志 |
| PreCompact | 上下文压缩前 | 保留关键信息 |
| Notification | 通知发送时 | 日志、响应 |

### 设计原则

1. **优先使用 prompt-based**：复杂逻辑用 LLM 处理
2. **使用 $CLAUDE_PLUGIN_ROOT**：确保路径可移植
3. **验证所有输入**：command hook 中验证输入
4. **设置合理超时**：避免阻塞
5. **返回结构化 JSON**：标准化输出格式

---

## 5. Tool（内置工具）

### 定义

Tool 是 Claude Code 内置的基础操作能力。

### 核心工具

**文件操作**：
- **Read**：读取文件内容
- **Write**：写入文件
- **Edit**：编辑文件
- **Glob**：文件模式匹配
- **Grep**：内容搜索

**执行操作**：
- **Bash**：执行 bash 命令
- **Task**：调用 Subagent

**交互操作**：
- **AskUserQuestion**：用户交互
- **TodoWrite**：任务列表管理

**高级操作**：
- **LSP**：语言服务器协议

### 特征

- 内置，无需配置
- 智能体直接调用
- 可通过 `allowed-tools` 限制访问

---

## 6. MCP（Model Context Protocol）

> **参考资料**：`skills/mcp-integration/SKILL.md`

### 定义

MCP 是可扩展的外部工具协议，用于集成外部服务。

### 配置格式

**`.mcp.json` 文件**：
```json
{
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["$CLAUDE_PLUGIN_ROOT/servers/server.js"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

### 特征

**可扩展**：
- 支持自定义工具
- 集成外部服务
- 扩展 Claude Code 能力

**自动启动**：
- 插件启用时自动启动服务器
- 无需手动管理

**环境变量**：
- 支持配置和认证
- 安全的密钥管理

### 服务器类型

- **stdio**：标准输入输出通信（本地进程）
- **SSE**：Server-Sent Events（托管服务）
- **HTTP**：HTTP 请求（远程服务）
- **WebSocket**：WebSocket 连接（实时通信）

---

## 能力特性对比

### 触发方式对比

| 能力 | 触发方式 | 触发者 | 可见性 |
|------|----------|--------|--------|
| Skill | 自动激活（描述匹配） | Claude Code | 对智能体可见 |
| Command | 用户显式调用 | 用户 | 对用户和智能体可见 |
| Subagent | Task 工具调用 | 主智能体 | 对主智能体可见 |
| Hook | 事件自动触发 | Claude Code | 对智能体不可见 |
| Tool | 智能体直接调用 | 智能体 | 对智能体可见 |
| MCP | 智能体直接调用 | 智能体 | 对智能体可见 |

### 上下文隔离对比

| 能力 | 上下文 | 状态 | 工具访问 |
|------|--------|------|----------|
| Skill | 注入主智能体上下文 | 无状态 | 继承主智能体 |
| Command | 主智能体上下文 | 有状态 | 可限制 |
| Subagent | 独立上下文 | 无状态 | 可限制 |
| Hook | 独立进程 | 无状态 | 无（仅脚本） |

### 适用场景对比

| 能力 | 适用场景 | 不适用场景 |
|------|----------|-----------|
| Skill | 提供领域知识、指导流程 | 执行具体任务 |
| Command | 用户交互入口、注入上下文 | 后台自动化 |
| Subagent | 独立任务执行、专注单一职责 | 全局协调 |
| Hook | 规则校验、安全拦截、自动化 | 业务逻辑 |
| Tool | 基础操作 | 复杂业务逻辑 |
| MCP | 外部服务集成 | 内置功能 |

---

## 最佳实践

### Skill 设计

1. **强触发条件**：description 包含明确的触发短语
2. **渐进式披露**：核心内容在 SKILL.md（<2k 词），详细内容在 references/
3. **祈使句风格**：使用动词开头的指令形式
4. **避免重复**：信息只存在于一处

### Command 设计

1. **为 Claude 编写**：指令是给智能体的，不是给用户的
2. **最小工具集**：只授予必要的工具权限
3. **清晰流程**：明确的步骤和决策点
4. **引用 Skill**：可引用相关 Skill 获取领域知识

### Subagent 设计

1. **强触发示例**：description 包含 2-4 个具体示例
2. **清晰职责**：明确的任务边界
3. **标准化输出**：定义明确的输出格式
4. **最小权限**：只授予必要的工具

### Hook 设计

1. **优先 prompt-based**：复杂逻辑用 LLM 处理
2. **使用 $CLAUDE_PLUGIN_ROOT**：确保路径可移植
3. **验证所有输入**：command hook 中验证输入
4. **设置合理超时**：避免阻塞
5. **返回结构化 JSON**：标准化输出格式

---

## 参考资料

### Plugin-Dev 官方技能

本文档基于以下官方技能文档整理：

- **`skills/skill-development/`**：Skill 开发完整指南
  - 渐进式披露设计原则
  - 捆绑资源组织方式
  - 触发条件编写规范

- **`skills/command-development/`**：Command 开发完整指南
  - Frontmatter 字段说明
  - 工具权限控制
  - 参数处理方式

- **`skills/agent-development/`**：Agent 开发完整指南
  - 触发示例编写规范
  - 系统提示词设计模式
  - 模型和工具配置

- **`skills/hook-development/`**：Hook 开发完整指南
  - Prompt-based vs Command hooks
  - 事件类型和用途
  - 输入输出格式
  - 安全最佳实践

- **`skills/mcp-integration/`**：MCP 集成完整指南
  - 服务器类型和配置
  - 环境变量管理
  - 认证和安全

### 外部资源

- **Claude Code 官方文档**：https://docs.claude.com/en/docs/claude-code
- **MCP 协议规范**：https://modelcontextprotocol.io

---

## 总结

Claude Code 提供了一套完整的能力体系：

**核心能力**：
1. **Skill** - 自动激活的领域知识，渐进式披露
2. **Command** - 用户显式调用的指令，上下文注入
3. **Subagent** - 独立执行的子智能体，专注单一任务
4. **Hook** - 事件驱动的拦截机制，不可见但强制
5. **Tool** - 内置的基础操作能力
6. **MCP** - 可扩展的外部工具协议

**设计原则**：
- 单一职责：每个能力专注一件事
- 最小权限：只授予必要的工具和权限
- 渐进式披露：按需加载详细信息
- 自动化优先：能自动化的不手动
- 安全第一：验证输入，限制权限

**参考资料**：
- 所有详细的开发指南都在 `skills/` 目录
- 每个能力都有对应的官方技能文档
- 包含完整的示例和最佳实践
