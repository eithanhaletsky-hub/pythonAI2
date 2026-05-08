import os
import io
import time
import urllib.request
from dotenv import load_dotenv
from google import genai
from ddgs import DDGS
from PIL import Image
import streamlit as st



# --- טעינת משתני סביבה ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- הגדרות עמוד ---
st.set_page_config(
    page_title="כלי מחקר שוק חכם",
    page_icon="🔍",
    layout="wide"
)

# --- עיצוב CSS ---
st.markdown("""
    <style>
        body { direction: rtl; }
        .main { background-color: #f0f4f8; }
        .stButton>button {
            background-color: #1a73e8;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .report-box {
            background-color: white;
            border-radius: 12px;
            padding: 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .source-link {
            background: white;
            border-left: 4px solid #1a73e8;
            padding: 10px 15px;
            margin: 6px 0;
            border-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .chat-user {
            background: #e8f0fe;
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
            border-left: 3px solid #1a73e8;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
    </style>
""", unsafe_allow_html=True)


# ===================== פונקציות =====================

def search_web(query, max_results=6):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        st.error(f"שגיאה בחיפוש: {e}")
        return []


def search_images(query, max_results=6):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_results))
        return results
    except Exception:
        return []


def load_image_from_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            img_data = response.read()
        img = Image.open(io.BytesIO(img_data))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        return img
    except Exception:
        return None


def search_news(topic):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(topic, max_results=4))
        return results
    except Exception:
        return []


def call_gemini(prompt):
    """פונקציה מרכזית לקריאה ל-Gemini עם fallback אוטומטי"""
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


def summarize_with_gemini(topic, search_results):
    content = "\n".join([r.get('body', '') for r in search_results])
    prompt = f"""
אתה מומחה מחקר שוק בכיר. בהתבסס על המידע הבא על "{topic}", כתוב דוח מחקר שוק מקצועי ומפורט בעברית.

הדוח יכלול את הסעיפים הבאים:
1. 📊 סקירת שוק כללית
2. 🏆 מתחרים עיקריים
3. 📈 מגמות ועתיד השוק
4. 🎯 קהל יעד
5. 💡 המלצות אסטרטגיות

מידע שנאסף מהאינטרנט:
{content}

כתוב את הדוח בצורה ברורה, מקצועית ומפורטת. השתמש בנקודות ובכותרות משנה.
    """
    return call_gemini(prompt)


def generate_competitors_table(topic, search_results):
    """יוצר טבלת מתחרים מסודרת"""
    content = "\n".join([r.get('body', '') for r in search_results])
    prompt = f"""
בהתבסס על המידע הבא על "{topic}", צור טבלת השוואת מתחרים מפורטת.

החזר את התשובה בפורמט הבא בדיוק (CSV עם | כמפריד):
שם חברה | תיאור קצר | חוזקות | חולשות | קהל יעד | מחיר משוער

כתוב 5-6 מתחרים עיקריים. אל תוסיף שום טקסט נוסף, רק את הטבלה.
השורה הראשונה תהיה כותרות, והשורות הבאות יהיו הנתונים.

מידע:
{content}
    """
    result = call_gemini(prompt)
    return result


def parse_table(raw_table):
    """ממיר טקסט CSV ל-list of dicts"""
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


def answer_chat_question(question, report, topic, answer_style):
    """עונה על שאלות המשתמש לפי סגנון שנבחר"""

    style_instructions = {
        "קצר": "ענה בצורה קצרה וממוקדת – מקסימום 3-4 משפטים. תן את התשובה העיקרית בלבד.",
        "ארוך": "ענה בצורה מפורטת ומקיפה עם דוגמאות, נתונים וניתוח מעמיק. השתמש בנקודות וכותרות.",
        "נקודות": "ענה אך ורק בצורת נקודות (bullet points) ממוספרות. כל נקודה – משפט אחד.",
        "טבלה": "ענה בצורת טבלה מסודרת עם עמודות רלוונטיות לשאלה. השתמש בפורמט Markdown.",
    }

    instruction = style_instructions.get(answer_style, style_instructions["קצר"])

    prompt = f"""
אתה מומחה מחקר שוק. המשתמש קרא דוח על הנושא: "{topic}".

להלן הדוח שנוצר:
{report}

שאלת המשתמש: {question}

הוראות תשובה: {instruction}

ענה בעברית בלבד. אל תוסיף הקדמות כמו "בהתבסס על הדוח" – פשוט ענה ישירות.
    """
    return call_gemini(prompt)


# ===================== פונקציית השוואה =====================

def compare_topics(topic_a, topic_b, results_a, results_b):
    content_a = "\n".join([r.get('body', '') for r in results_a])
    content_b = "\n".join([r.get('body', '') for r in results_b])
    prompt = f"""
אתה מומחה מחקר שוק. השווה בין שני נושאים.

נושא א': {topic_a}
נושא ב': {topic_b}

מידע על נושא א': {content_a}
מידע על נושא ב': {content_b}

צור טבלת השוואה בפורמט (| כמפריד):
קריטריון | {topic_a} | {topic_b}

כלול: גודל שוק, צמיחה, תחרותיות, קהל יעד, רמת כניסה, פוטנציאל

לאחר הטבלה כתוב 3-4 משפטי סיכום השוואתי בעברית.
    """
    return call_gemini(prompt)


# ===================== ממשק ראשי =====================

# אתחול היסטוריה
if "search_history" not in st.session_state:
    st.session_state["search_history"] = []

# לוגו מעוצב ב-CSS (ללא Pillow)
st.markdown("""
    <div style='background: linear-gradient(135deg, #1a73e8, #0d47a1);
                padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>
            🔍 כלי מחקר שוק חכם
        </h1>
        <p style='color: #cce0ff; margin: 5px 0 0 0; font-size: 1.1em;'>AI Market Research Tool | מבוסס Gemini + DuckDuckGo</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("#### קבל דוח מחקר שוק מקצועי תוך שניות")
st.markdown("---")

# ===================== טאבים =====================
tab1, tab2, tab3 = st.tabs(["🔍 מחקר שוק", "⚖️ השווה שני נושאים", "🕓 היסטוריית חיפושים"])


# ==================== טאב 1: מחקר שוק ====================
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "🔎 הכנס נושא או תחום לחקירה:",
            placeholder="לדוגמה: קפה קר בישראל, אפליקציות כושר, רהיטים מעוצבים...",
            key="topic_main"
        )
    with col2:
        num_results = st.slider("כמות תוצאות חיפוש", min_value=3, max_value=10, value=6)

    if st.button("🚀 צור דוח מחקר"):
        if not topic.strip():
            st.warning("אנא הכנס נושא לחיפוש.")
        else:
            with st.spinner("🔎 מחפש מידע, תמונות וחדשות..."):
                results = search_web(topic, max_results=num_results)
                images = search_images(topic, max_results=6)
                news = search_news(topic)

            if not results:
                st.error("לא נמצאו תוצאות. נסה נושא אחר.")
            else:
                with st.spinner("🧠 מנתח ומסכם עם AI..."):
                    report = summarize_with_gemini(topic, results)
                with st.spinner("📊 בונה טבלת מתחרים..."):
                    raw_table = generate_competitors_table(topic, results)

                if report:
                    st.session_state["report"] = report
                    st.session_state["topic"] = topic
                    st.session_state["chat_history"] = []

                    # שמור להיסטוריה
                    import datetime
                    st.session_state["search_history"].append({
                        "topic": topic,
                        "report": report,
                        "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    })

                    st.success("✅ הדוח מוכן!")
                    st.markdown("---")

                    # ===== דוח =====
                    st.markdown("## 📄 דוח מחקר שוק")
                    st.markdown(f'<div class="report-box">{report}</div>', unsafe_allow_html=True)
                    st.markdown("---")

                    # ===== טבלת מתחרים =====
                    st.markdown("## 🏆 השוואת מתחרים")
                    if raw_table:
                        headers, rows = parse_table(raw_table)
                        if headers and rows:
                            table_html = """
                            <style>
                            .comp-table { width:100%; border-collapse:collapse; font-size:0.9em; }
                            .comp-table th { background:#1a73e8; color:white; padding:10px; text-align:right; }
                            .comp-table td { padding:9px 12px; border-bottom:1px solid #e0e0e0; text-align:right; }
                            .comp-table tr:nth-child(even) { background:#f8f9fa; }
                            .comp-table tr:hover { background:#e8f0fe; }
                            </style>
                            <table class='comp-table'><thead><tr>
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
                            st.markdown(raw_table)
                    st.markdown("---")

                    # ===== תמונות =====
                    if images:
                        st.markdown("## 🖼️ תמונות רלוונטיות")
                        loaded_images = []
                        for img_result in images:
                            img = load_image_from_url(img_result.get('image', ''))
                            if img:
                                loaded_images.append((img, img_result.get('title', ''), img_result.get('url', '')))
                            if len(loaded_images) == 6:
                                break
                        if loaded_images:
                            cols = st.columns(3)
                            for i, (img, title, url) in enumerate(loaded_images):
                                with cols[i % 3]:
                                    st.image(img, caption=title[:60] if title else "", use_container_width=True)
                                    if url:
                                        st.markdown(f"[🔗 מקור]({url})")
                        st.markdown("---")

                    # ===== מקורות =====
                    st.markdown("## 🔗 מקורות מידע")
                    for i, result in enumerate(results, 1):
                        title = result.get('title', 'ללא כותרת')
                        url = result.get('href', '')
                        body = result.get('body', '')[:120]
                        if url:
                            st.markdown(
                                f'<div class="source-link"><b>{i}. <a href="{url}" target="_blank">{title}</a></b><br>'
                                f'<small style="color:gray">{body}...</small></div>',
                                unsafe_allow_html=True
                            )
                    st.markdown("---")

                    # ===== חדשות =====
                    if news:
                        st.markdown("## 📰 חדשות עדכניות")
                        for item in news:
                            with st.expander(f"📌 {item.get('title', 'ללא כותרת')}"):
                                st.write(item.get('body', ''))
                                if item.get('url'):
                                    st.markdown(f"[קרא עוד ←]({item['url']})")
                        st.markdown("---")

                    # ===== הורדה =====
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button("📥 הורד דוח (TXT)", report.encode("utf-8"),
                                           f"דוח_שוק_{topic}.txt", mime="text/plain")
                    with col_b:
                        st.download_button("📋 הורד דוח (Markdown)", report.encode("utf-8"),
                                           f"דוח_שוק_{topic}.md", mime="text/markdown")

    # ===== צ'אט =====
    if "report" in st.session_state and st.session_state["report"]:
        st.markdown("---")
        st.markdown("## 💬 שאל את ה-AI על הדוח")
        col_style, col_q = st.columns([1, 3])
        with col_style:
            answer_style = st.radio("📝 סגנון תשובה:",
                                    options=["קצר", "ארוך", "נקודות", "טבלה"], index=0)
        with col_q:
            user_question = st.text_input("✍️ שאלתך:",
                placeholder="לדוגמה: מה ההמלצה הכי חשובה? / מי המתחרה החזק ביותר?")
            send = st.button("📨 שלח שאלה")

        if send and user_question.strip():
            with st.spinner("🤔 ה-AI חושב..."):
                answer = answer_chat_question(
                    user_question, st.session_state["report"],
                    st.session_state["topic"], answer_style
                )
            if answer:
                if "chat_history" not in st.session_state:
                    st.session_state["chat_history"] = []
                st.session_state["chat_history"].append(
                    {"question": user_question, "answer": answer, "style": answer_style}
                )

        if st.session_state.get("chat_history"):
            st.markdown("### 🗂️ היסטוריית שיחה")
            for chat in reversed(st.session_state["chat_history"]):
                st.markdown(
                    f'<div class="chat-user">🧑 <b>{chat["question"]}</b> '
                    f'<span style="color:#888; font-size:0.8em">[{chat["style"]}]</span></div>',
                    unsafe_allow_html=True
                )
                st.markdown(f'<div class="chat-ai">🤖 {chat["answer"]}</div>', unsafe_allow_html=True)
            if st.button("🗑️ נקה שיחה"):
                st.session_state["chat_history"] = []
                st.rerun()


# ==================== טאב 2: השוואת נושאים ====================
with tab2:
    st.markdown("### ⚖️ השווה בין שני נושאים")
    st.markdown("הכנס שני נושאים והכלי יייצר טבלת השוואה מקיפה ביניהם.")

    col_a, col_b = st.columns(2)
    with col_a:
        topic_a = st.text_input("🅰️ נושא ראשון:", placeholder="לדוגמה: קפה קר", key="compare_a")
    with col_b:
        topic_b = st.text_input("🅱️ נושא שני:", placeholder="לדוגמה: מיצים טבעיים", key="compare_b")

    if st.button("⚖️ השווה בין הנושאים"):
        if not topic_a.strip() or not topic_b.strip():
            st.warning("אנא הכנס שני נושאים להשוואה.")
        else:
            with st.spinner(f"🔎 מחפש מידע על {topic_a}..."):
                results_a = search_web(topic_a, max_results=5)
            with st.spinner(f"🔎 מחפש מידע על {topic_b}..."):
                results_b = search_web(topic_b, max_results=5)
            with st.spinner("🧠 מנתח ומשווה..."):
                comparison = compare_topics(topic_a, topic_b, results_a, results_b)

            if comparison:
                st.success("✅ ההשוואה מוכנה!")
                st.markdown("---")

                # חלק את הפלט לטבלה + סיכום
                lines = comparison.strip().split("\n")
                table_lines = [l for l in lines if "|" in l]
                summary_lines = [l for l in lines if "|" not in l and l.strip()]

                # טבלה
                if table_lines:
                    st.markdown("## 📊 טבלת השוואה")
                    headers, rows = parse_table("\n".join(table_lines))
                    if headers and rows:
                        table_html = """
                        <style>
                        .cmp-table { width:100%; border-collapse:collapse; font-size:0.9em; }
                        .cmp-table th { background:#6a1b9a; color:white; padding:10px; text-align:right; }
                        .cmp-table td { padding:9px 12px; border-bottom:1px solid #e0e0e0; text-align:right; }
                        .cmp-table tr:nth-child(even) { background:#f3e5f5; }
                        .cmp-table tr:hover { background:#e1bee7; }
                        </style>
                        <table class='cmp-table'><thead><tr>
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

                # סיכום
                if summary_lines:
                    st.markdown("---")
                    st.markdown("## 💡 סיכום השוואתי")
                    st.markdown(
                        f'<div class="report-box">{"<br>".join(summary_lines)}</div>',
                        unsafe_allow_html=True
                    )

                # הורדה
                st.markdown("---")
                st.download_button(
                    "📥 הורד השוואה (TXT)",
                    comparison.encode("utf-8"),
                    f"השוואה_{topic_a}_vs_{topic_b}.txt",
                    mime="text/plain"
                )


# ==================== טאב 3: היסטוריית חיפושים ====================
with tab3:
    st.markdown("### 🕓 היסטוריית חיפושים")
    st.markdown("כל הדוחות שיצרת בסשן הנוכחי – לחץ על נושא לצפייה מחדש.")

    history = st.session_state.get("search_history", [])

    if not history:
        st.info("עדיין לא ביצעת חיפושים בסשן זה. עבור לטאב 'מחקר שוק' כדי להתחיל.")
    else:
        st.markdown(f"**סה\"כ חיפושים: {len(history)}**")
        st.markdown("---")

        for i, item in enumerate(reversed(history)):
            idx = len(history) - i
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f'<div style="background:white; border-radius:8px; padding:12px; '
                    f'margin:6px 0; box-shadow:0 1px 4px rgba(0,0,0,0.08);">'
                    f'<b>#{idx} {item["topic"]}</b> '
                    f'<span style="color:gray; font-size:0.85em">🕐 {item["time"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_btn:
                if st.button("📂 פתח", key=f"open_{i}"):
                    st.session_state["report"] = item["report"]
                    st.session_state["topic"] = item["topic"]
                    st.session_state["chat_history"] = []
                    st.markdown("---")
                    st.markdown(f"## 📄 דוח: {item['topic']}")
                    st.markdown(f'<div class="report-box">{item["report"]}</div>', unsafe_allow_html=True)
                    st.download_button(
                        "📥 הורד דוח",
                        item["report"].encode("utf-8"),
                        f"דוח_{item['topic']}.txt",
                        mime="text/plain",
                        key=f"dl_{i}"
                    )

        st.markdown("---")
        if st.button("🗑️ נקה היסטוריה"):
            st.session_state["search_history"] = []
            st.rerun()


# --- פוטר ---
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:gray;'>פותח באמצעות Gemini AI + DuckDuckGo | © 2026</p>",
    unsafe_allow_html=True
)