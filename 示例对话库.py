"""
示例对话库
用于存储和展示苏格拉底式引导的示例对话
"""

DIALOGUE_EXAMPLES = [
    {
        "id": 1,
        "title": "表白被拒后的心理调适",
        "scenario": "用户表白被拒，想继续追求",
        "initial_cognition": "我就是想让她当我女朋友。我对她那么好，她却只把我当成普通朋友。",
        "final_cognition": "我会努力以朋友的方式对她好，但是不对她是否喜欢我做出任何要求。",
        "dialogue_steps": [
            "你有没有想过自己对她的好，在她那里意味着什么？",
            "如果有一个普通朋友这样对你，你会怎么想？",
            "（用户理解了对方的感受）",
            "现在能接受跟她做普通朋友了吗？",
            "跟她做男女朋友，是你凭自己的努力就能做到的事情吗？",
            "你觉得她如何会同意？",
            "当你不给她压力的时候，她会觉得你是个安全可靠的人，却不一定会喜欢上你。换位思考一下，你觉得还缺什么？",
            "你能确知她的想法吗？"
        ],
        "key_strategies": [
            "使用反问而非直接否定",
            "引导用户换位思考",
            "帮助用户找到最优解",
            "引导接纳不确定性"
        ],
        "cognitive_progression": "第1层 → 第2层 → 第3层 → 第4层 → 第5层"
    },
    {
        "id": 2,
        "title": "设定健康的人际边界",
        "scenario": "用户被网友借钱，不想借但不想伤害对方",
        "initial_cognition": "不想借钱又不想伤害他，不知道该怎么办。",
        "final_cognition": "我应该拒绝他借钱的请求，至于他能不能接受，是他的事情了。真诚地拒绝，本身就是对关系的一种尊重。",
        "dialogue_steps": [
            "你提到'不想伤害他'，这让我想问问：当你想象'伤害他'的时候，你具体担心的是什么呢？",
            "你觉得在他心里，怎样才算'对他好'呢？是必须答应他的请求，还是真诚地对待他这个人？",
            "假如你是他，听到朋友坦诚地说'我现在手头也很紧张，实在帮不上忙'，你心里会怎么感受呢？",
            "你觉得他坚持说'房东很小气'的时候，可能是在表达什么样的情绪或需求呢？",
            "当他说线下朋友也没钱、房东很小气的时候，你觉得在这些话背后，他此刻最需要的是什么？",
            "当你感觉到他'非得找你借钱'的时候，你心里会不会隐约觉得，他可能也在期待一些比钱更重要的东西？",
            "你已经划清了一条很清晰的边界，那顺着这个思路想，你觉得接下来你应该怎么做呢？",
            "他的感受是你能够控制的吗？",
            "经历了这些思考，你现在心里有没有浮现出属于自己的答案？"
        ],
        "key_strategies": [
            "帮助用户梳理情绪和担忧",
            "引导用户设定健康边界",
            "帮助用户区分可控与不可控的事情",
            "支持用户做出真诚的决定"
        ],
        "cognitive_progression": "第1层 → 第2层 → 第3层 → 第4层 → 第5层"
    }
]

def get_example_dialogue(dialogue_id):
    """获取指定ID的示例对话"""
    for example in DIALOGUE_EXAMPLES:
        if example["id"] == dialogue_id:
            return example
    return None

def get_all_examples():
    """获取所有示例对话"""
    return DIALOGUE_EXAMPLES

def format_example_for_prompt(example):
    """将示例对话格式化为提示词"""
    formatted = f"""
示例对话标题：{example['title']}
对话背景：{example['scenario']}

用户初始认知（{example['cognitive_progression'].split('→')[0].strip()}）：{example['initial_cognition']}

引导过程：
"""
    for i, step in enumerate(example['dialogue_steps'], 1):
        formatted += f"{i}. {step}\n"
    
    formatted += f"\n用户最终认知（{example['cognitive_progression'].split('→')[-1].strip()}）：{example['final_cognition']}\n\n"
    formatted += "关键引导策略：\n"
    for strategy in example['key_strategies']:
        formatted += f"- {strategy}\n"
    
    return formatted

def get_all_formatted_examples():
    """获取所有格式化后的示例对话"""
    return [format_example_for_prompt(example) for example in DIALOGUE_EXAMPLES]

def add_example_dialogue(
    title,
    scenario,
    initial_cognition,
    final_cognition,
    dialogue_steps,
    key_strategies,
    cognitive_progression="第1层 → 第2层 → 第3层 → 第4层 → 第5层"
):
    """添加新的示例对话"""
    new_id = max([ex["id"] for ex in DIALOGUE_EXAMPLES]) + 1
    new_example = {
        "id": new_id,
        "title": title,
        "scenario": scenario,
        "initial_cognition": initial_cognition,
        "final_cognition": final_cognition,
        "dialogue_steps": dialogue_steps,
        "key_strategies": key_strategies,
        "cognitive_progression": cognitive_progression
    }
    DIALOGUE_EXAMPLES.append(new_example)
    return new_example

if __name__ == "__main__":
    print("=" * 60)
    print("      示例对话库")
    print("=" * 60)
    
    print(f"\n共收录 {len(DIALOGUE_EXAMPLES)} 个示例对话\n")
    
    for example in DIALOGUE_EXAMPLES:
        print(f"[{example['id']}] {example['title']}")
        print(f"   对话背景：{example['scenario']}")
        print(f"   认知层次：{example['cognitive_progression']}")
        print()
    
    print("\n" + "=" * 60)
    print("      示例1详细信息")
    print("=" * 60)
    example = get_example_dialogue(1)
    print(format_example_for_prompt(example))
    
    print("\n" + "=" * 60)
    print("      示例2详细信息")
    print("=" * 60)
    example = get_example_dialogue(2)
    print(format_example_for_prompt(example))
