# ☢️ ระบบจัดการเอกสารความปลอดภัยทางรังสี

Streamlit multipage app สำหรับเจ้าหน้าที่ความปลอดภัยทางรังสี (RSO) และนักรังสีการแพทย์

## โครงสร้างโปรเจค

```
radiation_project/
├── app.py                          ← หน้าหลัก (Home)
├── requirements.txt
├── .gitignore
├── README.md
│
├── pages/                          ← แต่ละหน้าของ app
│   ├── 1_🔍_จำแนกประเภทวัสดุ.py   ← จำแนกประเภทวัสดุกัมมันตรังสี (A/D ratio)
│   ├── 2_🚛_แผนขนส่ง.py            ← แผนขนส่ง + TI + Package Type + UN Number
│   ├── 3_🛡️_แผนป้องกันอันตราย.py  ← คำนวณกำบัง + Dose + AI ร่างแผน
│   ├── 4_🔒_แผนความมั่นคง.py       ← แผนรักษาความมั่นคงปลอดภัย
│   └── 5_🤖_Chatbot.py             ← Chatbot Typhoon2 (Thai-English RAG)
│
└── utils/                          ← ไฟล์ utility ที่ใช้ร่วมกัน
    ├── __init__.py
    └── data.py                     ← ฐานข้อมูลกลาง (D-values, isotope info ฯลฯ)
```

## ข้อมูลอ้างอิงใน utils/data.py

| ข้อมูล | แหล่งที่มา | จำนวน isotope |
|--------|-----------|--------------|
| D-value (ตารางที่ 2) | ประกาศ ปส. | 33 isotope |
| D-value (fallback) | IAEA-EPR-D-Values 2006 | 303 isotope |
| ตารางที่ 1 (การใช้ประโยชน์ → ประเภท) | ประกาศ ปส. | 21 รายการ |
| A1, A2 values | IAEA SSR-6 | 33 isotope |

## วิธีรัน Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## วิธี Deploy บน HF Spaces

1. สร้าง Space ใหม่ที่ huggingface.co/spaces → SDK = **Streamlit**
2. อัปโหลดทุกไฟล์ในโฟลเดอร์นี้ (รวม `utils/` และ `pages/`)
3. HF จะ build และ deploy ให้อัตโนมัติ ✅

## API Keys ที่ต้องใช้

| Page | Key | หมายเหตุ |
|------|-----|---------|
| Page 2, 3, 4 | Anthropic API Key | สำหรับ AI ร่างแผน |
| Page 5 | HF Token | สำหรับ Typhoon2 chatbot (ฟรี) |

## อ้างอิง

- พระราชบัญญัติพลังงานนิวเคลียร์เพื่อสันติ พ.ศ. 2559
- กฎกระทรวงความปลอดภัยทางรังสี พ.ศ. 2561
- ประกาศ ปส. ตารางที่ 1 และ 2
- IAEA SSR-6 (2018) — Safe Transport of Radioactive Material
- IAEA SRS No.47 — Radiation Protection in Radiotherapy
- NCRP Report No.151 — Structural Shielding Design
- IAEA-EPR-D-Values 2006
