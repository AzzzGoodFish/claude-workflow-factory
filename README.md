# CC Workflow Factory

交互式工作流构建向导，帮助用户创建符合 AI 工作流设计原则的 Claude Code 标准化工作流。

## 功能概述

通过多轮对话，引导用户：

1. **理解需求** - 分析用户提供的参考资料或进行调研
2. **设计节点** - 识别和定义工作流节点
3. **编排流程** - 设计执行顺序、并行、分支、错误处理
4. **定义契约** - 设计数据结构和校验规则
5. **生成工作流** - 输出完整的工作流目录结构

## 安装

```bash
# 使用 --plugin-dir 参数测试
claude --plugin-dir /path/to/cc-wf-factory

# 或复制到 Claude Code 插件目录
cp -r cc-wf-factory ~/.claude/plugins/
```

## 使用方法

```bash
# 启动工作流工厂
/cc-wf-factory 我想创建一个代码审查工作流

# 或不带参数启动
/cc-wf-factory
```

## 交互流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                       迭代式工作流构建                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 用户描述目标 / 提供参考资料                                       │
│                                                                      │
│  2. 分析资料 (wf-resource-analyzer)                                  │
│     或调研建议 (wf-researcher)                                       │
│                                                                      │
│  3. 确认/修改节点设计                                                │
│                                                                      │
│  4. 设计流程编排 (wf-flow-designer)                                  │
│                                                                      │
│  5. 设计数据契约 (wf-contract-designer)                              │
│                                                                      │
│  6. 生成工作流 (wf-generator)                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 组件

### Commands

| 名称 | 说明 |
|------|------|
| `cc-wf-factory` | 工作流构建向导入口 |

### Skills

| 名称 | 说明 |
|------|------|
| `workflow-design` | 工作流设计知识（Contract、Node、Flow、Context） |
| `resource-analysis` | 资料分析方法论，提取工作流设计要素 |

### Agents

| 名称 | 说明 |
|------|------|
| `wf-resource-analyzer` | 分析用户提供的参考资料 |
| `wf-researcher` | 工作流调研，提供方案建议 |
| `wf-contract-designer` | 设计数据契约 |
| `wf-flow-designer` | 设计流程编排 |
| `wf-generator` | 生成完整工作流 |

### Hooks

| 事件 | 说明 |
|------|------|
| `UserPromptSubmit` | 分析用户输入类型，提供上下文提示 |

## 生成的工作流结构

```
.claude/
├── commands/
│   └── <workflow-name>.md           # 工作流入口
├── agents/
│   └── <node-name>.md               # 节点 SubAgent
├── hooks/
│   └── [Hook 配置]
└── workflows/
    └── <workflow-name>/
        ├── flow.yaml                # Flow DSL
        ├── contracts/               # 契约定义
        └── validators/              # Python 校验器
```

## 设计文档

工作流设计过程中，中间文档保存在：

```
$WORKDIR/.wf-factory/
├── design/
│   ├── overview.md         # 工作流概述
│   ├── nodes.md            # 节点定义
│   ├── flow.md             # 流程编排
│   ├── contracts.md        # 契约定义
│   └── validators.md       # 校验器规格
└── resources/              # 用户参考资料
```

## 基于的设计原则

本插件基于以下设计原则：

- **Contract (契约)** - 数据结构规范和校验
- **Nodes (节点)** - 执行单元，由 SubAgent 实现
- **Flow (流程)** - 执行控制规则
- **Context (上下文)** - 环境信息和共享状态

详见 `skills/workflow-design/references/` 目录下的参考文档。

## Flow DSL 语法

```yaml
# 顺序执行
START >> step-a >> step-b >> END

# 并行执行
START >> [collect-a, collect-b] >> merge >> END

# 条件分支
analyze ?issues >> fix >> END
analyze ?clean >> approve >> END

# 循环迭代
processor * $items[3] >> merge >> END
```

## 许可证

MIT
