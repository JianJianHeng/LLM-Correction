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

Please provide your revision suggestions according to the following json format.
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


# NLG task
instruct_task_prompt = """According to the requirements of the input instruction, respond with content that satisfies reliability, consistency, and common sense, and try to meet the requirements given by the instruction.
After ensuring that there are no obvious errors or omissions and that the instructions' requirements are not being deviated from, if you feel that the answer can be improved, you can use the Modify operation to make modifications to the sentence you wish to modify.
Please be more daring in improving outputs to make them even better.
"""



