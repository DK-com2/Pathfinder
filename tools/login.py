import streamlit as st
from supabase import create_client, Client

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ーーー　ログイン　サインアップ　ログアウト　ーーー



def sign_up(email, password):
    return supabase.auth.sign_up({"email": email, "password": password})

def sign_in(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


# ログアウト
def sign_out():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()


# ログインページ
def login():
    st.title("ログイン")
    email = st.text_input("メールアドレス", key="login_email")
    password = st.text_input("パスワード", type="password", key="login_password")

    if st.button("ログイン"):
        try:
            res = sign_in(email, password)  # ユーザー認証
            session = supabase.auth.get_session()  # セッションを取得

            if session and session.access_token:
                st.session_state.logged_in = True  # ログイン状態を設定
                st.session_state.user = res.user
                st.session_state.access_token = session.access_token  # アクセストークンを保存

                st.success("ログインに成功しました")
                st.write(f"ログイン後の状態: {st.session_state.logged_in}")  # デバッグ用
                st.rerun()
            else:
                st.error("認証セッションが取得できませんでした。")
        except Exception as e:
            st.error(f"ログインに失敗しました: {str(e)}")


# サインアップページ
def signup():
    st.title("サインアップ")
    email = st.text_input("メールアドレス", key="signup_email")
    password = st.text_input("パスワード", type="password", key="signup_password")
    if st.button("サインアップ"):
        try:
            res = sign_up(email, password)
            st.success("アカウントが作成されました。メールを確認してアカウントを有効化してください。")
        except Exception as e:
            st.error(f"サインアップに失敗しました: {str(e)}")