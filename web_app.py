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
import threading
import uuid
from datetime import datetime

from flask import Flask, g, jsonify, render_template, request

from cn_llm_integration import ArkLLM, SiliconFlowEmbedding, TheoryAugmentedLLM

# deepseek-v3-2-251201 已不可用，替换为 deepseek-v4-1-flash-260910
MODEL_ID = "deepseek-v4-1-flash-260910"

# 语义搜索相似度阈值（与命令行版保持一致）
SIMILARITY_THRESHOLD = 0.3

# 预计算知识向量文件（15条知识，BGE-M3向量）
KNOWLEDGE_VECTORS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_vectors.json")

app = Flask(__name__)
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

    ark_api_key = os.environ.get("ARK_API_KEY") or (request.json or {}).get("ark_api_key") or None
    siliconflow_api_key = os.environ.get("SILICONFLOW_API_KEY") or (request.json or {}).get("siliconflow_api_key") or None

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
        "ark_configured": bool(os.environ.get("ARK_API_KEY")),
        "siliconflow_configured": bool(os.environ.get("SILICONFLOW_API_KEY")),
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


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """重置对话上下文"""
    session = get_dialogue_session()
    with session.lock:
        session.reset_context()
    return jsonify({"ok": True})


@app.route("/api/examples", methods=["GET"])
def api_examples():
    """获取示例对话列表"""
    from 示例对话库 import DIALOGUE_EXAMPLES

    examples = [
        {
            "id": ex["id"],
            "title": ex["title"],
            "scenario": ex["scenario"],
            "initial_cognition": ex["initial_cognition"],
        }
        for ex in DIALOGUE_EXAMPLES
    ]
    return jsonify({"examples": examples})


@app.route("/api/save", methods=["POST"])
def api_save():
    """保存对话记录"""
    session = get_dialogue_session()

    if not session.conversation_log:
        return jsonify({"error": "暂无对话记录可保存"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"对话记录_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("关系动力学对话记录\n")
        f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        for role, message in session.conversation_log:
            f.write(f"{role}：{message}\n\n")

    return jsonify({"ok": True, "filename": filename})


if __name__ == "__main__":
    print("=" * 60)
    print("      关系动力学对话助手（Web 版）")
    print("      火山引擎大模型 + 语义搜索")
    print("=" * 60)
    print(f"模型：{MODEL_ID}")
    print(f"知识向量：{len(KNOWLEDGE_VECTORS)} 条已加载")
    print("✓ 语义搜索功能已启用" if os.environ.get("SILICONFLOW_API_KEY") else "⚠️ 语义搜索功能不可用（未设置硅基流动API密钥）")
    print("\n请访问 http://127.0.0.1:5000 开始对话\n")

    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
