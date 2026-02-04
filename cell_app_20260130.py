import streamlit as st
import pandas as pd

# 1. 網頁基本配置
st.set_page_config(page_title="Lin-lab Cell Hub", layout="wide")

# 2. 逃生艙狀態設定
if 'print_key' not in st.session_state:
    st.session_state['print_key'] = False

def deactivate_print_mode():
    st.session_state["print_key"] = False

# 3. 宇宙無敵強 CSS 優化區
def inject_custom_css():
    st.markdown("""
        <style>
        /* 全域指標字體縮小 */
        [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; color: #1f77b4 !important; }
        
        /* 表格黑大粗 (去索引版) */
        .stTable td, .stTable th {
            font-size: 20px !important; font-weight: 700 !important;
            color: #000000 !important; text-align: center !important;
        }
        div[data-testid="stTable"] th:first-child, 
        div[data-testid="stTable"] td:first-child { display: none !important; }
        
        /* 網格文字優化 */
        .stAlert p, .stAlert b { font-size: 18pt !important; line-height: 1.5 !important; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# 4. 讀取最新 CSV 資料 (請務必確認網址正確)
sheet_url = "https://docs.google.com/spreadsheets/d/1BoE87REWmgNJ4aqeYHj271fw1G-yG69oYUPZRQDypCg/export?format=csv"
df = pd.read_csv(sheet_url)

# --- 側邊欄：控制中心 ---
st.sidebar.title("🧬 Lin-lab Cell Hub Pro")
print_mode = st.sidebar.checkbox("🖨️ 啟動列印模式", key="print_key")

with st.sidebar.expander("📖 系統操作規範", expanded=False):
    st.markdown("""
    * **入庫**：輸入 Cell_Name 並將 **Status 設為 1**。
    * **出庫**：清空 Cell_Name 並將 **Status 設為 0**。
    * **列印**：啟動模式後，按 Cmd/Ctrl+P，選 **Portrait (直向)** 並縮放至 **50%**。
    """)

st.sidebar.divider()
search_query = st.sidebar.text_input("🔍 搜尋細胞名稱...", "")

# 雙桶導航邏輯
selected_tank = st.sidebar.selectbox("🧊 選擇液態氮桶", ["Tank 1", "Tank 2"])
tank_df = df[df['Tank'] == selected_tank]
selected_rack = st.sidebar.selectbox("📏 選擇鐵架 (Rack)", sorted(tank_df['Rack'].unique()))
rack_df = tank_df[tank_df['Rack'] == selected_rack]
# 使用 Box_ID 欄位進行導航
selected_box_id = st.sidebar.selectbox("📦 選擇盒子 (Box ID)", sorted(rack_df['Box_ID'].unique()))

st.sidebar.divider()
st.sidebar.link_button("🔗 開啟原始試算表", "https://docs.google.com/spreadsheets/d/1BoE87REWmgNJ4aqeYHj271fw1G-yG69oYUPZRQDypCg/edit")

# --- 主畫面：數據統計與列印模式 ---
if print_mode:
    # 列印模式專屬導航與 CSS
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    if st.button("⬅️ 返回網頁模式", on_click=deactivate_print_mode):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        [data-testid="stSidebar"], header, footer { display: none !important; }
        @media print {
            .no-print, button { display: none !important; }
            .stAlert, .stAlert p, .stAlert b { color: black !important; } 
            body { -webkit-print-color-adjust: exact !important; }
        }
        .main .block-container { padding: 0.5rem !important; }
        [data-testid="column"] { width: 19% !important; flex: 1 1 19% !important; min-width: 19% !important; padding: 2px !important; }
        .stAlert { padding: 5px !important; min-height: 80px !important; border: 1px solid #ccc !important; }
        </style>
    """, unsafe_allow_html=True)

# 儀表板：即時動態統計 (列印模式下隱藏)
if not print_mode:
    st.markdown(f"### 📊 {selected_tank} 庫存概況")
    tank_total = len(tank_df)
    tank_occupied = (tank_df['Status'] == 1).sum()
    tank_empty = tank_total - tank_occupied
    
    m1, m2, m3 = st.columns(3)
    m1.metric("總容量", f"{tank_total} 支")
    m2.metric("在庫支數", f"{tank_occupied} 支")
    m3.metric("使用率", f"{(tank_occupied/tank_total)*100:.1f} %")
    st.divider()

# --- 主畫面：5x5 網格顯示 ---
if search_query:
    search_results = df[df['Cell_Name'].str.contains(search_query, case=False, na=False)]
    st.subheader(f"🔎 搜尋結果 ({len(search_results)} 筆)")
    st.table(search_results[['Tank', 'Rack', 'Box_ID', 'Position', 'Cell_Name', 'Date']])
else:
    # 取得當前盒子資料
    box_data = rack_df[rack_df['Box_ID'] == selected_box_id].sort_values('Position')
    box_empty_count = (box_data['Status'] == 0).sum()
    
    st.subheader(f"📍 {selected_tank} - {selected_rack} - {selected_box_id} (即時空位: {box_empty_count}/25)")

    # 繪製 5x5 網格
    for row in range(5):
        cols = st.columns(5)
        for col in range(5):
            pos = row * 5 + col + 1
            try:
                cell_info = box_data[box_data['Position'] == pos].iloc[0]
                d_name = str(cell_info['Cell_Name'])
                if len(d_name) > 50: d_name = d_name[:13] + ".."
                
                with cols[col]:
                    if cell_info['Status'] == 1:
                        st.success(f"**{pos}**\n{d_name}\n{cell_info['Date']}")
                    else:
                        st.info(f"**{pos}**\n(Empty)")
            except IndexError:
                with cols[col]: st.empty()

# 頁尾排行榜 (分桶顯示建議存放位置)
if not print_mode:
    st.divider()
    st.subheader("💡 建議存放位置 (空位最多盒子)")
    
    col_rank1, col_rank2 = st.columns(2)
    
    def get_top_boxes(tank_name):
        # 篩選特定桶且 Status 為 0
        tank_rank = df[(df['Tank'] == tank_name) & (df['Status'] == 0)].groupby(['Rack', 'Box_ID']).size().reset_index(name='Empty_Count')
        # 排序並取前 5
        top = tank_rank.sort_values('Empty_Count', ascending=False).head(5)
        if not top.empty:
            top.columns = ['鐵架', '盒子ID', '剩餘空位']
        return top

    with col_rank1:
        st.markdown("#### 🧊 Tank 1")
        top_t1 = get_top_boxes("Tank 1")
        if not top_t1.empty:
            st.table(top_t1)
        else:
            st.write("Tank 1 暫無可用空位。")
            
    with col_rank2:
        st.markdown("#### 🧊 Tank 2")
        top_t2 = get_top_boxes("Tank 2")
        if not top_t2.empty:
            st.table(top_t2)
        else:
            st.write("Tank 2 暫無可用空位。")