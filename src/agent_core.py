# agent_core.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class Agent(ABC):
    """
    Agent基类，定义了自主Agent的核心接口。
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: Dict[str, Any] = {} # 存储注册的工具

    def add_tool(self, tool_name: str, tool_func: Any):
        """
        注册一个工具供Agent使用。
        :param tool_name: 工具的名称
        :param tool_func: 工具对应的函数或方法
        """
        self.tools[tool_name] = tool_func
        print(f"工具 '{tool_name}' 已注册到 Agent '{self.name}'。")

    @abstractmethod
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Agent的运行方法，根据任务自主决策并执行。
        :param task: 用户输入的任务描述
        :param context: 运行上下文信息
        :return: 任务执行结果
        """
        pass

    def _execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """
        内部方法，用于执行已注册的工具。
        :param tool_name: 要执行的工具名称
        :param args: 工具函数的 positional arguments
        :param kwargs: 工具函数的 keyword arguments
        :return: 工具执行结果
        :raises ValueError: 如果工具未注册
        """
        if tool_name not in self.tools:
            raise ValueError(f"工具 '{tool_name}' 未注册。")
        print(f"Agent '{self.name}' 正在执行工具 '{tool_name}'...")
        return self.tools[tool_name](*args, **kwargs)

if __name__ == "__main__":
    # 示例用法
    class MyAgent(Agent):
        def __init__(self, name: str, description: str):
            super().__init__(name, description)

        def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
            print(f"Agent '{self.name}' 接收到任务: '{task}'")
            if "计算" in task:
                result = self._execute_tool("calculator", 5, 3)
                return f"计算结果: {result}"
            elif "问候" in task:
                result = self._execute_tool("greeter", "世界")
                return f"问候语: {result}"
            else:
                return "无法处理此任务。"

    def simple_calculator(a, b):
        return a + b

    def simple_greeter(name):
        return f"你好, {name}!"

    agent = MyAgent("测试Agent", "一个简单的测试Agent")
    agent.add_tool("calculator", simple_calculator)
    agent.add_tool("greeter", simple_greeter)

    print(agent.run("请帮我计算 5 加 3"))
    print(agent.run("请问候一下"))
    print(agent.run("请问候一下 世界"))
    print(agent.run("未知任务"))