from openai import OpenAI
import json
import argparse


from dotenv import load_dotenv
load_dotenv()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# 初始化通义千问API客户端
try:
    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
except Exception as e:
    print(f"初始化API客户端时出错：{e}")
    exit(1)

def load_function_contents(content_file):
    with open(content_file, 'r', encoding='utf-8') as f:
        function_contents = json.load(f)
    return function_contents

def generate_repair_prompt(function_name, function_contents, task_description, additional_description):
    function_code = function_contents.get(function_name, "No code available for this function.")
    
    prompt = f"### Task Description ###\n{task_description}\n\n"
    prompt += f"### Error Function ###\nFunction Name: {function_name}\n\n"
    prompt += f"### Function Code ###\n{function_code}\n\n"

    prompt += "### Repair Request ###\n"
    prompt += additional_description
    prompt += f"请详细分析{function_name}函数的代码，找出错误并修复。"
    # prompt += "Please analyze the error in the above code, explain the reasons and provide a fixed version for the error function, considering its context and related functions."
    # prompt += f"Note that problems may arise in {function_name} and the related functions."
    # prompt += "Finally print the documents of the related functions which I have given you."
    return prompt

def detect_and_fix_errors(function_name, function_contents, task_description, additional_description):
    prompt = generate_repair_prompt(function_name, function_contents, task_description, additional_description)
    
    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
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
    
    args = parser.parse_args()
    function_name = args.function_name
    
    additional_description = f"这个函数期望计算a的b次方对m的取模结果,但是并未成功获得正确的结果，请检查并修复错误，并给出原因。注意问题可能出现在{function_name}中，也可能出现在其调用的函数中,所以在检查一个函数时，你不仅需要检查该函数的实现是否存在问题，还要检查它调用的函数的实现是否正确。"

    function_contents = load_function_contents("function_contents.json")

    task_description = repair_task if args.task_type == 'repair' else complete_task

    fixed_code = detect_and_fix_errors(args.function_name, function_contents, task_description, additional_description)
    print(f"Fixed code:\n{fixed_code}")
