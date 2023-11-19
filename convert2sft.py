from transformers import AutoModelWithLMHead, AutoTokenizer, pipeline
from tree_sitter import Language, Parser, Node
from tqdm import tqdm
import argparse
import os
import json
import re
import time
import torch.distributed as dist
import pdb
from typing import Union

gpu_id = int(int(os.environ["LOCAL_RANK"]))


def count_CWE_file(src_path: str,language: str) -> int:
    count = 0
    file_path=""
    for root, _dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.'+language) and file.startswith('CWE'):
                file_path = os.path.join(root, file)
                count += 1
    return count, file_path


def build_json_item(file_count: int, bad_code_string: str, good_code_string: str, comments_translated: str) -> dict:
    meta_data = {
        "id": file_count,
        "instructions": "帮我修改一下代码的漏洞",
        "conversations": [
            {
                "from": "human",
                "value": bad_code_string.replace("private ", "public ")
            },
            {
                "from": "gpt",
                "value": comments_translated+good_code_string.replace("private ", "public ")
            }
        ]
    }
    return meta_data


def build_translated_comments(translated: list) -> str:
    comments_translated = ""
    if len(translated) != 0:
        comments_translated += "/* "
    for comment in translated:
        comments_translated += comment["translation_text"]+'\n* '
    if len(translated) != 0:
        comments_translated += " */\n"
    return comments_translated

def node_filter(node_list: list)->list:
    del_node = []
    method_names = []
    for node in node_list:
        for node_element in node.children:
            if node_element.type == "identifier":
                method_names.append(node_element.text.decode())
                continue
    for i,node in enumerate(node_list):
        for node_element in node.children:
            if node_element.type == "identifier":
                method_name = node_element.text.decode()
                print("method_name: ",method_name)
                if method_name == "good":
                    del_node.append(node)
                    continue
                elif method_name.startswith('good'):
                    assert node.children[-1].type == 'block', print(node.children)
                    # TODO remove involed function
                    # if node.children[-1].find('good'):
                    #     del_node.append(node)
                    #     continue
                    for invovled_method in method_names:
                        if node.children[-1].text.decode().find(invovled_method)!=-1:
                            del_node.append(node)
                            break
                    continue
                else:
                    raise RuntimeError("function name is not good*()")
    return [node for node in node_list if node not in del_node]
    

def match_name(node_text: bytes, function_name: str) -> bool:
    function_name_bytes = function_name.encode('utf-8')
    decoded_node_text = node_text.decode('utf-8').strip()
    if function_name=='good':
        return function_name_bytes.decode('utf-8') in decoded_node_text and (not decoded_node_text==function_name_bytes.decode('utf-8'))
    return function_name_bytes.decode('utf-8') in decoded_node_text


# return a list of block of function body with a count of function_name(good* or bad*)
# dfs
def find_function(node: Node, function_name: str, language: str) -> Node:
    # print(node.type)
    method_type = "method_declaration" if language=="java" else "function_definition"
    node.child_by_field_name
    count = 0
    node_list = []
    if node is None:
        return None
    if hasattr(node, 'text'):
        # TODO match function name, instead of node.text
        if match_name(node.text, function_name):
            if node.parent is None:
                pdb.set_trace()
            if node.parent.type == method_type:
                return [node.parent], count+1
    for child in node.children:
        sub_list, sub_count = find_function(child, function_name, language)
        node_list.extend(sub_list)
        count += sub_count
    return node_list, count
from peft import LoraConfig
def count_good_occurrences(input_string):    
    # 初始化计数器
    count = 0
    
    # 寻找 "good" 的次数
    index = input_string.find("good")
    while index != -1:
        count += 1
        # 从下一个位置开始继续查找
        index = input_string.find("good", index + 4)  # 4 是 "good" 的长度
    
    return count


parser = Parser()
argparser = argparse.ArgumentParser()
argparser.add_argument(
    '--library_path', type=str,default='build/java.so')
argparser.add_argument(
    '--language',type=str,default='java')
argparser.add_argument('--model_path',type=str,default='/mnt/42_store/sbc/trans-opus-mt-en-zh',help="翻译模型的路径")
argparser.add_argument(
    '--dataset_dir', type=str, default="datasets")
argparser.add_argument('--output_dir', type=str,
                       default="datasets_sft")
args = argparser.parse_args()
JAVA_LANGUAGE = Language(args.library_path, args.language)
parser.set_language(JAVA_LANGUAGE)

mode_name = args.model_path
model = AutoModelWithLMHead.from_pretrained(
    mode_name).bfloat16().to(gpu_id).eval()
tokenizer = AutoTokenizer.from_pretrained(mode_name)
translation = pipeline("translation_en_to_zh", model=model,
                       tokenizer=tokenizer, device=model.device)

dataset_dir = args.dataset_dir

file_list = [file_name for file_name in os.listdir(dataset_dir)]
# print(file_list)
file_count = 0
data_list = []
for file_name in tqdm(file_list, desc="Processing files"):
    src_path = os.path.join(dataset_dir, file_name, "src")
    count, file_path = count_CWE_file(src_path,args.language)
    # pdb.set_trace()
    if count > 1 or count==0:
        continue

    with open(file_path, 'r') as file:
        print(file_path)
        code_string = file.read()
        tree = parser.parse(bytes(code_string, 'utf-8'))
        # TODO 重构
        bad_functions,bad_count = find_function(tree.root_node, "bad", args.language)
        print("bad_count:",bad_count)
        if bad_count > 1:
            continue
        if bad_count == 1:
            import pdb
            good_functions,good_count = find_function(tree.root_node, "good", args.language)
            # pdb.set_trace()
            good_functions = node_filter(good_functions)
            # pdb.set_trace()
            bad_code_string = bad_functions[0].text.decode()
            bad_code_string = re.sub(
                r'/\*([^*]|(\*+[^*/]))*\*+/', '', bad_code_string)
            bad_code_string = re.sub(
                r'bad[^\(]*\(', 'function(', bad_code_string)

            if len(good_functions)>0:
                good_code_string=""
                # import pdb
                # pdb.set_trace()
                # 找到第一个没有调用goodxxx()的函数
                for good_function in good_functions:
                    good_code_string = good_function.text.decode()
                    if count_good_occurrences(good_code_string)==1:
                        break
                
                good_code_string = re.sub(
                    r'good[^\(]*\(', 'function(', good_code_string)
                # get all comments in function body
                comments = list(re.findall(
                    r'/\*(.*?)\*/', good_code_string, re.S))
                # replace comments in function body
                good_code_string = re.sub(
                    r'/\*([^*]|(\*+[^*/]))*\*+/', '', good_code_string)

                # if len(re.findall(r'[ ]+function\(([a-zA-Z]*[0-9]*[_]*|[,]*|[ ]*)*\);\\n', good_code_string, re.S)) > 1:
                #     import pdb
                #     print(file_path)
                #     pdb.set_trace()
                #     continue

                translated = translation(comments, max_length=400)

            else:
                print(good_function)
                print(file_path)
                continue


            comments_translated = build_translated_comments(translated)
            meta_data = build_json_item(
                file_count, bad_code_string, good_code_string, comments_translated)
            data_list.append(meta_data)

            file_count += 1
print(len(data_list))
print(args.output_dir)
os.system("mkdir -p "+args.output_dir)
saved_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
output_file_path = os.path.join(args.output_dir, "bug_detection_sft"+saved_date+".json")
print(output_file_path)

with open(output_file_path, 'w') as output_file:
    json.dump(data_list, output_file, ensure_ascii=False, indent=4)
