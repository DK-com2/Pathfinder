import streamlit as st
from streamlit_current_location import current_position
import folium
from streamlit_folium import folium_static
import pandas as pd
from datetime import datetime
from supabase import create_client

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="pathfinder",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="expanded"
)

# DBへ保存する関数
def save_to_db(df):
    for _, row in df.iterrows():
        data = {
            "username": row["username"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "timestamp": row["timestamp"],
            "comment": row["comment"]
        }
        # すでに同じデータがDBにあるか確認
        existing = supabase.table("locations").select("*").eq("username", row["username"]).eq("timestamp", row["timestamp"]).execute()

        if existing.data:  # すでに存在する場合は更新
            supabase.table("locations").update({"comment": row["comment"]}).eq("username", row["username"]).eq("timestamp", row["timestamp"]).execute()
        else:  # 存在しない場合は新規追加
            supabase.table("locations").insert(data).execute()


# セッション状態の確認
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("ログインしていません。ログインページに戻ってください。")
    st.stop()

# セッション状態にデータフレームを格納するための初期化
if "location_data" not in st.session_state:
    st.session_state.location_data = pd.DataFrame(columns=["username", "latitude", "longitude", "timestamp", "comment"])
    


st.write(f"ようこそ、{st.session_state.username}さん！")

st.title("📍 位置情報取得と地図表示")

position = current_position()

if st.button("現在地を取得"):
    if position is not None:
        lat = position["latitude"]
        lon = position["longitude"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_entry = pd.DataFrame({
            "username": [st.session_state.username],
            "latitude": [lat],
            "longitude": [lon],
            "timestamp": [timestamp],
            "comment": [""]  
        })
        
        st.session_state.location_data = pd.concat([st.session_state.location_data, new_entry], ignore_index=True)
        st.success("位置情報が保存されました！")

if not st.session_state.location_data.empty:
    st.write("### あなたの現在位置")

    # DataFrameを編集可能な形で表示
    edited_df = st.data_editor(
        st.session_state.location_data,
        column_config={"comment": {"editable": True}},  # コメントのみ編集可能
        disabled=["username", "latitude", "longitude", "timestamp"],
        num_rows="fixed"
    )
    st.session_state.location_data["comment"] = edited_df["comment"]  # コメントのみ更新

    # DBへ保存ボタン
    if st.button("DBへpush"):
        save_to_db(st.session_state.location_data)
        st.success("あなたの現在地がDBに保存されました！")

    last_entry = st.session_state.location_data.iloc[-1]
    map_location = folium.Map(location=[last_entry["latitude"], last_entry["longitude"]], zoom_start=15)
    folium.Marker([last_entry["latitude"], last_entry["longitude"]], popup=last_entry["comment"], tooltip=last_entry["username"]).add_to(map_location)
    folium_static(map_location)
else:
    st.warning("保存されたデータがありません。")



st.title(f"DBに保存されている{st.session_state.username}のデータ")
# データベースから username に一致するデータを取得
response = supabase.table("locations").select("*").eq("username", st.session_state.username).execute()

if response.data:
    df = pd.DataFrame(response.data)
    st.dataframe(df)
else:
    st.write("データが見つかりませんでした。")
