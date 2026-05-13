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
    page_title="משחקים נגד המחשב",
    page_icon="🎮",
    layout="wide"
)

st.markdown("""
    <style>
        body { direction: rtl; }
        .stButton>button {
            border-radius: 8px;
            padding: 0.4em 1.5em;
            font-size: 15px;
            font-weight: bold;
        }
        .game-box {
            background: white;
            border-radius: 12px;
            padding: 1.5em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 10px 0;
            text-align: center;
        }
        .card {
            display: inline-block;
            background: white;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 8px 14px;
            margin: 4px;
            font-size: 2em;
            min-width: 60px;
            text-align: center;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        }
        .card-red { color: #d32f2f; }
        .card-black { color: #212121; }
        .score-box {
            background: linear-gradient(135deg, #1a237e, #283593);
            color: white;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            margin: 8px 0;
        }
        .win-msg {
            background: #e8f5e9;
            border: 2px solid #43a047;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            color: #2e7d32;
        }
        .lose-msg {
            background: #ffebee;
            border: 2px solid #e53935;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            color: #c62828;
        }
        .draw-msg {
            background: #fff3e0;
            border: 2px solid #fb8c00;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
            color: #e65100;
        }
        .checkers-cell {
            width: 60px;
            height: 60px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8em;
            cursor: pointer;
            border-radius: 4px;
        }
        .trivia-box {
            background: #f3e5f5;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            font-size: 1.1em;
        }
        .ai-thinking {
            background: #e8eaf6;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            font-style: italic;
            color: #3949ab;
        }
    </style>
""", unsafe_allow_html=True)


# ===================== פונקציית Gemini =====================

def call_gemini(prompt, max_tokens=500):
    models = [
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
        "gemini-2.5-flash",
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


# ===================== כותרת =====================

st.markdown("""
    <div style='background: linear-gradient(135deg, #4a148c, #7b1fa2, #e040fb);
                padding: 25px; border-radius: 12px; text-align: center; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; font-size: 2.2em;'>🎮 משחקים נגד המחשב</h1>
        <p style='color: #f3e5f5; margin: 8px 0 0 0; font-size: 1.1em;'>
            5 משחקים מגניבים – האם תצליח לנצח את ה-AI?
        </p>
    </div>
""", unsafe_allow_html=True)

# ===================== טאבים =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "♥️ בלאק ג'ק",
    "⬛ דמקה",
    "⚽ טריוויה",
    "🐍 נחש",
    "🧠 20 שאלות"
])


# ==================== טאב 1: בלאק ג'ק ====================
with tab1:
    st.markdown("## ♥️ בלאק ג'ק")
    st.markdown("הגע ל-21 בלי לעבור! קרוב יותר מהמחשב = ניצחון 🃏")

    # אתחול
    if "bj_deck" not in st.session_state:
        st.session_state.bj_deck = []
        st.session_state.bj_player = []
        st.session_state.bj_dealer = []
        st.session_state.bj_game_over = True
        st.session_state.bj_message = ""
        st.session_state.bj_wins = 0
        st.session_state.bj_losses = 0
        st.session_state.bj_draws = 0

    def make_deck():
        suits = ["♥️", "♦️", "♣️", "♠️"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        deck = [(r, s) for s in suits for r in ranks]
        random.shuffle(deck)
        return deck

    def card_value(rank):
        if rank in ["J", "Q", "K"]:
            return 10
        if rank == "A":
            return 11
        return int(rank)

    def hand_value(hand):
        val = sum(card_value(r) for r, s in hand)
        aces = sum(1 for r, s in hand if r == "A")
        while val > 21 and aces:
            val -= 10
            aces -= 1
        return val

    def card_html(rank, suit):
        red = suit in ["♥️", "♦️"]
        cls = "card-red" if red else "card-black"
        return f'<span class="card {cls}">{rank}<br>{suit}</span>'

    def render_hand(hand):
        return "".join(card_html(r, s) for r, s in hand)

    # ניקוד
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(f'<div class="score-box">🏆 ניצחונות<br><b style="font-size:1.5em">{st.session_state.bj_wins}</b></div>', unsafe_allow_html=True)
    with col_s2:
        st.markdown(f'<div class="score-box" style="background:linear-gradient(135deg,#b71c1c,#c62828)">💀 הפסדים<br><b style="font-size:1.5em">{st.session_state.bj_losses}</b></div>', unsafe_allow_html=True)
    with col_s3:
        st.markdown(f'<div class="score-box" style="background:linear-gradient(135deg,#e65100,#f57c00)">🤝 תיקו<br><b style="font-size:1.5em">{st.session_state.bj_draws}</b></div>', unsafe_allow_html=True)

    st.markdown("---")

    if st.session_state.bj_game_over:
        if st.button("🃏 משחק חדש!", key="bj_new"):
            deck = make_deck()
            st.session_state.bj_deck = deck
            st.session_state.bj_player = [deck.pop(), deck.pop()]
            st.session_state.bj_dealer = [deck.pop(), deck.pop()]
            st.session_state.bj_game_over = False
            st.session_state.bj_message = ""
            st.rerun()
    else:
        player_val = hand_value(st.session_state.bj_player)
        dealer_val = hand_value(st.session_state.bj_dealer)

        # קלפי שחקן
        st.markdown("### 🧑 הקלפים שלך")
        st.markdown(render_hand(st.session_state.bj_player), unsafe_allow_html=True)
        st.markdown(f"**סכום: {player_val}**")

        # קלף גלוי של דילר
        st.markdown("### 🤖 קלפי הדילר")
        st.markdown(card_html(*st.session_state.bj_dealer[0]) + ' <span class="card">🂠</span>', unsafe_allow_html=True)
        st.markdown("**קלף אחד מוסתר**")

        st.markdown("---")
        col_hit, col_stand = st.columns(2)

        with col_hit:
            if st.button("🃏 קח קלף (Hit)", key="bj_hit"):
                st.session_state.bj_player.append(st.session_state.bj_deck.pop())
                if hand_value(st.session_state.bj_player) > 21:
                    st.session_state.bj_game_over = True
                    st.session_state.bj_losses += 1
                    st.session_state.bj_message = "💀 פוצצת! עברת 21"
                st.rerun()

        with col_stand:
            if st.button("✋ עצור (Stand)", key="bj_stand"):
                # דילר מושך עד 17
                while hand_value(st.session_state.bj_dealer) < 17:
                    st.session_state.bj_dealer.append(st.session_state.bj_deck.pop())
                p = hand_value(st.session_state.bj_player)
                d = hand_value(st.session_state.bj_dealer)
                if d > 21 or p > d:
                    st.session_state.bj_message = "🏆 ניצחת!"
                    st.session_state.bj_wins += 1
                elif p == d:
                    st.session_state.bj_message = "🤝 תיקו!"
                    st.session_state.bj_draws += 1
                else:
                    st.session_state.bj_message = "💀 הפסדת!"
                    st.session_state.bj_losses += 1
                st.session_state.bj_game_over = True
                st.rerun()

    # הודעת סיום
    if st.session_state.bj_message:
        if "ניצחת" in st.session_state.bj_message:
            css = "win-msg"
        elif "תיקו" in st.session_state.bj_message:
            css = "draw-msg"
        else:
            css = "lose-msg"
        st.markdown(f'<div class="{css}">{st.session_state.bj_message}</div>', unsafe_allow_html=True)

        if st.session_state.bj_game_over and not st.session_state.bj_game_over == True or "פוצצת" in st.session_state.bj_message or "ניצחת" in st.session_state.bj_message or "הפסדת" in st.session_state.bj_message or "תיקו" in st.session_state.bj_message:
            # הצג קלפי דילר מלאים
            if st.session_state.bj_dealer:
                st.markdown("### 🤖 כל קלפי הדילר")
                st.markdown(render_hand(st.session_state.bj_dealer), unsafe_allow_html=True)
                st.markdown(f"**סכום דילר: {hand_value(st.session_state.bj_dealer)}**")


# ==================== טאב 2: דמקה ====================
with tab2:
    st.markdown("## ⬛ דמקה")
    st.markdown("אתה ⚪ והמחשב ⚫ – כבוש את כל הכלים! לחץ על כלי ואז על היעד.")

    # אתחול לוח דמקה
    if "dk_board" not in st.session_state:
        board = [[None]*8 for _ in range(8)]
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 1:
                    board[r][c] = "B"  # מחשב שחור
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 1:
                    board[r][c] = "W"  # שחקן לבן
        st.session_state.dk_board = board
        st.session_state.dk_selected = None
        st.session_state.dk_turn = "W"
        st.session_state.dk_message = ""
        st.session_state.dk_wins = 0
        st.session_state.dk_losses = 0

    def get_moves(board, piece, r, c):
        moves = []
        jumps = []
        color = board[r][c]
        dirs = [(-1, -1), (-1, 1)] if color == "W" else [(1, -1), (1, 1)]
        if color in ["WK", "BK"]:
            dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]

        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if board[nr][nc] is None:
                    moves.append((nr, nc))
                else:
                    enemy = "B" if color in ["W","WK"] else "W"
                    if board[nr][nc] and board[nr][nc][0] == enemy:
                        jr, jc = nr+dr, nc+dc
                        if 0 <= jr < 8 and 0 <= jc < 8 and board[jr][jc] is None:
                            jumps.append((jr, jc, nr, nc))
        return jumps if jumps else moves, bool(jumps)

    def ai_move(board):
        pieces = [(r,c) for r in range(8) for c in range(8) if board[r][c] in ["B","BK"]]
        all_jumps = []
        all_moves = []
        for r,c in pieces:
            mvs, is_jump = get_moves(board, board[r][c], r, c)
            for m in mvs:
                if is_jump:
                    all_jumps.append((r,c,m))
                else:
                    all_moves.append((r,c,m))
        chosen = random.choice(all_jumps) if all_jumps else (random.choice(all_moves) if all_moves else None)
        if chosen:
            fr,fc,move = chosen
            tr,tc = move[0], move[1]
            board[tr][tc] = board[fr][fc]
            board[fr][fc] = None
            if len(move) == 4:
                board[move[2]][move[3]] = None
            if tr == 7 and board[tr][tc] == "B":
                board[tr][tc] = "BK"
        return board

    # ניקוד
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="score-box">🏆 ניצחונות שלך: {st.session_state.dk_wins}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="score-box" style="background:linear-gradient(135deg,#b71c1c,#c62828)">💀 ניצחונות מחשב: {st.session_state.dk_losses}</div>', unsafe_allow_html=True)

    # הצג לוח
    board = st.session_state.dk_board
    selected = st.session_state.dk_selected

    white_count = sum(1 for r in range(8) for c in range(8) if board[r][c] in ["W","WK"])
    black_count = sum(1 for r in range(8) for c in range(8) if board[r][c] in ["B","BK"])

    st.markdown(f"**⚪ שלך: {white_count} | ⚫ מחשב: {black_count}**")
    st.markdown(f"**תור: {'⚪ שלך' if st.session_state.dk_turn == 'W' else '⚫ מחשב'}**")

    valid_moves = []
    if selected:
        sr, sc = selected
        mvs, _ = get_moves(board, board[sr][sc], sr, sc)
        valid_moves = [(m[0], m[1]) for m in mvs]

    for r in range(8):
        cols_row = st.columns(8)
        for c in range(8):
            with cols_row[c]:
                cell = board[r][c]
                bg = "#8B4513" if (r+c)%2==1 else "#F5DEB3"
                is_sel = selected == (r,c)
                is_valid = (r,c) in valid_moves
                if is_sel:
                    bg = "#FFD700"
                elif is_valid:
                    bg = "#90EE90"

                emoji = ""
                if cell == "W": emoji = "⚪"
                elif cell == "WK": emoji = "👑"
                elif cell == "B": emoji = "⚫"
                elif cell == "BK": emoji = "🔮"

                if st.button(emoji or "·", key=f"dk_{r}_{c}",
                             help=f"({r},{c})",
                             use_container_width=True):
                    if st.session_state.dk_turn == "W":
                        if selected is None:
                            if cell in ["W","WK"]:
                                st.session_state.dk_selected = (r,c)
                        else:
                            if (r,c) in valid_moves:
                                sr,sc = selected
                                mvs,is_jump = get_moves(board,board[sr][sc],sr,sc)
                                board[r][c] = board[sr][sc]
                                board[sr][sc] = None
                                for m in mvs:
                                    if m[0]==r and m[1]==c and len(m)==4:
                                        board[m[2]][m[3]] = None
                                if r==0 and board[r][c]=="W":
                                    board[r][c]="WK"
                                st.session_state.dk_selected = None
                                st.session_state.dk_turn = "B"
                                # מחשב מהלך
                                st.session_state.dk_board = ai_move(board)
                                st.session_state.dk_turn = "W"
                                # בדוק ניצחון
                                w = sum(1 for row in range(8) for col in range(8) if st.session_state.dk_board[row][col] in ["W","WK"])
                                b = sum(1 for row in range(8) for col in range(8) if st.session_state.dk_board[row][col] in ["B","BK"])
                                if b == 0:
                                    st.session_state.dk_message = "🏆 ניצחת! כל כלי המחשב נלכדו!"
                                    st.session_state.dk_wins += 1
                                elif w == 0:
                                    st.session_state.dk_message = "💀 המחשב ניצח!"
                                    st.session_state.dk_losses += 1
                            elif cell in ["W","WK"]:
                                st.session_state.dk_selected = (r,c)
                            else:
                                st.session_state.dk_selected = None
                    st.rerun()

    if st.session_state.dk_message:
        css = "win-msg" if "ניצחת" in st.session_state.dk_message else "lose-msg"
        st.markdown(f'<div class="{css}">{st.session_state.dk_message}</div>', unsafe_allow_html=True)

    if st.button("🔄 משחק חדש", key="dk_new"):
        for key in ["dk_board","dk_selected","dk_turn","dk_message"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


# ==================== טאב 3: טריוויה ====================
with tab3:
    st.markdown("## ⚽ טריוויה נגד המחשב")
    st.markdown("ה-AI מייצר שאלות ואתה מנסה לנצח! 5 שאלות בכל סיבוב.")

    if "tv_questions" not in st.session_state:
        st.session_state.tv_questions = []
        st.session_state.tv_current = 0
        st.session_state.tv_score = 0
        st.session_state.tv_ai_score = 0
        st.session_state.tv_answered = False
        st.session_state.tv_selected = None
        st.session_state.tv_game_over = True
        st.session_state.tv_category = "כללי"

    category = st.selectbox("📚 קטגוריה:", [
        "כללי", "ספורט", "מדע", "היסטוריה",
        "גיאוגרפיה", "קולנוע ומוסיקה", "טכנולוגיה", "ישראל"
    ], key="tv_cat")

    if st.session_state.tv_game_over:
        if st.session_state.tv_score > 0 or st.session_state.tv_ai_score > 0:
            if st.session_state.tv_score > st.session_state.tv_ai_score:
                st.markdown('<div class="win-msg">🏆 ניצחת את המחשב!</div>', unsafe_allow_html=True)
            elif st.session_state.tv_score < st.session_state.tv_ai_score:
                st.markdown('<div class="lose-msg">💀 המחשב ניצח!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="draw-msg">🤝 תיקו!</div>', unsafe_allow_html=True)

        if st.button("🎯 התחל משחק טריוויה!", key="tv_start"):
            with st.spinner("🧠 ה-AI מייצר שאלות..."):
                prompt = f"""
צור 5 שאלות טריוויה בקטגוריה: {category}.
לכל שאלה תן בדיוק 4 תשובות אפשריות ורק אחת נכונה.

פורמט JSON בדיוק:
[
  {{
    "question": "שאלה",
    "options": ["תשובה1","תשובה2","תשובה3","תשובה4"],
    "answer": "התשובה הנכונה בדיוק כמו שהיא מופיעה ב-options",
    "explanation": "הסבר קצר"
  }}
]
החזר JSON בלבד ללא טקסט נוסף.
                """
                result = call_gemini(prompt)
                if result:
                    try:
                        import json
                        clean = result.replace("```json","").replace("```","").strip()
                        questions = json.loads(clean)
                        st.session_state.tv_questions = questions
                        st.session_state.tv_current = 0
                        st.session_state.tv_score = 0
                        st.session_state.tv_ai_score = 0
                        st.session_state.tv_answered = False
                        st.session_state.tv_selected = None
                        st.session_state.tv_game_over = False
                        st.session_state.tv_category = category
                        st.rerun()
                    except Exception:
                        st.error("שגיאה בטעינת שאלות. נסה שוב.")

    else:
        questions = st.session_state.tv_questions
        idx = st.session_state.tv_current

        # ניקוד
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="score-box">🧑 אתה: {st.session_state.tv_score}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="score-box" style="background:linear-gradient(135deg,#1b5e20,#2e7d32)">🤖 מחשב: {st.session_state.tv_ai_score}</div>', unsafe_allow_html=True)

        st.markdown(f"**שאלה {idx+1} מתוך {len(questions)}**")
        q = questions[idx]

        st.markdown(f'<div class="trivia-box"><b>{q["question"]}</b></div>', unsafe_allow_html=True)

        if not st.session_state.tv_answered:
            for opt in q["options"]:
                if st.button(opt, key=f"tv_opt_{opt}"):
                    st.session_state.tv_selected = opt
                    st.session_state.tv_answered = True
                    # בדוק תשובה
                    if opt == q["answer"]:
                        st.session_state.tv_score += 1
                    # מחשב בוחר אקראי (60% סיכוי)
                    ai_correct = random.random() < 0.6
                    if ai_correct:
                        st.session_state.tv_ai_score += 1
                    st.rerun()
        else:
            selected = st.session_state.tv_selected
            correct = q["answer"]
            ai_correct = st.session_state.tv_ai_score > (st.session_state.tv_score - (1 if selected == correct else 0))

            for opt in q["options"]:
                if opt == correct:
                    st.success(f"✅ {opt} – נכון!")
                elif opt == selected and selected != correct:
                    st.error(f"❌ {opt} – בחרת זאת")
                else:
                    st.write(f"  {opt}")

            st.info(f"💡 {q.get('explanation','')}")

            if st.button("➡️ שאלה הבאה", key="tv_next"):
                if idx + 1 < len(questions):
                    st.session_state.tv_current += 1
                    st.session_state.tv_answered = False
                    st.session_state.tv_selected = None
                else:
                    st.session_state.tv_game_over = True
                st.rerun()


# ==================== טאב 4: נחש ====================
with tab4:
    st.markdown("## 🐍 משחק נחש")
    st.markdown("השתמש בכפתורים לניהול הנחש – אכול 🍎 לגדול! אל תיפגע בקירות או בעצמך.")

    GRID = 15

    if "snake_body" not in st.session_state:
        st.session_state.snake_body = [(7,7),(7,6),(7,5)]
        st.session_state.snake_dir = (0,1)
        st.session_state.snake_food = (3,3)
        st.session_state.snake_score = 0
        st.session_state.snake_high = 0
        st.session_state.snake_alive = True
        st.session_state.snake_started = False

    def place_food(body):
        while True:
            pos = (random.randint(0,GRID-1), random.randint(0,GRID-1))
            if pos not in body:
                return pos

    def move_snake():
        if not st.session_state.snake_alive:
            return
        body = st.session_state.snake_body
        dr, dc = st.session_state.snake_dir
        head = (body[0][0]+dr, body[0][1]+dc)
        if (head[0]<0 or head[0]>=GRID or head[1]<0 or head[1]>=GRID or head in body):
            st.session_state.snake_alive = False
            if st.session_state.snake_score > st.session_state.snake_high:
                st.session_state.snake_high = st.session_state.snake_score
            return
        body.insert(0, head)
        if head == st.session_state.snake_food:
            st.session_state.snake_score += 10
            st.session_state.snake_food = place_food(body)
        else:
            body.pop()
        st.session_state.snake_body = body

    # ציור לוח
    grid = [["⬜" if (i+j)%2==0 else "🟩" for j in range(GRID)] for i in range(GRID)]
    for r,c in st.session_state.snake_body[1:]:
        grid[r][c] = "🟦"
    if st.session_state.snake_body:
        hr,hc = st.session_state.snake_body[0]
        grid[hr][hc] = "🟪"
    fr,fc = st.session_state.snake_food
    grid[fr][fc] = "🍎"

    board_str = "\n".join("".join(row) for row in grid)
    st.code(board_str, language=None)

    col1,col2,col3 = st.columns(3)
    with col2:
        if st.button("⬆️", key="sn_up", use_container_width=True):
            if st.session_state.snake_dir != (1,0):
                st.session_state.snake_dir = (-1,0)
            move_snake()
            st.rerun()

    col1,col2,col3 = st.columns(3)
    with col1:
        if st.button("⬅️", key="sn_left", use_container_width=True):
            if st.session_state.snake_dir != (0,1):
                st.session_state.snake_dir = (0,-1)
            move_snake()
            st.rerun()
    with col2:
        if st.button("⬇️", key="sn_down", use_container_width=True):
            if st.session_state.snake_dir != (-1,0):
                st.session_state.snake_dir = (1,0)
            move_snake()
            st.rerun()
    with col3:
        if st.button("➡️", key="sn_right", use_container_width=True):
            if st.session_state.snake_dir != (0,-1):
                st.session_state.snake_dir = (0,1)
            move_snake()
            st.rerun()

    col1,col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="score-box">🍎 ניקוד: {st.session_state.snake_score}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="score-box" style="background:linear-gradient(135deg,#1b5e20,#2e7d32)">🏆 שיא: {st.session_state.snake_high}</div>', unsafe_allow_html=True)

    if not st.session_state.snake_alive:
        st.markdown(f'<div class="lose-msg">💀 המשחק נגמר! ניקוד: {st.session_state.snake_score}</div>', unsafe_allow_html=True)
        if st.button("🔄 התחל מחדש", key="sn_restart"):
            st.session_state.snake_body = [(7,7),(7,6),(7,5)]
            st.session_state.snake_dir = (0,1)
            st.session_state.snake_food = place_food([(7,7),(7,6),(7,5)])
            st.session_state.snake_score = 0
            st.session_state.snake_alive = True
            st.rerun()
    else:
        st.info("💡 לחץ על כפתורי החצים כדי להזיז את הנחש. כל לחיצה = צעד אחד.")


# ==================== טאב 5: 20 שאלות ====================
with tab5:
    st.markdown("## 🧠 20 שאלות נגד ה-AI")
    st.markdown("חשוב על משהו – ה-AI ינסה לנחש בעזרת שאלות כן/לא! (או להיפך – אתה שואל!)")

    if "tq_mode" not in st.session_state:
        st.session_state.tq_mode = None
        st.session_state.tq_questions_asked = []
        st.session_state.tq_count = 0
        st.session_state.tq_secret = ""
        st.session_state.tq_game_over = False
        st.session_state.tq_won = False

    if st.session_state.tq_mode is None:
        st.markdown("### 🎯 בחר מצב משחק:")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
                <div class="game-box">
                    <h3>🤖 AI מנחש</h3>
                    <p>חשוב על משהו – ה-AI ישאל שאלות כן/לא וינסה לנחש!</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🤖 AI מנחש אותי!", key="tq_ai_guess"):
                st.session_state.tq_mode = "ai_guesses"
                st.session_state.tq_questions_asked = []
                st.session_state.tq_count = 0
                st.session_state.tq_game_over = False
                st.rerun()
        with col2:
            st.markdown("""
                <div class="game-box">
                    <h3>🧑 אני מנחש</h3>
                    <p>ה-AI חושב על משהו ואתה שואל שאלות כן/לא לנחש!</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🧑 אני מנחש!", key="tq_i_guess"):
                st.session_state.tq_mode = "i_guess"
                st.session_state.tq_questions_asked = []
                st.session_state.tq_count = 0
                st.session_state.tq_game_over = False
                with st.spinner("🧠 ה-AI חושב על משהו..."):
                    secret_prompt = "בחר משהו מוחשי לחשוב עליו (חיה, חפץ, מקום) – כתוב רק את המילה עצמה בעברית, ללא הסבר."
                    secret = call_gemini(secret_prompt)
                    st.session_state.tq_secret = secret.strip() if secret else "כלב"
                st.rerun()

    elif st.session_state.tq_mode == "ai_guesses":
        st.markdown("### 🤖 ה-AI מנחש")
        st.markdown("**חשוב על משהו (חיה, חפץ, מקום, אדם מפורסם...) ואל תגלה!**")

        if not st.session_state.tq_game_over:
            st.markdown(f"**שאלה {st.session_state.tq_count + 1} מתוך 20**")

            # ה-AI שואל שאלה
            history = "\n".join([f"ש: {q} | ת: {a}" for q,a in st.session_state.tq_questions_asked])
            prompt = f"""
אתה משחק 20 שאלות ומנסה לנחש מה חשב המשתמש.
שאלות ותשובות עד כה:
{history if history else "אין עדיין"}
שאלות שנותרו: {20 - st.session_state.tq_count}

{"נחש עכשיו את התשובה!" if st.session_state.tq_count >= 15 else "שאל שאלת כן/לא אחת חכמה שתצמצם את האפשרויות."}
כתוב רק את השאלה בעברית, ללא הסבר.
            """
            if not st.session_state.tq_questions_asked or st.session_state.tq_questions_asked[-1][1] != "":
                with st.spinner("🤔 ה-AI חושב על שאלה..."):
                    ai_q = call_gemini(prompt)
                if ai_q:
                    st.markdown(f'<div class="ai-thinking">🤖 ה-AI שואל: <b>{ai_q.strip()}</b></div>', unsafe_allow_html=True)

                    if st.session_state.tq_count >= 15:
                        guess = st.text_input("נחש ה-AI:", key="tq_verify")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ נכון!", key="tq_correct"):
                                st.session_state.tq_game_over = True
                                st.session_state.tq_won = False
                                st.rerun()
                        with col2:
                            if st.button("❌ טעות!", key="tq_wrong"):
                                st.session_state.tq_game_over = True
                                st.session_state.tq_won = True
                                st.rerun()
                    else:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("✅ כן", key="tq_yes"):
                                st.session_state.tq_questions_asked.append((ai_q.strip(), "כן"))
                                st.session_state.tq_count += 1
                                st.rerun()
                        with col2:
                            if st.button("❌ לא", key="tq_no"):
                                st.session_state.tq_questions_asked.append((ai_q.strip(), "לא"))
                                st.session_state.tq_count += 1
                                st.rerun()
                        with col3:
                            if st.button("🤷 לפעמים", key="tq_maybe"):
                                st.session_state.tq_questions_asked.append((ai_q.strip(), "לפעמים"))
                                st.session_state.tq_count += 1
                                st.rerun()

            if st.session_state.tq_count >= 20 and not st.session_state.tq_game_over:
                st.session_state.tq_game_over = True
                st.session_state.tq_won = True

        if st.session_state.tq_game_over:
            if st.session_state.tq_won:
                st.markdown('<div class="win-msg">🏆 ניצחת! ה-AI לא הצליח לנחש!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="lose-msg">💀 ה-AI ניחש נכון!</div>', unsafe_allow_html=True)

    elif st.session_state.tq_mode == "i_guess":
        st.markdown("### 🧑 אתה מנחש!")
        st.markdown("**ה-AI חשב על משהו – שאל שאלות כן/לא לנחש!**")
        st.markdown(f"**שאלה {st.session_state.tq_count + 1} מתוך 20**")

        if not st.session_state.tq_game_over:
            user_q = st.text_input("✍️ שאלתך (כן/לא):", placeholder="האם זה חיה?", key="tq_user_q")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📨 שאל!", key="tq_ask"):
                    if user_q.strip():
                        prompt = f"""
אתה ה-AI ב-20 שאלות. חשבת על: {st.session_state.tq_secret}
השאלה: {user_q}
ענה רק "כן", "לא", או "לפעמים". מילה אחת בלבד.
                        """
                        with st.spinner("🤔 ה-AI חושב..."):
                            answer = call_gemini(prompt)
                        if answer:
                            ans = answer.strip()
                            st.session_state.tq_questions_asked.append((user_q, ans))
                            st.session_state.tq_count += 1
                            st.rerun()
            with col2:
                guess = st.text_input("🎯 אני מנחש שזה:", key="tq_my_guess")
                if st.button("✅ נחשתי!", key="tq_final_guess"):
                    if guess.strip().lower() in st.session_state.tq_secret.lower() or st.session_state.tq_secret.lower() in guess.strip().lower():
                        st.session_state.tq_won = True
                    st.session_state.tq_game_over = True
                    st.rerun()

            # הצג היסטוריה
            for q,a in reversed(st.session_state.tq_questions_asked[-5:]):
                color = "#2e7d32" if a == "כן" else "#c62828" if a == "לא" else "#e65100"
                st.markdown(f'<div class="ai-thinking">❓ {q} → <b style="color:{color}">{a}</b></div>', unsafe_allow_html=True)

            if st.session_state.tq_count >= 20 and not st.session_state.tq_game_over:
                st.session_state.tq_game_over = True
                st.session_state.tq_won = False

        if st.session_state.tq_game_over:
            st.markdown(f"**ה-AI חשב על: `{st.session_state.tq_secret}`**")
            if st.session_state.tq_won:
                st.markdown('<div class="win-msg">🏆 כל הכבוד! ניחשת נכון!</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="lose-msg">💀 לא הצלחת לנחש!</div>', unsafe_allow_html=True)

    if st.session_state.tq_mode is not None:
        if st.button("🔄 משחק חדש", key="tq_reset"):
            for k in ["tq_mode","tq_questions_asked","tq_count","tq_secret","tq_game_over","tq_won"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

# --- פוטר ---
st.markdown("---")
st.markdown("""
    <p style='text-align:center; color:gray;'>
        🎮 משחקים נגד המחשב | פותח באמצעות Gemini AI | © 2026
    </p>
""", unsafe_allow_html=True)