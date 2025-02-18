import bcrypt
import streamlit as st
from supabase import create_client, Client
import folium
import pandas as pd


# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="pathfinder",  # タイトル
    page_icon="🌐",  # アイコン
    layout="centered",  # レイアウト（"centered" または "wide"）
    initial_sidebar_state="expanded"  # サイドバーの初期状態（"auto", "expanded", "collapsed"）
)


# セッションの状態がまだ設定されていない場合、"login" ページに遷移
if "page" not in st.session_state:
    st.session_state.page = "login"

# ログインチェックをする関数
def check_login():
    if "logged_in" not in st.session_state or not st.session_state.logged_in:
        st.session_state.page = "login"
        st.rerun()

# ログイン画面
if st.session_state.page == "login":
    st.title("ログイン画面")

    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        response = supabase.table("users").select("*").eq("username", username).execute()

        if response.data:
            user_data = response.data[0]

            # ハッシュ化されたパスワードを比較
            if bcrypt.checkpw(password.encode(), user_data["password"].encode()):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("ログイン成功！")

                st.session_state.page = "home"  
                st.rerun()  
            else:
                st.error("パスワードが間違っています。")
        else:
            st.error("ユーザー名が見つかりません。")

# ホーム画面（ログイン後）
if st.session_state.page == "home":
    check_login()  

    st.title(f"ようこそ、{st.session_state.username}さん！")
    
    response = supabase.table("locations").select("*").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        st.write(df)
        
    map = folium.Map(location=[36.0047, 137.5936], zoom_start=5)
    
    # 各地点にピンを追加
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"Username: {row['username']}\nComment: {row['comment']}\nTimestamp: {row['timestamp']}"
        ).add_to(map)

    st.write("### Locations Map")
    st.components.v1.html(map._repr_html_(), width=700, height=500)


    if st.button("ログアウト"):
        del st.session_state.logged_in
        del st.session_state.username
        st.session_state.page = "login"  
        st.rerun() 



