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
    page_title="השקעה פסיבית חכמה",
    page_icon="💼",
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
        .info-card {
            background: white;
            border-radius: 12px;
            padding: 20px 25px;
            margin: 12px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-right: 4px solid #1a73e8;
        }
        .report-box {
            background: white;
            border-radius: 12px;
            padding: 2em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            line-height: 1.8;
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
        .concept-box {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 18px 22px;
            margin: 10px 0;
            border-top: 3px solid #1a73e8;
        }
        .stButton>button {
            background-color: #1a73e8;
            color: white;
            border-radius: 8px;
            padding: 0.5em 2em;
            font-size: 16px;
        }
        .profile-summary {
            background: linear-gradient(135deg, #e8f0fe, #f0f4ff);
            border-radius: 10px;
            padding: 15px 20px;
            margin: 10px 0;
            border: 1px solid #c5d8ff;
        }
    </style>
""", unsafe_allow_html=True)


# ===================== פונקציות =====================

def search_market_data(query, max_results=6):
    """מחפש נתוני שוק עדכניים עם DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception:
        return []


def search_market_news(query, max_results=4):
    """מחפש חדשות שוק עדכניות"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
        return results
    except Exception:
        return []


def fetch_top_performing_markets(exchanges):
    """מחפש נתוני ביצועים עדכניים לכל בורסה שנבחרה"""
    all_data = {}
    exchange_queries = {
        "S&P 500 (ארה\"ב)":         "S&P 500 performance returns 2025 YTD",
        "NASDAQ (טכנולוגיה)":       "NASDAQ 100 performance returns 2025 YTD",
        "תל אביב (TASE)":           "Tel Aviv Stock Exchange TA-125 performance 2025",
        "MSCI World (עולמי)":       "MSCI World ETF performance returns 2025",
        "MSCI Emerging Markets":    "MSCI Emerging Markets ETF performance 2025",
        "אירופה (Euro Stoxx)":      "Euro Stoxx 50 performance returns 2025",
        "יפן (Nikkei)":             "Nikkei 225 performance returns 2025",
        "סין":                      "China CSI 300 Shanghai stock market performance 2025",
        "מגוון (כולם)":             "best performing global stock markets 2025 returns",
    }

    for exchange in exchanges:
        query = exchange_queries.get(exchange, f"{exchange} stock market performance 2025")
        results = search_market_data(query, max_results=4)
        news = search_market_news(f"{exchange} stock market 2025", max_results=2)
        all_data[exchange] = {"results": results, "news": news}

    return all_data


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


def generate_passive_plan(profile, market_data=None):
    """יוצר תוכנית מידע על השקעה פסיבית לפי פרופיל המשתמש + נתוני שוק אמיתיים"""

    monthly_surplus = profile['salary'] - profile['expenses']
    suggested_invest = int(monthly_surplus * (profile['invest_percent'] / 100))

    # בנה סיכום נתוני שוק אמיתיים מה-DDGS
    market_summary = ""
    if market_data:
        for exchange, data in market_data.items():
            texts = [r.get('body', '') for r in data.get('results', [])]
            news_titles = [n.get('title', '') for n in data.get('news', [])]
            market_summary += f"\n--- {exchange} ---\n"
            market_summary += "\n".join(texts[:3])
            if news_titles:
                market_summary += f"\nחדשות: {' | '.join(news_titles[:2])}\n"

    prompt = f"""
אתה מומחה לחינוך פיננסי. תפקידך לספק מידע כללי על השקעה פסיבית בלבד.

⚠️ חשוב מאוד: אינך יועץ השקעות מורשה. אינך ממליץ על השקעות ספציפיות.
אינך מתחשב במצב הפיננסי הספציפי של המשתמש לצורך ייעוץ.
כל המידע הוא לצרכי חינוך פיננסי כללי בלבד.

פרופיל המשתמש לצורך התאמת הסבר כללי:
- גיל: {profile['age']} שנים
- מטרת ההשקעה: {profile['goal']}
- בורסות מעניינות: {', '.join(profile['exchanges'])}
- הכנסה חודשית נטו: {profile['salary']:,} ₪
- הוצאות חודשיות: {profile['expenses']:,} ₪
- עודף חודשי משוער: {monthly_surplus:,} ₪
- אחוז מהעודף לחיסכון/השקעה: {profile['invest_percent']}%
- סכום חודשי פוטנציאלי: {suggested_invest:,} ₪
- אופק זמן: {profile['horizon']}
- רמת ידע פיננסי: {profile['knowledge']}
- גישה לסיכון: {profile['risk']}
- מדינת מגורים: {profile['country']}
- מטרה ספציפית: {profile['specific_goal']}

צור מסמך מידע מקיף הכולל את הסעיפים הבאים:

## 1. 👤 ניתוח הפרופיל שלך
הסבר על המאפיינים של פרופיל זה מבחינת השקעה פסיבית – גיל, אופק זמן, מטרה.
ציין את העודף החודשי ואחוז החיסכון המשוער.

## 2. 📚 מה מתאים לפרופיל זה – מידע כללי
הסבר אילו כלי השקעה פסיבית נפוצים (ETF, קרנות מחקות, קרן פנסיה, קופת גמל להשקעה)
מתאימים באופן כללי לפרופיל מסוג זה – לפי גיל, מטרה ואופק זמן.
הסבר את היתרונות של כל כלי.

## 3. 📊 ביצועי הבורסות שבחרת – נתונים עדכניים מהאינטרנט
להלן מידע עדכני שנאסף מהאינטרנט על כל בורסה שציין המשתמש:

{market_summary if market_summary else "לא נמצא מידע עדכני – הסבר על הבורסות מתוך הידע הכללי שלך."}

בהתבסס על המידע שנאסף:
- ציין אילו בורסות הציגו ביצועים טובים לאחרונה לפי הנתונים
- הסבר מה מאפיין כל בורסה (רמת סיכון, מגזרים דומיננטיים, מטבע)
- השווה בין הבורסות שנבחרו מבחינת ביצועים ומגמות עדכניות
- ציין בבירור שנתונים אלו הם היסטוריים ואינם מבטיחים תשואה עתידית

## 4. 📈 עקרון הריבית דריבית לאורך זמן
הסבר כיצד עובד עקרון הריבית דריבית בהשקעה פסיבית לאורך {profile['horizon']}.
תן דוגמה חישובית כללית (לא המלצה!) עם סכום של {suggested_invest:,} ₪ לחודש
לאורך 10, 20 ו-30 שנה בתשואה היסטורית ממוצעת של 7% בשנה.

## 5. ⚠️ סיכונים שחשוב להכיר
הסבר על הסיכונים העיקריים בהשקעה פסיבית שמשתמש בפרופיל זה צריך להכיר.

## 6. 📋 שלבים להתחלה – מידע כללי
הסבר בצורה כללית את השלבים הנדרשים להתחלת השקעה פסיבית בישראל.
ציין סוגי חשבונות ואפיקים נפוצים (IRA, קופת גמל, ברוקר מקוון) – ללא המלצה ספציפית.

בסוף כל סעיף הוסף:
"⚠️ זהו מידע כללי בלבד – לא ייעוץ השקעות אישי."

כתוב בעברית בצורה ברורה, ידידותית ומפורטת.
    """
    return call_gemini(prompt)


def answer_passive_question(question, plan, profile, answer_style):
    style_map = {
        "קצר": "ענה ב-3-4 משפטים בלבד.",
        "ארוך": "ענה בפירוט מלא עם דוגמאות והסברים.",
        "נקודות": "ענה אך ורק בנקודות ממוספרות.",
        "טבלה": "ענה בצורת טבלה Markdown עם עמודות רלוונטיות."
    }
    prompt = f"""
אתה מומחה לחינוך פיננסי. תפקידך לספק מידע כללי בלבד.
⚠️ אינך יועץ השקעות. אינך ממליץ על השקעות ספציפיות.
אם המשתמש מבקש המלצה אישית – הסבר שאינך יועץ והפנה ליועץ מורשה.

פרופיל המשתמש: גיל {profile['age']}, מטרה: {profile['goal']}, אופק: {profile['horizon']}

מסמך המידע שנוצר:
{plan}

שאלת המשתמש: {question}

{style_map.get(answer_style, style_map['קצר'])}
בסוף הוסף: "⚠️ מידע כללי בלבד – לא ייעוץ השקעות."
כתוב בעברית בלבד.
    """
    return call_gemini(prompt)


# ===================== ממשק ראשי =====================

# כותרת
st.markdown("""
    <div style='background: linear-gradient(135deg, #1565c0, #1a73e8, #42a5f5);
                padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 25px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>💼 מדריך השקעה פסיבית חכמה</h1>
        <p style='color: #e3f2fd; margin: 8px 0 0 0; font-size: 1.1em;'>
            הבן כיצד עובדת השקעה פסיבית – מותאם לפרופיל שלך
        </p>
    </div>
""", unsafe_allow_html=True)

# ===== כתב ויתור =====
st.markdown("""
    <div class="disclaimer-box">
        <b style='color:#cc0000; font-size:1.1em;'>⚠️ הצהרת אחריות – חובה לקרוא לפני השימוש</b><br><br>
        🔴 <b>דף זה אינו מספק ייעוץ השקעות בשום צורה.</b><br>
        🔴 המידע המוצג הוא <b>לצרכי חינוך פיננסי כללי בלבד</b> ואינו מהווה המלצה לביצוע פעולה כלשהי.<br>
        🔴 ה-AI <b>אינו יועץ השקעות מורשה</b> ואינו מתחשב במצבך הפיננסי האישי לצורך ייעוץ.<br>
        🔴 <b>לפני כל החלטת השקעה</b> – פנה ליועץ השקעות מורשה על ידי רשות ניירות ערך.<br>
        🔴 <b>השקעות כרוכות בסיכון</b> – ייתכן הפסד חלקי או מלא של הכסף.
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ===================== טאבים =====================
tab1, tab2, tab3 = st.tabs(["📚 מה זה השקעה פסיבית?", "👤 הפרופיל שלי", "💬 שאל את ה-AI"])

# ==================== טאב 1: הסבר ====================
with tab1:
    st.markdown("## 📚 מה זה השקעה פסיבית?")

    st.markdown("""
        <div class="info-card">
            <h3>🎯 הגדרה בקצרה</h3>
            <p>השקעה פסיבית היא אסטרטגיה שבה <b>משקיעים לאורך זמן ארוך</b> מבלי לנסות "לנצח את השוק".
            במקום לבחור מניות בודדות, משקיעים ב<b>קרנות מחקות או ETF</b> שעוקבות אחרי מדדים שלמים
            כמו S&P 500, נאסד"ק, או מדד ת"א 125.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="concept-box">
                <h4>📊 ETF</h4>
                <p>קרן סל הנסחרת בבורסה כמו מניה. מאפשרת השקעה במאות חברות בבת אחת
                בדמי ניהול נמוכים מאוד (לרוב 0.03%-0.2% בשנה).</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="concept-box">
                <h4>📈 קרן מחקה</h4>
                <p>קרן נאמנות שעוקבת אחרי מדד מסוים. בישראל נפוץ מאוד להשקיע דרך
                קרנות מחקות על S&P 500 או מדדים ישראליים.</p>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
            <div class="concept-box">
                <h4>🏦 קופת גמל להשקעה</h4>
                <p>מוצר ייחודי בישראל המאפשר השקעה עם הטבות מס.
                ניתן למשוך ללא מס רווחי הון בגיל 60, או כקצבה פטורה ממס.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## ✅ יתרונות השקעה פסיבית")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="info-card">
                <b>⏱️ חוסך זמן</b> – אין צורך לעקוב אחרי שוק ההון מדי יום.<br><br>
                <b>💰 דמי ניהול נמוכים</b> – לעומת קרנות אקטיביות שגובות 1%-2% בשנה.<br><br>
                <b>📉 פחות טעויות רגשיות</b> – לא מוכרים בפאניקה ולא קונים מתוך אופוריה.<br><br>
                <b>📊 פיזור רחב</b> – השקעה במאות חברות מקטינה את הסיכון.
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="info-card">
                <b>🔄 ריבית דריבית</b> – הרווחים מושקעים מחדש ויוצרים צמיחה מצטברת.<br><br>
                <b>🌍 גיוון גלובלי</b> – ניתן להשקיע בשווקים ברחבי העולם בקלות.<br><br>
                <b>📅 משמעת חיסכון</b> – השקעה קבועה חודשית יוצרת הרגל חיסכון.<br><br>
                <b>🏆 ביצועים היסטוריים</b> – רוב הקרנות האקטיביות לא מכות את המדד לאורך זמן.
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## ⚠️ חסרונות וסיכונים שחשוב להכיר")

    st.markdown("""
        <div class="info-card" style="border-right-color: #e53935;">
            <b>📉 תלות בשוק</b> – בזמן משבר כל המדד יורד, אין הגנה מפני ירידות שוק.<br><br>
            <b>⏳ דורש סבלנות</b> – ההשקעה הפסיבית מתגמלת לאורך שנים רבות, לא מהר.<br><br>
            <b>💱 סיכון מטבע</b> – השקעה בחו"ל חשופה לשינויי שערי מטבע (דולר, אירו).<br><br>
            <b>🌍 סיכון גיאופוליטי</b> – אירועים עולמיים משפיעים על השווקים.<br><br>
            <b>📊 אין גמישות</b> – לא ניתן להרוויח יותר מהמדד (אבל גם לא פחות ממנו).
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## 🔢 איך עובדת ריבית דריבית? – דוגמה כללית")

    st.markdown("""
        <div class="concept-box">
            <b>הנחה לדוגמה בלבד:</b> השקעה של 1,000 ₪ לחודש בתשואה היסטורית ממוצעת של 7% בשנה<br>
            (אינו מהווה תחזית או הבטחה לתשואה עתידית!)
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    examples = [
        ("10 שנים", "₪172,000", "₪120,000", "₪52,000"),
        ("20 שנים", "₪521,000", "₪240,000", "₪281,000"),
        ("30 שנים", "₪1,227,000", "₪360,000", "₪867,000"),
        ("40 שנים", "₪2,632,000", "₪480,000", "₪2,152,000"),
    ]
    for col, (period, total, invested, profit) in zip([col1, col2, col3, col4], examples):
        with col:
            st.markdown(f"""
                <div style='background:white; border-radius:10px; padding:15px;
                            text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.1);'>
                    <b style='color:#1a73e8; font-size:1.1em;'>{period}</b><br>
                    <span style='font-size:1.4em; font-weight:bold;'>{total}</span><br>
                    <small style='color:gray;'>הושקע: {invested}</small><br>
                    <small style='color:#2e7d32;'>רווח: {profit}</small>
                </div>
            """, unsafe_allow_html=True)

    st.caption("⚠️ הנתונים לעיל הם לצורך המחשה בלבד. אין ערובה לתשואה עתידית. זו אינה המלצת השקעה.")

    st.markdown("---")
    st.markdown("## 📋 שלבים כלליים להתחלה (מידע בלבד)")

    steps = [
        ("1", "🎓 למד את הבסיס", "קרא על ETF, קרנות מחקות, ומדדים עיקריים. יש המון חומר חינמי ברשת."),
        ("2", "🏦 בחר אפיק חיסכון", "בישראל: קופת גמל להשקעה, IRA, או ברוקר מקוון. לכל אחד יתרונות שונים."),
        ("3", "💳 פתח חשבון", "פתח חשבון בברוקר מורשה בישראל (מסנה, מיטב, אינטרקטיב ברוקרס וכו')."),
        ("4", "📅 הגדר הוראת קבע", "השקעה חודשית קבועה (Dollar Cost Averaging) מפחיתה סיכון תזמון."),
        ("5", "⏳ היה סבלני", "אל תיגע לכסף בזמן ירידות. זמן בשוק חשוב יותר מתזמון השוק."),
    ]

    for num, title, desc in steps:
        st.markdown(f"""
            <div class="info-card">
                <b style='color:#1a73e8; font-size:1.2em;'>{num}. {title}</b><br>
                {desc}
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="disclaimer-box" style="margin-top:20px;">
            ⚠️ <b>תזכורת:</b> כל המידע בדף זה הוא לצרכי חינוך פיננסי בלבד.
            לפני כל פעולה השקעתית – פנה ליועץ השקעות מורשה.
        </div>
    """, unsafe_allow_html=True)


# ==================== טאב 2: פרופיל אישי ====================
with tab2:
    st.markdown("## 👤 בנה את הפרופיל שלך")
    st.markdown("מלא את הפרטים הבאים כדי לקבל מידע כללי **מותאם לפרופיל שלך**.")
    st.info("🔒 הנתונים אינם נשמרים ומשמשים לצורך יצירת מידע כללי בלבד.")

    st.markdown("---")
    st.markdown("### 📋 פרטים אישיים")
    col1, col2, col3 = st.columns(3)

    with col1:
        age = st.number_input("🎂 גיל:", min_value=18, max_value=80, value=30, step=1)
        country = st.selectbox("🌍 מדינת מגורים:", ["ישראל", "ארה\"ב", "אחר"])

    with col2:
        goal = st.selectbox("🎯 מטרת ההשקעה הראשית:", [
            "חיסכון לפנסיה",
            "קניית דירה",
            "חופש פיננסי מוקדם (FIRE)",
            "חיסכון לילדים",
            "כרית ביטחון כלכלית",
            "הגדלת הון כללית",
            "חיסכון לטיול / רכב / הוצאה גדולה"
        ])
        specific_goal = st.text_input("✏️ פרט את המטרה (אופציונלי):",
                                       placeholder="לדוגמה: פרישה בגיל 55 עם 5,000 ₪ לחודש")

    with col3:
        horizon = st.select_slider("⏳ אופק השקעה:", options=[
            "פחות מ-3 שנים", "3-5 שנים", "5-10 שנים",
            "10-20 שנים", "20-30 שנים", "מעל 30 שנה"
        ], value="10-20 שנים")
        knowledge = st.select_slider("📚 רמת ידע פיננסי:", options=[
            "מתחיל", "בסיסי", "בינוני", "מתקדם", "מומחה"
        ], value="בסיסי")

    st.markdown("---")
    st.markdown("### 💰 פרטים כלכליים")
    col1, col2, col3 = st.columns(3)

    with col1:
        salary = st.number_input("💵 הכנסה חודשית נטו (₪):",
                                  min_value=0, max_value=100000, value=10000, step=500)
        expenses = st.number_input("🛒 הוצאות חודשיות (₪):",
                                    min_value=0, max_value=100000, value=7000, step=500)

    with col2:
        monthly_surplus = salary - expenses
        color = "#2e7d32" if monthly_surplus > 0 else "#c62828"
        st.markdown(f"""
            <div style='background:white; border-radius:10px; padding:20px;
                        text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.1); margin-top:28px;'>
                <b>עודף חודשי משוער</b><br>
                <span style='font-size:2em; font-weight:bold; color:{color};'>
                    {monthly_surplus:,} ₪
                </span>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        invest_percent = st.slider(
            "📊 אחוז מהעודף לחיסכון/השקעה:",
            min_value=5, max_value=100, value=30, step=5,
            help="כלל אצבע מקובל: 20%-30% מהעודף"
        )
        suggested = max(0, int(monthly_surplus * (invest_percent / 100)))
        st.markdown(f"""
            <div style='background:#e8f0fe; border-radius:10px; padding:15px;
                        text-align:center; margin-top:10px;'>
                <b>סכום חודשי פוטנציאלי</b><br>
                <span style='font-size:1.6em; font-weight:bold; color:#1a73e8;'>
                    {suggested:,} ₪
                </span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚙️ העדפות השקעה")
    col1, col2, col3 = st.columns(3)

    with col1:
        exchanges = st.multiselect("🏦 בורסות מעניינות:", [
            "S&P 500 (ארה\"ב)", "NASDAQ (טכנולוגיה)", "תל אביב (TASE)",
            "MSCI World (עולמי)", "MSCI Emerging Markets", "אירופה (Euro Stoxx)",
            "יפן (Nikkei)", "סין", "מגוון (כולם)"
        ], default=["S&P 500 (ארה\"ב)", "MSCI World (עולמי)"])

    with col2:
        risk = st.select_slider("⚖️ גישה לסיכון:", options=[
            "שמרני מאוד", "שמרני", "מאוזן", "אגרסיבי", "אגרסיבי מאוד"
        ], value="מאוזן")

    with col3:
        existing_savings = st.number_input("🏦 חיסכון קיים (₪) – אופציונלי:",
                                            min_value=0, value=0, step=1000)
        has_pension = st.checkbox("✅ יש לי פנסיה / קרן השתלמות פעילה")

    st.markdown("---")

    if monthly_surplus <= 0:
        st.warning("⚠️ ההוצאות עולות על ההכנסות – לא מומלץ להשקיע לפני איזון התקציב.")

    if st.button("🚀 צור מסמך מידע אישי"):
        if not exchanges:
            st.warning("אנא בחר לפחות בורסה אחת.")
        elif monthly_surplus <= 0:
            st.error("לא ניתן לייצר מסמך כאשר ההוצאות עולות על ההכנסות.")
        else:
            profile = {
                "age": age, "goal": goal, "specific_goal": specific_goal,
                "horizon": horizon, "knowledge": knowledge,
                "salary": salary, "expenses": expenses,
                "invest_percent": invest_percent, "exchanges": exchanges,
                "risk": risk, "country": country,
                "existing_savings": existing_savings, "has_pension": has_pension
            }

            # שלב 1: חיפוש נתוני שוק עדכניים עם DDGS
            with st.spinner("🔎 מחפש נתוני ביצועים עדכניים לבורסות שבחרת..."):
                market_data = fetch_top_performing_markets(exchanges)

            # הצג מה נמצא
            found = sum(1 for d in market_data.values() if d["results"])
            if found > 0:
                st.success(f"✅ נמצא מידע עדכני על {found}/{len(exchanges)} בורסות")
            else:
                st.info("ℹ️ לא נמצא מידע עדכני – ה-AI ישתמש בידע הכללי שלו")

            # שלב 2: ה-AI מנתח ומסכם עם הנתונים האמיתיים
            with st.spinner("🧠 ה-AI מנתח נתונים ומכין מסמך מותאם אישית..."):
                plan = generate_passive_plan(profile, market_data)

            if plan:
                st.session_state["passive_plan"] = plan
                st.session_state["passive_profile"] = profile
                st.session_state["passive_chat"] = []

                st.success("✅ מסמך המידע מוכן!")
                st.markdown("---")

                # סיכום פרופיל
                st.markdown(f"""
                    <div class="profile-summary">
                        <b>👤 פרופיל:</b> גיל {age} | {goal} | אופק: {horizon} | סיכון: {risk}<br>
                        <b>💰 כלכלי:</b> הכנסה {salary:,} ₪ | הוצאות {expenses:,} ₪ |
                        עודף {monthly_surplus:,} ₪ | השקעה פוטנציאלית {suggested:,} ₪/חודש<br>
                        <b>🏦 בורסות:</b> {', '.join(exchanges)}
                    </div>
                """, unsafe_allow_html=True)

                # הצג מסמך
                st.markdown("## 📄 מסמך מידע – השקעה פסיבית")
                st.markdown(f'<div class="report-box">{plan}</div>', unsafe_allow_html=True)

                # ===== חדשות עדכניות מהבורסות =====
                st.markdown("---")
                st.markdown("## 📰 חדשות עדכניות מהבורסות שבחרת")
                st.caption("⚠️ החדשות נאספו מהאינטרנט ואינן המלצת השקעה.")
                has_news = False
                for exchange, data in market_data.items():
                    news = data.get("news", [])
                    if news:
                        has_news = True
                        st.markdown(f"**🏦 {exchange}**")
                        for item in news:
                            with st.expander(f"📌 {item.get('title', 'ללא כותרת')}"):
                                st.write(item.get('body', ''))
                                if item.get('url'):
                                    st.markdown(f"[קרא עוד ←]({item['url']})")
                if not has_news:
                    st.info("לא נמצאו חדשות עדכניות לבורסות שנבחרו.")

                st.markdown("---")
                st.markdown("""
                    <div class="disclaimer-box">
                        ⚠️ <b>תזכורת חשובה:</b> המסמך לעיל הוא לצרכי חינוך פיננסי בלבד.
                        אינו מהווה ייעוץ השקעות אישי. פנה ליועץ מורשה לפני כל פעולה.
                    </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    "📥 הורד מסמך מידע (TXT)",
                    plan.encode("utf-8"),
                    f"מידע_השקעה_פסיבית_גיל_{age}.txt",
                    mime="text/plain"
                )


# ==================== טאב 3: צ'אט ====================
with tab3:
    st.markdown("## 💬 שאל את ה-AI על השקעה פסיבית")

    if "passive_plan" not in st.session_state:
        st.info("👆 קודם עבור לטאב **'הפרופיל שלי'**, מלא את הפרטים וצור מסמך מידע – ואז תוכל לשאול שאלות.")
    else:
        profile = st.session_state["passive_profile"]
        st.markdown(f"""
            <div class="profile-summary">
                <b>🔗 מחובר לפרופיל:</b> גיל {profile['age']} |
                {profile['goal']} | {profile['horizon']} | {profile['risk']}
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style='background:#ffebee; border:1px solid #ef9a9a;
                        border-radius:8px; padding:10px 15px; margin:15px 0;'>
                ⚠️ <b>תזכורת:</b> הסוכן מספק מידע כללי בלבד ואינו יועץ השקעות מורשה.
            </div>
        """, unsafe_allow_html=True)

        col_style, col_q = st.columns([1, 3])
        with col_style:
            answer_style = st.radio("📝 סגנון תשובה:",
                                    ["קצר", "ארוך", "נקודות", "טבלה"], index=0)
        with col_q:
            user_q = st.text_input("✍️ שאלתך:",
                placeholder="לדוגמה: מה ההבדל בין ETF לקרן מחקה? / מה זה DCA? / איך מפזרים סיכון?")
            send = st.button("📨 שלח שאלה")

        if send and user_q.strip():
            with st.spinner("🤔 ה-AI מכין תשובה..."):
                answer = answer_passive_question(
                    user_q,
                    st.session_state["passive_plan"],
                    profile,
                    answer_style
                )
            if answer:
                if "passive_chat" not in st.session_state:
                    st.session_state["passive_chat"] = []
                st.session_state["passive_chat"].append({
                    "question": user_q, "answer": answer, "style": answer_style
                })

        if st.session_state.get("passive_chat"):
            st.markdown("### 🗂️ היסטוריית שיחה")
            for chat in reversed(st.session_state["passive_chat"]):
                st.markdown(
                    f'<div class="chat-user">🧑 <b>{chat["question"]}</b> '
                    f'<span style="color:#888; font-size:0.8em">[{chat["style"]}]</span></div>',
                    unsafe_allow_html=True
                )
                st.markdown(f'<div class="chat-ai">🤖 {chat["answer"]}</div>', unsafe_allow_html=True)

            if st.button("🗑️ נקה שיחה"):
                st.session_state["passive_chat"] = []
                st.rerun()

# ===== כתב ויתור תחתון =====
st.markdown("---")
st.markdown("""
    <div class="disclaimer-box">
        <b style='color:#cc0000;'>⚠️ הצהרת אחריות סופית:</b><br>
        כל המידע בדף זה הוא לצרכי חינוך פיננסי כללי בלבד.
        הדף וה-AI <b>אינם מספקים ייעוץ השקעות</b> בשום צורה ובשום אופן.
        לפני כל החלטת השקעה – פנה ליועץ השקעות מורשה על ידי רשות ניירות ערך.
    </div>
""", unsafe_allow_html=True)

st.markdown(
    "<p style='text-align:center; color:gray;'>"
    "מדריך השקעה פסיבית | פותח באמצעות Gemini AI | © 2026<br>"
    "<b style='color:#cc0000;'>אינו מהווה ייעוץ השקעות בשום צורה</b>"
    "</p>",
    unsafe_allow_html=True
)