#!/usr/bin/env python3
"""
contract-validator.py - 全局契约校验 Hook 脚本

在工作流节点执行前后验证数据是否符合契约规范。

触发时机:
- UserPromptSubmit: 校验工作流输入
- PreToolUse (Task): 校验节点输入
- SubagentStop: 校验节点输出
- Stop: 校验工作流输出

退出码处理:
- UserPromptSubmit/PreToolUse: exit(2) + stderr 阻止执行
- SubagentStop/Stop: exit(0) + JSON {"decision": "block", "reason": "..."} 阻止结束

使用说明:
此脚本由 cc-wf-factory 生成，放置在用户工作流的 .claude/hooks/ 目录。
需要配合 .claude/contracts/ 目录中的契约文件使用。
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn, Optional

# 确保可以从任意工作目录导入同目录下的模块
sys.path.insert(0, str(Path(__file__).parent))
from wf_output_extractor import extract_from_transcript


# 日志配置
LOG_FILE = Path(".context/contract-validator.log")


def log(level: str, message: str, **kwargs) -> None:
    """
    记录日志到 .context/contract-validator.log

    Args:
        level: 日志级别 (DEBUG, INFO, WARN, ERROR)
        message: 日志消息
        **kwargs: 额外的结构化数据
    """
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().isoformat(timespec="milliseconds")

        entry: dict[str, Any] = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
        }
        if kwargs:
            entry["data"] = kwargs

        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


try:
    import yaml
except ImportError:
    yaml = None

try:
    import jsonschema
    from jsonschema import ValidationError, validate
except ImportError:
    jsonschema = None
    validate = None
    ValidationError = None


class ContractValidator:
    """契约校验器"""

    def __init__(self, contracts_dir: Path):
        self.contracts_dir = contracts_dir

    def load_contract(self, contract_name: str) -> Optional[dict]:
        """加载契约文件"""
        yaml_file = self.contracts_dir / f"{contract_name}.yaml"
        if yaml_file.exists():
            content = yaml_file.read_text(encoding="utf-8")
            if yaml:
                return yaml.safe_load(content)
            return None

        json_file = self.contracts_dir / f"{contract_name}.json"
        if json_file.exists():
            content = json_file.read_text(encoding="utf-8")
            return json.loads(content)

        return None

    def validate_schema(self, data: Any, schema: dict) -> tuple[bool, list[dict]]:
        """
        JSON Schema 结构校验

        Returns:
            (is_valid, errors)
        """
        if jsonschema is None or validate is None or ValidationError is None:
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

            for suberror in e.context:
                sub_schema = (
                    suberror.schema if isinstance(suberror.schema, dict) else {}
                )
                sub_detail = {
                    "field": ".".join(str(p) for p in suberror.absolute_path)
                    or "(root)",
                    "expected": str(sub_schema.get("type", suberror.validator)),
                    "actual": str(type(suberror.instance).__name__),
                    "message": suberror.message,
                }
                errors.append(sub_detail)

            return False, errors

    def run_validator_script(
        self, script_path: str, data: Any
    ) -> tuple[bool, list[dict]]:
        """
        执行自定义校验脚本

        脚本接收 JSON 数据作为 stdin，输出 JSON 结果到 stdout:
        - 通过: {"valid": true}
        - 失败: {"valid": false, "errors": [...]}
        """
        full_path = self.contracts_dir / script_path
        if not full_path.exists():
            return True, []

        try:
            result = subprocess.run(
                ["python", str(full_path)],
                input=json.dumps(data),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return False, [{"message": f"校验脚本执行失败: {result.stderr}"}]

            output = json.loads(result.stdout)
            if output.get("valid", True):
                return True, []
            return False, output.get("errors", [{"message": "自定义校验失败"}])
        except subprocess.TimeoutExpired:
            return False, [{"message": "校验脚本执行超时"}]
        except Exception as e:
            return False, [{"message": f"校验脚本执行异常: {str(e)}"}]


def find_contracts_dir() -> Path:
    """查找契约目录"""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        contracts_dir = Path(project_dir) / ".claude" / "contracts"
        if contracts_dir.exists():
            return contracts_dir

    cwd = Path.cwd()
    contracts_dir = cwd / ".claude" / "contracts"
    if contracts_dir.exists():
        return contracts_dir

    return Path(project_dir or cwd) / ".claude" / "contracts"


def generate_suggestion(errors: list[dict]) -> str:
    """生成修复建议"""
    if not errors:
        return ""

    suggestions = []
    for error in errors[:3]:
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


def format_error_message(
    node_name: str, contract_name: str, errors: list[dict], check_type: str
) -> str:
    """格式化错误消息"""
    suggestion = generate_suggestion(errors)
    error_summary = "; ".join(e.get("message", "")[:100] for e in errors[:3])

    return (
        f"contract-validator: 节点 '{node_name}' {check_type} 校验失败\n"
        f"契约: {contract_name}\n"
        f"错误: {error_summary}\n"
        f"建议: {suggestion}"
    )


def block_with_exit(message: str) -> NoReturn:
    """使用 exit(2) 阻止执行 (UserPromptSubmit/PreToolUse)"""
    print(message, file=sys.stderr)
    sys.exit(2)


def block_with_json(reason: str) -> NoReturn:
    """使用 JSON 阻止结束 (SubagentStop/Stop)"""
    result = {"decision": "block", "reason": reason}
    print(json.dumps(result))
    sys.exit(0)


def allow_continue(message: str = "") -> NoReturn:
    """允许继续执行"""
    if message:
        result = {"continue": True, "systemMessage": message}
    else:
        result = {"continue": True}
    print(json.dumps(result))
    sys.exit(0)


def check_workflow_match(prompt: str, workflow_name: str) -> bool:
    """
    检查 prompt 是否匹配工作流命令

    匹配模式: prompt 以 / 开头且包含工作流名称
    例如: /my-workflow, /my-workflow --arg value
    """
    if not prompt or not workflow_name:
        return False

    prompt = prompt.strip()
    if not prompt.startswith("/"):
        return False

    # 检查是否包含工作流名称
    return workflow_name in prompt


def handle_user_prompt_submit(
    input_data: dict,
    validator: ContractValidator,
    args: argparse.Namespace,
) -> None:
    """
    处理 UserPromptSubmit 事件

    从 .context/params.json 读取工作流参数并校验输入契约
    """
    workflow_name = args.workflow or ""
    contract_name = args.contract or ""
    prompt = input_data.get("prompt", "")

    # 检查是否匹配工作流命令
    if workflow_name and not check_workflow_match(prompt, workflow_name):
        # 不匹配则跳过
        log("DEBUG", "UserPromptSubmit: prompt 不匹配工作流",
            workflow=workflow_name, prompt=prompt[:50])
        allow_continue()

    # 如果没有指定契约，跳过校验
    if not contract_name:
        log("DEBUG", "UserPromptSubmit: 未指定输入契约，跳过校验")
        allow_continue()

    # 加载契约
    contract = validator.load_contract(contract_name)
    if not contract:
        # 契约不存在，报错
        block_with_exit(f"contract-validator: 未找到输入契约 '{contract_name}'")

    # 从 .context/params.json 读取参数
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    params_path = Path(project_dir or ".") / ".context" / "params.json"

    if not params_path.exists():
        # 参数文件不存在，可能是 wf-state.py 尚未写入
        # 这不应该发生，因为 wf-state.py 应该先执行
        block_with_exit(
            f"contract-validator: 参数文件不存在 ({params_path})。"
            "请确保 wf-state.py 在 contract-validator.py 之前执行。"
        )

    try:
        params_data = json.loads(params_path.read_text(encoding="utf-8"))
    except Exception as e:
        block_with_exit(f"contract-validator: 无法读取参数文件: {e}")

    # 执行校验
    all_errors: list[dict] = []

    # Schema 校验
    schema = contract.get("schema")
    if schema:
        is_valid, errors = validator.validate_schema(params_data, schema)
        if not is_valid:
            all_errors.extend(errors)

    # 自定义校验脚本
    validator_script = contract.get("validator_script")
    if validator_script and not all_errors:
        is_valid, errors = validator.run_validator_script(validator_script, params_data)
        if not is_valid:
            all_errors.extend(errors)

    if all_errors:
        log("ERROR", "UserPromptSubmit 校验失败",
            workflow=workflow_name, contract=contract_name, errors=all_errors)
        error_msg = format_error_message(
            workflow_name or "workflow", contract_name, all_errors, "输入"
        )
        block_with_exit(error_msg)
    else:
        log("INFO", "UserPromptSubmit 校验通过",
            workflow=workflow_name, contract=contract_name)
        allow_continue(f"contract-validator: 工作流输入校验通过")


def handle_pre_tool_use(
    input_data: dict,  # noqa: ARG001  # 保留用于将来扩展
    validator: ContractValidator,  # noqa: ARG001  # 保留用于将来扩展
) -> None:
    """
    处理 PreToolUse 事件

    设计说明：采用边界校验策略，不校验节点输入。
    - 节点输入 = 前序节点输出（已通过 SubagentStop 校验）
    - 节点输入校验是冗余的
    详见需求文档 3.1 校验设计理念
    """
    log("DEBUG", "PreToolUse 事件，跳过校验（边界校验策略）")
    allow_continue()


def handle_subagent_stop(
    input_data: dict, validator: ContractValidator, args: argparse.Namespace
) -> None:
    """处理 SubagentStop 事件"""
    contract_name: str = args.contract or ""
    node_name: str = args.node or input_data.get("agent_id", "unknown") or "unknown"

    if not contract_name:
        allow_continue("contract-validator: 未指定契约名称，跳过校验")

    contract = validator.load_contract(contract_name)
    if not contract:
        allow_continue(f"contract-validator: 未找到契约 '{contract_name}'")

    # 从 agent_transcript_path 提取节点输出（使用共享模块）
    transcript_path: str = input_data.get("agent_transcript_path") or ""
    if not transcript_path:
        block_with_json(f"contract-validator: 未找到节点 '{node_name}' 的 transcript")

    extraction_result = extract_from_transcript(transcript_path)
    if not extraction_result.success:
        block_with_json(f"contract-validator: 无法读取节点 '{node_name}' 的输出: {extraction_result.error}")

    data = extraction_result.json_data
    if data is None:
        block_with_json(
            f"contract-validator: 节点 '{node_name}' 输出中未找到符合契约的 JSON 数据"
        )

    # 执行校验
    all_errors: list[dict] = []

    # 1. Schema 校验
    schema = contract.get("schema")
    if schema:
        is_valid, errors = validator.validate_schema(data, schema)
        if not is_valid:
            all_errors.extend(errors)

    # 2. 自定义校验脚本
    validator_script = contract.get("validator_script")
    if validator_script and not all_errors:
        is_valid, errors = validator.run_validator_script(validator_script, data)
        if not is_valid:
            all_errors.extend(errors)

    if all_errors:
        log(
            "ERROR",
            "SubagentStop 校验失败",
            node=node_name,
            contract=contract_name,
            errors=all_errors,
        )
        error_msg = format_error_message(node_name, contract_name, all_errors, "输出")
        block_with_json(error_msg)
    else:
        log("INFO", "SubagentStop 校验通过", node=node_name, contract=contract_name)
        allow_continue(f"contract-validator: 节点 '{node_name}' 输出校验通过")


def handle_stop(
    input_data: dict,
    validator: ContractValidator,
    args: argparse.Namespace,
) -> None:
    """
    处理 Stop 事件（工作流输出校验）

    从 transcript_path 提取最后一条 assistant 消息并校验输出契约
    """
    workflow_name = args.workflow or ""
    contract_name = args.contract or ""

    # 如果没有指定契约，跳过校验
    if not contract_name:
        log("DEBUG", "Stop: 未指定输出契约，跳过校验")
        allow_continue()

    # 加载契约
    contract = validator.load_contract(contract_name)
    if not contract:
        allow_continue(f"contract-validator: 未找到输出契约 '{contract_name}'")

    # 从 transcript_path 提取工作流输出（使用共享模块）
    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        block_with_json(f"contract-validator: 工作流 '{workflow_name}' 的 transcript 路径缺失")

    extraction_result = extract_from_transcript(transcript_path)
    if not extraction_result.success:
        block_with_json(f"contract-validator: 无法读取工作流 '{workflow_name}' 的输出: {extraction_result.error}")

    data = extraction_result.json_data
    if data is None:
        block_with_json(
            f"contract-validator: 工作流 '{workflow_name}' 输出中未找到符合契约的 JSON 数据"
        )

    # 执行校验
    all_errors: list[dict] = []

    # Schema 校验
    schema = contract.get("schema")
    if schema:
        is_valid, errors = validator.validate_schema(data, schema)
        if not is_valid:
            all_errors.extend(errors)

    # 自定义校验脚本
    validator_script = contract.get("validator_script")
    if validator_script and not all_errors:
        is_valid, errors = validator.run_validator_script(validator_script, data)
        if not is_valid:
            all_errors.extend(errors)

    if all_errors:
        log("ERROR", "Stop 校验失败",
            workflow=workflow_name, contract=contract_name, errors=all_errors)
        error_msg = format_error_message(
            workflow_name or "workflow", contract_name, all_errors, "输出"
        )
        block_with_json(error_msg)
    else:
        log("INFO", "Stop 校验通过",
            workflow=workflow_name, contract=contract_name)
        allow_continue(f"contract-validator: 工作流输出校验通过")


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="契约校验脚本")
    parser.add_argument("--workflow", type=str, help="工作流名称（用于命令匹配）")
    parser.add_argument("--contract", type=str, help="契约名称")
    parser.add_argument("--node", type=str, help="节点名称")
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    # 读取 stdin 输入
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        log("ERROR", "无法解析输入", error=str(e))
        allow_continue(f"contract-validator: 无法解析输入 ({e})")

    hook_event = input_data.get("hook_event_name", "")
    log("DEBUG", "收到 Hook 事件", hook_event=hook_event, args=vars(args))

    # 初始化校验器
    contracts_dir = find_contracts_dir()
    validator = ContractValidator(contracts_dir)

    # 根据事件类型分发处理
    if hook_event == "UserPromptSubmit":
        handle_user_prompt_submit(input_data, validator, args)
    elif hook_event == "PreToolUse":
        handle_pre_tool_use(input_data, validator)
    elif hook_event == "SubagentStop":
        handle_subagent_stop(input_data, validator, args)
    elif hook_event == "Stop":
        handle_stop(input_data, validator, args)
    else:
        log("WARN", "未知的 Hook 事件", hook_event=hook_event)
        allow_continue()


if __name__ == "__main__":
    main()
