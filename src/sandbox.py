# sandbox.py

import subprocess
import os
import sys
from typing import Dict, Any, Optional

class Sandbox:
    """
    提供一个简易的进程级沙箱环境来执行CLI命令。
    主要通过subprocess模块实现，并提供超时和错误捕获。
    注意：这只是一个简易沙箱，不提供完全的隔离和安全保障，
    对于生产环境或高安全要求场景，应考虑更专业的容器化技术（如Docker）。
    """

    def __init__(self, cwd: Optional[str] = None):
        """
        初始化沙箱。
        :param cwd: 命令执行的工作目录，默认为当前进程的工作目录。
        """
        self.cwd = cwd if cwd else os.getcwd()
        print(f"Sandbox 已初始化，命令将在目录 '{self.cwd}' 中执行。")

    def execute_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """
        在沙箱环境中执行一个CLI命令。
        :param command: 要执行的CLI命令字符串。
        :param timeout: 命令执行的超时时间（秒）。
        :return: 包含命令输出、错误和返回码的字典。
        """
        print(f"Sandbox 正在执行命令: '{command}' (工作目录: {self.cwd})")
        try:
            # 使用subprocess.run执行命令
            # shell=True 允许执行shell命令字符串，但需要注意安全
            # capture_output=True 捕获stdout和stderr
            # text=True (或 encoding='utf-8') 将输出解码为文本
            # check=True 如果返回非零退出码，则抛出CalledProcessError
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return {
                "stdout": process.stdout.strip(),
                "stderr": process.stderr.strip(),
                "returncode": process.returncode,
                "success": True
            }
        except subprocess.CalledProcessError as e:
            # 命令执行失败（非零退出码）
            return {
                "stdout": e.stdout.strip(),
                "stderr": e.stderr.strip(),
                "returncode": e.returncode,
                "success": False,
                "error": f"命令执行失败 (返回码: {e.returncode}): {e.stderr.strip()}"
            }
        except subprocess.TimeoutExpired as e:
            # 命令执行超时
            return {
                "stdout": e.stdout.strip(),
                "stderr": e.stderr.strip(),
                "returncode": -1, # 自定义超时返回码
                "success": False,
                "error": f"命令执行超时 ({timeout}秒): {e}"
            }
        except FileNotFoundError:
            # 命令本身不存在（例如，在Windows上执行'ls'）
            return {
                "stdout": "",
                "stderr": "",
                "returncode": -2, # 自定义命令未找到返回码
                "success": False,
                "error": f"命令 '{command.split(' ')[0]}' 未找到。请检查命令是否正确或已安装。"
            }
        except Exception as e:
            # 其他未知错误
            return {
                "stdout": "",
                "stderr": "",
                "returncode": -3, # 自定义未知错误返回码
                "success": False,
                "error": f"执行命令时发生未知错误: {e}"
            }

if __name__ == "__main__":
    print("--- 沙箱环境测试 ---")

    # 1. 测试基本命令 (列出当前目录文件)
    print("\n--- 测试 'ls -l' 或 'dir' ---")
    current_dir_sandbox = Sandbox()
    command_to_run = "ls -l" if sys.platform != "win32" else "dir"
    result = current_dir_sandbox.execute_command(command_to_run)
    print(f"成功: {result['success']}")
    print(f"返回码: {result['returncode']}")
    print(f"标准输出:\n{result['stdout']}")
    if result['stderr']:
        print(f"标准错误:\n{result['stderr']}")
    if 'error' in result:
        print(f"错误: {result['error']}")

    # 2. 测试不存在的命令
    print("\n--- 测试不存在的命令 'non_existent_command' ---")
    result_fail = current_dir_sandbox.execute_command("non_existent_command")
    print(f"成功: {result_fail['success']}")
    print(f"返回码: {result_fail['returncode']}")
    print(f"标准输出:\n{result_fail['stdout']}")
    if result_fail['stderr']:
        print(f"标准错误:\n{result_fail['stderr']}")
    if 'error' in result_fail:
        print(f"错误: {result_fail['error']}")

    # 3. 测试带参数的命令 (创建并删除一个文件)
    print("\n--- 测试创建和删除文件 ---")
    test_file = "sandbox_test_file.txt"
    create_cmd = f"echo 'Hello Sandbox!' > {test_file}"
    delete_cmd = f"rm {test_file}" if sys.platform != "win32" else f"del {test_file}"

    create_result = current_dir_sandbox.execute_command(create_cmd)
    print(f"创建文件结果: {create_result['success']}")
    if create_result['success']:
        print(f"文件 '{test_file}' 已创建。")
        delete_result = current_dir_sandbox.execute_command(delete_cmd)
        print(f"删除文件结果: {delete_result['success']}")
        if delete_result['success']:
            print(f"文件 '{test_file}' 已删除。")
        else:
            print(f"删除文件失败: {delete_result['error']}")
    else:
        print(f"创建文件失败: {create_result['error']}")

    # 4. 测试超时命令 (模拟一个长时间运行的命令)
    print("\n--- 测试超时命令 (sleep 5秒，超时2秒) ---")
    long_command = "sleep 5" if sys.platform != "win32" else "timeout /t 5"
    timeout_result = current_dir_sandbox.execute_command(long_command, timeout=2)
    print(f"成功: {timeout_result['success']}")
    print(f"返回码: {timeout_result['returncode']}")
    if 'error' in timeout_result:
        print(f"错误: {timeout_result['error']}")

    # 5. 测试在指定工作目录执行命令
    print("\n--- 测试指定工作目录 ---")
    test_dir = "sandbox_test_dir"
    os.makedirs(test_dir, exist_ok=True)
    sandbox_in_subdir = Sandbox(cwd=test_dir)
    result_subdir = sandbox_in_subdir.execute_command(command_to_run)
    print(f"在 '{test_dir}' 中执行命令成功: {result_subdir['success']}")
    print(f"'{test_dir}' 目录内容:\n{result_subdir['stdout']}")
    os.rmdir(test_dir) # 清理测试目录