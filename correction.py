

import utils
import prompt

import copy
import time
import json
import random
from string import Template
from argparse import ArgumentParser


class Correction(object):
    def __init__(self, args):
        self.input_file = args.input_file
        self.output_file = args.output_file
        if args.mode == 'NLG':
            self.task_prompt = prompt.instruct_task_prompt_chinese
            self.main_prompt = prompt.Rethinking_prompt
        elif args.mode == 'NLU':
            self.task_prompt = prompt.event_label_task
            self.main_prompt = prompt.Rethinking_prompt_chinese
        else:
            raise("Unknown mode %s." % args.mode)
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

        pass_threshold = int(len(advises) * self.args.pass_threshold)
        op_threshold = int(len(advises) * self.args.op_threshold)
        
        for ad in advises:
            for op in ad:
                try:
                    operation = op['Operation']
                    sen_id = int(op['Sentence id'])
                    content = op['Content']
                except Exception as e:
                    print('Warn: not found key.\n %s' % e)
                    continue

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
        if -1 in sen_modified_dict and 'Pass' in sen_modified_dict[-1] and  sen_modified_dict[-1]['Pass']['num'] >= pass_threshold:
            operation_list.append({'Operation': 'Pass', 'Sentence id': -1, 'Content': ['None']})
            return operation_list
        

        for sen_id, op_dict in sen_modified_dict.items():
            # only allow one operation in one sentence id
            if sen_id == -1:
                continue
            
            max_num = 0
            max_op = ''
            contents = ''
                
            for op, op_content in op_dict.items():
                if op_content['num'] > max_num:
                    max_num = op_content['num']
                    max_op = op
                    contents = op_content['Content']
            
            if max_num >= op_threshold:
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

        llm_results = utils.ask_gpt(messages = complete_messages, model = args.model_name, n = 1, temperature = self.args.temperature)
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
            
            if self.args.use_api_ensemble:
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
                    if len(sen_list_copy) > 0:
                        del sen_list_copy[-1]  # 如果索引超出范围，则删除最后一个元素

            for a_op in add_list:
                sen_id = int(a_op['Sentence id']) - 1
                content = a_op['Content']
                try:
                    sen_list_copy.insert(sen_id + 1, content)  # 在索引后插入元素
                except IndexError:
                    sen_list_copy.append(content)  # 如果索引超出范围，则添加到列表末尾

            return_str = ''.join(sen_list_copy)
            if len(return_str) == 0:
                return_str = ''.join(sen_list)

            return return_str
        

    def ask_advises(self, input_str, output_str):
        """
        ask GPT for advises
        """
        if type(output_str) == list:            # for NLU format
            output_str = json.dumps(output_str, ensure_ascii=False)

        input_prompt = self.main_prompt.substitute(
            task=self.task_prompt,
            input=input_str,
            output=output_str)
        input_messages =[
                    {"role": "user", "content": input_prompt},
                ]
        
        llm_results = utils.ask_gpt(messages = input_messages, model = self.args.model_name, n = self.args.vote_num, temperature = self.args.temperature)
 
        advises = [] 
        for response in llm_results['choices']:
            result = response['message']['content']
            try:
                ad = json.loads(result)
                advises.append(ad)
            except Exception as e:
                print("Convert Error")
                print(result)
        
        return advises


    def vote_correct(self, sentence):
        """
        Correction with majority vote
        """
        input_str = sentence['input']
        output_str, sen_list = self.get_sentence_id(sentence['output'])

        print('Instruction: %s' % input_str)
        print('Output: %s' % output_str)
        print()

        advises = self.ask_advises(input_str, output_str)
        
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
    

    def get_sim_better(self, vote_list, rand_num):
        """
        get similarity and better result by vote
        """
        sim_score = 0
        score = 0
        same_score = 0
        better_score = 0
        gpt_vote_result = []

        for v in vote_list:
            try:
                sim = v['Whether highly similar'].lower()
                a = v['Which better'].lower()
                # print(v)
            except Exception as e:
                print('Warn: Error format.')
                continue

            if rand_num == 0:
                e_result = 'last'
                a_reslut = 'new'
            else:
                e_result = 'new'
                a_reslut = 'last'

            vote = {}

            if sim == 'yes':
                sim_score += 1
                vote['sim'] = 'yes'
            elif sim == 'no':
                sim_score -= 1
                vote['sim'] = 'no'
            
            if a == 'enthusiasm':
                score += 1
                vote['better'] = e_result
            elif a == 'ambition':
                score -= 1
                vote['better'] = a_reslut
            else:
                vote['better'] = 'same'
                same_score += 1
            
            gpt_vote_result.append(vote)

        if same_score >= int(len(vote_list) * 0.66):
            better_score = 0
        else:
            if score > 0:
                better_score = 1
            elif score < 0:
                better_score = -1
            else:
                better_score = 0
        
        return sim_score, better_score, gpt_vote_result


    def modify_pass_vote(self, last_output, advises):
        pass_threshold = self.args.pass_threshold
        threshold = int(pass_threshold * len(advises) + 0.5)
        pass_num = 0
        modify_values = []
        first_corrected_result = last_output

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

        if pass_num >= threshold or len(modify_values) == 0:
            return first_corrected_result, last_output
        else:
            return first_corrected_result, random.choice(modify_values)
                


    def ReAct_correct(self, sentence):
        input_str = sentence['input']
        output_data = sentence['output']

        first_corrected_result = output_data

        print('Instruction: %s' % input_str)
        print('Output: %s' % output_data)
        print()

        advises = self.ask_advises(input_str, output_data)

        if len(advises) != 0:
            first_corrected_result, corrected_result = self.modify_pass_vote(output_data, advises)
        else:
            corrected_result = output_data
        
        print('Correct: %s' % corrected_result)
        
        return corrected_result, first_corrected_result, advises



    def ReAct_cycle_correct(self, sentence, max_try = 5, same_cut = 3):
        """
        Correction using a loop frame by ReAct
        """
        input_str = sentence['input']
        output_result = sentence['output']
        last_output = output_result
        gpt_vote_history = []
        correction_history = [last_output]

        better_answer = last_output
        first_corrected_result = last_output

        print('Instruction: %s' % input_str)
        print('Origin Output: %s' % last_output)
        print()

        # cycle
        try_num = 1
        same_time = 0
        while try_num < max_try:
            # get correted output
            advises = self.ask_advises(input_str, last_output)

            if len(advises) != 0:
                _, new_output = self.modify_pass_vote(last_output, advises)
                if try_num == 1:
                    first_corrected_result = new_output
            else:
                new_output = last_output

            print('New Output: %s' % new_output)
            print()

            if new_output == last_output:       # cycle terminal
                print('Pass the output')
                break
            
            better_answer = new_output
            correction_history.append(better_answer)

            print('Cycle %d' % try_num)
            print()
            
            last_output = better_answer
            try_num += 1

        if try_num >= max_try:
            correction_history.append("Reach Max Retry...")
            print("Reach Max Retry...")

        return better_answer, first_corrected_result, correction_history, gpt_vote_history



    def run(self):
        start_id = self.args.start_id
            
        for index, data in enumerate(self.input_data):
            if index < start_id:
                continue

            print('-' * 20)
            print(index)
            print()

            if self.args.strategy == 'vote':
                corrected_text, first_corrected_text, advises  = self.vote_correct(data)
                save_dict = {'id': index, 'input': data['input'], 'origin_output': data['output'], 'corrected_output': corrected_text, 'gpt_advises': advises}
            elif self.args.strategy == 'ReAct':
                corrected_text, first_corrected_text, advises  = self.ReAct_correct(data)
                save_dict = {'id': index, 'input': data['input'], 'origin_output': data['output'], 'corrected_output': corrected_text, 'gpt_advises': advises}
            elif self.args.strategy == 'ReAct_circle':
                corrected_text, first_corrected_text, compare_history, gpt_vote_history = self.ReAct_cycle_correct(data)
                save_dict = {'id': index, 'input': data['input'], 'origin_output': data['output'], 'corrected_output': corrected_text, 'compare_history': compare_history, 'gpt_vote_history': gpt_vote_history}
            else:
                raise("Unknown strategy %s" % self.args.strategy)

            if args.save_first:
                save_dict['first_corrected_output'] = first_corrected_text
            
            # save data
            with open(self.output_file,'a+') as f:
                json_str = json.dumps(save_dict,ensure_ascii=False)
                f.write(json_str)
                f.write('\n')



if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("--input_file", default="/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_labeled_data.json", type=str)
    parser.add_argument("--output_file", default="/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_corrected_chatgpt_ReAct.json", type=str) 
    parser.add_argument("--start_id", default=0, type=int)                # skip instances
    parser.add_argument("--vote_num", default=10, type=int)                  # how many GPT votes
    parser.add_argument("--mode", default="NLG", type=str)                  # can choose NLG or NLU
    parser.add_argument("--lang", default="chinese", type=str)              # can choose chinese or english
    parser.add_argument("--save_first", default=True, action='store_true')            # save first GPT correction result
         
    parser.add_argument("--use_api_ensemble", default=False, action='store_true')     # use GPT api to ensemble vote result
    parser.add_argument("--strategy", default='ReAct', type=str)           # circle, vote
    parser.add_argument("--pass_threshold", default=0.8, type=float)
    parser.add_argument("--op_threshold", default=0.2, type=float)

    parser.add_argument("--model_name", default='gpt-3.5-turbo', type=str)     
    parser.add_argument("--temperature", default=1, type=float) 
    parser.add_argument("--api_key", default='sk-O925mee9VN8z6HsUcQ3E8hQc31pqRnCfV49UEzR1s7yO1oP1', type=str)
    args = parser.parse_args()

    print(args)

    if len(args.api_key) != 0:
        utils.set_api_key(args.api_key)


    correction = Correction(args)
    correction.run()
