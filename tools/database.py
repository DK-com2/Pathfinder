import streamlit as st
import psycopg2
import pandas as pd

# .streamlit/secrets.toml から接続情報を読み取る
db_config = st.secrets["postgresql"]

# データベース接続関数
def get_db_connection():
    return psycopg2.connect(
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
        port=db_config["port"]
    )

# データ取得関数
def get_timeline_data(username=None):
    conn = get_db_connection()
    query = "SELECT * FROM timeline_data"
    if username:
        query += " WHERE username = %s"
        df = pd.read_sql(query, conn, params=(username,))
    else:
        df = pd.read_sql(query, conn)
    conn.close()
    return df

# タイムスタンプをJSTに変換
def convert_to_jst(df, time_columns=['start_time', 'end_time', 'point_time']):
    for col in time_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            df[col] = df[col].dt.tz_convert('Asia/Tokyo')
    return df

# 統計表示
def show_statistics(df):
    with st.container():
        st.header("📊 myDB")
        df = convert_to_jst(df)

        with st.expander("🔍 基本統計量"):
            st.write(df.describe(include='all'))

        with st.expander("📂 タイプ別データ数"):
            if 'type' in df.columns:
                st.bar_chart(df['type'].value_counts())

        with st.expander("🧭 Visit Semantic Type"):
            if 'visit_semanticType' in df.columns:
                st.bar_chart(df['visit_semanticType'].value_counts())

        with st.expander("🏃 Activity Type"):
            if 'activity_type' in df.columns:
                st.bar_chart(df['activity_type'].value_counts())

        with st.expander("🗺️ マップ"):
            if 'latitude' in df.columns and 'longitude' in df.columns:
                st.map(df[['latitude', 'longitude']])

# メイン画面
def database_view():
    st.title("🗂️ PostgreSQL データベースビュー")

    if "username" not in st.session_state:
        st.warning("⚠ ユーザー名がセッションに保存されていません。")
        return

    username = st.session_state.username

    with st.container():
        st.subheader("データベースから取得")
        if st.button("📥 myDBへ接続"):
            try:
                df = get_timeline_data(username)
                if df.empty:
                    st.info(f"{username} のデータは存在しません。")
                else:
                    show_statistics(df)
            except Exception as e:
                st.error(f"データの取得に失敗しました: {e}")


