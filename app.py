"""
🏠 หน้าหลัก — ระบบจัดการเอกสารความปลอดภัยทางรังสี
"""
import streamlit as st

st.set_page_config(
    page_title="ระบบเอกสารความปลอดภัยทางรังสี",
    page_icon="☢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif !important; }
.card {
    background: white; border-radius: 14px; padding: 24px;
    border: 1.5px solid #e5e7eb; margin-bottom: 12px;
    transition: box-shadow 0.2s;
}
.card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 12px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background: linear-gradient(135deg, #0f2d4a, #1a4a7a, #2d7dd2);
            padding: 32px; border-radius: 16px; color: white; margin-bottom: 28px;">
    <h1 style="margin:0; font-size:28px;">☢️ ระบบจัดการเอกสารความปลอดภัยทางรังสี</h1>
    <p style="margin:8px 0 0; opacity:0.85; font-size:15px;">
        สำหรับเจ้าหน้าที่ความปลอดภัยทางรังสี (RSO) และนักรังสีการแพทย์<br>
        อ้างอิงตามประกาศสำนักงานปรมาณูเพื่อสันติ (ปส.) และ IAEA SSR-6
    </p>
</div>
""", unsafe_allow_html=True)

# ── Page cards ────────────────────────────────────────────────────────────────
pages = [
    {
        "icon": "🔍",
        "title": "จำแนกประเภทวัสดุกัมมันตรังสี",
        "desc": "จำแนกประเภท 1–5 จากตารางการใช้ประโยชน์ หรือคำนวณ A/D ratio จากตารางค่า D ของ ปส.",
        "features": ["ตารางที่ 1: จำแนกจากการใช้งาน", "ตารางที่ 2: ค่า D ทุก isotope", "คำนวณ A/D หลายแหล่งพร้อมกัน (Sum A/D)"],
        "color": "#1a4a7a",
        "page": "pages/1_🔍_จำแนกประเภทวัสดุ.py",
        "status": "พร้อมใช้งาน",
        "status_color": "#16a34a",
    },
    {
        "icon": "🚛",
        "title": "แผนการขนส่งวัสดุกัมมันตรังสี",
        "desc": "ร่างแผนขนส่งตาม IAEA SSR-6 คำนวณ Transport Index และ Category พร้อม export Word",
        "features": ["คำนวณ TI และ Category อัตโนมัติ", "AI ร่างแผนภาษาไทยพร้อม submit ปส.", "Export Word (.docx)"],
        "color": "#ea580c",
        "page": "pages/2_🚛_แผนขนส่ง.py",
        "status": "พร้อมใช้งาน",
        "status_color": "#16a34a",
    },
    {
        "icon": "🛡️",
        "title": "แผนป้องกันอันตรายจากรังสี",
        "desc": "คำนวณกำบังรังสี Controlled/Supervised Area และ Dose ผู้ปฏิบัติงาน พร้อมร่างแผน",
        "features": ["คำนวณความหนากำบังรังสี", "กำหนด Controlled/Supervised Area", "AI ร่างแผนป้องกันอันตราย"],
        "color": "#7c3aed",
        "page": "pages/3_🛡️_แผนป้องกันอันตราย.py",
        "status": "พร้อมใช้งาน",
        "status_color": "#16a34a",
    },
    {
        "icon": "🔒",
        "title": "แผนรักษาความมั่นคงปลอดภัย",
        "desc": "ร่างแผนรักษาความมั่นคงปลอดภัยทางรังสีตามกฎกระทรวงความมั่นคงปลอดภัยทางรังสี พ.ศ. 2561",
        "features": ["ครอบคลุมทุกหัวข้อตามกฎกระทรวง", "AI ร่างแผนความมั่นคง", "Export Word (.docx)"],
        "color": "#0891b2",
        "page": "pages/4_🔒_แผนความมั่นคง.py",
        "status": "พร้อมใช้งาน",
        "status_color": "#16a34a",
    },
    {
        "icon": "🤖",
        "title": "Chatbot ถาม-ตอบเอกสาร ปส.",
        "desc": "ถามตอบจากคู่มือ ปส. แนวปฏิบัติ และกฎหมายความปลอดภัยทางรังสีได้โดยตรง",
        "features": ["อัปโหลด PDF เอกสาร ปส.", "ถามตอบภาษาไทย", "อ้างอิงหน้าและแหล่งที่มา"],
        "color": "#be185d",
        "page": "pages/5_🤖_Chatbot.py",
        "status": "พร้อมใช้งาน",
        "status_color": "#16a34a",
    },
]

cols = st.columns(2)
for i, p in enumerate(pages):
    with cols[i % 2]:
        features_html = "".join(
            f'<li style="font-size:13px; color:#374151; margin:3px 0;">✓ {f}</li>'
            for f in p["features"]
        )
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                <span style="font-size:28px;">{p['icon']}</span>
                <span class="badge" style="background:{p['status_color']}22; color:{p['status_color']};">
                    {p['status']}
                </span>
            </div>
            <h3 style="margin:0 0 6px; color:{p['color']}; font-size:16px;">{p['title']}</h3>
            <p style="font-size:13px; color:#6b7280; margin:0 0 10px;">{p['desc']}</p>
            <ul style="margin:0; padding-left:4px; list-style:none;">{features_html}</ul>
        </div>
        """, unsafe_allow_html=True)

# ── Quick reference ────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📞 หน่วยงานฉุกเฉินทางรังสี")
cols2 = st.columns(4)
contacts = [
    ("☢️", "สำนักงานปรมาณูเพื่อสันติ (ปส.)", "02-596-7600", "นอกเวลา: 089-200-6243"),
    ("🚒", "กรมป้องกันและบรรเทาสาธารณภัย", "1784", "ตลอด 24 ชั่วโมง"),
    ("🏥", "ศูนย์นเรนทร กระทรวงสาธารณสุข", "1669", "กรณีมีผู้บาดเจ็บ"),
    ("🚨", "สำนักงานตำรวจแห่งชาติ", "191", "กรณีเกี่ยวข้องก่อการร้าย"),
]
for col, (icon, name, phone, note) in zip(cols2, contacts):
    with col:
        st.markdown(f"""
        <div style="background:#f8fafc; border-radius:10px; padding:14px; border:1px solid #e2e8f0; text-align:center;">
            <div style="font-size:24px;">{icon}</div>
            <p style="font-size:12px; color:#374151; font-weight:600; margin:6px 0 4px;">{name}</p>
            <p style="font-size:20px; font-weight:700; color:#1a4a7a; margin:0;">{phone}</p>
            <p style="font-size:11px; color:#6b7280; margin:4px 0 0;">{note}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<br>
<p style="text-align:center; font-size:12px; color:#9ca3af;">
อ้างอิง: ประกาศ ปส. ตารางที่ 1 และ 2 | กฎกระทรวงความมั่นคงปลอดภัยทางรังสี พ.ศ. 2561 | IAEA SSR-6
</p>
""", unsafe_allow_html=True)
