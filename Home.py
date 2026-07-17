import streamlit as st
import requests

st.set_page_config(page_title="📷 AI高画質写真検索ツール", layout="wide")

st.title("📷 高画質写真検索ツール (Unsplash × Gemini AI版)")
st.write("曖昧な表現やシチュエーションを入力すると、AIが意図を汲み取って世界中から最適なフリー素材を探し出します。")

# ==========================================
# 1. アプリの「記憶（Session State）」を準備する
# ==========================================
if "page_num" not in st.session_state:
    st.session_state.page_num = 1
if "current_keyword" not in st.session_state:
    st.session_state.current_keyword = ""
if "ai_keyword" not in st.session_state: # 👈 追加：AIが作った英語キーワードを記憶する場所
    st.session_state.ai_keyword = ""

# 検索窓
keyword_input = st.text_input(
    "🔎 どんなイメージの画像をお探しですか？（曖昧な日本語でOK！）", 
    value=st.session_state.current_keyword,
    placeholder="例：夏の終わりの寂しい夕暮れ、仕事がはかどる静かなカフェ、など"
)

# 検索ボタンが押されたら、記憶を完全にリセットして新規検索
if st.button("AIで検索する", type="primary"):
    st.session_state.current_keyword = keyword_input
    st.session_state.page_num = 1
    st.session_state.ai_keyword = "" # 新規検索なので、AIキーワードの記憶も消す

# 記憶されているキーワードがある場合のみ、検索処理を実行
keyword = st.session_state.current_keyword

if keyword:
    # --- ここがポイント！ ---
    # すでにAIキーワード（英語）を記憶しているかどうかで、バックエンドへの頼み方を変える
    if st.session_state.ai_keyword:
        # 【2ページ目以降】すでに英語が手元にあるので、それを使って直接検索（高速！）
        api_url = f"http://127.0.0.1:8002/search-images?keyword={st.session_state.ai_keyword}&page={st.session_state.page_num}&is_already_english=True"
        spinner_msg = f"「{keyword}」の {st.session_state.page_num} ページ目を読み込み中..."
    else:
        # 【最初の1回】まだ英語がないので、Geminiを動かしてキーワードを作ってもらう
        api_url = f"http://127.0.0.1:8002/search-images?keyword={keyword}&page={st.session_state.page_num}&is_already_english=False"
        spinner_msg = f"「{keyword}」のニュアンスをAIが解析中..."

    with st.spinner(spinner_msg):
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and data["images"]:
                # 🤖 初回時、バックエンドから返ってきた英語キーワードをセッションに記憶する！
                if not st.session_state.ai_keyword:
                    st.session_state.ai_keyword = data.get("ai_keyword", "")
                
                # 検索結果とAIの解析結果を表示
                st.success(f"「{keyword}」の検索結果（{st.session_state.page_num}ページ目）")
                st.info(f"💡 **AI検索アシスト:** 「{keyword}」を **『 {st.session_state.ai_keyword} 』** と解釈して画像を厳選しました！")
                
                # --- 2. ページネーション（< 1 2 3 4 5 >）のUI作成 ---
                page_cols = st.columns(7)
                
                # [◀] 前へボタン
                with page_cols[0]:
                    if st.button("◀", disabled=(st.session_state.page_num == 1)):
                        st.session_state.page_num -= 1
                        st.rerun()
                
                # [1] [2] [3] [4] [5] 数字ボタン
                start_page = max(1, st.session_state.page_num - 2)
                for i in range(5):
                    p = start_page + i
                    with page_cols[i + 1]:
                        btn_type = "primary" if p == st.session_state.page_num else "secondary"
                        if st.button(str(p), type=btn_type):
                            st.session_state.page_num = p
                            st.rerun()
                
                # [▶] 次へボタン
                with page_cols[6]:
                    if st.button("▶"):
                        st.session_state.page_num += 1
                        st.rerun()
                
                st.markdown("---")
                
                # --- 3. 画像の表示（3列ギャラリー） ---
                img_cols = st.columns(3)
                for i, img_url in enumerate(data["images"]):
                    img_cols[i % 3].image(img_url, use_container_width=True)
            else:
                st.warning("画像が見つかりませんでした。別のキーワードを試してください。")
        else:
            st.error("バックエンドとの通信に失敗しました。")