import streamlit as st
from supabase import create_client, Client
import folium
import pandas as pd

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ユーザー情報を表示
def show_session_info():
    if "logged_in" in st.session_state and st.session_state.logged_in:
        st.markdown("### 👤 ユーザー情報")
        
        try:
            # ユーザー情報を取得
            user_dict = st.session_state.user.dict()
            
            st.markdown(f"**ユーザーID:** {user_dict.get('id', '不明')}")
            st.markdown(f"**メールアドレス:** {user_dict.get('email', '不明')}")
        
        except AttributeError:
            st.error("ユーザー情報の取得に失敗しました。")

    else:
        st.warning("⚠ ログインしていません。ログインしてください。")


#Supabaseからuser_idに一致するusernameを取得し、結果を表示
def get_username_by_user_id():
    # セッションからuser_idを取得
    try:
        user_dict = st.session_state.user.dict()
        user_id = user_dict.get("id", None)  
    except AttributeError:
        st.warning("⚠ ユーザー情報がセッションに保存されていません。")
        return None
    
    if not user_id:
        st.warning("⚠ ユーザーIDが見つかりません。")
        return None
    
    # user_idに一致するusername
    response = supabase.table("username").select("username").eq("user_id", user_id).execute()

   
    if response.data:
        # ユーザー名が見つかった場合
        username = response.data[0]["username"]
        st.session_state.username = username
        st.markdown(f"**ユーザー名**: {username}")
        return username
    else:
        # ユーザー名が見つからない場合
        st.warning("⚠ ユーザー名が設定されていないです。")
        
        # 新しいユーザー名の入力
        with st.container():
            new_username = st.text_input("ユーザー名を入力してください")
            if st.button("登録"):
                if new_username:
                    # 新しいユーザー名をSupabaseに登録
                    supabase.table("username").insert({"user_id": user_id, "username": new_username}).execute()
                    st.session_state.username = new_username
                    st.success(f"ユーザー名「{new_username}」を登録しました。")
                    return new_username
                else:
                    st.warning("ユーザー名を入力してください。")
        return None



# DB からデータを取得してマップに表示 
def map():    
    response = supabase.table("locations").select("*").eq("username", st.session_state.username).execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        st.write(df)
        
        map = folium.Map(location=[36.0047, 137.5936], zoom_start=5)
        
        # 各地点にピンを追加
    for _, row in df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"username: {row['username']}\nComment: {row['comment']}\nTimestamp: {row['timestamp']}"
        ).add_to(map)
    
    st.write("### Locations Map")
    st.components.v1.html(map._repr_html_(), width=700, height=500)



def dashboard():
    st.title("ダッシュボード")
    st.write(f"ようこそ、{st.session_state.user.email}さん！")
    
    show_session_info()
    get_username_by_user_id()
    map()
    