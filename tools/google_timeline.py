import streamlit as st
import pandas as pd
import numpy as np
import io
import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_values
from supabase import create_client, Client

# Supabase のセットアップ
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def show_username_if_exists(supabase):
    # セッションから user_id を取得
    try:
        user_dict = st.session_state.user.dict()
        user_id = user_dict.get("id", None)
    except AttributeError:
        st.warning("⚠ ユーザー情報がセッションに保存されていません。")
        return None
    
    if not user_id:
        st.warning("⚠ ユーザーIDが見つかりません。")
        return None

    # Supabaseから username を取得
    response = supabase.table("username").select("username").eq("user_id", user_id).execute()

    if response.data:
        username = response.data[0]["username"]
        st.session_state.username = username  # ← セッションに保存！
        st.markdown(f"**ユーザー名**: {username}")
        return username
    else:
        st.warning("⚠ ユーザー名が登録されていません。")
        return None


def convert_series_to_utc(series: pd.Series) -> pd.Series:
    dt_series = pd.to_datetime(series, errors='coerce')
    if dt_series.dt.tz is None:
        dt_series = dt_series.dt.tz_localize('Asia/Tokyo')
    else:
        dt_series = dt_series.dt.tz_convert('Asia/Tokyo')
    return dt_series.dt.tz_convert('UTC')


def extract_timeline_data(uploaded_file):
    file_content = uploaded_file.getvalue().decode()
    data = json.load(io.StringIO(file_content))

    if 'semanticSegments' not in data:
        raise ValueError("Error: 'semanticSegments' key not found in the JSON file.")

    records = []
    for segment in data['semanticSegments']:
        start_time = segment.get('startTime')
        end_time = segment.get('endTime')

        if 'timelinePath' in segment:
            for path in segment['timelinePath']:
                point_time = path.get('time')

                try:
                    lat, lng = map(float, path['point'].replace('°', '').split(', '))
                except Exception:
                    lat, lng = None, None

                records.append([
                    "timelinePath", start_time, end_time, point_time, lat, lng,
                    None, None, None, None, None, None, st.session_state.username
                ])

        if 'visit' in segment:
            visit = segment['visit']
            top_candidate = visit.get('topCandidate', {})
            try:
                lat, lng = map(float, top_candidate.get('placeLocation', {}).get('latLng', '').replace('°', '').split(', '))
            except Exception:
                lat, lng = None, None

            records.append([
                "visit", start_time, end_time, None, lat, lng,
                visit.get('probability'), top_candidate.get('placeId'), top_candidate.get('semanticType'),
                None, None, None, st.session_state.username
            ])

        if 'activity' in segment:
            activity = segment['activity']
            top_candidate = activity.get('topCandidate', {})
            for key in ['start', 'end']:
                if key in activity and 'latLng' in activity[key]:
                    try:
                        lat, lng = map(float, activity[key]['latLng'].replace('°', '').split(', '))
                    except Exception:
                        lat, lng = None, None

                    records.append([
                        f"activity_{key}", start_time, end_time, None, lat, lng,
                        None, None, None,
                        activity.get('distanceMeters'), top_candidate.get('type'), top_candidate.get('probability'),
                        st.session_state.username
                    ])

    columns = [
        "type", "start_time", "end_time", "point_time", "latitude", "longitude",
        "visit_probability", "visit_placeId", "visit_semanticType",
        "activity_distanceMeters", "activity_type", "activity_probability",
        "username"
    ]
    df = pd.DataFrame(records, columns=columns)

    # ⏱ タイムスタンプ列の高速一括変換
    for col in ["start_time", "end_time", "point_time"]:
        df[col] = convert_series_to_utc(df[col])

    df = df.astype({
        "latitude": "float64",
        "longitude": "float64",
        "activity_distanceMeters": "float32",
        "visit_probability": "float32",
        "activity_probability": "float32"
    })

    df = df.replace({np.nan: None})
    return df


def upload_to_postgresql(df, conn, table_name="timeline_data"):
    # アップロード処理中の表示
    with st.spinner("データをアップロードしています... 少々お待ちください。"):
        with conn.cursor() as cur:
            insert_query = f"""
            INSERT INTO {table_name} (
                type, start_time, end_time, point_time,
                latitude, longitude,
                visit_probability, visit_placeId, visit_semanticType,
                activity_distanceMeters, activity_type, activity_probability,
                username
            ) VALUES %s
            """
            values = df.values.tolist()
            execute_values(cur, insert_query, values)
            conn.commit()


def google_timeline():
    username = st.session_state.get("username", None)
    if not username:
        st.warning("⚠ ユーザー名がセッションに保存されていません。")
        return

    st.title("📍 Google Timeline データのアップロード")

    # 説明と画像を追加
    st.markdown("### ❓ Google タイムラインのエクスポート方法")
    st.markdown("""
    まず、Google タイムラインはスマホの「位置情報」機能を使って端末本体に収集されていることを確認してください。

    1. **Androidの場合**: 設定画面から「位置情報」設定に進み、「Google タイムライン」オプションを探してみましょう。
    2. **iPhoneの場合**: まぁ、少し大変かもしれませんが、頑張って探してみてくださいね。Google マップアプリ内にもオプションがあるかもしれません！
    3. 「タイムラインのエクスポート」から**JSON形式**でエクスポートしてください。

    これで準備完了です！あとはこのファイルをアップロードするだけです。
    """)
    st.image("items/googel_timeline-1.png", caption="Google Timelineのエクスポート手順", use_container_width=True)

    # アップロードUI
    st.markdown("### 📤 JSONファイルのアップロード")
    uploaded_file = st.file_uploader("Google Timeline JSONファイルを選択", type=["json"])

    if uploaded_file:
        try:
            df = extract_timeline_data(uploaded_file)
            df["username"] = username  # ユーザー名を追加
            st.success(f"{len(df)} 件のレコードを抽出しました。")
            st.dataframe(df, use_container_width=True)

            # PostgreSQLにアップロードボタン
            if st.button("⬆ PostgreSQLにアップロード"):
                with st.spinner("データをアップロード中..."):
                    conn = psycopg2.connect(**st.secrets["postgresql"])
                    upload_to_postgresql(df, conn)
                    conn.close()
                st.success("✅ アップロードが完了しました！")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")