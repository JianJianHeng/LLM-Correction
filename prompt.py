from string import Template


correct_system_prompt = Template("""
You are a very professional NLP annotation quality inspector, and your task is to evaluate and modify the annotations made by NLP annotators.

Quality Inspection Task
Please evaluate whether the above annotation result meets the requirements of the annotation task. As a quality inspector, you can perform the following operations to correct the annotation results:
1) Pass: You believe that the annotated answer meets the requirements of the annotation task and there are no errors, so you pass this annotation result.
2) Add: You think that the annotated answer has omissions, and you decide to add content to its answer. Please specify where you want to add after which sentence number, and provide the content to be added.
3) Delete: You believe that the annotated answer contains redundant content, and you think this content should be deleted. Please specify the number of the sentence you want to delete.
4) Modify: You believe that the annotated answer has errors, or you think this answer can be further modified. Please specify the number of the sentence you want to modify, and provide the modified sentence content.

Please provide your revision suggestions according to the following json format. Note that you can give 1-5 modification operations at a time, and please provide the reason for the modification:
'''
[
    {
        "Reason": "<provide reason>",                   # Provide the reason for this operation
        "Operation": "<provide operation>",             # Provide this operation, which must be one of Pass, Add, Delete, Modify
        "Sentence id": "<indicate sentence number>",    # Provide the sentence number of this operation, please give -1 when you pass
        "Content": "<modified content>"                 # If it is an Add, Modify operation, please provide the added or modified text content. If it is a Pass, Delete operation, please provide "none".
    },
    {
        "Reason": "<provide reason>",           
        "Operation": "<provide operation>",           
        "Sentence id": "<indicate sentence number>",      
        "Content": "<modified content>"
    },
    ....
]
'''
Please note that sentence numbers are identified at the beginning of the sentence in the format "(%d): ".
Please note that if you think the annotation answer has passed, the JSON format list you return can only contain one Pass operation. 
Next, please review the following annotation results in conjunction with the specific annotation task:

Annotation Task:
$task

Input:
$input

Output:
$output

Please provide the review results in JSON format:
""")



NLG_modified_prompt = Template("""
You are a highly professional NLP annotation editor. Your task is to modify the annotation results based on input, annotation results, and a series of annotation editing operations.

Quality Inspection Task
Please evaluate whether the above annotation result meets the requirements of the annotation task. You can perform the following operations to correct the annotation results:
1) Add: You think that the annotated answer has omissions, and you decide to add content to its answer. Please specify where you want to add after which sentence number, and provide the content to be added.
2) Delete: You believe that the annotated answer contains redundant content, and you think this content should be deleted. Please specify the number of the sentence you want to delete.
3) Modify: You believe that the annotated answer has errors, or you think this answer can be further modified. Please specify the number of the sentence you want to modify, and provide the modified sentence content.

Please provide your revision suggestions according to the following json format:
'''
[
    {
        "Operation": "<provide operation>",             # Provide this operation, which must be one of Pass, Add, Delete, Modify
        "Sentence id": "<indicate sentence number>",    # Provide the sentence number of this operation, please give -1 when you pass
        "Content": "<modified content>"                 # If it is an Add, Modify operation, please provide the added or modified text content. If it is a Pass, Delete operation, please provide "none".
    },
    {
        "Operation": "<provide operation>",           
        "Sentence id": "<indicate sentence number>",     
        "Content": "<modified content>"
    },
    ....
]
'''
Please note that sentence numbers are identified at the beginning of the sentence in the format "(%d): ".
Translation:

Next, we will provide you with a detailed description of the annotation task, the input for the annotation task, the output of the annotation task, and a series of modification operations. 
Note that the "Content" in the operation sequence we provide is a list. You can select one from the list or combine all the answers to provide the one you consider most ideal. The "Content" in your returned result must be a string.
Please complete the modification operations in the order specified and according to the mentioned output format.

Please provide your modify result based on the following results:


Annotation Task:
$task

Input:
$input

Output:
$output

Operations:
$operations

Please provide the review results in JSON format:
""")


# Compare Prompt
compare_prompt = Template("""You are a professional NLP annotation reviewer, and your task is to compare the similarity between two annotation results of the same annotated content based on the requirements of the annotation task. You are required to select the better and more suitable result for the annotation task from the two annotations.

Audit Task
1) Similarity Audit: You need to assess whether two annotation results are highly similar. If the content of the two answers is very similar, with almost identical word order and the same semantics, it is considered highly similar. Please note that semantics is the most crucial factor for this criterion. Even if the syntax of an answer is identical, if the meaning conveyed is completely opposite or different, it should be considered dissimilar for this task.
2) Annotation Result Selection: You need to choose the better one among the two annotation results. Your selection should strictly meet the requirements of the annotation task.Please note that we use the words "Enthusiasm" and "Ambition" as labels for two different annotation results. When choosing the preferred annotation result, please use these two words as markers for the return response.

Please provide your revision suggestions according to the following json format:
{
    "Reason": "<provide reason>",                   # Provide the reason for this audit
    "Whether highly similar": "<yes/no>",           # Please evaluate whether the two annotated results are highly similar in terms of form, structure, grammar, and semantics. Please select "no" if there is semantic opposition or difference. Your answer should be limited to "yes" or "no."
    "Which better": "<Enthusiasm/Ambition/Same>"    # Please select the result that you believe is better and more suitable for the annotation task. Your choice must be one of the following: Enthusiasm, Ambition, or Same. Please note that "Same" indicates that you consider the two results to be equally good.
}

Annotation Task:
$task

Input:
$input

Enthusiasm:
$output_1

Ambition:
$output_2

Please provide the audit results in JSON format:
""")



# NLG task
instruct_task_prompt = """According to the requirements of the input instruction, respond with content that satisfies reliability, consistency, and common sense, and try to meet the requirements given by the instruction.
After ensuring that there are no obvious errors or omissions and that the instructions' requirements are not being deviated from, if you feel that the answer can be improved, you can use the Modify operation to make modifications to the sentence you wish to modify.
Please be more daring in improving outputs to make them even better."""

instruct_task_prompt_chinese = """根据输入Input中指令的要求，回应满足可靠性、一致性和常识性的内容，并尽力满足指令给出的要求。
在确保没有明显的错误或遗漏，并且没有偏离指令的要求后，如果你觉得答案可以改进，你可以使用Modify操作对你想修改的句子进行修改。
如果指令为中文，并且指令中没有要求回复为别的语言的话，请你的结果value中也要回答中文
"""



Rethinking_prompt = Template("""
You are a highly professional NLP annotation editor. Your task is to modify the annotation results based on input, annotation results, and a series of annotation editing operations.

During your evaluation process, please first think through, then make two acts: Modify or Pass. Pass indicates that you believe this response is fairly good, fulfilling the task's requirements, with little to no room for revision. Modify indicates that you believe this output hasn't met the requirements, and you decide to revise the answer or generate your own response. If you chose Pass, please fill in "None" in the value field; if you chose Modify, please fill in the content you wish to modify in the value field.

Please think through before taking any action, it needs to be persuasive. Afterwards, please make your decision (Modify/Pass). If your decision is to Modify, please provide your revised result in the value field. If your decision is to Pass, please fill in "None" in the value field.

Please provide your review according to the following json format:
{
    "think": "<think>", 
    "act": "<Modify/Pass>",
    "value": "<value>"
}

Annotation Task:
$task

Input:
$input

Output:
$output

Please provide your review results in the json format mentioned above:
""")