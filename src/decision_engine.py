# decision_engine.py

import json
import requests
import time # 导入time模块
import re # 导入re模块
from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from zhipuai import ZhipuAI # 导入ZhipuAI库

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
    基于LLM的决策引擎，通过大模型进行推理（使用OpenAI风格API）。
    """
    def __init__(self, llm_config: Dict[str, str]):
        self.llm_config = llm_config
        # ZhipuAI客户端不再需要base_url，它会自行处理
        self.api_key = llm_config.get("api_key")
        self.model_name = llm_config.get("model_name", "glm-4") # 默认使用智谱AI模型名

        if not self.api_key:
             raise ValueError("LLM API Key 未配置。") # API Key现在是必需的

        self.client = ZhipuAI(api_key=self.api_key) # 初始化ZhipuAI客户端

        print(f"LLM决策引擎已初始化，使用智谱AI模型: {self.model_name}。")

    def decide(self, task: str, available_tools: Dict[str, Callable], context: Optional[Dict[str, Any]] = None) -> Action:
        print(f"LLM引擎开始决策任务: '{task}'")
        
        # 准备工具信息（OpenAI Function Calling 格式）
        print(f"LLM引擎接收到的可用工具: {list(available_tools.keys())}")
        tools_list = []
        for tool_name, tool_func in available_tools.items():
            # 尝试从函数签名和docstring提取信息
            import inspect
            try:
                sig = inspect.signature(tool_func)
                parameters = {}
                required_params = []
                for param_name, param in sig.parameters.items():
                    if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                         # 简化处理，假设所有参数都是string类型，且没有默认值的为必需参数
                        parameters[param_name] = {"type": "string"}
                        if param.default == inspect.Parameter.empty:
                            required_params.append(param_name)

                tool_description = tool_func.__doc__.strip() if tool_func.__doc__ else f"执行 {tool_name} 功能。"
                if tool_name == "get_current_time":
                    tool_description = "获取当前的日期和时间。"

                tools_list.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": tool_description,
                        "parameters": {
                            "type": "object",
                            "properties": parameters,
                            "required": required_params
                        } if tool_name != "get_current_time" else {"type": "object", "properties": {}, "required": []}
                    }
                })
            except Exception as e:
                print(f"Warning: 无法为工具 '{tool_name}' 生成Function Calling信息: {e}")
                # 如果无法提取信息，至少提供工具名称
                tools_list.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": f"执行 {tool_name} 功能。",
                        "parameters": {"type": "object", "properties": {}}
                    }
                })


        print(f"LLM引擎构建的工具列表: {json.dumps(tools_list, indent=2, ensure_ascii=False)}")

        # 构建消息列表
        messages = [{"role": "user", "content": task}]
        
        # 构建工具列表 (ZhipuAI SDK的tools参数与OpenAI类似)
        # 智谱AI的tools参数结构与OpenAI Function Calling类似，可以直接使用
        
        # 发送HTTP请求 (通过ZhipuAI SDK)
        max_retries = 3
        response_data = None
        for attempt in range(max_retries):
            try:
                print(f"Calling ZhipuAI API with model: {self.model_name} (Attempt {attempt + 1}/{max_retries})")
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools_list,
                    tool_choice="auto" # 智谱AI支持auto
                )
                response_data = response.model_dump() # 将Pydantic模型转换为字典
                print(f"LLM Raw Response: {json.dumps(response_data, indent=2)}")
                break # 请求成功，跳出循环
            except Exception as e: # 捕获所有可能的SDK异常
                error_message = str(e)
                # 智谱AI SDK的异常中，速率限制通常会包含"429"或"rate limit"
                if ("429" in error_message or "rate limit" in error_message.lower()) and attempt < max_retries - 1:
                    sleep_time = 2 ** attempt # 指数退避
                    print(f"Received rate limit error. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    print(f"调用LLM API失败: {e}")
                    return Action(type="response", response=f"调用LLM API失败: {e}")
        else: # 如果所有重试都失败
            print(f"所有 {max_retries} 次重试均失败。")
            return Action(type="response", response=f"调用LLM API失败: 达到最大重试次数。")

        # 解析LLM响应
        if response_data and response_data.get("choices"):
            choice = response_data["choices"][0]
            message = choice.get("message")
            if message:
                # 检查是否存在工具调用
                # 智谱AI的tool_calls可能在message.tool_calls中，也可能在message.function_call中，甚至在content中
                tool_calls = message.get("tool_calls")
                function_call = message.get("function_call") # 兼容旧版或不同模型
                content_str = message.get("content")

                # 优先处理message.tool_calls字段 (智谱AI新版格式)
                if tool_calls:
                    # 假设只有一个工具调用
                    tool_call = tool_calls[0].get("function")
                    if tool_call:
                        tool_name = tool_call.get("name")
                        try:
                            tool_params = json.loads(tool_call.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            print(f"Warning: LLM返回的工具参数不是有效的JSON: {tool_call.get('arguments')}")
                            tool_params = {}

                        print(f"LLM决定调用工具: '{tool_name}'，参数: {tool_params}")
                        return Action(type="tool_call", tool_name=tool_name, tool_params=tool_params)
                # 其次处理message.function_call字段 (兼容旧版或不同模型)
                elif function_call:
                    tool_name = function_call.get("name")
                    try:
                        tool_params = json.loads(function_call.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        print(f"Warning: LLM返回的工具参数不是有效的JSON: {function_call.get('arguments')}")
                        tool_params = {}
                    print(f"LLM决定调用工具 (旧版): '{tool_name}'，参数: {tool_params}")
                    return Action(type="tool_call", tool_name=tool_name, tool_params=tool_params)
                # 最后尝试从content中解析工具调用（智谱AI流式响应的特殊情况）
                elif content_str:
                    print(f"Debug: Attempting to parse tool call from content: {content_str}")
                    try:
                        # 查找content中是否包含JSON字符串，并尝试解析
                        # 移除<think>标签及其内容
                        clean_content_str = re.sub(r'<think>.*?</think>', '', content_str, flags=re.DOTALL).strip()
                        
                        # 查找content中是否包含JSON字符串，并尝试解析
                        json_start = clean_content_str.find('{')
                        json_end = clean_content_str.rfind('}')
                        
                        if json_start != -1 and json_end != -1 and json_end > json_start:
                            json_part = clean_content_str[json_start : json_end + 1]
                            parsed_content = json.loads(json_part)
                            
                            # 检查delta.tool_calls路径 (智谱AI流式响应格式)
                            # 智谱AI的tool_calls信息通常在delta.tool_calls中
                            if "delta" in parsed_content and "tool_calls" in parsed_content["delta"] and parsed_content["delta"]["tool_calls"]:
                                # 遍历所有tool_calls，虽然通常只有一个
                                for tool_call_item in parsed_content["delta"]["tool_calls"]:
                                    tool_call_function = tool_call_item.get("function")
                                    if tool_call_function:
                                        tool_name = tool_call_function.get("name")
                                        try:
                                            # 智谱AI的arguments可能已经是JSON字符串，直接解析
                                            tool_params = json.loads(tool_call_function.get("arguments", "{}"))
                                        except json.JSONDecodeError:
                                            print(f"Warning: LLM返回的content中工具参数不是有效的JSON: {tool_call_function.get('arguments')}")
                                            tool_params = {}
                                        print(f"LLM决定调用工具 (从content解析): '{tool_name}'，参数: {tool_params}")
                                        return Action(type="tool_call", tool_name=tool_name, tool_params=tool_params)
                            # 兼容直接在顶层tool_calls的情况 (不太可能，但保留)
                            elif "tool_calls" in parsed_content and parsed_content["tool_calls"]:
                                for tool_call_item in parsed_content["tool_calls"]:
                                    tool_call_function = tool_call_item.get("function")
                                    if tool_call_function:
                                        tool_name = tool_call_function.get("name")
                                        try:
                                            tool_params = json.loads(tool_call_function.get("arguments", "{}"))
                                        except json.JSONDecodeError:
                                            print(f"Warning: LLM返回的content中工具参数不是有效的JSON: {tool_call_function.get('arguments')}")
                                            tool_params = {}
                                        print(f"LLM决定调用工具 (从content解析): '{tool_name}'，参数: {tool_params}")
                                        return Action(type="tool_call", tool_name=tool_name, tool_params=tool_params)
                    except (json.JSONDecodeError, KeyError, IndexError) as parse_e:
                        print(f"Warning: 无法从content中解析工具调用信息: {parse_e}")
                    
                    # 如果没有工具调用，检查是否有文本响应
                    clean_text_response = re.sub(r'<think>.*?</think>', '', content_str, flags=re.DOTALL).strip()
                    # 移除可能存在的JSON部分
                    clean_text_response = re.sub(r'\{.*\}', '', clean_text_response, flags=re.DOTALL).strip()

                    if clean_text_response:
                        print(f"LLM直接响应: {clean_text_response}")
                        return Action(type="response", response=clean_text_response)

        print(f"LLM响应格式未知或为空。")
        return Action(type="response", response=f"LLM未能生成有效响应。")



class HybridDecisionEngine(DecisionEngine):
    """
    混合决策引擎，结合规则和LLM进行决策。
    """
    def __init__(self, rule_engine: RuleBasedDecisionEngine, llm_engine: DecisionEngine):
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
        """读取指定路径的文件内容。"""
        print(f"模拟读取文件: {path}")
        return f"文件 '{path}' 的内容。"

    def mock_get_system_status():
        """获取当前系统状态，包括CPU和内存使用情况。"""
        print("模拟获取系统状态")
        return "CPU: 50%, 内存: 70%"

    def mock_calculator(num1: int, num2: int):
        """计算两个数字的和。"""
        print(f"模拟计算: {num1} + {num2}")
        return num1 + num2
        
    def mock_get_current_time():
        """获取当前日期和时间。"""
        print("模拟获取当前时间")
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    available_tools = {
        "read_file": mock_read_file,
        "get_system_status": mock_get_system_status,
        "calculator": mock_calculator,
        "get_current_time": mock_get_current_time
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
    rule_engine.add_rule(
        pattern="现在几点|当前时间",
        tool_name="get_current_time",
        params_extractor=lambda t: {}
    )


    # 实例化LLM引擎 (使用模拟配置，但LLMDecisionEngine现在使用requests)
    """llm_config_mock = {
        "llm_type": "OpenAI", # 类型改为OpenAI风格
        "api_key": "YOUR_API_KEY", # 实际使用时请替换为有效API Key
        "base_url": "http://localhost:8000", # 模拟一个本地OpenAI风格API端点
        "model_name": "mock-model" # 模拟模型名称
    }
    # 注意：这里的LLMDecisionEngine将尝试调用 http://localhost:8000/v1/chat/completions
    # 如果没有运行模拟的OpenAI风格API服务，这里会失败。
    llm_engine = LLMDecisionEngine(llm_config_mock)

    # 实例化混合决策引擎
    hybrid_engine = HybridDecisionEngine(rule_engine, llm_engine)
"""