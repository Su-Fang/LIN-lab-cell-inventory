import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 網頁基本配置
st.set_page_config(page_title="Lab Cell Hub Pro", layout="wide")

# ========== CSS 終極美容區塊 (連索引一起消滅版) ==========
def inject_custom_css():
    st.markdown("""
        <style>
        /* 1. Metric 大數字指標 */
        [data-testid="stMetricValue"] > div { 
            font-size: 26px !important; 
            font-weight: 700 !important; 
            color: #1f77b4; 
        }
        
        /* 2. 針對 st.table 的強力黑化與加大 */
        .stTable td {
            font-size: 20px !important; 
            font-weight: 700 !important;
            color: #000000 !important;
            text-align: center !important; /* 【核心修正】：內容置中 */
        }
        .stTable th {
            font-size: 20px !important;
            font-weight: 800 !important;
            color: #000000 !important;
            background-color: #f0f2f6 !important;
            text-align: center !important; /* 【核心修正】：表頭置中 */
        }

        /* 【核心修正】：強制隱藏 st.table 的第一欄 (Index) */
        /* 無論它怎麼跑出來，我們都叫它不准顯示 */
        div[data-testid="stTable"] th:first-child, 
        div[data-testid="stTable"] td:first-child {
            display: none !important;
        }
        
        /* 3. 調整章節標題 */
        h3 { font-size: 26px !important; font-weight: 800 !important; color: #000000 !important; }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()
# ================================================


# --- 請確認您的 Google Sheets 分享網址 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1BoE87REWmgNJ4aqeYHj271fw1G-yG69oYUPZRQDypCg/edit?usp=drive_link" 

# 2. 建立連線與讀取資料
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    data = conn.read(spreadsheet=SHEET_URL)
    data.columns = [str(c).strip() for c in data.columns]
    data = data.rename(columns={'Box#': 'Box_Number', 'Box Number': 'Box_Number', '盒號': 'Box_Number'})
    
    if 'Tank' in data.columns:
        data = data.dropna(subset=['Tank'])
        data = data[data['Tank'].astype(str).str.contains('Tank', na=False)]
    
    for col in ['Position', 'Status', 'Box_Number']:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
    return data

try:
    df = load_data()

    # --- 標題與連結 ---
    st.title("🧬 R2-1211 細胞凍管管理系統 📗")
    st.markdown(f"📊 **即時數據來源：** [Google Sheets 雲端主表]({SHEET_URL})")
    st.markdown("---")

    menu = st.sidebar.radio("功能導航", ["🔍 全庫搜尋", "📦 5x5 盒子平面圖", "📊 庫存概況"])

    if menu == "🔍 全庫搜尋":
        st.subheader("🔍 快速檢索 (全庫)")
        search_query = st.text_input("輸入關鍵字 (如: 細胞名、ID)")
        if search_query:
            mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
            st.dataframe(df[mask], use_container_width=True, hide_index=True)

    elif menu == "📦 5x5 盒子平面圖":
        st.subheader("📦 實體盒子佈局檢視")
        c1, c2, c3 = st.columns(3)
        with c1: tank = st.selectbox("1. 選擇桶號", sorted(df['Tank'].unique()))
        with c2: rack = st.selectbox("2. 選擇鐵架", sorted(df[df['Tank']==tank]['Rack'].unique()))
        with c3:
            temp_df = df[(df['Tank']==tank) & (df['Rack']==rack)]
            box_num = st.selectbox("3. 選擇盒子層數", sorted(temp_df['Box_Number'].unique()))

        box_df = temp_df[temp_df['Box_Number'] == box_num].sort_values('Position')
        st.info(f"📍 目前位置：{tank} > {rack} > 第 {int(box_num)} 層")
        
        for r in range(5):
            cols = st.columns(5)
            for c in range(5):
                pos = r * 5 + c + 1
                target = box_df[box_df['Position'] == pos]
                with cols[c]:
                    if not target.empty:
                        item = target.iloc[0]
                        if int(item['Status']) == 1:
                            st.success(f"**{pos:02d}**\n\n{item['Cell_Name']}")
                        else:
                            st.markdown(f'<div style="background-color:#f0f2f6;padding:10px;border-radius:5px;height:80px;text-align:center;color:#5f6368;border:1px solid #ddd;">{pos:02d}<br><small>(Empty)</small></div>', unsafe_allow_html=True)

    elif menu == "📊 庫存概況":
        # st.subheader("📊 實驗室數據統計") # 把這行拿掉，讓畫面更乾淨

        # 定義計算函數
        def get_stats(target_df):
            stocked = len(target_df[target_df['Status'] == 1])
            empty = len(target_df[target_df['Status'] == 0])
            rate = (stocked / len(target_df)) * 100 if len(target_df) > 0 else 0
            return stocked, empty, rate

        # 1. 雙桶指標對照
        st.markdown("### 📊 實驗室數據統計")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("#### 🧊 Tank 1 現況")
            df_t1 = df[df['Tank'] == 'Tank 1']
            s1, e1, r1 = get_stats(df_t1)
            st.metric("在庫支數", f"{s1} 支")
            st.metric("剩餘空位", f"{e1} 支")
            st.metric("使用率", f"{r1:.1f} %")
            
        with col_t2:
            st.markdown("#### 🧊 Tank 2 現況")
            df_t2 = df[df['Tank'] == 'Tank 2']
            s2, e2, r2 = get_stats(df_t2)
            st.metric("在庫支數", f"{s2} 支")
            st.metric("剩餘空位", f"{e2} 支")
            st.metric("使用率", f"{r2:.1f} %")

        st.write("---")
        
        # 2. Tank 1 補位建議 (表格變大變黑了!)
        st.markdown("### 🈳 Tank 1 優先補位建議 (前 5 名最空盒子)")
        ranking = df_t1[df_t1['Status'] == 0].groupby(['Rack', 'Box_Number', 'Box_ID']).size().reset_index(name='空位數量')
        top_5_t1 = ranking.sort_values(by='空位數量', ascending=False).head(5)
        
        if not top_5_t1.empty:
            top_5_t1.columns = ['鐵架', '層數', '盒子標籤', '空位數量']
            #【關鍵修改】：將 st.dataframe 改成 st.table
            # 這樣您的 CSS 就能 100% 覆蓋並黑化內容了！
            st.table(top_5_t1)


except Exception as e:
    st.error(f"⚠️ 發生錯誤：{e}")