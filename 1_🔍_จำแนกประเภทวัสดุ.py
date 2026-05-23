"""
🔍 Page 1 — จำแนกประเภทวัสดุกัมมันตรังสี
ขั้นที่ 1: ค้นหาจากตารางการใช้ประโยชน์
ขั้นที่ 2: คำนวณ A/D ratio จากตารางค่า D
รองรับหลาย isotope พร้อมกัน (Sum A/D)
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import (D_VALUES_TBQ, USE_TYPE_CATEGORY, ISOTOPE_INFO,
                  UNIT_TO_TBQ, CATEGORY_COLORS, CATEGORY_BG,
                  classify_material, CATEGORY_THRESHOLDS)

st.set_page_config(page_title="จำแนกประเภทวัสดุกัมมันตรังสี", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔍 จำแนกประเภทวัสดุกัมมันตรังสี")
st.caption("อ้างอิงตารางที่ 1 และตารางที่ 2 จากประกาศสำนักงานปรมาณูเพื่อสันติ")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🧮 จำแนกประเภท (Single / Multiple)",
    "📋 ตารางค่า D อ้างอิง",
    "📊 ตารางการจำแนกประเภท",
])

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("กรอกข้อมูลวัสดุกัมมันตรังสี")

    mode = st.radio("โหมดการใช้งาน", ["แหล่งเดียว", "หลายแหล่ง (คำนวณ Sum A/D)"],
                    horizontal=True)

    isotope_list = list(D_VALUES_TBQ.keys())
    use_list = ["— ไม่พบในตาราง / ให้คำนวณ A/D —"] + list(USE_TYPE_CATEGORY.keys())
    unit_list = list(UNIT_TO_TBQ.keys())

    # ── Single source ─────────────────────────────────────────────────────────
    if mode == "แหล่งเดียว":
        c1, c2, c3, c4 = st.columns([2, 1.5, 1, 2])
        with c1:
            isotope = st.selectbox("ชนิดนิวไคลด์", isotope_list, index=isotope_list.index("Ir-192"))
        with c2:
            activity = st.number_input("ค่ากัมมันตภาพ", min_value=0.0, value=5.5, format="%.4f")
        with c3:
            unit = st.selectbox("หน่วย", unit_list, index=unit_list.index("Ci"))
        with c4:
            use_type = st.selectbox("การใช้ประโยชน์", use_list)

        # แสดงข้อมูล isotope
        if isotope in ISOTOPE_INFO:
            info = ISOTOPE_INFO[isotope]
            d_val = D_VALUES_TBQ.get(isotope, "-")
            st.info(f"**{isotope}** — ครึ่งชีวิต: {info['halfLife']} | UN: {info['unNo']} | "
                    f"A₁: {info['a1']} TBq | A₂: {info['a2']} TBq | **D: {d_val} TBq**")

        if st.button("🔍 จำแนกประเภท", type="primary"):
            activity_tbq = activity * UNIT_TO_TBQ.get(unit, 1)
            ut = use_type if use_type != "— ไม่พบในตาราง / ให้คำนวณ A/D —" else ""
            result = classify_material(isotope, activity_tbq, ut)

            if result["category"] is None:
                st.error("❌ " + result["detail"])
            else:
                cat = result["category"]
                color = CATEGORY_COLORS[cat]
                bg = CATEGORY_BG[cat]

                st.markdown(f"""
                <div style="background:{bg}; border:2px solid {color}; border-radius:14px; padding:20px; margin-top:16px;">
                    <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
                        <div style="background:{color}; color:white; border-radius:10px;
                                    padding:10px 24px; font-size:22px; font-weight:700;">
                            ประเภท {cat}
                        </div>
                        <div>
                            <p style="margin:0; font-size:14px; font-weight:700; color:{color};">
                                เกณฑ์: {result['threshold']}
                            </p>
                            <p style="margin:4px 0 0; font-size:12px; color:#6b7280;">
                                วิธี: {'จำแนกจากตารางการใช้ประโยชน์' if result['method']=='use_table' else 'คำนวณจาก A/D ratio'}
                            </p>
                        </div>
                    </div>
                    <hr style="border-color:{color}44; margin:14px 0;">
                    <p style="margin:0; font-size:13px; color:#374151;">{result['detail']}</p>
                </div>
                """, unsafe_allow_html=True)

                if result["method"] == "ad_ratio" and result["ad_ratio"]:
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Activity (TBq)", f"{result['activity_tbq']:.3e}")
                    m2.metric("D Value (TBq)", f"{result['d_value']:.2e}")
                    m3.metric("A/D Ratio", f"{result['ad_ratio']:.4f}")
                    m4.metric("ประเภท", f"ประเภท {cat}")

    # ── Multiple sources (Sum A/D) ─────────────────────────────────────────────
    else:
        st.markdown("**เพิ่มวัสดุกัมมันตรังสีแต่ละชนิด** (ระบบจะคำนวณ Sum A/D รวมให้)")

        if "sources" not in st.session_state:
            st.session_state.sources = [
                {"isotope": "Am-241/Be", "activity": 5.5,  "unit": "Ci"},
                {"isotope": "Cf-252",    "activity": 0.063, "unit": "Ci"},
                {"isotope": "Cs-137",    "activity": 0.12,  "unit": "Ci"},
            ]

        # ── แสดงแถวกรอกข้อมูล ─────────────────────────────────────────────
        sources_updated = []
        for idx, src in enumerate(st.session_state.sources):
            cols = st.columns([2.5, 1.5, 1, 0.5])
            with cols[0]:
                iso = st.selectbox(f"Isotope #{idx+1}", isotope_list,
                                   index=isotope_list.index(src["isotope"])
                                   if src["isotope"] in isotope_list else 0,
                                   key=f"iso_{idx}")
            with cols[1]:
                act = st.number_input(f"Activity #{idx+1}", min_value=0.0,
                                      value=float(src["activity"]), format="%.4f",
                                      key=f"act_{idx}")
            with cols[2]:
                unt = st.selectbox(f"Unit #{idx+1}", unit_list,
                                   index=unit_list.index(src["unit"])
                                   if src["unit"] in unit_list else 0,
                                   key=f"unt_{idx}")
            with cols[3]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{idx}", help="ลบแถวนี้"):
                    continue
            sources_updated.append({"isotope": iso, "activity": act, "unit": unt})

        st.session_state.sources = sources_updated

        c_add, c_calc = st.columns([1, 3])
        with c_add:
            if st.button("➕ เพิ่มแหล่งกัมมันตรังสี"):
                st.session_state.sources.append({"isotope": "Co-60", "activity": 1.0, "unit": "Ci"})
                st.rerun()

        with c_calc:
            if st.button("🧮 คำนวณ Sum A/D และจำแนกประเภท", type="primary"):
                rows = []
                sum_ad = 0.0
                for src in st.session_state.sources:
                    activity_tbq = src["activity"] * UNIT_TO_TBQ.get(src["unit"], 1)
                    d_val = D_VALUES_TBQ.get(src["isotope"])
                    if d_val and activity_tbq > 0:
                        ad = activity_tbq / d_val
                        sum_ad += ad
                        rows.append({
                            "Isotope": src["isotope"],
                            "Activity": f"{src['activity']} {src['unit']}",
                            "Activity (TBq)": f"{activity_tbq:.3e}",
                            "D Value (TBq)": f"{d_val:.2e}",
                            "A/D": f"{ad:.4f}",
                        })
                    else:
                        rows.append({
                            "Isotope": src["isotope"],
                            "Activity": f"{src['activity']} {src['unit']}",
                            "Activity (TBq)": "—",
                            "D Value (TBq)": "ไม่พบค่า D",
                            "A/D": "—",
                        })

                # แสดงตาราง
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                # Sum A/D result
                if sum_ad > 0:
                    cat = classify_material("", 0, "")["category"]
                    # classify by sum
                    from utils.data import classify_by_ad
                    cat = classify_by_ad(sum_ad)
                    color = CATEGORY_COLORS[cat]
                    bg = CATEGORY_BG[cat]
                    threshold = CATEGORY_THRESHOLDS[cat][2]

                    st.markdown(f"""
                    <div style="background:{bg}; border:2px solid {color}; border-radius:12px; padding:18px; margin-top:12px;">
                        <h3 style="margin:0 0 8px; color:{color};">Σ A/D รวม = {sum_ad:.4f}</h3>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <div style="background:{color}; color:white; border-radius:8px;
                                        padding:8px 20px; font-size:20px; font-weight:700;">
                                ประเภท {cat}
                            </div>
                            <p style="margin:0; color:{color}; font-weight:600;">เกณฑ์: {threshold}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("ตารางที่ 2 — ค่า D ของวัสดุกัมมันตรังสีแต่ละชนิด")
    st.caption("ที่มา: ประกาศสำนักงานปรมาณูเพื่อสันติ")

    # Build table
    rows = []
    for iso, d_tbq in D_VALUES_TBQ.items():
        d_ci = d_tbq / 3.7e-2
        info = ISOTOPE_INFO.get(iso, {})
        rows.append({
            "นิวไคลด์": iso,
            "ครึ่งชีวิต": info.get("halfLife", "—"),
            "D (TBq)": f"{d_tbq:.2e}",
            "D (Ci)": f"{d_ci:.2e}",
            "UN Number": info.get("unNo", "—"),
        })
    df = pd.DataFrame(rows)

    search = st.text_input("🔍 ค้นหานิวไคลด์", placeholder="เช่น Ir-192, Co-60")
    if search:
        df = df[df["นิวไคลด์"].str.contains(search, case=False)]

    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={"D (TBq)": st.column_config.TextColumn(width="small"),
                                "D (Ci)": st.column_config.TextColumn(width="small")})


# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("ตารางที่ 1 — การจำแนกประเภทวัสดุกัมมันตรังสีตามการประยุกต์ใช้ประโยชน์")
    st.caption("ที่มา: ประกาศสำนักงานปรมาณูเพื่อสันติ")

    for cat_num in range(1, 6):
        color = CATEGORY_COLORS[cat_num]
        bg = CATEGORY_BG[cat_num]
        threshold = CATEGORY_THRESHOLDS[cat_num][2]
        uses = [k for k, v in USE_TYPE_CATEGORY.items() if v == cat_num]

        with st.expander(f"ประเภท {cat_num} — {threshold}", expanded=(cat_num <= 2)):
            st.markdown(f"""
            <div style="background:{bg}; border-left:4px solid {color}; padding:12px 16px; border-radius:0 8px 8px 0;">
            """, unsafe_allow_html=True)
            for u in uses:
                st.markdown(f"• {u}")
            st.markdown("</div>", unsafe_allow_html=True)
