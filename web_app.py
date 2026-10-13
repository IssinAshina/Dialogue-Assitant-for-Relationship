"""
关系动力学对话助手 - Web 版
使用火山引擎大模型 + 硅基流动BAAI/bge-m3语义搜索
基于 chat_interface_cn.py（命令行版）改造为网页应用

运行方式：
    python web_app.py
然后浏览器访问 http://127.0.0.1:5000
"""

import json
import os
import sys
import threading
import uuid
import webbrowser
from datetime import datetime

from flask import Flask, Response, g, jsonify, render_template, request

from cn_llm_integration import ArkLLM, SiliconFlowEmbedding, TheoryAugmentedLLM

# deepseek-v3-2-251201 已不可用，替换为 deepseek-v4-1-flash-260910
MODEL_ID = "deepseek-v4-1-flash-260910"

# 语义搜索相似度阈值（与命令行版保持一致）
SIMILARITY_THRESHOLD = 0.3

# 心理危机关键词硬匹配（确定性，不依赖模型输出）
CRISIS_KEYWORDS = [
    "自杀", "想自杀", "自杀倾向", "轻生", "自残", "自伤", "割腕", "跳楼",
    "上吊", "服毒", "结束生命", "了结生命", "不想活", "不想活了", "活不下去",
    "活不下去了", "想死", "去死", "一了百了", "活着没意思", "活着没意义",
    "没有活下去的意义", "没有活下去的理由", "崩溃到想", "抑郁到想",
]

# 触发心理危机时的固定回复（停止追问、引导专业求助，不做任何诊断或治疗建议）
CRISIS_REPLY = (
    "我听到你现在非常痛苦，这种感受是真实的，你不是一个人。\n\n"
    "但我没办法在这些事情上真正帮到你，也请你不要伤害自己。"
    "请尽快联系专业心理援助：\n"
    "- 全国心理援助热线：400-161-9995\n"
    "- 北京心理危机研究与干预中心：010-82951332\n"
    "- 生命热线：400-821-1215\n\n"
    "如果此刻有立即的危险，请直接拨打 120 或 110。请一定找专业的人聊聊。"
)


def detect_crisis(text):
    """检测用户输入是否涉及自伤/自杀/严重心理危机"""
    if not text:
        return False
    return any(kw in text for kw in CRISIS_KEYWORDS)


def resource_path(relative_path):
    """获取资源文件路径，兼容 PyInstaller 冻结模式（sys._MEIPASS）"""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# 打包内嵌密钥（embedded_keys.py 已被 .gitignore 排除，仅打包时本地生成）
try:
    from embedded_keys import EMBEDDED_ARK_API_KEY, EMBEDDED_SILICONFLOW_API_KEY
except ImportError:
    EMBEDDED_ARK_API_KEY = ""
    EMBEDDED_SILICONFLOW_API_KEY = ""


def default_ark_key():
    """火山引擎密钥：环境变量优先，其次打包内嵌密钥"""
    return os.environ.get("ARK_API_KEY") or EMBEDDED_ARK_API_KEY or None


def default_siliconflow_key():
    """硅基流动密钥：环境变量优先，其次打包内嵌密钥"""
    return os.environ.get("SILICONFLOW_API_KEY") or EMBEDDED_SILICONFLOW_API_KEY or None


# 预计算知识向量文件（15条知识，BGE-M3向量）
KNOWLEDGE_VECTORS_PATH = resource_path("knowledge_vectors.json")

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", uuid.uuid4().hex)


def load_knowledge_vectors():
    """加载预计算的知识向量索引"""
    with open(KNOWLEDGE_VECTORS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


KNOWLEDGE_VECTORS = load_knowledge_vectors()

# 提示词构建器（复用命令行版中的固定提示词，简体中文内容保持不变）
PROMPT_BUILDER = TheoryAugmentedLLM()


def semantic_lookup(query, embedding_client, threshold=SIMILARITY_THRESHOLD):
    """基于预计算向量进行语义搜索，只需对用户输入向量化一次"""
    if not embedding_client.api_key:
        return None

    embeddings = embedding_client.embed(query)
    if not embeddings:
        return None

    # 解包嵌套列表
    query_embedding = embeddings[0] if isinstance(embeddings[0], list) else embeddings[0]

    # 确保query_embedding是一维列表
    if isinstance(query_embedding[0], list):
        query_embedding = query_embedding[0]

    best_item = None
    best_similarity = 0.0
    for item in KNOWLEDGE_VECTORS:
        similarity = embedding_client.cosine_similarity(query_embedding, item["embedding"])
        if similarity > best_similarity:
            best_similarity = similarity
            best_item = item

    if best_item and best_similarity >= threshold:
        return {
            "name": best_item["name"],
            "type": best_item["type"],
            "text": best_item["text"],
            "similarity": best_similarity,
        }
    return None


def build_theory_section(matched):
    """动态生成第6点：根据用户输入调用的相关理论"""
    theory_section = "## 六、理论基础（供你内部参考，不得直接输出）\n\n"

    if matched:
        theory_section += f"根据当前对话（相似度：{matched['similarity']:.2f}），以下是相关的理论参考：\n\n"
        theory_section += matched["text"]
    else:
        theory_section += "当前对话可能与调用的理论无直接关联，请基于对话方法和示例对话进行引导。"

    return theory_section


class WebDialogueSession:
    """网页版对话会话（每个浏览器会话独立）"""

    def __init__(self, ark_api_key, siliconflow_api_key, thinking_enabled=False):
        self.ark_api_key = ark_api_key
        self.siliconflow_api_key = siliconflow_api_key
        self.embedding_client = SiliconFlowEmbedding(siliconflow_api_key)
        self.ark_llm = ArkLLM(api_key=ark_api_key, model_id=MODEL_ID, thinking_enabled=thinking_enabled)
        self.conversation_log = []
        self.crisis_ended = False  # 心理危机命中后标记为已结束，不再继续引导
        self.lock = threading.Lock()

    def ensure_keys(self, ark_api_key, siliconflow_api_key, thinking_enabled):
        """当请求携带的密钥与会话密钥不一致时，重建对应客户端"""
        if ark_api_key and ark_api_key != self.ark_api_key:
            self.ark_api_key = ark_api_key
            self.ark_llm = ArkLLM(api_key=ark_api_key, model_id=MODEL_ID, thinking_enabled=thinking_enabled)
            self.conversation_log = []
        if siliconflow_api_key and siliconflow_api_key != self.siliconflow_api_key:
            self.siliconflow_api_key = siliconflow_api_key
            self.embedding_client = SiliconFlowEmbedding(siliconflow_api_key)

    def respond(self, user_input, thinking_enabled):
        """生成回复"""
        # 硬防护：会话已因心理危机结束，固定回复且不再调用模型
        if self.crisis_ended:
            self.conversation_log.append(("用户", user_input))
            self.conversation_log.append(("对话助手", CRISIS_REPLY))
            return CRISIS_REPLY, None

        # 硬防护：命中心理危机关键词，结束引导并返回固定求助话术
        if detect_crisis(user_input):
            self.crisis_ended = True
            self.conversation_log.append(("用户", user_input))
            self.conversation_log.append(("对话助手", CRISIS_REPLY))
            return CRISIS_REPLY, None

        self.ark_llm.thinking_enabled = thinking_enabled

        # 语义检索相关理论
        matched = semantic_lookup(user_input, self.embedding_client)

        # 构建完整的系统提示词
        system_prompt = (
            PROMPT_BUILDER.fixed_prompt_part1 +
            build_theory_section(matched) +
            PROMPT_BUILDER.fixed_prompt_part2
        )

        reply = self.ark_llm.generate_response(system_prompt, user_input)

        # 记录对话
        self.conversation_log.append(("用户", user_input))
        self.conversation_log.append(("对话助手", reply))

        return reply, matched

    def reset_context(self):
        """重置对话上下文"""
        self.ark_llm.reset_context()
        self.conversation_log = []
        self.crisis_ended = False


# 浏览器会话 -> 对话会话
DIALOGUE_SESSIONS = {}
SESSIONS_LOCK = threading.Lock()


@app.after_request
def set_dialogue_sid(response):
    """将会话ID写入浏览器Cookie"""
    sid = g.get("dialogue_sid")
    if sid:
        response.set_cookie("dialogue_sid", sid, max_age=7 * 24 * 3600, httponly=True)
    return response


def get_dialogue_session():
    """获取（或创建）当前浏览器的对话会话"""
    sid = request.cookies.get("dialogue_sid") or uuid.uuid4().hex
    g.dialogue_sid = sid

    ark_api_key = default_ark_key() or (request.json or {}).get("ark_api_key") or None
    siliconflow_api_key = default_siliconflow_key() or (request.json or {}).get("siliconflow_api_key") or None

    with SESSIONS_LOCK:
        session = DIALOGUE_SESSIONS.get(sid)
        if session is None:
            session = WebDialogueSession(ark_api_key, siliconflow_api_key)
            DIALOGUE_SESSIONS[sid] = session

    return session


@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


@app.route("/api/status", methods=["GET"])
def api_status():
    """检查API密钥配置状态"""
    return jsonify({
        "ark_configured": bool(default_ark_key()),
        "siliconflow_configured": bool(default_siliconflow_key()),
        "model_id": MODEL_ID,
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """对话接口"""
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"error": "请输入内容后再发送"}), 400

    thinking_enabled = bool(data.get("thinking", False))

    session = get_dialogue_session()
    session.ensure_keys(
        data.get("ark_api_key"),
        data.get("siliconflow_api_key"),
        thinking_enabled,
    )

    try:
        with session.lock:
            reply, matched = session.respond(user_input, thinking_enabled)
    except Exception as e:
        return jsonify({"error": f"连接模型时出现错误：{str(e)}"}), 500

    theory = None
    if matched:
        theory = {
            "name": matched["name"],
            "type": matched["type"],
            "similarity": round(matched["similarity"], 3),
        }

    return jsonify({"reply": reply, "theory": theory})


@app.route("/api/chat/stream", methods=["POST"])
def api_chat_stream():
    """流式对话接口（SSE）。

    事件协议：
      - {"type":"theory","theory":{...}|null}  命中的理论（可能为 null）
      - {"type":"text","content":"..."}          回答文本片段（多次）
      - {"type":"done"}                           流式结束
    心理危机命中时不进入流式，直接返回 JSON {"crisis":true,"reply":"..."}。
    """
    data = request.get_json(silent=True) or {}
    user_input = (data.get("message") or "").strip()

    if not user_input:
        return jsonify({"error": "请输入内容后再发送"}), 400

    thinking_enabled = bool(data.get("thinking", False))
    show_thinking = bool(data.get("show_thinking", False))

    session = get_dialogue_session()
    session.ensure_keys(
        data.get("ark_api_key"),
        data.get("siliconflow_api_key"),
        thinking_enabled,
    )

    # 硬防护：心理危机命中，不进入流式
    if session.crisis_ended or detect_crisis(user_input):
        session.crisis_ended = True
        with session.lock:
            session.conversation_log.append(("用户", user_input))
            session.conversation_log.append(("对话助手", CRISIS_REPLY))
        return jsonify({"crisis": True, "reply": CRISIS_REPLY})

    def generate():
        with session.lock:
            session.ark_llm.thinking_enabled = thinking_enabled

            # 语义检索相关理论
            matched = semantic_lookup(user_input, session.embedding_client)

            # 构建完整的系统提示词
            system_prompt = (
                PROMPT_BUILDER.fixed_prompt_part1 +
                build_theory_section(matched) +
                PROMPT_BUILDER.fixed_prompt_part2
            )

            theory = None
            if matched:
                theory = {
                    "name": matched["name"],
                    "type": matched["type"],
                    "similarity": round(matched["similarity"], 3),
                }
            yield f"data: {json.dumps({'type': 'theory', 'theory': theory}, ensure_ascii=False)}\n\n"

            full_reply = []
            for kind, chunk in session.ark_llm.generate_response_stream(system_prompt, user_input, show_thinking=show_thinking):
                if kind == "text":
                    full_reply.append(chunk)
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"
                elif kind == "thinking":
                    yield f"data: {json.dumps({'type': 'thinking', 'content': chunk}, ensure_ascii=False)}\n\n"

            reply_text = "".join(full_reply)
            session.conversation_log.append(("用户", user_input))
            session.conversation_log.append(("对话助手", reply_text))

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """重置对话上下文"""
    session = get_dialogue_session()
    with session.lock:
        session.reset_context()
    return jsonify({"ok": True})


@app.route("/api/save", methods=["POST"])
def api_save():
    """返回对话记录文本内容，由前端选择保存位置（不写入服务器磁盘）"""
    session = get_dialogue_session()

    if not session.conversation_log:
        return jsonify({"error": "暂无对话记录可保存"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"对话记录_{timestamp}.txt"

    lines = []
    lines.append("=" * 60)
    lines.append("关系动力学对话记录")
    lines.append(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")

    for role, message in session.conversation_log:
        lines.append(f"{role}：{message}")
        lines.append("")

    return jsonify({"ok": True, "filename": filename, "content": "\n".join(lines)})


if __name__ == "__main__":
    print("=" * 60)
    print("      关系动力学对话助手（Web 版）")
    print("      火山引擎大模型 + 语义搜索")
    print("=" * 60)
    print(f"模型：{MODEL_ID}")
    print(f"知识向量：{len(KNOWLEDGE_VECTORS)} 条已加载")
    print("✓ 语义搜索功能已启用" if default_siliconflow_key() else "⚠️ 语义搜索功能不可用（未设置硅基流动API密钥）")
    print("\n请访问 http://127.0.0.1:5000 开始对话\n")

    # 启动后自动打开浏览器（打包为可执行程序后方便面试官直接使用）
    threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
