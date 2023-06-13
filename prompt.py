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


NLU_label_prompt_Chinese = Template("""
你是一位高度专业的自然语言处理（NLP）标注人员。你的任务是根据任务需求，对输入的文本进行标注。

标注任务：
$task

标注样例：
input:
个股跌多涨少，跌停家数近60家，多头动能全无，成交量萎靡，资金氛围趋冷。
label:
[
    {"事件": "跌停", "触发词": "跌停"}
]
input:
宝鼎科技(002552)周二上涨10.01%。公司是一家主要从事各类大型铸锻件产品研发、生产和销售的高新技术企业，下设机械、水压机、锻造、机加工、铸造五个分厂，年生产能力达10万吨。公司产品作为装备制造业的关键核心部件，广泛用于船舶、海洋工程、电力、工程机械和军工等行业。最新消息，公司控股股东将变为招金集团；公司控股股东部分股份质押展期。二级市场上，该股复牌九天收获八涨停，知名游资日前现身龙虎榜，追涨或有风险。
label:
[
    {"事件": "涨停", "触发词": "涨停", "涨停股票": "宝鼎科技(002552)"}
]
input:
美瑞健康国际(02327)公告，2019年9月4日，美瑞健康国际，通过其一家全资附属公司，签订了股权转让协议，向一位自然人收购深圳龙舞科技创新有限公司(深圳龙舞)的8.3077%股权(于公司根据该公告中提述的增资协议完成对深圳龙舞的6%增资后，该股权将被稀释到7.809231%)，收购对价为约人民币1080.3万元，此收购对价乃按照公司同意对深圳龙舞增资6%之前深圳龙舞的上一轮融资的投资后估值即人民币1.3亿元计算得出的数字作为估值而得出。
label:
[
    {"事件": "出售/收购", "触发词": "收购", "时间": "2019年9月4日", "出售方": "一位自然人", "交易物": "深圳龙舞科技创新有限公司(深圳龙舞)的8.3077%股权", "出售价格": "约人民币1080.3万元", "收购方": "美瑞健康国际"}, 
    {"事件": "融资", "触发词": "融资", "融资方": "深圳龙舞科技创新有限公司", "融资金额": "人民币1.3亿元"}
]
input:
挪威央行进一步与其他国家央行背道而驰，宣布了一年以来的第四次加息决定，以期给受到石油投资推动的经济降温。
label:
[
    {"事件": "加息", "触发词": "加息", "加息机构": "挪威央行"}
]


接下来请你根据任务的要求，以上述要求的JSON格式提供你的标注结果。注意你只用返回一个json格式的标注结果，不要生成多余的样例：

input:
$input
label:
""")


NLU_modifed_prompt_Chinese = Template("""
您是一位高度专业的自然语言处理（NLP）标注审核员。您的任务是使用一系列操作，根据输入审核标注结果。

质量检查任务
请评估上述注释结果是否满足注释任务的要求。您可以执行以下操作来更正注释结果：
1）Pass：您认为注解的答案满足了注解任务的要求且没有错误，因此您通过了这个注解结果。
2）Add：您认为注释的答案有遗漏，决定为其答案添加内容。请指明您希望在哪个句子之后添加，并提供要添加的内容。
3）Delete：您认为注释的答案包含了冗余的内容，您认为这些内容应被删除。请指出您希望删除的句子的编号。
4）Modify：您认为注释的答案有错误，或者您认为这个答案可以进一步修改。请指出您希望修改的句子的编号，并提供修改后的句子内容。

请根据以下的json格式提供您的修订建议：
'''
[
    {
        “Reson”: "<提供原因>",                  # 请分析一下您采取这个操作的原因
        "Operation": "<提供操作>",              # 提供这个操作，它必须是 Pass, Add, Delete, Modify 之一
        "Key": "<>",         # 提供此操作的句子编号，通过时请给出 -1
        "Content": "<修改内容>"                  # 如果是 Add, Modify 操作，请提供添加或修改的文本内容。如果是 Pass, Delete 操作，请提供 "none"。
    },
    {
        "Operation": "<提供操作>",           
        "Sentence id": "<指示句子编号>",     
        "Content": "<修改内容>"
    },
    ....
]
'''

接下来，我们将为您详细介绍注解任务，注解任务的输入，注解任务的输出，以及一系列的修改操作。
请注意，我们提供的操作序列中的 "Content" 是一个列表。您可以从列表中选择一个，或者合并所有答案提供您认为最理想的一个。您返回的结果中的 "Content" 必须是一个字符串。
请按照指定的顺序和提到的输出格式完成修改操作。

请根据以下结果提供您的修改结果：

注释任务：
$task

输入：
$input

输出：
$output

操作：
$operations

请以JSON格式提供审查结果：
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
    "Which better": "<Enthusiasm/Ambition>"         # Please select the result that you believe is better and more suitable for the annotation task. Your choice must be one of the following: Enthusiasm, Ambition.
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


Rethinking_prompt_chinese = Template("""
你是一位专业的资深NLP标注审核员。你的任务是审核输入和其对应的标注结果，并对出现问题的标注进行修改。

在你的评估过程中，请你首先理解标注任务的要求，然后对输入和标注结果进行分析，之后做出两种Act：Pass或Modify。Pass表示你认为这个回应相当好，满足任务的要求，几乎没有需要修改的地方。Modify则表示你认为这个输出存在问题，没有达到标注要求，你决定修改一下你的回答。

请在采取任何Act前进行深度思考，你给出的理由需要有说服力。然后，请在act字段中做出你的决定（Pass/Modify）。注意，如果你选择Pass，请在value字段中填写“None”；如果你选择Modify，请在value字段中填写你修改后的标注。

请按照以下的json格式提供你的审核结果：
{
    "think": "<think>", 
    "act": "<Modify/Pass>",
    "value": "<value>"
}


标注任务：
$task

审核样例：
'''
输入：
徐闻港航公司收购广东双泰集团逾九成股权
标签：
[{'事件': '出售/收购', '触发词': '收购', '出售方': '广东双泰集团', '收购方': '徐闻港航公司', '交易物': '逾九成股权'}]
审核：
{
    "think": "标签中已经准确地标记出了相关的事件，事件触发词以及事件要素。出售/收购事件，触发词是'收购'，出售方是'广东双泰集团'，收购方是'徐闻港航公司'，交易物是'逾九成股权'。该文本中不存在的事件要素在结果字典中没有显示，符合要求。", 
    "act": "Pass",
    "value": "None"
}
输入：
港股异动︱福莱特玻璃(06865)A股涨停板 H股跟涨近5%
标签：
[{'事件': '涨停', '触发词': '涨停板', '市场': '玻璃'}, {'事件': '涨价', '触发词': '跟涨', '涨价物': '玻璃', '涨价幅度': '近5%'}]
审核：
{
    "think": "标注结果中存在两个主要的问题。首先，对于'涨停'事件的标注，抽取的'市场'不属于任务要求中的事件要素，且文中提到了'涨停股票'是'福莱特玻璃(06865)'。其次，对于'涨价'事件的标注，抽取的'涨价物'同样应该是'福莱特玻璃(06865)'而非'玻璃'。综上所述，该标注结果需要修改。",
    "act": "Modify",
    "value": "[{'事件': '涨停', '触发词': '涨停板', '涨停股票': '福莱特玻璃(06865)'}, {'事件': '涨价', '触发词': '跟涨', '涨价物': '福莱特玻璃(06865) H股', '涨价幅度': '近5%'}]"
}
输入：
骁龙845+IP68+4000mAH, 降至1999成高配置高性价比中端机
标签：
[{'事件': '降价', '触发词': '降至', '降价物': '骁龙845+IP68+4000mAH', '降价幅度': '1999元'}]
审核：
{
    "think": "在标注中，事件识别为'降价'是准确的，触发词和降价物也是正确的。然而，降价幅度的标注为'1999元'存在错误，因为'1999元'实际上是降价后的价格，而非降价的幅度。但是因为文本中并未明确给出降价的幅度，故应在结果中不予显示。",
    "act": "Modify",
    "value": "[{'事件': '降价', '触发词': '降至', '降价物': '骁龙845+IP68+4000mAH'
}
'''


接下来，请按照上述的json格式，对下面的输入和标签进行审核：

输入：
$input
标签：
$output
审核：
""")



event_label_task = """你的任务是要从文本中提取出相关的事件、事件触发词和事件要素，你所有抽取的事件schema如下所示：
-----------------------------------------------------
<事件>：<事件要素>
出售/收购： 时间 - 出售方 - 交易物 - 出售价格 - 收购方
跌停： 时间 - 跌停股票
加息： 时间 - 加息幅度 - 加息机构
降价： 时间 - 降价方 - 降价物 - 降价幅度
降息： 时间 - 降息幅度 - 降息机构
融资： 时间 - 跟投方 - 领投方 - 融资轮次 - 融资金额 - 融资方
上市： 时间 - 地点 - 上市企业 - 融资金额
涨价： 时间 - 涨价幅度 - 涨价物 - 涨价方
涨停： 时间 - 涨停股票
-----------------------------------------------------
请注意，一个文本中可能出现多个事件，你需要将所有的事件都抽取出来。对于文本中不存在的事件要素，在结果的字典中不予显示。
"""


