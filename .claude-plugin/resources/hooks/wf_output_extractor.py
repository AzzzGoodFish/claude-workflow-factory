#!/usr/bin/env python3
"""
wf-output-extractor.py - 工作流节点输出提取工具

从 transcript 文件或 tool_response 文本中提取节点的结构化输出。
供 contract-validator.py 和 wf-state.py 共同使用，确保提取逻辑一致。

用法：
  作为模块导入：
    from wf_output_extractor import extract_from_transcript, extract_from_text

  作为命令行工具：
    python wf-output-extractor.py --transcript <path>
    python wf-output-extractor.py --text <text>
    echo "<text>" | python wf-output-extractor.py --stdin
"""

import json
import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class ExtractionResult:
    """提取结果"""
    success: bool
    json_data: Optional[Any] = None  # 提取的 JSON 数据（若有）
    raw_text: str = ""               # 原始文本内容
    error: Optional[str] = None      # 错误信息（若失败）
    source: str = ""                 # 数据来源描述

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "json_data": self.json_data,
            "raw_text": self.raw_text,
            "error": self.error,
            "source": self.source,
        }


def extract_json_from_text(text: str) -> ExtractionResult:
    """
    从文本中提取 JSON 数据

    提取规则（按优先级）：
    1. 优先匹配 ```json ... ``` 代码块
    2. 若无代码块，尝试将整条消息解析为 JSON
    3. 两者都失败则返回原始文本（json_data 为 None）
    """
    if not text or not text.strip():
        return ExtractionResult(
            success=False,
            raw_text=text or "",
            error="输入文本为空",
            source="text"
        )

    # 尝试匹配 ```json ... ``` 代码块
    json_block_pattern = r'```json\s*([\s\S]*?)\s*```'
    matches = re.findall(json_block_pattern, text)

    if matches:
        # 取最后一个 json 代码块（通常是最终输出）
        json_str = matches[-1].strip()
        try:
            json_data = json.loads(json_str)
            return ExtractionResult(
                success=True,
                json_data=json_data,
                raw_text=text,
                source="json_code_block"
            )
        except json.JSONDecodeError:
            # 代码块内容不是有效 JSON，继续尝试其他方式
            pass

    # 尝试将整条消息解析为 JSON
    try:
        json_data = json.loads(text.strip())
        return ExtractionResult(
            success=True,
            json_data=json_data,
            raw_text=text,
            source="raw_json"
        )
    except json.JSONDecodeError:
        pass

    # 无法提取 JSON，返回原始文本
    return ExtractionResult(
        success=True,  # 提取成功，只是没有结构化数据
        json_data=None,
        raw_text=text,
        source="plain_text"
    )


def parse_transcript_line(line: str) -> Optional[dict]:
    """解析 transcript 文件的一行"""
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def get_text_from_message(message: dict) -> str:
    """从 message 对象中提取文本内容"""
    content = message.get("content", [])

    # content 可能是字符串（user 消息）或数组（assistant 消息）
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        return "\n".join(text_parts)

    return ""


def extract_from_transcript(transcript_path: str) -> ExtractionResult:
    """
    从 transcript 文件中提取最后一条 assistant 消息的输出

    Transcript 文件格式（JSONL）：
    - 每行一个 JSON 对象
    - type: "user" | "assistant"
    - message.content: 消息内容数组
      - {type: "text", text: "..."} 文本内容
      - {type: "tool_use", ...} 工具调用
    """
    path = Path(transcript_path)

    if not path.exists():
        return ExtractionResult(
            success=False,
            error=f"Transcript 文件不存在: {transcript_path}",
            source="transcript"
        )

    # 读取并解析所有行
    assistant_messages = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                entry = parse_transcript_line(line)
                if entry and entry.get("type") == "assistant":
                    assistant_messages.append(entry)
    except Exception as e:
        return ExtractionResult(
            success=False,
            error=f"读取 transcript 文件失败: {e}",
            source="transcript"
        )

    if not assistant_messages:
        return ExtractionResult(
            success=False,
            error="Transcript 中没有 assistant 消息",
            source="transcript"
        )

    # 取最后一条 assistant 消息
    last_message = assistant_messages[-1].get("message", {})
    text = get_text_from_message(last_message)

    if not text:
        return ExtractionResult(
            success=False,
            error="最后一条 assistant 消息没有文本内容（可能只有 tool_use）",
            source="transcript"
        )

    # 从文本中提取 JSON
    result = extract_json_from_text(text)
    result.source = f"transcript:{result.source}"
    return result


def extract_from_tool_response(tool_response: str) -> ExtractionResult:
    """
    从 tool_response 中提取输出

    tool_response 是 Task 工具返回的节点最后一条消息内容
    """
    result = extract_json_from_text(tool_response)
    result.source = f"tool_response:{result.source}"
    return result


def main():
    parser = argparse.ArgumentParser(
        description="从 transcript 或文本中提取节点输出"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--transcript", "-t",
        help="Transcript 文件路径"
    )
    group.add_argument(
        "--text",
        help="直接提供文本内容"
    )
    group.add_argument(
        "--stdin",
        action="store_true",
        help="从 stdin 读取文本"
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="只输出提取的 JSON（若无则输出 null）"
    )
    parser.add_argument(
        "--raw-only",
        action="store_true",
        help="只输出原始文本"
    )

    args = parser.parse_args()

    # 执行提取
    if args.transcript:
        result = extract_from_transcript(args.transcript)
    elif args.text:
        result = extract_from_tool_response(args.text)
    else:  # --stdin
        text = sys.stdin.read()
        result = extract_from_tool_response(text)

    # 输出结果
    if args.json_only:
        if result.json_data is not None:
            print(json.dumps(result.json_data, ensure_ascii=False, indent=2))
        else:
            print("null")
    elif args.raw_only:
        print(result.raw_text)
    else:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))

    # 返回码
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
