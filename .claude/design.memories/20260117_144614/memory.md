# 会话上下文 - 2026-01-17 14:46

> 这是此前的对话记录。请根据此文件继续处理用户的请求。
>
> **格式**: **U:** 用户 | **A:** 助手 | 💭 思考 | 📖 读取 | ✍️ 写入 | ✂️ 编辑 | 💻 命令 | 🔍 搜索 | 📁 文件 | 🤖 子任务

_压缩: 86,170 → 19,673 tokens (77.2%)_

---

**U:** @.claude/memories/20260117_134012/memory.md

**A:** 💭The user is referencing a file path with the @ symbol, which typically means they want me to read this file. Let me read the memory file they're pointing to.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭The file is quite large. Let me read it in portions to understand what the user wants me to see.

**A:** The memory file is quite large. Let me read it in portions.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭Let me continue reading the memory file to understand where the conversation left off.

**A:** Let me continue reading the memory file to see where the conversation left off.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭Let me continue reading to see where the conversation ended.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭Let me continue reading to see where the conversation ends and what the current status is.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭Let me continue reading to see where the conversation ends.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭Let me continue reading to see the rest of the conversation and understand where it ended.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/.claude/memories/20260117_134012/memory.md)]

**A:** 💭I've reached the end of the memory file. Let me summarize what was discussed and what the current state is.

The conversation was about the cc-wf-factory (Claude Code Workflow Factory) project. The main focus was on:

1. **Problem 1: How contract-validator.py finds the contract definition**
   - SubagentStop data acquisition: Using prompt matching to get subagent_type
   - subagent_type format: `{plugin}:{agent-name}`
   - Contract location flow (5 steps)
   - node-builder output format (frontmatter with contract fields)

2. **Problem 2: Contract structure definition**
   - Contract file location: `contracts/{name}.yaml`
   - Three-layer validation:
     - Layer 1: schema (JSON Schema structure validation)
     - Layer 2: validator_script (external Python script reference)
     - Layer 3: semantic_check (semantic validation prompt)
   - Metadata: name, description
   - Examples: valid/invalid test data

The conversation ended with the assistant asking if there are other scenarios that need to be supplemented.

Let me summarize this for the user and ask what they want to do next.

**A:** 我已经阅读了完整的会话记录。以下是上次对话的总结和当前状态：

---

## 会话摘要

我们解决了两个核心问题：

### 问题1：契约校验器如何找到指定契约定义 ✅

**完整流程**：
1. SubagentStop 提供 `agent_id` 和 `agent_transcript_path`
2. 通过 **prompt 匹配** 在主会话 transcript 中找到对应的 Task tool_use
3. 获取 `subagent_type`（格式：`{plugin}:{agent-name}`）
4. 定位 agent 配置文件（如 `.claude-plugin/agents/{agent-name}.md`）
5. 从 frontmatter 获取 `output_contract` 字段
6. 读取 `contracts/{contract-name}.yaml`

### 问题2：契约结构定义 ✅

**三层校验**：
| 层级 | 字段 | 说明 |
|------|------|------|
| 元信息 | `name`, `description` | 契约基本信息 |
| 第一层 | `schema` | JSON Schema 结构校验 |
| 第二层 | `validator_script` | 外部 Python 脚本引用 |
| 第三层 | `semantic_check` | 语义校验 prompt |
| 测试 | `examples` | 正例/反例数据 |

脚本接口：`validate(data, context) -> (bool, error_msg)`

---

上次对话以 "还有其他场景需要补充吗？" 结束。

你想继续什么？

**U:** 我在想 semantic_check 实际是怎样工作的

**A:** 💭用户在问 semantic_check 实际是怎样工作的。这是一个很好的问题，因为之前我们只定义了它的存在，但没有详细讨论它的实现机制。

semantic_check 需要 LLM 来理解自然语言并做出判断。在 Claude Code 的 hooks 系统中，有两种类型：
1. `type: "command"` - 执行 bash 命令/脚本
2. `type: "prompt"` - 使用 LLM 评估

contract-validator.py 是一个 command 类型的 hook。那 semantic_check 如何触发 LLM 判断呢？

可能的实现方式：

1. **contract-validator.py 直接调用 LLM API**
   - 脚本内部调用 Anthropic API
   - 需要 API key 和额外依赖
   - 复杂度高

2. **返回特殊状态，让 Claude Code 继续用 prompt hook 处理**
   - contract-validator.py 返回 "需要语义校验"
   - 但 hooks 系统可能不支持这种链式调用

3. **使用两个独立的 hook**
   - contract-validator.py (command) 做结构校验
   - 另一个 prompt-based hook 做语义校验
   - 配置更复杂

4. **contract-validator.py 输出内容供后续处理**
   - 在输出中包含语义校验的需求和 prompt
   - Claude Code 读取并执行
   - 依赖于 hooks 的输出处理机制
   
根据参考文档，prompt-based hooks 可以用于 SubagentStop 事件，所以可以用 command hook 做结构校验，再用 prompt hook 处理语义校验。但这需要协调两个 hook 的执行顺序和数据传递。更直接的方式是让 contract-validator.py 完成结构校验后，如果需要语义校验就返回相应信号。

我应该先了解你的具体需求，或者列举几种可行的实现方案供选择。

**A:** 好问题。`semantic_check` 需要 LLM 理解自然语言并做判断，但 `contract-validator.py` 是一个 command 类型的 hook（执行脚本）。

**几种实现方式**：

### 方案1：contract-validator.py 直接调用 LLM API

```python
# contract-validator.py 内部
if contract.get('semantic_check') and schema_passed:
    from anthropic import Anthropic
    client = Anthropic()
    response = client.messages.create(
        model="claude-3-haiku-...",
        messages=[{
            "role": "user", 
            "content": f"根据以下标准检查数据：\n{semantic_check}\n\n数据：\n{json.dumps(data)}"
        }]
    )
    # 解析 LLM 响应判断是否通过
```

- 优点：一个 hook 完成所有校验
- 缺点：需要 API key、额外依赖、增加成本

### 方案2：两个独立 hook

```json
{
  "hooks": {
    "SubagentStop": [
      { "type": "command", "command": "contract-validator.py" },
      { "type": "prompt", "prompt": "..." }
    ]
  }
}
```

- 优点：利用 Claude Code 原生的 prompt hook
- 缺点：如何传递契约信息给 prompt hook？配置复杂

### 方案3：contract-validator.py 输出 prompt，由主会话 Claude 继续处理

- contract-validator.py 输出包含语义校验需求
- 主会话 Claude 看到输出后执行语义判断
- 依赖 Claude 的行为，不够确定

你倾向哪种方式？或者有其他想法？

**U:** prompt hook 是怎样工作的呢

**A:** 💭用户在问 prompt hook 是怎样工作的。这是一个关于 Claude Code hooks 机制的问题。

让我回忆一下参考文档中关于 prompt-based hooks 的内容：

1. prompt hook 的 type 是 "prompt"
2. 它会让 Claude Code 的 LLM 根据提供的 prompt 进行评估
3. 主要用于 Stop 和 SubagentStop 事件
4. 可以用于语义校验、质量检查等需要 LLM 判断的场景

但我需要确认具体的工作机制。让我搜索一下参考文档或者之前的会话记录，看看有没有更详细的信息。

实际上，用户可能想了解：
1. prompt hook 如何配置
2. prompt hook 的输入是什么
3. prompt hook 如何判断通过/失败
4. prompt hook 的输出如何影响执行流程

我应该查阅一下相关文档来给出准确的答案。

**A:** 让我查一下参考文档中关于 prompt hook 的详细说明。

**A:** [🔍 Grep(`type.*prompt|prompt.*hook`)]

**A:** 💭Let me check the hook reference document to understand how prompt hooks work.

**A:** [🔍 Grep(`type.*prompt|Prompt-based`)]

**A:** 💭Now I have a clearer picture of how prompt-based hooks work. Let me summarize:

1. **配置方式**：
   - `type: "prompt"` 
   - `prompt`: 发送给 LLM 的提示文本
   - `$ARGUMENTS` 是一个占位符，会被替换为 hook 的输入 JSON

2. **工作机制**：
   - 不执行 bash 命令，而是让 LLM 评估
   - LLM 必须返回 JSON 格式：`{"ok": true}` 或 `{"ok": false, "reason": "..."}`
   - `ok: true` 允许操作继续
   - `ok: false` 阻止操作，并显示 reason

3. **支持的事件**：
   - Stop
   - SubagentStop
   - UserPromptSubmit
   - PreToolUse

4. **用途**：
   - 智能判断 Claude 是否应该停止
   - 评估 subagent 是否完成任务
   - 验证用户提示
   - 做上下文感知的权限决策

现在我可以回答用户的问题了。关键点是：prompt hook 让 Claude Code 内部的 LLM 来评估，而不是外部 API 调用。

**A:** 找到了。Prompt hook 的工作机制：

## Prompt Hook 工作原理

**配置方式**：
```json
{
  "hooks": {
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "评估 subagent 输出是否符合要求。输入: $ARGUMENTS\n\n检查...",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**执行流程**：
1. 事件触发（如 SubagentStop）
2. Claude Code 将 `$ARGUMENTS` 替换为 hook 输入的 JSON
3. **由 Claude Code 内部的 LLM 评估**（不是外部 API 调用）
4. LLM 必须返回 JSON：
   - `{"ok": true}` → 允许继续
   - `{"ok": false, "reason": "原因"}` → 阻止操作

**支持的事件**：
- `Stop` - 判断主会话是否应该停止
- `SubagentStop` - 评估 subagent 是否完成任务
- `UserPromptSubmit` - 验证用户输入
- `PreToolUse` - 上下文感知的权限决策

---

**对于 semantic_check 的启示**：

我们可以用两个 hook 配合：
1. `contract-validator.py` (command) - 做结构校验
2. prompt hook - 做语义校验

但问题是：**prompt hook 如何知道要用哪个契约的 semantic_check 内容？**

`$ARGUMENTS` 只包含 SubagentStop 的输入（agent_id、transcript_path 等），不包含契约信息。

你有什么想法？

**U:** 这样有个严重的问题，如果配置了一个 prompt hook，那么每个节点都会触发，无法按需触发

**A:** 💭用户指出了一个很关键的问题：如果在 settings.json 中配置了 SubagentStop 的 prompt hook，那么每个 subagent 结束时都会触发这个 hook，无法根据具体节点是否需要语义校验来按需触发。

这确实是个问题：
1. 并非所有节点都需要语义校验
2. 不同节点的语义校验标准不同
3. 静态配置的 prompt hook 无法动态适应

可能的解决方案：

1. **在 prompt hook 中判断是否需要校验**
   - prompt hook 先读取节点配置，看是否有 semantic_check
   - 如果没有，直接返回 `{"ok": true}`
   - 如果有，执行校验
   - 问题：需要在 prompt 中实现这个逻辑，复杂

2. **只用 command hook，在脚本中调用 LLM API**
   - contract-validator.py 判断是否需要语义校验
   - 如果需要，调用 Anthropic API
   - 问题：需要 API key，额外成本

3. **contract-validator.py 输出特殊格式，让主会话 Claude 继续处理**
   - 比如返回 `{"needs_semantic_check": true, "prompt": "...", "data": "..."}`
   - 主会话 Claude 看到后执行语义判断
   - 问题：依赖 Claude 的行为解读，不够确定

4. **放弃 prompt hook，语义校验由节点自身负责**
   - 节点 agent 的系统提示词中包含输出要求，自己确保符合语义标准
   - contract-validator.py 只负责结构校验
   - 如果需要额外的语义校验，可作为下一个节点的任务

5. **contract-validator.py 返回 block 状态并附带说明**
   - 脚本返回特殊状态来表示需要 Claude 判断的语义校验
   - 说明中包含具体需要判断的内容

，Claude 看到后做判断
   - 问题：hook 的 block 状态本身表示"阻止"，不是"需要进一步判断"

实际上方案4更加可行——节点的系统提示词已经明确定义了输出要求，包括语义层面的约束。Claude 作为节点执行者本身就能确保输出符合要求，contract-validator.py 作为最后的结构校验防线。如果结构通过但语义有问题，那是节点提示词设计不够完善，应该改进提示词而不是依赖额外的校验机制。

不过用户可能需要更复杂的场景，比如关键输出需要"第二双眼睛"审查。这种情况下可以把语义校验设计成独立的审查节点，让工作流变成节点A → 审查节点 → 节点B，由审查节点专门负责质量把关。

**A:** 你说得对，这是个根本性的问题。静态配置的 prompt hook 无法按需触发。

**几种解决思路**：

### 方案1：在 prompt hook 中内置判断逻辑

```json
{
  "prompt": "先检查节点是否需要语义校验（读取契约文件），如果不需要直接返回 {\"ok\": true}，否则执行校验..."
}
```

- 问题：prompt 变得很复杂，每次都要读文件判断

### 方案2：contract-validator.py 直接调用 LLM API

- 脚本内部判断是否需要语义校验
- 需要时调用 Anthropic API
- 问题：需要 API key、额外成本

### 方案3：放弃独立的语义校验机制

- 节点的系统提示词已经定义了输出要求（包括语义层面）
- Claude 作为节点执行者本身就有能力确保质量
- contract-validator.py 只做结构校验作为"最后防线"
- 如果需要额外审查，设计一个"审查节点"放在工作流中

### 方案4：contract-validator.py 输出说明，由主会话 Claude 判断

- 脚本检测到需要语义校验时，输出特殊内容
- 主会话 Claude 看到后执行判断
- 问题：依赖 Claude 的行为解读，不够确定

---

你觉得哪个方向更合理？或者我们重新审视一下：**语义校验真的需要作为 hook 机制的一部分吗？**

**U:** 我现在觉得语义校验通过 settings 添加 prompt 类型钩子的方式有很大的问题，你有什么想法？

**A:** 💭用户觉得通过 settings 添加 prompt 类型钩子来做语义校验有很大问题。让我分析一下问题所在：

**prompt hook 的问题**：
1. **无法按需触发**：静态配置，每个节点都会触发
2. **无法传递契约信息**：$ARGUMENTS 只有 hook 输入，没有契约的 semantic_check 内容
3. **配置复杂**：需要在 settings.json 中维护复杂的 prompt
4. **不灵活**：不同节点的语义校验需求不同，一个静态 prompt 难以覆盖

**重新思考语义校验的定位**：

语义校验的本质是什么？是要确保 AI 生成的内容符合某种质量标准或业务要求。

但 AI（Claude）本身就是生成这些内容的，如果我们用另一个 AI 来检查，这本质上是：
- 用 AI 检查 AI
- 增加了调用成本
- 可能引入新的不确定性

也许更好的思路是：

1. **在节点设计阶段解决**：
   - 节点的系统提示词中明确定义输出要求
   - 包括结构要求和语义要求
   - Claude 作为执行者，应该能满足这些要求

2. **结构校验作为硬性约束**：
   - contract-validator.py 做结构校验
   - 结构不对就失败，节点需要重试

3. **语义问题通过工作流设计解决**：
   - 如果某个输出需要审查，设计一个"审查节点"来检查前一个节点的输出
   - 这样在工作流层面处理，而不是依赖 hook 机制

4. **或者让节点自检**：
   - 在系统提示词中要求节点先校验再输出
   - 这样把责任放在节点本身，不依赖外部 hook

现在我想把这些方案分享给用户，听听他怎么看。

**A:** 我的想法：

## prompt hook 做语义校验的核心问题

1. **静态 vs 动态**：hook 配置是静态的，但语义校验需求是动态的（不同节点、不同契约）
2. **信息传递断层**：`$ARGUMENTS` 只有 hook 输入，无法获取契约中的 `semantic_check` 内容
3. **全局 vs 局部**：一个 hook 配置影响所有节点，无法精确控制

## 重新思考语义校验的定位

**本质问题**：我们想用 AI 检查 AI 的输出。但：
- 节点执行者本身就是 Claude
- 节点的系统提示词已经定义了输出要求（包括语义层面）
- Claude 应该能在输出时就满足这些要求

**也许语义校验不应该是 hook 机制的一部分，而是：**

| 方式 | 说明 |
|------|------|
| **节点自检** | 节点提示词中要求"输出前先自检是否符合要求" |
| **审查节点** | 工作流中设计专门的审查节点，检查前序输出 |
| **人工介入** | 关键输出标记为需要人工确认 |

**contract-validator.py 的定位**：
- 只做**结构校验**（JSON Schema）
- 作为硬性约束的"最后防线"
- 语义质量由节点设计保证，不由 hook 保证

你怎么看这个方向？

**U:** 执行者往往需要和校验者分离

**A:** 💭用户提出了一个重要的设计原则：执行者和校验者应该分离。这是对的：

1. **自己检查自己的问题**：
   - 节点自检可能有盲点
   - 容易"自我感觉良好"
   - 缺乏客观性

2. **分离的好处**：
   - 独立视角
   - 更严格的标准
   - 可追溯的校验记录

那问题就变成了：**如何在 Claude Code 的架构下实现执行者和校验者的分离？**

可能的方案：

1. **审查节点模式**：
   - 工作流中显式添加审查节点
   - 节点A → 审查节点 → 节点B
   - 审查节点是一个独立的 agent，专门负责检查
   - 这确实是执行者和校验者分离

2. **contract-validator.py 作为校验者**：
   - 对于结构校验，脚本就是独立的校验者 ✅
   - 对于语义校验，脚本需要调用 LLM
   - 这样 LLM 调用是在脚本的上下文中，不是在节点的上下文中
   - 实现了分离

3. **两阶段 hook**：
   - 第一阶段：contract-validator.py 做结构校验
   - 第二阶段：如果需要语义校验，脚本调用 LLM API
   - 这样语义校验的 LLM 是"校验者"，与节点执行的 LLM 是分离的
   - 语义校验需要 contract-validator.py 能够调用 LLM API，从环境变量获取 API key，从契约文件加载 semantic_check 的 prompt，然后脚本加载 prompt 并调用 API
   - 这样执行者是节点 agent（Claude），结构校验者是 contract-validator.py（脚本），语义校验者是脚本调用的另一个 LLM

（Claude 实例）

**A:** 你说得对。执行者和校验者分离是重要的设计原则：

- 自己检查自己容易有盲点
- 缺乏客观性
- "既当运动员又当裁判"

## 如何实现分离？

**结构校验**：已经分离 ✅
- 执行者：节点 agent（Claude）
- 校验者：contract-validator.py（脚本）

**语义校验**：需要独立的校验者

| 方案 | 执行者 | 校验者 | 说明 |
|------|--------|--------|------|
| **审查节点** | 节点 A | 审查节点（另一个 agent） | 工作流层面的分离 |
| **脚本调 LLM** | 节点 agent | contract-validator.py 调用的 LLM | hook 层面的分离 |

### 方案：contract-validator.py 负责所有校验（包括语义）

```
节点执行 (Claude A)
    ↓
SubagentStop 触发
    ↓
contract-validator.py
    ├── 结构校验：JSON Schema
    └── 语义校验：调用 LLM API (Claude B)
```

这样：
- 节点 Claude 是执行者
- 脚本调用的 Claude 是校验者
- 完全分离，独立上下文

**需要**：
- 契约文件中定义 `semantic_check` prompt
- 脚本读取 prompt，调用 Anthropic API
- API key 从环境变量获取

你觉得这个方向可行吗？

**U:** 脚本已经是在 claude 的环境中运行了，我觉得可以在脚本内部直接调用 claude 进行语义校验。

**A:** 💭用户提出了一个很好的观点：脚本是在 Claude Code 的环境中运行的，所以可以直接利用这个环境来调用 Claude 进行语义校验，而不需要单独配置 API key 或调用外部 API。

这让我想到几种可能的实现方式：

1. **使用 Claude Code 的 CLI**：
   - 脚本内部调用 `claude` 命令
   - 比如 `echo "prompt" | claude --print`
   - 利用已有的认证环境

2. **使用子进程调用 claude**：
   - `subprocess.run(['claude', '-p', 'prompt'])`
   - 获取输出作为校验结果

3. **通过某种内部机制**：
   - Claude Code 可能提供了某种方式让 hook 脚本调用 LLM
   - 需要查看是否有这样的机制

这个方案的优点：
- 不需要额外的 API key 配置
- 利用 Claude Code 已有的环境和认证
- 执行者和校验者仍然是分离的（不同的 Claude 调用）
- 实现相对简单

让我确认一下这个思路，并讨论具体的实现方式。

**A:** 这个思路很好！脚本在 Claude Code 环境中运行，可以直接调用 `claude` CLI：

```python
# contract-validator.py 中的语义校验

import subprocess
import json

def semantic_validate(data, semantic_check_prompt):
    """调用 claude 进行语义校验"""
    
    full_prompt = f"""根据以下标准检查数据，返回 JSON 格式结果：
{{"ok": true}} 或 {{"ok": false, "reason": "具体原因"}}

检查标准：
{semantic_check_prompt}

待检查数据：
{json.dumps(data, ensure_ascii=False, indent=2)}
"""
    
    result = subprocess.run(
        ['claude', '-p', full_prompt, '--output-format', 'json'],
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)
```

**优点**：
- 无需额外 API key 配置
- 利用 Claude Code 已有的认证环境
- 执行者和校验者完全分离（不同的 Claude 调用，不同的上下文）
- 按需触发（只有契约定义了 `semantic_check` 才调用）

**contract-validator.py 的完整流程**：
```
1. 读取契约文件
2. 结构校验（JSON Schema）
   ↓ 通过
3. 有 semantic_check？
   ├── 否 → 通过
   └── 是 → 调用 claude CLI 进行语义校验
        ↓
4. 返回最终结果
```

要更新文档中的 contract-validator.py 设计吗？

**U:** 待检查数据不一定是结构化的吧

**A:** 💭用户指出了一个重要的点：待检查的数据不一定是结构化的。

回顾之前的讨论，契约校验有两种场景：
1. 结构化数据：JSON、YAML 等，可以用 JSON Schema 校验
2. 非结构化数据：Markdown 报告、纯文本输出等

如果是非结构化数据（比如 Markdown 报告、自然语言回复）：
- 没有 JSON Schema 可以校验
- 主要依赖语义校验
- 数据本身就是文本，不需要 `json.dumps`

所以 semantic_validate 函数应该能处理任意类型的数据，不只是 JSON：

```python
def semantic_validate(data, semantic_check_prompt):
    """调用 claude 进行语义校验"""
    
    # data 可能是字符串（Markdown、纯文本）或结构化数据
    if isinstance(data, str):
        data_str = data
    else:
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    full_prompt = f"""...
待检查内容：
{data_str}
"""
```

而且，对于非结构化数据的契约，可能：
- 没有 `schema` 字段（因为无法用 JSON Schema 校验）
- 只有 `semantic_check` 字段
- 或者有一个简单的类型检查（如"必须是非空字符串"）

这意味着契约文件的结构可能需要更灵活：

```yaml
# 结构化数据契约


name: analysis-result
schema:
  type: object
  required: [summary, issues]
  ...
semantic_check: |
  检查 summary 是否准确...

# 非结构化数据契约
name: report-output
# 没有 schema，或者只有基本的类型约束
type: text  # 或 markdown
semantic_check: |
  检查报告是否包含以下章节...
  检查语言是否通顺...
```

对于非结构化数据，契约校验的重点转向语义层面。结构化数据可以同时使用 schema 和语义校验，而纯文本或 Markdown 输出则主要依赖 Claude 的语义理解来验证内容的正确性、完整性和质量。

**A:** 对，数据可能是：

| 类型 | 例子 | 结构校验 | 语义校验 |
|------|------|----------|----------|
| 结构化 | JSON、YAML | JSON Schema | 可选 |
| 半结构化 | Markdown 报告 | 简单检查（非空、长度） | 主要依赖 |
| 纯文本 | 摘要、回复 | 基本检查 | 主要依赖 |

**契约文件需要更灵活**：

```yaml
# 结构化数据契约
name: analysis-result
schema:
  type: object
  required: [summary, issues]
  properties: ...
semantic_check: |
  检查 summary 是否准确概括了 issues...

# 非结构化数据契约（如 Markdown 报告）
name: design-report
content_type: markdown
basic_check:
  min_length: 500
  required_sections:
    - "## 概述"
    - "## 设计方案"
semantic_check: |
  检查报告是否完整回答了设计问题...
  检查方案是否具有可行性...
```

**semantic_validate 处理任意数据**：

```python
def semantic_validate(data, semantic_check_prompt):
    # data 可能是字符串或结构化数据
    if isinstance(data, str):
        data_repr = data
    else:
        data_repr = json.dumps(data, ensure_ascii=False, indent=2)
    
    prompt = f"""检查标准：
{semantic_check_prompt}

待检查内容：
{data_repr}
"""
    # 调用 claude...
```

需要更新契约结构定义，支持非结构化数据吗？

**U:** 契约中，结构化校验本来就是可选项

**A:** 💭用户指出契约中结构化校验本来就是可选的。这是对的，我之前的设计中 `schema` 字段已经是可选的。让我重新审视契约结构：

```yaml
name: xxx
description: xxx

# 可选：结构校验
schema: ...

# 可选：自定义校验脚本
validator_script: ...

# 可选：语义校验
semantic_check: ...
```

所有校验层都是可选的，契约可以只有其中一种或几种：
- 纯结构校验的契约：只有 schema
- 纯语义校验的契约：只有 semantic_check
- 混合校验的契约：schema + semantic_check
- 复杂校验的契约：schema + validator_script + semantic_check

用户的意思是我不需要为非结构化数据专门设计一种新的契约格式（如 `content_type: markdown`），因为契约本身就是灵活的——不需要 schema 就不写 schema。

所以契约结构应该保持简单：

```yaml
name: xxx
description: xxx

schema: ...           # 可选
validator_script: ... # 可选  
semantic_check: ...   # 可选

examples: ...
```

对于非结构化数据，契约可能只有：
```yaml
name: design-report
description: 设计报告输出规范

semantic_check: |
  检查报告是否包含概述、设计方案、实现计划等章节
  检查内容是否完整、逻辑是否清晰
```

这样更简洁，不需要引入新的字段如 `content_type`、`basic_check` 等。


这个思路是对的。

**A:** 对，你说得对。契约结构本来就是灵活的：

```yaml
name: xxx
description: xxx

schema: ...           # 可选
validator_script: ... # 可选  
semantic_check: ...   # 可选

examples: ...
```

**不同场景的契约**：

```yaml
# 纯结构校验
name: api-response
schema:
  type: object
  required: [status, data]
  ...

# 纯语义校验（非结构化输出）
name: design-report
semantic_check: |
  检查报告是否包含概述、设计方案、实现计划
  检查逻辑是否清晰、方案是否可行

# 混合校验
name: analysis-result
schema:
  type: object
  required: [summary, issues]
  ...
semantic_check: |
  检查 summary 是否准确概括了 issues
```

不需要额外的字段如 `content_type`、`basic_check`，保持简洁。

**contract-validator.py 的逻辑**：

```python
# 有 schema → 做结构校验
# 有 validator_script → 执行自定义校验
# 有 semantic_check → 调用 claude 做语义校验
# 全部通过 → 返回成功
```

这样理解对吗？

**U:** yes！

**A:** 💭用户确认了这个理解。现在我们对契约校验有了清晰的设计：

1. 契约结构：schema、validator_script、semantic_check 都是可选的
2. contract-validator.py 按顺序执行存在的校验
3. 语义校验通过脚本内部调用 claude CLI 实现，实现执行者和校验者的分离

现在应该更新文档，把这些设计固化下来。需要更新的内容：
1. 契约文件结构（确认各字段都是可选的）
2. contract-validator.py 的工作流程（包括语义校验的实现方式）

让我问用户是否要更新文档。

**A:** 现在契约校验的设计清晰了：

**契约结构**：
- `schema` - 可选，JSON Schema 结构校验
- `validator_script` - 可选，自定义 Python 脚本
- `semantic_check` - 可选，语义校验 prompt

**contract-validator.py 流程**：
```
1. 读取契约文件
2. schema 存在？→ JSON Schema 校验
3. validator_script 存在？→ 执行自定义脚本
4. semantic_check 存在？→ 调用 claude CLI 语义校验
5. 全部通过 → 成功
```

**关键设计决策**：
- 语义校验通过脚本内部调用 `claude` CLI 实现
- 执行者（节点 agent）和校验者（脚本调用的 claude）分离
- 按需触发，只有契约定义了相应字段才执行对应校验

要更新需求文档吗？

**U:** yes！

**A:** 💭用户同意更新文档。我需要：
1. 更新契约文件结构，确认各字段都是可选的
2. 更新 contract-validator.py 的工作流程，包括语义校验通过调用 claude CLI 实现

让我先读取当前文档的相关部分，然后进行更新。

**A:** [🔧 TodoWrite]

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭I need to find the contract structure definition and the contract-validator.py section. Let me search for them.

**A:** [🔍 Grep(`契约文件结构|semantic_check|validato`)]

**A:** 💭Let me read the contract structure section to see what needs to be updated.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭Good, I found the contract file structure section (lines 712-771). Now I need to:
1. Update the contract file structure to clearly indicate all fields are optional
2. Update the semantic_check section to explain it's implemented via calling claude CLI

Let me also find the contract-validator.py section to update it.

**A:** [🔍 Grep(`^## 3\. contract-validator|con`)]

**A:** 💭Let me read the contract-validator.py section to understand its current structure and update it.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭Now I have a good understanding of the current document structure. I need to make two key updates:

1. Update the contract file structure section (around line 712-771) to:
   - Clearly indicate that schema, validator_script, and semantic_check are all optional
   - Add explanation for how semantic_check is implemented (via calling claude CLI)

2. Update the contract-validator.py section (around line 521-656) to:
   - Add semantic_check to the workflow
   - Explain that semantic_check is executed by calling claude CLI within the script

Let me start with the first update - the contract file structure section.

**A:** Now I'll update the contract file structure to clarify all fields are optional and explain semantic_check implementation.

**A:** [✂️ Edit(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭Good, the first part is updated. Now I need to update the contract-validator.py section to explain how semantic_check is implemented via calling claude CLI. Let me update the workflow section (3.6) and add details about semantic validation.

**A:** [🔧 TodoWrite]

**A:** [✂️ Edit(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭Good, both updates are complete. Let me mark the todo as done and summarize for the user.

**A:** [🔧 TodoWrite]

**A:** 💭All updates are complete. Let me summarize for the user.

**A:** 文档已更新完成。主要更新内容：

**1. 契约文件结构（Section 4.3）**：
- 明确所有校验字段（schema、validator_script、semantic_check）均为可选
- 添加字段说明表格
- 添加不同类型契约的示例（纯结构、纯语义、混合）
- 更新校验执行顺序流程图

**2. contract-validator.py（Section 3.6-3.9）**：
- 更新工作流程，体现分层校验逻辑
- 新增 **3.7 语义校验实现**：
  - 设计原则：执行者与校验者分离
  - 实现方式：调用 `claude` CLI
  - 示例代码
- 更新设计要点，增加"分层校验"和"执行者/校验者分离"

**关键设计决策已固化**：
```
契约校验流程：
1. schema 存在？→ JSON Schema 结构校验
2. validator_script 存在？→ 执行自定义脚本
3. semantic_check 存在？→ 调用 claude CLI 语义校验
4. 全部通过 → 成功
```

还有其他需要补充或修改的吗？

**U:** 接下来我想看看 ## 5. node-builder (Agent)

**A:** 💭用户想查看 node-builder (Agent) 的部分。让我读取这部分内容。

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭Let me continue reading to see the rest of the node-builder section.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭Now I have the complete node-builder section. Let me present it to the user and wait for their feedback or questions.

**A:** 这是 node-builder 的完整内容：

---

## 5. node-builder (Agent)

### 5.1 功能定义

**用途**：根据节点设计文档创建 cc-wf-node (Subagent)。

**类型**：Subagent

### 5.2 输入

**输入来源**：`02-nodes-design.md` 中的单个节点章节

```markdown
## Node: {node-name}

### 基本信息
- **名称**: {node-name}
- **职责**: {responsibility}
- **模型**: {model}

### 输入输出
- **输入**: {input-description}
- **输出**: {output-path}
- **输入契约**: {input-contract}
- **输出契约**: {output-contract}

### 绑定技能
- @skills/{skill-name}

### 工具需求
- {tool-1}
- {tool-2}

### 触发示例
<example>
Context: {context}
user: "{user-request}"
assistant: "{assistant-response}"
</example>
```

### 5.3 输出

```
agents/{node-name}.md
```

**文件结构**：
```yaml
---
name: node-identifier
description: Use this agent when [触发条件].

<example>
Context: [场景描述]
user: "[用户请求]"
assistant: "[智能体响应]"
<commentary>
[触发原因说明]
</commentary>
</example>

model: inherit
color: blue
tools: ["Read", "Write", "Grep"]

# 契约配置（供 contract-validator.py 解析）
input_contract: {contract-name}   # 可选
output_contract: {contract-name}  # 可选
---

You are [角色描述]...

**Your Core Responsibilities:**
1. [职责1]
2. [职责2]

**Process:**
1. [步骤1]
2. [步骤2]

**Output Format:**
[输出格式说明]
```

### 5.4 技术规范

- **model**: inherit
- **tools**: `["Read", "Write", "Edit", "Glob", "Grep"]`
- **绑定技能**: `@skills/agent-development`

### 5.5 设计要点

1. **单一职责**：一个节点完成一个明确的任务
2. **契约意识**：系统提示词中明确说明输入输出契约
3. **强触发示例**：description 包含 2-4 个具体的触发示例
4. **最小权限**：只授予完成任务必需的工具

---

有什么问题或需要修改的地方吗？

**U:** 两个消息：
1. 好消息！我在查看文档 docs/ref/ref-claude-code-subagents.md 第 208 行时，发现可以专门为 subagent 配置 hook，我们此前大费周章设置的契约校验钩子脚本可以简化了
2. node-builder 的输出中，没有提到 skill 和 hook 的信息

**A:** 💭用户提出了两个重要的点：

1. **好消息**：可以专门为 subagent 配置 hook，这意味着契约校验可以简化！之前我们担心 SubagentStop hook 是全局的，会对所有 subagent 触发。如果可以为特定 subagent 配置 hook，那就可以只在需要契约校验的节点上触发。

2. **问题**：node-builder 的输出中没有提到 skill 和 hook 的信息。节点可能需要绑定技能，也可能需要配置自己的 hook（比如契约校验）。

让我先查看一下 ref-claude-code-subagents.md 的第 208 行附近，了解 subagent 专属 hook 的配置方式。

**A:** 这是好消息！让我查看一下 subagent 专属 hook 的配置方式。

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/ref/ref-claude-code-subagents.md)]

**A:** 💭这是非常重要的发现！subagent 的 frontmatter 可以包含：
1. `skills` - 加载到 subagent 上下文中的技能
2. `hooks` - 专门为这个 subagent 配置的生命周期钩子

这意味着：
1. **契约校验可以简化**：不需要在全局 settings.json 中配置 SubagentStop hook，而是可以在每个节点的 agent 文件中配置自己的 hook。这样只有定义了 hook 的节点才会触发校验。

2. **node-builder 的输出需要更新**：需要包含 `skills` 和 `hooks` 字段。

让我继续查看更多关于 subagent hooks 的信息。

**A:** [🔍 Grep(`Define hooks for subagents|sub`)]

**A:** 💭Let me read more about hooks in subagent frontmatter.

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/ref/ref-claude-code-subagents.md)]

**A:** 💭这是非常重要的发现！

**关键点**：

1. **Subagent frontmatter 可以定义 hooks**：
   - `PreToolUse` - 工具使用前
   - `PostToolUse` - 工具使用后
   - `Stop` - subagent 结束时（自动转换为 SubagentStop）

2. **这意味着契约校验可以简化**：
   - 每个节点 agent 可以在自己的 frontmatter 中定义 `Stop` hook
   - 只有定义了 hook 的节点才会触发校验
   - 不需要全局配置！

3. **node-builder 的输出需要更新**：
   - 添加 `skills` 字段（加载技能）
   - 添加 `hooks` 字段（契约校验）

**新的设计**：

```yaml
---
name: analyzer
description: ...
tools: [...]
skills:
  - "@skills/analysis"

# 契约校验 hook
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py"

# 契约配置
input_contract: analysis-input
output_contract: analysis-result
---
```

这样：
1. 节点自带契约校验 hook
2. 只有定义了 output_contract 的节点才需要 Stop hook
3. contract-validator.py 还是全局脚本，但只被需要校验的节点触发

让我向用户确认这个理解，并讨论如何更新文档。

**A:** 太好了！这是重要发现：

## 发现 1：Subagent 可以定义自己的 hooks

**frontmatter 支持的 hook 事件**：
| Event | 触发时机 |
|-------|----------|
| `PreToolUse` | subagent 使用工具前 |
| `PostToolUse` | subagent 使用工具后 |
| `Stop` | subagent 结束时（自动转换为 SubagentStop） |

**简化后的契约校验方案**：

```yaml
---
name: analyzer
description: ...
tools: [...]

# 绑定技能
skills:
  - "@skills/analysis"

# 契约校验 hook（只在此节点触发）
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py"

# 契约配置
input_contract: analysis-input
output_contract: analysis-result
---
```

**优点**：
- 不需要全局配置 SubagentStop hook
- 只有定义了 `output_contract` 的节点才配置 Stop hook
- 按需触发，精确控制

---

## 发现 2：node-builder 输出需要补充

当前缺失：
1. `skills` - 绑定的技能列表
2. `hooks` - 节点专属的 hook 配置

需要更新 node-builder 的输出格式。要现在更新吗？

**U:** 回顾我们此前的契约校验逻辑，看看哪里需要修改

**A:** 💭用户让我回顾此前的契约校验逻辑，看看哪些地方需要修改。让我梳理一下：

**之前的设计**（基于全局 settings.json 配置）：

1. **触发方式**：在 settings.json 中配置全局的 SubagentStop hook
2. **问题**：每个 subagent 结束都会触发，无法按需触发
3. **数据获取**：
   - SubagentStop 提供 agent_id 和 agent_transcript_path
   - 通过 prompt 匹配获取 subagent_type
   - 从 subagent_type 定位 agent 配置文件
   - 从 agent 配置的 frontmatter 获取 output_contract
   - 加载契约文件进行校验

**新的发现**：
1. Subagent 可以在 frontmatter 中定义自己的 hooks
2. Stop hook 会自动转换为 SubagentStop
3. 只有定义了 hook 的节点才会触发

**需要修改的地方**：

1. **触发方式变化**：
   - 不再需要全局 settings.json 配置
   - 每个节点在自己的 frontmatter 中定义 Stop hook
   - 只有有契约的节点才配置 hook

2. **数据获取可能简化**：
   - 因为 hook 是在节点 agent 文件中定义的
   - contract-validator.py 可以直接知道是哪个节点触发的吗？
   - 需要验证：Stop hook 的输入是否包含节点信息
   
contract-validator.py 的工作流程需要调整——之前依赖 prompt 匹配来识别 subagent_type，现在可能有更直接的方式，或者这个逻辑仍然是必需的。node-builder 需要生成 skills 和 hooks 字段，特别是当节点有 output_contract 时。cc-settings-builder 可能不再需要配置全局的 SubagentStop hook，需要检查是否还有其他必要的配置。

**A:** 让我回顾一下契约校验相关的设计，看看需要修改哪些地方。

**A:** [🔧 TodoWrite]

**A:** [🔍 Grep(`SubagentStop|settings\.json.*h`)]

**A:** 💭现在让我整理一下需要修改的地方：

**当前设计（需要修改的部分）**：

1. **Section 3.1 contract-validator.py**：
   - 当前说"在 settings.json 的 hooks 字段中配置"
   - 需要改为：可以在节点 agent 文件的 frontmatter 中配置 Stop hook

2. **Section 3.2 触发时机**：
   - 当前列出了 4 种事件
   - SubagentStop 的触发方式需要更新：从全局配置改为节点级配置

3. **SubagentStop 数据获取方式**：
   - 当前通过 prompt 匹配获取 subagent_type
   - 如果 hook 是在节点 frontmatter 中定义的，可能有更简单的方式？
   - 需要验证：节点级 Stop hook 的输入是否与全局 SubagentStop 相同

4. **契约定位流程**：
   - 当前需要从 subagent_type 定位到 agent 配置文件
   - 如果 hook 在节点自己的文件中，可能可以简化

5. **cc-settings-builder (Section 7)**：
   - 当前生成的 settings.json 包含全局的 SubagentStop hook
   - 需要移除或简化

6. **node-builder (Section 5)**：
   - 输出格式需要添加 skills 和 hooks 字段
   - 当有 output_contract 时，生成 Stop hook 配置

让我也检查一下 cc-settings-builder 的部分。

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭现在我有了完整的图景。让我整理需要修改的内容：

**需要修改的地方**：

## 1. contract-validator.py (Section 3)

**当前**：
- 3.1 说"在 settings.json 的 hooks 字段中配置"
- 3.2 触发时机包含 SubagentStop（全局配置）
- 数据获取需要通过 prompt 匹配

**修改方向**：
- **节点输出校验**：改为在节点 agent frontmatter 中配置 Stop hook
- **工作流级校验**（UserPromptSubmit, Stop）：仍然在 settings.json 中全局配置
- **节点输入校验**（PreToolUse Task）：仍然在 settings.json 中全局配置

**简化**：
- 节点级 Stop hook 触发时，contract-validator.py 可能不需要复杂的 prompt 匹配逻辑
- 但需要验证：节点 frontmatter 中的 Stop hook 输入格式是什么？

实际上，根据文档：
> Stop hooks in frontmatter are automatically converted to SubagentStop events.

所以输入格式应该和全局 SubagentStop 一样，包含 agent_id 和 agent_transcript_path。

**但有一个关键区别**：
- 节点级 Stop hook 只在该节点结束时触发
- contract-validator.py 可以假设：当前触发的就是这个节点
- 但 contract-validator.py 仍然需要知道是哪个契约要校验

**思考**：contract-validator.py 如何知道要校验哪个契约？


关键是确定校验的契约类型。可以通过 prompt 匹配获取 subagent_type，然后查询 agent 配置找到对应的契约名。或者在 hook 命令中直接传递契约参数，比如 `contract-validator.py --contract analysis-result`，但这会增加配置复杂度。还有一种方式是从 agent_transcript_path 推导契约信息。

我倾向于第一种方案——保持现有逻辑不变，只调整触发的范围。

对于 cc-settings-builder 的修改，需要从 settings.json 中移除全局的 SubagentStop hook 配置，改为在节点级别处理。当前配置包含 UserPromptSubmit、PreToolUse 和 Stop 等 hook，SubagentStop 的 contract-validator.py 调用应该被删除。

不过 wf-state.py 仍然保留 SubagentStop 配置，因为状态追踪依然需要全局监听。

node-builder 需要在输出的 frontmatter 中新增 skills 字段，并在存在 output_contract 时自动配置 Stop hook。

wf-state.py 继续维持全局 SubagentStop hook 用于追踪各节点的执行状态。

**A:** 整理一下需要修改的地方：

## 修改清单

### 1. contract-validator.py (Section 3)

**当前**：所有事件都在 settings.json 全局配置

**修改**：区分触发层级

| 事件 | 配置位置 | 说明 |
|------|----------|------|
| UserPromptSubmit | settings.json（全局） | 工作流输入校验 |
| PreToolUse (Task) | settings.json（全局） | 节点输入校验 |
| **SubagentStop** | **节点 frontmatter** | **节点输出校验（改为节点级）** |
| Stop | settings.json（全局） | 工作流输出校验 |

**数据获取逻辑**：基本不变，仍然通过 prompt 匹配获取 subagent_type

---

### 2. cc-settings-builder (Section 7)

**当前 settings.json 包含**：
```json
"SubagentStop": [
  {
    "hooks": [
      { "command": "contract-validator.py" },  // ← 移除
      { "command": "wf-state.py" }             // ← 保留
    ]
  }
]
```

**修改**：SubagentStop 中移除 contract-validator.py，保留 wf-state.py（状态追踪仍需全局）

---

### 3. node-builder (Section 5)

**当前输出**：
```yaml
---
name: analyzer
input_contract: xxx
output_contract: xxx
---
```

**修改后**：
```yaml
---
name: analyzer
skills:
  - "@skills/analysis"
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py"
input_contract: xxx
output_contract: xxx
---
```

> 只有定义了 output_contract 的节点才生成 Stop hook

---

### 4. wf-state.py (Section 8)

**不变**：保持全局 SubagentStop 配置，用于追踪所有节点状态

---

这样理解对吗？要开始更新文档吗？

**U:** 1. wf-state.py 可以在 posttooluse 触发，这里才是 subagent 真正结束的地方 2. 该文档好好对照此前的契约设计，不要遗漏重要细节

**U:** [Request interrupted by user]

**U:** 1. wf-state.py 可以在 posttooluse 触发，这里才是 subagent 真正结束的地方 2. 改文档前好好对照此前的契约设计，不要遗漏重要细节

**A:** 💭用户提出了两个重要的点：

1. **wf-state.py 可以在 PostToolUse 触发**：
   - 之前的触发顺序是：PreToolUse → SubagentStop → PostToolUse
   - SubagentStop 触发时 tool_result 还没写入
   - PostToolUse 触发时 tool_result 已经写入了
   - 所以 wf-state.py 用 PostToolUse (Task) 来记录节点完成更合适
   - 这样就不需要全局的 SubagentStop hook 了！

2. **改文档前仔细对照此前的契约设计**：
   - 用户提醒我不要遗漏重要细节
   - 我需要重新阅读契约相关的设计，确保理解完整

让我重新梳理一下：

**Hook 触发顺序**：
1. PreToolUse (Task) - 节点即将启动
2. 节点执行中...
3. SubagentStop (或节点 frontmatter 中的 Stop) - 节点准备结束，但 tool_result 还没写入
4. PostToolUse (Task) - 节点已结束，tool_result 已写入

**契约校验**：
- 节点输出校验需要在节点结束时触发
- 使用节点 frontmatter 中的 Stop hook
- 触发时机：SubagentStop（Stop 自动转换）
- 此时 tool_result 还没写入，需要从 agent_transcript_path 读取输出

**状态追踪**：
- wf-state.py 需要记录节点开始和结束


- 开始时用 PreToolUse (Task)，结束时用 PostToolUse (Task)，这样能获取完整的节点信息

这样的话，全局 SubagentStop 配置就可以移除了。契约校验由各节点的 frontmatter Stop hook 负责，状态追踪由 PreToolUse 和 PostToolUse 配合完成。现在需要重新检查文档中关于契约设计的部分，确保没有遗漏任何细节。

**A:** 你说得对！让我重新梳理：

**Hook 触发顺序**：
```
PreToolUse (Task) → 节点执行 → SubagentStop → PostToolUse (Task)
                                    ↑              ↑
                            tool_result 未写入   tool_result 已写入
```

**修正后的设计**：

| 用途 | Hook 事件 | 配置位置 |
|------|-----------|----------|
| 节点输入校验 | PreToolUse (Task) | settings.json |
| 节点输出校验 | Stop (节点级) | 节点 frontmatter |
| 节点状态记录-开始 | PreToolUse (Task) | settings.json |
| 节点状态记录-结束 | **PostToolUse (Task)** | settings.json |
| 工作流输入校验 | UserPromptSubmit | settings.json |
| 工作流输出校验 | Stop | settings.json |

**这样 settings.json 就不需要 SubagentStop 了！**

---

让我仔细对照此前的契约设计，确保不遗漏细节。

**A:** [📖 Read(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**A:** 💭我现在看到了完整的契约校验设计。让我整理需要修改的细节：

**关键变化**：
1. SubagentStop 改为节点级 Stop hook（在节点 frontmatter 中配置）
2. wf-state.py 的 SubagentStop 改为 PostToolUse (Task)

**需要修改的内容**：

### Section 3.1
- 当前："在 settings.json 的 hooks 字段中配置"
- 修改：区分全局配置和节点级配置

### Section 3.2 触发时机
- 当前：SubagentStop 用于节点输出校验
- 修改：改为节点 frontmatter 中的 Stop hook

### Section 3.3 输入
- 事件特有字段表格：SubagentStop 的描述需要更新
- hook_event_name：节点级 Stop hook 触发时，事件名是 "Stop" 还是 "SubagentStop"？
  - 根据文档："Stop hooks in frontmatter are automatically converted to SubagentStop events"
  - 所以触发时 hook_event_name 应该还是 "SubagentStop"
  - 输入格式应该相同

### Section 3.3 SubagentStop 数据获取方式
- 这部分逻辑基本不变
- 但标题可能需要改为"节点输出校验数据获取方式"

### Section 3.4 输出 - 校验失败时的处理
- SubagentStop 行保持不变（逻辑一样，只是配置位置变了）


- 后续章节需要说明不同事件的配置位置差异，以及节点级 hook 与全局 hook 的区别。settings.json 示例中应移除 SubagentStop 中的 contract-validator.py，改为在 PostToolUse (Task) 中配置 wf-state.py。

触发时机表格也需相应调整，将 SubagentStop 改为 PostToolUse (Task)。node-builder 的输出格式需要补充 skills 字段和 hooks 字段（当存在 output_contract 时）。

**A:** [🔧 TodoWrite]

**A:** 💭Let me now create a comprehensive modification list based on my review.

**A:** 仔细对照后，整理完整的修改清单：

---

## 完整修改清单

### Section 3: contract-validator.py

**3.1 功能定义**
- 当前："在 settings.json 的 hooks 字段中配置"
- 修改：说明有两种配置位置（全局 + 节点级）

**3.2 触发时机**

| Hook 事件 | 配置位置 | 校验类型 |
|-----------|----------|----------|
| UserPromptSubmit | settings.json | 工作流输入校验 |
| PreToolUse (Task) | settings.json | 节点输入校验 |
| **Stop (节点级)** | **节点 frontmatter** | **节点输出校验** |
| Stop (全局) | settings.json | 工作流输出校验 |

> 注：节点 frontmatter 中的 Stop hook 会自动转换为 SubagentStop 事件，输入格式相同

**3.3 输入**
- hook_event_name 说明：节点级 Stop 触发时，事件名仍为 `SubagentStop`
- 数据获取逻辑不变

**3.4 输出 - 校验失败处理**
- 将表格中的 "SubagentStop" 改为 "Stop (节点级)"，逻辑不变

**3.5 契约定位流程**
- 标题改为"节点输出校验时定位契约的流程"
- 流程逻辑不变

---

### Section 5: node-builder

**5.3 输出格式需要补充**：

```yaml
---
name: analyzer
description: ...

# 绑定技能（新增）
skills:
  - "@skills/analysis"

# 契约校验 hook（新增，仅当有 output_contract 时）
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py"

# 契约配置
input_contract: analysis-input
output_contract: analysis-result

model: inherit
tools: [...]
---
```

---

### Section 7: cc-settings-builder

**settings.json 示例修改**：

```json
{
  "hooks": {
    "UserPromptSubmit": [...],  // 不变
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          { "command": "contract-validator.py" },
          { "command": "wf-state.py" }
        ]
      }
    ],
    // 移除 SubagentStop
    "PostToolUse": [           // 新增
      {
        "matcher": "Task",
        "hooks": [
          { "command": "wf-state.py" }  // 状态追踪移到这里
        ]
      }
    ],
    "Stop": [...]              // 不变
  }
}
```

---

### Section 8: wf-state.py

**8.2 触发时机修改**：

| Hook 事件 | 动作 |
|-----------|------|
| UserPromptSubmit | 检测工作流启动 |
| PreToolUse (Task) | 记录节点开始 |
| **PostToolUse (Task)** | **记录节点完成/失败**（原 SubagentStop） |
| Stop | 记录工作流完成 |

---

确认无误后开始更新文档？

**U:** 你是不是漏了契约的 semantic_check 了

**A:** 💭用户提醒我可能漏掉了 semantic_check。让我想想...

semantic_check 是契约文件中的一个可选字段，用于语义校验。之前我们讨论过：
1. semantic_check 通过 contract-validator.py 内部调用 claude CLI 实现
2. 执行者和校验者分离

在我的修改清单中，我确实没有提到 semantic_check 相关的内容。但实际上：
1. semantic_check 的设计在 Section 3.7 已经定义好了
2. 它是契约文件结构的一部分（Section 4.3）
3. 它的执行逻辑在 contract-validator.py 中

问题是：当触发方式从全局 SubagentStop 改为节点级 Stop hook 时，semantic_check 的执行逻辑会受影响吗？

让我再想想...

不会！因为：
1. contract-validator.py 是同一个脚本
2. 无论从哪里触发（全局或节点级），脚本的逻辑都一样
3. 脚本会读取契约文件，检查是否有 semantic_check 字段
4. 如果有，就调用 claude CLI 进行语义校验

所以 semantic_check 的设计不需要修改，它仍然是 contract-validator.py 工作流程的一部分。

但是...等等，用户说"漏了"，是不是指我在修改清单中没有强调这一点？或者有其他遗漏？

让我重新审视一下：


契约文件结构（Section 4.3）包含 schema、validator_script、semantic_check 三个可选字段，这些都已经在之前的讨论中明确了。contract-validator.py 的工作流程是依次检查这三个字段是否存在，然后执行相应的校验逻辑——JSON Schema 结构校验、自定义脚本执行、以及 claude CLI 语义校验。这部分的设计在现有文档中已经完整定义，不需要因为触发方式的改变而修改。

**A:** 让我确认一下 semantic_check 相关的内容：

**当前文档中已有**：
1. **契约文件结构（Section 4.3）**：semantic_check 作为可选字段 ✅
2. **contract-validator.py 工作流程（Section 3.6）**：包含 semantic_check 校验步骤 ✅
3. **语义校验实现（Section 3.7）**：通过 claude CLI 调用的详细实现 ✅

**我的理解**：
- 触发方式从全局 SubagentStop 改为节点级 Stop hook
- 但 contract-validator.py 的内部逻辑不变
- semantic_check 仍然是脚本工作流程的一部分，按需执行

你说的"漏了"是指：
1. 修改清单中需要明确说明 semantic_check 逻辑不变？
2. 还是有其他地方需要补充 semantic_check 相关的设计？

请指出具体哪里需要补充。

**U:** semantic_check 可以从校验脚本中取出来了

**A:** 💭啊，用户的意思是：既然我们现在可以为每个节点单独配置 hook，那么 semantic_check 可以不再通过 contract-validator.py 内部调用 claude CLI，而是直接使用 Claude Code 原生的 prompt hook！

之前的问题是：
- 全局配置的 prompt hook 会对所有节点触发，无法按需触发
- 所以我们选择在 contract-validator.py 内部调用 claude CLI

现在的变化：
- 每个节点可以在自己的 frontmatter 中配置 hooks
- 可以配置多个 hook，包括 command 和 prompt 类型
- 所以 semantic_check 可以直接作为 prompt hook 配置在节点 frontmatter 中！

新的设计：

```yaml
---
name: analyzer
description: ...

hooks:
  Stop:
    - hooks:
        # 结构校验（command hook）
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py"
        # 语义校验（prompt hook）- 可选
        - type: prompt
          prompt: |
            检查输出是否符合以下要求：
            - summary 是否准确概括了 issues
            - 每个 issue 的描述是否具体、可操作
            ...

output_contract: analysis-result
---
```

这样：
1. contract-validator.py 只负责结构校验（schema）和自定义脚本校验（validator_script）
2. semantic_check 直接作为 prompt hook 配置
3. 利用 Claude Code 原生的 prompt hook 机制


4. 脚本中无需再调用 claude CLI

现在的关键问题是 semantic_check 的内容应该在哪里定义。方案 A 是在契约文件中定义，由 node-builder 读取后生成到节点 frontmatter；方案 B 是直接在节点设计文档中定义。我倾向于方案 A，因为 semantic_check 本质上属于契约的一部分，应该和契约定义在一起。

这样的话，contract-validator.py 需要调整——移除 semantic_check 相关的逻辑，只保留 schema 和 validator_script 的校验。semantic_check 仍在契约文件中定义，但不再由 contract-validator.py 执行，而是由 node-builder 读取并转换为节点的 prompt hook。

**A:** 你说得对！现在节点可以单独配置 hook，semantic_check 可以直接用 Claude Code 原生的 prompt hook，不需要在脚本中调用 claude CLI 了。

**之前的问题**：全局 prompt hook 无法按需触发
**现在的解决**：节点级 prompt hook，只在该节点触发

**新的设计**：

```yaml
# 节点 agent frontmatter
---
name: analyzer
description: ...

hooks:
  Stop:
    - hooks:
        # 结构校验（command hook）
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/contract-validator.py"
        # 语义校验（prompt hook）- 从契约的 semantic_check 生成
        - type: prompt
          prompt: |
            检查输出是否符合以下要求：
            - summary 是否准确概括了 issues
            - 每个 issue 的描述是否具体、可操作

output_contract: analysis-result
---
```

**需要修改的内容**：

| 部分 | 修改 |
|------|------|
| **contract-validator.py (Section 3.6-3.7)** | 移除 semantic_check 逻辑，只做 schema + validator_script |
| **契约文件结构 (Section 4.3)** | semantic_check 仍然定义在契约中，但说明由 node-builder 生成为 prompt hook |
| **node-builder (Section 5.3)** | 读取契约的 semantic_check，生成为节点的 prompt hook |

**流程变化**：
```
契约文件定义 semantic_check
    ↓
node-builder 读取契约
    ↓
生成节点 frontmatter 中的 prompt hook
    ↓
节点结束时，Claude Code 原生执行 prompt hook
```

这样理解对吗？

**U:** yes

**A:** 💭用户确认了我的理解。现在我需要更新修改清单，加入 semantic_check 相关的变化。让我整理完整的修改清单：

1. **contract-validator.py (Section 3)**:
   - 3.1: 说明配置位置（全局 + 节点级）
   - 3.2: 触发时机表格更新
   - 3.6: 工作流程移除 semantic_check
   - 3.7: 删除整个"语义校验实现"章节，或改为说明语义校验通过节点级 prompt hook 实现
   - 3.8/3.9: 章节编号调整

2. **契约文件结构 (Section 4.3)**:
   - semantic_check 仍然定义在契约中
   - 说明它由 node-builder 读取并生成为节点的 prompt hook
   - 不再由 contract-validator.py 执行

3. **node-builder (Section 5)**:
   - 5.2 输入：需要读取契约文件获取 semantic_check
   - 5.3 输出：frontmatter 包含 skills、hooks（command + prompt）

4. **cc-settings-builder (Section 7)**:
   - 移除 SubagentStop
   - 添加 PostToolUse (Task) 用于 wf-state.py

5. **wf-state.py (Section 8)**:
   - 触发时机：SubagentStop 改为 PostToolUse (Task)

现在开始更新文档。

**A:** 好，现在整理最终的修改清单并开始更新文档。

**A:** [🔧 TodoWrite]

**A:** 💭Now let me start updating the document. First, I'll update Section 3 contract-validator.py to:
1. Update the trigger mechanism description
2. Remove semantic_check from the workflow
3. Remove or modify Section 3.7 about semantic validation implementation

Let me read the current content and make the edits.

**A:** [✂️ Edit(/home/lhy/dev/llm/claude-workflow-factory/docs/05-cc-wf-factory-requirements.md)]

**U:** [Request interrupted by user]
