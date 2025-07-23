import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# --- 1. Streamlitページの基本設定 ---
st.set_page_config(
    page_title="👗💄 パーソナルカラー・骨格診断マッチングツール",
    layout="wide", # ページレイアウトを広く設定
    initial_sidebar_state="expanded" # サイドバーをデフォルトで開いた状態にする
)

st.title("👗💄 パーソナルカラー・骨格診断マッチングツール")
st.markdown("あなたのパーソナルカラーと骨格タイプに合わせたファッション・コスメアイテムを見つけましょう！")

# --- 2. データ読み込み (パフォーマンス最適化のためにキャッシュを使用) ---
@st.cache_data
def load_data():
    """CSVファイルを読み込む関数。キャッシュにより高速化。"""
    try:
        # Excelで保存したCSVやPythonでutf-8-sigで保存したCSVは 'utf-8-sig' を推奨
        df = pd.read_csv('cosmetic_products.csv', encoding='utf-8-sig')
        return df
    except FileNotFoundError:
        st.error("`cosmetic_products.csv` ファイルが見つかりません。アプリと同じフォルダにアップロードしてください。")
        st.info("データ生成コードを実行してファイルを作成してください。")
        return pd.DataFrame() # 空のデータフレームを返す

df = load_data()

if df.empty:
    st.stop() # データが読み込めなかった場合は、アプリの実行を停止

# --- 3. UI（ユーザーインターフェース）の構築: サイドバー ---
st.sidebar.header("あなたの診断結果を入力してください")

# パーソナルカラーの複数選択
personal_color_options = ["イエベ春", "イエベ秋", "ブルベ夏", "ブルベ冬"]
selected_personal_colors = st.sidebar.multiselect(
    "💡 あなたのパーソナルカラーは？（複数選択可）",
    personal_color_options,
    default=[] # 初期値は空リスト
)

# 骨格タイプの複数選択
bone_structure_options = ["ストレート", "ウェーブ", "ナチュラル"]
selected_bone_structures = st.sidebar.multiselect(
    "💡 あなたの骨格タイプは？（複数選択可）",
    bone_structure_options,
    default=[] # 初期値は空リスト
)

# --- 4. データフィルタリング ---
filtered_df = df.copy() # オリジナルのデータフレームを保護

# パーソナルカラーでの絞り込み
if selected_personal_colors: # リストが空でない場合のみフィルタリング
    # isin() を使用して、リスト内のいずれかの値に一致する行を抽出
    filtered_df = filtered_df[filtered_df['Personal_Color_Type'].isin(selected_personal_colors)]

# 骨格タイプでの絞り込み
if selected_bone_structures: # リストが空でない場合のみフィルタリング
    # isin() を使用して、リスト内のいずれかの値に一致する行を抽出
    filtered_df = filtered_df[filtered_df['Bone_Structure_Type'].isin(selected_bone_structures)]

# --- 5. データ表示と可視化 ---

# タブ機能で表示を切り替え
tab1, tab2, tab3, tab4, = st.tabs([
    "✨ おすすめアイテムリスト",
    "📊 カテゴリ別構成",
    "🎨 カラーパレット",
    "🤖 AIアドバイス",
])

with tab1:
    st.subheader("あなたにおすすめのアイテム一覧")
    if not filtered_df.empty:
        # 表示する列を選択し、インデックスをリセットして見やすくする
        display_columns = ['Product_Name', 'Category', 'Personal_Color_Type', 'Bone_Structure_Type', 'Color_Group', 'Description']
        st.dataframe(filtered_df[display_columns].reset_index(drop=True), use_container_width=True)
        
        # ダウンロードボタン
        st.download_button(
            label="ダウンロード (CSV)",
            data=filtered_df[display_columns].to_csv(index=False).encode('utf-8-sig'),
            file_name="おすすめアイテム.csv",
            mime="text/csv",
        )
    else:
        st.info("選択された条件に合うアイテムが見つかりませんでした。サイドバーの条件を変更してみてください。")

with tab2:
    st.subheader("おすすめアイテムのカテゴリ別構成")
    if not filtered_df.empty:
        category_counts = filtered_df['Category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        fig_pie = px.pie(
            category_counts,
            values='Count',
            names='Category',
            title='おすすめアイテムのカテゴリ別割合',
            hole=0.3, # ドーナツグラフにする
            color_discrete_sequence=px.colors.qualitative.Pastel # 色のテーマを変更
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label') # 割合とラベルを内部に表示
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("表示するデータがありません。サイドバーで条件を選択してください。")

with tab3:
    st.subheader("おすすめカラーパレット")
    if not filtered_df.empty:
        color_counts = filtered_df['Color_Group'].value_counts().reset_index()
        color_counts.columns = ['Color_Group', 'Count']
        fig_bar = px.bar(
            color_counts,
            x='Color_Group',
            y='Count',
            title='おすすめカラーグループのアイテム数',
            color='Count', # Countの数で色を付ける
            color_continuous_scale='Sunsetdark' # カラーパレットを変更
        )
        fig_bar.update_layout(xaxis_tickangle=-45) # ラベルを斜めに表示して見やすくする
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("表示するデータがありません。サイドバーで条件を選択してください。")



with tab4:
    st.subheader("AIアドバイス")
    st.write("Gemini APIと連携して、パーソナルなアドバイスを受け取ることができます。")

    try:
        # .streamlit/secrets.toml ファイルに GEMINI_API_KEY = "your_api_key_here" を設定してください。
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key="AIzaSyA3WRHZZBKzLiW21KjeDdL17YXrjB6KJ50")
        # 使用するモデルを指定します。利用可能なモデルはGemini APIのドキュメントで確認してください。
        # 例: 'gemini-1.5-flash-latest', 'gemini-1.5-pro-latest' など
        model = genai.GenerativeModel('gemini-2.0-flash-latest')
    

        st.write("### AIに質問してみる")
        user_query = st.text_area(
            "例: 『ブルベ夏におすすめのリップの選び方は？』や『ストレート骨格に似合うトップスは？』",
            height=100
        )
        
        if st.button("AIにアドバイスを求める"):
            if user_query:
                with st.spinner("AIがアドバイスを生成中..."):
                    # ユーザーの選択とフィルタリングされたデータもプロンプトに含めることで、より的確なアドバイスが可能
                    prompt_parts = [
                        "あなたはファッションとコスメのパーソナルアドバイザーです。",
                        f"ユーザーのパーソナルカラー: {', '.join(selected_personal_colors) if selected_personal_colors else '未選択'}",
                        f"ユーザーの骨格タイプ: {', '.join(selected_bone_structures) if selected_bone_structures else '未選択'}",
                        "", # 改行
                        "現在表示されているアイテムの一部（参考）：",
                        # フィルタリングされたデータが空でない場合のみhead()を適用
                        filtered_df[['Product_Name', 'Category', 'Color_Group', 'Personal_Color_Type', 'Bone_Structure_Type']].head(5).to_string() if not filtered_df.empty else "（該当アイテムなし）",
                        "", # 改行
                        f"ユーザーからの質問：{user_query}",
                        "上記の情報を踏まえ、具体的で役立つファッション・コスメのアドバイスをしてください。",
                        "敬語で丁寧にお答えください。"
                    ]
                    response = model.generate_content(prompt_parts)
                    st.success("AIからのアドバイス：")
                    st.markdown(response.text) # Markdown形式で表示
            else:
                st.warning("質問を入力してください。")
    except KeyError:
        st.warning("Gemini APIキーが設定されていません。`.streamlit/secrets.toml` に `GEMINI_API_KEY = \"あなたのAPIキー\"` を追加してください。")
        st.markdown("[Google AI Studio でAPIキーを取得](https://aistudio.google.com/app/apikey) (Googleアカウントが必要です)")
    except Exception as e:
        st.error(f"Gemini APIの呼び出し中にエラーが発生しました。詳細: {e}")
        st.info("APIキーが正しいか、インターネット接続があるか、APIの利用制限に達していないかご確認ください。")
