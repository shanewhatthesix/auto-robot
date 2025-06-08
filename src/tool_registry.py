# tool_registry.py

from typing import Dict, Callable, Any, Optional # 新增导入 Optional
import inspect

class ToolRegistry:
    """
    工具注册中心，用于管理Agent可用的所有工具。
    工具可以是任何可调用的函数或静态方法。
    """
    _instance: Optional['ToolRegistry'] = None # 明确_instance的类型

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance._tools = {} # 移除这里的类型批注，在__init__中处理
            print("ToolRegistry 单例已初始化。")
        return cls._instance

    def __init__(self):
        # 确保 _tools 只在第一次初始化时设置类型
        if not hasattr(self, '_initialized'):
            self._tools: Dict[str, Callable] = {}
            self._initialized = True

    def register_tool(self, tool_name: str, tool_func: Callable):
        """
        注册一个工具。
        :param tool_name: 工具的唯一名称
        :param tool_func: 工具对应的可调用函数或静态方法
        """
        if not callable(tool_func):
            raise TypeError(f"注册失败: '{tool_func}' 不是一个可调用的对象。")
        self._tools[tool_name] = tool_func
        print(f"工具 '{tool_name}' 已注册。")

    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """
        根据名称获取已注册的工具。
        :param tool_name: 工具名称
        :return: 工具函数，如果不存在则返回None
        """
        return self._tools.get(tool_name)

    def get_all_tools(self) -> Dict[str, Callable]:
        """
        获取所有已注册的工具。
        :return: 包含所有工具的字典 {tool_name: tool_function}
        """
        return self._tools

    def get_tool_signature(self, tool_name: str) -> Dict[str, Any]:
        """
        获取工具的函数签名信息，包括参数名称和类型。
        这对于LLM理解如何调用工具非常有用。
        :param tool_name: 工具名称
        :return: 包含参数信息的字典
        :raises ValueError: 如果工具未注册
        """
        tool_func = self.get_tool(tool_name)
        if not tool_func:
            raise ValueError(f"工具 '{tool_name}' 未注册。")

        signature = inspect.signature(tool_func)
        params_info = {}
        for name, param in signature.parameters.items():
            param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
            params_info[name] = {
                "type": param_type,
                "default": str(param.default) if param.default != inspect.Parameter.empty else "NoDefault"
            }
        return params_info

    def register_class_tools(self, tool_class: Any):
        """
        注册一个类中的所有静态方法或普通方法作为工具。
        如果方法名以'_'开头，则不注册。
        :param tool_class: 包含工具方法的类
        """
        print(f"正在注册类 '{tool_class.__name__}' 中的工具...")
        for name in dir(tool_class):
            if name.startswith('_'):
                continue
            attr = getattr(tool_class, name)
            # 检查是否是可调用的方法（排除类属性）
            if inspect.isfunction(attr) or inspect.ismethod(attr):
                # 对于实例方法，需要绑定到实例
                if inspect.ismethod(attr) and not inspect.isbuiltin(attr): # 排除内置方法
                    # 如果是普通方法，需要一个实例来调用
                    # 这里我们假设工具类的方法都是静态方法或类方法，或者在Agent中通过实例调用
                    # 为了简化，我们只注册静态方法或类方法，或者直接注册函数
                    # 如果是普通方法，需要确保它能被正确调用，这里暂时不处理实例方法
                    # 更好的做法是让Agent持有工具类的实例
                    pass
                else:
                    self.register_tool(name, attr)
            elif inspect.isclass(attr):
                # 忽略嵌套类
                pass
            else:
                # 忽略其他属性
                pass
        print(f"类 '{tool_class.__name__}' 中的工具注册完成。")


if __name__ == "__main__":
    # 示例工具类
    class MyTestTools:
        @staticmethod
        def add(a: int, b: int) -> int:
            """计算两个数的和。"""
            return a + b

        @staticmethod
        def subtract(a: int, b: int) -> int:
            """计算两个数的差。"""
            return a - b

        def _private_method(self):
            """私有方法不应被注册。"""
            pass

        def instance_method(self, x: str):
            """实例方法，通常不直接注册，除非有特定实例。"""
            return f"实例方法调用: {x}"

    def greet(name: str = "World") -> str:
        """问候语。"""
        return f"Hello, {name}!"

    # 获取ToolRegistry单例
    registry = ToolRegistry()

    # 注册单个函数
    registry.register_tool("greeter", greet)

    # 注册类中的静态方法
    registry.register_class_tools(MyTestTools)

    print("\n--- 已注册工具 ---")
    for name, func in registry.get_all_tools().items():
        print(f"- {name}: {func.__doc__.strip() if func.__doc__ else '无描述'}")

    print("\n--- 获取工具签名 ---")
    try:
        print(f"签名 'add': {registry.get_tool_signature('add')}")
        print(f"签名 'greeter': {registry.get_tool_signature('greeter')}")
    except ValueError as e:
        print(e)

    print("\n--- 调用工具 ---")
    add_func = registry.get_tool("add")
    if add_func:
        print(f"10 + 5 = {add_func(10, 5)}")

    greeter_func = registry.get_tool("greeter")
    if greeter_func:
        print(greeter_func("Agent"))

    # 尝试获取未注册的工具
    print("\n--- 尝试获取未注册工具 ---")
    unknown_tool = registry.get_tool("unknown_tool")
    print(f"获取 'unknown_tool': {unknown_tool}")

    # 验证私有方法未被注册
    print("\n--- 验证私有方法 ---")
    private_method = registry.get_tool("_private_method")
    print(f"获取 '_private_method': {private_method}")

    # 验证实例方法未被直接注册 (因为这里没有实例)
    print("\n--- 验证实例方法 ---")
    instance_method = registry.get_tool("instance_method")
    print(f"获取 'instance_method': {instance_method}")