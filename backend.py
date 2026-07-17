import os
import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai  # 👈 追加

load_dotenv()
app = FastAPI()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# ==========================================
# 🤖 Gemini APIの初期化
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')  # 高速・軽量で最適なモデル

@app.get("/search-images")
def search_images(
    keyword: str = Query(..., description="ユーザーの入力文、またはAI生成済みの英語キーワード"),
    page: int = Query(1, description="ページ番号"),
    is_already_english: bool = Query(False, description="すでにAI翻訳済みの英語キーワードかどうか")  # 👈 これを追加！
):
    """
    1. 初回（is_already_english=False）は、日本語をGeminiで英語キーワードに変換。
    2. 2回目以降（is_already_english=True）は、Geminiを通さずにそのキーワードで直接検索。
    """
    
    # ------------------------------------------
    # 🧠 Step 1: Geminiによる「AI検索キーワード生成」（初回のみ！）
    # ------------------------------------------
    if not is_already_english:
        prompt = f"""
        あなたは優秀な画像検索アシスタントです。
        ユーザーが入力した日本語の「曖昧な表現、感情、シチュエーション」を深く解釈し、
        Unsplashでそのニュアンスに合致する美しい写真を見つけるための、
        最も適切な「英語の検索キーワード（2〜3語のスペース区切り）」を1つだけ生成してください。

        【制約ルール】
        - 余計な説明、挨拶、導入文、引用符などは絶対に含めず、英語キーワードのみを出力すること。
        - 例：「休日の朝にコーヒーを飲んでリラックス」 -> "cozy morning coffee" のように出力。

        ユーザーの入力: {keyword}
        """
        try:
            response = model.generate_content(prompt)
            ai_keyword = response.text.strip().replace('"', '')
            print(f"🤖 [Gemini 新規解析] 「{keyword}」 ➜ 『{ai_keyword}』")
        except Exception as e:
            print(f"⚠️ Gemini APIエラー: {e}")
            ai_keyword = keyword
    else:
        # 2ページ目以降は、送られてきたキーワードをそのまま使う（Geminiは起動しない！）
        ai_keyword = keyword
        print(f"⚡ [AIパススルー] すでに翻訳済みのキーワード『{ai_keyword}』で{page}ページ目を直接検索します。")

    # ------------------------------------------
    # 📸 Step 2: Unsplashを検索
    # ------------------------------------------
    url = "https://api.unsplash.com/search/photos"
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    params = {
        "query": ai_keyword,
        "per_page": 30,
        "page": page
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        
        image_urls = []
        for item in data.get("results", []):
            image_urls.append(item["urls"]["regular"])
                
        return {
            "status": "success", 
            "images": image_urls,
            "ai_keyword": ai_keyword
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}