import os
from openai import OpenAI
import json
import pickle
import argparse


GDH_API_KEY = "sk-66ccd9858bc24cce93e1b5f9ae542262"
BZY_API_KEY = "sk-a11ed5e5b3a3473e86b42adb46571436"

# 初始化通义千问API客户端
try:
    client = OpenAI(
        api_key=GDH_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
except Exception as e:
    print(f"初始化API客户端时出错：{e}")
    exit(1)

def load_function_docs(doc_file):
    with open(doc_file, 'rb') as f:
        function_docs = pickle.load(f)
    return function_docs

def load_function_contents(content_file):
    with open(content_file, 'r', encoding='utf-8') as f:
        function_contents = json.load(f)
    return function_contents

def load_call_graph(graph_file):
    with open(graph_file, 'r', encoding='utf-8') as f:
        call_graph = json.load(f)
    return call_graph

def generate_repair_prompt(function_name, function_docs, function_contents, related_functions, task_description):
    """
    生成适合大模型的代码修复 Prompt。
    :param function_name: 出错函数名
    :param function_code: 出错函数代码
    :param function_docs: 包含所有函数文档的字典
    :param related_functions: 相关函数列表
    :param task_description: 修复任务描述
    :return: Prompt 字符串
    """
    function_doc = function_docs.get(function_name, "No documentation available for this function.")
    function_code = function_contents.get(function_name, "No code available for this function.")
    
    prompt = f"### Task Description ###\n{task_description}\n\n"
    prompt += f"### Error Function ###\nFunction Name: {function_name}\n\n"
    prompt += f"### Function Documentation ###\n{function_doc}\n\n"
    prompt += f"### Function Code ###\n{function_code}\n\n"
    prompt += "### Related Functions and their contents ###\n"

    for func in related_functions:
        if func in function_contents:
            prompt += f"Function: {func}\n"
            # prompt += f"{function_docs[func]}\n\n"
            prompt += f"{function_contents[func]}\n\n"
            # print(f"Function: {func}\n{function_docs[func]}\n\n")

    prompt += "### Repair Request ###\n"
    prompt += f"Error occurs during compiling in the {function_name} function, please analyze the error in the above code, explain the reasons and provide a fixed version for the error function, considering its context and related functions."
    # prompt += "Finally print the documents of the related functions which I have given you."
    return prompt

def detect_and_fix_errors(function_name, function_docs, function_contents, related_functions, task_description):
    """
    使用大模型对特定函数进行错误检测与修复，并将函数文档注入到 prompt 中进行辅助检测。
    
    参数:
    function_name (str): 函数名
    function_docs (dict): 包含所有函数文档的字典
    function_contents (dict): 包含所有函数内容的字典
    related_functions (list): 相关函数列表
    task_description (str): 任务描述
    
    返回:
    str: 修复后的函数代码
    """
    prompt = generate_repair_prompt(function_name, function_docs, function_contents, related_functions, task_description)
    
    try:
        completion = client.chat.completions.create(
            model="qwen-turbo",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        response = completion.choices[0].message.content
    except Exception as e:
        print(f"生成修复代码时出错：{e}")
        return None

    fixed_code = response.split("Assistant:")[-1].strip()
    print("成功生成修复代码！")
    return fixed_code

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用大模型对特定函数进行错误检测与修复。")
    repair_task = "There are some errors in the function code. Please detect and fix the errors in the function code."
    complete_task = "Please complete the following function code according to the existing code"
    parser.add_argument(
        'function_name',
        help='需要检测和修复的函数名',
        default='main'
    )

    parser.add_argument(
        '--task_type',
        default='repair',
        help='任务类型,repair 为检测和修复错误,complete 为补全代码'
    )
    
    parser.add_argument(
        '--task_description',
        help='任务描述'
    )
    args = parser.parse_args()

    function_docs = load_function_docs("documents.pkl")
    function_contents = load_function_contents("function_contents.json")
    call_graph = load_call_graph("call_graph.json")
    related_functions = call_graph.get(args.function_name, [])
    
    task_description = repair_task if args.task_type == 'repair' else complete_task
    task_description = task_description + args.task_description if args.task_description else task_description

    fixed_code = detect_and_fix_errors(args.function_name, function_docs, function_contents, related_functions, task_description)
    print(f"Fixed code:\n{fixed_code}")