"""
🤖 Page 5 — Chatbot ถาม-ตอบความปลอดภัยทางรังสี
โมเดล: Typhoon2 (scb10x/llama3.1-typhoon2-8b-instruct) ผ่าน HF Serverless API
RAG แบบ Hybrid:
  Mode 1 — Web Search: ค้นหาข้อมูล IAEA/ปส. จากอินเทอร์เน็ต
  Mode 2 — PDF RAG: อัปโหลดเอกสารแล้วถาม-ตอบจากเนื้อหาในไฟล์
Embedding: paraphrase-multilingual-MiniLM-L12-v2 (Thai + English)
"""
import streamlit as st
import requests
import json
import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="Chatbot ถาม-ตอบความปลอดภัยทางรังสี",
    page_icon="🤖", layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif !important; }
.chat-user {
    background: #eff6ff; border-radius: 12px 12px 4px 12px;
    padding: 12px 16px; margin: 6px 0; max-width: 85%; margin-left: auto;
    border: 1px solid #bfdbfe;
}
.chat-bot {
    background: #f8fafc; border-radius: 12px 12px 12px 4px;
    padding: 12px 16px; margin: 6px 0; max-width: 90%;
    border: 1px solid #e2e8f0; border-left: 4px solid #1a4a7a;
}
.source-badge {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 11px; font-weight: 600; margin: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_ID   = "scb10x/llama3.1-typhoon2-8b-instruct"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
HF_API_BASE = "https://api-inference.huggingface.co/models"
HF_CHAT_URL = f"https://api-inference.huggingface.co/v1/chat/completions"

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

# ── Helper: call Typhoon2 via HF Serverless API ───────────────────────────────
def call_typhoon2(messages: list, hf_token: str, max_tokens: int = 1000) -> str:
    """เรียก Typhoon2 ผ่าน HF Serverless API (chat completion endpoint)"""
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
        resp = requests.post(HF_CHAT_URL, headers=headers,
                             json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        elif resp.status_code == 503:
            return "⏳ โมเดลกำลัง warm up อยู่ค่ะ กรุณารอสักครู่แล้วลองใหม่ (ประมาณ 20-30 วินาที)"
        elif resp.status_code == 401:
            return "❌ HF Token ไม่ถูกต้อง กรุณาตรวจสอบ Token ใน sidebar ค่ะ"
        elif resp.status_code == 429:
            return "⚠️ Rate limit เกิน กรุณารอสักครู่แล้วลองใหม่ค่ะ (HF Free Tier ~few hundred req/hr)"
        else:
            return f"❌ Error {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.Timeout:
        return "⏰ Request timeout — โมเดลใช้เวลานานเกินไป กรุณาลองใหม่ค่ะ"
    except Exception as e:
        return f"❌ เกิดข้อผิดพลาด: {str(e)}"


# ── Helper: Web Search via DuckDuckGo (no API key needed) ────────────────────
def web_search(query: str, num_results: int = 5) -> list[dict]:
    """ค้นหาข้อมูลผ่าน DuckDuckGo Instant Answer API (ฟรี ไม่ต้อง key)"""
    try:
        # DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        results = []

        # Abstract (คำตอบหลัก)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "DuckDuckGo"),
                "snippet": data["Abstract"],
                "url": data.get("AbstractURL", ""),
                "source": "DuckDuckGo Instant Answer",
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                    "snippet": topic["Text"],
                    "url": topic.get("FirstURL", ""),
                    "source": "DuckDuckGo",
                })

        return results[:num_results]
    except Exception as e:
        return [{"title": "Error", "snippet": f"ค้นหาไม่สำเร็จ: {e}", "url": "", "source": "error"}]


# ── Helper: PDF processing (simple chunking, no vector DB needed for small docs)
def extract_pdf_text(uploaded_file) -> list[dict]:
    """Extract text จาก PDF แบ่งเป็น chunks พร้อม metadata"""
    try:
        import pypdf
        import io

        reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
        chunks = []
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue
            # แบ่ง chunk ทุก ~500 chars (ประมาณ paragraph)
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
            if not paragraphs:
                paragraphs = [text[i:i+500] for i in range(0, len(text), 500)]
            for para in paragraphs:
                chunks.append({
                    "text": para,
                    "page": page_num + 1,
                    "filename": uploaded_file.name,
                })
        return chunks
    except ImportError:
        st.error("กรุณาติดตั้ง pypdf: `pip install pypdf`")
        return []
    except Exception as e:
        st.error(f"อ่าน PDF ไม่สำเร็จ: {e}")
        return []


def simple_search_chunks(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """
    Simple keyword + TF-IDF like search ใน chunks
    ถ้าติดตั้ง sentence-transformers ได้จะใช้ semantic search
    ถ้าไม่ได้จะ fallback ไป keyword matching
    """
    try:
        from sentence_transformers import SentenceTransformer, util
        import torch

        # โหลด model ครั้งเดียว cache ใน session
        if "embed_model" not in st.session_state:
            with st.spinner("โหลด embedding model..."):
                st.session_state.embed_model = SentenceTransformer(EMBED_MODEL)

        model = st.session_state.embed_model
        texts = [c["text"] for c in chunks]

        q_emb = model.encode(query, convert_to_tensor=True)
        c_embs = model.encode(texts, convert_to_tensor=True)
        scores = util.cos_sim(q_emb, c_embs)[0]
        top_indices = scores.topk(min(top_k, len(chunks))).indices.tolist()

        return [
            {**chunks[i], "score": float(scores[i])}
            for i in top_indices
        ]

    except Exception:
        # Fallback: keyword matching
        query_words = set(query.lower().split())
        scored = []
        for chunk in chunks:
            text_lower = chunk["text"].lower()
            score = sum(1 for w in query_words if w in text_lower)
            if score > 0:
                scored.append({**chunk, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 การตั้งค่า")
    hf_token = st.text_input(
        "Hugging Face Token",
        type="password",
        help="สร้างได้ที่ huggingface.co/settings/tokens — ต้องมี permission: Inference API"
    )
    if hf_token:
        st.success("✅ Token พร้อมใช้งาน")
    else:
        st.warning("⚠️ กรุณาใส่ HF Token")
        st.markdown("""
        **วิธีสร้าง HF Token ฟรี:**
        1. ไปที่ [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
        2. กด **New token**
        3. เลือก Permission: **Inference API** (Read)
        4. Copy มาวางที่นี่
        """)

    st.divider()
    st.markdown("### 🤖 โมเดลที่ใช้")
    st.markdown("""
    **Typhoon2-8B-Instruct**
    - พัฒนาโดย SCB 10X
    - Thai-English bilingual
    - บน Llama 3.1 architecture
    - ผ่าน HF Serverless API (ฟรี)
    """)

    st.divider()
    st.markdown("### 📊 สถานะ Session")
    docs = st.session_state.get("pdf_chunks", [])
    n_docs = len(set(c.get("filename","") for c in docs)) if docs else 0
    st.metric("เอกสาร PDF", f"{n_docs} ไฟล์")
    st.metric("Total chunks", len(docs))
    if docs and st.button("🗑️ ล้างเอกสารทั้งหมด"):
        st.session_state.pdf_chunks = []
        st.rerun()

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("# 🤖 Chatbot ถาม-ตอบความปลอดภัยทางรังสี")
st.caption(
    "ขับเคลื่อนด้วย Typhoon2 (SCB 10X) | Thai-English Bilingual | "
    "อ้างอิงเอกสาร ปส. + มาตรฐาน IAEA"
)

tab_chat, tab_docs = st.tabs(["💬 ถาม-ตอบ", "📄 จัดการเอกสาร PDF"])

# ════════════════════════════════════════════════════════════════════════════
with tab_docs:
    st.subheader("📄 อัปโหลดเอกสารเพื่อถาม-ตอบ")
    st.caption("รองรับ PDF ทั้งภาษาไทยและอังกฤษ — เช่น คู่มือ ปส., IAEA Safety Reports, NCRP")

    col_up, col_list = st.columns([1, 1])

    with col_up:
        uploaded_files = st.file_uploader(
            "เลือกไฟล์ PDF",
            type=["pdf"],
            accept_multiple_files=True,
            help="อัปโหลดได้หลายไฟล์พร้อมกัน"
        )

        if uploaded_files:
            if st.button("📥 ประมวลผลเอกสาร", type="primary"):
                if "pdf_chunks" not in st.session_state:
                    st.session_state.pdf_chunks = []

                existing_files = {c.get("filename") for c in st.session_state.pdf_chunks}
                new_count = 0

                for f in uploaded_files:
                    if f.name in existing_files:
                        st.info(f"⏭️ {f.name} มีอยู่แล้ว")
                        continue
                    with st.spinner(f"ประมวลผล {f.name}..."):
                        chunks = extract_pdf_text(f)
                        st.session_state.pdf_chunks.extend(chunks)
                        new_count += len(chunks)
                        st.success(f"✅ {f.name} — {len(chunks)} chunks")

                if new_count > 0:
                    st.success(f"🎉 เพิ่ม {new_count} chunks ทั้งหมด พร้อมถามตอบแล้วค่ะ")

    with col_list:
        chunks = st.session_state.get("pdf_chunks", [])
        if chunks:
            st.markdown("**เอกสารที่โหลดแล้ว:**")
            files_info = {}
            for c in chunks:
                fn = c.get("filename", "unknown")
                files_info[fn] = files_info.get(fn, 0) + 1

            for fn, count in files_info.items():
                max_page = max(c["page"] for c in chunks if c.get("filename") == fn)
                st.markdown(f"""
                <div style="background:#f0fdf4;border:1px solid #16a34a;border-radius:8px;
                            padding:10px 14px;margin:6px 0;">
                    <b>📄 {fn}</b><br>
                    <small style="color:#6b7280;">{count} chunks | {max_page} หน้า</small>
                </div>
                """, unsafe_allow_html=True)

            # Quick preview
            with st.expander("🔍 ดูตัวอย่าง chunk"):
                sample = chunks[0]
                st.markdown(f"**ไฟล์:** {sample['filename']} | **หน้า:** {sample['page']}")
                st.text(sample["text"][:300] + "...")
        else:
            st.info("ยังไม่มีเอกสาร — อัปโหลด PDF เพื่อเริ่มต้นค่ะ")

    # Quick reference docs
    st.divider()
    st.markdown("#### 📚 เอกสารอ้างอิงที่แนะนำให้อัปโหลด")
    ref_docs = [
        ("ปส.", "แนวทางการเขียนแผนป้องกันอันตรายจากรังสี"),
        ("ปส.", "คู่มือการดำเนินงานรับแจ้งเหตุฉุกเฉินทางนิวเคลียร์และรังสี"),
        ("ปส.", "เจ้าหน้าที่ความปลอดภัยทางรังสีกับการประเมินความปลอดภัย"),
        ("IAEA", "Safety Reports Series No.47 — Radiation Protection in Radiotherapy"),
        ("IAEA", "IAEA-EPR-D-Values 2006 — Dangerous Quantities"),
        ("IAEA", "SSR-6 — Regulations for Safe Transport of Radioactive Material"),
        ("NCRP", "Report No.151 — Structural Shielding Design"),
    ]
    cols = st.columns(2)
    for i, (src, name) in enumerate(ref_docs):
        color = "#1a4a7a" if src == "ปส." else "#0891b2" if src == "IAEA" else "#7c3aed"
        bg = "#eff6ff" if src == "ปส." else "#ecfeff" if src == "IAEA" else "#f5f3ff"
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {color}44;border-radius:6px;
                        padding:8px 12px;margin:4px 0;">
                <span style="background:{color};color:white;padding:2px 7px;
                             border-radius:10px;font-size:11px;font-weight:700;">{src}</span>
                <span style="font-size:12px;color:#374151;margin-left:6px;">{name}</span>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
with tab_chat:

    # Mode selector
    mode = st.radio(
        "โหมดการค้นหาข้อมูล",
        [
            "🔍 Web Search — ค้นหาข้อมูลทั่วไปจาก IAEA/ปส. จากอินเทอร์เน็ต",
            "📄 เอกสารที่อัปโหลด — ถาม-ตอบจากไฟล์ PDF ที่อัปโหลดไว้",
            "🔀 Hybrid — ใช้ทั้งสองอย่าง (แนะนำ)",
        ],
        horizontal=False,
        label_visibility="collapsed",
    )

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Show suggested questions
    if not st.session_state.chat_history:
        st.markdown("#### 💡 คำถามที่น่าสนใจ")
        suggestions = [
            "วัสดุกัมมันตรังสีประเภท 2 มีมาตรการความมั่นคงปลอดภัยอะไรบ้าง?",
            "ขีดจำกัดปริมาณรังสีสำหรับผู้ปฏิบัติงานทางรังสีตามกฎหมายไทยคือเท่าไหร่?",
            "Transport Index คืออะไร คำนวณอย่างไร?",
            "D-value ของ Ir-192 คือเท่าไหร่ และใช้ทำอะไร?",
            "Controlled Area และ Supervised Area แตกต่างกันอย่างไร?",
            "กรณีวัสดุกัมมันตรังสีสูญหายต้องแจ้งหน่วยงานอะไรบ้าง?",
            "ALARA principle คืออะไร ประยุกต์ใช้อย่างไรในทางปฏิบัติ?",
            "HVL ของตะกั่วสำหรับ Co-60 คือเท่าไหร่?",
        ]
        cols = st.columns(2)
        for i, q in enumerate(suggestions):
            if cols[i % 2].button(f"💬 {q}", key=f"sug_{i}", use_container_width=True):
                st.session_state.pending_question = q
                st.rerun()

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-user">
                <b style="color:#1a4a7a;">คุณ:</b><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Parse sources if embedded
            content = msg["content"]
            sources_html = ""
            if msg.get("sources"):
                badges = []
                for src in msg["sources"]:
                    color = "#1a4a7a" if "ปส" in src or "OAP" in src else "#0891b2"
                    badges.append(
                        f'<span class="source-badge" style="background:{color}22;'
                        f'color:{color};border:1px solid {color}44;">{src}</span>'
                    )
                sources_html = f'<div style="margin-top:8px;">{"".join(badges)}</div>'

            st.markdown(f"""
            <div class="chat-bot">
                <b style="color:#374151;">🤖 Typhoon2:</b><br>
                {content.replace(chr(10), '<br>')}
                {sources_html}
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Chat input
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_area(
            "ถามคำถาม",
            value=st.session_state.pop("pending_question", ""),
            placeholder="พิมพ์คำถามเกี่ยวกับความปลอดภัยทางรังสีได้เลยค่ะ...\nสามารถถามทั้งภาษาไทยและอังกฤษ",
            height=80, label_visibility="collapsed",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        send = st.button("📤 ส่ง", type="primary", use_container_width=True)

    col_clear, col_info = st.columns([1, 3])
    with col_clear:
        if st.button("🗑️ ล้างการสนทนา", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    with col_info:
        chunks_count = len(st.session_state.get("pdf_chunks", []))
        if chunks_count:
            st.caption(f"📄 มีเอกสาร {chunks_count} chunks พร้อมใช้งาน")

    # Process question
    if send and user_input.strip():
        if not hf_token:
            st.error("❌ กรุณาใส่ HF Token ใน sidebar ก่อนค่ะ")
            st.stop()

        question = user_input.strip()
        st.session_state.chat_history.append({"role": "user", "content": question})

        context_parts = []
        sources_used = []

        use_web    = "Web Search" in mode or "Hybrid" in mode
        use_docs   = "เอกสาร" in mode or "Hybrid" in mode
        has_docs   = len(st.session_state.get("pdf_chunks", [])) > 0

        with st.spinner("🔍 กำลังค้นหาข้อมูล..."):

            # ── Mode: PDF RAG ────────────────────────────────────────────────
            if use_docs and has_docs:
                relevant = simple_search_chunks(
                    question,
                    st.session_state["pdf_chunks"],
                    top_k=5
                )
                if relevant:
                    doc_context = "\n\n".join([
                        f"[เอกสาร: {c['filename']} หน้า {c['page']}]\n{c['text']}"
                        for c in relevant
                        if c.get("score", 0) > 0
                    ])
                    if doc_context:
                        context_parts.append(
                            f"=== ข้อมูลจากเอกสารที่อัปโหลด ===\n{doc_context}"
                        )
                        unique_files = list({c["filename"] for c in relevant})
                        sources_used.extend([f"📄 {fn}" for fn in unique_files])

            elif use_docs and not has_docs and "เอกสาร" in mode:
                st.warning("⚠️ ยังไม่มีเอกสาร PDF — กรุณาอัปโหลดในแท็บ 'จัดการเอกสาร PDF' ก่อนค่ะ")

            # ── Mode: Web Search ─────────────────────────────────────────────
            if use_web:
                # สร้าง query ที่เหมาะสม
                search_q = f"radiation safety {question} IAEA OAP Thailand"
                results  = web_search(search_q, num_results=4)

                web_context = "\n\n".join([
                    f"[แหล่ง: {r['title']}]\n{r['snippet']}"
                    for r in results
                    if r.get("snippet") and r.get("title") != "Error"
                ])
                if web_context:
                    context_parts.append(
                        f"=== ข้อมูลจากการค้นหาออนไลน์ ===\n{web_context}"
                    )
                    sources_used.append("🌐 Web Search")

        # ── Build prompt ─────────────────────────────────────────────────────
        with st.spinner("🤖 Typhoon2 กำลังตอบ..."):

            # สร้าง context string
            context_str = "\n\n".join(context_parts) if context_parts else ""

            # Build messages
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # ใส่ประวัติการสนทนา (สูงสุด 6 รอบล่าสุด)
            history = st.session_state.chat_history[:-1]  # exclude current question
            for h in history[-12:]:  # 6 รอบ = 12 messages
                messages.append({"role": h["role"], "content": h["content"]})

            # User message พร้อม context
            if context_str:
                user_msg = f"""คำถาม: {question}

ข้อมูลอ้างอิงที่ค้นพบ:
{context_str}

กรุณาตอบคำถามโดยอ้างอิงจากข้อมูลด้านบน และระบุว่าข้อมูลมาจากแหล่งใด"""
            else:
                user_msg = question

            messages.append({"role": "user", "content": user_msg})

            # Call Typhoon2
            answer = call_typhoon2(messages, hf_token, max_tokens=800)

            # เพิ่มใน history
            if not sources_used:
                sources_used.append("🧠 Typhoon2 (ความรู้โดยตรง)")

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer,
                "sources": sources_used,
            })

        st.rerun()

    # Info footer
    st.markdown("""
    <div style="background:#f8fafc;border-radius:8px;padding:10px 14px;
                margin-top:12px;font-size:12px;color:#6b7280;">
        <b>หมายเหตุ:</b> Typhoon2 ให้บริการผ่าน HF Serverless API ฟรี (~few hundred req/hr) |
        ถ้า timeout ให้รอ 20-30 วินาทีแล้วลองใหม่ |
        คำตอบเป็นข้อมูลเบื้องต้น กรุณาตรวจสอบกับ ปส. สำหรับการใช้งานจริง
    </div>
    """, unsafe_allow_html=True)
