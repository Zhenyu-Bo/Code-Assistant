import argparse
import json
import subprocess
import re
from collections import defaultdict
import os

def discover_project_files(repo_path, extensions):
    """
    遍历指定目录，查找符合扩展名的文件。

    参数:
        repo_path (str): 项目目录路径。
        extensions (list): 文件扩展名列表，如 ['.c', '.h']。

    返回:
        list: 符合条件的文件路径列表。
    """
    matched_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                matched_files.append(os.path.join(root, file))
    return matched_files

def generate_call_graph(repo_path):
    """
    使用 Clang 命令生成函数调用关系邻接表，并去除标准头文件中的函数。

    参数:
        repo_path (str): C 代码所在的目录路径。

    返回:
        dict: 函数调用关系的邻接表。
    """
    call_graph = defaultdict(list)
    user_functions = set()

    # 遍历所有 .c 文件
    source_files = discover_project_files(repo_path, extensions=[".c"])

    # 收集所有用户自定义的函数
    for file in source_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 匹配函数定义（简化版）
                functions = re.findall(r'\b\w+\s+\w+\s*\(.*?\)\s*\{', content)
                for func in functions:
                    func_name = re.findall(r'\b\w+\s+(\w+)\s*\(.*?\)\s*\{', func)
                    if func_name:
                        user_functions.add(func_name[0])
                        call_graph[func_name[0]] = []
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")

    # 输出用户自定义函数列表
    print(f"用户自定义函数: {', '.join(user_functions)}")

    for file in source_files:
        try:
            # 执行 Clang 命令，添加 -c 以仅进行编译，避免链接错误
            result = subprocess.run(
                [
                    "clang",
                    "-Xclang",
                    "-analyzer-checker=debug.DumpCallGraph",
                    "-Xclang",
                    "-analyze",
                    # "-c",  # 仅编译，不链接
                    file
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                # 移除 check=True，以便即使 Clang 返回错误也能继续处理
                check=False
            )

            output = result.stdout
            error_output = result.stderr
            combined_output = output + error_output
            
            # 保存clang的报错信息到error_output.log中以便后续使用
            with open('error_output.log', 'w', encoding='utf-8') as f:
                f.write(error_output)
                f.write('\n')
            
            # 解析调用图输出
            for line in combined_output.splitlines():
                # 解析格式为 "Function: A calls: B1 B2 ..."
                match = re.match(r'\s+Function:\s+(\w+)\s+calls:\s+(.+)', line)
                if match:
                    caller = match.group(1)
                    callees = match.group(2).split()
                    # for callee in callees:
                    #     call_graph[caller].append(callee)
                    # 仅保留用户自定义函数之间的调用关系
                    if caller in user_functions:
                        for callee in callees:
                            if callee in user_functions and callee not in call_graph[caller]:
                                call_graph[caller].append(callee)

        except Exception as e:
            print(f"分析文件 {file} 时出错: {e}")

    # 打印调用关系
    if call_graph:
        for caller, callees in call_graph.items():
            print(f"{caller}: {', '.join(callees)}")
    else:
        print("未检测到任何函数调用关系。")

    return call_graph

def main(repo_path):
    # 生成调用关系邻接表
    adjacency_list = generate_call_graph(repo_path)

    # 将邻接表保存为 JSON 文件
    output_file = 'call_graph.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(adjacency_list, f, indent=4, ensure_ascii=False)
        print(f"函数调用关系已保存到 {output_file}")
    except Exception as e:
        print(f"保存调用关系到 {output_file} 时出错: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成C程序的函数调用关系图。")
    parser.add_argument(
        'repo_path',
        nargs='?',
        default='./repo',
        help='项目目录路径，默认为当前目录下的 ./repo'
    )
    args = parser.parse_args()
    main(args.repo_path)