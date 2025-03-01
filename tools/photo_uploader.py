import streamlit as st
import pandas as pd
import zipfile  
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import folium
from streamlit_folium import folium_static
from supabase import create_client, Client
from datetime import datetime

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_username():
    if "username" not in st.session_state or not st.session_state.username:
        st.error("⚠️ ダッシュボードでユーザーネームを作成してください。")

def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info is not None:
        for tag, value in info.items():
            tag_name = TAGS.get(tag, tag)
            exif_data[tag_name] = value
    return exif_data

def get_gps_info(exif_data):
    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]
        gps_data = {GPSTAGS.get(t, t): gps_info[t] for t in gps_info}

        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)

        if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
            lat = convert_to_degrees(gps_data["GPSLatitude"])
            lon = convert_to_degrees(gps_data["GPSLongitude"])
            if gps_data["GPSLatitudeRef"] == "S":
                lat = -lat
            if gps_data["GPSLongitudeRef"] == "W":
                lon = -lon
            return lat, lon
    return None, None

def get_formatted_datetime(date_taken):
    if date_taken:
        try:
            return datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_to_db(supabase, df):
    for _, row in df.iterrows():
        timestamp = row["timestamp"]
        data = {
            "username": row["username"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "timestamp": timestamp,
            "comment": row["comment"]
        }
        existing = supabase.table("locations").select("*").eq("username", row["username"]).eq("timestamp", timestamp).execute()
        if existing.data:
            supabase.table("locations").update({"comment": row["comment"]}).eq("username", row["username"]).eq("timestamp", timestamp).execute()
        else:
            supabase.table("locations").insert(data).execute()

def process_uploaded_files(uploaded_images, uploaded_zip):
    data_list = []
    if uploaded_zip:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                    with zip_ref.open(file_name) as file:
                        data_list.append(extract_metadata(file))
    if uploaded_images:
        for uploaded_file in uploaded_images:
            data_list.append(extract_metadata(uploaded_file))
    return data_list

def extract_metadata(file):
    image = Image.open(file)
    exif_data = get_exif_data(image)
    latitude, longitude = get_gps_info(exif_data)
    formatted_date = get_formatted_datetime(exif_data.get("DateTimeOriginal"))
    return {"username": st.session_state.username, "latitude": latitude, "longitude": longitude, "timestamp": formatted_date, "comment": ""}

def display_map(data_list):
    st.subheader("位置情報を地図で表示")
    map_location = folium.Map(location=[35.0, 135.0], zoom_start=5)
    for data in data_list:
        if data["latitude"] is not None and data["longitude"] is not None:
            folium.Marker([data["latitude"], data["longitude"]],
                          popup=f"Username: {data['username']}\nComment: {data['comment']}\nTimestamp: {data['timestamp']}").add_to(map_location)
    folium_static(map_location)


def main():
    st.title("📸 写真アップローダー & EXIFデータ取得")
    uploaded_images = st.file_uploader("画像ファイルをアップロードしてください", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    uploaded_zip = st.file_uploader("ZIPファイルをアップロードしてください", type=["zip"], accept_multiple_files=False)
    data_list = process_uploaded_files(uploaded_images, uploaded_zip)
    if data_list:
        st.session_state.data_list = data_list
        st.success("データが保存されました！")
    if "data_list" in st.session_state and st.session_state.data_list:
        df = pd.DataFrame(st.session_state.data_list)
        edited_df = st.data_editor(df, column_config={"comment": {"editable": True}}, disabled=["username", "latitude", "longitude", "timestamp"], num_rows="fixed")
        st.session_state.data_list = edited_df.to_dict(orient="records")
        display_map(st.session_state.data_list)
        if st.button("DBへpush"):
            save_to_db(supabase, pd.DataFrame(st.session_state.data_list))
            st.success("データがDBに保存されました！")
    st.title(f"DBに保存されている{st.session_state.username}のデータ")
    response = supabase.table("locations").select("*").eq("username", st.session_state.username).execute()
    if response.data:
        st.dataframe(pd.DataFrame(response.data))
    else:
        st.write("データが見つかりませんでした。")



def photo_uploader():
    st.write(f"ようこそ、{st.session_state.user.email}さん！")
    
    check_username()
    main()
    
