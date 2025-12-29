import streamlit as st
import pandas as pd
import os
from datetime import datetime, date, timedelta
import altair as alt

# --- 1. 页面配置 & 皮肤注入 ---
st.set_page_config(page_title="💩 窜稀拉屎𠈌众帮", page_icon="🚽", layout="wide")

# 注入自定义 CSS (美化核心)
st.markdown("""
<style>
    /* 全局背景色：米黄色 (草纸色) */
    .stApp {
        background-color: #FEF9E7;
    }

    /* 标题颜色：深褐色 */
    h1, h2, h3, h4 {
        color: #5D4037 !important;
        font-family: 'Microsoft YaHei', sans-serif;
    }

    /* 按钮样式优化 */
    .stButton>button {
        border-radius: 20px;
        border: 2px solid #8B4513;
        color: #8B4513;
        background-color: #FFF8DC;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #8B4513;
        color: white;
        border-color: #8B4513;
    }

    /* 指标卡片 (Metric) */
    div[data-testid="stMetricValue"] {
        color: #8B4513; /* 数字变成褐色 */
        font-weight: 900;
    }
    div[data-testid="stMetricLabel"] {
        color: #A0522D;
    }

    /* 分割线颜色 */
    hr {
        border-color: #D2691E;
    }

    /* 自定义卡片背景 */
    .member-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(139, 69, 19, 0.1);
        border: 1px solid #DEB887;
        text-align: center;
    }

    /* 屎王横幅动画效果 */
    @keyframes shine {
        0% {background-position: left;}
        100% {background-position: right;}
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "shit_database.csv"
MEMBERS = ["甲鱼", "气温", "牛子", "一哥", "毛毛", "老司", "JK"]


# --- 2. 核心数据逻辑 (保持不变) ---
def load_data():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame(columns=["日期", "姓名", "次数", "备注"])
    df = pd.read_csv(DB_FILE)
    df['备注'] = df['备注'].fillna("")
    df['日期'] = pd.to_datetime(df['日期'])
    return df


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
            new_row = pd.DataFrame([{
                "日期": target_date_dt,
                "姓名": name,
                "次数": final_count,
                "备注": new_comment if new_comment else ""
            }])
            df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')


def get_week_range(target_date):
    if isinstance(target_date, str):
        target_date = pd.to_datetime(target_date).date()
    elif isinstance(target_date, datetime):
        target_date = target_date.date()
    days_from_sunday = (target_date.weekday() + 1) % 7
    start_sunday = target_date - timedelta(days=days_from_sunday)
    end_saturday = start_sunday + timedelta(days=6)
    return start_sunday, end_saturday


def get_weekly_stats(df, start_date, end_date):
    mask = (df['日期'].dt.date >= start_date) & (df['日期'].dt.date <= end_date)
    week_df = df[mask].copy()
    if week_df.empty: return None, 0.0

    total_counts = week_df.groupby("姓名")['次数'].sum()
    if total_counts.empty: return None, 0.0

    max_val = total_counts.max()
    winners = total_counts[total_counts == max_val].index.tolist()
    total_shit = week_df['次数'].sum()
    daily_avg_per_person = total_shit / 7 / len(MEMBERS)
    return winners, daily_avg_per_person


# --- 3. UI 主程序 ---

df = load_data()
today = date.today()
current_start, current_end = get_week_range(today)

# --- Header ---
st.markdown(
    "<h1 style='text-align: center; font-size: 3em;'>🚽 窜稀拉屎𠈌众帮 <span style='color:#D2691E; font-size:0.5em'>Pro</span></h1>",
    unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8B4513;'>记录每一份努力，见证每一次释放</p>", unsafe_allow_html=True)

curr_winners, curr_avg = get_weekly_stats(df, current_start, current_end)

# --- 荣誉横幅 ---
if curr_winners and sum(df[df['日期'].dt.date >= current_start]['次数']) > 0:
    winner_str = " & ".join(curr_winners)
    # 使用 CSS 渐变色制作土豪金横幅
    st.markdown(f"""
    <div style='
        background: linear-gradient(45deg, #B8860B, #FFD700, #B8860B);
        background-size: 200% 200%;
        animation: shine 3s infinite;
        padding: 25px; 
        border-radius: 15px; 
        text-align: center; 
        color: #5D4037;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        margin-bottom: 20px;
        border: 2px solid #FFF8DC;
    '>
        <h3 style='margin:0; color: #5D4037;'>👑 本周屎王 ({current_start.strftime('%m.%d')} - {current_end.strftime('%m.%d')})</h3>
        <h1 style='font-size: 60px; margin: 10px 0; text-shadow: 2px 2px 0px rgba(255,255,255,0.5);'>{winner_str}</h1>
        <p style='margin:0'>全员日均产量: <b>{curr_avg:.2f}</b> 次/人/天</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("🌬️ 本周的风还在吹，王座空悬，等你来拉！")

# --- 操作区 ---
c_date, c_title = st.columns([1, 4])
with c_date:
    entry_date = st.date_input("📅 时光机 (补录/修改)", today)
with c_title:
    st.subheader(f"🛠️记录板 ({entry_date.strftime('%Y-%m-%d')})")

cols = st.columns(4)
for i, member in enumerate(MEMBERS):
    day_mask = (df['日期'].dt.date == entry_date) & (df['姓名'] == member)
    current_data = df[day_mask]

    if not current_data.empty:
        curr_count = int(current_data.iloc[0]['次数'])
        curr_note = current_data.iloc[0]['备注']
    else:
        curr_count = 0
        curr_note = ""

    # 动态表情判断
    face = "😐"
    if curr_count >= 1: face = "😌"
    if curr_count >= 2: face = "😤"
    if curr_count >= 3: face = "😱"

    with cols[i % 4]:
        # 使用自定义样式的容器
        with st.container(border=True):
            st.markdown(
                f"<div style='text-align:center; font-size:1.2em; font-weight:bold; color:#8B4513'>{face} {member}</div>",
                unsafe_allow_html=True)

            # 指标
            st.metric("今日产量", f"{curr_count}", label_visibility="collapsed")

            c1, c2 = st.columns(2)
            if c1.button("➕1", key=f"add_{member}", use_container_width=True):
                update_record(entry_date, member, 1)
                st.rerun()
            if c2.button("➖1", key=f"sub_{member}", use_container_width=True):
                update_record(entry_date, member, -1)
                st.rerun()

            # 备注折叠区
            with st.popover(f"📝 {curr_note[:5]}..." if curr_note else "📝 备注"):
                new_note = st.text_input("记录感受...", value=curr_note, key=f"note_{member}")
                if st.button("保存备注", key=f"sav_{member}"):
                    if new_note != curr_note:  # 只有变了才存
                        update_record(entry_date, member, 0, new_note)
                        st.rerun()

st.markdown("---")

# --- 周报区 ---
st.subheader("📊 本周屎况 (周报)")

week_mask = (df['日期'].dt.date >= current_start) & (df['日期'].dt.date <= current_end)
week_df = df[week_mask].copy()

if not week_df.empty:
    pivot_count = week_df.pivot_table(index='姓名', columns='日期', values='次数', aggfunc='sum').fillna(0)
    pivot_count = pivot_count.reindex(MEMBERS, fill_value=0)

    pivot_count['本周总计'] = pivot_count.sum(axis=1)
    pivot_count['日均'] = pivot_count['本周总计'] / 7
    global_avg_daily = pivot_count['日均'].mean()

    display_df = pd.DataFrame(index=MEMBERS)

    # 构造更直观的表格
    for i in range(7):
        d = current_start + timedelta(days=i)
        # 表头加个 emoji
        week_emojis = ['🌞', '🌙', '🔥', '💧', '🌲', '🍻', '🛌']
        col_name = f"{week_emojis[d.weekday()]} {d.strftime('%m-%d')}"

        col_data = []
        for member in MEMBERS:
            record = week_df[(week_df['日期'].dt.date == d) & (week_df['姓名'] == member)]
            if not record.empty:
                cnt = int(record.iloc[0]['次数'])
                rem = record.iloc[0]['备注']
                # 用气泡展示备注
                cell_str = f"{cnt}"
                if rem: cell_str += f" 💬"
                if cnt == 0: cell_str = "-"
            else:
                cell_str = "-"
            col_data.append(cell_str)
        display_df[col_name] = col_data

    # 数据列
    display_df['日均'] = pivot_count['日均']
    display_df['评价'] = display_df['日均'].apply(lambda x: "👍 优秀" if x > global_avg_daily else "👎 加油")

    # 使用 Streamlit 的高级表格配置 (Column Config) 来美化
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "日均": st.column_config.ProgressColumn(
                "日均产量",
                help="每日平均次数",
                format="%.2f",
                min_value=0,
                max_value=4,  # 假设4次封顶，进度条满
            ),
        }
    )

    # 显示备注详情列表
    st.caption("🔍 本周备注详情：")
    notes_df = week_df[week_df['备注'] != ""][['日期', '姓名', '备注']].sort_values('日期', ascending=False)
    if not notes_df.empty:
        for _, row in notes_df.iterrows():
            st.text(f"{row['日期'].strftime('%m-%d')} {row['姓名']}: {row['备注']}")

else:
    st.info("本周还没人开张。")

# --- 图表区 (方方正正折线图 + 标准差) ---
c_chart, c_hist = st.columns([2, 1])

with c_chart:
    st.subheader("📈 30天产量走势 (点击名字筛选)")
    if not df.empty:
        # 1. 准备数据：筛选最近30天
        date_30_days_ago = pd.Timestamp(today - timedelta(days=30))
        chart_df = df[df['日期'] >= date_30_days_ago].copy()

        if not chart_df.empty:
            # 2. 计算标准差 (Std Dev)
            # 按姓名分组，计算次数的标准差，并合并回原数据
            std_df = chart_df.groupby('姓名')['次数'].std().reset_index()
            std_df.columns = ['姓名', '标准差']
            # 将 NaN (比如只有一条数据时) 填充为 0
            std_df['标准差'] = std_df['标准差'].fillna(0).round(2)

            # 合并数据
            chart_df = pd.merge(chart_df, std_df, on='姓名', how='left')

            # 3. 定义交互选择器 (点击图例高亮)
            selection = alt.selection_point(fields=['姓名'], bind='legend')

            # 4. 构建阶梯折线图 (interpolate='step-after')
            chart = alt.Chart(chart_df).mark_line(
                point=True,  # 显示圆点
                strokeWidth=3,  # 线条加粗
                interpolate='step-after'  # 【关键】让线条变成方方正正的直角折线
            ).encode(
                # X轴：时间
                x=alt.X('日期:T', axis=alt.Axis(format='%m-%d', title=None)),

                # Y轴：次数 (自动堆叠)
                y=alt.Y('次数:Q', axis=alt.Axis(tickMinStep=1), title='次数'),

                # 颜色：区分人员
                color=alt.Color('姓名:N', scale=alt.Scale(scheme='tableau10')),

                # 悬停提示 (加入标准差)
                tooltip=[
                    alt.Tooltip('日期:T', format='%Y-%m-%d'),
                    '姓名',
                    '次数',
                    '备注',
                    alt.Tooltip('标准差', title='波动(标准差)')  # 新增这一行
                ],

                # 交互逻辑：未选中的变成半透明
                opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
            ).add_params(
                selection
            ).properties(
                height=350
            ).interactive()  # 允许拖拽平移

            st.altair_chart(chart, use_container_width=True)
        else:
            st.caption("近期无数据")

with c_hist:
    st.subheader("🏆 历代屎王")
    history_data = []
    start_history_date = date(2025, 10, 19)
    iter_date = start_history_date

    while iter_date <= today:
        iter_end = iter_date + timedelta(days=6)
        w_winners, w_avg = get_weekly_stats(df, iter_date, iter_end)
        if w_winners:
            # 简化名字显示
            winner_text = " & ".join(w_winners)
            history_data.append({
                "周期": f"{iter_date.strftime('%m.%d')}",
                "王者": f"{winner_text}",
                "日均": f"{w_avg:.2f}"
            })
        iter_date += timedelta(days=7)

    if history_data:
        st.dataframe(
            pd.DataFrame(history_data).iloc[::-1],
            use_container_width=True,
            hide_index=True,
            column_config={
                "日均": st.column_config.NumberColumn(format="%.2f"),
                "王者": st.column_config.TextColumn(width="medium")
            }
        )
# --- 底部原始数据 ---
with st.expander("📋 查看原始数据库 (仅供核对)"):
    if not df.empty:
        show_df = df.sort_values("日期", ascending=False).copy()
        show_df['日期'] = show_df['日期'].dt.strftime('%Y-%m-%d')
        st.dataframe(show_df, use_container_width=True)