# 对NLU的投票结果进行综合
import json
import random
import copy
import collections

ext_list = []

cls_names = [
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


cls_elements = ['事件']
ext_elements = [
    '时间', '出售方', '交易物', '出售价格', '收购方', '跌停股票',
    '加息幅度', '加息机构', '降价方', '降价物', '降价幅度',
    '降息幅度', '降息机构', '跟投方', '领投方', '融资轮次',
    '融资金额', '融资方', '地点', '上市企业', '涨价幅度',
    '涨价物', '涨价方', '涨停股票', '触发词'
]
def filter_vote(input_text, gpt_result):
    main_key = '事件'
    ret_list = []
    
    for r in gpt_result:
        add_dict = {}
        try:
            if type(r) == str:
                # 替换单引号
                r = r.replace("'", '"')
                r = json.loads(r)
        

            for key, value in r.items():
                if value == None:
                    continue

                if type(value) == list:
                    v_str = ''
                    for i, v in enumerate(value):
                        if i == 0:
                            v_str += str(v)
                        else:
                            v_str += ',' + str(v)
                    value = v_str

                # 过滤事件
                if  key not in cls_elements and key not in ext_elements:
                    continue
                if key in cls_elements and value not in cls_names:
                    continue
                if key in ext_elements and value not in input_text:
                    continue
                
                add_dict[key] = value

        except Exception as e:
            print("filter vote convert error...")
        
        if len(add_dict) != 0 and main_key in add_dict:
            ret_list.append(add_dict)
    
    return ret_list



def filter_vote_list(input_text, gpt_advises):
    return_list = []

    for ad in gpt_advises:
        try:
            op = ad['act'].lower()
            modified_label = ad['value']
            
            if op != 'pass':
                if type(modified_label) == str:
                    # 替换单引号为双引号
                    modified_label = modified_label.replace("'", '"')
                    modified_label = json.loads(modified_label)
                add_dict = filter_vote(input_text, modified_label)
                
                if len(add_dict) != 0:
                    return_list.append(add_dict)

        except Exception as e:
            print("operation convert error.")
            continue

    return return_list


def diff_of_lists(list1, list2):
    main_key = '事件'
    

    dict1 = {item[main_key]: item for item in list1 if main_key in item}
    dict2 = {item[main_key]: item for item in list2 if main_key in item}

    label2id = {}
    for index, label_item in enumerate(list1):
        if main_key in label_item:
            label2id[label_item[main_key]] = index

    # 计算事件级别的差异
    deleted_items = {k: v for k, v in dict1.items() if k not in dict2.keys()}
    added_items = {k: v for k, v in dict2.items() if k not in dict1.keys()}

    # 列表2和列表1中都有，但是内容不同的元素
    common_keys = set(dict1.keys()).intersection(dict2.keys())

    modified_items = {}
    for k in common_keys:
        item1, item2 = dict1[k], dict2[k]
        if item1 != item2:
            added_attrs = {attr: val for attr, val in item2.items() if attr not in item1.keys()}
            deleted_attrs = {attr: val for attr, val in item1.items() if attr not in item2.keys()}
            modified_attrs = {attr: {'原内容': item1[attr], '新内容': item2[attr]} for attr in set(item1.keys()).intersection(item2.keys()) if item1[attr] != item2[attr]}
            modified_items[k] = {'新增': added_attrs, '删除': deleted_attrs, '修改': modified_attrs}
    
    changes = {'新增事件': added_items, '删除事件': deleted_items, '修改事件': modified_items}
    # print(changes)

    # 拆分成细粒度的结果
    op_list = []

    # 新增操作
    for key, v_dict in changes['新增事件'].items():
        op_list.append({'op': 'add', 'id': 'add_list', 'key': main_key, 'value': key})

        for k, v  in v_dict.items():
            op_list.append({'op': 'add', 'id': 'add_list#' + key, 'key': k, 'value': v})

    # 删除操作
    for key, v_dict in changes['删除事件'].items():
        op_list.append({'op': 'delete', 'id':label2id[key], 'key': key, 'value': '#All'})

    # 修改操作
    for key, v_dict in changes['修改事件'].items():

        for add_k, add_v in v_dict['新增'].items():
            op_list.append({'op': 'add', 'id':label2id[key], 'key': add_k, 'value': add_v})

        for del_k, del_v in v_dict['删除'].items():
            op_list.append({'op': 'delete', 'id':label2id[key], 'key': del_k, 'value': del_v})

        for mod_k, mod_v in v_dict['修改'].items():
            op_list.append({'op': 'modify', 'id':label2id[key], 'key': mod_k, 'value': mod_v['新内容']})

    return op_list



def NLU_vote(advises, input_text, last_output, op_threshold):
    origin_output = filter_vote(input_text, last_output)
    last_output = copy.deepcopy(origin_output)
    filter_output_list = filter_vote_list(input_text, advises)

    op_dict = collections.defaultdict(int)

    for f_o in filter_output_list:
        op_list = diff_of_lists(last_output, f_o)

        for op in op_list:
            op_dict[json.dumps(op, ensure_ascii=False)] += 1

    # 最终需要被执行的operation
    exec_op = []

    for op, num in op_dict.items():
        if num >= int(len(filter_output_list) * op_threshold + 0.5):
            exec_op.append(json.loads(op))

    # 执行operation
    add_dict = {}
    remove_list = []
    
    for op in exec_op:
        op_name = op['op']
        id = op['id']
        key = op['key']
        value = op['value']
        
        if op_name == 'add' and type(id) == str and 'add_list' in id:
            if id == 'add_list':
                add_dict[value] = {}
            else:
                add_key = id.split('#')[1]
                add_dict[add_key][key] = value

        if op_name == 'delete':
            if value == '#All':
                remove_list.append(json.dumps(last_output[id], ensure_ascii=False))
            else:
                del last_output[id][key]

        if op_name == 'modify':
            last_output[id][key] = value

    final_list = []
    for l_o in last_output:
        l_o_str = json.dumps(l_o, ensure_ascii=False)
        if l_o_str not in remove_list:
            final_list.append(l_o)

    for key, add_item in add_dict.items():
        final_list.append(add_item)

    return final_list

       

def majority_vote(advises, last_output, input_text='', pass_threshold=0.5, op_threshold=0.5):
    pass_num = 0
    modify_values = []
    first_corrected_result = last_output
    effective_vote = 0      # 有效的建议数量

    for i, ad in enumerate(advises):
        try:
            act = ad['act'].lower()
            value = ad['value']
        except Exception as e:
            print('Parsing advise wrong: %s' % e)
            continue

        if act == 'pass':
            pass_num += 1
        elif act == 'modify':
            modify_values.append(value)
            if i == 0:
                first_corrected_result = value

        effective_vote += 1

    threshold = int(pass_threshold * effective_vote)

    if pass_num >= threshold or len(modify_values) == 0:
        return first_corrected_result, last_output
    else:
        return first_corrected_result, NLU_vote(advises, input_text, last_output, op_threshold)



def start_vote(input_file, output_file, pass_threshold, op_threshold):
    sava_data = []
    with open(input_file, 'r') as f:
        all_data = f.readlines()
        for line in all_data:
            json_data = json.loads(line)
            input_str = json_data['input']
            origin_output = json_data['origin_output']
            gpt_vote_list = json_data['gpt_advises']

            # vote_reslut = 
            _, corrected_reslut = majority_vote(gpt_vote_list, origin_output, input_str, pass_threshold, op_threshold)

            sava_data.append({'input': input_str, 'origin_output': origin_output, 'corrected_output': corrected_reslut})

    with open(output_file,'w') as f:
        for data in sava_data:
            json_str = json.dumps(data,ensure_ascii=False)
            f.write(json_str)
            f.write('\n')




if __name__ == '__main__':
    # pass_threshold = 0.5
    # op_threshold = 0.3
    
    # input_data = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_chatgpt_vote_random.json'
    # output_data = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_chatgpt_vote_major.json'

    # start_vote(input_data, output_data, pass_threshold, op_threshold)

    # GPT4的参数设计
    pass_threshold = 0.5
    op_threshold = 0.3

    input_data = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_gpt4_vote_random.json'
    output_data = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/correction/NLU_corrected_gpt4_vote_major.json'

    start_vote(input_data, output_data, pass_threshold, op_threshold)