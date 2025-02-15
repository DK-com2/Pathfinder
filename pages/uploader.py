import streamlit as st
import pandas as pd
import zipfile  
import os
import re
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def get_exif_data(image):
    """EXIFデータを取得して、GPS情報と撮影日時を抽出"""
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


st.title("写真アップローダー & EXIFデータ取得")

uploaded_images = st.file_uploader("画像ファイルをアップロードしてください", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
uploaded_zip = st.file_uploader("ZIPファイルをアップロードしてください", type=["zip"], accept_multiple_files=False)

data_list = []

if uploaded_zip:
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                with zip_ref.open(file_name) as file:
                    image = Image.open(file)
                    exif_data = get_exif_data(image)
                    latitude, longitude = get_gps_info(exif_data)
                    date_taken = exif_data.get("DateTimeOriginal", "不明")
                    
                    data_list.append({
                        "ファイル名": file_name,
                        "撮影日時": date_taken,
                        "緯度": latitude,
                        "経度": longitude,
                    })

if uploaded_images:
    for uploaded_file in uploaded_images:
        image = Image.open(uploaded_file)
        exif_data = get_exif_data(image)
        latitude, longitude = get_gps_info(exif_data)
        date_taken = exif_data.get("DateTimeOriginal", "不明")
        
        data_list.append({
            "ファイル名": uploaded_file.name,
            "撮影日時": date_taken,
            "緯度": latitude,
            "経度": longitude,
        })

if data_list:
    st.session_state.data_list = data_list
    st.success("データが保存されました！")

if "data_list" in st.session_state and st.session_state.data_list:
    st.subheader("アップロードされたデータ一覧")
    df = pd.DataFrame(st.session_state.data_list)
    

    st.dataframe(df)
else:
    st.info("まだデータがありません。写真をアップロードしてください。")
