import json
import os
import threading
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
parser = argparse.ArgumentParser()
current_dir = Path.cwd()
parser.add_argument('--output_dir',type=str,default=current_dir/"data_zips")
parser.add_argument('--api_dir',type=str,default=current_dir/"apis")
args = parser.parse_args()
output_dir = current_dir/args.output_dir
print("output_dir: ",output_dir)
os.system("mkdir -p "+str(output_dir))
# api_file = "api.json"
api_dir = args.api_dir
def download_thread(download_url, output_dir):
    # print("downloading...")
    cmd = "wget -P " + str(output_dir) + ' -nc ' + download_url
    print(cmd)

    os.system(cmd)
api_files=[file for file in os.listdir(api_dir) if file.endswith(".json")]
count=0
# print(api_files)
with ThreadPoolExecutor(max_workers=25) as executor:
    for api_file in api_files:
        with open(os.path.join(api_dir, api_file), 'r') as file:
            testCases = json.load(file)["testCases"]
            # print(testCases)
            for case in testCases:
                download_url = case["download"]
                # print(download_url)
                # thread = threading.Thread(target=download_thread, args=(download_url, output_dir))
                # thread.start()
                executor.submit(download_thread,download_url,output_dir)
                # thread.start()
                count+=1
print(count)
# os.system("bash "+str(current_dir/"extract.sh"))