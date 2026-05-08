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
    page_title="סוכן מידע פיננסי",
    page_icon="📈",
    layout="wide"
)

# --- עיצוב CSS ---
st.markdown("""
    <style>
        body { direction: rtl; }
        .disclaimer-box {
            background: #fff3cd;
            border: 2px solid #ff6b00;
            border-radius: 10px;
            padding: 15px 20px;
            margin: 10px 0 20px 0;
        }
        .disclaimer-title {
            color: #cc0000;
            font-size: 1.1em;
            font-weight: bold;
        }
        .report-box {
            background-color: white;
            border-radius: 12px;
            padding: 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .source-link {
            background: white;
            border-left: 4px solid #2e7d32;
            padding: 10px 15px;
            margin: 6px 0;
            border-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .stButton>button {
            background-color: #2e7d32;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .chat-user {
            background: #e8f5e9;
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
            border-left: 3px solid #2e7d32;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .warning-inline {
            color: #cc0000;
            font-size: 0.85em;
            font-style: italic;
        }
    </style>
""", unsafe_allow_html=True)


# ===================== כתב ויתור =====================
def show_disclaimer(location="top"):
    st.markdown("""
        <div class="disclaimer-box">
            <div class="disclaimer-title">⚠️ הצהרת אחריות חשובה – חובה לקרוא</div>
            <p>
            🔴 <b>האתר וה-AI אינם יועצי השקעות מורשים.</b><br>
            🔴 המידע המוצג כאן הוא <b>לצרכי מידע כללי בלבד</b> ואינו מהווה בשום אופן ייעוץ השקעות, ייעוץ פיננסי, או המלצה לביצוע פעולה כלשהי בשוק ההון.<br>
            🔴 ה-AI <b>אוסף ומסכם מידע ציבורי בלבד</b> – הוא אינו מנתח את מצבך הפיננסי האישי ואינו ממליץ על השקעות ספציפיות.<br>
            🔴 <b>לפני כל החלטת השקעה</b> – יש להתייעץ עם יועץ השקעות מורשה על ידי רשות ניירות ערך.<br>
            🔴 <b>השקעות כרוכות בסיכון</b> – ייתכן הפסד של חלק מהכסף או כולו.
            </p>
        </div>
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
    st.error("❌ כל המודלים לא זמינים כרגע. נסה שוב מאוחר יותר.")
    return None


def search_financial_data(query, max_results=8):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        st.error(f"שגיאה בחיפוש: {e}")
        return []


def search_financial_news(query, max_results=5):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        return results
    except Exception:
        return []


def generate_market_report(country, sector, time_period, risk_level, results):
    """מייצר דוח מידע על שוק ספציפי"""
    content = "\n".join([r.get('body', '') for r in results])

    prompt = f"""
אתה סוכן מידע פיננסי שתפקידו לאסוף ולסכם מידע ציבורי בלבד.

⚠️ חשוב מאוד: אינך יועץ השקעות. אינך ממליץ על השקעות ספציפיות.
תפקידך הוא לסכם מידע ציבורי בלבד בצורה ברורה ומאורגנת.

פרמטרים שהמשתמש ביקש לחקור:
- מדינה/אזור: {country}
- סקטור: {sector}
- פרק זמן: {time_period}
- רמת סיכון שמעניינת אותו: {risk_level}

המידע שנאסף מהאינטרנט:
{content}

צור סיכום מידע מפורט הכולל:

1. 📊 סקירת השוק ב{country} – מה קורה כיום
2. 📈 נתוני צמיחה בסקטור {sector} ב{time_period} האחרון/ים
3. 🔍 גורמים עיקריים המשפיעים על השוק
4. ⚠️ סיכונים ידועים באזור זה
5. 📰 מגמות עדכניות

בסיום הסיכום, הוסף בבירור:
"⚠️ תזכורת: מסמך זה הוא סיכום מידע ציבורי בלבד. אינו מהווה ייעוץ השקעות. יש להתייעץ עם יועץ מורשה."

כתוב בעברית, בצורה ברורה ומקצועית.
    """
    return call_gemini(prompt)


def generate_comparison_table(countries, sector, time_period, results):
    """מייצר טבלת השוואה בין שווקים"""
    content = "\n".join([r.get('body', '') for r in results])

    prompt = f"""
אתה סוכן מידע פיננסי. סכם מידע ציבורי על שווקים שונים בצורת טבלה.
אינך יועץ השקעות ואינך ממליץ על השקעות.

השווקים לבדיקה: {", ".join(countries)}
סקטור: {sector}
פרק זמן: {time_period}

מידע שנאסף:
{content}

צור טבלת השוואה בפורמט הבא בדיוק (השתמש | כמפריד):
מדינה/שוק | צמיחה משוערת | יציבות | סיכון עיקרי | מגמה | מידע נוסף

כתוב נתונים ל-{len(countries)} שווקים.
אל תוסיף שום טקסט נוסף – רק את הטבלה.
    """
    return call_gemini(prompt)


def parse_table(raw_table):
    lines = [l.strip() for l in raw_table.strip().split("\n") if l.strip() and "|" in l]
    if len(lines) < 2:
        return None, None
    headers = [h.strip() for h in lines[0].split("|")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return headers, rows


def answer_financial_question(question, report, context, answer_style):
    style_instructions = {
        "קצר": "ענה בצורה קצרה וממוקדת – מקסימום 3-4 משפטים.",
        "ארוך": "ענה בצורה מפורטת עם נתונים, הסברים ודוגמאות.",
        "נקודות": "ענה אך ורק בצורת נקודות ממוספרות. כל נקודה – משפט אחד.",
        "טבלה": "ענה בצורת טבלה מסודרת עם עמודות רלוונטיות בפורמט Markdown.",
    }
    instruction = style_instructions.get(answer_style, style_instructions["קצר"])

    prompt = f"""
אתה סוכן מידע פיננסי שתפקידו לסכם מידע ציבורי בלבד.

⚠️ חשוב: אינך יועץ השקעות. אינך ממליץ על השקעות ספציפיות לאדם זה.
אם המשתמש מבקש המלצה אישית – הסבר בנחתיות שאינך יועץ והפנה אותו לפנות ליועץ מורשה.

הקשר המחקר: {context}

הדוח שנוצר:
{report}

שאלת המשתמש: {question}

הוראות תשובה: {instruction}

בסוף כל תשובה הוסף בשורה נפרדת:
"⚠️ תזכורת: זהו מידע כללי בלבד – לא ייעוץ השקעות."

ענה בעברית בלבד.
    """
    return call_gemini(prompt)


# ===================== ממשק ראשי =====================

# כותרת
st.markdown("""
    <div style='background: linear-gradient(135deg, #1b5e20, #2e7d32);
                padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>
            📈 סוכן מידע פיננסי חכם
        </h1>
        <p style='color: #c8e6c9; margin: 5px 0 0 0; font-size: 1.1em;'>
            Financial Market Intelligence | מבוסס Gemini AI + DuckDuckGo
        </p>
    </div>
""", unsafe_allow_html=True)

# ===== כתב ויתור ראשי =====
show_disclaimer("top")

st.markdown("---")

# ===================== פרמטרי חיפוש =====================
st.markdown("## ⚙️ הגדר את פרמטרי המחקר")

col1, col2 = st.columns(2)

with col1:
    countries = st.multiselect(
        "🌍 בחר מדינות / שווקים לבדיקה:",
        ["ישראל", "ארה\"ב", "אירופה", "סין", "יפן", "הודו",
         "ברזיל", "גרמניה", "בריטניה", "קנדה", "אוסטרליה", "דרום קוריאה"],
        default=["ישראל", "ארה\"ב"]
    )

    sector = st.selectbox(
        "🏭 סקטור:",
        ["טכנולוגיה", "אנרגיה", "נדל\"ן", "בריאות", "פיננסים",
         "תעשייה", "צריכה", "תקשורת", "חקלאות", "תשתיות", "כללי"]
    )

with col2:
    time_period = st.selectbox(
        "⏱️ פרק זמן לבדיקה:",
        ["שבוע אחרון", "חודש אחרון", "רבעון אחרון",
         "חצי שנה אחרונה", "שנה אחרונה", "3 שנים אחרונות"]
    )

    risk_level = st.select_slider(
        "⚖️ רמת סיכון שמעניינת אותך (למידע בלבד):",
        options=["שמרני מאוד", "שמרני", "מאוזן", "אגרסיבי", "אגרסיבי מאוד"],
        value="מאוזן"
    )

st.caption("⚠️ רמת הסיכון משמשת לסינון מידע בלבד – אין בכך המלצה להשקיע ברמת סיכון זו.")

st.markdown("---")

# ===================== כפתור חיפוש =====================
if st.button("🔍 בצע מחקר שוק"):
    if not countries:
        st.warning("אנא בחר לפחות מדינה אחת.")
    else:
        primary_country = countries[0]
        search_query = f"{sector} stock market {primary_country} {time_period} growth 2025"
        news_query = f"{sector} market {' '.join(countries)} financial news"

        with st.spinner("🔎 מחפש נתונים פיננסיים עדכניים..."):
            results = search_financial_data(search_query, max_results=8)
            news = search_financial_news(news_query, max_results=5)

        if not results:
            st.error("לא נמצאו תוצאות. נסה פרמטרים שונים.")
        else:
            with st.spinner("🧠 מנתח ומסכם מידע..."):
                report = generate_market_report(
                    primary_country, sector, time_period, risk_level, results
                )

            comp_table_raw = None
            if len(countries) > 1:
                with st.spinner("📊 בונה טבלת השוואה בין שווקים..."):
                    comp_query = f"{sector} market comparison {' vs '.join(countries)} {time_period}"
                    comp_results = search_financial_data(comp_query, max_results=6)
                    comp_table_raw = generate_comparison_table(
                        countries, sector, time_period, comp_results
                    )

            if report:
                # שמור ב-session
                st.session_state["fin_report"] = report
                st.session_state["fin_context"] = f"{sector} | {', '.join(countries)} | {time_period}"
                st.session_state["fin_chat"] = []

                st.success("✅ המחקר הושלם!")

                # ===== כתב ויתור לפני הדוח =====
                st.markdown("---")
                show_disclaimer("before_report")

                # ===== דוח =====
                st.markdown("## 📄 סיכום מידע שוק")
                st.markdown(
                    f'<div class="report-box">{report}</div>',
                    unsafe_allow_html=True
                )

                # ===== טבלת השוואה =====
                if comp_table_raw and len(countries) > 1:
                    st.markdown("---")
                    st.markdown("## 🌍 השוואה בין שווקים")
                    st.caption("⚠️ הנתונים מבוססים על מידע ציבורי ואינם מדויקים לצורך ביצוע השקעות.")

                    headers, rows = parse_table(comp_table_raw)
                    if headers and rows:
                        table_html = """
                        <style>
                        .fin-table { width:100%; border-collapse:collapse; font-size:0.9em; }
                        .fin-table th { background:#2e7d32; color:white; padding:10px; text-align:right; }
                        .fin-table td { padding:9px 12px; border-bottom:1px solid #e0e0e0; text-align:right; }
                        .fin-table tr:nth-child(even) { background:#f1f8e9; }
                        .fin-table tr:hover { background:#dcedc8; }
                        </style>
                        <table class='fin-table'><thead><tr>
                        """
                        for h in headers:
                            table_html += f"<th>{h}</th>"
                        table_html += "</tr></thead><tbody>"
                        for row in rows:
                            table_html += "<tr>"
                            for h in headers:
                                table_html += f"<td>{row.get(h, '')}</td>"
                            table_html += "</tr>"
                        table_html += "</tbody></table>"
                        st.markdown(table_html, unsafe_allow_html=True)
                    else:
                        st.markdown(comp_table_raw)

                # ===== חדשות =====
                if news:
                    st.markdown("---")
                    st.markdown("## 📰 חדשות פיננסיות עדכניות")
                    for item in news:
                        with st.expander(f"📌 {item.get('title', 'ללא כותרת')}"):
                            st.write(item.get('body', ''))
                            if item.get('url'):
                                st.markdown(f"[קרא עוד ←]({item['url']})")

                # ===== מקורות =====
                st.markdown("---")
                st.markdown("## 🔗 מקורות מידע")
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'ללא כותרת')
                    url = result.get('href', '')
                    body = result.get('body', '')[:120]
                    if url:
                        st.markdown(
                            f'<div class="source-link">'
                            f'<b>{i}. <a href="{url}" target="_blank">{title}</a></b><br>'
                            f'<small style="color:gray">{body}...</small>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                # ===== הורדה =====
                st.markdown("---")
                st.download_button(
                    label="📥 הורד סיכום מידע (TXT)",
                    data=report.encode("utf-8"),
                    file_name=f"מידע_שוק_{sector}_{primary_country}.txt",
                    mime="text/plain"
                )

# ===================== צ'אט אישי מותאם =====================
if "fin_report" in st.session_state and st.session_state["fin_report"]:
    st.markdown("---")
    st.markdown("## 🎯 סוכן מידע אישי מותאם")
    st.markdown("ענה על מספר שאלות קצרות כדי שהסוכן יוכל לתת לך מידע **מכוון ומותאם** עבורך.")

    st.markdown("""
        <div style='background:#ffebee; border:1px solid #ef9a9a;
                    border-radius:8px; padding:10px 15px; margin-bottom:20px;'>
            ⚠️ <b>תזכורת:</b> הסוכן מספק <b>מידע כללי בלבד</b> ואינו יועץ השקעות מורשה.
            אל תבסס החלטות פיננסיות על תשובותיו. יש להתייעץ עם יועץ מורשה.
        </div>
    """, unsafe_allow_html=True)

    # ===== פרופיל המשתמש =====
    st.markdown("### 👤 פרופיל המשתמש")

    col1, col2, col3 = st.columns(3)

    with col1:
        investment_type = st.radio(
            "📌 סגנון השקעה מועדף:",
            options=["פסיבי", "אקטיבי", "מעורב"],
            help="פסיבי = קרנות מחקות/ETF | אקטיבי = מניות בודדות, מסחר תכוף"
        )

        preferred_exchange = st.multiselect(
            "🏦 בורסות מועדפות:",
            ["NYSE (ניו יורק)", "NASDAQ", "תל אביב (TASE)", "לונדון (LSE)",
             "טוקיו (TSE)", "שנגחאי (SSE)", "פרנקפורט (FSE)", "כל הבורסות"],
            default=["NASDAQ"]
        )

    with col2:
        investment_horizon = st.select_slider(
            "⏳ אופק השקעה:",
            options=["פחות מ-6 חודשים", "6-12 חודשים", "1-3 שנים",
                     "3-5 שנים", "5-10 שנים", "מעל 10 שנים"],
            value="1-3 שנים"
        )

        investment_goal = st.selectbox(
            "🎯 מטרת ההשקעה:",
            ["צמיחת הון", "הכנסה שוטפת (דיבידנדים)", "שמירת ערך",
             "פנסיה / חיסכון לטווח ארוך", "ספקולציה / סיכון גבוה"]
        )

    with col3:
        answer_length = st.radio(
            "📝 אורך תשובה מועדף:",
            options=["קצר ותמציתי", "בינוני", "מפורט ומעמיק"],
            index=1
        )

        answer_format = st.radio(
            "🗂️ פורמט תשובה:",
            options=["טקסט רגיל", "נקודות", "טבלה"],
            index=1
        )

    st.markdown("---")

    # ===== שאלה חופשית =====
    st.markdown("### ✍️ שאלתך האישית")
    user_question = st.text_input(
        "מה תרצה לדעת?",
        placeholder="לדוגמה: אילו ETF מחקות צומחות? / מה קורה בנאסד\"ק לאחרונה? / אילו סקטורים פעילים?"
    )

    send_personal = st.button("📨 קבל מידע מותאם אישית")

    if send_personal and user_question.strip():

        # בנה הקשר אישי מלא
        exchanges_str = ", ".join(preferred_exchange) if preferred_exchange else "לא צוין"

        length_map = {
            "קצר ותמציתי": "ענה בקצרה – מקסימום 4 משפטים. תן רק את העיקר.",
            "בינוני": "ענה בצורה בינונית – כ-2 פסקאות עם הנקודות החשובות.",
            "מפורט ומעמיק": "ענה בפירוט רב – כלול נתונים, הסברים, דוגמאות וניתוח מעמיק."
        }
        format_map = {
            "טקסט רגיל": "כתוב בפסקאות רגילות.",
            "נקודות": "כתוב אך ורק בצורת נקודות ממוספרות.",
            "טבלה": "הצג את המידע בצורת טבלה Markdown עם עמודות רלוונטיות."
        }

        personal_prompt = f"""
אתה סוכן מידע פיננסי. תפקידך לסכם מידע ציבורי בלבד בצורה מותאמת למשתמש.
⚠️ אינך יועץ השקעות. אינך ממליץ על השקעות ספציפיות. אם נשאל – הפנה ליועץ מורשה.

פרופיל המשתמש שעל בסיסו תתאים את המידע:
- סגנון השקעה מועדף: {investment_type}
- בורסות מועדפות: {exchanges_str}
- אופק השקעה: {investment_horizon}
- מטרת ההשקעה: {investment_goal}

הדוח שנוצר על הנושא:
{st.session_state["fin_report"]}

שאלת המשתמש: {user_question}

הוראות תשובה:
- {length_map[answer_length]}
- {format_map[answer_format]}
- התאם את המידע לפרופיל המשתמש – אם הוא פסיבי, דגש על ETF/קרנות. אם אקטיבי, דגש על מניות ומגמות.
- התייחס לבורסות שציין אם רלוונטי.
- התייחס לאופק הזמן שלו.
- כתוב בעברית בלבד.
- בסוף הוסף: "⚠️ מידע כללי בלבד – אינו ייעוץ השקעות."
        """

        with st.spinner("🤔 הסוכן מכין מידע מותאם אישית..."):
            answer = call_gemini(personal_prompt)

        if answer:
            if "fin_personal_chat" not in st.session_state:
                st.session_state["fin_personal_chat"] = []
            st.session_state["fin_personal_chat"].append({
                "question": user_question,
                "answer": answer,
                "profile": f"{investment_type} | {exchanges_str} | {investment_horizon} | {investment_goal}",
                "format": f"{answer_length} + {answer_format}"
            })

    # הצג היסטוריית שיחה אישית
    if st.session_state.get("fin_personal_chat"):
        st.markdown("### 🗂️ היסטוריית מידע אישי")
        for chat in reversed(st.session_state["fin_personal_chat"]):
            st.markdown(
                f'<div class="chat-user">'
                f'🧑 <b>{chat["question"]}</b><br>'
                f'<span style="color:#666; font-size:0.8em">👤 פרופיל: {chat["profile"]} | 📝 {chat["format"]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="chat-ai">🤖 {chat["answer"]}</div>',
                unsafe_allow_html=True
            )

        if st.button("🗑️ נקה היסטוריה אישית"):
            st.session_state["fin_personal_chat"] = []
            st.rerun()

# ===== כתב ויתור תחתון =====
st.markdown("---")
show_disclaimer("bottom")
st.markdown(
    "<p style='text-align:center; color:gray;'>"
    "סוכן מידע פיננסי | פותח באמצעות Gemini AI + DuckDuckGo | © 2026<br>"
    "<b style='color:#cc0000;'>אינו מהווה ייעוץ השקעות בשום צורה</b>"
    "</p>",
    unsafe_allow_html=True
)