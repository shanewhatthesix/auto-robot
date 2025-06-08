# tools/system_tools.py

import platform
import psutil
import subprocess
from typing import Dict, Any, List

class SystemTools:
    """
    系统监控工具集。
    """

    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """
        获取系统基本信息。
        :return: 包含系统信息的字典
        """
        print("正在获取系统信息...")
        info = {
            "操作系统": platform.system(),
            "操作系统版本": platform.version(),
            "架构": platform.machine(),
            "处理器": platform.processor(),
            "Python版本": platform.python_version()
        }
        return info

    @staticmethod
    def get_cpu_usage() -> float:
        """
        获取当前CPU使用率。
        :return: CPU使用率百分比
        """
        print("正在获取CPU使用率...")
        return psutil.cpu_percent(interval=0.1)

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """
        获取当前内存使用情况。
        :return: 包含内存使用信息的字典 (总内存, 已用内存, 可用内存, 使用率)
        """
        print("正在获取内存使用情况...")
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent
        }

    @staticmethod
    def list_processes() -> List[Dict[str, Any]]:
        """
        列出当前运行的进程。
        :return: 进程信息列表 (pid, name, cpu_percent, memory_percent)
        """
        print("正在列出进程...")
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    @staticmethod
    def get_current_time() -> str:
        """
        获取当前日期和时间。
        :return: 当前日期和时间的字符串表示
        """
        from datetime import datetime
        print("正在获取当前时间...")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def execute_command(command: str, timeout: int = 60) -> Dict[str, Any]:
        """
        执行一个CLI命令并返回其输出。
        注意：此工具应在沙箱环境中谨慎使用，以防恶意命令。
        :param command: 要执行的CLI命令字符串
        :param timeout: 命令执行超时时间（秒）
        :return: 包含命令输出、错误和返回码的字典
        """
        print(f"正在执行命令: '{command}'")
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True # 如果返回非零退出码，则抛出CalledProcessError
            )
            return {
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip(),
                "returncode": process.returncode
            }
        except subprocess.CalledProcessError as e:
            return {
                "stdout": e.stdout.strip(),
                "stderr": e.stderr.strip(),
                "returncode": e.returncode,
                "error": f"命令执行失败: {e}"
            }
        except subprocess.TimeoutExpired as e:
            return {
                "stdout": e.stdout.strip(),
                "stderr": e.stderr.strip(),
                "returncode": -1, # 表示超时
                "error": f"命令执行超时 ({timeout}秒): {e}"
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": "",
                "returncode": -2, # 表示其他错误
                "error": f"执行命令时发生未知错误: {e}"
            }

if __name__ == "__main__":
    print("--- 系统工具测试 ---")

    # 1. 获取系统信息
    print("\n系统信息:")
    info = SystemTools.get_system_info()
    for k, v in info.items():
        print(f"  {k}: {v}")

    # 2. 获取CPU使用率
    print(f"\nCPU使用率: {SystemTools.get_cpu_usage()}%")

    # 3. 获取内存使用情况
    print("\n内存使用:")
    mem_info = SystemTools.get_memory_usage()
    for k, v in mem_info.items():
        print(f"  {k}: {v}")

    # 4. 列出进程 (可能需要管理员权限或在某些系统上受限)
    print("\n部分进程信息:")
    processes = SystemTools.list_processes()
    for i, proc in enumerate(processes[:5]): # 只显示前5个
        print(f"  PID: {proc.get('pid')}, Name: {proc.get('name')}, CPU: {proc.get('cpu_percent')}%, Mem: {proc.get('memory_percent')}%")
    if len(processes) > 5:
        print(f"  ... (共 {len(processes)} 个进程)")

    # 5. 执行命令 (示例：列出当前目录文件)
    print("\n执行命令 'ls -l' (或 'dir' on Windows):")
    command_to_run = "ls -l" if platform.system() != "Windows" else "dir"
    cmd_result = SystemTools.execute_command(command_to_run)
    print(f"  Return Code: {cmd_result['returncode']}")
    print(f"  Stdout:\n{cmd_result['stdout']}")
    if cmd_result['stderr']:
        print(f"  Stderr:\n{cmd_result['stderr']}")
    if 'error' in cmd_result:
        print(f"  Error: {cmd_result['error']}")

    # 6. 执行一个不存在的命令 (错误示例)
    print("\n执行不存在的命令 'non_existent_command':")
    cmd_result_fail = SystemTools.execute_command("non_existent_command")
    print(f"  Return Code: {cmd_result_fail['returncode']}")
    print(f"  Stdout:\n{cmd_result_fail['stdout']}")
    if cmd_result_fail['stderr']:
        print(f"  Stderr:\n{cmd_result_fail['stderr']}")
    if 'error' in cmd_result_fail:
        print(f"  Error: {cmd_result_fail['error']}")