import streamlit as st
from supabase import create_client, Client

# secrets.tomlからSupabaseのURLとキーを取得（.streamlit/secrets.tomlに設定しておく）
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]

# Supabaseクライアントを作成
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

    # ユーザー名とパスワードを入力するフォームを表示
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")

    if st.button("ログイン"):
        # ユーザー名とパスワードを使ってDBからデータを取得
        response = supabase.table("users").select("*").eq("username", username).execute()

        if response.data:
            user_data = response.data[0]

            # パスワードを確認（平文で比較）
            if user_data["password"] == password:
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
    check_login()  # ログインチェック

    st.title(f"ようこそ、{st.session_state.username}さん！")

    # ログアウトボタン
    if st.button("ログアウト"):
        del st.session_state.logged_in
        del st.session_state.username
        st.session_state.page = "login"  # ログアウト後はログインページに戻る
        st.rerun() 



