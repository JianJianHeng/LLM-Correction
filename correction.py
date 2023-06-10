

import utils
import prompt

import copy
import time
import json
import random
from string import Template
from argparse import ArgumentParser


class Correction(object):
    def __init__(self, input_file, output_file, task_prompt, args):
        self.input_file = input_file
        self.output_file = output_file
        self.task_prompt = task_prompt
        self.args = args

        self.input_data = self.read_input_file()

    def read_input_file(self):
        ret_data = []
        with open(self.input_file, 'r') as f:
            all_data = f.readlines()
            for line in all_data:
                json_data = json.loads(line)
                ret_data.append(json_data)
        return ret_data

    def get_sentence_id(self, output_str):
        sentences = []
        current_sentence = ""

        if self.args.lang == "chinese":
            split_punc = "。"
        else:
            split_punc = "."

        for char in output_str:
            if char == '\n' and len(sentences) != 0:
                sentences[-1] += char
            else:
                current_sentence += char
                if char == split_punc:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""

        # 添加最后一个句子（如果存在）
        if current_sentence:
            sentences.append(current_sentence.strip())

        sen_id = 1
        add_id_sentences = ""
        for s in sentences:
            id_text = "(" + "%d" % sen_id + "): "
            add_id_sentences += id_text + s
            sen_id += 1

        return add_id_sentences, sentences

    def majority_vote(self, output_str, sen_list, advises):
        operation_list = []
        sen_modified_dict = {}

        threshlod = int(len(advises) / 2)
        
        for ad in advises:
            for op in ad:
                operation = op['Operation']
                try:
                    sen_id = int(op['Sentence id'])
                except Exception as e:
                    continue
                content = op['Content']

                # avoid repeat
                if operation in ['Add', 'Modify'] and (content in output_str or content in sen_list):
                    continue
                
                if sen_id not in sen_modified_dict:
                    sen_modified_dict[sen_id] = {operation: {'num': 1, 'Content': [content]}}
                else:
                    if operation not in sen_modified_dict[sen_id]:
                        sen_modified_dict[sen_id][operation] = {'num': 1, 'Content': [content]}
                    else:
                        sen_modified_dict[sen_id][operation]['num'] += 1
                        if content not in sen_modified_dict[sen_id][operation]['Content']:
                            sen_modified_dict[sen_id][operation]['Content'].append(content)
                # operation_list.append({'Operation': op['Operation'], 'Sentence id': op['Sentence id'], 'Content': [op['Content']]})

        # if Pass reach threshold
        if -1 in sen_modified_dict and 'Pass' in sen_modified_dict[-1] and  sen_modified_dict[-1]['Pass']['num'] >= threshlod:
            operation_list.append({'Operation': 'Pass', 'Sentence id': -1, 'Content': ['None']})
            return operation_list
        

        for sen_id, op_dict in sen_modified_dict.items():
            # only allow one operation in one sentence id
            max_num = 0
            max_op = ''
            contents = ''
                
            for op, op_content in op_dict.items():
                if op_content['num'] > max_num:
                    max_num = op_content['num']
                    max_op = op
                    contents = op_content['Content']
            
            if max_num >= threshlod:
                operation_list.append({'Operation': max_op, 'Sentence id': sen_id, 'Content': contents})
        return operation_list
    
    def complete_operation(self, input_str, output_str, operation_list):
        # delete pass operation in multi
        exec_list = []
        for op in operation_list:
            if op['Operation'] != 'Pass':
                exec_list.append(op) 

        operation_str = json.dumps(exec_list, ensure_ascii=False)

        complete_prompt = prompt.NLG_modified_prompt.substitute(
            task = self.task_prompt,
            input = input_str,
            output = output_str,
            operations = operation_str)
        
        complete_messages =[
                    {"role": "user", "content": complete_prompt}
                ]

        llm_results = utils.ask_gpt(messages = complete_messages, model = args.model_name, n = 1)
        modification_list = json.loads(llm_results['choices'][0]['message']['content'])

        return modification_list


    def random_choice(self, operation_list):
        """
        random chosse one Content
        """
        modification_list = []
        for op in operation_list:
            op["Content"] = random.choice(op["Content"])
            modification_list.append(op)

        return  modification_list

    
    def modify(self, input_str, output_str, sen_list, operation_list):
        if self.args.mode == 'NLG':
            if len(operation_list) == 1 and operation_list[0]['Operation'].lower() == 'pass':
                return ''.join(sen_list)
            
            if args.use_api_ensemble:
                operation_list = self.complete_operation(input_str, output_str, operation_list)
            else:
                operation_list = self.random_choice(operation_list)
            sen_list_copy = copy.deepcopy(sen_list)   
            
            modify_list = []
            del_list = []
            add_list = []

            for op in operation_list:
                operation = op['Operation']
                if operation.lower() == 'add':
                    add_list.append(op)
                elif operation.lower() == 'delete':
                    del_list.append(op)
                elif operation.lower() == 'modify':
                    modify_list.append(op)

            for m_op in modify_list:
                sen_id = int(m_op['Sentence id']) - 1
                content = m_op['Content']
                try:
                    sen_list_copy[sen_id] = content  # 修改特定索引处的元素
                except IndexError:
                    sen_list_copy.append(content)  # 如果索引超出范围，添加到最后

            for d_op in del_list:
                sen_id = int(d_op['Sentence id']) - 1
                content = d_op['Content']
                try:
                    del sen_list_copy[sen_id]  # 删除特定索引处的元素
                except IndexError:
                    del sen_list_copy[-1]  # 如果索引超出范围，则删除最后一个元素

            for a_op in add_list:
                sen_id = int(a_op['Sentence id']) - 1
                content = a_op['Content']
                try:
                    sen_list_copy.insert(sen_id + 1, content)  # 在索引后插入元素
                except IndexError:
                    sen_list_copy.append(content)  # 如果索引超出范围，则添加到列表末尾

            return ''.join(sen_list_copy)
            
    
    def correct(self, sentence):
        input_str = sentence['input']
        output_str, sen_list = self.get_sentence_id(sentence['output'])

        print('Instruction: %s' % input_str)
        print('Output: %s' % output_str)
        print()

        input_prompt = prompt.correct_system_prompt.substitute(
            task=self.task_prompt,
            input=input_str,
            output=output_str)
        input_messages =[
                    {"role": "user", "content": input_prompt},
                ]
        
        llm_results = utils.ask_gpt(messages = input_messages, model = args.model_name, n = self.args.vote_num)
 
        advises = [] 
        for response in llm_results['choices']:
            result = response['message']['content']
            try:
                ad = json.loads(result)
                advises.append(ad)
            except Exception as e:
                print("Convert Error")
        
        first_corrected_text = ''
        if len(advises) != 0:
            if args.save_first:
                first_operation_list = self.majority_vote(output_str, sen_list, [advises[0]])
                first_corrected_text = self.modify(input_str, output_str, sen_list, first_operation_list)

            operation_list = self.majority_vote(output_str, sen_list, advises)
            corrected_text = self.modify(input_str, output_str, sen_list, operation_list)
        else:
            corrected_text = ''.join(sen_list)

        print('Corrected: %s' % corrected_text)
        
        if args.save_first and first_corrected_text == '':
            first_corrected_text = corrected_text
        return corrected_text, first_corrected_text, advises

    def run(self):
        start_id = self.args.start_id
            
        for index, data in enumerate(self.input_data):
            if index < start_id:
                continue

            print('-' * 20)
            print(index)
            print()

            corrected_text, first_corrected_text, advises  = self.correct(data)
            save_dict = {'id': index, 'input': data['input'], 'origin_output': data['output'], 'corrected_output': corrected_text, 'gpt_advises': advises}

            if args.save_first:
                save_dict['first_corrected_output'] = first_corrected_text
            
            # save data
            with open(self.output_file,'a+') as f:
                json_str = json.dumps(save_dict,ensure_ascii=False)
                f.write(json_str)
                f.write('\n')




if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("--load_model", default="", type=str)  # full path, with .pth
    parser.add_argument("--start_id", default=102, type=int)  # wandb project name. if "" then don't use wandb
    parser.add_argument("--vote_num", default=6, type=int)
    parser.add_argument("--mode", default="NLG", type=str)
    parser.add_argument("--lang", default="chinese", type=str)
    parser.add_argument("--save_first", default=True, type=bool)
    parser.add_argument("--model_name", default='gpt-4', type=str)
    parser.add_argument("--use_api_ensemble", default=False, type=bool)
    args = parser.parse_args()

    print(args)

    instruction_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_labeled_data.json"
    save_file = "/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_gpt4.json"

    correction = Correction(instruction_file, save_file, prompt.instruct_task_prompt, args)

    correction.run()
