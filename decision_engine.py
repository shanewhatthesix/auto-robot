# decision_engine.py

from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod

class Action:
    """
    表示Agent需要执行的一个动作，可以是工具调用或直接响应。
    """
    def __init__(self, type: str, tool_name: Optional[str] = None,
                 tool_params: Optional[Dict[str, Any]] = None,
                 response: Optional[str] = None):
        self.type = type # "tool_call" or "response"
        self.tool_name = tool_name
        self.tool_params = tool_params
        self.response = response

    def __repr__(self):
        if self.type == "tool_call":
            return f"Action(type='{self.type}', tool_name='{self.tool_name}', tool_params={self.tool_params})"
        else:
            return f"Action(type='{self.type}', response='{self.response}')"

class DecisionEngine(ABC):
    """
    决策引擎基类，定义了Agent如何根据任务做出决策的接口。
    """
    @abstractmethod
    def decide(self, task: str, available_tools: Dict[str, Callable], context: Optional[Dict[str, Any]] = None) -> Action:
        """
        根据任务和可用工具，决定Agent下一步的动作。
        :param task: 用户输入的任务描述
        :param available_tools: Agent当前可用的工具字典 {tool_name: tool_function}
        :param context: 决策上下文信息
        :return: 决策结果，一个Action对象
        """
        pass

class RuleBasedDecisionEngine(DecisionEngine):
    """
    基于规则的决策引擎，优先匹配预定义规则。
    """
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def add_rule(self, pattern: str, tool_name: str, params_extractor: Callable[[str], Dict[str, Any]]):
        """
        添加一个决策规则。
        :param pattern: 用于匹配任务的关键词或正则表达式
        :param tool_name: 匹配成功时调用的工具名称
        :param params_extractor: 从任务中提取工具参数的函数
        """
        self.rules.append({
            "pattern": pattern,
            "tool_name": tool_name,
            "params_extractor": params_extractor
        })
        print(f"规则已添加: 匹配 '{pattern}' 调用工具 '{tool_name}'。")

    def decide(self, task: str, available_tools: Dict[str, Callable], context: Optional[Dict[str, Any]] = None) -> Action:
        print(f"规则引擎开始决策任务: '{task}'")
        for rule in self.rules:
            if rule["pattern"] in task: # 简单的关键词匹配
                tool_name = rule["tool_name"]
                if tool_name in available_tools:
                    try:
                        tool_params = rule["params_extractor"](task)
                        print(f"规则匹配成功，决定调用工具 '{tool_name}'，参数: {tool_params}")
                        return Action(type="tool_call", tool_name=tool_name, tool_params=tool_params)
                    except Exception as e:
                        print(f"参数提取失败或规则执行错误: {e}")
                        continue
                else:
                    print(f"规则匹配到工具 '{tool_name}'，但该工具未注册。")
        print("规则引擎未匹配到任何规则。")
        return Action(type="response", response="规则引擎无法直接处理此任务，将转交LLM。")

class LLMDecisionEngine(DecisionEngine):
    """
    基于LLM的决策引擎，通过大模型进行推理。
    （此处仅为骨架，实际需要集成Qwen Agent或其他LLM库）
    """
    def __init__(self, llm_model: Any):
        self.llm_model = llm_model
        print("LLM决策引擎已初始化。")

    def decide(self, task: str, available_tools: Dict[str, Callable], context: Optional[Dict[str, Any]] = None) -> Action:
        print(f"LLM引擎开始决策任务: '{task}'")
        # 模拟LLM决策逻辑
        # 实际中，这里会构建prompt，调用LLM API，解析LLM返回的工具调用或响应
        prompt = f"根据任务 '{task}' 和可用工具 {list(available_tools.keys())}，决定下一步动作。如果需要调用工具，请返回工具名称和参数；否则，直接给出响应。"
        print(f"LLM Prompt: {prompt}")

        # 假设LLM返回一个工具调用或直接响应
        # 这是一个简化的模拟，实际需要复杂的LLM交互和解析
        if "文件" in task and "读取" in task:
            return Action(type="tool_call", tool_name="read_file", tool_params={"path": "example.txt"})
        elif "系统" in task and "状态" in task:
            return Action(type="tool_call", tool_name="get_system_status", tool_params={})
        else:
            return Action(type="response", response=f"LLM认为：'{task}' 任务需要进一步思考或直接响应。")

class HybridDecisionEngine(DecisionEngine):
    """
    混合决策引擎，结合规则和LLM进行决策。
    """
    def __init__(self, rule_engine: RuleBasedDecisionEngine, llm_engine: LLMDecisionEngine):
        self.rule_engine = rule_engine
        self.llm_engine = llm_engine
        print("混合决策引擎已初始化。")

    def decide(self, task: str, available_tools: Dict[str, Callable], context: Optional[Dict[str, Any]] = None) -> Action:
        print(f"混合决策引擎开始处理任务: '{task}'")
        # 1. 尝试通过规则引擎决策
        rule_action = self.rule_engine.decide(task, available_tools, context)
        if rule_action.type == "tool_call" and rule_action.tool_name in available_tools:
            print("混合决策引擎：规则引擎成功决策。")
            return rule_action
        elif rule_action.type == "response" and "规则引擎无法直接处理此任务" not in rule_action.response:
            # 如果规则引擎给出了明确的非工具调用响应，也采纳
            print("混合决策引擎：规则引擎给出明确响应。")
            return rule_action

        # 2. 如果规则引擎未能有效决策，转交LLM引擎
        print("混合决策引擎：规则引擎未能有效决策，转交LLM引擎。")
        llm_action = self.llm_engine.decide(task, available_tools, context)
        return llm_action

if __name__ == "__main__":
    # 模拟工具函数
    def mock_read_file(path: str):
        print(f"模拟读取文件: {path}")
        return f"文件 '{path}' 的内容。"

    def mock_get_system_status():
        print("模拟获取系统状态")
        return "CPU: 50%, 内存: 70%"

    def mock_calculator(num1: int, num2: int):
        print(f"模拟计算: {num1} + {num2}")
        return num1 + num2

    available_tools = {
        "read_file": mock_read_file,
        "get_system_status": mock_get_system_status,
        "calculator": mock_calculator
    }

    # 实例化规则引擎
    rule_engine = RuleBasedDecisionEngine()
    rule_engine.add_rule(
        pattern="计算",
        tool_name="calculator",
        params_extractor=lambda t: {"num1": int(t.split("计算")[1].split("加")[0].strip()),
                                     "num2": int(t.split("加")[1].strip())}
    )
    rule_engine.add_rule(
        pattern="读取文件",
        tool_name="read_file",
        params_extractor=lambda t: {"path": t.split("读取文件")[1].strip()}
    )

    # 实例化LLM引擎 (这里用一个简单的模拟LLM)
    class MockLLM:
        def generate(self, prompt: str):
            # 实际中这里会调用LLM API
            return "LLM模拟响应"
    llm_engine = LLMDecisionEngine(MockLLM())

    # 实例化混合决策引擎
    hybrid_engine = HybridDecisionEngine(rule_engine, llm_engine)

    print("\n--- 测试混合决策引擎 ---")
    # 规则匹配成功
    action1 = hybrid_engine.decide("请帮我计算 10 加 20", available_tools)
    print(f"决策结果1: {action1}")
    if action1.type == "tool_call":
        result = available_tools[action1.tool_name](**action1.tool_params)
        print(f"工具执行结果1: {result}")

    print("\n--- 测试LLM决策 ---")
    # 规则未匹配，转交LLM
    action2 = hybrid_engine.decide("请帮我读取文件 example.txt", available_tools)
    print(f"决策结果2: {action2}")
    if action2.type == "tool_call":
        result = available_tools[action2.tool_name](**action2.tool_params)
        print(f"工具执行结果2: {result}")

    print("\n--- 测试LLM决策 (系统状态) ---")
    action3 = hybrid_engine.decide("查看系统状态", available_tools)
    print(f"决策结果3: {action3}")
    if action3.type == "tool_call":
        result = available_tools[action3.tool_name](**action3.tool_params)
        print(f"工具执行结果3: {result}")

    print("\n--- 测试无法处理的任务 ---")
    action4 = hybrid_engine.decide("请帮我画一幅画", available_tools)
    print(f"决策结果4: {action4}")