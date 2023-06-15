"""预处理NLU任务的数据"""
import jsonlines
import random
import json


def filter_jsonl_file(input_file, output_file):
    id = 1
    with jsonlines.open(input_file) as reader, jsonlines.open(output_file, mode='w') as writer:
        for obj in reader:
            event_list = obj['event_list']
            filtered_events = [event for event in event_list if event['class'] == '财经/交易']
            
            if len(filtered_events) != 0:
                obj['event_list'] = filtered_events
                obj['id'] = id
                writer.write(obj)
                id += 1


def extract_text(jsonl_file, output_file, label_file):
    label_data = []
    with open(jsonl_file, 'r') as file:
        
            for line in file:
                data = json.loads(line)
                text = data.get('text', '')
                label_data.append((text, data))

    random.shuffle(label_data)

    with open(output_file, 'w') as output:
        for d in label_data:
            output.write(d[0] + '\n')

    with open(label_file, 'w') as output:
        for d in label_data:
            json_str = json.dumps(d[1], ensure_ascii=False)
            output.write(json_str + '\n')



def convert_jsonl_to_label_studio(jsonl_file, label_studio_file, tag, is_first=False):
    save_data = []   
    total_num = 0 
    with open(jsonl_file, 'r') as f_in, open(label_studio_file, 'w') as f_out:
        for line in f_in:
            total_num += 1
            data = json.loads(line)
            instruction = data['input']
            output_1 = data['origin_output']
            if is_first:
                output_2 = data['first_corrected_output']
            else:
                output_2 = data['corrected_output']

            if output_1 == output_2:
                continue

            rand_num = random.choice([1, 0])
            if rand_num == 1:
                output_1 = data['corrected_output']
                output_2 = data['origin_output']
                tag_dict = {'1': tag, '2': 'origin'}
            else:
                tag_dict = {'1': 'origin', '2': tag}
            
            label_studio_data = { 
                "data": {
                    "sen_id": data['id'],
                    "tag": tag_dict,
                    "instruction": instruction,
                    "output_1": output_1, 
                    "output_2": output_2
                }
            }
            save_data.append(label_studio_data)


        # print(len(save_data))
        modify_num = len(save_data)

        if len(save_data) < 500:
            sample_num = len(save_data)
        else:
            sample_num = 500
        save_data = random.sample(save_data, sample_num)
        print(tag)
        print('Data Num:', modify_num)
        print('Total Data: ', total_num)
        print('Modify_rate: ', modify_num / total_num)    
        print()
        json.dump(save_data, f_out, ensure_ascii=False)
        # f_out.write('\n')


# 转换金融数据集
def transform_dicts(old_dict):
    new_dict = old_dict.copy()  # create a copy of the original dictionary
    new_dict["event_list"] = []  # initialize a new event_list

    for event in old_dict["event_list"]:
        transformed_event = {}
        transformed_event["事件"] = event["event_type"].split("-")[1]
        transformed_event["触发词"] = event["trigger"]

        for argument in event["arguments"]:
            transformed_event[argument["role"]] = argument["argument"]

        new_dict["event_list"].append(transformed_event)  # append the transformed event to the new event_list

    return new_dict

def transform_file(input_filepath, output_filepath):
    with open(input_filepath, 'r', encoding='utf-8') as f_in, \
         open(output_filepath, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            old_dict = json.loads(line)
            new_dict = transform_dicts(old_dict)  # transform the dictionary
            json.dump(new_dict, f_out, ensure_ascii=False)  # write the transformed dictionary to the output file
            f_out.write('\n')  # add a newline character after each dictionary



# 转换GPT标注NLU任务的结果
def process_jsonl(input_file, output_file):
    output_data = []

    with open(input_file, "r") as file:
        for line in file:
            data = json.loads(line)
            data["input"] = data.pop("text")
            data["output"] = data.pop("label")
            output_data.append(data)

    with open(output_file, "w") as file:
        for data in output_data:
            file.write(json.dumps(data, ensure_ascii=False) + "\n")


def filter_repeat(input_file, label_file, output_file):
    map_dict = {}

    with open(input_file, "r") as file:
        for line in file:
            data = json.loads(line)
            # data["input"] = data.pop("text")
            # data["output"] = data.pop("label")
            # output_data.append(data)
            text = data['input']
            label = data['output']

            if text not in map_dict:
                map_dict[text] = [label]
            else:
                map_dict[text].append(label)

    save_data = []
    with open(label_file, "r") as file:
        for line in file:
            data = json.loads(line)

            text = data['text']
            
            if text in map_dict:
                save_data.append({'input': text, 'output': random.choice(map_dict[text])})
            else:
                raise("No found label...")
            
    with open(output_file, "w") as file:
        for data in save_data:
            file.write(json.dumps(data, ensure_ascii=False) + "\n")






if __name__ == '__main__':
    # # 转换金融事件抽取的数据集
    # input_filepath = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label.json'  # replace with your input file path
    # output_filepath = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label_converted.json'  # replace with your output file path
    # transform_file(input_filepath, output_filepath)

    # # 转换标注结果
    # input_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_label.json"
    # output_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_label_2.json"
    # process_jsonl(input_file, output_file)

    # input_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_label.json"
    # output_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_label_2.json"
    # process_jsonl(input_file, output_file)

    # input_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_label_2.json"
    # label_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label_converted.json"
    # output_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/gpt4_label_3.json"
    # filter_repeat(input_file, label_file, output_file)

    # # 转化事件抽取数据集
    # input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/duee_train.json'
    # output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events.json'
    # filter_jsonl_file(input_file, output_file)

    # # 转化标注文档
    # jsonl_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events.json'
    # output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/inputtexture.txt'
    # label_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label.json'
    # extract_text(jsonl_file, output_file, label_file)


    # # 导出进行标注
    # first_gpt4
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_gpt4_ReAct.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_first_gpt4_label.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'new_first_gpt4', is_first=True)

    #first_chatgpt
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_chatgpt_ReAct.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_first_chatgpt_label.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'new_first_chatgpt', is_first=True)

    # vote_gpt4
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_gpt4_ReAct.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_vote_gpt4_label.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'new_vote_gpt4')

    # vote_chatgpt
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_chatgpt_ReAct.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_vote_chatgpt_label.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'new_vote_chatgpt')

    # cycle_chatgpt
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_chatgpt_ReAct_simple_circle.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/simple_circle_chatgpt_label_2.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'simple_circle_chatgpt')

    # cycle_gpt4
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_gpt4_ReAct_simple_circle.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/simple_circle_gpt4_label_2.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'simple_circle_gpt4')


    # single_chatgpt
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/chatgpt_simple_circle_single.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/single_circle_chatgpt_label.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'single_circle_chatgpt')

    # cycle_gpt4
    input_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/gpt4_simple_circle_single.json'
    output_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/single_circle_gpt4_label.json'
    convert_jsonl_to_label_studio(input_file, output_file, 'single_circle_gpt4')

    

    # 集合数据列表
    # 列出所有的json文件名
    files = [
        # '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_first_gpt4_label.json',
        # '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_first_chatgpt_label.json',
        # '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_vote_gpt4_label.json',
        # '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/new_vote_chatgpt_label.json',
        '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/simple_circle_chatgpt_label_2.json',
        '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/simple_circle_gpt4_label_2.json',
        '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/single_circle_chatgpt_label.json',
        '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/single_circle_gpt4_label.json'
    ]

    # 创建一个空列表来储存所有的字典
    all_dicts = []

    # 按顺序打开并读取每个文件的内容
    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            all_dicts.extend(data)

    # 打乱列表
    random.shuffle(all_dicts)

    # 将打乱后的列表输出到一个新的json文件
    # with open('/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLG/merged/cycle_merged_data.json', 'w') as f:
    #     json.dump(all_dicts, f, ensure_ascii=False)
