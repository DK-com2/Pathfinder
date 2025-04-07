import streamlit as st
from supabase import create_client, Client
from tools.login import *
from tools.dashboard import *
from tools.current_location import *
from tools.photo_uploader import *
from tools.google_timeline import *
from tools.database import *


# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="pathfinder",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 初期設定
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# メニューの設定
login_page = st.Page(login, title="ログイン", icon=":material/login:")
signup_page = st.Page(signup, title="サインアップ", icon=":material/app_registration:")
dashboard_page = st.Page(dashboard, title="ダッシュボード", icon=":material/dashboard:")
current_location_page = st.Page(display_location_info, title="位置情報取得", icon=":material/location_on:")
photo_uploader_page = st.Page(photo_uploader, title="写真アップローダー", icon=":material/photo_camera:")
google_map_timeline = st.Page(google_timeline, title="Google Map タイムライン", icon=":material/map:")
detabase_view_page = st.Page(database_view, title="myデータベース", icon=":material/database:")


# デバッグ用
st.write("ログイン状態: ", st.session_state.logged_in)


# サイドバーに表示されるナビゲーション
# ログインしてとき
if st.session_state.logged_in:
    pg = st.navigation(
        {
            "ダッシュボード": [dashboard_page],
            "Google Map タイムライン": [google_map_timeline, detabase_view_page],
            "位置情報取得": [current_location_page, photo_uploader_page],
            "ログアウト": [st.Page(sign_out, title="ログアウト", icon=":material/logout:")],
        }
    )
    # ログインしていないとき
else:
    
    pg = st.navigation(
        {
            "ログイン": [login_page],
            "サインアップ": [signup_page]
        }
    )

pg.run()



