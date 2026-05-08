import os
import time
from dotenv import load_dotenv
from google import genai
from ddgs import DDGS
import streamlit as st

# --- טעינת משתני סביבה ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# --- הגדרות עמוד ---
st.set_page_config(
    page_title="בונה קורות חיים חכם",
    page_icon="💼",
    layout="wide"
)


# --- עיצוב CSS ---
st.markdown("""
    <style>
        body { direction: rtl; }
        .stButton>button {
            background-color: #0077b5;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .cv-box {
            background: white;
            border-radius: 12px;
            padding: 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            line-height: 1.9;
            border-top: 4px solid #0077b5;
            font-family: Arial, sans-serif;
        }
        .tip-box {
            background: #e8f4fd;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
            border-right: 3px solid #0077b5;
        }
        .section-card {
            background: white;
            border-radius: 10px;
            padding: 18px 22px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        }
        .chat-user {
            background: #e3f2fd;
            border-radius: 12px 12px 0 12px;
            padding: 10px 15px;
            margin: 8px 0;
            text-align: right;
        }
        .chat-ai {
            background: white;
            border-radius: 12px 12px 12px 0;
            padding: 10px 15px;
            margin: 8px 0;
            border-left: 3px solid #0077b5;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
    </style>
""", unsafe_allow_html=True)


# ===================== פונקציות =====================

def call_gemini(prompt):
    models = [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ]
    for model in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                if "503" in error_str:
                    wait = 15 * (attempt + 1)
                    st.warning(f"⏳ {model} עמוס – ממתין {wait} שניות...")
                    time.sleep(wait)
                elif "429" in error_str or "404" in error_str:
                    break
                else:
                    st.error(f"שגיאה: {e}")
                    return None
    st.error("❌ כל המודלים לא זמינים. נסה שוב מאוחר יותר.")
    return None


def search_web(query, max_results=5):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []


def search_job_market(role, field):
    """מחפש מידע עדכני על שוק העבודה"""
    results = search_web(f"{role} {field} job market skills 2025 Israel demand", max_results=5)
    keywords_results = search_web(f"{role} {field} resume keywords skills 2025", max_results=4)
    return results, keywords_results


def generate_cv(data, job_market_info, keywords_info):
    """מייצר קורות חיים מלאים"""

    job_context = "\n".join([r.get('body', '') for r in job_market_info[:3]])
    keywords_context = "\n".join([r.get('body', '') for r in keywords_info[:3]])

    prompt = f"""
אתה מומחה בכתיבת קורות חיים מקצועיים בישראל.

פרטי המועמד:
- שם מלא: {data['name']}
- תפקיד מבוקש: {data['role']}
- תחום: {data['field']}
- גיל: {data['age']}
- עיר מגורים: {data['city']}
- טלפון: {data['phone']}
- אימייל: {data['email']}
- LinkedIn: {data.get('linkedin', 'לא צוין')}
- השכלה: {data['education']}
- ניסיון עבודה: {data['experience']}
- כישורים טכניים: {data['skills']}
- שפות: {data['languages']}
- התנדבות / פעילות נוספת: {data.get('volunteering', 'לא צוין')}
- הישגים בולטים: {data.get('achievements', 'לא צוין')}
- סגנון קורות חיים: {data['cv_style']}
- שפת קורות החיים: {data['cv_language']}

מידע על שוק העבודה שנאסף מהאינטרנט:
{job_context}

מילות מפתח רלוונטיות לתפקיד:
{keywords_context}

צור קורות חיים מקצועיים ומלאים ב{data['cv_language']} הכוללים:

1. **כותרת** – שם, תפקיד מבוקש, פרטי קשר
2. **תקציר מקצועי** – 3-4 משפטים שמוכרים את המועמד
3. **ניסיון עבודה** – מסודר מהאחרון לראשון עם הישגים מדידים
4. **השכלה** – תארים, מוסדות, שנים
5. **כישורים** – טכניים ורכים, כולל מילות מפתח רלוונטיות שנמצאו
6. **שפות** – עם רמה
7. **התנדבות / פעילות נוספת** (אם קיים)

הנחיות:
- השתמש במילות המפתח הרלוונטיות שנמצאו בחיפוש
- כתוב הישגים עם מספרים ותוצאות מדידות כשניתן
- התאם לסגנון {data['cv_style']}
- כתוב ב{data['cv_language']} בלבד
- עצב בצורה קריאה ומסודרת
    """
    return call_gemini(prompt)


def improve_cv_section(section, content, role, field):
    """משפר חלק ספציפי בקורות החיים"""
    prompt = f"""
אתה מומחה בכתיבת קורות חיים. שפר את החלק הבא של קורות החיים.

תפקיד מבוקש: {role}
תחום: {field}
החלק לשיפור: {section}
תוכן נוכחי: {content}

שפר את הניסוח:
- הפוך אותו לחזק, ממוקד ומשכנע
- השתמש בפעלי פעולה חזקים
- הוסף מילות מפתח רלוונטיות
- הפוך הישגים למדידים (אם אפשר)
- כתוב בעברית

הצג:
1. הגרסה המשופרת
2. הסבר קצר על מה שיפרת
    """
    return call_gemini(prompt)


def answer_cv_question(question, cv_content, role, answer_style):
    """עונה על שאלות לגבי קורות החיים"""
    style_map = {
        "קצר": "ענה ב-3-4 משפטים בלבד.",
        "מפורט": "ענה בפירוט עם דוגמאות.",
        "נקודות": "ענה בנקודות ממוספרות בלבד.",
    }
    prompt = f"""
אתה יועץ קריירה מומחה. ענה על שאלת המשתמש לגבי קורות החיים שלו.

התפקיד המבוקש: {role}
קורות החיים:
{cv_content}

שאלה: {question}
{style_map.get(answer_style, style_map['קצר'])}
כתוב בעברית בלבד.
    """
    return call_gemini(prompt)


# ===================== ממשק ראשי =====================

# כותרת
st.markdown("""
    <div style='background: linear-gradient(135deg, #004e92, #0077b5, #00a8e8);
                padding: 28px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>💼 בונה קורות חיים חכם</h1>
        <p style='color: #cce8ff; margin: 8px 0 0 0; font-size: 1.1em;'>
            צור קורות חיים מקצועיים מותאמים לשוק העבודה | מבוסס Gemini AI + DuckDuckGo
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===================== טאבים =====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 פרטים אישיים",
    "⚡ שפר חלק מסוים",
    "💬 שאל יועץ קריירה",
    "💡 טיפים לחיפוש עבודה"
])


# ==================== טאב 1: בנה קורות חיים ====================
with tab1:
    st.markdown("## 📋 פרטי המועמד")
    st.info("מלא את הפרטים הבאים – ה-AI יבנה קורות חיים מקצועיים תוך שניות!")

    # --- פרטים בסיסיים ---
    st.markdown("### 👤 פרטים אישיים")
    col1, col2, col3 = st.columns(3)
    with col1:
        name = st.text_input("שם מלא:", placeholder="ישראל ישראלי", key="cv_name")
        age = st.number_input("גיל:", min_value=16, max_value=70, value=25, key="cv_age")
    with col2:
        city = st.text_input("עיר מגורים:", placeholder="תל אביב", key="cv_city")
        phone = st.text_input("טלפון:", placeholder="050-0000000", key="cv_phone")
    with col3:
        email = st.text_input("אימייל:", placeholder="name@email.com", key="cv_email")
        linkedin = st.text_input("LinkedIn (אופציונלי):", placeholder="linkedin.com/in/name", key="cv_linkedin")

    st.markdown("---")

    # --- תפקיד ותחום ---
    st.markdown("### 🎯 תפקיד ותחום")
    col1, col2, col3 = st.columns(3)
    with col1:
        role = st.text_input("תפקיד מבוקש:", placeholder="מפתח Full Stack / מנהל שיווק", key="cv_role")
    with col2:
        field = st.selectbox("תחום:", [
            "הייטק / טכנולוגיה", "שיווק ופרסום", "כספים וחשבונאות",
            "משאבי אנוש", "מכירות", "עיצוב וקריאייטיב",
            "חינוך", "בריאות ורפואה", "משפטים", "הנדסה",
            "לוגיסטיקה", "קמעונאות", "אחר"
        ], key="cv_field")
    with col3:
        cv_style = st.selectbox("סגנון קורות חיים:", [
            "מקצועי ורשמי",
            "יצירתי ודינמי",
            "טכנולוגי ומפורט",
            "קצר ותמציתי (מקסימום עמוד אחד)"
        ], key="cv_style")

    cv_language = st.radio("🌐 שפת קורות החיים:",
                            ["עברית", "אנגלית", "שתיהן"],
                            horizontal=True, key="cv_lang")

    st.markdown("---")

    # --- השכלה וניסיון ---
    st.markdown("### 🎓 השכלה וניסיון")
    col1, col2 = st.columns(2)
    with col1:
        education = st.text_area("השכלה:",
            placeholder="תואר ראשון במדעי המחשב – אוניברסיטת תל אביב (2020-2023)\nתעודת בגרות מלאה – תיכון X (2020)",
            height=120, key="cv_education")
    with col2:
        experience = st.text_area("ניסיון עבודה:",
            placeholder="מפתח Junior – חברת ABC (2023-היום)\n- פיתחתי מודול X שחסך 30% בזמן עיבוד\n- עבדתי עם React, Node.js, PostgreSQL\n\nסטאז' – חברת DEF (2022)",
            height=120, key="cv_experience")

    st.markdown("---")

    # --- כישורים ושפות ---
    st.markdown("### 🛠️ כישורים ושפות")
    col1, col2, col3 = st.columns(3)
    with col1:
        skills = st.text_area("כישורים טכניים:",
            placeholder="Python, JavaScript, React\nSQL, Git, Docker\nExcel, PowerPoint",
            height=100, key="cv_skills")
    with col2:
        languages = st.text_area("שפות:",
            placeholder="עברית – שפת אם\nאנגלית – גבוהה (C1)\nערבית – בסיסית",
            height=100, key="cv_languages")
    with col3:
        achievements = st.text_area("הישגים בולטים:",
            placeholder="זכייה בהאקתון X (2023)\nניהול פרויקט של 5 אנשים\nהגדלת מכירות ב-40%",
            height=100, key="cv_achievements")

    volunteering = st.text_input("התנדבות / פעילות נוספת (אופציונלי):",
                                  placeholder="מדריך בנוער עובד ולומד, חבר בעמותת X",
                                  key="cv_volunteering")

    st.markdown("---")

    # --- כפתור יצירה ---
    if st.button("🚀 צור קורות חיים מקצועיים!", key="cv_generate"):
        required = [name, role, education, experience, skills, languages, phone, email, city]
        if not all(f.strip() for f in required):
            st.warning("אנא מלא את כל השדות החובה (שם, תפקיד, השכלה, ניסיון, כישורים, שפות, פרטי קשר).")
        else:
            # שלב 1: חיפוש שוק עבודה עדכני
            with st.spinner(f"🔎 מחפש מידע עדכני על שוק העבודה ל{role}..."):
                job_market, keywords = search_job_market(role, field)

            found = len(job_market) + len(keywords)
            if found > 0:
                st.success(f"✅ נמצא מידע עדכני משוק העבודה – קורות החיים יכללו מילות מפתח רלוונטיות!")

            # שלב 2: יצירת קורות חיים
            data = {
                "name": name, "role": role, "field": field,
                "age": age, "city": city, "phone": phone,
                "email": email, "linkedin": linkedin,
                "education": education, "experience": experience,
                "skills": skills, "languages": languages,
                "achievements": achievements, "volunteering": volunteering,
                "cv_style": cv_style, "cv_language": cv_language
            }

            with st.spinner("🧠 ה-AI בונה קורות חיים מקצועיים..."):
                cv = generate_cv(data, job_market, keywords)

            if cv:
                st.session_state["cv_content"] = cv
                st.session_state["cv_role"] = role
                st.session_state["cv_chat"] = []

                st.success("✅ קורות החיים מוכנים!")
                st.markdown("---")
                st.markdown("## 📄 קורות החיים שלך")
                st.markdown(f'<div class="cv-box">{cv}</div>', unsafe_allow_html=True)

                st.markdown("---")

                # טיפים מהחיפוש
                if job_market:
                    st.markdown("### 🔍 מה מחפשים מעסיקים בתחום שלך כרגע?")
                    st.caption("מבוסס על חיפוש עדכני מהאינטרנט")
                    for item in job_market[:3]:
                        if item.get('href'):
                            with st.expander(f"📌 {item.get('title', '')}"):
                                st.write(item.get('body', '')[:300])
                                st.markdown(f"[קרא עוד ←]({item['href']})")

                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button("📥 הורד קורות חיים (TXT)",
                                       cv.encode("utf-8"),
                                       f"CV_{name}.txt", mime="text/plain")
                with col_b:
                    st.download_button("📋 הורד קורות חיים (Markdown)",
                                       cv.encode("utf-8"),
                                       f"CV_{name}.md", mime="text/markdown")


# ==================== טאב 2: שפר חלק מסוים ====================
with tab2:
    st.markdown("## ⚡ שפר חלק ספציפי בקורות החיים")
    st.markdown("הדבק חלק מקורות החיים שלך – ה-AI ישפר אותו לגרסה חזקה וממוקדת יותר!")

    col1, col2 = st.columns(2)
    with col1:
        improve_role = st.text_input("תפקיד מבוקש:", placeholder="מפתח Frontend", key="imp_role")
        improve_field = st.text_input("תחום:", placeholder="הייטק", key="imp_field")
    with col2:
        section_type = st.selectbox("איזה חלק לשפר?", [
            "תקציר מקצועי",
            "תיאור תפקיד / ניסיון",
            "רשימת כישורים",
            "הישגים",
            "מכתב מוטיבציה / כיסוי",
        ], key="imp_section")

    section_content = st.text_area(
        "📋 הדבק את החלק לשיפור:",
        placeholder="הדבק כאן את הטקסט הנוכחי שרוצה לשפר...",
        height=150,
        key="imp_content"
    )

    if st.button("⚡ שפר!", key="imp_btn"):
        if not section_content.strip() or not improve_role.strip():
            st.warning("אנא מלא תפקיד ותוכן לשיפור.")
        else:
            with st.spinner("✨ משפר..."):
                result = improve_cv_section(section_type, section_content, improve_role, improve_field)
            if result:
                st.success("✅ הגרסה המשופרת:")
                st.markdown(f'<div class="cv-box">{result}</div>', unsafe_allow_html=True)
                st.download_button("📥 הורד (TXT)", result.encode("utf-8"),
                                   f"שיפור_{section_type}.txt", mime="text/plain")


# ==================== טאב 3: יועץ קריירה ====================
with tab3:
    st.markdown("## 💬 שאל את יועץ הקריירה")

    if "cv_content" not in st.session_state:
        st.info("👆 קודם עבור לטאב **'פרטים אישיים'** וצור קורות חיים – ואז תוכל לשאול שאלות.")
    else:
        st.markdown(f"**🔗 מחובר לקורות החיים שלך לתפקיד:** {st.session_state.get('cv_role', '')}")

        col_style, col_q = st.columns([1, 3])
        with col_style:
            answer_style = st.radio("📝 סגנון תשובה:",
                                    ["קצר", "מפורט", "נקודות"], index=0, key="cv_chat_style")
        with col_q:
            cv_question = st.text_input("✍️ שאלתך:",
                placeholder="לדוגמה: איך לשפר את התקציר? / מה חסר בקורות החיים? / איך להתאים לתפקיד X?",
                key="cv_q")
            send = st.button("📨 שלח", key="cv_send")

        if send and cv_question.strip():
            with st.spinner("🤔 יועץ הקריירה חושב..."):
                answer = answer_cv_question(
                    cv_question,
                    st.session_state["cv_content"],
                    st.session_state["cv_role"],
                    answer_style
                )
            if answer:
                if "cv_chat" not in st.session_state:
                    st.session_state["cv_chat"] = []
                st.session_state["cv_chat"].append({
                    "q": cv_question, "a": answer, "style": answer_style
                })

        if st.session_state.get("cv_chat"):
            st.markdown("### 🗂️ היסטוריית שיחה")
            for chat in reversed(st.session_state["cv_chat"]):
                st.markdown(
                    f'<div class="chat-user">🧑 <b>{chat["q"]}</b> '
                    f'<span style="color:#888; font-size:0.8em">[{chat["style"]}]</span></div>',
                    unsafe_allow_html=True
                )
                st.markdown(f'<div class="chat-ai">🤖 {chat["a"]}</div>', unsafe_allow_html=True)

            if st.button("🗑️ נקה שיחה", key="cv_clear"):
                st.session_state["cv_chat"] = []
                st.rerun()


# ==================== טאב 4: טיפים לחיפוש עבודה ====================
with tab4:
    st.markdown("## 💡 טיפים לחיפוש עבודה בישראל")

    tip_role = st.text_input("🔎 לאיזה תפקיד? (לקבלת טיפים מותאמים):",
                              placeholder="מפתח Python / מנהל שיווק...", key="tip_role")

    if st.button("🔍 מצא טיפים מותאמים!", key="tip_btn"):
        if tip_role.strip():
            with st.spinner("🔎 מחפש טיפים עדכניים..."):
                results = search_web(f"{tip_role} job hunting tips Israel LinkedIn 2025", max_results=5)
                salary_results = search_web(f"{tip_role} salary Israel 2025 average", max_results=3)

            prompt = f"""
אתה יועץ קריירה מומחה בשוק העבודה הישראלי.
בהתבסס על המידע שנאסף, תן טיפים מעשיים לחיפוש עבודה כ{tip_role} בישראל.

מידע שנאסף מהאינטרנט:
{chr(10).join([r.get('body','') for r in results[:3]])}

מידע שכר:
{chr(10).join([r.get('body','') for r in salary_results[:2]])}

כלול:
1. 💰 טווח שכר משוער לתפקיד זה בישראל (לפי המידע שנמצא)
2. 🏆 3 אתרי גיוס מומלצים לתפקיד זה
3. 📌 5 טיפים ספציפיים לחיפוש עבודה בתפקיד זה
4. 🔑 מילות מפתח חשובות לפרופיל LinkedIn
5. ❓ 3 שאלות ראיון נפוצות לתפקיד זה + איך לענות

כתוב בעברית בצורה ברורה ומעשית.
            """
            with st.spinner("🧠 מכין טיפים מותאמים..."):
                tips_result = call_gemini(prompt)

            if tips_result:
                st.markdown(f'<div class="cv-box">{tips_result}</div>', unsafe_allow_html=True)

                # קישורי מקורות
                if results:
                    st.markdown("---")
                    st.markdown("### 🔗 מקורות שנמצאו")
                    for r in results:
                        if r.get('href'):
                            st.markdown(f"- [{r.get('title', 'קישור')}]({r.get('href')})")

    st.markdown("---")
    st.markdown("### 📋 טיפים כלליים לכל מחפש עבודה")

    tips_general = [
        ("🎯 התאם כל קורות חיים בנפרד",
         "אל תשלח אותם קורות חיים לכל מקום. קרא את הדרישות והתאם את השפה והמילות המפתח."),
        ("💼 LinkedIn הוא חובה",
         "עדכן את הפרופיל, הוסף תמונה מקצועית, וכתוב תקציר מרשים. מגייסים מחפשים שם ראשונים."),
        ("🔢 השתמש בנתונים מספריים",
         "במקום 'שיפרתי תהליכים' כתוב 'שיפרתי תהליכים ב-30% ובחסכתי 5 שעות שבועיות'."),
        ("📧 מכתב כיסוי = יתרון",
         "לא כולם כותבים – אם תכתוב אחד מותאם ואישי, תתבלט מהקהל."),
        ("🤝 נטוורקינג עובד",
         "כ-70% מהמשרות מתמלאות דרך המלצות. פנה לאנשים בתחום שלך ב-LinkedIn."),
        ("⏰ הגש מהר",
         "משרות רבות מתמלאות תוך ימים ספורים. הגדר התראות ב-LinkedIn, AllJobs, Jobmaster."),
    ]

    col1, col2 = st.columns(2)
    for i, (title, desc) in enumerate(tips_general):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
                <div class="tip-box">
                    <b>{title}</b><br>
                    <small>{desc}</small>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🌐 אתרי חיפוש עבודה מומלצים בישראל")
    sites = [
        ("AllJobs", "https://www.alljobs.co.il", "הפלטפורמה הגדולה בישראל"),
        ("LinkedIn Jobs", "https://www.linkedin.com/jobs", "חובה לכל מחפש עבודה"),
        ("Jobmaster", "https://www.jobmaster.co.il", "נפוץ בהייטק ובתעשייה"),
        ("Drushim", "https://www.drushim.co.il", "מגוון תחומים"),
        ("Comeet", "https://www.comeet.com", "חברות הייטק"),
        ("JobNet", "https://www.jobnet.co.il", "מגזר ציבורי ופרטי"),
    ]
    cols = st.columns(3)
    for i, (name_site, url, desc) in enumerate(sites):
        with cols[i % 3]:
            st.markdown(f"""
                <div class="section-card" style="text-align:center;">
                    <b><a href="{url}" target="_blank">{name_site}</a></b><br>
                    <small style="color:gray;">{desc}</small>
                </div>
            """, unsafe_allow_html=True)

# --- פוטר ---
st.markdown("---")
st.markdown("""
    <p style='text-align:center; color:gray;'>
        💼 בונה קורות חיים חכם | פותח באמצעות Gemini AI + DuckDuckGo | © 2026
    </p>
""", unsafe_allow_html=True)