# audit_logger.py

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List # 新增导入 List

class AuditLogger:
    """
    审计日志系统，记录Agent的操作和决策。
    """
    _instance = None
    _log_file_path: str = "agent_audit.log" # 默认日志文件路径

    def __new__(cls, log_file_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(AuditLogger, cls).__new__(cls)
            cls._instance._log_file_path = log_file_path if log_file_path else cls._log_file_path
            # 确保日志文件目录存在
            log_dir = os.path.dirname(cls._instance._log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            print(f"AuditLogger 单例已初始化，日志将写入: {cls._instance._log_file_path}")
        return cls._instance

    def log_action(self,
                   action_type: str,
                   description: str,
                   details: Optional[Dict[str, Any]] = None,
                   status: str = "info",
                   error: Optional[str] = None):
        """
        记录一个Agent操作或决策日志。
        :param action_type: 操作类型 (e.g., "decision", "tool_call", "tool_result", "error", "user_input")
        :param description: 操作的简要描述
        :param details: 包含操作相关详细信息的字典 (e.g., tool_name, tool_params, task)
        :param status: 日志状态 (e.g., "info", "success", "warning", "error")
        :param error: 如果有错误，错误信息
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "description": description,
            "status": status,
            "details": details if details is not None else {},
            "error": error
        }
        self._write_log(log_entry)

    def _write_log(self, entry: Dict[str, Any]):
        """
        将日志条目写入文件。
        """
        try:
            with open(self._log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except IOError as e:
            print(f"写入审计日志失败: {e}")

    def get_logs(self) -> List[Dict[str, Any]]:
        """
        读取所有历史日志条目。
        :return: 日志条目列表
        """
        logs = []
        if not os.path.exists(self._log_file_path):
            return logs
        try:
            with open(self._log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        print(f"跳过无效日志行: {line.strip()}")
            return logs
        except IOError as e:
            print(f"读取审计日志失败: {e}")
            return []

if __name__ == "__main__":
    # 示例用法
    # 可以指定日志文件路径，也可以使用默认路径
    logger = AuditLogger("logs/my_agent_audit.log")

    print("--- 审计日志测试 ---")

    # 记录用户输入
    logger.log_action(
        action_type="user_input",
        description="用户输入任务",
        details={"task": "请帮我读取文件 example.txt"}
    )

    # 记录决策过程
    logger.log_action(
        action_type="decision",
        description="决策引擎决定调用工具",
        details={"engine": "HybridDecisionEngine", "tool_name": "read_file", "tool_params": {"path": "example.txt"}}
    )

    # 记录工具调用
    logger.log_action(
        action_type="tool_call",
        description="调用文件读取工具",
        details={"tool_name": "read_file", "tool_params": {"path": "example.txt"}}
    )

    # 记录工具执行结果
    logger.log_action(
        action_type="tool_result",
        description="文件读取成功",
        details={"tool_name": "read_file", "result": "文件内容：Hello World!"},
        status="success"
    )

    # 记录错误
    logger.log_action(
        action_type="tool_call",
        description="尝试删除不存在的文件",
        details={"tool_name": "delete_file", "tool_params": {"path": "non_existent.txt"}},
        status="error",
        error="FileNotFoundError: 文件不存在: non_existent.txt"
    )

    print("\n--- 读取所有日志 ---")
    all_logs = logger.get_logs()
    for log in all_logs:
        print(json.dumps(log, indent=2, ensure_ascii=False))

    # 清理测试日志文件
    if os.path.exists("logs/my_agent_audit.log"):
        os.remove("logs/my_agent_audit.log")
        print("\n测试日志文件已清理。")
    if os.path.exists("logs"):
        os.rmdir("logs")
        print("测试日志目录已清理。")