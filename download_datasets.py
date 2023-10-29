import json
import os
import threading
import argparse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
parser = argparse.ArgumentParser()
parser.add_argument('--output_dir',type=str,default="/mnt/42_store/sbc/bug_detection/data_zips")
parser.add_argument('--api_dir',type=str,default="/mnt/42_store/sbc/bug_detection/apis1029")
args = parser.parse_args()
output_dir = args.output_dir
os.system("mkdir -p "+output_dir)
# api_file = "/mnt/42_store/sbc/bug_detection/api.json"
api_dir = args.api_dir
def download_thread(download_url, output_dir):
    os.system("wget -P " + output_dir + ' -qnc ' + download_url)
api_files=[file for file in os.listdir(api_dir) if file.endswith(".json")]
count=0
with ThreadPoolExecutor(max_workers=25) as executor:
    for api_file in api_files:
        with open(os.path.join(api_dir, api_file), 'r') as file:
            testCases = json.load(file)["testCases"]
            for case in testCases:
                download_url = case["download"]
                # thread = threading.Thread(target=download_thread, args=(download_url, output_dir))
                # thread.start()
                executor.submit(download_thread,download_url,output_dir)
                # thread.start()
                count+=1
print(count)
os.system("bash /mnt/42_store/sbc/bug_detection/extract.sh")