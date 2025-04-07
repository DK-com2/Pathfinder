import streamlit as st
from supabase import create_client, Client
import folium
import pandas as pd

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def show_session_info():
    if "logged_in" in st.session_state and st.session_state.logged_in:
        with st.container():
            st.markdown("### 👤 ユーザー情報")
            try:
                user_email = st.session_state.user.dict().get("email", "不明")
                st.markdown(f"**📧 メールアドレス:** {user_email}")
            except AttributeError:
                st.error("ユーザー情報の取得に失敗しました。")
    else:
        st.warning("⚠ ログインしていません。ログインしてください。")


def get_username_by_user_id():
    try:
        user_id = st.session_state.user.dict().get("id", None)
    except AttributeError:
        st.warning("⚠ ユーザー情報がセッションに保存されていません。")
        return None

    if not user_id:
        st.warning("⚠ ユーザーIDが見つかりません。")
        return None

    response = supabase.table("username").select("username").eq("user_id", user_id).execute()

    with st.container():
        st.markdown("### 📝 ユーザー名")

        if response.data:
            username = response.data[0]["username"]
            st.session_state.username = username
            st.success(f"ようこそ **{username}** さん！")
            return username
        else:
            new_username = st.text_input("ユーザー名を入力してください")
            if st.button("登録"):
                if new_username:
                    supabase.table("username").insert({
                        "user_id": user_id,
                        "username": new_username
                    }).execute()
                    st.session_state.username = new_username
                    st.success(f"ユーザー名「{new_username}」を登録しました。")
                    return new_username
                else:
                    st.warning("ユーザー名を入力してください。")
            return None



def dashboard():
    st.title("📊 ダッシュボード")

    with st.container():
        show_session_info()
        get_username_by_user_id()

    # 今後の方針セクション
    with st.container():
        st.markdown("---")
        st.markdown("### 🚀 今後の方針")
        
        st.markdown("#### 1. **Google Timelineの将来について**")
        st.markdown("Googleが提供する**Timeline**は、徐々に機能縮小に向かっています。"
                    "これにより、個々のユーザーが過去の軌跡を振り返る機会が減少しつつあります。しかし、"
                    "このサービスは多くの人々にとって、日々の生活を振り返る貴重なツールであることには変わりありません。")

        st.markdown("#### 2. **位置情報共有と軌跡記録のギャップ**")
        st.markdown("現在、多くの位置情報共有アプリはありますが、それと同時に自分の**軌跡**を残すサービスは非常に少ないのが現状です。"
                    "また、位置情報を取得しているものの、そのデータを**ユーザーにとって使いやすい形で提供**しているサービスは多くありません。"
                    "ユーザー自身の記録として、もっと直感的に活用したいという需要があると考えています。")

        st.markdown("#### 3. **このWebアプリの目指すもの**")
        st.markdown("このWebアプリは、あなたの**軌跡**を簡単に記録し、**シンプルに共有**できることを目指しています。"
                    "これにより、ただの位置情報ではなく、あなたの「歩み」を他の人と共有できる新しい価値を提供します。"
                    "未来的には、**どこに行ったかをただ見るだけでなく、どんな体験をしたのか**を振り返り、共有することができるようにしたいと考えています。")

        st.markdown("#### 4. **スマホアプリとの連携**")
        st.markdown("現在、このWebアプリはもちろん、**スマホアプリ**の開発も進めています。"
                    "スマートフォンを通じて、あなたの軌跡をさらに快適に記録し、どこでも簡単にアクセスできるようにしていきます。"
                    "これにより、日常生活で自然に利用できるようになることを目指します。")
