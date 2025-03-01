import streamlit as st
from streamlit_current_location import current_position
import folium
from streamlit_folium import folium_static
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



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
            

def get_and_save_current_position():
    position = current_position()
    
    if "location_data" not in st.session_state:
        st.session_state.location_data = pd.DataFrame(columns=["username", "latitude", "longitude", "timestamp", "comment"])

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

            # FutureWarning の修正
            if not new_entry.dropna(how="all").empty:
                st.session_state.location_data = pd.concat([st.session_state.location_data, new_entry], ignore_index=True)

            st.success("位置情報を取得しました！")
            

def display_and_edit_location_data():
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
        


def display_location_info():
    st.write(f"ようこそ、{st.session_state.user.email}さん！")
    
    get_and_save_current_position()
    display_and_edit_location_data()