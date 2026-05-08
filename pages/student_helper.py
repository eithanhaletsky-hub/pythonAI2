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
    page_title="עוזר לימודים חכם",
    page_icon="🎓",
    layout="wide"
)

# --- עיצוב CSS ---
st.markdown("""
    <style>
        body { direction: rtl; }
        .main { background-color: #f8f9ff; }
        .stButton>button {
            background-color: #7c4dff;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .answer-box {
            background: white;
            border-radius: 12px;
            padding: 1.5em 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.09);
            line-height: 1.9;
            border-right: 4px solid #7c4dff;
        }
        .card-box {
            background: white;
            border-radius: 10px;
            padding: 16px 20px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-top: 3px solid #7c4dff;
        }
        .chat-user {
            background: #ede7f6;
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
            border-left: 3px solid #7c4dff;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .tip-box {
            background: #e8f5e9;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
            border-right: 3px solid #43a047;
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


# ===================== כותרת ראשית =====================
st.markdown("""
    <div style='background: linear-gradient(135deg, #4527a0, #7c4dff, #b388ff);
                padding: 28px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>🎓 עוזר לימודים חכם</h1>
        <p style='color: #ede7f6; margin: 8px 0 0 0; font-size: 1.1em;'>
            כל הכלים שתלמיד צריך – במקום אחד | מופעל על ידי Gemini AI
        </p>
    </div>
""", unsafe_allow_html=True)

# ===================== טאבים =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📚 שיעורי בית",
    "🎯 כרטיסיות לימוד",
    "🎓 עוזר לבגרות",
    "🌐 מתרגל שפות",
    "✍️ עבודות וחיבורים"
])


# ==================== טאב 1: שיעורי בית ====================
with tab1:
    st.markdown("## 📚 עוזר שיעורי בית חכם")
    st.markdown("כתוב את השאלה או התרגיל שלך – ה-AI יסביר **שלב אחר שלב** ולא יתן את התשובה ישירות!")

    col1, col2 = st.columns([2, 1])
    with col1:
        subject = st.selectbox("📖 מקצוע:", [
            "מתמטיקה", "פיזיקה", "כימיה", "ביולוגיה",
            "היסטוריה", "אנגלית", "ספרות", "גיאוגרפיה",
            "אזרחות", "תנ\"ך", "אחר"
        ], key="hw_subject")
    with col2:
        grade = st.selectbox("🏫 כיתה:", [
            "ז'", "ח'", "ט'", "י'", "י\"א", "י\"ב"
        ], key="hw_grade")

    explain_style = st.radio(
        "🎨 סגנון הסבר:",
        ["מסביר בעדינות (מתחיל)", "מסביר בינוני", "מסביר מהר (מתקדם)"],
        horizontal=True,
        key="hw_style"
    )

    question = st.text_area(
        "✏️ כתוב את השאלה / התרגיל:",
        placeholder="לדוגמה: פתור את המשוואה 2x + 5 = 13\nאו: הסבר מדוע פרצה מלחמת העולם הראשונה",
        height=120,
        key="hw_question"
    )

    if st.button("🔍 הסבר לי!", key="hw_btn"):
        if not question.strip():
            st.warning("אנא כתוב שאלה.")
        else:
            style_map = {
                "מסביר בעדינות (מתחיל)": "הסבר בצורה פשוטה מאוד, עם דוגמאות קלות. השתמש במילים פשוטות.",
                "מסביר בינוני": "הסבר בצורה ברורה עם שלבים. לא פשוט מדי ולא מסובך.",
                "מסביר מהר (מתקדם)": "הסבר בצורה תמציתית ומדויקת. ניתן להשתמש במונחים מקצועיים."
            }
            prompt = f"""
אתה מורה מעולה המלמד תלמיד כיתה {grade} במקצוע {subject}.

כללים חשובים:
- אל תיתן את התשובה הסופית ישירות!
- הסבר את הדרך לפתרון שלב אחר שלב
- בסוף כל שלב שאל "האם הבנת עד כאן?"
- השתמש בדוגמאות ממשיות וברורות
- {style_map[explain_style]}
- כתוב בעברית בלבד

השאלה / התרגיל של התלמיד:
{question}

הסבר את הגישה לפתרון בשלבים ברורים.
            """
            with st.spinner("🧠 מכין הסבר..."):
                answer = call_gemini(prompt)
            if answer:
                st.markdown("### 💡 הסבר:")
                st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)
                if "hw_chat" not in st.session_state:
                    st.session_state["hw_chat"] = []
                st.session_state["hw_chat"].append({"q": question, "a": answer, "subject": subject})

    # צ'אט המשך
    if st.session_state.get("hw_chat"):
        st.markdown("---")
        st.markdown("### 💬 שאל שאלת המשך")
        followup = st.text_input("עדיין לא הבנת משהו? שאל:", key="hw_followup")
        if st.button("📨 שלח", key="hw_followup_btn"):
            if followup.strip():
                context = st.session_state["hw_chat"][-1]["a"]
                prompt = f"""
אתה מורה עוזר. ענה על שאלת ההמשך של התלמיד בצורה פשוטה וברורה.
הקשר קודם: {context}
שאלת ההמשך: {followup}
כתוב בעברית בלבד.
                """
                with st.spinner("🤔 חושב..."):
                    followup_ans = call_gemini(prompt)
                if followup_ans:
                    st.session_state["hw_chat"].append({"q": followup, "a": followup_ans, "subject": subject})

        # הצג היסטוריה
        for chat in reversed(st.session_state["hw_chat"]):
            st.markdown(f'<div class="chat-user">🧑 {chat["q"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-ai">🤖 {chat["a"]}</div>', unsafe_allow_html=True)

        if st.button("🗑️ נקה שיחה", key="hw_clear"):
            st.session_state["hw_chat"] = []
            st.rerun()


# ==================== טאב 2: כרטיסיות לימוד ====================
with tab2:
    st.markdown("## 🎯 מחולל כרטיסיות לימוד")
    st.markdown("הדבק טקסט מספר לימוד – ה-AI ייצר תקציר, כרטיסיות שאלה-תשובה ושאלות בחינה!")

    col1, col2 = st.columns([2, 1])
    with col1:
        cards_subject = st.selectbox("📖 מקצוע:", [
            "מתמטיקה", "פיזיקה", "כימיה", "ביולוגיה",
            "היסטוריה", "אנגלית", "ספרות", "גיאוגרפיה", "אחר"
        ], key="cards_subject")
    with col2:
        num_cards = st.slider("כמות כרטיסיות:", min_value=3, max_value=15, value=7, key="num_cards")

    text_input = st.text_area(
        "📋 הדבק כאן טקסט מספר / מחברת:",
        placeholder="הדבק כאן קטע מספר לימוד, הרצאה, או כל טקסט שרוצה ללמוד...",
        height=200,
        key="cards_text"
    )

    output_type = st.multiselect(
        "📦 מה לייצר?",
        ["📝 תקציר קצר", "🃏 כרטיסיות שאלה-תשובה", "❓ שאלות בחינה פוטנציאליות", "🔑 מילות מפתח"],
        default=["📝 תקציר קצר", "🃏 כרטיסיות שאלה-תשובה"],
        key="cards_output"
    )

    if st.button("✨ צור חומר לימוד!", key="cards_btn"):
        if not text_input.strip():
            st.warning("אנא הדבק טקסט.")
        elif not output_type:
            st.warning("אנא בחר לפחות סוג פלט אחד.")
        else:
            sections = []
            if "📝 תקציר קצר" in output_type:
                sections.append("תקציר קצר וברור של הנושא (4-6 משפטים)")
            if "🃏 כרטיסיות שאלה-תשובה" in output_type:
                sections.append(f"{num_cards} כרטיסיות לימוד בפורמט:\nשאלה: [שאלה]\nתשובה: [תשובה קצרה]\n---")
            if "❓ שאלות בחינה פוטנציאליות" in output_type:
                sections.append("5 שאלות בסגנון בחינה (כולל שאלות פתוחות וסגורות)")
            if "🔑 מילות מפתח" in output_type:
                sections.append("10 מילות מפתח חשובות עם הסבר קצר לכל אחת")

            prompt = f"""
אתה מורה מומחה במקצוע {cards_subject}.
נתח את הטקסט הבא וצור את הדברים הבאים בעברית:

{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(sections))}

הטקסט ללימוד:
{text_input}

כתוב בצורה ברורה ומסודרת. השתמש בכותרות ברורות לכל חלק.
            """
            with st.spinner("🃏 מייצר חומר לימוד..."):
                result = call_gemini(prompt)

            if result:
                st.success("✅ חומר הלימוד מוכן!")
                st.markdown(f'<div class="answer-box">{result}</div>', unsafe_allow_html=True)
                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button("📥 הורד (TXT)", result.encode("utf-8"),
                                       f"כרטיסיות_{cards_subject}.txt", mime="text/plain")
                with col_b:
                    st.download_button("📋 הורד (Markdown)", result.encode("utf-8"),
                                       f"כרטיסיות_{cards_subject}.md", mime="text/markdown")


# ==================== טאב 3: עוזר לבגרות ====================
with tab3:
    st.markdown("## 🎓 עוזר לבגרות")
    st.markdown("בחר מקצוע בגרות – ה-AI ייצר שאלות תרגול בסגנון בגרות אמיתי ויסביר את התשובות!")

    col1, col2, col3 = st.columns(3)
    with col1:
        bagrut_subject = st.selectbox("📖 מקצוע בגרות:", [
            "מתמטיקה 3 יח'", "מתמטיקה 4 יח'", "מתמטיקה 5 יח'",
            "אנגלית", "עברית (הבנת הנקרא)", "היסטוריה",
            "פיזיקה", "כימיה", "ביולוגיה", "אזרחות",
            "ספרות", "גיאוגרפיה", "מחשבת ישראל", "תנ\"ך"
        ], key="bagrut_subject")
    with col2:
        difficulty = st.select_slider("⚡ רמת קושי:", [
            "קל", "בינוני", "קשה", "רמת בגרות מלאה"
        ], value="בינוני", key="bagrut_diff")
    with col3:
        num_questions = st.slider("כמות שאלות:", 1, 5, 3, key="bagrut_num")

    topic = st.text_input(
        "📌 נושא ספציפי (אופציונלי):",
        placeholder="לדוגמה: גזרות נגזרות / מלחמת יום כיפור / הסבר על תאי עצב",
        key="bagrut_topic"
    )

    mode = st.radio(
        "🎯 מצב:",
        ["📝 צור שאלות תרגול", "✅ צור שאלות עם תשובות מלאות", "📊 הסבר נושא לפני תרגול"],
        horizontal=True,
        key="bagrut_mode"
    )

    if st.button("🎓 צור חומר לבגרות!", key="bagrut_btn"):
        mode_prompt = {
            "📝 צור שאלות תרגול": f"צור {num_questions} שאלות תרגול בסגנון בגרות. אל תיתן תשובות – רק את השאלות.",
            "✅ צור שאלות עם תשובות מלאות": f"צור {num_questions} שאלות בגרות עם פתרון מלא ומפורט לכל שאלה.",
            "📊 הסבר נושא לפני תרגול": f"הסבר את הנושא בצורה מקיפה ואז צור {num_questions} שאלות תרגול."
        }

        # חיפוש מידע עדכני אם יש נושא ספציפי
        extra_info = ""
        if topic.strip():
            with st.spinner(f"🔎 מחפש מידע על {topic}..."):
                results = search_web(f"{bagrut_subject} {topic} בגרות הסבר", max_results=3)
                if results:
                    extra_info = "\n".join([r.get('body', '') for r in results])

        prompt = f"""
אתה מורה מומחה לבגרויות בישראל במקצוע {bagrut_subject}.

{mode_prompt[mode]}
רמת קושי: {difficulty}
נושא: {topic if topic.strip() else "לבחירתך לפי המקצוע"}

{f"מידע רקע שנמצא: {extra_info}" if extra_info else ""}

הנחיות:
- כתוב בסגנון בגרות ישראלי אמיתי
- ציין כמה נקודות שווה כל שאלה
- השתמש בפורמט ברור עם מספור
- כתוב בעברית בלבד
        """
        with st.spinner("📝 מכין שאלות בגרות..."):
            result = call_gemini(prompt)

        if result:
            st.success("✅ מוכן!")
            st.markdown(f'<div class="answer-box">{result}</div>', unsafe_allow_html=True)

            if "bagrut_history" not in st.session_state:
                st.session_state["bagrut_history"] = []
            st.session_state["bagrut_history"].append({
                "subject": bagrut_subject, "topic": topic or "כללי", "content": result
            })

            st.download_button("📥 הורד שאלות (TXT)", result.encode("utf-8"),
                               f"בגרות_{bagrut_subject}.txt", mime="text/plain")

    # היסטוריית תרגולים
    if st.session_state.get("bagrut_history"):
        st.markdown("---")
        st.markdown("### 🕓 תרגולים קודמים בסשן זה")
        for i, item in enumerate(reversed(st.session_state["bagrut_history"])):
            with st.expander(f"📄 {item['subject']} – {item['topic']}"):
                st.markdown(item["content"])
        if st.button("🗑️ נקה היסטוריה", key="bagrut_clear"):
            st.session_state["bagrut_history"] = []
            st.rerun()


# ==================== טאב 4: מתרגל שפות ====================
with tab4:
    st.markdown("## 🌐 מתרגל שפות")
    st.markdown("כתוב משפט בשפה שאתה לומד – ה-AI יתקן, יסביר את השגיאות וילמד אותך!")

    col1, col2, col3 = st.columns(3)
    with col1:
        language = st.selectbox("🌍 שפה:", [
            "אנגלית", "ערבית", "צרפתית", "ספרדית", "גרמנית"
        ], key="lang_select")
    with col2:
        lang_level = st.select_slider("📊 רמה:", [
            "מתחיל", "בסיסי", "בינוני", "מתקדם"
        ], value="בסיסי", key="lang_level")
    with col3:
        lang_mode = st.selectbox("🎯 מצב תרגול:", [
            "תקן את המשפט שלי",
            "תרגם לי מעברית",
            "תרגם לי לעברית",
            "שיחה חופשית בשפה",
            "הסבר מילה / ביטוי",
        ], key="lang_mode")

    user_text = st.text_area(
        "✍️ כתוב כאן:",
        placeholder="כתוב משפט, מילה, או שאלה בשפה שתרצה...",
        height=100,
        key="lang_text"
    )

    if st.button("🌐 בדוק / תרגם / הסבר!", key="lang_btn"):
        if not user_text.strip():
            st.warning("אנא כתוב משהו.")
        else:
            mode_prompts = {
                "תקן את המשפט שלי": f"""
תקן את המשפט הבא ב{language} ברמת {lang_level}.
הסבר כל שגיאה שמצאת בעברית.
פרמט תשובה:
✅ המשפט המתוקן: [...]
📝 שגיאות והסברים:
- שגיאה 1: [הסבר]
- שגיאה 2: [הסבר]
💡 טיפ: [טיפ שימושי]
המשפט: {user_text}""",
                "תרגם לי מעברית": f"תרגם את הטקסט הבא לעברית מ{language}. הסבר מילים קשות. טקסט: {user_text}",
                "תרגם לי לעברית": f"תרגם את הטקסט הבא מעברית ל{language} ברמת {lang_level}. הסבר בחירות מילים: {user_text}",
                "שיחה חופשית בשפה": f"שוחח איתי ב{language} ברמת {lang_level}. אם אני טועה – תקן בעדינות. ואז ענה בעברית גם. הודעה שלי: {user_text}",
                "הסבר מילה / ביטוי": f"הסבר בעברית את המילה/ביטוי '{user_text}' ב{language}. כלול: משמעות, דוגמאות שימוש, ביטויים קשורים."
            }

            prompt = mode_prompts[lang_mode]
            with st.spinner(f"🌐 מעבד {language}..."):
                result = call_gemini(prompt)

            if result:
                st.markdown(f'<div class="answer-box">{result}</div>', unsafe_allow_html=True)

                if "lang_chat" not in st.session_state:
                    st.session_state["lang_chat"] = []
                st.session_state["lang_chat"].append({
                    "input": user_text, "output": result, "lang": language, "mode": lang_mode
                })

    # טיפים לשפה הנבחרת
    with st.expander(f"💡 טיפים ללימוד {language}"):
        tips = {
            "אנגלית": ["הקשב לפודקאסטים באנגלית", "קרא חדשות ב-BBC Learning English", "תרגל 10 מילים חדשות כל יום"],
            "ערבית": ["התחל עם ערבית דיבורית (עמייה)", "קרא את האלפבית יום יום", "שמע מוסיקה ערבית"],
            "צרפתית": ["האזן ל-RFI Français Facile", "צפה בסרטים צרפתיים עם כתוביות", "תרגל זיווג מגדרי"],
            "ספרדית": ["ספרדית קרובה לאנגלית – הרבה מילים דומות!", "האזן ל-Radio Ambulante", "תרגל conjugation"],
            "גרמנית": ["למד Der/Die/Das מיד עם כל מילה", "גרמנית מדויקת – שים לב לסדר מילים", "שמע Deutsche Welle"],
        }
        for tip in tips.get(language, ["תרגל כל יום!", "אל תפחד לטעות!", "צפה בתכנים בשפה המקורית"]):
            st.markdown(f'<div class="tip-box">💡 {tip}</div>', unsafe_allow_html=True)

    # היסטוריית תרגול שפה
    if st.session_state.get("lang_chat"):
        st.markdown("---")
        st.markdown("### 🗂️ תרגולים קודמים")
        for chat in reversed(st.session_state["lang_chat"][-5:]):
            st.markdown(f'<div class="chat-user">🧑 [{chat["lang"]} – {chat["mode"]}] {chat["input"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-ai">🤖 {chat["output"]}</div>', unsafe_allow_html=True)
        if st.button("🗑️ נקה", key="lang_clear"):
            st.session_state["lang_chat"] = []
            st.rerun()


# ==================== טאב 5: עבודות וחיבורים ====================
with tab5:
    st.markdown("## ✍️ עוזר עבודות וחיבורים")
    st.markdown("ה-AI עוזר לך לבנות, לכתוב ולשפר – אבל **לא כותב את העבודה בשבילך!**")

    col1, col2 = st.columns([2, 1])
    with col1:
        essay_subject = st.selectbox("📖 מקצוע:", [
            "עברית", "היסטוריה", "אנגלית", "ספרות",
            "אזרחות", "ביולוגיה", "גיאוגרפיה", "אחר"
        ], key="essay_subject")
    with col2:
        essay_mode = st.selectbox("🎯 מה אתה צריך?", [
            "🏗️ בנה מבנה לעבודה",
            "💡 עזור לי עם הקדמה",
            "📝 שפר את הניסוח שלי",
            "🔍 חפש מקורות",
            "✅ בדוק עבורי את החיבור",
            "💬 הסבר על נושא",
        ], key="essay_mode")

    essay_topic = st.text_input(
        "📌 נושא העבודה / החיבור:",
        placeholder="לדוגמה: השפעת מלחמת יום כיפור על החברה הישראלית",
        key="essay_topic"
    )

    user_essay = st.text_area(
        "📄 כתוב כאן (הטקסט שלך / שאלה / בקשה):",
        placeholder="הדבק כאן את מה שכתבת, או תאר מה אתה צריך...",
        height=180,
        key="essay_text"
    )

    essay_length = st.radio(
        "📏 אורך תגובה:",
        ["קצר ותמציתי", "בינוני", "מפורט"],
        horizontal=True,
        key="essay_length"
    )

    if st.button("✍️ עזור לי!", key="essay_btn"):
        if not essay_topic.strip() and not user_essay.strip():
            st.warning("אנא כתוב נושא או טקסט.")
        else:
            length_map = {
                "קצר ותמציתי": "תן תשובה קצרה של 3-5 משפטים.",
                "בינוני": "תן תשובה בינונית עם הסברים.",
                "מפורט": "תן תשובה מפורטת ומקיפה עם דוגמאות."
            }

            # אם צריך מקורות – חפש עם DDGS
            sources_info = ""
            if essay_mode == "🔍 חפש מקורות" and essay_topic.strip():
                with st.spinner("🔎 מחפש מקורות..."):
                    results = search_web(f"{essay_topic} מקורות מידע", max_results=6)
                    if results:
                        sources_info = "\n".join([
                            f"- {r.get('title', '')} | {r.get('href', '')}"
                            for r in results if r.get('href')
                        ])

            mode_prompts = {
                "🏗️ בנה מבנה לעבודה": f"בנה מבנה מפורט לעבודה על: {essay_topic}. כלול: מבוא, פרקים ראשיים, מסקנה. {length_map[essay_length]}",
                "💡 עזור לי עם הקדמה": f"עזור לי לכתוב הקדמה לעבודה על: {essay_topic}. הסבר מה צריכה הקדמה טובה לכלול. {length_map[essay_length]}",
                "📝 שפר את הניסוח שלי": f"שפר את הניסוח של הטקסט הבא תוך שמירה על המשמעות המקורית. הסבר מה שיפרת: {user_essay}",
                "🔍 חפש מקורות": f"הנה מקורות שנמצאו ברשת על {essay_topic}:\n{sources_info}\n\nסכם אילו מקורות נראים איכותיים ולמה.",
                "✅ בדוק עבורי את החיבור": f"בדוק את החיבור הבא. ציין: שגיאות שפה, מבנה, ניסוח לשיפור, ונקודות חזקות:\n{user_essay}",
                "💬 הסבר על נושא": f"הסבר את הנושא: {essay_topic}. {length_map[essay_length]} כתוב בצורה שתעזור לי לכתוב עבודה."
            }

            prompt = f"""
אתה מורה עוזר לתלמיד במקצוע {essay_subject}.
חשוב: אל תכתוב את העבודה המלאה בשביל התלמיד! עזור, הכווין ולמד.

{mode_prompts[essay_mode]}

כתוב בעברית בלבד בצורה ברורה ועניינית.
            """

            with st.spinner("✍️ מכין עזרה..."):
                result = call_gemini(prompt)

            if result:
                st.success("✅ הנה העזרה שביקשת!")
                st.markdown(f'<div class="answer-box">{result}</div>', unsafe_allow_html=True)

                # הצג מקורות עם קישורים אם חיפשנו
                if essay_mode == "🔍 חפש מקורות" and sources_info:
                    st.markdown("---")
                    st.markdown("### 🔗 קישורים למקורות שנמצאו")
                    results = search_web(f"{essay_topic} מקורות מידע", max_results=6)
                    for r in results:
                        if r.get('href'):
                            st.markdown(f"- [{r.get('title', 'קישור')}]({r.get('href')})")

                st.download_button(
                    "📥 הורד עזרה (TXT)",
                    result.encode("utf-8"),
                    f"עזרה_{essay_topic[:20]}.txt",
                    mime="text/plain"
                )

                if "essay_history" not in st.session_state:
                    st.session_state["essay_history"] = []
                st.session_state["essay_history"].append({
                    "topic": essay_topic, "mode": essay_mode, "result": result
                })

    # היסטוריה
    if st.session_state.get("essay_history"):
        st.markdown("---")
        st.markdown("### 🕓 עזרות קודמות")
        for item in reversed(st.session_state["essay_history"][-4:]):
            with st.expander(f"📄 {item['mode']} – {item['topic'][:40]}"):
                st.markdown(item["result"])
        if st.button("🗑️ נקה היסטוריה", key="essay_clear"):
            st.session_state["essay_history"] = []
            st.rerun()

# --- פוטר ---
st.markdown("---")
st.markdown("""
    <p style='text-align:center; color:gray;'>
        🎓 עוזר לימודים חכם | פותח באמצעות Gemini AI + DuckDuckGo | © 2026<br>
        <small>הכלי מסייע ללמידה ואינו מחליף מורה או מכין שיעורי בית במקום התלמיד</small>
    </p>
""", unsafe_allow_html=True)