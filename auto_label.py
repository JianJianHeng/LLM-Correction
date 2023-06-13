"""
自动标注
"""
import json
from argparse import ArgumentParser

import prompt
import utils


class Auto_Label(object):
    def __init__(self, args):
        self.input_file = args.input_file
        self.output_file = args.output_file
        if args.mode == 'NLG':
            self.task_prompt = prompt.instruct_task_prompt_chinese
        elif args.mode == 'NLU':
            self.task_prompt = prompt.event_label_task
        self.args = args
        

    def label(self):
        start_id = self.args.start_id
        with open(self.input_file, 'r') as file:
            for index, line in enumerate(file):
                if index < start_id:
                    continue

                print('-' * 20)
                print(index)
                print()
                
                data = json.loads(line)
                input_text = data['text']

                print('Input: %s' % input_text)
                print()

                input_prompt = prompt.NLU_label_prompt_Chinese.substitute(task = self.task_prompt, input = input_text)
                input_messages =[
                    {"role": "user", "content": input_prompt},
                ]

                success = False
                retry_num = 0

                while success == False and retry_num < 10:
                    llm_results = utils.ask_gpt(messages = input_messages, model = self.args.model_name, temperature = self.args.temperature)
                    
                    for response in llm_results['choices']:
                        result = response['message']['content']
                        try:
                            label = json.loads(result)
                            success = True
                        except Exception as e:
                            print("Convert Error")
                            print(result)
                        
                        retry_num += 1
                
                if retry_num >= 10:
                    raise("Reach Max API Retry...")
                
                print('Label: %s' % label)

                # save data
                with open(self.output_file,'a+') as f:
                    save_dict = {'text': input_text, 'label': label}
                    json_str = json.dumps(save_dict,ensure_ascii=False)
                    f.write(json_str)
                    f.write('\n')
                



if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument("--input_file", default="/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/finacial_events_label_converted.json", type=str)
    parser.add_argument("--output_file", default="/Users/jjh/Desktop/git_projects/GPT-Correction/data/NLU/chatgpt_label.json", type=str) 
    parser.add_argument("--start_id", default=0, type=int)                # skip instances
    parser.add_argument("--mode", default="NLU", type=str)                  # can choose NLG or NLU
    parser.add_argument("--lang", default="chinese", type=str)              # can choose chinese or english
         
    parser.add_argument("--strategy", default='ReAct', type=str)           # circle, vote

    parser.add_argument("--model_name", default='gpt-3.5-turbo', type=str)     
    parser.add_argument("--temperature", default=1, type=float) 
    parser.add_argument("--api_key", default='sk-O925mee9VN8z6HsUcQ3E8hQc31pqRnCfV49UEzR1s7yO1oP1', type=str)
    args = parser.parse_args()

    print(args)

    if len(args.api_key) != 0:
        utils.set_api_key(args.api_key)


    auto_labeler = Auto_Label(args)

    auto_labeler.label()