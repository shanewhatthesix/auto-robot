# tools/file_tools.py

import os
from typing import List, Dict, Any

class FileTools:
    """
    文件操作工具集。
    """

    @staticmethod
    def read_file(path: str) -> str:
        """
        读取指定文件的内容。
        :param path: 文件路径
        :return: 文件内容
        :raises FileNotFoundError: 如果文件不存在
        :raises IOError: 如果读取文件时发生错误
        """
        print(f"正在读取文件: {path}")
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise IOError(f"读取文件 '{path}' 失败: {e}")

    @staticmethod
    def write_file(path: str, content: str) -> str:
        """
        向指定文件写入内容。如果文件不存在则创建，存在则覆盖。
        :param path: 文件路径
        :param content: 要写入的内容
        :return: 写入成功消息
        :raises IOError: 如果写入文件时发生错误
        """
        print(f"正在写入文件: {path}")
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"文件 '{path}' 写入成功。"
        except Exception as e:
            raise IOError(f"写入文件 '{path}' 失败: {e}")

    @staticmethod
    def list_directory(path: str = '.') -> List[str]:
        """
        列出指定目录下的文件和子目录。
        :param path: 目录路径，默认为当前目录
        :return: 文件和子目录名称列表
        :raises FileNotFoundError: 如果目录不存在
        """
        print(f"正在列出目录: {path}")
        if not os.path.isdir(path):
            raise FileNotFoundError(f"目录不存在: {path}")
        try:
            return os.listdir(path)
        except Exception as e:
            raise IOError(f"列出目录 '{path}' 失败: {e}")

    @staticmethod
    def delete_file(path: str) -> str:
        """
        删除指定文件。
        :param path: 文件路径
        :return: 删除成功消息
        :raises FileNotFoundError: 如果文件不存在
        :raises OSError: 如果删除文件时发生错误
        """
        print(f"正在删除文件: {path}")
        if not os.path.exists(path):
            raise FileNotFoundError(f"文件不存在: {path}")
        try:
            os.remove(path)
            return f"文件 '{path}' 删除成功。"
        except Exception as e:
            raise OSError(f"删除文件 '{path}' 失败: {e}")

    @staticmethod
    def create_directory(path: str) -> str:
        """
        创建指定目录及其所有父目录。
        :param path: 要创建的目录路径
        :return: 创建成功消息
        :raises OSError: 如果创建目录时发生错误
        """
        print(f"正在创建目录: {path}")
        try:
            os.makedirs(path, exist_ok=True)
            return f"目录 '{path}' 创建成功。"
        except Exception as e:
            raise OSError(f"创建目录 '{path}' 失败: {e}")

if __name__ == "__main__":
    # 示例用法
    test_dir = "test_agent_files"
    test_file = os.path.join(test_dir, "test.txt")
    test_sub_dir = os.path.join(test_dir, "sub_dir")

    print("--- 文件工具测试 ---")

    # 1. 创建目录
    print(FileTools.create_directory(test_dir))

    # 2. 写入文件
    print(FileTools.write_file(test_file, "这是测试文件内容。\n第二行内容。"))

    # 3. 读取文件
    try:
        content = FileTools.read_file(test_file)
        print(f"读取到的内容:\n{content}")
    except Exception as e:
        print(f"读取文件失败: {e}")

    # 4. 列出目录
    print(FileTools.create_directory(test_sub_dir))
    print(FileTools.write_file(os.path.join(test_sub_dir, "sub_file.txt"), "子目录文件。"))
    print(f"'{test_dir}' 目录内容: {FileTools.list_directory(test_dir)}")

    # 5. 删除文件
    print(FileTools.delete_file(test_file))
    print(f"'{test_dir}' 目录内容 (删除后): {FileTools.list_directory(test_dir)}")

    # 清理
    print(FileTools.delete_file(os.path.join(test_sub_dir, "sub_file.txt")))
    os.rmdir(test_sub_dir) # 删除空子目录
    os.rmdir(test_dir) # 删除空主目录
    print("测试完成，清理完毕。")