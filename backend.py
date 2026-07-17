import os
import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 取得したUnsplashのAccess Keyをセット（本来は.envに入れますが、テスト用なら直接でもOKです）
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "gjZCIJ0zQCKRAwC1uJMRpyPvJsTPM1KzK_8cc91X3N8")

@app.get("/search-images")
def search_images(
    keyword: str = Query(..., description="検索キーワード"),
    page: int = Query(1, description="ページ番号")  # デフォルトは1ページ目
):
    """
    Unsplash APIを使って画像を検索し、URLのリストを返すエンドポイント
    """
    url = "https://api.unsplash.com/search/photos"
    
    # 認証情報をヘッダーにセット
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    
    # 検索パラメータ（キーワードと取得件数）
    params = {
        "query": keyword,
        "per_page": 30,  # 1ページあたりのMAX件数
        "page": page     # 指定されたページ番号
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # 検索結果から画像のURL（標準サイズ）だけを抽出
        image_urls = []
        for item in data.get("results", []):
            image_urls.append(item["urls"]["regular"])
                
        return {"status": "success", "images": image_urls}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}