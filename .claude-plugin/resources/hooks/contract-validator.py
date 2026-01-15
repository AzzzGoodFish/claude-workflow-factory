#!/usr/bin/env python3
"""
contract-validator.py - 全局契约校验 Hook 脚本

在工作流节点执行前后验证数据是否符合契约规范。

触发时机:
- PreToolUse (Task): 校验节点输入
- PostToolUse (Task): 校验节点输出
- Stop: 校验工作流最终输出

输出格式:
- 校验通过: {"status": "pass", ...}
- 校验失败: {"status": "fail", "decision": "block", "errors": [...], ...}

使用说明:
此脚本由 cc-wf-factory 生成，放置在用户工作流的 .claude/hooks/ 目录。
需要配合 .claude/contracts/mapping.yaml 和契约 Schema 文件使用。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    jsonschema = None
    validate = None
    ValidationError = None


class ContractValidator:
    """契约校验器"""

    def __init__(self, contracts_dir: Path, mapping_file: Path):
        self.contracts_dir = contracts_dir
        self.mapping_file = mapping_file
        self.mapping = self._load_mapping()

    def _load_mapping(self) -> dict:
        """加载契约映射配置"""
        if not self.mapping_file.exists():
            return {"version": "1.0", "nodes": {}}

        content = self.mapping_file.read_text(encoding="utf-8")
        if yaml:
            return yaml.safe_load(content) or {"version": "1.0", "nodes": {}}
        else:
            # Fallback: 尝试 JSON 格式
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"version": "1.0", "nodes": {}}

    def _load_contract_schema(self, contract_name: str) -> Optional[dict]:
        """加载契约 Schema"""
        # 尝试 YAML 格式
        yaml_file = self.contracts_dir / f"{contract_name}.yaml"
        if yaml_file.exists():
            content = yaml_file.read_text(encoding="utf-8")
            if yaml:
                return yaml.safe_load(content)
            else:
                return None

        # 尝试 JSON 格式
        json_file = self.contracts_dir / f"{contract_name}.json"
        if json_file.exists():
            content = json_file.read_text(encoding="utf-8")
            return json.loads(content)

        return None

    def get_contracts_for_node(
        self, node_name: str
    ) -> tuple[Optional[str], Optional[str]]:
        """获取节点的输入/输出契约名称"""
        nodes = self.mapping.get("nodes", {})
        node_config = nodes.get(node_name, {})

        input_contract = node_config.get("input")
        output_contract = node_config.get("output")

        return input_contract, output_contract

    def validate_data(
        self, data: Any, schema: dict
    ) -> tuple[bool, list[dict]]:
        """
        校验数据是否符合 Schema

        Returns:
            (is_valid, errors)
        """
        if jsonschema is None or validate is None or ValidationError is None:
            # 没有 jsonschema 库时，跳过校验
            return True, []

        errors: list[dict] = []
        try:
            validate(instance=data, schema=schema)
            return True, []
        except ValidationError as e:
            schema_dict = e.schema if isinstance(e.schema, dict) else {}
            error_detail = {
                "field": ".".join(str(p) for p in e.absolute_path) or "(root)",
                "expected": str(schema_dict.get("type", e.validator)),
                "actual": str(type(e.instance).__name__),
                "message": e.message,
            }
            errors.append(error_detail)

            # 收集所有错误（包括嵌套错误）
            for suberror in e.context:
                sub_schema = suberror.schema if isinstance(suberror.schema, dict) else {}
                sub_detail = {
                    "field": ".".join(str(p) for p in suberror.absolute_path)
                    or "(root)",
                    "expected": str(sub_schema.get("type", suberror.validator)),
                    "actual": str(type(suberror.instance).__name__),
                    "message": suberror.message,
                }
                errors.append(sub_detail)

            return False, errors


def find_contracts_dir() -> Path:
    """查找契约目录"""
    # 优先使用环境变量指定的项目目录
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        contracts_dir = Path(project_dir) / ".claude" / "contracts"
        if contracts_dir.exists():
            return contracts_dir

    # 其次尝试当前工作目录
    cwd = Path.cwd()
    contracts_dir = cwd / ".claude" / "contracts"
    if contracts_dir.exists():
        return contracts_dir

    # 最后返回默认路径（即使不存在）
    return Path(project_dir or cwd) / ".claude" / "contracts"


def extract_node_name(tool_input: dict) -> Optional[str]:
    """从 Task 工具输入中提取节点名称"""
    # Task 工具的 subagent_type 参数就是 Agent/节点名称
    return tool_input.get("subagent_type")


def extract_data_to_validate(
    hook_event: str, tool_input: dict, tool_output: Any
) -> Optional[Any]:
    """
    提取需要校验的数据

    PreToolUse: 校验 Task 的 prompt 中是否有符合契约的数据
    PostToolUse: 校验 Task 的输出结果
    """
    if hook_event == "PreToolUse":
        # 对于输入校验，我们检查 prompt 中是否包含 JSON 数据
        prompt = tool_input.get("prompt", "")
        # 尝试从 prompt 中提取 JSON
        return try_extract_json_from_text(prompt)

    elif hook_event == "PostToolUse":
        # 对于输出校验，我们检查工具输出
        if tool_output:
            # tool_output 可能直接是结果，或在某个字段中
            if isinstance(tool_output, dict):
                # 尝试常见的输出字段
                for field in ["result", "output", "data", "content"]:
                    if field in tool_output:
                        result = tool_output[field]
                        if isinstance(result, str):
                            return try_extract_json_from_text(result)
                        return result
                # 如果没有特定字段，返回整个输出
                return tool_output
            # tool_output 不是 dict 类型
            if isinstance(tool_output, str):
                return try_extract_json_from_text(tool_output)
            return tool_output

    return None


def try_extract_json_from_text(text: str) -> Optional[Any]:
    """尝试从文本中提取 JSON 数据"""
    if not text:
        return None

    # 直接尝试解析整个文本
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试查找 JSON 代码块
    import re

    json_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    matches = re.findall(json_block_pattern, text)
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue

    # 尝试查找独立的 JSON 对象
    brace_start = text.find("{")
    if brace_start >= 0:
        # 找到匹配的闭合括号
        depth = 0
        for i, char in enumerate(text[brace_start:], brace_start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start : i + 1])
                    except json.JSONDecodeError:
                        break

    return None


def generate_suggestion(errors: list[dict]) -> str:
    """生成修复建议"""
    if not errors:
        return ""

    suggestions = []
    for error in errors[:3]:  # 只取前 3 个错误
        field = error.get("field", "unknown")
        expected = error.get("expected", "unknown")
        message = error.get("message", "")

        if "required" in message.lower():
            suggestions.append(f"添加必需字段 '{field}'")
        elif "type" in message.lower():
            suggestions.append(f"将字段 '{field}' 的类型修改为 {expected}")
        elif "minLength" in message.lower() or "minimum" in message.lower():
            suggestions.append(f"确保字段 '{field}' 满足最小值/长度要求")
        else:
            suggestions.append(f"修复字段 '{field}': {message}")

    return "; ".join(suggestions)


def main():
    """主函数"""
    # 读取 stdin 输入
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        # 无法解析输入，直接通过
        result = {
            "continue": True,
            "systemMessage": f"contract-validator: 无法解析输入 ({e})",
        }
        print(json.dumps(result))
        return

    # 获取 Hook 事件信息
    hook_event = input_data.get("hook_event_name", "")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_output = input_data.get("tool_result")  # PostToolUse 时有值

    # 只处理 Task 工具调用
    if tool_name != "Task":
        result = {"continue": True}
        print(json.dumps(result))
        return

    # 提取节点名称
    node_name = extract_node_name(tool_input)
    if not node_name:
        result = {
            "continue": True,
            "systemMessage": "contract-validator: 未找到节点名称，跳过校验",
        }
        print(json.dumps(result))
        return

    # 初始化校验器
    contracts_dir = find_contracts_dir()
    mapping_file = contracts_dir / "mapping.yaml"
    validator = ContractValidator(contracts_dir, mapping_file)

    # 获取节点的契约配置
    input_contract, output_contract = validator.get_contracts_for_node(node_name)

    # 确定需要校验的契约
    check_type = "input" if hook_event == "PreToolUse" else "output"
    contract_name = input_contract if check_type == "input" else output_contract

    # 如果没有配置契约，跳过校验
    if not contract_name:
        result = {
            "continue": True,
            "systemMessage": f"contract-validator: 节点 '{node_name}' 无 {check_type} 契约配置",
        }
        print(json.dumps(result))
        return

    # 加载契约 Schema
    schema = validator._load_contract_schema(contract_name)
    if not schema:
        result = {
            "continue": True,
            "systemMessage": f"contract-validator: 未找到契约 '{contract_name}'",
        }
        print(json.dumps(result))
        return

    # 提取需要校验的数据
    data = extract_data_to_validate(hook_event, tool_input, tool_output)

    # 如果没有数据可校验，对于输入校验跳过，对于输出校验失败
    if data is None:
        if check_type == "input":
            result = {
                "continue": True,
                "systemMessage": f"contract-validator: 节点 '{node_name}' 输入中未找到 JSON 数据",
            }
        else:
            result = {
                "continue": True,
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": f"contract-validator: 节点 '{node_name}' 输出中未找到符合契约的数据",
            }
        print(json.dumps(result))
        return

    # 执行校验
    is_valid, errors = validator.validate_data(data, schema)

    if is_valid:
        # 校验通过
        result = {
            "continue": True,
            "systemMessage": f"contract-validator: 节点 '{node_name}' {check_type} 校验通过",
        }
        print(json.dumps(result))
    else:
        # 校验失败
        suggestion = generate_suggestion(errors)
        error_summary = "; ".join(e.get("message", "")[:100] for e in errors[:3])

        result = {
            "continue": True,
            "hookSpecificOutput": {"permissionDecision": "deny"},
            "systemMessage": (
                f"contract-validator: 节点 '{node_name}' {check_type} 校验失败\n"
                f"契约: {contract_name}\n"
                f"错误: {error_summary}\n"
                f"建议: {suggestion}"
            ),
        }

        # 同时输出详细错误到 stderr（会被 Claude 看到）
        detailed_error = {
            "status": "fail",
            "node": node_name,
            "check_type": check_type,
            "contract": contract_name,
            "errors": errors,
            "suggestion": suggestion,
        }
        print(json.dumps(detailed_error), file=sys.stderr)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
