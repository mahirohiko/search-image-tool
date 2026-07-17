import os
import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import warnings

load_dotenv()
app = FastAPI()

# ==========================================
# 👿 セキュリティソフト貫通パッチ (Unsplash & Gemini共通)
# ==========================================
warnings.filterwarnings("ignore")
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@app.get("/search-images")
def search_images(
    keyword: str = Query(..., description="ユーザーの入力文、またはAI生成済みの英語キーワード"),
    page: int = Query(1, description="ページ番号"),
    is_already_english: bool = Query(False, description="すでにAI翻訳済みの英語キーワードかどうか")
):
    
    # ------------------------------------------
    # 🧠 Step 1: Geminiによる「AI検索キーワード生成」（初回のみ！）
    # ------------------------------------------
    if not is_already_english:
        prompt = f"""
        あなたは優秀な画像検索アシスタントです。
        ユーザーの入力を分析し、Unsplashで画像検索するための最適な「英語の検索キーワード（2〜5語）」を1つだけ生成してください。

        【重要ルール】
        1. 感情やシチュエーションの場合は、ニュアンスを汲み取った意訳（例："moody sunset"）にしてください。
        2. 具体的な被写体を求められている場合は、その被写体を表す直接的な英単語を含めてください。
        3. ⚠️【Unsplashの特性への配慮】Unsplashは欧米向けのフリー素材サイトであるため、ニッチな固有名詞や「japanese ○○」のような限定的すぎる組み合わせは画像がヒットしません。
           もし検索結果が0件になりそうなローカルな被写体の場合は、より汎用的で視覚的な要素に分解してください。
           （例：「日本のロックバンド」→ "live concert rock band" や "guitarist live stage" など）
        4. 余計な説明、挨拶、引用符などは絶対に含めず、英語キーワードのみを出力すること。
        ユーザーの入力: {keyword}
        """
        
        try:
            # 💡 公式ライブラリを使わず、直接 requests で Gemini API を叩く！
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GOOGLE_API_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            # Unsplashと同じように verify=False でSSLを強行突破！
            gemini_res = requests.post(gemini_url, json=payload, verify=False)
            gemini_res.raise_for_status()
            
            # JSONから生成されたテキストを抽出
            ai_keyword = gemini_res.json()["candidates"][0]["content"]["parts"][0]["text"].strip().replace('"', '')
            print(f"🤖 [Gemini 新規解析] 「{keyword}」 ➜ 『{ai_keyword}』")
            
        except Exception as e:
            print(f"⚠️ Gemini APIエラー: {e}")
            ai_keyword = keyword
    else:
        ai_keyword = keyword
        print(f"⚡ [AIパススルー] すでに翻訳済みのキーワード『{ai_keyword}』で{page}ページ目を直接検索します。")

    # ------------------------------------------
    # 📸 Step 2: Unsplashを検索
    # ------------------------------------------
    unsplash_url = "https://api.unsplash.com/search/photos"
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    params = {
        "query": ai_keyword,
        "per_page": 30,
        "page": page
    }
    
    try:
        response = requests.get(unsplash_url, headers=headers, params=params, verify=False)
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