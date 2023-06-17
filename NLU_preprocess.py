import os
import json
import glob
from typing import Dict, Any

def process_directory(parent_dir: str, output_dir: str, ):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 遍历父文件夹中的所有子文件夹
    for user_dir in os.listdir(parent_dir):
        # 检查是否为文件夹
        if os.path.isdir(os.path.join(parent_dir, user_dir)):
            jsonl_data = []
            
            # 在当前子文件夹中查找所有的json文件
            for file in glob.glob(os.path.join(parent_dir, user_dir, "result*.json")):
                # 读取json文件并转化为字典
                with open(file, 'r') as json_file:
                    data = json.load(json_file)
                
                # 从文件名中获取id，即result后面的数字部分
                file_id = os.path.basename(file).split('.')[0].replace("result", "")
                
                event_list = []
                for event, e_list in data.items():
                    for e in e_list:
                        add_dict = {"事件": event}
                        for k,v in e.items():
                            if len(v) != 0:
                                add_dict[k] = v
                        
                        if len(e) != 0:
                            event_list.append(add_dict)
                

                # 创建新的数据结构
                new_data = {
                    'id': file_id,
                    'event_list': event_list,
                }
                jsonl_data.append(new_data)

            # 将jsonl数据写入到新的jsonl文件
            with open(os.path.join(output_dir, user_dir + '.jsonl'), 'w') as jsonl_file:
                jsonl_data = sorted(jsonl_data, key=lambda x: int(x['id']))
                for entry in jsonl_data:
                    jsonl_file.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    


def evaluate_event_extraction(pred: list, target: list) -> dict:
    event_TP, event_FP, event_FN = 0, 0, 0
    trigger_TP, trigger_FP, trigger_FN = 0, 0, 0
    element_TP, element_FP, element_FN = 0, 0, 0

    # Compute event level metrics
    for p in pred:
        if p in target:
            event_TP += 1
        else:
            event_FP += 1
    for t in target:
        if t not in pred:
            event_FN += 1

    # Compute trigger and other elements level metrics
    for p in pred:
        for t in target:
            if p['事件'] == t['事件']:
                if '触发词' in p and (t['触发词'] in p['触发词']):
                    trigger_TP += 1
                else:
                    trigger_FP += 1

                for key in p.keys():
                    # if key not in ['事件', '触发词']:
                    if key in t and (t[key] in p[key] or p[key] in t[key]):
                        element_TP += 1
                    else:
                        element_FP += 1

    for t in target:
        find_flag = False
        for p in pred:
            if t['事件'] == p['事件']:
                find_flag = True
                trigger_list = []
                for e in pred:
                    if e['事件'] == p['事件'] and '触发词' in e:
                        trigger_list.append(e['触发词'])

                target_trigger = t['触发词']
                cover_flag = False
                for the_t in trigger_list:
                    if target_trigger in the_t or the_t in target_trigger:
                        cover_flag = True
                
                if cover_flag == False:
                    trigger_FN += 1

                for key in t.keys():
                    # if key not in ['事件', '触发词']:
                    if key not in p or (t[key] not in p[key] and p[key] not in t[key]):
                        element_FN += 1

        # if find_flag == False:
        #     trigger_FN += 1

        #     for key in t.keys():
        #             # if key not in ['事件', '触发词']:
        #             element_FN += 1



    return {
        'event': {'TP': event_TP, 'FP': event_FP, 'FN': event_FN},
        'trigger': {'TP': trigger_TP, 'FP': trigger_FP, 'FN': trigger_FN},
        'element': {'TP': element_TP, 'FP': element_FP, 'FN': element_FN},
    }


import json

def evaluate_jsonl_files(pred_file: str, target_file: str) -> dict:
    with open(pred_file, 'r') as f:
        pred = [json.loads(line) for line in f]
    with open(target_file, 'r') as f:
        target = [json.loads(line) for line in f]

    results = {
        'event': {'TP': 0, 'FP': 0, 'FN': 0},
        'trigger': {'TP': 0, 'FP': 0, 'FN': 0},
        'element': {'TP': 0, 'FP': 0, 'FN': 0},
    }

    # Compute TP, FP and FN for each event list
    for pred_event, target_event in zip(pred, target):
        pred_events = pred_event['event_list']
        target_events = target_event['event_list']
        temp_results = evaluate_event_extraction(pred_events, target_events)
        for category, values in temp_results.items():
            results[category]['TP'] += values['TP']
            results[category]['FP'] += values['FP']
            results[category]['FN'] += values['FN']

    # Compute precision, recall and F1 score
    for category, values in results.items():
        TP, FP, FN = values['TP'], values['FP'], values['FN']
        P = TP / (TP + FP) if TP + FP > 0 else 0
        R = TP / (TP + FN) if TP + FN > 0 else 0
        F1 = 2 * P * R / (P + R) if P + R > 0 else 0
        results[category]['P'] = P
        results[category]['R'] = R
        results[category]['F1'] = F1

    return results

def print_evaluation_results(results: dict):
    for category, values in results.items():
        print(f"{category.capitalize()} Evaluation Results:")
        print(f"  TP: {values['TP']}")
        print(f"  FP: {values['FP']}")
        print(f"  FN: {values['FN']}")
        print(f"  Precision (P): {values['P']:.4f}")
        print(f"  Recall (R): {values['R']:.4f}")
        print(f"  F1 Score: {values['F1']:.4f}")
        print()


import os

def evaluate_folder(folder_path: str, target_file: str, tag = 'event_list'):
    # Initialize counters for combined results
    combined_results = {
        'event': {'TP': 0, 'FP': 0, 'FN': 0},
        'trigger': {'TP': 0, 'FP': 0, 'FN': 0},
        'element': {'TP': 0, 'FP': 0, 'FN': 0},
    }

    # Iterate over all jsonl files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".jsonl"):
            print(f"Evaluating {filename}:")
            file_path = os.path.join(folder_path, filename)

            # Evaluate file and print results
            results = evaluate_jsonl_files(file_path, target_file)
            print_evaluation_results(results)

            # Update combined results
            for category in combined_results:
                combined_results[category]['TP'] += results[category]['TP']
                combined_results[category]['FP'] += results[category]['FP']
                combined_results[category]['FN'] += results[category]['FN']

    # Calculate P, R and F1 for combined results
    print("Combined Evaluation Results:")
    for category, values in combined_results.items():
        TP, FP, FN = values['TP'], values['FP'], values['FN']
        P = TP / (TP + FP) if TP + FP > 0 else 0
        R = TP / (TP + FN) if TP + FN > 0 else 0
        F1 = 2 * P * R / (P + R) if P + R > 0 else 0
        combined_results[category]['P'] = P
        combined_results[category]['R'] = R
        combined_results[category]['F1'] = F1

    # Print combined results
    print("Final result:")
    print_evaluation_results(combined_results)


event_names = [
    "出售/收购",
    "跌停",
    "加息",
    "降价",
    "降息",
    "融资",
    "上市",
    "涨价",
    "涨停"
]

event_elements = [
    '时间', '出售方', '交易物', '出售价格', '收购方', '跌停股票',
    '加息幅度', '加息机构', '降价方', '降价物', '降价幅度',
    '降息幅度', '降息机构', '跟投方', '领投方', '融资轮次',
    '融资金额', '融资方', '地点', '上市企业', '涨价幅度',
    '涨价物', '涨价方', '涨停股票', '触发词'
]


def preprocess_auto_label(input_file, output_file, tag = 'output'):
    import json
    import re

    # 读取jsonl文件
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    new_lines = []  # 用来存储处理过的行

    for line in lines:
        json_dict = json.loads(line)  # 把每一行转换为json字典
        input_text = json_dict["input"]  # 获取input项
        output_list = json_dict[tag]  # 获取output项，它是一个列表
        
        new_output_list = []  # 用来存储处理过的output项
        
        for output in output_list:  # 遍历output列表中的每一项
            try:
                event = output.get("事件")  # 获取"事件"字段
                if event not in event_names:
                    continue
                
                add_dict = {}
                for k, v in output.items():
                    if k == '事件':
                        add_dict[k] = v

                    if type(v) ==str and k in event_elements and v in input_text:
                        add_dict[k] = v

                if len(add_dict) != 0:
                    new_output_list.append(add_dict)
            except Exception as e:
                # print(e)
                continue

        json_dict["event_list"] = new_output_list  # 更新json字典中的output项
        
        new_lines.append(json.dumps(json_dict, ensure_ascii=False))  # 把处理过的json字典转换回json字符串，并添加到new_lines中

    # 把处理过的行写入新的jsonl文件
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in new_lines:
            file.write(line + '\n')



import json

def compare_files(txt_file, jsonl_file):
    with open(txt_file, 'r') as txt, open(jsonl_file, 'r') as jsonl:
        for i, (line_txt, line_jsonl) in enumerate(zip(txt, jsonl), 1):
            # 解析jsonl文件的一行
            data = json.loads(line_jsonl)
            if 'input' in data:
                # 去除txt文件和jsonl文件中行尾的换行符，然后比较
                if line_txt.rstrip('\n') != data['input']:
                    print(f'两个文件的第一个不同出现在第{i}行')
                    return

    print('两个文件没有找到不同')

# # 调用函数
# compare_files('file1.txt', 'file2.jsonl')




if __name__ == '__main__':
    # # 转换标注数据
    # input_folder = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/NLU_label_6.14'
    # output_folder = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/huaman_label'
    # process_directory(input_folder, output_folder)

    list_1 = [{"事件": "降价", "触发词": "跌至", "降价方": "OPPO", "降价物": "OPPO R17", "降价幅度": "1400"}]
    list_2 =[{"事件": "降价", "触发词": "跌至", "降价方": "OPPO", "降价物": "OPPO R17", "降价幅度": "1400"}]

    label_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label_converted.json'

    # # 评估标注结果
    human_level_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/huaman_label/result（常261-852）.jsonl'



    label_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_special.json'
    # # results = evaluate_jsonl_files(human_level_file, label_file)
    huaman_label_dir = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/huaman_label' 
    evaluate_folder(huaman_label_dir, label_file)

    compare_files('/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/inputtexture.txt', label_file)



    label_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label_converted.json'
    # 转化ChatGPT原始标注
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_chatgpt_vote_random.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_label_3.json'
    preprocess_auto_label(input_file, output_file, tag='origin_output')

    # 评估ChatGPT
    print('ChatGPT 原始')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)


    # 转化GPT4原始标注
    # input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_label_3.json'
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_gpt4_vote_major.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_label_4.json'
    preprocess_auto_label(input_file, output_file, tag='origin_output')

    # 评估GPT4
    print('GPT4 原始')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)

    # 转化ChatGPT原始标注
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_chatgpt_vote_random.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_correction_label.json'
    preprocess_auto_label(input_file, output_file, tag='corrected_output')

    # 评估ChatGPT
    print('ChatGPT random Correction')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)

    # 转化ChatGPT原始标注
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_chatgpt_vote_major.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_correction_label_major.json'
    preprocess_auto_label(input_file, output_file, tag='corrected_output')

    # 评估ChatGPT
    print('ChatGPT majority vote Correction')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)


    # 转化GPT4原始标注
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_gpt4_vote_random.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_correction_label.json'
    preprocess_auto_label(input_file, output_file, tag='corrected_output')

    # 评估GPT4
    print('GPT4 random Correction')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)

    # 转化GPT4
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_gpt4_vote_major.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_correction_label_major.json'
    preprocess_auto_label(input_file, output_file, tag='corrected_output')

    # 评估GPT4
    print('GPT4 majority vote Correction')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)


    # 转化ChatGPT cycle
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_chatgpt_cycle_random.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_correction_label_cycle.json'
    preprocess_auto_label(input_file, output_file, tag='corrected_output')

    # 评估GPT4
    print('ChatGPT cycle Correction')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)

    # 转化GPT4 cycle
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_gpt4_cycle_random.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_correction_label_cycle.json'
    preprocess_auto_label(input_file, output_file, tag='corrected_output')

    # 评估GPT4
    print('GPT4 cycle Correction')
    results = evaluate_jsonl_files(output_file, label_file)
    print_evaluation_results(results)