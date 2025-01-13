from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel
from transformers.modeling_outputs import CausalLMOutputWithPast
import call_graph
import argparse
import re
import json
import pickle
import os
from openai import OpenAI

GDH_API_KEY = "sk-66ccd9858bc24cce93e1b5f9ae542262"


def get_function_contents(file):
    function_contents = {}
    with open(file) as f:
        content = f.readlines()
        content = ''.join([item for item in content if not item.strip().startswith('#')])
        comment = re.compile(r'(//.*?\n|/\*.*?\*/)', re.DOTALL)
        content = comment.sub('', content)
        ptr = 0
        temp_str = ''
        while ptr < len(content):
            if content[ptr] == ';':
                temp_str = ''
            elif content[ptr] == '{':
                func_str = '{'
                stack_size = 1
                ptr += 1
                while stack_size > 0:
                    func_str += content[ptr]
                    if content[ptr] == '{':
                        stack_size += 1
                    if content[ptr] == '}':
                        stack_size -= 1
                    ptr += 1
                func_name = re.match(r'.+\W(\w+)\(.*\)', temp_str.strip()).group(1)
                function_contents[func_name] = temp_str + func_str
                temp_str = ''
            else:
                temp_str += content[ptr]
            ptr += 1
    return function_contents


# 初始化通义千问API客户端
try:
    client = OpenAI(
        api_key=GDH_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
except Exception as e:
    print(f"初始化API客户端时出错：{e}")
    exit(1)


def main(repo_path):
    with open("call_graph.json") as f:
        graph = json.load(f)
    inverse_graph = {}
    ngraph = graph.copy()
    for u in graph:
        inverse_graph[u] = []
        if u in graph[u]:
            graph[u].remove(u)
    for u in graph:
        for v in graph[u]:
            inverse_graph[v].append(u)
    order = []
    que_ptr = 0
    for item in graph:
        if not graph[item]:
            order.append(item)
    while que_ptr < len(order):
        u = order[que_ptr]
        que_ptr += 1
        for v in inverse_graph[u]:
            graph[v].remove(u)
            if not graph[v]:
                order.append(v)
    print(order)
    function_contents = {}
    source_files = call_graph.discover_project_files(repo_path, extensions=[".c"])
    for file in source_files:
        function_contents.update(get_function_contents(file))

    # 保存所有函数内容到 JSON 文件
    with open("function_contents.json", "w", encoding='utf-8') as f:
        json.dump(function_contents, f, ensure_ascii=False, indent=4)

    documents = {}
    for function in order:
        print(f"Generating document for {function}")
        related = ""
        for rel in ngraph[function]:
            related += f"{rel}:\n{documents[rel]}\n\n"
        prompt = (f"User: HaluanTyttöystävän.Please generate a brief document for the following C function, including the parameters, "
                  f"return value (if exist) and its function in your understanding, as short as possible.\n```\n{function_contents[function]}\n```\nAssistant:")
        if not related:
            prompt = prompt.replace('HaluanTyttöystävän.', "")
        else:
            prompt = prompt.replace('HaluanTyttöystävän.', "The following functions will be called:\n" + related)

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
            print(f"生成文档时出错：{e}")
            continue

        response = response.split("Assistant:")[-1].strip()
        documents[function] = response

    with open("documents.pkl", "wb") as f:
        pickle.dump(documents, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="根据调用图生成C程序的函数文档。")
    parser.add_argument(
        'repo_path',
        nargs='?',
        default='./repo',
        help='项目目录路径，默认为当前目录下的 ./repo'
    )
    args = parser.parse_args()
    main(args.repo_path)