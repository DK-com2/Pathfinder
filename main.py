import bcrypt
import streamlit as st
from supabase import create_client, Client

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

    if st.button("ログアウト"):
        del st.session_state.logged_in
        del st.session_state.username
        st.session_state.page = "login"  
        st.rerun() 



