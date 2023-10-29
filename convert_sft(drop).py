import pandas as pd 
import numpy as np
import json
import os 
file_path = "/mnt/42_store/sbc/bug_detection/VD_java_results.csv"
file = pd.read_csv(file_path)
df = pd.DataFrame(file)
# print(df.head())
content = df[['code','flag']]
print(content.head())
output_file=os.path.join(*os.path.split(file_path)[:-1],'VD_java_sft.csv')
print(len(content))
data_list=[]
# print(df['flag'][0].dtype)
# print(df['code'][0].dtype)
for i in range(len(content)):
    item={
        "id":i,
        "instructions": "这段代码有漏洞吗",
        "conversations":[
            {
                "from":"human",
                "value":df['code'][i]
            },
            {
                "from":"gpt",
                "value":int(df['ori_code'][i])
            }
        ]
    }
    data_list.append(item)
with open(output_file,'w') as of:
    json.dump(data_list,of,ensure_ascii=False,indent=4)