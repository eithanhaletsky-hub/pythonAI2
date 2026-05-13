import os
import time
import random
from dotenv import load_dotenv
from google import genai
import streamlit as st

# --- טעינת משתני סביבה ---
load_dotenv()
client = genai.Client(api_key=os.getenv("API_KEY"))

# --- הגדרות עמוד ---
st.set_page_config(
    page_title="⚔️ מסע הגבורה – RPG",
    page_icon="⚔️",
    layout="wide"
)

st.markdown("""
    <style>
        body { direction: rtl; background-color: #0d0d0d; }
        .stApp { background-color: #0d0d0d; }
        h1, h2, h3, p, label, div { color: #e8d5b7 !important; }

        .story-box {
            background: linear-gradient(180deg, #1a0a00, #2d1500);
            border: 2px solid #8b6914;
            border-radius: 10px;
            padding: 20px 25px;
            margin: 10px 0;
            font-size: 1.05em;
            line-height: 1.8;
            color: #f0e0c0 !important;
            box-shadow: 0 0 20px rgba(139,105,20,0.3);
            font-family: Georgia, serif;
        }
        .stat-box {
            background: linear-gradient(135deg, #1a0a00, #2d1500);
            border: 1px solid #8b6914;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            margin: 4px;
        }
        .hp-bar-container {
            background: #333;
            border-radius: 10px;
            height: 20px;
            margin: 5px 0;
            overflow: hidden;
        }
        .hp-bar {
            height: 20px;
            border-radius: 10px;
            transition: width 0.3s;
        }
        .action-btn {
            background: linear-gradient(135deg, #4a2800, #8b4513) !important;
            color: #ffd700 !important;
            border: 1px solid #8b6914 !important;
            border-radius: 6px !important;
            font-weight: bold !important;
        }
        .win-box {
            background: linear-gradient(135deg, #1a3a00, #2d5a00);
            border: 2px solid #4caf50;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            font-size: 1.3em;
            color: #a5d6a7 !important;
        }
        .lose-box {
            background: linear-gradient(135deg, #3a0000, #5a0000);
            border: 2px solid #f44336;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            font-size: 1.3em;
            color: #ef9a9a !important;
        }
        .enemy-box {
            background: linear-gradient(135deg, #1a0000, #2d0a0a);
            border: 1px solid #8b0000;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        .item-box {
            background: linear-gradient(135deg, #001a2d, #002a45);
            border: 1px solid #1565c0;
            border-radius: 6px;
            padding: 8px 12px;
            margin: 4px 0;
            font-size: 0.9em;
        }
        .log-box {
            background: #0d0d0d;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 10px;
            max-height: 200px;
            overflow-y: auto;
            font-size: 0.85em;
            color: #aaa !important;
        }
        .level-box {
            background: linear-gradient(135deg, #1a1a00, #2d2d00);
            border: 1px solid #ffd700;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }
        .stButton>button {
            background: linear-gradient(135deg, #4a2800, #8b4513);
            color: #ffd700;
            border: 1px solid #8b6914;
            border-radius: 6px;
            font-weight: bold;
            width: 100%;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #6b3d00, #a0522d);
            border-color: #ffd700;
        }
        .stTextInput>div>div>input {
            background: #1a0a00;
            color: #f0e0c0;
            border: 1px solid #8b6914;
        }
        .stSelectbox>div>div {
            background: #1a0a00;
            color: #f0e0c0;
        }
    </style>
""", unsafe_allow_html=True)


# ===================== Gemini =====================

def call_gemini(prompt):
    models = [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ]
    for model in models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                return response.text
            except Exception as e:
                error_str = str(e)
                if "503" in error_str:
                    time.sleep(10)
                elif "429" in error_str or "404" in error_str:
                    break
                else:
                    return None
    return None


# ===================== נתוני משחק =====================

CLASSES = {
    "⚔️ לוחם": {
        "hp": 120, "max_hp": 120, "attack": 20, "defense": 10,
        "mana": 30, "max_mana": 30, "speed": 8,
        "abilities": ["⚔️ מכה חזקה", "🛡️ הגנה", "💢 זעם לוחם"],
        "desc": "לוחם עמיד עם נזק גבוה ושריון כבד"
    },
    "🧙 קוסם": {
        "hp": 70, "max_hp": 70, "attack": 30, "defense": 4,
        "mana": 100, "max_mana": 100, "speed": 7,
        "abilities": ["🔥 כדור אש", "❄️ סערת קרח", "⚡ ברק"],
        "desc": "קוסם חזק עם כישורי קסם הרסניים"
    },
    "🏹 קשת": {
        "hp": 90, "max_hp": 90, "attack": 25, "defense": 6,
        "mana": 50, "max_mana": 50, "speed": 12,
        "abilities": ["🏹 חץ מהיר", "🎯 כוון מדויק", "💨 גשם חצים"],
        "desc": "קשת זריז עם מהירות ודיוק גבוהים"
    },
    "🗡️ מתנקש": {
        "hp": 80, "max_hp": 80, "attack": 35, "defense": 5,
        "mana": 60, "max_mana": 60, "speed": 15,
        "abilities": ["🗡️ דקירה קטלנית", "🌑 הסתרה", "☠️ רעל"],
        "desc": "מתנקש מהיר עם נזק קריטי גבוה"
    },
    "✨ כוהן": {
        "hp": 85, "max_hp": 85, "attack": 15, "defense": 7,
        "mana": 120, "max_mana": 120, "speed": 9,
        "abilities": ["✨ ריפוי", "🌟 ברכת האל", "💀 קללת חושך"],
        "desc": "כוהן שמרפא ותומך עם כוחות אלוהיים"
    },
}

ENEMIES_BY_LEVEL = {
    1: [
        {"name": "🐺 זאב מוחשך", "hp": 40, "max_hp": 40, "attack": 8, "defense": 2, "xp": 30, "gold": 10},
        {"name": "🕷️ עכביש ענק",  "hp": 35, "max_hp": 35, "attack": 10, "defense": 1, "xp": 25, "gold": 8},
        {"name": "💀 שלד",         "hp": 45, "max_hp": 45, "attack": 7,  "defense": 3, "xp": 35, "gold": 12},
    ],
    2: [
        {"name": "👹 גוב ירוק",     "hp": 70, "max_hp": 70, "attack": 15, "defense": 5, "xp": 60, "gold": 20},
        {"name": "🧟 זומבי",        "hp": 80, "max_hp": 80, "attack": 12, "defense": 6, "xp": 55, "gold": 18},
        {"name": "🦇 ואמפיר",       "hp": 65, "max_hp": 65, "attack": 18, "defense": 4, "xp": 65, "gold": 22},
    ],
    3: [
        {"name": "🐉 דרקון צעיר",   "hp": 120, "max_hp": 120, "attack": 25, "defense": 10, "xp": 100, "gold": 50},
        {"name": "🧌 ענק אבן",      "hp": 140, "max_hp": 140, "attack": 20, "defense": 15, "xp": 110, "gold": 45},
        {"name": "🔮 מכשף שחור",    "hp": 100, "max_hp": 100, "attack": 30, "defense": 8,  "xp": 120, "gold": 55},
    ],
    4: [
        {"name": "👑 מלך הדמונים",  "hp": 200, "max_hp": 200, "attack": 35, "defense": 18, "xp": 200, "gold": 100},
        {"name": "🐲 דרקון עתיק",   "hp": 220, "max_hp": 220, "attack": 40, "defense": 15, "xp": 220, "gold": 120},
    ],
    5: [
        {"name": "😈 אלוהי החושך",  "hp": 350, "max_hp": 350, "attack": 50, "defense": 25, "xp": 500, "gold": 300},
    ],
}

ITEMS = [
    {"name": "🧪 כוס ריפוי קטנה", "type": "heal", "value": 30, "price": 20},
    {"name": "🧪 כוס ריפוי גדולה", "type": "heal", "value": 70, "price": 50},
    {"name": "💙 כוס מנה",         "type": "mana", "value": 40, "price": 25},
    {"name": "⚔️ חרב ברזל",        "type": "attack", "value": 10, "price": 80},
    {"name": "🛡️ מגן עץ",          "type": "defense", "value": 5,  "price": 60},
    {"name": "👟 מגפי מהירות",      "type": "speed", "value": 5,   "price": 70},
    {"name": "💎 שריון יהלום",     "type": "defense", "value": 15, "price": 200},
    {"name": "🗡️ חרב מיתולוגית",   "type": "attack", "value": 25, "price": 350},
]

LOCATIONS = [
    "🌲 יער הצללים", "🏔️ הרי הגיהנום", "🏰 מבצר הקוסמים",
    "🌊 מערות החוף", "🗺️ מדבר הנצח", "🏚️ הכפר הנטוש",
    "⛪ מקדש האבות", "🌋 פסגת הגעש", "🌑 ממלכת החושך"
]

XP_TO_LEVEL = [0, 100, 250, 450, 700, 1000]


# ===================== פונקציות עזר =====================

def init_game():
    """אתחול מצב משחק"""
    cls = st.session_state.rpg_class
    base = CLASSES[cls].copy()
    st.session_state.rpg_player = {
        **base,
        "name": st.session_state.rpg_name,
        "class": cls,
        "level": 1,
        "xp": 0,
        "gold": 50,
        "inventory": ["🧪 כוס ריפוי קטנה", "🧪 כוס ריפוי קטנה"],
        "equipped_attack": 0,
        "equipped_defense": 0,
        "kills": 0,
        "battles": 0,
    }
    st.session_state.rpg_enemy = None
    st.session_state.rpg_in_battle = False
    st.session_state.rpg_log = []
    st.session_state.rpg_story = ""
    st.session_state.rpg_location = random.choice(LOCATIONS)
    st.session_state.rpg_dungeon_level = 1
    st.session_state.rpg_game_over = False
    st.session_state.rpg_victory = False
    st.session_state.rpg_started = True
    st.session_state.rpg_turn = "player"
    st.session_state.rpg_story_history = []


def get_level_from_xp(xp):
    for i, threshold in enumerate(XP_TO_LEVEL):
        if xp < threshold:
            return max(1, i)
    return 5


def hp_bar_html(current, maximum, color="#e53935"):
    pct = max(0, int((current / maximum) * 100))
    if pct > 60:
        color = "#43a047"
    elif pct > 30:
        color = "#fb8c00"
    else:
        color = "#e53935"
    return f"""
    <div class="hp-bar-container">
        <div class="hp-bar" style="width:{pct}%; background:{color};"></div>
    </div>
    <small>{current}/{maximum}</small>
    """


def add_log(msg):
    st.session_state.rpg_log.insert(0, msg)
    if len(st.session_state.rpg_log) > 30:
        st.session_state.rpg_log.pop()


def spawn_enemy():
    level = st.session_state.rpg_dungeon_level
    pool = ENEMIES_BY_LEVEL.get(min(level, 5), ENEMIES_BY_LEVEL[5])
    enemy = random.choice(pool).copy()
    # סקייל לפי רמת מבוך
    scale = 1 + (level - 1) * 0.2
    enemy["hp"] = int(enemy["hp"] * scale)
    enemy["max_hp"] = enemy["hp"]
    enemy["attack"] = int(enemy["attack"] * scale)
    st.session_state.rpg_enemy = enemy
    st.session_state.rpg_in_battle = True
    st.session_state.rpg_turn = "player"


def generate_story_intro():
    p = st.session_state.rpg_player
    loc = st.session_state.rpg_location
    prompt = f"""
אתה מספר סיפורים של RPG פנטזיה. כתוב פסקה קצרה ומרתקת (4-5 משפטים) בעברית.
הגיבור: {p['name']}, {p['class']}, רמה {p['level']}
מיקום: {loc}
רמת מבוך: {st.session_state.rpg_dungeon_level}
תאר את הגיבור מגיע למיקום חדש ומה הוא רואה. סיים עם מצב מותח.
    """
    return call_gemini(prompt)


def generate_battle_story(action, result, enemy_name):
    p = st.session_state.rpg_player
    prompt = f"""
כתוב 2-3 משפטים קצרים בעברית המתארים קרב RPG:
הגיבור {p['name']} ({p['class']}) השתמש ב{action} נגד {enemy_name}.
תוצאה: {result}
כתוב בסגנון פנטזיה מרגש ותיאורי. אל תוסיף מספרים.
    """
    return call_gemini(prompt)


def player_attack(ability):
    p = st.session_state.rpg_player
    e = st.session_state.rpg_enemy

    # חישוב נזק
    base_dmg = p["attack"] + p.get("equipped_attack", 0)
    crit = random.random() < 0.15
    dmg = int(base_dmg * (1.5 if crit else 1) * random.uniform(0.8, 1.2))
    actual_dmg = max(1, dmg - e["defense"])

    e["hp"] -= actual_dmg
    e["hp"] = max(0, e["hp"])

    msg = f"⚔️ {ability}: נזק {actual_dmg}"
    if crit:
        msg += " 💥 מכה קריטית!"
    add_log(msg)

    result = f"גרם {actual_dmg} נזק"
    if crit:
        result += " (קריטי!)"

    # סיפור
    with st.spinner("📖 מספר את הקרב..."):
        story = generate_battle_story(ability, result, e["name"])
    if story:
        st.session_state.rpg_story = story

    if e["hp"] <= 0:
        end_battle_win()
    else:
        # תור אויב
        enemy_turn()


def enemy_turn():
    p = st.session_state.rpg_player
    e = st.session_state.rpg_enemy
    if not e or e["hp"] <= 0:
        return

    dmg = max(1, int(e["attack"] * random.uniform(0.8, 1.2)) - (p["defense"] + p.get("equipped_defense", 0)))
    p["hp"] -= dmg
    p["hp"] = max(0, p["hp"])
    add_log(f"👹 {e['name']} תקף: נזק {dmg}")

    if p["hp"] <= 0:
        end_battle_lose()


def use_item(item_name):
    p = st.session_state.rpg_player
    if item_name not in p["inventory"]:
        return

    item = next((i for i in ITEMS if i["name"] == item_name), None)
    if not item:
        return

    p["inventory"].remove(item_name)

    if item["type"] == "heal":
        healed = min(item["value"], p["max_hp"] - p["hp"])
        p["hp"] += healed
        add_log(f"🧪 השתמשת ב{item_name}: +{healed} HP")
    elif item["type"] == "mana":
        restored = min(item["value"], p["max_mana"] - p["mana"])
        p["mana"] += restored
        add_log(f"💙 השתמשת ב{item_name}: +{restored} מנה")

    # אויב תוקף אחרי שימוש בפריט
    if st.session_state.rpg_in_battle:
        enemy_turn()


def end_battle_win():
    p = st.session_state.rpg_player
    e = st.session_state.rpg_enemy

    xp_gain = e["xp"]
    gold_gain = e["gold"] + random.randint(0, 10)
    p["xp"] += xp_gain
    p["gold"] += gold_gain
    p["kills"] += 1
    p["battles"] += 1

    add_log(f"🏆 ניצחת! +{xp_gain} XP, +{gold_gain} זהב")

    # בדוק רמה
    new_level = get_level_from_xp(p["xp"])
    if new_level > p["level"]:
        p["level"] = new_level
        p["max_hp"] += 20
        p["hp"] = p["max_hp"]
        p["attack"] += 5
        p["defense"] += 2
        add_log(f"⬆️ עלית לרמה {new_level}! סטטים עלו!")

    # סיכוי לפריט
    if random.random() < 0.3:
        loot = random.choice([i for i in ITEMS if i["type"] in ["heal", "mana"]])
        p["inventory"].append(loot["name"])
        add_log(f"🎁 מצאת: {loot['name']}")

    st.session_state.rpg_in_battle = False
    st.session_state.rpg_enemy = None
    st.session_state.rpg_dungeon_level += 1
    st.session_state.rpg_location = random.choice(LOCATIONS)

    if st.session_state.rpg_dungeon_level > 5 and p["kills"] >= 8:
        st.session_state.rpg_victory = True
        st.session_state.rpg_game_over = True


def end_battle_lose():
    p = st.session_state.rpg_player
    p["battles"] += 1
    add_log(f"💀 נפלת בקרב!")
    st.session_state.rpg_game_over = True
    st.session_state.rpg_victory = False


def flee_battle():
    p = st.session_state.rpg_player
    e = st.session_state.rpg_enemy
    speed_diff = p["speed"] - (e.get("speed", 8) or 8)
    flee_chance = 0.5 + speed_diff * 0.05
    if random.random() < max(0.2, min(0.9, flee_chance)):
        add_log("🏃 ברחת מהקרב!")
        st.session_state.rpg_in_battle = False
        st.session_state.rpg_enemy = None
        st.session_state.rpg_location = random.choice(LOCATIONS)
    else:
        add_log("❌ הבריחה נכשלה!")
        enemy_turn()


def buy_item(item):
    p = st.session_state.rpg_player
    if p["gold"] < item["price"]:
        add_log(f"❌ אין מספיק זהב!")
        return
    p["gold"] -= item["price"]
    if item["type"] in ["heal", "mana"]:
        p["inventory"].append(item["name"])
        add_log(f"🛒 קנית: {item['name']}")
    elif item["type"] == "attack":
        p["equipped_attack"] = p.get("equipped_attack", 0) + item["value"]
        add_log(f"⚔️ ציידת: {item['name']} (+{item['value']} התקפה)")
    elif item["type"] == "defense":
        p["equipped_defense"] = p.get("equipped_defense", 0) + item["value"]
        add_log(f"🛡️ ציידת: {item['name']} (+{item['value']} הגנה)")
    elif item["type"] == "speed":
        p["speed"] += item["value"]
        add_log(f"👟 ציידת: {item['name']} (+{item['value']} מהירות)")


# ===================== ממשק =====================

st.markdown("""
    <div style='background: linear-gradient(135deg, #1a0000, #4a0000, #1a0000);
                border: 2px solid #8b0000; padding: 25px; border-radius: 12px;
                text-align: center; margin-bottom: 20px;
                box-shadow: 0 0 30px rgba(139,0,0,0.5);'>
        <h1 style='color: #ffd700 !important; margin: 0; font-size: 2.5em; font-family: Georgia, serif;'>
            ⚔️ מסע הגבורה
        </h1>
        <p style='color: #c0a060 !important; margin: 8px 0 0 0; font-size: 1.1em;'>
            משחק תפקידים | מסופר על ידי Gemini AI
        </p>
    </div>
""", unsafe_allow_html=True)

# ===================== מסך יצירת דמות =====================
if "rpg_started" not in st.session_state or not st.session_state.rpg_started:
    st.markdown("## 🧙 צור את הגיבור שלך")

    col1, col2 = st.columns(2)
    with col1:
        char_name = st.text_input("📛 שם הגיבור:", placeholder="הכנס שם...", key="rpg_name_input")
        char_class = st.selectbox("⚔️ בחר מקצוע:", list(CLASSES.keys()), key="rpg_class_input")

        if char_class:
            c = CLASSES[char_class]
            st.markdown(f"""
                <div class="stat-box">
                    <b>{char_class}</b><br>
                    <small>{c['desc']}</small><br><br>
                    ❤️ HP: {c['hp']} | ⚔️ התקפה: {c['attack']}<br>
                    🛡️ הגנה: {c['defense']} | ⚡ מהירות: {c['speed']}<br>
                    💙 מנה: {c['mana']}
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
            <div class="story-box">
                <b style="color:#ffd700 !important;">📖 על המשחק:</b><br><br>
                ⚔️ צא למסע אפי נגד מפלצות ודמונים<br>
                🧙 ה-AI מספר את הסיפור שלך בזמן אמת<br>
                🏆 נצח 8 אויבים ועלה 5 קומות מבוך<br>
                🛒 קנה ציוד בחנות<br>
                ⬆️ עלה ברמה ושפר סטטים<br>
                💀 אם HP מגיע ל-0 – המשחק נגמר!<br><br>
                <b style="color:#ffd700 !important;">🎯 מטרה:</b> הגע לרמת מבוך 5 ונצח את <b style="color:#ff4444 !important;">אלוהי החושך!</b>
            </div>
        """, unsafe_allow_html=True)

    if st.button("⚔️ התחל מסע!", key="rpg_start"):
        if not char_name.strip():
            st.warning("אנא הכנס שם לגיבור!")
        else:
            st.session_state.rpg_name = char_name
            st.session_state.rpg_class = char_class
            init_game()
            with st.spinner("📖 מייצר את פתיחת הסיפור..."):
                intro = generate_story_intro()
            if intro:
                st.session_state.rpg_story = intro
            st.rerun()

# ===================== מסך משחק =====================
elif st.session_state.get("rpg_started") and not st.session_state.get("rpg_game_over"):
    p = st.session_state.rpg_player
    e = st.session_state.rpg_enemy

    # --- פאנל שחקן (שמאל) ---
    col_player, col_main, col_right = st.columns([1, 2, 1])

    with col_player:
        st.markdown(f"""
            <div class="stat-box">
                <b style="color:#ffd700 !important; font-size:1.1em;">{p['name']}</b><br>
                <small>{p['class']}</small><br>
                <b style="color:#ffd700 !important;">רמה {p['level']}</b>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"❤️ **HP:**")
        st.markdown(hp_bar_html(p["hp"], p["max_hp"]), unsafe_allow_html=True)
        st.markdown(f"💙 **מנה:** {p['mana']}/{p['max_mana']}")

        xp_needed = XP_TO_LEVEL[min(p["level"], 4)] if p["level"] < 5 else XP_TO_LEVEL[4]
        xp_prev = XP_TO_LEVEL[p["level"] - 1]
        xp_pct = int(((p["xp"] - xp_prev) / max(1, xp_needed - xp_prev)) * 100) if p["level"] < 5 else 100
        st.markdown(f"""
            <div class="level-box">
                <small>XP: {p['xp']}</small><br>
                <div class="hp-bar-container">
                    <div class="hp-bar" style="width:{xp_pct}%; background:#ffd700;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="stat-box" style="margin-top:8px;">
                ⚔️ התקפה: {p['attack'] + p.get('equipped_attack',0)}<br>
                🛡️ הגנה: {p['defense'] + p.get('equipped_defense',0)}<br>
                ⚡ מהירות: {p['speed']}<br>
                💰 זהב: {p['gold']}<br>
                💀 ניצחונות: {p['kills']}
            </div>
        """, unsafe_allow_html=True)

        # חנות
        with st.expander("🛒 חנות"):
            for item in ITEMS:
                can_buy = p["gold"] >= item["price"]
                if st.button(
                    f"{item['name']} – {item['price']}💰",
                    key=f"buy_{item['name']}",
                    disabled=not can_buy
                ):
                    buy_item(item)
                    st.rerun()

    # --- פאנל ראשי (מרכז) ---
    with col_main:
        # אויב
        if st.session_state.rpg_in_battle and e:
            st.markdown(f"""
                <div class="enemy-box">
                    <h2 style="color:#ff4444 !important; margin:0;">{e['name']}</h2>
                    <b style="color:#ff4444 !important;">❤️ HP:</b>
            """, unsafe_allow_html=True)
            st.markdown(hp_bar_html(e["hp"], e["max_hp"], "#e53935"), unsafe_allow_html=True)
            st.markdown(f"""
                    <small>⚔️ {e['attack']} | 🛡️ {e['defense']}</small>
                </div>
            """, unsafe_allow_html=True)

        # סיפור
        if st.session_state.rpg_story:
            st.markdown(f'<div class="story-box">{st.session_state.rpg_story}</div>', unsafe_allow_html=True)

        # פעולות קרב
        if st.session_state.rpg_in_battle and e:
            st.markdown("### ⚔️ פעולות קרב")
            abilities = CLASSES[p["class"]]["abilities"]

            cols_ab = st.columns(len(abilities))
            for i, ability in enumerate(abilities):
                with cols_ab[i]:
                    if st.button(ability, key=f"ability_{i}"):
                        with st.spinner("⚔️ נלחם..."):
                            player_attack(ability)
                        st.rerun()

            col_item, col_flee = st.columns(2)
            with col_item:
                heal_items = [item for item in p["inventory"] if "כוס" in item]
                if heal_items:
                    if st.button(f"🧪 {heal_items[0]}", key="use_item_btn"):
                        use_item(heal_items[0])
                        st.rerun()
                else:
                    st.button("🧪 אין פריטי ריפוי", disabled=True)
            with col_flee:
                if st.button("🏃 ברח!", key="flee_btn"):
                    flee_battle()
                    st.rerun()

        # פעולות מפה
        else:
            st.markdown(f"### 🗺️ {st.session_state.rpg_location}")
            st.markdown(f"**רמת מבוך: {st.session_state.rpg_dungeon_level}/5**")

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("⚔️ חפש קרב!", key="find_battle"):
                    spawn_enemy()
                    with st.spinner("📖 מספר את הפגישה..."):
                        story = call_gemini(f"כתוב 2 משפטים מותחים בעברית על {p['name']} {p['class']} שפוגש לפתע {st.session_state.rpg_enemy['name']} ב{st.session_state.rpg_location}. סגנון פנטזיה.")
                    if story:
                        st.session_state.rpg_story = story
                    st.rerun()
            with col_b2:
                if st.button("🏕️ מנוח (+20 HP)", key="rest_btn"):
                    if p["hp"] < p["max_hp"]:
                        healed = min(20, p["max_hp"] - p["hp"])
                        p["hp"] += healed
                        add_log(f"🏕️ נחת: +{healed} HP")
                        with st.spinner("📖 מספר..."):
                            story = call_gemini(f"כתוב משפט אחד בעברית על {p['name']} נח ב{st.session_state.rpg_location}. סגנון פנטזיה.")
                        if story:
                            st.session_state.rpg_story = story
                    else:
                        add_log("❤️ HP מלא!")
                    st.rerun()
            with col_b3:
                if st.button("🗺️ מקום חדש", key="explore_btn"):
                    st.session_state.rpg_location = random.choice(LOCATIONS)
                    with st.spinner("📖 מספר..."):
                        story = generate_story_intro()
                    if story:
                        st.session_state.rpg_story = story
                    st.rerun()

    # --- פאנל ימין: מלאי ולוג ---
    with col_right:
        st.markdown("### 🎒 מלאי")
        if p["inventory"]:
            for item_name in set(p["inventory"]):
                count = p["inventory"].count(item_name)
                st.markdown(f'<div class="item-box">{item_name} {"x"+str(count) if count>1 else ""}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="item-box">ריק</div>', unsafe_allow_html=True)

        st.markdown("### 📜 יומן")
        log_html = "<br>".join(st.session_state.rpg_log[:15])
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

# ===================== מסך סיום =====================
elif st.session_state.get("rpg_game_over"):
    p = st.session_state.get("rpg_player", {})

    if st.session_state.get("rpg_victory"):
        with st.spinner("📖 מייצר סיום אפי..."):
            ending = call_gemini(f"""
כתוב סיום אפי ומרגש (5-6 משפטים) בעברית למסע של הגיבור:
{p.get('name','הגיבור')} ({p.get('class','')})
הוא ניצח {p.get('kills',0)} אויבים ועלה לרמה {p.get('level',1)}.
הוא סוף סוף ניצח את אלוהי החושך והציל את הממלכה!
כתוב בסגנון פנטזיה אפי ומרגש.
            """)
        st.markdown(f"""
            <div class="win-box">
                <h2 style="color:#ffd700 !important;">🏆 ניצחת! המסע הושלם!</h2>
                <p style="color:#a5d6a7 !important;">{ending or 'הגיבור ניצח ושמר על הממלכה!'}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner("📖 מייצר סיום..."):
            ending = call_gemini(f"""
כתוב 3 משפטים דרמטיים בעברית על נפילתו של הגיבור:
{p.get('name','הגיבור')} ({p.get('class','')}) שנפל בקרב עם {st.session_state.rpg_enemy.get('name','האויב') if st.session_state.rpg_enemy else 'האויב'}.
הגיבור ניצח {p.get('kills',0)} אויבים לפני שנפל. סגנון פנטזיה.
            """)
        st.markdown(f"""
            <div class="lose-box">
                <h2 style="color:#ff4444 !important;">💀 נפלת בקרב...</h2>
                <p style="color:#ef9a9a !important;">{ending or 'הגיבור נפל בגבורה...'}</p>
            </div>
        """, unsafe_allow_html=True)

    # סטטיסטיקות
    st.markdown(f"""
        <div class="stat-box" style="margin-top:20px;">
            <h3 style="color:#ffd700 !important;">📊 סיכום המסע</h3>
            🧙 גיבור: {p.get('name','')} | {p.get('class','')}<br>
            ⬆️ רמה סופית: {p.get('level',1)}<br>
            💀 אויבים שנוצחו: {p.get('kills',0)}<br>
            ⭐ XP שנצבר: {p.get('xp',0)}<br>
            💰 זהב שנצבר: {p.get('gold',0)}
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 שחק שוב עם אותו גיבור", key="rpg_retry"):
            st.session_state.rpg_started = False
            del st.session_state.rpg_player
            st.rerun()
    with col2:
        if st.button("🆕 גיבור חדש לגמרי", key="rpg_new"):
            for key in list(st.session_state.keys()):
                if key.startswith("rpg_"):
                    del st.session_state[key]
            st.rerun()

# --- פוטר ---
st.markdown("---")
st.markdown("""
    <p style='text-align:center; color:#8b6914;'>
        ⚔️ מסע הגבורה | סופר על ידי Gemini AI | © 2026
    </p>
""", unsafe_allow_html=True)