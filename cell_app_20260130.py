import streamlit as st
import pandas as pd

# 1. 網頁基本配置
st.set_page_config(page_title="📔Lin-lab Cell Hub", layout="wide")

# 2. 狀態管理與回呼函數 (解決 StreamlitAPIException 的關鍵)
if 'print_key' not in st.session_state:
    st.session_state['print_key'] = False

def deactivate_print_mode():
    # 使用 callback 修改狀態，這會在下一次渲染開始前執行，避免報錯
    st.session_state["print_key"] = False

# 3. 宇宙無敵強 CSS 優化區
def inject_custom_css():
    st.markdown("""
        <style>
        /* 網頁顯示優化 */
        [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; color: #1f77b4 !important; }
        .stTable td, .stTable th {
            font-size: 20px !important; font-weight: 700 !important;
            color: #000000 !important; text-align: center !important;
        }
        div[data-testid="stTable"] th:first-child, 
        div[data-testid="stTable"] td:first-child { display: none !important; }
        
        /* 網格大字體 (18pt) */
        .stAlert p, .stAlert b { font-size: 18pt !important; line-height: 1.5 !important; }

        /* 隱藏預設頁首頁尾 */
        header, footer { visibility: hidden !important; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# 4. 讀取最新 CSV 資料
sheet_url = "https://docs.google.com/spreadsheets/d/1BoE87REWmgNJ4aqeYHj271fw1G-yG69oYUPZRQDypCg/export?format=csv"
df = pd.read_csv(sheet_url)

# --- ✨ 全自動感應邏輯 (以細胞名稱為最終準則) ---
def calculate_status(row):
    name = str(row['Cell_Name']).strip().lower()
    # 判定「空位」：nan, 空白, 或是各種橫線
    if not name or name in ['nan', '', '-', '–', 'none']:
        return 0
    return 1

df['Effective_Status'] = df.apply(calculate_status, axis=1)
# -----------------------------------------------

# --- 側邊欄控制中心 ---
st.sidebar.title("🧬 Lin-lab Cell Hub")
# 側邊欄元件
print_mode = st.sidebar.checkbox("🖨️ 啟動列印模式", key="print_key")

with st.sidebar.expander("🧤 實驗室操作守則", expanded=False):
    st.markdown("""
    ### 🔬 研究員紀律
    1. **入庫**：填寫名稱並手動改 Status=1。
    2. **出庫**：清空名稱並手動改 Status=0。
    ### 🛡️ AI 感應
    * 系統以「細胞名稱」為準。刪除名稱即視為空位。
    """)

st.sidebar.divider()
search_query = st.sidebar.text_input("🔍 搜尋細胞名稱...", "")
selected_tank = st.sidebar.selectbox("🧊 選擇液態氮桶", ["Tank 1", "Tank 2"])
tank_df = df[df['Tank'] == selected_tank]
selected_rack = st.sidebar.selectbox("📏 選擇鐵架 (Rack)", sorted(tank_df['Rack'].unique()))
rack_df = tank_df[tank_df['Rack'] == selected_rack]
selected_box_id = st.sidebar.selectbox("📦 選擇盒子 (Box ID)", sorted(rack_df['Box_ID'].unique()))

st.sidebar.divider()
st.sidebar.link_button("🔗 開啟原始試算表", "https://docs.google.com/spreadsheets/d/1BoE87REWmgNJ4aqeYHj271fw1G-yG69oYUPZRQDypCg/edit")

# --- 🖨️ 列印模式：修正按鈕與「絕對黑字」CSS ---
if print_mode:
    # 使用 on_click 回呼函數，這能徹底解決 StreamlitAPIException
    if st.button("⬅️ 結束列印並返回", on_click=deactivate_print_mode):
        st.rerun()
    
    st.markdown('<p class="no-print" style="color:red; font-weight:bold; font-size:20px;">【列印模式已啟動】請按 Ctrl/Cmd + P 列印</p>', unsafe_allow_html=True)

    st.markdown("""
        <style>
        /* 1. 網頁預覽時：隱藏側邊欄 */
        section[data-testid="stSidebar"], 
        [data-testid="stSidebarCollapsedControl"] { 
            display: none !important; 
        }

        /* 2. 真正列印時 (紙張上) 的強力設定 */
        @media print {
            /* 隱藏按鈕與紅字 */
            .no-print, button, .stButton { display: none !important; }
            
            /* 【核心修正】強制將所有文字轉為純黑，並移除背景顏色 */
            .stAlert {
                background-color: transparent !important;
                color: black !important;
                border: 1px solid black !important;
                box-shadow: none !important;
            }
            /* 強制所有子元素內容皆為黑色 */
            .stAlert p, .stAlert b, .stAlert div, .stAlert span {
                color: black !important;
                -webkit-text-fill-color: black !important;
            }
            /* 隱藏成功/資訊圖示，讓畫面更乾淨 */
            .stAlert svg { display: none !important; }
            
            /* 讓主容器佔滿寬度，不留白 */
            .main .block-container { padding: 0px !important; margin: 0px !important; max-width: 100% !important; }
        }
        </style>
    """, unsafe_allow_html=True)

# --- 主畫面顯示 ---
if not print_mode:
    st.markdown(f"### 📊 {selected_tank} 庫存概況")
    tank_total = len(tank_df)
    tank_occupied = (tank_df['Effective_Status'] == 1).sum()
    tank_empty = tank_total - tank_occupied
    
    m1, m2, m3 = st.columns(3)
    m1.metric("總容量", f"{tank_total} 支")
    m2.metric("在庫支數 (自動感應)", f"{tank_occupied} 支")
    m3.metric("使用率", f"{(tank_occupied/tank_total)*100:.1f} %")
    st.divider()

if search_query:
    search_results = df[df['Cell_Name'].str.contains(search_query, case=False, na=False)]
    st.subheader(f"🔎 搜尋結果 ({len(search_results)} 筆)")
    st.table(search_results[['Tank', 'Rack', 'Box_ID', 'Position', 'Cell_Name', 'Date']])
else:
    box_data = rack_df[rack_df['Box_ID'] == selected_box_id].sort_values('Position')
    box_empty_count = (box_data['Effective_Status'] == 0).sum()
    st.subheader(f"📍 {selected_tank} - {selected_rack} - {selected_box_id} (空位: {box_empty_count}/25)")

    for row in range(5):
        cols = st.columns(5)
        for col in range(5):
            pos = row * 5 + col + 1
            try:
                cell_info = box_data[box_data['Position'] == pos].iloc[0]
                d_name = str(cell_info['Cell_Name'])
                
                # 名稱截斷邏輯
                if len(d_name) > 50: d_name = d_name[:13] + ".."
                
                with cols[col]:
                    if cell_info['Effective_Status'] == 1:
                        # 網頁上看是綠色，列印時會被 CSS 強制轉為黑字
                        st.success(f"**{pos}**\n{d_name}\n{cell_info['Date']}")
                    else:
                        st.info(f"**{pos}**\n(Empty)")
            except IndexError:
                with cols[col]: st.empty()

# 頁尾排行榜 (同樣依據 Effective_Status)
if not print_mode:
    st.divider()
    st.subheader("💡 建議存放位置 (空位最多盒子)")
    col_rank1, col_rank2 = st.columns(2)
    def get_top_boxes(tank_name):
        tank_rank = df[(df['Tank'] == tank_name) & (df['Effective_Status'] == 0)].groupby(['Rack', 'Box_ID']).size().reset_index(name='Empty_Count')
        return tank_rank.sort_values('Empty_Count', ascending=False).head(5)

    with col_rank1:
        st.markdown("#### 🧊 Tank 1")
        top_t1 = get_top_boxes("Tank 1")
        if not top_t1.empty:
            top_t1.columns = ['鐵架', '盒子ID', '剩餘空位']
            st.table(top_t1)
    with col_rank2:
        st.markdown("#### 🧊 Tank 2")
        top_t2 = get_top_boxes("Tank 2")
        if not top_t2.empty:
            top_t2.columns = ['鐵架', '盒子ID', '剩餘空位']
            st.table(top_t2)