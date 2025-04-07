import streamlit as st
import psycopg2

# .streamlit/secrets.toml から接続情報を読み取る
db_config = st.secrets["postgresql"]

# 接続情報の確認（デバッグ用）
st.write(db_config)
