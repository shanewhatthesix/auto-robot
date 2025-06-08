# main.py

import os
import json
from typing import Dict, Any, Optional

# 导入核心模块
from agent_core import Agent
from decision_engine import RuleBasedDecisionEngine, LLMDecisionEngine, HybridDecisionEngine, Action
from tool_registry import ToolRegistry
from audit_logger import AuditLogger
from sandbox import Sandbox

# 导入工具集
from tools.file_tools import FileTools
from tools.system_tools import SystemTools

class AutonomousAgent(Agent):
    """
    自主工具Agent的实现。
    """
    def __init__(self, name: str, description: str,
                 decision_engine: HybridDecisionEngine,
                 tool_registry: ToolRegistry,
                 audit_logger: AuditLogger,
                 sandbox: Sandbox):
        super().__init__(name, description)
        self.decision_engine = decision_engine
        self.tool_registry = tool_registry
        self.audit_logger = audit_logger
        self.sandbox = sandbox
        print(f"自主Agent '{self.name}' 已初始化。")

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Agent的运行方法，根据任务自主决策并执行。
        """
        self.audit_logger.log_action(
            action_type="user_input",
            description="接收到用户任务",
            details={"task": task}
        )
        print(f"\nAgent '{self.name}' 接收到任务: '{task}'")

        # 获取所有可用工具
        available_tools = self.tool_registry.get_all_tools()

        # 决策下一步动作
        action = self.decision_engine.decide(task, available_tools, context)

        self.audit_logger.log_action(
            action_type="decision",
            description="决策结果",
            details={"action_type": action.type, "tool_name": action.tool_name, "tool_params": action.tool_params, "response": action.response}
        )

        if action.type == "tool_call":
            tool_name = action.tool_name
            tool_params = action.tool_params if action.tool_params is not None else {}

            if tool_name not in available_tools:
                error_msg = f"错误: 决策引擎决定调用未注册的工具 '{tool_name}'。"
                print(error_msg)
                self.audit_logger.log_action(
                    action_type="error",
                    description="工具调用失败",
                    details={"tool_name": tool_name, "tool_params": tool_params},
                    status="error",
                    error=error_msg
                )
                return error_msg

            tool_func = available_tools[tool_name]
            print(f"Agent 决定调用工具: '{tool_name}'，参数: {tool_params}")

            try:
                # 对于SystemTools.execute_command，我们通过Sandbox执行
                if tool_name == "execute_command":
                    command = tool_params.get("command")
                    timeout = tool_params.get("timeout", 60)
                    if not command:
                        raise ValueError("execute_command 工具需要 'command' 参数。")

                    self.audit_logger.log_action(
                        action_type="tool_call",
                        description=f"通过沙箱执行CLI命令: {command}",
                        details={"tool_name": tool_name, "command": command, "timeout": timeout}
                    )

                    sandbox_result = self.sandbox.execute_command(command, timeout=timeout)

                    if sandbox_result["success"]:
                        result_output = (
                            f"命令执行成功 (返回码: {sandbox_result['returncode']}):\n"
                            f"Stdout:\n{str(sandbox_result['stdout'])}\n"
                            f"Stderr:\n{str(sandbox_result['stderr'])}"
                        )
                        self.audit_logger.log_action(
                            action_type="tool_result",
                            description="CLI命令执行成功",
                            details={"tool_name": tool_name, "command": command, "result": result_output},
                            status="success"
                        )
                        return result_output
                    else:
                        error_msg = (
                            f"命令执行失败 (返回码: {sandbox_result['returncode']}): {sandbox_result['error']}\n"
                            f"Stdout:\n{str(sandbox_result['stdout'])}\n"
                            f"Stderr:\n{str(sandbox_result['stderr'])}"
                        )
                        self.audit_logger.log_action(
                            action_type="tool_result",
                            description="CLI命令执行失败",
                            details={"tool_name": tool_name, "command": command, "error": error_msg},
                            status="error",
                            error=error_msg
                        )
                        return error_msg
                else:
                    # 其他工具直接调用
                    self.audit_logger.log_action(
                        action_type="tool_call",
                        description=f"调用工具: {tool_name}",
                        details={"tool_name": tool_name, "tool_params": tool_params}
                    )

                    result = tool_func(**tool_params)

                    self.audit_logger.log_action(
                        action_type="tool_result",
                        description=f"工具 '{tool_name}' 执行成功",
                        details={"tool_name": tool_name, "result": str(result)},
                        status="success"
                    )
                    return result
            except Exception as e:
                error_msg = f"执行工具 '{tool_name}' 失败: {e}"
                print(error_msg)
                self.audit_logger.log_action(
                    action_type="tool_result",
                    description=f"工具 '{tool_name}' 执行失败",
                    details={"tool_name": tool_name, "tool_params": tool_params},
                    status="error",
                    error=error_msg
                )
                return error_msg
        elif action.type == "response":
            print(f"Agent 直接响应: {action.response}")
            return action.response
        else:
            error_msg = f"未知决策动作类型: {action.type}"
            print(error_msg)
            self.audit_logger.log_action(
                action_type="error",
                description="未知决策动作类型",
                details={"action_type": action.type},
                status="error",
                error=error_msg
            )
            return error_msg

# 模拟LLM类 (用于LLMDecisionEngine)
class MockLLM:
    def generate(self, prompt: str):
        # 这是一个非常简化的模拟，实际中会调用Qwen或其他LLM API
        # 根据prompt内容，模拟LLM的工具调用或响应
        if "文件" in prompt and "读取" in prompt:
            # 尝试从prompt中提取路径，简化为固定值
            return '{"type": "tool_call", "tool_name": "read_file", "tool_params": {"path": "README.md"}}'
        elif "系统" in prompt and "状态" in prompt:
            return '{"type": "tool_call", "tool_name": "get_system_info", "tool_params": {}}'
        elif "列出" in prompt and "目录" in prompt:
            return '{"type": "tool_call", "tool_name": "list_directory", "tool_params": {"path": "."}}'
        elif "执行命令" in prompt:
            # 假设用户明确要求执行某个命令
            # 这是一个安全风险点，实际LLM应更智能地构造命令或拒绝危险命令
            if "ls" in prompt or "dir" in prompt:
                cmd = "ls -l" if os.name != "nt" else "dir"
                return f'{{"type": "tool_call", "tool_name": "execute_command", "tool_params": {{"command": "{cmd}"}}}}'
            else:
                return '{"type": "response", "response": "LLM不确定如何安全地执行此命令。"}'
        else:
            return f'{{"type": "response", "response": "LLM认为：我无法直接处理您的请求，请尝试更具体的任务。"}}'

    def parse_llm_response(self, llm_output: str) -> Action:
        """
        解析LLM的输出，将其转换为Action对象。
        """
        try:
            data = json.loads(llm_output)
            if data.get("type") == "tool_call":
                return Action(
                    type="tool_call",
                    tool_name=data.get("tool_name"),
                    tool_params=data.get("tool_params")
                )
            elif data.get("type") == "response":
                return Action(
                    type="response",
                    response=data.get("response")
                )
            else:
                return Action(type="response", response=f"LLM返回了无法解析的格式: {llm_output}")
        except json.JSONDecodeError:
            return Action(type="response", response=f"LLM返回了非JSON格式的响应: {llm_output}")

# 扩展LLMDecisionEngine以使用MockLLM的解析能力
class ExtendedLLMDecisionEngine(LLMDecisionEngine):
    def decide(self, task: str, available_tools: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Action:
        print(f"LLM引擎开始决策任务: '{task}'")
        # 构建prompt，包含可用工具信息
        tool_descriptions = []
        for tool_name, tool_func in available_tools.items():
            try:
                signature = self.llm_model.tool_registry.get_tool_signature(tool_name) # 假设LLM模型可以访问工具注册表
                tool_descriptions.append(f"- {tool_name}: {tool_func.__doc__.strip() if tool_func.__doc__ else '无描述'} (参数: {signature})")
            except Exception:
                tool_descriptions.append(f"- {tool_name}: 无描述 (参数未知)")

        prompt = (
            f"你是一个能够使用工具的智能Agent。你的任务是根据用户请求，决定是调用一个工具还是直接给出响应。\n"
            f"当前任务: '{task}'\n"
            f"可用工具:\n{'\n'.join(tool_descriptions)}\n\n"
            f"请以JSON格式返回你的决策。如果调用工具，格式为: "
            f'{{"type": "tool_call", "tool_name": "工具名称", "tool_params": {{"参数1": "值1", "参数2": "值2"}}}}\n'
            f"如果直接响应，格式为: "
            f'{{"type": "response", "response": "你的响应内容"}}\n'
            f"请确保工具名称和参数与可用工具完全匹配。"
        )
        print(f"LLM Prompt:\n{prompt}")

        llm_raw_output = self.llm_model.generate(prompt)
        print(f"LLM原始输出: {llm_raw_output}")
        return self.llm_model.parse_llm_response(llm_raw_output)


def setup_agent() -> AutonomousAgent:
    """
    设置并返回一个配置好的自主Agent实例。
    """
    # 1. 初始化核心组件
    tool_registry = ToolRegistry()
    audit_logger = AuditLogger("logs/agent_audit.log") # 日志文件路径
    sandbox = Sandbox()

    # 2. 注册工具
    # 注册FileTools中的所有静态方法
    tool_registry.register_class_tools(FileTools)
    # 注册SystemTools中的所有静态方法
    tool_registry.register_class_tools(SystemTools)

    # 3. 初始化决策引擎
    # 模拟LLM，并让其可以访问工具注册表以获取工具签名
    mock_llm_instance = MockLLM()
    mock_llm_instance.tool_registry = tool_registry # 注入tool_registry

    rule_engine = RuleBasedDecisionEngine()
    # 添加文件操作规则
    rule_engine.add_rule(
        pattern="读取文件",
        tool_name="read_file",
        params_extractor=lambda t: {"path": t.split("读取文件")[1].strip()}
    )
    rule_engine.add_rule(
        pattern="写入文件",
        tool_name="write_file",
        params_extractor=lambda t: {"path": t.split("写入文件")[1].split("内容")[0].strip(),
                                     "content": t.split("内容")[1].strip()}
    )
    rule_engine.add_rule(
        pattern="列出目录",
        tool_name="list_directory",
        params_extractor=lambda t: {"path": t.split("列出目录")[1].strip() if t.split("列出目录")[1].strip() else "."}
    )
    rule_engine.add_rule(
        pattern="删除文件",
        tool_name="delete_file",
        params_extractor=lambda t: {"path": t.split("删除文件")[1].strip()}
    )
    rule_engine.add_rule(
        pattern="创建目录",
        tool_name="create_directory",
        params_extractor=lambda t: {"path": t.split("创建目录")[1].strip()}
    )

    # 添加系统监控规则
    rule_engine.add_rule(
        pattern="系统信息",
        tool_name="get_system_info",
        params_extractor=lambda t: {}
    )
    rule_engine.add_rule(
        pattern="CPU使用率",
        tool_name="get_cpu_usage",
        params_extractor=lambda t: {}
    )
    rule_engine.add_rule(
        pattern="内存使用",
        tool_name="get_memory_usage",
        params_extractor=lambda t: {}
    )
    rule_engine.add_rule(
        pattern="列出进程",
        tool_name="list_processes",
        params_extractor=lambda t: {}
    )
    rule_engine.add_rule(
        pattern="执行命令",
        tool_name="execute_command",
        params_extractor=lambda t: {"command": t.split("执行命令")[1].strip()}
    )

    llm_engine = ExtendedLLMDecisionEngine(mock_llm_instance)
    hybrid_decision_engine = HybridDecisionEngine(rule_engine, llm_engine)

    # 4. 创建Agent实例
    agent = AutonomousAgent(
        name="AutoCLI_Agent",
        description="一个能够自主使用CLI工具进行文件操作和系统监控的Agent。",
        decision_engine=hybrid_decision_engine,
        tool_registry=tool_registry,
        audit_logger=audit_logger,
        sandbox=sandbox
    )
    return agent

def main():
    agent = setup_agent()
    print("\n欢迎使用 AutoCLI Agent！")
    print("您可以输入任务，例如：")
    print("  - 读取文件 README.md")
    print("  - 列出目录 .")
    print("  - 获取系统信息")
    print("  - 执行命令 ls -l")
    print("  - 写入文件 new_file.txt 内容 这是新文件的内容。")
    print("输入 '退出' 或 'exit' 结束程序。")

    while True:
        user_task = input("\n请输入您的任务: ")
        if user_task.lower() in ["退出", "exit"]:
            print("Agent 已退出。")
            break

        result = agent.run(user_task)
        print(f"\nAgent 最终结果:\n{result}")

if __name__ == "__main__":
    main()