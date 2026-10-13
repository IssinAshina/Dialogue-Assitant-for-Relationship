/* 关系动力学对话助手 - 前端逻辑 */

const LS_ARK_KEY = "gdlx_ark_api_key";
const LS_SF_KEY = "gdlx_siliconflow_api_key";

const els = {
    messages: document.getElementById("messages"),
    chatScroll: document.getElementById("chatScroll"),
    emptyState: document.getElementById("emptyState"),
    input: document.getElementById("input"),
    sendBtn: document.getElementById("sendBtn"),
    resetBtn: document.getElementById("resetBtn"),
    saveBtn: document.getElementById("saveBtn"),
    thinkingToggle: document.getElementById("thinkingToggle"),
    theoryCard: document.getElementById("theoryCard"),
    modelTag: document.getElementById("modelTag"),
    toast: document.getElementById("toast"),

    drawerToggle: document.getElementById("drawerToggle"),
    drawerMask: document.getElementById("drawerMask"),
    sidebar: document.getElementById("sidebar"),

    settingsModal: document.getElementById("settingsModal"),
    settingsToggle: document.getElementById("settingsToggle"),
    settingsToggleMobile: document.getElementById("settingsToggleMobile"),
    settingsClose: document.getElementById("settingsClose"),
    settingsSave: document.getElementById("settingsSave"),
    arkKeyInput: document.getElementById("arkKeyInput"),
    sfKeyInput: document.getElementById("sfKeyInput"),
    keyStatus: document.getElementById("keyStatus"),
};

let pending = false;
let hasConversation = false;

/* ---------- 工具 ---------- */

function toast(text, duration = 2600) {
    els.toast.textContent = text;
    els.toast.classList.add("show");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => els.toast.classList.remove("show"), duration);
}

function escapeHtml(str) {
    return str.replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
}

function scrollBottom() {
    els.chatScroll.scrollTop = els.chatScroll.scrollHeight;
}

function getKey(name) {
    return localStorage.getItem(name) || "";
}

/* ---------- 消息渲染 ---------- */

function addUserMessage(text) {
    hasConversation = true;
    els.emptyState.style.display = "none";
    const wrap = document.createElement("div");
    wrap.className = "msg user";
    wrap.innerHTML = `
        <div class="avatar">我</div>
        <div class="bubble"></div>`;
    wrap.querySelector(".bubble").textContent = text;
    els.messages.appendChild(wrap);
    scrollBottom();
}

function addTypingMessage() {
    const wrap = document.createElement("div");
    wrap.className = "msg assistant";
    wrap.id = "pendingMsg";
    wrap.innerHTML = `
        <div class="avatar">知</div>
        <div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div>`;
    els.messages.appendChild(wrap);
    scrollBottom();
}

function addErrorMessage(text) {
    hasConversation = true;
    els.emptyState.style.display = "none";
    document.getElementById("pendingMsg")?.remove();
    const wrap = document.createElement("div");
    wrap.className = "msg assistant error";
    wrap.innerHTML = `
        <div class="avatar">知</div>
        <div class="bubble"></div>`;
    wrap.querySelector(".bubble").textContent = text;
    els.messages.appendChild(wrap);
    scrollBottom();
}

/* 打字机逐字显示 */
function typewriter(el, text, done) {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
        el.textContent = text;
        scrollBottom();
        done && done();
        return;
    }
    let i = 0;
    const caret = document.createElement("span");
    caret.className = "caret";
    const textNode = document.createTextNode("");
    el.textContent = "";
    el.appendChild(textNode);
    el.appendChild(caret);
    const step = () => {
        const chunk = Math.max(1, Math.round(text.length / 220));
        i = Math.min(text.length, i + chunk);
        textNode.data = text.slice(0, i);
        scrollBottom();
        if (i < text.length) {
            setTimeout(step, 24);
        } else {
            caret.remove();
            done && done();
        }
    };
    setTimeout(step, 120);
}

function finishAssistantMessage(text, theory) {
    document.getElementById("pendingMsg")?.remove();
    hasConversation = true;
    els.emptyState.style.display = "none";
    const wrap = document.createElement("div");
    wrap.className = "msg assistant";
    wrap.innerHTML = `
        <div class="avatar">知</div>
        <div class="bubble"></div>`;
    els.messages.appendChild(wrap);
    const bubble = wrap.querySelector(".bubble");
    typewriter(bubble, text, () => {
        if (theory) renderTheory(theory);
    });
}

function renderTheory(theory) {
    const pct = Math.round(theory.similarity * 100);
    els.theoryCard.innerHTML = `
        <div>
            <span class="theory-name">${escapeHtml(theory.name)}</span>
            <span class="theory-type">${escapeHtml(theory.type)}</span>
        </div>
        <div class="similarity-row">
            <div class="similarity-track"><div class="similarity-fill" style="width:0%"></div></div>
            <span class="similarity-val">相似度 ${theory.similarity.toFixed(3)}</span>
        </div>`;
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            els.theoryCard.querySelector(".similarity-fill").style.width = pct + "%";
        });
    });
}

/* ---------- 发送 ---------- */

async function sendMessage() {
    const text = els.input.value.trim();
    if (!text || pending) return;

    els.input.value = "";
    autoResize();
    els.sendBtn.disabled = true;
    pending = true;
    addUserMessage(text);
    addTypingMessage();

    const body = {
        message: text,
        thinking: els.thinkingToggle.checked,
    };
    const arkKey = getKey(LS_ARK_KEY);
    const sfKey = getKey(LS_SF_KEY);
    if (arkKey) body.ark_api_key = arkKey;
    if (sfKey) body.siliconflow_api_key = sfKey;

    try {
        const res = await fetch("/api/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        const contentType = res.headers.get("content-type") || "";

        // 非流式响应：心理危机命中或参数错误
        if (!contentType.includes("text/event-stream")) {
            const data = await res.json();
            document.getElementById("pendingMsg")?.remove();
            if (data.crisis) {
                finishAssistantMessage(data.reply, null);
            } else if (!res.ok) {
                addErrorMessage(data.error || "服务出现未知错误，请稍后重试。");
            } else {
                finishAssistantMessage(data.reply, data.theory);
            }
            return;
        }

        // 流式响应：创建助手气泡，逐段追加文本
        document.getElementById("pendingMsg")?.remove();
        hasConversation = true;
        els.emptyState.style.display = "none";
        const wrap = document.createElement("div");
        wrap.className = "msg assistant";
        wrap.innerHTML = `<div class="avatar">知</div><div class="bubble"></div>`;
        els.messages.appendChild(wrap);
        const bubble = wrap.querySelector(".bubble");

        if (!res.body) {
            addErrorMessage("当前浏览器不支持流式读取，请改用最新版 Chrome/Edge。");
            return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let streamDone = false;

        while (!streamDone) {
            const { value, done } = await reader.read();
            streamDone = done;
            if (!value) continue;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || ""; // 保留未完成的最后一行
            for (const line of lines) {
                if (!line.startsWith("data:")) continue;
                const payload = line.slice(5).trim();
                if (!payload) continue;
                let evt;
                try { evt = JSON.parse(payload); } catch (e) { continue; }
                if (evt.type === "theory" && evt.theory) {
                    renderTheory(evt.theory);
                } else if (evt.type === "text") {
                    bubble.textContent += evt.content;
                    scrollBottom();
                } else if (evt.type === "error") {
                    addErrorMessage(evt.message || "服务出现错误");
                    return;
                }
            }
        }
    } catch (err) {
        addErrorMessage("无法连接到本地服务，请确认 web_app.py 正在运行。");
    } finally {
        pending = false;
        els.sendBtn.disabled = false;
        els.input.focus();
    }
}

/* ---------- 重置 / 保存 ---------- */

async function resetConversation() {
    if (pending) { toast("请等待当前回复完成"); return; }
    try {
        await fetch("/api/reset", { method: "POST" });
    } catch (e) { /* 服务未运行时仅清空界面 */ }
    els.messages.innerHTML = "";
    hasConversation = false;
    els.emptyState.style.display = "flex";
    els.theoryCard.innerHTML = `<p class="theory-empty">等待对话开始…</p>`;
    toast("对话已重置");
}

async function saveConversation() {
    if (!hasConversation) { toast("暂无对话记录可保存"); return; }
    try {
        const res = await fetch("/api/save", { method: "POST" });
        const data = await res.json();
        if (!res.ok) { toast(data.error || "保存失败"); return; }

        const blob = new Blob([data.content], { type: "text/plain;charset=utf-8" });

        // 优先使用 File System Access API，让用户选择保存位置
        if (window.showSaveFilePicker) {
            try {
                const handle = await window.showSaveFilePicker({
                    suggestedName: data.filename,
                    types: [{ description: "文本文件", accept: { "text/plain": [".txt"] } }],
                });
                const writable = await handle.createWritable();
                await writable.write(blob);
                await writable.close();
                toast("对话记录已保存");
                return;
            } catch (err) {
                if (err.name === "AbortError") return; // 用户取消了选择
                toast("保存失败，尝试浏览器下载…");
            }
        }

        // 回退：触发浏览器下载（用户可在下载对话框中选择位置）
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
        toast("对话记录已下载");
    } catch (e) {
        toast("无法连接到本地服务");
    }
}

/* ---------- 设置 ---------- */

function openSettings() {
    els.arkKeyInput.value = getKey(LS_ARK_KEY);
    els.sfKeyInput.value = getKey(LS_SF_KEY);
    updateKeyStatus();
    els.settingsModal.classList.add("open");
    els.arkKeyInput.focus();
}

function closeSettings() {
    els.settingsModal.classList.remove("open");
}

function updateKeyStatus() {
    const hasArk = Boolean(getKey(LS_ARK_KEY));
    const hasSf = Boolean(getKey(LS_SF_KEY));
    const parts = [];
    parts.push(hasArk ? "✓ 已填写火山引擎密钥" : "○ 未填写火山引擎密钥");
    parts.push(hasSf ? "✓ 已填写硅基流动密钥" : "○ 未填写硅基流动密钥（语义检索将不可用）");
    els.keyStatus.textContent = parts.join("　");
}

/* ---------- 初始化 ---------- */

async function loadStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        els.modelTag.textContent = `模型：${data.model_id}`;
        if (!data.ark_configured && !getKey(LS_ARK_KEY)) {
            toast("尚未配置火山引擎 API Key，请点击右上角「密钥设置」", 4200);
        }
    } catch (e) {
        els.modelTag.textContent = "模型：服务未连接";
    }
}

function autoResize() {
    els.input.style.height = "auto";
    els.input.style.height = Math.min(els.input.scrollHeight, 150) + "px";
}

function closeDrawer() {
    els.sidebar.classList.remove("open");
    els.drawerMask.classList.remove("show");
}

/* 事件绑定 */
els.sendBtn.addEventListener("click", sendMessage);
els.resetBtn.addEventListener("click", resetConversation);
els.saveBtn.addEventListener("click", saveConversation);

els.input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
els.input.addEventListener("input", autoResize);

els.drawerToggle.addEventListener("click", () => {
    els.sidebar.classList.toggle("open");
    els.drawerMask.classList.toggle("show", els.sidebar.classList.contains("open"));
});
els.drawerMask.addEventListener("click", closeDrawer);

els.settingsToggle.addEventListener("click", openSettings);
els.settingsToggleMobile.addEventListener("click", openSettings);
els.settingsClose.addEventListener("click", closeSettings);
els.settingsModal.addEventListener("click", e => {
    if (e.target === els.settingsModal) closeSettings();
});
els.settingsSave.addEventListener("click", () => {
    const ark = els.arkKeyInput.value.trim();
    const sf = els.sfKeyInput.value.trim();
    ark ? localStorage.setItem(LS_ARK_KEY, ark) : localStorage.removeItem(LS_ARK_KEY);
    sf ? localStorage.setItem(LS_SF_KEY, sf) : localStorage.removeItem(LS_SF_KEY);
    updateKeyStatus();
    closeSettings();
    toast("密钥已保存到本浏览器");
});
document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeSettings();
});

loadStatus();
els.input.focus();
