import streamlit as st



st.set_page_config(
    page_title="אודות הכלי",
    page_icon="ℹ️",
    layout="wide"
)

st.markdown("""
    <style>
        body { direction: rtl; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin: 15px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .feature-icon { font-size: 2em; margin-bottom: 8px; }
        .step-number {
            background: #1a73e8;
            color: white;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-left: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# כותרת
st.markdown("""
    <div style='background: linear-gradient(135deg, #1a73e8, #0d47a1);
                padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 25px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>ℹ️ אודות הכלי</h1>
        <p style='color: #cce0ff; margin: 8px 0 0 0; font-size: 1.1em;'>
            כל מה שצריך לדעת על כלי מחקר השוק החכם
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# === מה הכלי עושה ===
st.markdown("## 🎯 מה הכלי עושה?")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
        <div class='card' style='text-align:center;'>
            <div class='feature-icon'>🔍</div>
            <h3>מחקר שוק חכם</h3>
            <p>מחפש מידע עדכני מהאינטרנט ומסכם אותו לדוח מקצועי תוך שניות באמצעות Gemini AI.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class='card' style='text-align:center;'>
            <div class='feature-icon'>📈</div>
            <h3>מידע פיננסי</h3>
            <p>בודק בורסות ושווקים במדינות שונות, מציג מגמות צמיחה ומאפשר השוואה בין שווקים.</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class='card' style='text-align:center;'>
            <div class='feature-icon'>💬</div>
            <h3>צ'אט AI מותאם</h3>
            <p>שאל שאלות על הדוח וקבל תשובות מותאמות לפרופיל שלך – קצר, ארוך, נקודות או טבלה.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# === איך להשתמש ===
st.markdown("## 🚀 איך משתמשים בכלי?")

steps = [
    ("מחקר שוק", "עבור לדף הראשי, הכנס נושא לחיפוש ולחץ על 'צור דוח מחקר'. הכלי יחפש מידע ויייצר דוח מקצועי."),
    ("מידע פיננסי", "עבור לדף 'סוכן מידע פיננסי', בחר מדינות וסקטור ולחץ על 'בצע מחקר שוק'."),
    ("שאל שאלות", "לאחר יצירת הדוח, גלול למטה לקטע הצ'אט ושאל שאלות ממוקדות על הנושא."),
    ("הורד את הדוח", "בסיום, לחץ על כפתור ההורדה לקבלת הדוח כקובץ TXT או Markdown."),
]

for i, (title, desc) in enumerate(steps, 1):
    st.markdown(f"""
        <div class='card'>
            <span class='step-number'>{i}</span>
            <b>{title}</b> – {desc}
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# === טכנולוגיות ===
st.markdown("## 🛠️ טכנולוגיות בשימוש")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
        <div class='card'>
            <h4>🤖 Gemini AI (Google)</h4>
            <p>מודל שפה מתקדם של Google לניתוח וסיכום מידע. משתמש במודלים החדשים ביותר עם מנגנון fallback אוטומטי.</p>
            <h4>🔎 DuckDuckGo Search</h4>
            <p>מנוע חיפוש פרטיות-ראשון לאיסוף מידע עדכני מהאינטרנט – כולל טקסט, תמונות וחדשות.</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class='card'>
            <h4>📊 Streamlit</h4>
            <p>פלטפורמה לבניית אפליקציות data science בפייתון בצורה מהירה ומקצועית.</p>
            <h4>🖼️ Pillow</h4>
            <p>ספריית עיבוד תמונות לטעינה ועיבוד תמונות מהאינטרנט בזמן אמת.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# === הגבלות ===
st.markdown("## ⚠️ הגבלות חשובות")
st.markdown("""
    <div class='card' style='border-right: 4px solid #ff6b00;'>
        <ul style='margin:0; padding-right: 20px;'>
            <li>הכלי משתמש ב-<b>Free Tier</b> של Gemini – ייתכנו עיכובים בשעות עומס.</li>
            <li>המידע הפיננסי הוא <b>לצרכי מידע בלבד</b> ואינו ייעוץ השקעות.</li>
            <li>דיוק המידע תלוי במקורות הציבוריים הזמינים באינטרנט.</li>
            <li>חיפוש תמונות עשוי להיכשל עבור חלק מהנושאים.</li>
        </ul>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# === פוטר ===
st.markdown("""
    <p style='text-align:center; color:gray;'>
        פותח באמצעות Gemini AI + DuckDuckGo + Streamlit | © 2026
    </p>
""", unsafe_allow_html=True)