import streamlit as st
import requests

st.title("📷 高画質写真検索ツール (Unsplash版)")
st.write("おしゃれなフリー素材を検索してギャラリー表示します。")

# 1. アプリの「記憶（Session State）」を準備する
# これにより、ボタンを押して画面が再読み込みされても「現在のキーワード」と「現在のページ」を忘れないようにします
if "page_num" not in st.session_state:
    st.session_state.page_num = 1
if "current_keyword" not in st.session_state:
    st.session_state.current_keyword = ""

# 検索窓
keyword_input = st.text_input("検索キーワード（例: cat, tokyo, nature など）", value=st.session_state.current_keyword)

# 検索ボタンが押されたら、記憶をリセットして1ページ目から検索開始
if st.button("検索"):
    st.session_state.current_keyword = keyword_input
    st.session_state.page_num = 1

# 記憶されているキーワードがある場合のみ、検索処理を実行
keyword = st.session_state.current_keyword

if keyword:
    with st.spinner(f"「{keyword}」の {st.session_state.page_num} ページ目を検索中..."):
        api_url = f"http://127.0.0.1:8002/search-images?keyword={keyword}&page={st.session_state.page_num}"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and data["images"]:
                st.success(f"「{keyword}」の検索結果（{st.session_state.page_num}ページ目）")
                
                # --- 2. ここからページネーション（< 1 2 3 4 5 >）のUI作成 ---
                # 7等分の細いカラムを作り、横一列にボタンを並べます
                page_cols = st.columns(7)
                
                # [◀] 前へボタン（1ページ目の時は押せないようにする）
                with page_cols[0]:
                    if st.button("◀", disabled=(st.session_state.page_num == 1)):
                        st.session_state.page_num -= 1
                        st.rerun()  # クリックされた瞬間に画面を強制リロード
                
                # [1] [2] [3] [4] [5] 数字ボタン（現在のページを中心に5つ表示）
                start_page = max(1, st.session_state.page_num - 2)
                for i in range(5):
                    p = start_page + i
                    with page_cols[i + 1]:
                        # 現在のページだけボタンの色を目立たせる（primary）
                        btn_type = "primary" if p == st.session_state.page_num else "secondary"
                        if st.button(str(p), type=btn_type):
                            st.session_state.page_num = p
                            st.rerun()
                
                # [▶] 次へボタン
                with page_cols[6]:
                    if st.button("▶"):
                        st.session_state.page_num += 1
                        st.rerun()
                
                st.markdown("---") # 見栄えを良くするための横線
                
                # --- 3. 画像の表示 ---
                img_cols = st.columns(3)
                for i, img_url in enumerate(data["images"]):
                    img_cols[i % 3].image(img_url, use_container_width=True)
            else:
                st.warning("画像が見つかりませんでした。別のキーワードを試してください。")
        else:
            st.error("バックエンドとの通信に失敗しました。")