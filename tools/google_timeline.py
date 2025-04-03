import json
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import io


def parse_timestamp(time_str, offset):
    if time_str:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return dt - timedelta(minutes=offset)
    return None


def extract_timeline_data(uploaded_file):
    """JSONデータを解析し、DataFrameに変換（軽量化対応）"""
    file_content = uploaded_file.getvalue().decode()  # メモリ効率化のために変換
    data = json.load(io.StringIO(file_content))  # 文字列として処理
    if 'semanticSegments' not in data:
        raise ValueError("Error: 'semanticSegments' key not found in the JSON file.")

    records = []
    for segment in data['semanticSegments']:
        start_time = parse_timestamp(segment.get('startTime'), segment.get('startTimeTimezoneUtcOffsetMinutes', 0))
        end_time = parse_timestamp(segment.get('endTime'), segment.get('endTimeTimezoneUtcOffsetMinutes', 0))

        if 'timelinePath' in segment:
            for path in segment['timelinePath']:
                point_time = parse_timestamp(path.get('time'), segment.get('startTimeTimezoneUtcOffsetMinutes', 0))
                lat, lng = map(float, path['point'].replace('°', '').split(', '))
                records.append(["timelinePath", start_time, end_time, point_time, lat, lng, None, None, None, None, None, None])

        if 'visit' in segment:
            visit = segment['visit']
            top_candidate = visit.get('topCandidate', {})
            if 'placeLocation' in top_candidate and 'latLng' in top_candidate['placeLocation']:
                lat, lng = map(float, top_candidate['placeLocation']['latLng'].replace('°', '').split(', '))
                records.append(["visit", start_time, end_time, None, lat, lng, visit.get('probability'), top_candidate.get('placeId'), top_candidate.get('semanticType'), None, None, None])

        if 'activity' in segment:
            activity = segment['activity']
            top_candidate = activity.get('topCandidate', {})
            for key in ['start', 'end']:
                if key in activity and 'latLng' in activity[key]:
                    lat, lng = map(float, activity[key]['latLng'].replace('°', '').split(', '))
                    records.append([f"activity_{key}", start_time, end_time, None, lat, lng, None, None, None, activity.get('distanceMeters'), top_candidate.get('type'), top_candidate.get('probability')])

    columns = ["type", "start_time", "end_time", "point_time", "latitude", "longitude", "visit_probability", "visit_placeId", "visit_semanticType", "activity_distanceMeters", "activity_type", "activity_probability"]
    df = pd.DataFrame(records, columns=columns)

    # メモリ最適化: float型をfloat32に変換
    df["latitude"] = df["latitude"].astype("float64")
    df["longitude"] = df["longitude"].astype("float64")
    df["activity_distanceMeters"] = pd.to_numeric(df["activity_distanceMeters"], errors="coerce").astype("float32")
    df["visit_probability"] = pd.to_numeric(df["visit_probability"], errors="coerce").astype("float32")
    df["activity_probability"] = pd.to_numeric(df["activity_probability"], errors="coerce").astype("float32")

    return df


# Streamlit UI
def google_timeline():
    st.title("📍 Google Timeline JSON Converter")

    # 説明
    st.markdown("""
    **このツールについて**  
    Google マップの **タイムライン JSON ファイル** を、見やすい表形式に変換します。  
    CSVとしてダウンロードしたり、地図上に表示したりできます。
    """)
    

    png_path = "items/googel_timeline-1.png"
    st.image(png_path, caption="Googleマップのタイムラインエクスポート方法", use_container_width=True)

    # JSONアップロード
    uploaded_file = st.file_uploader("📂 タイムラインJSONファイルをアップロード", type="json")

    if uploaded_file is not None:
        with st.spinner("🔄 データを解析中..."):
            df = extract_timeline_data(uploaded_file)

        st.success(f"✅ 解析完了！{len(df):,} 行のデータを取得しました。")

        
        st.subheader("📊 解析結果 (最大50行表示)")
        st.dataframe(df.head(50))  

        csv_data = df.to_csv(index=False).encode('utf-8')

        st.download_button("📥 CSVをダウンロード", csv_data, "timeline_data.csv", "text/csv")
        
        
        st.subheader("📊 各カラムの説明")
        st.markdown("""
        | **カラム名**                | **説明**                                                                                                                                     |
        |-----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
        | **type**                    | イベントの種類。`timelinePath`（移動経路）、`visit`（訪問場所）、`activity_start` / `activity_end`（アクティビティの開始/終了）があります。 |
        | **start_time**               | イベントの開始時刻（ISO 8601形式、タイムゾーン付き）。                                                                                       |
        | **end_time**                 | イベントの終了時刻（ISO 8601形式、タイムゾーン付き）。                                                                                       |
        | **point_time**               | 特定のタイムポイントの時刻（`NaT`は時刻が存在しないことを示します）。                                                                        |
        | **latitude**                 | イベントが発生した場所の緯度（例: 34.780489）。                                                                                               |
        | **longitude**                | イベントが発生した場所の経度（例: 135.475209）。                                                                                              |
        | **visit_probability**        | 訪問の確率。訪問している場合の確率（`NaN`はデータがないことを意味します）。                                                                 |
        | **visit_placeId**            | 訪問した場所のID（Google Places APIのIDなど）。                                                                                               |
        | **visit_semanticType**       | 訪問した場所のタイプ（例: `INFERRED_HOME`、`RESTAURANT`）。                                                                                   |
        | **activity_distanceMeters**  | アクティビティの移動距離（メートル単位）。`NaN`は移動が記録されていないことを意味します。                                                   |
        | **activity_type**            | ユーザーのアクティビティのタイプ（例: `UNKNOWN_ACTIVITY_TYPE`、`WALKING`、`DRIVING`）。                                                      |
        | **activity_probability**     | アクティビティの確率（0.0はアクティビティが発生していないことを示し、1.0はアクティビティが確実であることを示します）。                        |
        """)
        
        if "latitude" in df.columns and "longitude" in df.columns:
            st.subheader("📍 位置情報を地図に表示")

            # **データが多すぎる場合、サンプリング**
            if len(df) > 10_0000:
                st.warning("⚠️ データが多いため、一部のみ表示しています (10,0000件サンプリング)")
                df_map = df.sample(10_0000, random_state=42)
            else:
                df_map = df.copy()

            st.map(df_map[["latitude", "longitude"]])
