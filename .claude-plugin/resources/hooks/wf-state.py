#!/usr/bin/env python3
"""
wf-state.py - 工作流状态治理 Hook 脚本

自动维护工作流执行状态文件，支持进度追踪和断点续传。

触发时机:
- UserPromptSubmit: 检测工作流启动
- PreToolUse (Task): 记录节点开始
- PostToolUse (Task): 记录节点完成/失败
- Stop: 记录工作流完成

输出:
- .context/state.md: 状态文件（Markdown + YAML frontmatter）

使用说明:
此脚本由 cc-wf-factory 生成，放置在用户工作流的 .claude/hooks/ 目录。
状态文件采用 Markdown 格式，人类可直接查看。
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


class WorkflowState:
    """工作流状态管理器"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """加载现有状态"""
        if not self.state_file.exists():
            return self._create_empty_state()

        try:
            content = self.state_file.read_text(encoding="utf-8")
            return self._parse_state_file(content)
        except Exception:
            return self._create_empty_state()

    def _create_empty_state(self) -> dict:
        """创建空状态"""
        return {
            "workflow": "",
            "status": "pending",
            "started_at": None,
            "updated_at": None,
            "completed_at": None,
            "current_node": None,
            "total_nodes": 0,
            "completed_nodes": 0,
            "nodes": {},  # {node_name: {status, started_at, completed_at, summary}}
            "logs": [],  # [{node, event, timestamp, message}]
        }

    def _parse_state_file(self, content: str) -> dict:
        """解析状态文件"""
        # 提取 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                if yaml:
                    state = yaml.safe_load(frontmatter) or {}
                else:
                    # 简单解析
                    state = {}
                    for line in frontmatter.split("\n"):
                        if ": " in line:
                            key, value = line.split(": ", 1)
                            state[key.strip()] = value.strip()

                # 确保所有必需字段存在
                base = self._create_empty_state()
                base.update(state)

                # 保留 nodes 和 logs（它们在 frontmatter 中可能不完整）
                if "nodes" not in base or not isinstance(base["nodes"], dict):
                    base["nodes"] = {}
                if "logs" not in base or not isinstance(base["logs"], list):
                    base["logs"] = []

                return base

        return self._create_empty_state()

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _get_time_display(self) -> str:
        """获取显示用时间"""
        return datetime.now().strftime("%H:%M:%S")

    def start_workflow(self, workflow_name: str, total_nodes: int = 0):
        """开始工作流"""
        now = self._get_timestamp()
        self.state["workflow"] = workflow_name
        self.state["status"] = "running"
        self.state["started_at"] = now
        self.state["updated_at"] = now
        self.state["total_nodes"] = total_nodes
        self.state["completed_nodes"] = 0
        self.state["current_node"] = None

        self._add_log("workflow", "start", f"工作流 '{workflow_name}' 启动")

    def start_node(self, node_name: str):
        """开始节点执行"""
        now = self._get_timestamp()
        self.state["current_node"] = node_name
        self.state["updated_at"] = now
        self.state["status"] = "running"

        if node_name not in self.state["nodes"]:
            self.state["nodes"][node_name] = {}

        self.state["nodes"][node_name].update({
            "status": "running",
            "started_at": now,
            "completed_at": None,
            "summary": None,
        })

        self._add_log(node_name, "start", f"节点 '{node_name}' 开始执行")

    def complete_node(self, node_name: str, success: bool = True, summary: str = ""):
        """完成节点执行"""
        now = self._get_timestamp()
        self.state["updated_at"] = now

        if node_name in self.state["nodes"]:
            self.state["nodes"][node_name].update({
                "status": "completed" if success else "failed",
                "completed_at": now,
                "summary": summary or ("执行成功" if success else "执行失败"),
            })

        if success:
            self.state["completed_nodes"] = self.state.get("completed_nodes", 0) + 1

        status_text = "完成" if success else "失败"
        self._add_log(node_name, "complete", f"节点 '{node_name}' {status_text}")

        # 如果当前节点完成，清除 current_node
        if self.state.get("current_node") == node_name:
            self.state["current_node"] = None

    def complete_workflow(self, success: bool = True):
        """完成工作流"""
        now = self._get_timestamp()
        self.state["status"] = "completed" if success else "failed"
        self.state["updated_at"] = now
        self.state["completed_at"] = now
        self.state["current_node"] = None

        status_text = "完成" if success else "失败"
        self._add_log("workflow", "complete", f"工作流 {status_text}")

    def _add_log(self, node: str, event: str, message: str):
        """添加日志条目"""
        self.state["logs"].append({
            "node": node,
            "event": event,
            "timestamp": self._get_time_display(),
            "message": message,
        })

    def save(self):
        """保存状态文件（原子写入）"""
        # 确保目录存在
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 生成文件内容
        content = self._generate_state_file()

        # 原子写入：先写入临时文件，再重命名
        fd, tmp_path = tempfile.mkstemp(
            dir=self.state_file.parent,
            prefix=".state_",
            suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            # 重命名（原子操作）
            os.replace(tmp_path, self.state_file)
        except Exception:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _generate_state_file(self) -> str:
        """生成状态文件内容"""
        # YAML frontmatter
        frontmatter = {
            "workflow": self.state.get("workflow", ""),
            "status": self.state.get("status", "pending"),
            "started_at": self.state.get("started_at"),
            "updated_at": self.state.get("updated_at"),
            "completed_at": self.state.get("completed_at"),
            "current_node": self.state.get("current_node"),
            "total_nodes": self.state.get("total_nodes", 0),
            "completed_nodes": self.state.get("completed_nodes", 0),
        }

        if yaml:
            frontmatter_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        else:
            # 简单格式化
            lines = []
            for k, v in frontmatter.items():
                if v is None:
                    lines.append(f"{k}: null")
                elif isinstance(v, str):
                    lines.append(f"{k}: {v}")
                else:
                    lines.append(f"{k}: {v}")
            frontmatter_str = "\n".join(lines)

        # 状态图标
        status_icons = {
            "pending": "⏳ 待执行",
            "running": "🔄 运行中",
            "completed": "✅ 已完成",
            "failed": "❌ 失败",
            "paused": "⏸️ 已暂停",
        }

        node_status_icons = {
            "pending": "⏳ 待执行",
            "running": "🔄 执行中",
            "completed": "✅ 完成",
            "failed": "❌ 失败",
        }

        status = self.state.get("status", "pending")
        status_display = status_icons.get(status, status)

        workflow_name = self.state.get("workflow", "unknown")
        total = self.state.get("total_nodes", 0)
        completed = self.state.get("completed_nodes", 0)
        current = self.state.get("current_node", "-")

        # Markdown 正文
        body_parts = [
            f"# 工作流执行状态",
            "",
            "## 执行概览",
            f"- **工作流**: {workflow_name}",
            f"- **状态**: {status_display}",
            f"- **进度**: {completed}/{total} 节点完成",
            f"- **当前节点**: {current or '-'}",
            "",
            "## 节点状态",
            "",
            "| 节点 | 状态 | 开始时间 | 完成时间 | 备注 |",
            "|------|------|----------|----------|------|",
        ]

        # 节点表格
        nodes = self.state.get("nodes", {})
        for node_name, node_info in nodes.items():
            node_status = node_info.get("status", "pending")
            status_icon = node_status_icons.get(node_status, node_status)
            started = node_info.get("started_at", "-")
            if started and started != "-":
                # 只显示时间部分
                started = started.split("T")[1].replace("Z", "") if "T" in started else started
            completed_at = node_info.get("completed_at", "-")
            if completed_at and completed_at != "-":
                completed_at = completed_at.split("T")[1].replace("Z", "") if "T" in completed_at else completed_at
            summary = node_info.get("summary", "-") or "-"
            body_parts.append(f"| {node_name} | {status_icon} | {started} | {completed_at} | {summary} |")

        # 如果没有节点，显示提示
        if not nodes:
            body_parts.append("| - | - | - | - | 暂无节点记录 |")

        # 执行日志
        body_parts.extend([
            "",
            "## 执行日志",
            "",
        ])

        logs = self.state.get("logs", [])
        if logs:
            # 按节点分组显示日志
            current_node = None
            for log in logs:
                node = log.get("node", "unknown")
                if node != current_node:
                    current_node = node
                    if node == "workflow":
                        body_parts.append(f"### 工作流事件")
                    else:
                        body_parts.append(f"### {node}")
                    body_parts.append("")

                timestamp = log.get("timestamp", "")
                message = log.get("message", "")
                body_parts.append(f"- **{timestamp}**: {message}")
            body_parts.append("")
        else:
            body_parts.append("暂无日志记录")
            body_parts.append("")

        # 组合完整文件
        return f"---\n{frontmatter_str}---\n\n" + "\n".join(body_parts)


def find_state_file() -> Path:
    """查找状态文件路径"""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return Path(project_dir) / ".context" / "state.md"
    return Path.cwd() / ".context" / "state.md"


def extract_node_name(tool_input: dict) -> Optional[str]:
    """从 Task 工具输入中提取节点名称"""
    return tool_input.get("subagent_type")


def extract_workflow_name(user_prompt: str) -> Optional[str]:
    """
    从用户输入中提取工作流名称

    识别模式:
    - /workflow-name
    - 执行 workflow-name 工作流
    - 运行 workflow-name
    """
    if not user_prompt:
        return None

    # 检查是否是 slash command
    if user_prompt.startswith("/"):
        # /workflow-name 或 /workflow-name args
        parts = user_prompt[1:].split(None, 1)
        if parts:
            return parts[0]

    # 其他模式暂不识别（可扩展）
    return None


def check_node_success(tool_output: Any) -> tuple[bool, str]:
    """
    检查节点执行是否成功

    Returns:
        (success, summary)
    """
    if tool_output is None:
        return True, "执行完成"

    if isinstance(tool_output, dict):
        # 检查常见的错误标识
        if tool_output.get("error"):
            return False, str(tool_output.get("error"))[:100]
        if tool_output.get("status") == "failed":
            return False, tool_output.get("message", "执行失败")[:100]
        if tool_output.get("status") == "error":
            return False, tool_output.get("message", "执行出错")[:100]

        # 尝试提取摘要
        summary = tool_output.get("summary") or tool_output.get("message") or "执行完成"
        if isinstance(summary, str) and len(summary) > 100:
            summary = summary[:97] + "..."
        return True, summary

    if isinstance(tool_output, str):
        # 检查是否包含错误关键词
        lower_output = tool_output.lower()
        if "error" in lower_output or "failed" in lower_output or "exception" in lower_output:
            return False, tool_output[:100] if len(tool_output) > 100 else tool_output
        return True, tool_output[:100] if len(tool_output) > 100 else tool_output

    return True, "执行完成"


def main():
    """主函数"""
    # 读取 stdin 输入
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        result = {
            "continue": True,
            "systemMessage": f"wf-state: 无法解析输入 ({e})",
        }
        print(json.dumps(result))
        return

    # 获取 Hook 事件信息
    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_output = input_data.get("tool_result")
    user_prompt = input_data.get("prompt", "")  # UserPromptSubmit 事件的用户输入

    # 初始化状态管理器
    state_file = find_state_file()
    state_manager = WorkflowState(state_file)

    try:
        if hook_event == "UserPromptSubmit":
            # 检测工作流启动
            workflow_name = extract_workflow_name(user_prompt)
            if workflow_name:
                state_manager.start_workflow(workflow_name)
                state_manager.save()
                result = {
                    "continue": True,
                    "systemMessage": f"wf-state: 工作流 '{workflow_name}' 已启动",
                }
            else:
                # 不是工作流命令，忽略
                result = {"continue": True}

        elif hook_event == "PreToolUse" and tool_name == "Task":
            # 记录节点开始
            node_name = extract_node_name(tool_input)
            if node_name:
                state_manager.start_node(node_name)
                state_manager.save()
                result = {
                    "continue": True,
                    "systemMessage": f"wf-state: 节点 '{node_name}' 开始执行",
                }
            else:
                result = {"continue": True}

        elif hook_event == "PostToolUse" and tool_name == "Task":
            # 记录节点完成
            node_name = extract_node_name(tool_input)
            if node_name:
                success, summary = check_node_success(tool_output)
                state_manager.complete_node(node_name, success, summary)
                state_manager.save()
                status_text = "完成" if success else "失败"
                result = {
                    "continue": True,
                    "systemMessage": f"wf-state: 节点 '{node_name}' {status_text}",
                }
            else:
                result = {"continue": True}

        elif hook_event == "Stop":
            # 记录工作流完成
            # 检查是否有失败的节点
            nodes = state_manager.state.get("nodes", {})
            has_failure = any(
                n.get("status") == "failed" for n in nodes.values()
            )
            state_manager.complete_workflow(success=not has_failure)
            state_manager.save()
            status_text = "完成" if not has_failure else "失败"
            result = {
                "continue": True,
                "systemMessage": f"wf-state: 工作流 {status_text}",
            }

        else:
            # 其他事件，忽略
            result = {"continue": True}

    except Exception as e:
        # 状态更新失败不应阻塞工作流
        result = {
            "continue": True,
            "systemMessage": f"wf-state: 状态更新失败 ({e})",
        }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
