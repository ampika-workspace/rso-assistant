"""
🤖 Page 5 — Chatbot ถาม-ตอบความปลอดภัยทางรังสี
โมเดล: Typhoon2 (scb10x/llama3.1-typhoon2-8b-instruct) ผ่าน HF Serverless API
"""
import streamlit as st
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Chatbot ความปลอดภัยทางรังสี",
    page_icon="🤖", layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif !important; }
.chat-user {
    background: #eff6ff; border-radius: 12px 12px 4px 12px;
    padding: 12px 16px; margin: 8px 0; margin-left: 15%;
    border: 1px solid #bfdbfe;
}
.chat-bot {
    background: #f8fafc; border-radius: 12px 12px 12px 4px;
    padding: 12px 16px; margin: 8px 0; margin-right: 10%;
    border: 1px solid #e2e8f0; border-left: 4px solid #1a4a7a;
}
.status-ok   { background:#f0fdf4; border:1.5px solid #16a34a; border-radius:8px; padding:8px 14px; }
.status-warn { background:#fffbeb; border:1.5px solid #d97706; border-radius:8px; padding:8px 14px; }
.status-err  { background:#fef2f2; border:1.5px solid #dc2626; border-radius:8px; padding:8px 14px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_ID    = "scb10x/llama3.1-typhoon2-8b-instruct"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
HF_CHAT_URL = "https://api-inference.huggingface.co/v1/chat/completions"

SYSTEM_PROMPT = """คุณเป็นผู้เชี่ยวชาญด้านความปลอดภัยทางรังสีและกฎหมายพลังงานนิวเคลียร์ของประเทศไทย
ช่วยตอบคำถามเกี่ยวกับ:
- กฎหมายพลังงานนิวเคลียร์เพื่อสันติ พ.ศ. 2559 และกฎกระทรวงที่เกี่ยวข้อง
- แนวปฏิบัติของสำนักงานปรมาณูเพื่อสันติ (ปส.)
- มาตรฐาน IAEA และ ICRP ด้านความปลอดภัยทางรังสี
- การป้องกันอันตรายจากรังสี การขนส่ง ความมั่นคงปลอดภัย
- เวชศาสตร์นิวเคลียร์และรังสีการแพทย์

กฎการตอบ:
1. ตอบเป็นภาษาไทยเสมอ แม้คำถามหรือเอกสารจะเป็นภาษาอังกฤษ
2. ถ้ามีข้อมูลจากเอกสารที่ผู้ใช้อัปโหลด ให้อ้างอิงชื่อเอกสารและหน้าด้วย
3. ถ้าข้อมูลมาจากการค้นหา ให้บอกว่ามาจากแหล่งไหน
4. ถ้าไม่แน่ใจ ให้บอกตรงๆ และแนะนำให้ตรวจสอบกับ ปส. โดยตรง
5. ให้คำตอบที่ถูกต้องตามกฎหมายและมาตรฐานสากล"""

SUGGESTIONS = [
    "วัสดุกัมมันตรังสีประเภท 2 มีมาตรการความมั่นคงปลอดภัยอะไรบ้าง?",
    "ขีดจำกัดปริมาณรังสีสำหรับผู้ปฏิบัติงานทางรังสีตามกฎหมายไทยคือเท่าไหร่?",
    "Transport Index คืออะไร คำนวณอย่างไร?",
    "D-value ของ Ir-192 คือเท่าไหร่ และใช้ทำอะไร?",
    "Controlled Area และ Supervised Area แตกต่างกันอย่างไร?",
    "กรณีวัสดุกัมมันตรังสีสูญหายต้องแจ้งหน่วยงานอะไรบ้าง?",
    "ALARA principle คืออะไร ประยุกต์ใช้อย่างไรในทางปฏิบัติ?",
    "HVL ของตะกั่วสำหรับ Co-60 คือเท่าไหร่?",
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def test_api_connection(hf_token: str) -> tuple[bool, str]:
    """ทดสอบการเชื่อมต่อ HF API"""
    try:
        resp = requests.post(
            HF_CHAT_URL,
            headers={"Authorization": f"Bearer {hf_token}",
                     "Content-Type": "application/json"},
            json={"model": MODEL_ID,
                  "messages": [{"role": "user", "content": "hi"}],
                  "max_tokens": 5},
            timeout=15,
        )
        if resp.status_code == 200:
            return True, "เชื่อมต่อสำเร็จ"
        elif resp.status_code == 401:
            return False, "Token ไม่ถูกต้อง"
        elif resp.status_code == 503:
            return True, "โมเดลกำลัง warm up (ปกติ)"
        else:
            return False, f"Error {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except Exception as e:
        return False, str(e)[:60]


def call_typhoon2(messages: list, hf_token: str, max_tokens: int = 800) -> str:
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "stream": False,
    }
    try:
        resp = requests.post(HF_CHAT_URL, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        elif resp.status_code == 503:
            return "⏳ โมเดลกำลัง warm up อยู่ค่ะ กรุณารอสัก 20-30 วินาทีแล้วลองใหม่"
        elif resp.status_code == 401:
            return "❌ HF Token ไม่ถูกต้อง กรุณาตรวจสอบใน sidebar ค่ะ"
        elif resp.status_code == 429:
            return "⚠️ Rate limit เกิน กรุณารอสักครู่แล้วลองใหม่ค่ะ"
        else:
            return f"❌ Error {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.Timeout:
        return "⏰ Timeout — โมเดลใช้เวลานานเกินไป กรุณาลองใหม่ค่ะ"
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}"


def web_search(query: str, num_results: int = 4) -> list[dict]:
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
        )
        data = resp.json()
        results = []
        if data.get("Abstract"):
            results.append({"title": data.get("Heading", ""), "snippet": data["Abstract"],
                            "url": data.get("AbstractURL", "")})
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({"title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                                "snippet": topic["Text"], "url": topic.get("FirstURL", "")})
        return results[:num_results]
    except Exception as e:
        return [{"title": "Error", "snippet": f"ค้นหาไม่สำเร็จ: {e}", "url": ""}]


def extract_pdf_text(uploaded_file) -> list[dict]:
    try:
        import pypdf, io
        reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
        chunks = []
        for page_num, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
            if not paragraphs:
                paragraphs = [text[i:i+500] for i in range(0, len(text), 500)]
            for para in paragraphs:
                chunks.append({"text": para, "page": page_num + 1,
                               "filename": uploaded_file.name})
        return chunks
    except ImportError:
        st.error("กรุณาติดตั้ง pypdf: `pip install pypdf`")
        return []
    except Exception as e:
        st.error(f"อ่าน PDF ไม่สำเร็จ: {e}")
        return []


def search_chunks(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    try:
        from sentence_transformers import SentenceTransformer, util
        if "embed_model" not in st.session_state:
            st.session_state.embed_model = SentenceTransformer(EMBED_MODEL)
        model = st.session_state.embed_model
        texts = [c["text"] for c in chunks]
        q_emb = model.encode(query, convert_to_tensor=True)
        c_embs = model.encode(texts, convert_to_tensor=True)
        scores = util.cos_sim(q_emb, c_embs)[0]
        top_idx = scores.topk(min(top_k, len(chunks))).indices.tolist()
        return [{**chunks[i], "score": float(scores[i])} for i in top_idx]
    except Exception:
        query_words = set(query.lower().split())
        scored = [{**c, "score": sum(1 for w in query_words if w in c["text"].lower())}
                  for c in chunks]
        return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 HF Token")
    hf_token = st.text_input(
        "Hugging Face Token", type="password",
        help="สร้างได้ที่ huggingface.co/settings/tokens → Permission: Inference API",
        placeholder="hf_xxxxxxxxxxxx",
    )

    # ── Status indicator ──────────────────────────────────────────────────────
    if hf_token:
        if st.button("🔌 ทดสอบการเชื่อมต่อ", use_container_width=True):
            with st.spinner("กำลังทดสอบ..."):
                ok, msg = test_api_connection(hf_token)
            st.session_state["api_status"] = (ok, msg)

        status = st.session_state.get("api_status")
        if status:
            ok, msg = status
            if ok:
                st.markdown(f"""<div class="status-ok">
                    ✅ <b>เชื่อมต่อสำเร็จ</b><br>
                    <small style="color:#166534;">Typhoon2 พร้อมใช้งาน — {msg}</small>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="status-err">
                    ❌ <b>เชื่อมต่อไม่สำเร็จ</b><br>
                    <small style="color:#991b1b;">{msg}</small>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="status-warn">
                ⚪ <b>ยังไม่ได้ทดสอบ</b><br>
                <small style="color:#92400e;">กดปุ่มด้านบนเพื่อตรวจสอบ</small>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        **วิธีสร้าง HF Token:**
        1. ไปที่ [settings/tokens](https://huggingface.co/settings/tokens)
        2. New token → Permission: **Inference API**
        3. Copy มาวางด้านบน
        """)
    else:
        st.markdown("""<div class="status-warn">
            ⚠️ <b>กรุณาใส่ HF Token</b><br>
            <small style="color:#92400e;">จำเป็นสำหรับเรียกใช้ Typhoon2</small>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── Session info ──────────────────────────────────────────────────────────
    st.markdown("### 📊 Session")
    docs = st.session_state.get("pdf_chunks", [])
    n_files = len(set(c.get("filename", "") for c in docs)) if docs else 0
    n_msgs  = len([m for m in st.session_state.get("chat_history", [])
                   if m["role"] == "user"])
    col1, col2 = st.columns(2)
    col1.metric("PDF", f"{n_files} ไฟล์")
    col2.metric("คำถาม", f"{n_msgs} ข้อ")

    if st.button("🗑️ ล้างการสนทนา", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    if docs and st.button("📂 ล้างเอกสาร PDF", use_container_width=True):
        st.session_state.pdf_chunks = []
        if "embed_model" in st.session_state:
            del st.session_state.embed_model
        st.rerun()

    st.divider()
    st.markdown("### 🤖 โมเดล")
    st.markdown("""
    **Typhoon2-8B-Instruct**
    SCB 10X · Thai-English Bilingual
    Context: ~90K tokens
    ผ่าน HF Serverless API (ฟรี)
    """)

# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("# 🤖 Chatbot ความปลอดภัยทางรังสี")
st.caption("Typhoon2 (SCB 10X) · Thai-English · อ้างอิงเอกสาร ปส. + IAEA")

# ── Status bar (top) ──────────────────────────────────────────────────────────
status_bar = st.container()
with status_bar:
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])

    # API Status
    api_status = st.session_state.get("api_status")
    if not hf_token:
        c1.markdown("🔴 **API:** ไม่มี Token")
    elif api_status and api_status[0]:
        c1.markdown("🟢 **API:** เชื่อมต่อแล้ว")
    elif api_status and not api_status[0]:
        c1.markdown("🔴 **API:** เชื่อมต่อไม่ได้")
    else:
        c1.markdown("🟡 **API:** ยังไม่ทดสอบ")

    # PDF Status
    n_chunks = len(st.session_state.get("pdf_chunks", []))
    c2.markdown(f"📄 **PDF:** {n_files} ไฟล์ ({n_chunks} chunks)")

    # Mode (จะเซ็ตด้านล่าง)
    c3.markdown("🔍 **Mode:** เลือกด้านล่าง")

    # Chat count
    c4.markdown(f"💬 **สนทนา:** {n_msgs} คำถาม")

st.divider()

# ── Layout: 2 columns — Chat (ซ้าย) + Upload (ขวา) ───────────────────────────
col_chat, col_upload = st.columns([3, 1])

# ════════════════════════════════════════════════════════════════════════════
with col_upload:
    st.markdown("#### 📄 เอกสาร PDF")

    uploaded_files = st.file_uploader(
        "อัปโหลด PDF",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        if st.button("📥 ประมวลผล", type="primary", use_container_width=True):
            if "pdf_chunks" not in st.session_state:
                st.session_state.pdf_chunks = []
            existing = {c.get("filename") for c in st.session_state.pdf_chunks}
            for f in uploaded_files:
                if f.name in existing:
                    st.info(f"มีอยู่แล้ว: {f.name}")
                    continue
                with st.spinner(f"ประมวลผล {f.name}..."):
                    chunks = extract_pdf_text(f)
                    st.session_state.pdf_chunks.extend(chunks)
                    st.success(f"✅ {f.name}\n({len(chunks)} chunks)")

    # แสดงรายการเอกสาร
    if n_chunks > 0:
        st.markdown("**เอกสารที่โหลดแล้ว:**")
        files_info = {}
        for c in st.session_state.get("pdf_chunks", []):
            fn = c.get("filename", "?")
            files_info[fn] = files_info.get(fn, 0) + 1
        for fn, cnt in files_info.items():
            max_pg = max(c["page"] for c in st.session_state["pdf_chunks"]
                         if c.get("filename") == fn)
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #16a34a44;
                        border-radius:6px;padding:8px 10px;margin:4px 0;font-size:12px;">
                📄 <b>{fn[:25]}{'…' if len(fn)>25 else ''}</b><br>
                <span style="color:#6b7280;">{cnt} chunks · {max_pg} หน้า</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#f8fafc;border:1px dashed #d1d5db;border-radius:8px;
                    padding:14px;text-align:center;font-size:12px;color:#9ca3af;">
            ยังไม่มีเอกสาร<br>อัปโหลด PDF เพื่อถาม-ตอบ
        </div>
        """, unsafe_allow_html=True)

    # เอกสารแนะนำ
    with st.expander("📚 เอกสารแนะนำ"):
        refs = [
            ("ปส.", "แนวทางเขียนแผนป้องกันอันตราย"),
            ("ปส.", "เจ้าหน้าที่ RSO กับการประเมินความปลอดภัย"),
            ("IAEA", "SRS No.47 — Radiation Protection"),
            ("IAEA", "SSR-6 — Safe Transport"),
            ("IAEA", "EPR-D-Values 2006"),
            ("NCRP", "Report No.151 — Shielding"),
        ]
        for src, name in refs:
            color = "#1a4a7a" if src=="ปส." else "#0891b2" if src=="IAEA" else "#7c3aed"
            st.markdown(f"""
            <div style="margin:3px 0;font-size:11px;">
                <span style="background:{color};color:white;padding:1px 6px;
                             border-radius:8px;font-size:10px;">{src}</span>
                <span style="color:#374151;margin-left:4px;">{name}</span>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
with col_chat:
    # Mode selector
    mode = st.radio(
        "โหมด",
        ["🔍 Web Search", "📄 เอกสารที่อัปโหลด", "🔀 Hybrid (แนะนำ)"],
        horizontal=True, label_visibility="collapsed",
    )

    # ── Chat history ──────────────────────────────────────────────────────────
    chat_container = st.container(height=420)
    with chat_container:
        history = st.session_state.get("chat_history", [])
        if not history:
            st.markdown("""
            <div style="text-align:center;color:#9ca3af;padding:40px 20px;font-size:13px;">
                🤖 สวัสดีค่ะ! ฉันเป็น Chatbot ด้านความปลอดภัยทางรังสี<br>
                พิมพ์คำถามด้านล่างได้เลยค่ะ หรือกดที่คำถามแนะนำด้านล่าง
            </div>
            """, unsafe_allow_html=True)
        for msg in history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-user">
                    <b style="color:#1a4a7a;font-size:12px;">คุณ</b><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                src_html = ""
                if msg.get("sources"):
                    badges = "".join(
                        f'<span style="background:#1a4a7a22;color:#1a4a7a;border:1px solid #1a4a7a44;'
                        f'border-radius:10px;padding:2px 8px;font-size:10px;margin:2px;">{s}</span>'
                        for s in msg["sources"]
                    )
                    src_html = f'<div style="margin-top:8px;">{badges}</div>'
                st.markdown(f"""
                <div class="chat-bot">
                    <b style="color:#374151;font-size:12px;">🤖 Typhoon2</b><br>
                    {msg['content'].replace(chr(10),'<br>')}
                    {src_html}
                </div>
                """, unsafe_allow_html=True)

    # ── Input area ────────────────────────────────────────────────────────────
    with st.container():
        inp_col, btn_col = st.columns([5, 1])
        with inp_col:
            user_input = st.text_area(
                "คำถาม",
                value=st.session_state.pop("pending_q", ""),
                placeholder="พิมพ์คำถามเกี่ยวกับความปลอดภัยทางรังสีได้เลยค่ะ...",
                height=72, label_visibility="collapsed", key="chat_input",
            )
        with btn_col:
            st.markdown("<br>", unsafe_allow_html=True)
            send = st.button("📤 ส่ง", type="primary", use_container_width=True)

    # ── Processing ────────────────────────────────────────────────────────────
    if send and user_input.strip():
        if not hf_token:
            st.error("❌ กรุณาใส่ HF Token ใน sidebar ก่อนค่ะ")
            st.stop()

        question = user_input.strip()
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append({"role": "user", "content": question})

        context_parts = []
        sources_used = []

        use_web  = "Web" in mode or "Hybrid" in mode
        use_docs = "เอกสาร" in mode or "Hybrid" in mode
        has_docs = len(st.session_state.get("pdf_chunks", [])) > 0

        # ── Step 1: ค้นหาข้อมูล ──────────────────────────────────────────────
        prog = st.progress(0, text="🔍 กำลังค้นหาข้อมูล...")

        if use_docs and has_docs:
            prog.progress(20, text="📄 กำลังค้นหาในเอกสาร PDF...")
            relevant = search_chunks(question, st.session_state["pdf_chunks"], top_k=5)
            ctx = "\n\n".join(
                f"[เอกสาร: {c['filename']} หน้า {c['page']}]\n{c['text']}"
                for c in relevant if c.get("score", 0) > 0
            )
            if ctx:
                context_parts.append(f"=== ข้อมูลจากเอกสารที่อัปโหลด ===\n{ctx}")
                sources_used.extend([f"📄 {fn}" for fn in
                                     list({c['filename'] for c in relevant})])
        elif use_docs and not has_docs and "เอกสาร" in mode:
            st.warning("⚠️ ยังไม่มี PDF — อัปโหลดในช่องด้านขวาก่อนค่ะ")

        if use_web:
            prog.progress(50, text="🌐 กำลังค้นหาจากอินเทอร์เน็ต...")
            results = web_search(f"radiation safety {question} IAEA OAP Thailand", 4)
            ctx_web = "\n\n".join(
                f"[แหล่ง: {r['title']}]\n{r['snippet']}"
                for r in results if r.get("snippet") and r.get("title") != "Error"
            )
            if ctx_web:
                context_parts.append(f"=== ข้อมูลจากการค้นหาออนไลน์ ===\n{ctx_web}")
                sources_used.append("🌐 Web Search")

        # ── Step 2: เรียก Typhoon2 ────────────────────────────────────────────
        prog.progress(75, text="🤖 Typhoon2 กำลังคิดคำตอบ...")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in st.session_state.chat_history[-12:][:-1]:
            messages.append({"role": h["role"], "content": h["content"]})

        context_str = "\n\n".join(context_parts)
        if context_str:
            user_msg = f"คำถาม: {question}\n\nข้อมูลอ้างอิง:\n{context_str}\n\nกรุณาตอบโดยอ้างอิงแหล่งที่มาด้วยค่ะ"
        else:
            user_msg = question
        messages.append({"role": "user", "content": user_msg})

        answer = call_typhoon2(messages, hf_token)

        prog.progress(100, text="✅ ได้รับคำตอบแล้ว!")
        prog.empty()

        if not sources_used:
            sources_used.append("🧠 Typhoon2")

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "sources": sources_used,
        })
        st.rerun()

    # ── Suggested questions (ล่างสุด) ────────────────────────────────────────
    st.divider()
    st.markdown("##### 💡 คำถามที่น่าสนใจ")
    sug_cols = st.columns(2)
    for i, q in enumerate(SUGGESTIONS):
        if sug_cols[i % 2].button(q, key=f"sug_{i}", use_container_width=True):
            st.session_state["pending_q"] = q
            st.rerun()

    st.markdown("""
    <div style="font-size:11px;color:#9ca3af;margin-top:8px;text-align:center;">
        Typhoon2 ผ่าน HF Serverless API (ฟรี ~few hundred req/hr) |
        คำตอบเป็นข้อมูลเบื้องต้น กรุณาตรวจสอบกับ ปส. สำหรับการใช้งานจริง
    </div>
    """, unsafe_allow_html=True)
