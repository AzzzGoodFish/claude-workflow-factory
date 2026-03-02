#!/usr/bin/env python3
"""
wf-state.py - 工作流状态治理 Hook 脚本

自动维护工作流执行状态文件，支持进度追踪和断点续传。

触发时机:
- UserPromptSubmit: 检测工作流启动
- PreToolUse (Task): 记录节点开始
- PostToolUse (Task): 记录节点完成/失败，提取输出写入文件
- Stop: 记录工作流完成

输出:
- .context/state.md: 状态文件（Markdown + YAML frontmatter）
- .context/outputs/{node-name}.json: 节点原始输出
- .context/outputs/{node-name}.md: 节点可读输出

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

# 确保可以从任意工作目录导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))
from wf_output_extractor import extract_from_tool_response


def get_project_dir() -> Path:
    """获取项目目录"""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        return Path(project_dir)
    return Path.cwd()


def ensure_outputs_dir() -> Path:
    """确保输出目录存在"""
    outputs_dir = get_project_dir() / ".context" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    return outputs_dir


def write_node_output(node_name: str, tool_response: str) -> Optional[str]:
    """
    将节点输出写入文件（使用共享模块提取）

    Args:
        node_name: 节点名称
        tool_response: Task 工具返回的原始响应

    Returns:
        输出文件的相对路径（.json），若写入失败则返回 None
    """
    outputs_dir = ensure_outputs_dir()
    json_path = outputs_dir / f"{node_name}.json"
    md_path = outputs_dir / f"{node_name}.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 使用共享模块提取输出
    extraction_result = extract_from_tool_response(tool_response)

    # 写入 JSON 文件（仅当有 JSON 数据时）
    json_written = False
    if extraction_result.json_data is not None:
        try:
            json_content = json.dumps(extraction_result.json_data, ensure_ascii=False, indent=2)
            _atomic_write(json_path, json_content)
            json_written = True
        except Exception:
            pass

    # 写入 Markdown 文件（始终写入 raw_text）
    try:
        md_content = _generate_output_markdown(
            node_name,
            extraction_result.json_data if extraction_result.json_data else extraction_result.raw_text,
            timestamp,
            raw_text=extraction_result.raw_text
        )
        _atomic_write(md_path, md_content)
    except Exception:
        pass  # Markdown 写入失败不影响主流程

    # 返回相对路径（优先返回 JSON 路径）
    if json_written:
        return f".context/outputs/{node_name}.json"
    return f".context/outputs/{node_name}.md"


def _generate_output_markdown(
    node_name: str,
    output_data: Any,
    timestamp: str,
    raw_text: Optional[str] = None
) -> str:
    """
    生成节点输出的 Markdown 格式

    Args:
        node_name: 节点名称
        output_data: 结构化输出数据（JSON）
        timestamp: 时间戳
        raw_text: 原始文本内容（用于展示完整上下文）
    """
    lines = [
        f"# 节点输出: {node_name}",
        "",
        "## 元信息",
        f"- 执行时间: {timestamp}",
        "- 状态: 成功",
        "",
    ]

    # 如果有结构化数据，展示 JSON
    if isinstance(output_data, (dict, list)):
        lines.extend([
            "## 结构化数据",
            "",
            "```json",
            json.dumps(output_data, ensure_ascii=False, indent=2),
            "```",
            "",
        ])

    # 展示原始文本（如果与结构化数据不同）
    if raw_text:
        lines.extend([
            "## 原始输出",
            "",
            raw_text,
            "",
        ])
    elif output_data is None:
        lines.extend([
            "## 输出数据",
            "",
            "_无输出数据_",
            "",
        ])
    elif isinstance(output_data, str):
        lines.extend([
            "## 输出数据",
            "",
            output_data,
            "",
        ])

    return "\n".join(lines)


def _atomic_write(file_path: Path, content: str):
    """原子写入文件"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=".tmp_",
        suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


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
            "session_id": None,  # 断点恢复的关键
            "status": "pending",
            "started_at": None,
            "updated_at": None,
            "completed_at": None,
            "current_node": None,
            "progress": "0/0",
            "total_nodes": 0,
            "completed_nodes": 0,
            "outputs": {},  # {node_name: output_file_path}
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

                # 保留 nodes、logs、outputs（它们在 frontmatter 中可能不完整）
                if "nodes" not in base or not isinstance(base["nodes"], dict):
                    base["nodes"] = {}
                if "logs" not in base or not isinstance(base["logs"], list):
                    base["logs"] = []
                if "outputs" not in base or not isinstance(base["outputs"], dict):
                    base["outputs"] = {}

                return base

        return self._create_empty_state()

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _get_time_display(self) -> str:
        """获取显示用时间"""
        return datetime.now().strftime("%H:%M:%S")

    def start_workflow(self, workflow_name: str, session_id: Optional[str] = None, total_nodes: int = 0):
        """开始工作流"""
        now = self._get_timestamp()
        self.state["workflow"] = workflow_name
        self.state["session_id"] = session_id
        self.state["status"] = "running"
        self.state["started_at"] = now
        self.state["updated_at"] = now
        self.state["total_nodes"] = total_nodes
        self.state["completed_nodes"] = 0
        self.state["current_node"] = None
        self.state["progress"] = f"0/{total_nodes}"
        self.state["outputs"] = {}

        self._add_log("workflow", "start", f"工作流 '{workflow_name}' 启动")

    def start_node(self, node_name: str):
        """开始节点执行"""
        now = self._get_timestamp()
        self.state["current_node"] = node_name
        self.state["updated_at"] = now
        self.state["status"] = "running"

        # 如果是新发现的节点，增加 total_nodes 计数
        is_new_node = node_name not in self.state["nodes"]
        if is_new_node:
            self.state["nodes"][node_name] = {}
            self.state["total_nodes"] = self.state.get("total_nodes", 0) + 1
            # 更新进度显示
            total = self.state["total_nodes"]
            completed = self.state.get("completed_nodes", 0)
            self.state["progress"] = f"{completed}/{total}"

        self.state["nodes"][node_name].update({
            "status": "running",
            "started_at": now,
            "completed_at": None,
            "summary": None,
        })

        self._add_log(node_name, "start", f"节点 '{node_name}' 开始执行")

    def complete_node(self, node_name: str, success: bool = True, summary: str = "", output_path: Optional[str] = None):
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

        # 更新进度
        total = self.state.get("total_nodes", 0)
        completed = self.state.get("completed_nodes", 0)
        self.state["progress"] = f"{completed}/{total}"

        # 记录输出文件路径
        if output_path:
            self.state["outputs"][node_name] = output_path

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
        # 计算 progress
        total = self.state.get("total_nodes", 0)
        completed = self.state.get("completed_nodes", 0)
        progress = f"{completed}/{total}"

        # YAML frontmatter（按需求文档格式）
        frontmatter = {
            "workflow": self.state.get("workflow", ""),
            "session_id": self.state.get("session_id"),
            "status": self.state.get("status", "pending"),
            "started_at": self.state.get("started_at"),
            "updated_at": self.state.get("updated_at"),
            "completed_at": self.state.get("completed_at"),
            "current_node": self.state.get("current_node"),
            "progress": progress,
            "total_nodes": total,
            "completed_nodes": completed,
            "outputs": self.state.get("outputs", {}),
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
        session_id = self.state.get("session_id", "-")
        current = self.state.get("current_node", "-")
        outputs = self.state.get("outputs", {})

        # Markdown 正文
        body_parts = [
            f"# 工作流执行状态",
            "",
            "## 执行概览",
            f"- **工作流**: {workflow_name}",
            f"- **会话**: {session_id or '-'}",
            f"- **状态**: {status_display}",
            f"- **进度**: {progress} 节点完成",
            f"- **当前节点**: {current or '-'}",
            "",
            "## 节点状态",
            "",
            "| 节点 | 状态 | 开始时间 | 完成时间 | 输出 |",
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

            # 输出链接
            if node_name in outputs:
                output_link = f"[查看]({outputs[node_name]})"
            else:
                output_link = "-"
            body_parts.append(f"| {node_name} | {status_icon} | {started} | {completed_at} | {output_link} |")

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


def extract_workflow_name(user_prompt: str, expected_workflow: Optional[str] = None) -> Optional[str]:
    """
    从用户输入中提取工作流名称

    Args:
        user_prompt: 用户输入
        expected_workflow: 预期的工作流名称（从命令行参数传入）

    识别模式:
    - /workflow-name
    - /workflow-name --arg value
    """
    if not user_prompt:
        return None

    user_prompt = user_prompt.strip()

    # 检查是否是 slash command
    if not user_prompt.startswith("/"):
        return None

    # 提取命令名
    parts = user_prompt[1:].split(None, 1)
    if not parts:
        return None

    command_name = parts[0]

    # 如果指定了预期的工作流名称，检查是否匹配
    if expected_workflow:
        if expected_workflow in command_name:
            return expected_workflow
        return None

    return command_name


def parse_workflow_params(user_prompt: str) -> dict:
    """
    从用户输入中解析工作流参数

    支持格式:
    - --arg value
    - --arg=value
    - 位置参数（作为 _positional 数组）

    示例:
    /my-workflow --target src/ --format json
    -> {"target": "src/", "format": "json"}

    /my-workflow src/ --verbose
    -> {"_positional": ["src/"], "verbose": True}
    """
    params: dict = {"_positional": []}

    if not user_prompt:
        return params

    user_prompt = user_prompt.strip()

    # 跳过 slash command 部分
    if user_prompt.startswith("/"):
        parts = user_prompt[1:].split(None, 1)
        if len(parts) < 2:
            return params
        args_str = parts[1]
    else:
        args_str = user_prompt

    # 解析参数
    import shlex
    try:
        tokens = shlex.split(args_str)
    except ValueError:
        # 解析失败，使用简单分割
        tokens = args_str.split()

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.startswith("--"):
            # 长参数
            if "=" in token:
                # --arg=value 格式
                key, value = token[2:].split("=", 1)
                params[key] = value
            elif i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                # --arg value 格式
                key = token[2:]
                params[key] = tokens[i + 1]
                i += 1
            else:
                # --flag 格式（布尔标志）
                key = token[2:]
                params[key] = True
        elif token.startswith("-") and len(token) == 2:
            # 短参数 -a value
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                key = token[1:]
                params[key] = tokens[i + 1]
                i += 1
            else:
                # -f 格式（布尔标志）
                key = token[1:]
                params[key] = True
        else:
            # 位置参数
            params["_positional"].append(token)

        i += 1

    # 如果没有位置参数，删除空列表
    if not params["_positional"]:
        del params["_positional"]

    return params


def write_params_files(params: dict, workflow_name: str) -> None:
    """
    将工作流参数写入文件

    写入:
    - .context/params.json: 原始 JSON 格式
    - .context/params.md: 人类可读的 Markdown 格式
    """
    project_dir = get_project_dir()
    context_dir = project_dir / ".context"
    context_dir.mkdir(parents=True, exist_ok=True)

    json_path = context_dir / "params.json"
    md_path = context_dir / "params.md"

    # 写入 JSON 文件
    json_content = json.dumps(params, ensure_ascii=False, indent=2)
    _atomic_write(json_path, json_content)

    # 写入 Markdown 文件
    md_lines = [
        "# 工作流参数",
        "",
        f"**工作流**: {workflow_name}",
        "",
        "| 参数 | 值 |",
        "|------|-----|",
    ]

    for key, value in params.items():
        if key == "_positional":
            if value:
                md_lines.append(f"| (位置参数) | {', '.join(str(v) for v in value)} |")
        else:
            md_lines.append(f"| {key} | {value} |")

    md_lines.append("")
    _atomic_write(md_path, "\n".join(md_lines))


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


def parse_args():
    """解析命令行参数"""
    import argparse
    parser = argparse.ArgumentParser(description="工作流状态治理脚本")
    parser.add_argument("--workflow", type=str, help="工作流名称（用于命令匹配）")
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    expected_workflow = args.workflow

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
    tool_output = input_data.get("tool_response")  # PostToolUse 时的节点输出
    if tool_output is None:
        tool_output = input_data.get("tool_result")  # 兼容旧字段名
    user_prompt = input_data.get("prompt", "")  # UserPromptSubmit 事件的用户输入
    session_id = input_data.get("session_id")  # 会话 ID

    # 初始化状态管理器
    state_file = find_state_file()
    state_manager = WorkflowState(state_file)

    try:
        if hook_event == "UserPromptSubmit":
            # 检测工作流启动
            workflow_name = extract_workflow_name(user_prompt, expected_workflow)
            if workflow_name:
                # 解析工作流参数
                params = parse_workflow_params(user_prompt)

                # 写入参数文件
                write_params_files(params, workflow_name)

                # 启动工作流
                state_manager.start_workflow(workflow_name, session_id=session_id)
                state_manager.save()

                result = {
                    "continue": True,
                    "systemMessage": f"wf-state: 工作流 '{workflow_name}' 已初始化，参数已写入 .context/params.json",
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
            # 记录节点完成，提取并写入输出
            node_name = extract_node_name(tool_input)
            if node_name:
                success, summary = check_node_success(tool_output)

                # 写入节点输出文件
                output_path = None
                if success and tool_output is not None:
                    output_path = write_node_output(node_name, tool_output)

                state_manager.complete_node(node_name, success, summary, output_path=output_path)
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
