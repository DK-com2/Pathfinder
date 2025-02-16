import streamlit as st
from streamlit_current_location import current_position
import folium
from streamlit_folium import folium_static

st.set_page_config(
    page_title="pathfinder",  # タイトル
    page_icon="🚀",  # ファビコン
    layout="centered",  # レイアウト（"centered" または "wide"）
    initial_sidebar_state="expanded"  # サイドバーの初期状態（"auto", "expanded", "collapsed"）
)


# セッション状態の確認
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("ログインしていません。ログインページに戻ってください。")
    st.stop()  # 他の処理を止める


# ログイン後のページ内容
st.write(f"ようこそ、{st.session_state.username}さん！")

st.title("📍 位置情報取得と地図表示")


position = current_position()


if st.button("現在地を表示"):

    if position is not None:
        lat = position["latitude"]
        lon = position["longitude"]

        st.write(f"### 緯度: {lat}")
        st.write(f"### 経度: {lon}")

        map_location = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], popup="現在地", tooltip="ここです").add_to(map_location)

        folium_static(map_location)

    else:
        st.warning("位置情報の取得に失敗しました。再度試してみてください。")
