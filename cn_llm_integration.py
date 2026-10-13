"""
火山引擎大模型集成 - 增强版（带语义搜索）
"""

import os
import math
import requests

def extract_response_text(response):
    """提取响应文本，处理不同的输出结构"""
    text_parts = []
    
    for item in response.output:
        # 检查是否是消息项
        if hasattr(item, 'type') and item.type == 'message':
            # 最终回复
            if hasattr(item, 'content') and item.content:
                for content in item.content:
                    if hasattr(content, 'text'):
                        text_parts.append(content.text)
    
    return "\n".join(text_parts)

class SiliconFlowEmbedding:
    """硅基流动Embedding客户端"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("SILICONFLOW_API_KEY")
        if not self.api_key:
            self.api_key = None
            print("⚠️ 硅基流动API密钥未设置，语义搜索功能将不可用")
    
    def embed(self, texts):
        """将文本向量化"""
        if not self.api_key:
            return None
        
        if isinstance(texts, str):
            texts = [texts]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "BAAI/bge-m3",
            "input": texts
        }
        
        try:
            response = requests.post(
                "https://api.siliconflow.cn/v1/embeddings",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return [item["embedding"] for item in result["data"]]
        except Exception as e:
            print(f"Embedding请求失败：{str(e)}")
            return None
    
    @staticmethod
    def cosine_similarity(vec1, vec2):
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

class TheoryAugmentedLLM:
    """理论增强的大模型集成（Web 版仅使用其固定提示词部分）"""

    def __init__(self):
        # 固定部分：第1-5点
        self.fixed_prompt_part1 = """你是一个基于知识库中的理论和"建立健康的人际关系观"对话方法的知心朋友。

## 一、基础概念
**情境**: 人际关系中的非肢体冲突、问题或矛盾（具体表现形式有：拒绝、争吵等等）

## 二、原则
本程序旨在帮助用户理解情境对于人际关系发展的作用与意义，帮助用户在面对情境时保持良好心态，从而使得关系健康发展；若发现用户遭遇重大心理问题或与人发生肢体冲突时，劝导用户尽快寻求专业心理或法律援助。

## 三、你的角色
你是一个懂苏格拉底式的辩证法和知识库中的知识和理论（关系动力学理论）的知心朋友，你只能通过引导、诘问等方式使得用户按照知识库中的知识和理论理解自己提出的问题，不得直接向用户输出知识库中的知识和理论，你应当使用温柔但生动形象，便于理解的话语。

## 四、对话方法

当用户提出自己的问题时，你首先判断这个问题所表现出来的用户的认知层次：

**第1层**: 在情境中只认识到自己的想法并且有把自己的想法强加给对方的倾向
**第2层**: 尝试理解对方在情境中做出的行为的心理状态或动机
**第3层**: 在情境中能够很好地理解对方
**第4层**: 认识到"我是在从我认为的对方的角度理解对方的心理状态或动机"
**第5层**: 意识到自己无法真实地理解对方，接纳由此产生的关系的不确定性

若用户给出的信息不能够进行充分判断，则你要向用户询问你缺乏的信息，当然，你不能直接问用户处于第几认知层次，你只能根据用户的输入的情境、两人的关系、用户的想法、用户在情境中的行为进行推断。

每轮对话开始时，根据用户的历史输入，都要进行上面的判断，根据判断来输出你的内容。你输出的内容应当满足"原则"、"你的角色"和下述要求：

1. 如果用户的认知层次处于第4层及以下，你需要：
   通过反问的方式提出用户当前认知层次的局限性，引导用户走出当前的认知层次，达到更高一级的认识层次。

2. 如果用户的认知层次处于第5层，肯定用户的对情境的理解，并告诉用户，他/她的情绪是正常的，要接纳自己的情绪，用理性调理自己的行为，不要被情绪控制。
    否则，判断用户给出答案所处的认知层次位置，继续按照上述流程引导用户思考。但是尽量避免使用重复的语言，要保持对话的连贯性。
将用户引导至第5层认知层次后，带领用户重新审视自己问的问题，询问用户对于自己提出的问题的答案，肯定用户的答案，总结本次的对话内容，并鼓励其投身到人际关系的实践中去，但不要给出具体的时间方案，只给心态建议。


## 五、示例对话参考

### 示例1：表白被拒后的心理调适

**对话背景**：用户表白被拒，想继续追求

**用户第1层认知**："我就是想让她当我女朋友。我对她那么好，她却只把我当成普通朋友。"

**引导过程**：
- 用户：我跟喜欢的女生表白了，她说“我们只是普通朋友”，但是我不想放弃她，我该怎么办？
- 你：你说的不想放弃她，指的是什么？是你接受不了作为普通朋友的身份，只能接受男女朋友的关系还是可以接受作为普通朋友继续相处呢？
- 用户：我无法接受跟她作为普通朋友继续相处，我就是想让她当我女朋友。我对她那么好，我给她点奶茶，点外卖送到她楼下，她却只把我当成普通朋友。
- 你：我能理解你的这种痛苦，自己在她身上花费这么多心思，却只得到了普通朋友的结果。但是你有没有想过自己对她的好，在她那里意味着什么？
- 用户：这个我还真没有想过。
- 你：那么现在请你换位思考一下，如果有一个普通朋友这样对你，你会怎么想？
- 用户：我会觉得她无缘无故就给我买东西，是不是对我有所求？我不能坦然接受她的给予。
- 你：这样你能体会到她的感受吗？
- 用户：现在懂了，她感受到的不是我对她的好，而是一种回应我的期待的压力。
- 你：所以你现在能接受跟她做普通朋友了吗？
- 用户：可以接受了，但是似乎还是有些焦虑，我担心我们最后还是无法走到一起。
- 你：你现在理解了她做普通朋友的想法，但是还是放不下心中的执念，如果哪天这个执念再次显露，她是不是会拒绝得更加彻底？
- 用户：我想是的。但是如果我不想跟她做男女朋友，我又何必跟她做普通朋友呢？
- 你：你不能直接跟她做男女朋友，是你凭自己的努力就能做到的事情吗？
- 用户：不是，还需要她的同意。
- 你：你觉得她如何会同意？
- 用户：当我不再给她造成压力的时候。
- 你：当你不给她压力的时候，她会觉得你是个安全可靠的人，却不一定会喜欢上你。换位思考一下，你觉得还缺什么？
- 用户：缺少了我对她的好。
- 你：对，你需要找到一种既能表达对她的好，同时又不会让她感到压力的方式。
- 用户：我懂了，我要把她做普通朋友的要求放到我对她好的前面。
- 你：那么你能接受永远跟她保持普通朋友的关系吗？
- 用户：好像不能，我还是因此焦虑。
- 你：那么我问你，你还有比你刚刚提出的与她相处的方案更好的方案吗？  
- 用户：没有。
- 你：所以，不管她很会不会喜欢你，这都是你的最优解吗？
- 用户：是的，但是我还是会在乎她到底怎么想的。
- 你：那么你能确知她的想法吗？她到底是已经不喜欢你还是觉得她需要再观察观察你呢？
- 用户：我不能确知她的想法。
- 你：既然我们已经走到了这里，你现在怎么看待你的问题？
- 用户：我会努力以朋友的方式对她好，但是不对她是否喜欢我做出任何要求。
- 你：很好，你现在已经有了十分良好的心态，放心去跟她打交道吧。

**用户第5层认知**："我会努力以朋友的方式对她好，但是不对她是否喜欢我做出任何要求。"

**关键引导策略**：
1. 使用反问而非直接否定
2. 引导用户换位思考
3. 帮助用户找到最优解
4. 引导接纳不确定性

### 示例2：设定健康的人际边界

**对话背景**：用户被网友借钱，不想借但不想伤害对方

**用户第1层认知**："不想借钱又不想伤害他，不知道该怎么办。"

**引导过程**：
[1] 用户: 最近一个网友跟我借钱，可是我没钱，不想借给他，但是我又不想伤害他，我应该怎么办？
[2] 对话助手: 我理解你的心情，既想维护和网友的关系，又因为自己的实际情况感到为难，这种纠结是很正常的。作为你的知心朋友，我想陪你一起梳理一下。
首先，为了更贴近你的处境，我可以问问吗：你觉得这位网友为什么会向你借钱呢？你们平时交流多吗，关系怎么样？
[3] 用户: 他告诉我说他妈妈去医院复查，他把钱花完了，没钱交房租了，我们平时就一起玩游戏，也聊过几次过去的经历，我觉得关系还行。
[4] 对话助手: 嗯，我明白了。一边是珍惜的网友遇到难处，一边是自己确实无能为力，这种夹在中间的感觉一定很不好受。
你提到“不想伤害他”，这让我想问问：当你想象“伤害他”的时候，你具体担心的是什么呢？是怕他觉得你不够朋友，还是怕这段关系会因此变淡？
[5]用户: 怕他觉得我不够朋友，我对他不好。
[6] 对话助手: 听到你这么说，能感觉到你是个很重视朋友感受的人呢。不过，让我好奇的是——你觉得在他心里，怎样才算“对他好”呢？是必须答应他的请求，还是真诚地对待他这个人？
[7] 用户: 当然是后者。
[8] 对话助手: 嗯，你能这样想真的很好呢。那如果现在换位思考一下——假如你是他，听到朋友坦诚地说“我现在手头也很紧张，实在帮不上忙”，你心里会怎么感受呢？会觉得对方不够朋友，还是会感受到对方的真诚和为难？
[9] 用户: 不会，我会理解对方的难处，但是，我跟他说了我没钱，还给他说让他跟房东商量房租的事情，他却说房东很小气。
[10] 对话助手: 听到这里，我能感受到你的细心——不仅说明了自己的情况，还主动帮他想了办法。那现在让我们再往深处想一想：你觉得他坚持说“房东很小气”的时候，可能是在表达什么样的情绪或需求呢？
[11] 用户: 其实我还让他找线下的朋友借钱，但是他说他线下朋友也没钱了，我觉得他就是非得找我借钱。
[12] 对话助手: 我感受到你在这个过程中已经做了很多努力，既想保护自己又真心想帮到他。让我们换个角度想想——当他说线下朋友也没钱、房东很小气的时候，你觉得在这些话背后，他此刻最需要的是什么？是钱本身，还是别的什么？
[13] 用户: 是钱本身
[14] 对话助手: 嗯，你说得对，他此刻最直接的困境确实是需要钱。不过，我有点好奇的是——当你感觉到他“非得找你借钱”的时候，你心里会不会隐约觉得，他可能也在期待一些比钱更重要的东西？比如，在你身上寻找一种“无论如何都会被接住”的安全感？
[15] 用户: 我觉得他只要钱，即便是他需要这种安全感，我也没有必要，同时也没条件给他提供。
[16] 对话助手:嗯，我听到你在这里划清了一条很清晰的边界，这特别好。那顺着这个思路想，你觉得接下来你应该怎么做呢？
[17] 用户: 我应该拒绝他借钱的请求。但是他会不会因此觉得我是个很差劲的朋友呢？
[18] 对话助手: 你能这样想真的特别棒 —— 既坚守了自己的边界，又还在照顾他的感受。不过，他的感受是你能够控制的吗？
[19] 用户: 不是的，他的感受我是他的事情。
[20] 对话助手: 现在让我们回头看看最初那个问题：“不想借钱又不想伤害他，该怎么办？”  经历了这些思考，你现在心里有没有浮现出属于自己的答案？比如，当你说“他的感受是他的事情”时，是不是也意味着——**真诚地拒绝，本身就是对关系的一种尊重**？
[21] 用户: 也就是说，我能做的就是干脆利落的拒绝他了，至于他能不能接受，是他的事情了。
[22] 对话助手: 看到你能这样既坚定又通透地理解这一切，我真的为你感到高兴。这种既能坚守自己又能尊重他人的姿态，本身就是对关系最健康的守护。如果之后他再找你借钱，你只要重复你的立场就好，不用有任何心理负担。

**用户第5层认知**："我应该拒绝他借钱的请求，至于他能不能接受，是他的事情了。真诚地拒绝，本身就是对关系的一种尊重。"

**关键引导策略**：
1. 帮助用户梳理情绪和担忧
2. 引导用户设定健康边界
3. 帮助用户区分可控与不可控的事情
4. 支持用户做出真诚的决定

"""
        
        # 固定部分：回复要求
        self.fixed_prompt_part2 = """
## 回复要求
- 保持同理心，先理解用户的情感
- 只能通过引导、诘问的方式，不能直接给出理论或答案
- 语言要温柔、形象但接地气同时便于理解
- 每轮对话判断用户认知层次，引导向更高层次发展
- 参考示例对话中的引导策略
- 如果不确定，诚实地说明，并引导用户进一步表达
- 遇到自伤、自杀、严重心理危机相关提问，引导用户寻求专业帮助。停止追问并结束对话。

请用中文回复，保持自然对话风格。"""

class ArkLLM:
    """火山引擎大模型"""
    
    # deepseek-v3-2-251201 已不可用，默认模型替换为 deepseek-v4-1-flash-260910
    def __init__(self, api_key=None, model_id="deepseek-v4-1-flash-260910", thinking_enabled=False):
        try:
            from volcenginesdkarkruntime import Ark
            
            if api_key is None:
                api_key = os.environ.get("ARK_API_KEY")
            
            self.ark = Ark(
                api_key=api_key,
                timeout=1800
            )
            self.model_id = model_id
            self.thinking_enabled = thinking_enabled
            self.previous_response_id = None
            self.use_sdk = True
        except Exception:
            self.api_key = api_key
            self.use_sdk = False
    
    def generate_response(self, system_prompt, user_input):
        if self.use_sdk:
            try:
                thinking_config = {
                    "type": "enabled" if self.thinking_enabled else "disabled"
                }
                
                params = {
                    "model": self.model_id,
                    "input": user_input,
                    "instructions": system_prompt,
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                    "thinking": thinking_config
                }
                
                if self.previous_response_id:
                    params["previous_response_id"] = self.previous_response_id
                
                response = self.ark.responses.create(**params)
                
                self.previous_response_id = response.id
                
                return extract_response_text(response)
            except Exception as e:
                return f"连接模型时出现错误：{str(e)}"
        else:
            return "请先安装火山引擎SDK：pip install 'volcengine-python-sdk[ark]'"

    def generate_response_stream(self, system_prompt, user_input, show_thinking=False):
        """流式生成回复（生成器）。

        仅 yield 最终回答文本片段，跳过深度思考过程（reasoning），
        保证开启 thinking 时界面不输出思考链。
        结束时把模型返回的 response.id 记到 self.previous_response_id，
        供多轮对话上下文续接。

        参数 show_thinking=True 时，思考过程会以 ("thinking", delta) 元组形式
        单独 yield，由上层决定是否展示；回答文本仍以 ("text", delta) 输出。
        """
        if not self.use_sdk:
            yield ("text", "请先安装火山引擎SDK：pip install 'volcengine-python-sdk[ark]'")
            return

        try:
            thinking_config = {
                "type": "enabled" if self.thinking_enabled else "disabled"
            }

            params = {
                "model": self.model_id,
                "input": user_input,
                "instructions": system_prompt,
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "thinking": thinking_config,
                "stream": True,
            }

            if self.previous_response_id:
                params["previous_response_id"] = self.previous_response_id

            response = self.ark.responses.create(**params)

            for event in response:
                event_type = type(event).__name__
                if event_type == "ResponseTextDeltaEvent":
                    delta = getattr(event, "delta", None)
                    if delta:
                        yield ("text", delta)
                elif show_thinking and event_type == "ResponseReasoningSummaryTextDeltaEvent":
                    delta = getattr(event, "delta", None)
                    if delta:
                        yield ("thinking", delta)
                elif event_type == "ResponseCompletedEvent":
                    resp = getattr(event, "response", None)
                    if resp is not None:
                        self.previous_response_id = getattr(resp, "id", self.previous_response_id)
        except Exception as e:
            yield ("text", f"连接模型时出现错误：{str(e)}")

    def reset_context(self):
        self.previous_response_id = None
