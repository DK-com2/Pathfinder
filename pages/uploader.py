import streamlit as st
import pandas as pd
import zipfile  
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import folium
from streamlit_folium import folium_static
from supabase import create_client
from datetime import datetime

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# 日付フォーマットを変換する関数
def get_formatted_datetime(date_taken):
    if date_taken:
        try:
            # "YYYY:MM:DD HH:MM:SS"形式からdatetimeに変換
            date_taken = datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")
            # それを"YYYY-MM-DD HH:MM:SS"形式に変換
            return date_taken.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_to_db(df):
    for _, row in df.iterrows():
        # timestampを適切な形式に変換
        timestamp = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row["timestamp"], datetime) else row["timestamp"]
        
        data = {
            "username": row["username"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "timestamp": timestamp,  # 修正したtimestampを使う
            "comment": row["comment"]
        }

        # DBの確認とデータ挿入処理
        existing = supabase.table("locations").select("*").eq("username", row["username"]).eq("timestamp", row["timestamp"]).execute()

        if existing.data:  # すでに存在する場合は更新
            supabase.table("locations").update({"comment": row["comment"]}).eq("username", row["username"]).eq("timestamp", row["timestamp"]).execute()
        else:  # 存在しない場合は新規追加
            supabase.table("locations").insert(data).execute()

st.set_page_config(
    page_title="pathfinder",  # タイトル
    page_icon="🌐",  # ファビコン
    layout="centered",  # レイアウト（"centered" または "wide"）
    initial_sidebar_state="expanded"  # サイドバーの初期状態（"auto", "expanded", "collapsed"）
)

# セッション状態の確認
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("ログインしていません。ログインページに戻ってください。")
    st.stop()  # 他の処理を止める

# ログイン後のページ内容
st.write(f"ようこそ、{st.session_state.username}さん！")

st.title("📸 写真アップローダー & EXIFデータ取得")

uploaded_images = st.file_uploader("画像ファイルをアップロードしてください", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
uploaded_zip = st.file_uploader("ZIPファイルをアップロードしてください", type=["zip"], accept_multiple_files=False)

data_list = []

# ZIPファイルの処理
if uploaded_zip:
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        for file_name in zip_ref.namelist():
            if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                with zip_ref.open(file_name) as file:
                    image = Image.open(file)
                    exif_data = get_exif_data(image)
                    latitude, longitude = get_gps_info(exif_data)
                    # EXIFのDateTimeOriginalを取得して処理
                    date_taken = exif_data.get("DateTimeOriginal")
                    formatted_date = get_formatted_datetime(date_taken)

                    data_list.append({
                        "username": st.session_state.username,
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": formatted_date,
                        "comment": ""
                    })
                    
                    
# 通常の画像ファイルの処理
if uploaded_images:
    for uploaded_file in uploaded_images:
        image = Image.open(uploaded_file)
        exif_data = get_exif_data(image)
        latitude, longitude = get_gps_info(exif_data)
        # EXIFのDateTimeOriginalを取得して処理
        date_taken = exif_data.get("DateTimeOriginal")
        formatted_date = get_formatted_datetime(date_taken)  # 関数を使ってフォーマット
        data_list.append({
            "username": st.session_state.username,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": formatted_date,  # フォーマットした日付を使用
            "comment": ""
        })


# データをセッション状態に保存
if data_list:
    st.session_state.data_list = data_list
    st.success("データが保存されました！")

# DataFrameの編集
if "data_list" in st.session_state and st.session_state.data_list:
    st.subheader("アップロードされたデータ一覧")
    
    # DataFrameを作成
    df = pd.DataFrame(st.session_state.data_list)

    # st.data_editorでコメントのみ編集可能にする
    edited_df = st.data_editor(
        df,
        column_config={"comment": {"editable": True}},  # コメントのみ編集可能
        disabled=["username", "latitude", "longitude", "timestamp"],  
        num_rows="fixed"
    )

    # 編集後のDataFrameをセッション状態に保存
    st.session_state.data_list = edited_df.to_dict(orient="records")  # DataFrame のまま保存

    # 地図表示
    st.subheader("位置情報を地図で表示")
    map_location = folium.Map(location=[35.0, 135.0], zoom_start=5)  

    for data in st.session_state.data_list:
        lat = data["latitude"]
        lon = data["longitude"]
        if lat is not None and lon is not None:
            folium.Marker([lat, lon],
                        popup=f"Username: {data['username']}\nComment: {data['comment']}\nTimestamp: {data['timestamp']}").add_to(map_location)  

    folium_static(map_location)

    # DBへ保存ボタン
    if st.button("DBへpush"):
        save_to_db(pd.DataFrame(st.session_state.data_list))  # DataFrameに戻してDBへ保存
        st.success("データがDBに保存されました！")

else:
    st.info("まだデータがありません。写真をアップロードしてください。")
    
# DBに保存されているデータ
st.title(f"DBに保存されている{st.session_state.username}のデータ")
response = supabase.table("locations").select("*").eq("username", st.session_state.username).execute()

if response.data:
    df = pd.DataFrame(response.data)
    st.dataframe(df)
else:
    st.write("データが見つかりませんでした。")
