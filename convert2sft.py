from transformers import AutoModelWithLMHead, AutoTokenizer, pipeline
from tree_sitter import Language, Parser, Node
from tqdm import tqdm
import argparse
import os
import json
import re
import time

gpu_id = int(int(os.environ["LOCAL_RANK"]))


def count_CWE_file(src_path: str) -> int:
    count = 0
    for root, _dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.java') and file.startswith('CWE'):
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


def match_name(node_text: bytes, function_name: str) -> bool:
    function_name_bytes = function_name.encode('utf-8')
    decoded_node_text = node_text.decode('utf-8').strip()
    return decoded_node_text.startswith(function_name_bytes.decode('utf-8'))


# return a list of block of function body with a count of function_name(good* or bad*)
def find_function(node: Node, function_name: str) -> Node:
    count = 0
    node_list = []
    if node == None:
        return None
    if hasattr(node, 'text'):
        if match_name(node.text, function_name):
            return [node.parent], count+1
    for child in node.children:
        sub_list, sub_count = find_function(child, function_name)
        node_list.extend(sub_list)
        count += sub_count
    return node_list, count

def count_good_occurrences(input_string):
    # 将输入字符串转换为小写，以不区分大小写进行匹配
    input_string = input_string.lower()
    
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
    '--library_path', type=str,default='/mnt/42_store/sbc/bug_detection/build/java.so')
argparser.add_argument(
    '--language',type=str,default='java')
argparser.add_argument('--model_name',type=str,default='/mnt/42_store/sbc/trans-opus-mt-en-zh',help="翻译模型的路径")
argparser.add_argument(
    '--dataset_dir', type=str, default="/mnt/42_store/sbc/bug_detection/datasets")
argparser.add_argument('--output_dir', type=str,
                       default="/mnt/42_store/sbc/bug_detection/datasets_new")
args = argparser.parse_args()
JAVA_LANGUAGE = Language(args.library_path, args.language)
parser.set_language(JAVA_LANGUAGE)

mode_name = args.model_name
model = AutoModelWithLMHead.from_pretrained(
    mode_name).bfloat16().to(gpu_id).eval()
tokenizer = AutoTokenizer.from_pretrained(mode_name)
translation = pipeline("translation_en_to_zh", model=model,
                       tokenizer=tokenizer, device=model.device)

dir = args.dataset_dir

file_list = [file_name for file_name in os.listdir(dir)]
# print(file_list)
file_count = 0
data_list = []
for file_name in tqdm(file_list, desc="Processing files"):
    src_path = os.path.join(dir, file_name, "src")
    count, file_path = count_CWE_file(src_path)
    if count > 1:
        continue

    with open(file_path, 'r') as file:
        print(file_path)
        code_string = file.read()
        tree = parser.parse(bytes(code_string, 'utf-8'))
        # TODO 重构
        bad_functions,bad_count = find_function(tree.root_node, "bad")
        good_functions,good_count = find_function(tree.root_node, "good")

        if bad_count == 1:
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
saved_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
output_file_path = os.path.join(args.output_dir, "bug_detection_sft"+saved_date+".json")
print(output_file_path)
with open(output_file_path, 'w') as output_file:
    json.dump(data_list, output_file, ensure_ascii=False, indent=4)
