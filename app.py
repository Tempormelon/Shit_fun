import streamlit as st
import pandas as pd
import os
import streamlit.components.v1 as components
from datetime import datetime, date, timedelta
import altair as alt
import base64
import json
import re  # 必须导入正则库
from openai import OpenAI
import yt_dlp
# --- 1. 页面配置 & 皮肤注入 ---
st.set_page_config(page_title="💩 XXXX", page_icon="🚽", layout="wide")

# 注入自定义 CSS
st.markdown("""
<style>
    /* 全局颜色配置 */
    .stApp { background-color: #FEF9E7; }
    h1, h2, h3, h4 { color: #5D4037 !important; font-family: 'Microsoft YaHei', sans-serif; }
    .stApp p, .stApp small, .stApp div, .stApp span, .stApp label, .stCaption, .stMarkdown {
        color: #5D4037 !important;
    }
    div[data-testid="stDataFrame"] div[role="grid"] {
        color: #5D4037 !important;
        background-color: rgba(255, 255, 255, 0.5) !important;
    }
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        color: #5D4037 !important;
        font-weight: bold;
    }
    .stButton>button {
        border-radius: 20px;
        border: 2px solid #8B4513 !important;
        color: #8B4513 !important;
        background-color: #FFF8DC !important;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #8B4513 !important;
        color: white !important;
        border-color: #8B4513 !important;
    }
    input[type="text"], input[type="number"], div[data-baseweb="select"] {
        color: #5D4037 !important;
        background-color: #FFFFFF !important;
    }
    div[data-testid="stMetricValue"] { color: #8B4513 !important; font-weight: 900; }
    div[data-testid="stMetricLabel"] { color: #A0522D !important; }
    hr { border-color: #D2691E; }
    .milestone-card {
        background-color: #FFF8DC;
        border-left: 5px solid #8B4513;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .milestone-date { font-weight: bold; font-size: 1.1em; color: #A0522D; }
    .milestone-event { font-size: 1.2em; font-weight: bold; margin: 5px 0; }
    .milestone-people { font-size: 0.9em; color: #666; font-style: italic; }

    /* 聊天气泡样式 */
    .stChatMessage { background-color: rgba(255, 255, 255, 0.5); border-radius: 10px; padding: 10px; margin-bottom: 10px; }

    @keyframes shine { 0% {background-position: left;} 100% {background-position: right;} }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 👇👇👇 API Key 👇👇👇
DEEPSEEK_API_KEY = "请使用你自己的API Key代替"
# 2. OpenRouter 的地址
OPENROUTER_BASE_URL = "请使用你自己的API地址代替"
# 3. 模型的名字
AI_MODEL_NAME = "请使用你自己的模型名称代替"
# ==========================================

DB_FILE = "shit_database.csv"
HISTORY_FILE = "milestones.csv"
GAME_DB_FILE = "game_leaderboard.csv"
# 新增视频播放列表文件
PLAYLIST_FILE = "video_playlist.csv"

MEMBERS = ["请使用你自己的用户姓名1", "请使用你自己的用户姓名2", "请使用你自己的用户姓名3"]  # 请替换为实际的用户姓名列表
SECRET_SALT = 8848  # 加密盐值


# --- 2. 核心数据逻辑 ---

def load_data():
    if not os.path.exists(DB_FILE): return pd.DataFrame(columns=["日期", "姓名", "次数", "备注"])
    try:
        df = pd.read_csv(DB_FILE);
        df['备注'] = df['备注'].fillna("");
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except:
        return pd.DataFrame(columns=["日期", "姓名", "次数", "备注"])


def update_record(target_date, name, delta_count, new_comment=None):
    df = load_data()
    if isinstance(target_date, str):
        target_date_dt = pd.to_datetime(target_date)
    else:
        target_date_dt = pd.to_datetime(target_date)
    mask = (df['日期'] == target_date_dt) & (df['姓名'] == name)
    if mask.any():
        idx = df[mask].index[0]
        current_count = int(df.at[idx, '次数'])
        new_count = max(0, current_count + int(delta_count))
        df.at[idx, '次数'] = new_count
        if new_comment:
            old_comment = str(df.at[idx, '备注'])
            if old_comment:
                df.at[idx, '备注'] = f"{old_comment}, {new_comment}"
            else:
                df.at[idx, '备注'] = new_comment
    else:
        final_count = max(0, int(delta_count))
        if final_count > 0 or new_comment:
            new_row = pd.DataFrame([{"日期": target_date_dt, "姓名": name, "次数": final_count,
                                     "备注": new_comment if new_comment else ""}])
            df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')


def load_history():
    if not os.path.exists(HISTORY_FILE): return pd.DataFrame(columns=["日期", "事件", "人物"])
    try:
        df = pd.read_csv(HISTORY_FILE);
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except:
        return pd.DataFrame(columns=["日期", "事件", "人物"])


def add_milestone(date_val, event, people):
    df = load_history()
    new_row = pd.DataFrame([{"日期": pd.to_datetime(date_val), "事件": event, "人物": people}])
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.sort_values(by="日期", ascending=False)
    df.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')


def load_leaderboard():
    if not os.path.exists(GAME_DB_FILE): return pd.DataFrame(columns=["日期", "姓名", "分数"])
    try:
        df = pd.read_csv(GAME_DB_FILE);
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    except:
        return pd.DataFrame(columns=["日期", "姓名", "分数"])


def verify_and_save_score(name, code):
    try:
        json_str = base64.b64decode(code).decode('utf-8')
        data = json.loads(json_str)
        score = int(data.get('s'))
        check_sum = int(data.get('h'))
        expected_check = (score * 1337) + SECRET_SALT
        if check_sum == expected_check:
            df = load_leaderboard()
            new_row = pd.DataFrame([{"日期": datetime.now(), "姓名": name, "分数": score}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(GAME_DB_FILE, index=False, encoding='utf-8-sig')
            return True, score
        else:
            return False, 0
    except Exception as e:
        return False, 0


def get_top_leaderboard():
    df = load_leaderboard()
    if df.empty: return pd.DataFrame(columns=["排名", "选手", "最高分", "创造时间"])
    df = df.sort_values(by="分数", ascending=False)
    df_top = df.drop_duplicates(subset=["姓名"], keep="first").reset_index(drop=True)
    display_data = []
    for idx, row in df_top.iterrows():
        display_data.append({
            "排名": f"第 {idx + 1} 名",
            "选手": row['姓名'],
            "最高分": int(row['分数']),
            "创造时间": row['日期'].strftime('%m-%d %H:%M')
        })
    return pd.DataFrame(display_data)


def get_week_range(target_date):
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()
    days_from_sunday = (target_date.weekday() + 1) % 7
    start_sunday = target_date - timedelta(days=days_from_sunday)
    return start_sunday, start_sunday + timedelta(days=6)


def get_weekly_stats(df, start_date, end_date):
    mask = (df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)
    week_df = df[mask].copy()
    if week_df.empty: return None, 0.0
    total_counts = week_df.groupby("姓名")['次数'].sum()
    if total_counts.empty: return None, 0.0
    today_date = date.today()
    if end_date < today_date:
        days_passed = 7
    elif start_date > today_date:
        days_passed = 1
    else:
        days_passed = min(7, max(1, (today_date - start_date).days + 1))
    return total_counts[total_counts == total_counts.max()].index.tolist(), week_df['次数'].sum() / days_passed / len(
        MEMBERS)


# --- 视频播放列表相关辅助函数 ---
def load_playlist():
    if not os.path.exists(PLAYLIST_FILE):
        return pd.DataFrame(columns=["时间", "点播人", "链接", "备注"])
    try:
        return pd.read_csv(PLAYLIST_FILE)
    except:
        return pd.DataFrame(columns=["时间", "点播人", "链接", "备注"])

def save_playlist(df):
    df.to_csv(PLAYLIST_FILE, index=False, encoding='utf-8-sig')

def extract_url(text):
    url_pattern = re.compile(r'https?://\S+')
    match = url_pattern.search(text)
    if match:
        return match.group(0)
    return None


# --- 3. 游戏 HTML ---
game_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; padding: 0; overflow: hidden; background-color: #FEF9E7; font-family: 'Arial', sans-serif; touch-action: none; }}
    #gameCanvas {{ display: block; margin: 0 auto; background: #FFF8DC; border: 2px solid #8B4513; border-radius: 10px; }}
    #ui {{ position: absolute; top: 10px; left: 50%; transform: translateX(-50%); width: 300px; text-align: center; pointer-events: none; }}
    .score-board {{ font-size: 20px; font-weight: bold; color: #5D4037; }}
    #startScreen, #gameOverScreen {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; border: 3px solid #8B4513; box-shadow: 0 4px 10px rgba(0,0,0,0.2); width: 80%; max-width: 300px; }}
    button {{ background: #8B4513; color: white; border: none; padding: 10px 20px; font-size: 18px; border-radius: 20px; cursor: pointer; margin-top: 10px; }}
    button:active {{ background: #5D4037; }}
    .code-box {{ background: #eee; padding: 10px; margin: 10px 0; border-radius: 5px; word-break: break-all; font-family: monospace; color: #333; font-size: 14px; user-select: all; }}
</style>
</head>
<body>
<div id="ui"><div class="score-board">得分: <span id="score">0</span> | 生命: <span id="lives">❤️❤️❤️</span></div></div>
<canvas id="gameCanvas"></canvas>
<div id="startScreen"><h2 style="color:#5D4037; margin:0 0 10px 0;">💩 进击的粑粑</h2><p style="color:#8B4513;">左右滑动控制马桶<br>漏接3个就输了！</p><button onclick="startGame()">开始挑战</button></div>
<div id="gameOverScreen" style="display: none;"><h2 style="color:#5D4037;">游戏结束!</h2><p style="color:#8B4513;">得分: <strong id="finalScoreDisplay">0</strong></p><p style="color:#666; font-size:0.9em;">👇 长按复制下方红色战绩码 👇</p><div id="resultCode" class="code-box" style="color: #D2691E; border: 1px dashed #D2691E;"></div><p style="color:#999; font-size:0.8em;">(粘贴到下方输入框即可上榜)</p><button onclick="startGame()">再来一局</button></div>
<script>
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let windowWidth = window.innerWidth;
    let gameWidth = Math.min(windowWidth - 20, 600);
    let gameHeight = 400;
    canvas.width = gameWidth; canvas.height = gameHeight;
    let toilet = {{ x: gameWidth / 2, y: gameHeight - 60, width: 50, height: 50 }};
    let poops = []; let score = 0; let lives = 3; let gameRunning = false; let frameCount = 0;
    let baseSpeed = 1.8; let speedMultiplier = 0.25; const SALT = {SECRET_SALT}; 
    function generateCode(s) {{ let h = (s * 1337) + SALT; let data = {{ "s": s, "h": h }}; return btoa(JSON.stringify(data)); }}
    function moveToilet(clientX) {{ let rect = canvas.getBoundingClientRect(); let relativeX = clientX - rect.left; if(relativeX > 0 && relativeX < canvas.width) {{ toilet.x = relativeX - toilet.width / 2; }} }}
    canvas.addEventListener('mousemove', e => {{ if(gameRunning) moveToilet(e.clientX); }});
    canvas.addEventListener('touchmove', e => {{ if(gameRunning) {{ e.preventDefault(); moveToilet(e.touches[0].clientX); }} }}, {{passive: false}});
    function spawnPoop() {{ let size = 30; let x = Math.random() * (canvas.width - size); let speed = baseSpeed + (score / 10) * speedMultiplier; speed = Math.min(speed, 6.5); poops.push({{ x: x, y: -size, size: size, speed: speed }}); }}
    function draw() {{ if (!gameRunning) return; ctx.clearRect(0, 0, canvas.width, canvas.height); ctx.font = "40px Arial"; ctx.fillText("🚽", toilet.x, toilet.y + 40); frameCount++; let currentSpawnRate = Math.max(25, 75 - Math.floor(score / 15) * 5); if (frameCount % currentSpawnRate === 0) {{ spawnPoop(); }} for (let i = 0; i < poops.length; i++) {{ let p = poops[i]; p.y += p.speed; ctx.font = "30px Arial"; ctx.fillText("💩", p.x, p.y + 30); if (p.x < toilet.x + toilet.width && p.x + p.size > toilet.x && p.y < toilet.y + toilet.height && p.y + p.size > toilet.y) {{ score++; document.getElementById('score').innerText = score; poops.splice(i, 1); i--; }} else if (p.y > canvas.height) {{ lives--; updateLives(); poops.splice(i, 1); i--; if (lives <= 0) gameOver(); }} }} requestAnimationFrame(draw); }}
    function updateLives() {{ let heartStr = ""; for(let i=0; i<lives; i++) heartStr += "❤️"; document.getElementById('lives').innerText = heartStr; }}
    function startGame() {{ score = 0; lives = 3; poops = []; gameRunning = true; document.getElementById('score').innerText = "0"; updateLives(); document.getElementById('startScreen').style.display = 'none'; document.getElementById('gameOverScreen').style.display = 'none'; draw(); }}
    function gameOver() {{ gameRunning = false; document.getElementById('finalScoreDisplay').innerText = score; let code = generateCode(score); document.getElementById('resultCode').innerText = code; document.getElementById('gameOverScreen').style.display = 'block'; }}
</script>
</body>
</html>
"""

# --- 4. UI 主程序 ---
df = load_data()
today = date.today()
current_start, current_end = get_week_range(today)

st.markdown(
    "<h1 style='text-align: center; font-size: 2.8em;'>🚽 窜稀拉屎𠈌众帮 <span style='color:#D2691E; font-size:0.5em'>Pro</span></h1>",
    unsafe_allow_html=True)

curr_winners, curr_avg = get_weekly_stats(df, current_start, current_end)
if curr_winners and sum(df[df['日期'].dt.date >= current_start]['次数']) > 0:
    st.markdown(f"""
    <div style='background: linear-gradient(45deg, #B8860B, #FFD700, #B8860B); background-size: 200% 200%; animation: shine 3s infinite; padding: 25px; border-radius: 15px; text-align: center; color: #5D4037; box-shadow: 0 10px 20px rgba(0,0,0,0.15); margin-bottom: 20px; border: 2px solid #FFF8DC;'>
        <h3 style='margin:0; color: #5D4037;'>👑 本周屎王 ({current_start.strftime('%m.%d')} - {current_end.strftime('%m.%d')})</h3>
        <h1 style='font-size: 50px; margin: 10px 0; text-shadow: 2px 2px 0px rgba(255,255,255,0.5);'>{" & ".join(curr_winners)}</h1>
        <p style='margin:0'>全员日均产量: <b>{curr_avg:.2f}</b> 次/人/天</p>
    </div>""", unsafe_allow_html=True)
else:
    st.info("🌬️ 本周的风还在吹，王座空悬，等你来拉！")

# --- Tabs (这里必须定义 6 个) ---
tab_board, tab_input, tab_history, tab_game, tab_ai, tab_video = st.tabs(
    ["📊 屎况", "🛠️ 记录板", "📜 Hall of Shit", "🎮 玩💩", "🤖 你好小史", "🎬 艺术交流"])

with tab_board:
    st.subheader("📊 本周屎况")
    week_mask = (df['日期'].dt.date >= current_start) & (df['日期'].dt.date <= current_end)
    week_df = df[week_mask].copy()
    if not week_df.empty:
        pivot_count = week_df.pivot_table(index='姓名', columns='日期', values='次数', aggfunc='sum').fillna(0)
        pivot_count = pivot_count.reindex(MEMBERS, fill_value=0)
        pivot_count['本周总计'] = pivot_count.sum(axis=1)
        current_days_divisor = 7 if current_end < today else min(7, max(1, (today - current_start).days + 1))
        pivot_count['日均'] = pivot_count['本周总计'] / current_days_divisor
        display_df = pd.DataFrame(index=MEMBERS)
        for i in range(7):
            d = current_start + timedelta(days=i)
            col_name = f"{d.strftime('%m.%d')} {['日', '一', '二', '三', '四', '五', '六'][d.weekday()]}"
            col_data = []
            for member in MEMBERS:
                record = week_df[(week_df['日期'].dt.date == d) & (week_df['姓名'] == member)]
                if not record.empty:
                    cnt = int(record.iloc[0]['次数']);
                    rem = record.iloc[0]['备注']
                    cell_str = f"{cnt}" + (f" 💬" if rem else "") if cnt > 0 else "-"
                else:
                    cell_str = "-"
                col_data.append(cell_str)
            display_df[col_name] = col_data
        display_df['日均'] = pivot_count['日均']
        display_df['评价'] = display_df['日均'].apply(
            lambda x: "👍 优秀" if x > pivot_count['日均'].mean() else "👎 加油")
        st.dataframe(display_df, use_container_width=True, column_config={
            "日均": st.column_config.ProgressColumn("日均产量", help=f"截止今日({current_days_divisor}天)的平均值",
                                                    format="%.2f", min_value=0, max_value=4)})
        st.caption("🔍 本周备注详情：")
        notes_df = week_df[week_df['备注'] != ""][['日期', '姓名', '备注']].sort_values('日期', ascending=False)
        for _, row in notes_df.iterrows(): st.text(f"{row['日期'].strftime('%m-%d')} {row['姓名']}: {row['备注']}")
    else:
        st.info("本周还没人开张。")

    st.subheader("📈 30天产量走势")
    if not df.empty:
        chart_df = df[df['日期'] >= pd.Timestamp(today - timedelta(days=30))].copy()
        if not chart_df.empty:
            std_df = chart_df.groupby('姓名')['次数'].std().reset_index();
            std_df.columns = ['姓名', '标准差'];
            std_df['标准差'] = std_df['标准差'].fillna(0).round(2)
            chart_df = pd.merge(chart_df, std_df, on='姓名', how='left')
            selection = alt.selection_point(fields=['姓名'], bind='legend')
            chart = alt.Chart(chart_df).mark_line(point=True, strokeWidth=3, interpolate='step-after').encode(
                x=alt.X('日期:T',
                        axis=alt.Axis(format='%m-%d', title=None, labelColor='#5D4037', titleColor='#5D4037')),
                y=alt.Y('次数:Q', axis=alt.Axis(tickMinStep=1, labelColor='#5D4037', titleColor='#5D4037'),
                        title='次数'),
                color=alt.Color('姓名:N', scale=alt.Scale(scheme='tableau10')),
                tooltip=[alt.Tooltip('日期:T', format='%Y-%m-%d'), '姓名', '次数', '备注',
                         alt.Tooltip('标准差', title='波动')],
                opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
            ).add_params(selection).properties(height=350).interactive()
            st.altair_chart(chart, use_container_width=True)
    with st.expander("🏆 每周屎王"):
        history_data = []
        iter_date = date(2025, 10, 19)
        while iter_date <= today:
            iter_end = iter_date + timedelta(days=6)
            w_winners, w_avg = get_weekly_stats(df, iter_date, iter_end)
            if w_winners: history_data.append(
                {"周期": f"{iter_date.strftime('%m.%d')}", "王者": " & ".join(w_winners), "日均": f"{w_avg:.2f}"})
            iter_date += timedelta(days=7)
        if history_data: st.dataframe(pd.DataFrame(history_data).iloc[::-1], use_container_width=True, hide_index=True)

with tab_input:
    c_date, c_title = st.columns([1, 4])
    with c_date:
        entry_date = st.date_input("📅 时光机", today)
    with c_title:
        st.subheader(f"🛠️记录板 ({entry_date.strftime('%Y-%m-%d')})")
    cols = st.columns(4)
    for i, member in enumerate(MEMBERS):
        day_mask = (df['日期'].dt.date == entry_date) & (df['姓名'] == member)
        current_data = df[day_mask]
        curr_count = int(current_data.iloc[0]['次数']) if not current_data.empty else 0
        curr_note = current_data.iloc[0]['备注'] if not current_data.empty else ""
        face = "😐";
        if curr_count >= 1: face = "😌";
        if curr_count >= 2: face = "😤";
        if curr_count >= 3: face = "😱"
        with cols[i % 4]:
            with st.container(border=True):
                st.markdown(
                    f"<div style='text-align:center; font-size:1.2em; font-weight:bold; color:#8B4513'>{face} {member}</div>",
                    unsafe_allow_html=True)
                st.metric("今日", f"{curr_count}", label_visibility="collapsed")
                c1, c2 = st.columns(2)
                if c1.button("➕", key=f"add_{member}", use_container_width=True): update_record(entry_date, member,
                                                                                                1); st.rerun()
                if c2.button("➖", key=f"sub_{member}", use_container_width=True): update_record(entry_date, member,
                                                                                                -1); st.rerun()
                with st.popover(f"📝"):
                    new_note = st.text_input("...", value=curr_note, key=f"note_{member}")
                    if st.button("存", key=f"sav_{member}"):
                        if new_note != curr_note: update_record(entry_date, member, 0, new_note); st.rerun()

with tab_history:
    st.subheader("📜 屎册")
    with st.expander("✍️ 屎官执笔"):
        with st.form("history_form"):
            col1, col2 = st.columns([1, 2])
            h_date = col1.date_input("发生日期", today)
            h_people = col2.multiselect("涉及人物", MEMBERS)
            h_event = st.text_area("大事件描述")
            if st.form_submit_button("载入屎册"):
                if h_event and h_people:
                    add_milestone(h_date, h_event, "、".join(h_people));
                    st.success("✅ 已载入屎册！");
                    st.rerun()
                else:
                    st.error("❌ 请填写事件和人物")
    hist_df = load_history()
    if not hist_df.empty:
        hist_df = hist_df.sort_values(by="日期", ascending=False)
        st.markdown("---")
        for _, row in hist_df.iterrows():
            st.markdown(f"""
            <div class="milestone-card">
                <div class="milestone-date">📅 {row['日期'].strftime('%Y年%m月%d日')}</div>
                <div class="milestone-event">{row['事件']}</div>
                <div class="milestone-people">👥 涉及: {row['人物']}</div>
            </div>""", unsafe_allow_html=True)
        with st.expander("🗑️ 管理"):
            edited_hist = st.data_editor(hist_df, num_rows="dynamic", use_container_width=True)
            if st.button("保存修改"): edited_hist.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig'); st.success(
                "已更新"); st.rerun()
    else:
        st.info("📜 屎册暂无记录...")

with tab_game:
    st.subheader("🎮 进击的巨屎 (休闲小游戏)")
    components.html(game_html, height=450, scrolling=False)
    st.markdown("---")
    col_reg, col_rank = st.columns([1, 1])
    with col_reg:
        st.info("💡 游戏结束后会生成一串红色乱码，请复制并粘贴到下方验证！")
        with st.form("game_score_form"):
            g_name = st.selectbox("我是谁", MEMBERS)
            g_code = st.text_input("战绩码 (请粘贴)", placeholder="例如: eyJzIjoyLCJoIjo1OTIyfQ==")
            if st.form_submit_button("📜 验证并上传"):
                if g_code:
                    success, score = verify_and_save_score(g_name, g_code.strip())
                    if success:
                        st.balloons();
                        st.success(f"✅ 验证通过！{g_name} 的 {score} 分已上榜！");
                        st.rerun()
                    else:
                        st.error("❌ 验证失败！战绩码无效或被篡改！")
                else:
                    st.warning("请粘贴战绩码")
    with col_rank:
        st.subheader("🏆 接翔高手榜 (TOP)")
        top_df = get_top_leaderboard()
        if not top_df.empty:
            # 修复：JSON报错问题
            max_score = int(top_df['最高分'].max())
            st.dataframe(top_df, use_container_width=True, hide_index=True, column_config={
                "排名": st.column_config.TextColumn(width="small"),
                "最高分": st.column_config.ProgressColumn("最高纪录", format="%d", min_value=0, max_value=max_score)})
        else:
            st.caption("暂无战绩，快来抢第一！")

# ========== Tab 5: AI 聊天 ==========
with tab_ai:
    st.subheader("🤖 拉屎AI助手——XX")
    st.caption(f"🧠 已连接 OpenRouter | 📚 读取数据: 实时记录/史册/游戏榜 | 毒舌模式ON")

    # --- 1. 数据准备 (RAG 核心：把三份数据打包成字符串) ---
    rag_context = ""

    # (A) 读取拉屎记录 (最近 150 条)
    try:
        if not df.empty:
            recent_df = df.sort_values(by="日期", ascending=False).head(150)
            data_str = recent_df.to_csv(index=False)
            rag_context += f"\n【数据表1：最近150条拉屎记录】\n{data_str}\n"
        else:
            rag_context += "\n【数据表1】暂无数据\n"
    except:
        rag_context += "\n【数据表1】读取失败\n"

    # (B) 读取大事记 (Milestones)
    try:
        hist_df = load_history()  # 调用之前的工具函数
        if not hist_df.empty:
            hist_str = hist_df.to_csv(index=False)
            rag_context += f"\n【数据表2：众帮编年史(大事记)】\n{hist_str}\n"
        else:
            rag_context += "\n【数据表2】暂无大事记\n"
    except:
        rag_context += "\n【数据表2】大事记读取失败\n"

    # (C) 读取游戏排行榜 (Game Leaderboard)
    try:
        game_df = load_leaderboard()  # 调用之前的工具函数
        if not game_df.empty:
            # 为了省token，只给AI看前50名的高分记录，并按分数倒序
            game_top = game_df.sort_values(by="分数", ascending=False).head(50)
            game_str = game_top.to_csv(index=False)
            rag_context += f"\n【数据表3：接翔游戏排行榜(Top 50)】\n{game_str}\n"
        else:
            rag_context += "\n【数据表3】暂无游戏记录\n"
    except:
        rag_context += "\n【数据表3】游戏榜读取失败\n"

    # --- 2. 注入人设 ---
    ai_system_prompt = f"""
    【角色设定】
     XXXX


    【性格特征】
     XXXX

    【你目前掌握的所有数据（已开天眼）】
    {rag_context}

    【回复规则】
     XXXX
    """

    # 3. 初始化对话
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": ai_system_prompt}]
        st.session_state.messages.append({"role": "assistant",
                                          "content": "我是XXX... 想聊啥？💩"})

    # 4. 强制更新 System Prompt
    if st.session_state.messages[0]["role"] == "system":
        st.session_state.messages[0]["content"] = ai_system_prompt

    # 5. 渲染聊天记录
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 6. 处理输入
    if prompt := st.chat_input("问问XX..."):
        if not DEEPSEEK_API_KEY:
            st.error("❌ 警告：API Key 未配置！请在代码中填入 Key。")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # 使用 OpenRouter / DeepSeek
                    client = OpenAI(
                        api_key=DEEPSEEK_API_KEY,
                        base_url=OPENROUTER_BASE_URL
                    )

                    response = client.chat.completions.create(
                        model=AI_MODEL_NAME,
                        messages=st.session_state.messages,
                        temperature=1.2,
                        extra_headers={
                            "HTTP-Referer": "http://localhost:8501",
                            "X-Title": "ShitKingApp",
                        },
                        stream=False
                    )
                    reply = response.choices[0].message.content
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                except Exception as e:
                    st.error(f"XX脑子堵住了（网络错误），稍后再试...\n错误信息: {e}")

# 头部需要导入 random 库，如果没有请在文件最开头加上: import random
# 确保头部导入
import yt_dlp

# 头部不需要 yt-dlp 了，只需要 pandas, datetime, re, os (这些之前都导入过了)

# ========== Tab 6: 艺术交流 (漂流瓶模式) ==========
with tab_video:
    st.subheader("🎨 艺术交流中心")
    st.caption("这里没有算法，只有群友留下的漂流瓶。")

    ART_FILE = "art_library.csv"


    # --- 基础数据函数 ---
    def load_art_lib():
        if not os.path.exists(ART_FILE): return pd.DataFrame(columns=["提交时间", "链接", "备注"])
        try:
            return pd.read_csv(ART_FILE)
        except:
            return pd.DataFrame(columns=["提交时间", "链接", "备注"])


    def save_art_lib(df):
        df.to_csv(ART_FILE, index=False, encoding='utf-8-sig')


    # --- 1. 数据分流 (今日 vs 历史) ---
    df_art = load_art_lib()
    if not df_art.empty:
        df_art['提交时间'] = pd.to_datetime(df_art['提交时间'])
        today_date = datetime.now().date()

        # 只要日期是今天的，就算今日彩蛋；过了今晚12点，自动变成历史
        mask_today = df_art['提交时间'].dt.date == today_date
        df_daily = df_art[mask_today]
        df_history = df_art[~mask_today]
    else:
        df_daily = pd.DataFrame()
        df_history = pd.DataFrame()

    # --- Session 管理 (保证随机结果不消失) ---
    if 'art_pick' not in st.session_state:
        st.session_state.art_pick = None
    if 'art_type' not in st.session_state:
        st.session_state.art_type = ""

    # ================= UI 布局 =================

    # --- A. 抽卡区 ---
    st.markdown("### 🎲 随机艺术")
    c1, c2, c3 = st.columns([1, 1, 0.5])

    with c1:
        # 显示今日数量
        btn_label = f"📅 换一个 ({len(df_daily)})"
        if st.button(btn_label, use_container_width=True, type="primary"):
            if not df_daily.empty:
                st.session_state.art_pick = df_daily.sample(n=1).iloc[0]
                st.session_state.art_type = "艺术品"
            else:
                st.toast("今日池子空空如也，快去埋一个！")

    with c2:
        # 显示历史数量
        btn_label = f"🏛️ 艺术史 ({len(df_history)})"
        if st.button(btn_label, use_container_width=True):
            if not df_history.empty:
                st.session_state.art_pick = df_history.sample(n=1).iloc[0]
                st.session_state.art_type = "考古发现"
            else:
                st.toast("历史库里也没货...")

    with c3:
        if st.button("🧹", help="清空卡片"):
            st.session_state.art_pick = None
            st.rerun()

    st.markdown("---")

    # --- B. 展示卡片区 ---
    if st.session_state.art_pick is not None:
        row = st.session_state.art_pick
        target_url = row['链接']
        note = row['备注']
        time_str = row['提交时间'].strftime('%m-%d %H:%M')

        # 使用容器画一个漂亮的卡片
        with st.container(border=True):
            st.markdown(f"#### 💌 [{st.session_state.art_type}]")

            # 1. 核心：显示留言 (如果没有留言就显示默认文案)
            display_note = note if note else "（神秘人扔下链接就跑了，没留下一句话）"

            st.markdown(f"""
            <div style="background-color:rgba(255, 255, 255, 0.6); padding:20px; border-radius:10px; border-left: 6px solid #8B4513; margin-bottom: 15px;">
                <div style="font-size: 1.5em; font-weight: bold; color: #5D4037; font-family: '楷体', serif;">
                    “ {display_note} ”
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2. 核心：巨大的跳转按钮
            # 链接太长的话，按钮上只显示“点击跳转”，保持美观
            st.link_button("👉 点击跳转", target_url, type="primary", use_container_width=True)

            # 3. 底部元数据
            st.caption(f"📅 埋藏时间: {time_str} | 🔗 链接: {target_url[:40]}...")

    else:
        # 空闲状态
        st.info("👈 点击左上方按钮，随机捞取一个视频")

    st.markdown("---")

    # --- C. 埋雷区 (投稿) ---
    with st.expander("🎁 投入艺术链接", expanded=False):
        with st.form("simple_submit"):
            st.write("分享你的快乐源泉 (B站/抖音/任何链接)")
            c_link, c_note = st.columns([2, 2])

            new_link = c_link.text_input("链接地址", placeholder="长按粘贴链接...")
            new_note = c_note.text_input("一句骚话 (选填)", placeholder="分享你的艺术")

            if st.form_submit_button("🏺 扔进池子"):
                # 依然用正则提取一下链接，防止用户复制了一大堆文字进来
                clean_url = extract_url(new_link)

                # 如果正则没提取到，但用户填了东西，就直接用用户填的 (宽容模式)
                final_link = clean_url if clean_url else new_link.strip()

                if final_link and len(final_link) > 4:  # 简单校验长度
                    df_new = pd.DataFrame([{
                        "提交时间": datetime.now(),
                        "链接": final_link,
                        "备注": new_note
                    }])
                    # 合并保存
                    save_art_lib(pd.concat([load_art_lib(), df_new], ignore_index=True))
                    st.success("✅ 已入库！")
                    st.rerun()
                else:
                    st.error("❌ 链接好像是空的？")