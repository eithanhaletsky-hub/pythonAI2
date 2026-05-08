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
    page_title="מתכנן טיולים חכם",
    page_icon="🧳",
    layout="wide"
)

st.markdown("""
    <style>
        body { direction: rtl; }
        .stButton>button {
            background-color: #e65100;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .plan-box {
            background: white;
            border-radius: 12px;
            padding: 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            line-height: 1.9;
            border-top: 4px solid #e65100;
        }
        .tip-box {
            background: #fff3e0;
            border-radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
            border-right: 3px solid #e65100;
        }
        .source-link {
            background: white;
            border-left: 4px solid #e65100;
            padding: 10px 15px;
            margin: 6px 0;
            border-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .chat-user {
            background: #fff3e0;
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
            border-left: 3px solid #e65100;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .budget-box {
            background: #e8f5e9;
            border-radius: 10px;
            padding: 15px 20px;
            text-align: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
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
                response = client.models.generate_content(model=model, contents=prompt)
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
    st.error("❌ כל המודלים לא זמינים. נסה שוב.")
    return None


def search_web(query, max_results=6):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        return []


def search_images(query, max_results=6):
    try:
        with DDGS() as ddgs:
            return list(ddgs.images(query, max_results=max_results))
    except Exception:
        return []


def search_news(query, max_results=4):
    try:
        with DDGS() as ddgs:
            return list(ddgs.news(query, max_results=max_results))
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


def generate_trip_plan(data, attractions_info, food_info, tips_info):
    """מייצר תוכנית טיול מפורטת"""
    attractions_text = "\n".join([r.get('body', '') for r in attractions_info[:4]])
    food_text = "\n".join([r.get('body', '') for r in food_info[:3]])
    tips_text = "\n".join([r.get('body', '') for r in tips_info[:3]])

    budget_per_day = data['budget'] // data['days'] if data['days'] > 0 else data['budget']

    prompt = f"""
אתה מתכנן טיולים מומחה. צור תוכנית טיול מפורטת ומעשית.

פרטי הטיול:
- יעד: {data['destination']}
- ממתי: {data['start_date']} | עד: {data['end_date']}
- מספר ימים: {data['days']}
- מספר מטיילים: {data['travelers']}
- סוג מטיילים: {data['traveler_type']}
- תקציב כולל: {data['budget']:,} {data['currency']}
- תקציב ליום: {budget_per_day:,} {data['currency']}
- סגנון טיול: {data['style']}
- תחומי עניין: {', '.join(data['interests'])}
- מגבלות / העדפות: {data.get('restrictions', 'אין')}

מידע על אטרקציות שנאסף מהאינטרנט:
{attractions_text}

מידע על אוכל ומסעדות:
{food_text}

טיפים ומידע מעשי:
{tips_text}

צור תוכנית טיול מלאה הכוללת:

## 🗓️ תוכנית יומית מפורטת
לכל יום כתוב:
- בוקר / צהריים / ערב – פעילויות ספציפיות
- המלצות אוכל (מסעדות / שווקים)
- זמני נסיעה משוערים
- עלויות משוערות ליום

## 💰 פירוט תקציב משוער
חלק את התקציב לקטגוריות: לינה, אוכל, תחבורה, אטרקציות, קניות, מזדמן

## 🎒 מה לארוז – רשימה
בהתאם ליעד, לעונה ולסגנון הטיול

## 📋 טיפים חשובים ליעד
ויזה, מטבע, בטיחות, תרבות מקומית, תחבורה

## ⚠️ דברים שחשוב לדעת
טיפים ספציפיים שנמצאו עבור {data['destination']}

כתוב בעברית בצורה מפורטת ומעשית.
    """
    return call_gemini(prompt)


def answer_trip_question(question, plan, destination, answer_style):
    style_map = {
        "קצר": "ענה ב-3-4 משפטים.",
        "מפורט": "ענה בפירוט עם דוגמאות.",
        "נקודות": "ענה בנקודות ממוספרות בלבד.",
        "טבלה": "ענה בצורת טבלה Markdown.",
    }
    prompt = f"""
אתה מתכנן טיולים מומחה ליעד {destination}.
תוכנית הטיול: {plan}
שאלה: {question}
{style_map.get(answer_style, style_map['קצר'])}
כתוב בעברית בלבד.
    """
    return call_gemini(prompt)


# ===================== ממשק ראשי =====================

st.markdown("""
    <div style='background: linear-gradient(135deg, #bf360c, #e65100, #ff8f00);
                padding: 28px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>🧳 מתכנן טיולים חכם</h1>
        <p style='color: #ffe0b2; margin: 8px 0 0 0; font-size: 1.1em;'>
            תכנן את הטיול המושלם שלך | מבוסס Gemini AI + DuckDuckGo
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===================== טאבים =====================
tab1, tab2, tab3 = st.tabs([
    "✈️ תכנן טיול",
    "🖼️ גלה את היעד",
    "💬 שאל מומחה טיולים"
])


# ==================== טאב 1: תכנן טיול ====================
with tab1:
    st.markdown("## ✈️ פרטי הטיול")

    # --- פרטים בסיסיים ---
    col1, col2, col3 = st.columns(3)
    with col1:
        destination = st.text_input("🌍 יעד הטיול:",
            placeholder="לדוגמה: טוקיו, יפן / ברצלונה, ספרד", key="dest")
        traveler_type = st.selectbox("👥 סוג מטיילים:", [
            "זוג", "משפחה עם ילדים", "חברים", "סולו",
            "קבוצה גדולה", "הורים וילדים גדולים"
        ], key="trav_type")

    with col2:
        import datetime
        start_date = st.date_input("📅 תאריך יציאה:",
            value=datetime.date.today() + datetime.timedelta(days=30), key="start")
        end_date = st.date_input("📅 תאריך חזרה:",
            value=datetime.date.today() + datetime.timedelta(days=37), key="end")
        days = (end_date - start_date).days
        st.metric("⏳ מספר ימים:", days)

    with col3:
        travelers = st.number_input("👤 מספר מטיילים:", min_value=1, max_value=20, value=2, key="travelers")
        col_budget, col_currency = st.columns([2, 1])
        with col_budget:
            budget = st.number_input("💰 תקציב כולל:", min_value=0, value=10000, step=500, key="budget")
        with col_currency:
            currency = st.selectbox("מטבע:", ["₪", "$", "€", "£"], key="currency")

    if days > 0:
        budget_per_day = budget // days
        budget_per_person = budget // travelers if travelers > 0 else budget
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
                <div class="budget-box">
                    <b>תקציב ליום</b><br>
                    <span style='font-size:1.8em; font-weight:bold; color:#2e7d32;'>
                        {budget_per_day:,} {currency}
                    </span>
                </div>
            """, unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
                <div class="budget-box">
                    <b>תקציב לאדם</b><br>
                    <span style='font-size:1.8em; font-weight:bold; color:#1565c0;'>
                        {budget_per_person:,} {currency}
                    </span>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # --- סגנון ותחומי עניין ---
    col1, col2 = st.columns(2)
    with col1:
        style = st.selectbox("🎨 סגנון טיול:", [
            "תרבות ותיירות רגילה",
            "הרפתקאות וטבע",
            "מנוחה ואיפוס (חופים / ספא)",
            "גסטרונומיה ואוכל",
            "היסטוריה ואמנות",
            "מסע קולינרי + תרבות",
            "ספורט ופעילות גופנית",
        ], key="style")
    with col2:
        interests = st.multiselect("❤️ תחומי עניין:", [
            "מוזיאונים", "שווקים מקומיים", "טיולי טבע",
            "חופים", "ספורט אתגרי", "מסעדות מפורסמות",
            "חיי לילה", "קניות", "ארכיטקטורה",
            "אוכל רחוב", "גנים ופארקים", "ספות וסטריפ"
        ], default=["מוזיאונים", "שווקים מקומיים", "מסעדות מפורסמות"],
        key="interests")

    restrictions = st.text_input("⚠️ מגבלות / העדפות מיוחדות (אופציונלי):",
        placeholder="לדוגמה: טבעוני, נסיעה עם עגלה, לא מטוסים, צמחוני...",
        key="restrictions")

    st.markdown("---")

    if st.button("🚀 צור תוכנית טיול!", key="plan_btn"):
        if not destination.strip():
            st.warning("אנא הכנס יעד טיול.")
        elif days <= 0:
            st.warning("תאריך החזרה חייב להיות אחרי תאריך היציאה.")
        elif not interests:
            st.warning("אנא בחר לפחות תחום עניין אחד.")
        else:
            # חיפוש מידע עדכני
            with st.spinner(f"🔎 מחפש מידע עדכני על {destination}..."):
                attractions = search_web(f"top attractions things to do {destination} 2025", max_results=6)
                food = search_web(f"best restaurants food {destination} local cuisine 2025", max_results=4)
                tips = search_web(f"travel tips {destination} visa safety budget 2025", max_results=4)
                news = search_news(f"{destination} travel tourism 2025", max_results=3)

            st.success(f"✅ נמצא מידע עדכני על {destination}!")

            data = {
                "destination": destination,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "days": days,
                "travelers": travelers,
                "traveler_type": traveler_type,
                "budget": budget,
                "currency": currency,
                "style": style,
                "interests": interests,
                "restrictions": restrictions
            }

            with st.spinner("🧠 ה-AI בונה תוכנית טיול מותאמת אישית..."):
                plan = generate_trip_plan(data, attractions, food, tips)

            if plan:
                st.session_state["trip_plan"] = plan
                st.session_state["trip_dest"] = destination
                st.session_state["trip_chat"] = []

                st.success("✅ תוכנית הטיול מוכנה!")
                st.markdown("---")
                st.markdown(f"## 🗺️ תוכנית הטיול שלך – {destination}")
                st.markdown(f'<div class="plan-box">{plan}</div>', unsafe_allow_html=True)

                # חדשות עדכניות על היעד
                if news:
                    st.markdown("---")
                    st.markdown("## 📰 חדשות עדכניות על היעד")
                    for item in news:
                        with st.expander(f"📌 {item.get('title', '')}"):
                            st.write(item.get('body', ''))
                            if item.get('url'):
                                st.markdown(f"[קרא עוד ←]({item['url']})")

                # מקורות
                if attractions:
                    st.markdown("---")
                    st.markdown("## 🔗 מקורות מידע שנמצאו")
                    for r in (attractions + tips)[:6]:
                        if r.get('href'):
                            st.markdown(
                                f'<div class="source-link">'
                                f'<a href="{r["href"]}" target="_blank">{r.get("title", "קישור")}</a>'
                                f'</div>',
                                unsafe_allow_html=True
                            )

                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.download_button("📥 הורד תוכנית (TXT)",
                                       plan.encode("utf-8"),
                                       f"טיול_{destination}.txt", mime="text/plain")
                with col_b:
                    st.download_button("📋 הורד תוכנית (Markdown)",
                                       plan.encode("utf-8"),
                                       f"טיול_{destination}.md", mime="text/markdown")


# ==================== טאב 2: גלה את היעד ====================
with tab2:
    st.markdown("## 🖼️ גלה את היעד")
    st.markdown("חפש תמונות, אטרקציות ומידע ויזואלי על כל יעד בעולם.")

    discover_dest = st.text_input("🌍 הכנס יעד לחיפוש:",
        placeholder="לדוגמה: קיוטו יפן / סנטוריני יוון", key="discover_dest")

    discover_type = st.multiselect("🔎 מה לחפש?", [
        "📸 תמונות", "🏛️ אטרקציות מובילות",
        "🍽️ מסעדות ואוכל", "🏨 אזורי לינה מומלצים",
        "💡 עובדות מעניינות"
    ], default=["📸 תמונות", "🏛️ אטרקציות מובילות"], key="discover_type")

    if st.button("🔍 גלה!", key="discover_btn"):
        if not discover_dest.strip():
            st.warning("אנא הכנס יעד.")
        else:
            if "📸 תמונות" in discover_type:
                with st.spinner("🖼️ מחפש תמונות..."):
                    images = search_images(f"{discover_dest} travel tourism landmark", max_results=6)

                if images:
                    st.markdown("### 📸 תמונות")
                    loaded = []
                    for img_r in images:
                        img = load_image_from_url(img_r.get('image', ''))
                        if img:
                            loaded.append((img, img_r.get('title', ''), img_r.get('url', '')))
                        if len(loaded) == 6:
                            break
                    if loaded:
                        cols = st.columns(3)
                        for i, (img, title, url) in enumerate(loaded):
                            with cols[i % 3]:
                                st.image(img, caption=title[:50] if title else "",
                                         use_container_width=True)
                                if url:
                                    st.markdown(f"[🔗 מקור]({url})")

            if "🏛️ אטרקציות מובילות" in discover_type:
                with st.spinner("🏛️ מחפש אטרקציות..."):
                    attr_results = search_web(f"top 10 attractions {discover_dest} must see", max_results=5)

                if attr_results:
                    st.markdown("### 🏛️ אטרקציות מובילות")
                    prompt = f"סכם את 8 האטרקציות המובילות ב{discover_dest} בעברית. כל אטרקציה – שם, תיאור קצר ולמה כדאי לבקר. מידע: {' '.join([r.get('body','') for r in attr_results])}"
                    with st.spinner("🧠 מסכם..."):
                        attr_summary = call_gemini(prompt)
                    if attr_summary:
                        st.markdown(f'<div class="plan-box">{attr_summary}</div>', unsafe_allow_html=True)

            if "🍽️ מסעדות ואוכל" in discover_type:
                with st.spinner("🍽️ מחפש מסעדות ואוכל מקומי..."):
                    food_results = search_web(f"best food restaurants local cuisine {discover_dest}", max_results=5)

                if food_results:
                    st.markdown("### 🍽️ אוכל ומסעדות")
                    prompt = f"סכם את האוכל המקומי והמסעדות המומלצות ב{discover_dest} בעברית. כלול: מנות חובה, שווקים, טיפים לאוכלים. מידע: {' '.join([r.get('body','') for r in food_results])}"
                    with st.spinner("🧠 מסכם..."):
                        food_summary = call_gemini(prompt)
                    if food_summary:
                        st.markdown(f'<div class="plan-box">{food_summary}</div>', unsafe_allow_html=True)

            if "🏨 אזורי לינה מומלצים" in discover_type:
                with st.spinner("🏨 מחפש אזורי לינה..."):
                    hotel_results = search_web(f"best areas to stay neighborhoods {discover_dest} hotels", max_results=4)

                if hotel_results:
                    st.markdown("### 🏨 אזורי לינה")
                    prompt = f"סכם את האזורים המומלצים ללינה ב{discover_dest} בעברית. לכל אזור – מאפיינים, למי מתאים, טווח מחיר. מידע: {' '.join([r.get('body','') for r in hotel_results])}"
                    with st.spinner("🧠 מסכם..."):
                        hotel_summary = call_gemini(prompt)
                    if hotel_summary:
                        st.markdown(f'<div class="plan-box">{hotel_summary}</div>', unsafe_allow_html=True)

            if "💡 עובדות מעניינות" in discover_type:
                with st.spinner("💡 מחפש עובדות..."):
                    facts_results = search_web(f"interesting facts about {discover_dest} culture history", max_results=4)

                if facts_results:
                    st.markdown("### 💡 עובדות מעניינות")
                    prompt = f"כתוב 8 עובדות מעניינות ומפתיעות על {discover_dest} בעברית. כל עובדה – משפט אחד. מידע: {' '.join([r.get('body','') for r in facts_results])}"
                    with st.spinner("🧠 מסכם..."):
                        facts_summary = call_gemini(prompt)
                    if facts_summary:
                        st.markdown(f'<div class="plan-box">{facts_summary}</div>', unsafe_allow_html=True)


# ==================== טאב 3: שאל מומחה טיולים ====================
with tab3:
    st.markdown("## 💬 שאל את מומחה הטיולים")

    if "trip_plan" not in st.session_state:
        st.info("👆 קודם עבור לטאב **'תכנן טיול'** וצור תוכנית – ואז תוכל לשאול שאלות.")

        # אבל עדיין אפשר לשאול שאלות כלליות
        st.markdown("---")
        st.markdown("### 💬 או שאל שאלת טיול כללית")
        general_q = st.text_input("✍️ שאלה כללית:", placeholder="מה היעד הכי מומלץ לתקציב נמוך? / מה חובה לראות ביפן?", key="gen_q")
        if st.button("📨 שאל", key="gen_btn"):
            if general_q.strip():
                with st.spinner("🤔 מומחה הטיולים חושב..."):
                    result = call_gemini(f"אתה מומחה טיולים. ענה על השאלה הבאה בעברית בצורה מועילה ומפורטת: {general_q}")
                if result:
                    st.markdown(f'<div class="plan-box">{result}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"**🔗 מחובר לתוכנית הטיול שלך ל:** {st.session_state.get('trip_dest', '')}")

        col_style, col_q = st.columns([1, 3])
        with col_style:
            answer_style = st.radio("📝 סגנון תשובה:",
                                    ["קצר", "מפורט", "נקודות", "טבלה"],
                                    index=0, key="trip_style")
        with col_q:
            trip_q = st.text_input("✍️ שאלתך:",
                placeholder="לדוגמה: מה לאכול ביום 2? / כמה לתת טיפ? / האם צריך ויזה?",
                key="trip_q")
            send = st.button("📨 שלח", key="trip_send")

        if send and trip_q.strip():
            with st.spinner("🤔 מומחה הטיולים חושב..."):
                answer = answer_trip_question(
                    trip_q,
                    st.session_state["trip_plan"],
                    st.session_state["trip_dest"],
                    answer_style
                )
            if answer:
                if "trip_chat" not in st.session_state:
                    st.session_state["trip_chat"] = []
                st.session_state["trip_chat"].append({
                    "q": trip_q, "a": answer, "style": answer_style
                })

        if st.session_state.get("trip_chat"):
            st.markdown("### 🗂️ היסטוריית שיחה")
            for chat in reversed(st.session_state["trip_chat"]):
                st.markdown(
                    f'<div class="chat-user">🧑 <b>{chat["q"]}</b> '
                    f'<span style="color:#888; font-size:0.8em">[{chat["style"]}]</span></div>',
                    unsafe_allow_html=True
                )
                st.markdown(f'<div class="chat-ai">🤖 {chat["a"]}</div>', unsafe_allow_html=True)

            if st.button("🗑️ נקה שיחה", key="trip_clear"):
                st.session_state["trip_chat"] = []
                st.rerun()

# --- פוטר ---
st.markdown("---")
st.markdown("""
    <p style='text-align:center; color:gray;'>
        🧳 מתכנן טיולים חכם | פותח באמצעות Gemini AI + DuckDuckGo | © 2026
    </p>
""", unsafe_allow_html=True)