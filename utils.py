import json
import openai
import time

def remove_quotes(text):
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    elif text.startswith("'") and text.endswith("'"):
        return text[1:-1]
    else:
        return text



def convert_instruction_data(data_file, save_file):
    save_data = []
    with open(data_file, 'r') as f:
        all_data = json.load(f)
        for d in all_data:
            json_data = d
            instruction = remove_quotes(json_data['instruction'])
            input = remove_quotes(json_data['input'])
            output = remove_quotes(json_data['output'])

            input_str = instruction
            if len(input) != 0:
                input_str += '\n' + input

            if len(input_str) > 250:
                continue

            save_data.append({
                'input': input_str,
                'output': output
                })

    with open(save_file,'w') as f:
        for data in save_data:
            json_str = json.dumps(data,ensure_ascii=False)
            f.write(json_str)
            f.write('\n')


def read_api(filename):
    with open(filename, 'r') as file:
        first_line = file.readline().strip()
    return first_line

openai.api_base = "https://api.chatanywhere.com.cn/v1"
openai.api_key = read_api('gpt_tokens.txt')

def ask_gpt(messages, model='gpt-4', n=1, temperature=1, max_retry=10):
    # Note: you need to be using OpenAI Python v0.27.0 for the code below to work
    success = False
    retry = 1
    while success == False and retry < max_retry:
        try:
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                n=n,
                temperature=temperature)
            success = True
        except Exception as e:
            print('API Error:', str(e))
            retry += 1
            time.sleep(10)
    if success == False:
        raise("API Error can't fix.")
    if response == None:
        raise Exception("ChatGPT API Error")
    
    return response


def split_sentences(text):
    sentences = []
    current_sentence = ""
    
    for char in text:
        if char == '\n' and len(sentences) != 0:
            sentences[-1] += char
        else:
            current_sentence += char
            if char == "." or char == "。":
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



if __name__ == '__main__':
    instruct_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/trans_chinese_alpaca_data.json'
    save_file = '/Users/jjh/Desktop/git_projects/GPT-Correction/data/luotuo_labeled_data_gpt4.json'
    convert_instruction_data(instruct_file, save_file)

    text = "An atom is the basic building block of all matter and is made up of three types of particles: protons, neutrons, and electrons. The structure of an atom can be described as a nucleus at the center surrounded by a cloud of electrons.\n\nThe nucleus of an atom is made up of protons and neutrons.\n Protons are positively charged particles and neutrons are neutral particles with no charge.\n Both of these particles are located in the nucleus of the atom, which is at the center of the atom and contains most of the atom's mass.\n\nSurrounding the nucleus of the atom is a cloud of electrons. Electrons are negatively charged particles that are in constant motion around the nucleus. The electron cloud is divided into shells or orbitals, and each shell can hold a certain number of electrons. The number of electrons in the outermost shell, called the valence shell, determines the chemical properties of the atom. \n\nIn a neutral atom, the number of protons in the nucleus is equal to the number of electrons in the electron cloud, so the positive and negative charges balance out and the atom has no overall charge. The number of protons, also called the atomic number, determines what element the atom is."

    add_id_sentences, sentences = split_sentences(text)
    print(sentences)
    print(add_id_sentences)
