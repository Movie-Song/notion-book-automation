import os
import requests
import datetime
from notion_client import Client

# 1. 환경 변수에서 Notion 및 네이버 API 키를 불러옵니다.
#    GitHub Actions의 Secrets에 등록된 값과 일치해야 합니다.
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")
# ⭐️ 이 부분에 여러분의 Notion DB ID를 직접 넣어주세요.
DATABASE_ID = "여러분의_Notion_DB_ID를_여기에_넣으세요"

# 2. Notion 클라이언트를 초기화합니다.
notion = Client(auth=NOTION_TOKEN)

def get_empty_book_pages():
    """
    Notion DB에서 'autour' 속성이 비어있는 페이지들을 쿼리합니다.
    """
    try:
        results = notion.databases.query(
            database_id=DATABASE_ID,
            filter={
                "property": "autour",
                "rich_text": {
                    "is_empty": True
                }
            }
        ).get("results")
        return results
    except Exception as e:
        print(f"Notion DB를 쿼리하는 중 오류가 발생했습니다: {e}")
        return []

def search_naver_book(query):
    """
    네이버 도서 API를 사용하여 책 정보를 검색합니다.
    """
    url = "https://openapi.naver.com/v1/search/book.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": 1} # 검색 결과 1개만 가져오기
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # HTTP 오류가 발생하면 예외를 발생시킵니다.
        return response.json().get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"네이버 API 요청 중 오류가 발생했습니다: {e}")
        return []

def update_notion_page(page_id, book_data):
    """
    네이버 API 검색 결과로 Notion 페이지 속성을 업데이트합니다.
    """
    try:
        # 네이버 API에서 받은 'price'와 'page'는 문자열이므로 정수로 변환합니다.
        list_price = int(book_data.get('price', 0))
        page_count = int(book_data.get('page', 0))

        notion.pages.update(
            page_id=page_id,
            properties={
                "autour": {
                    "rich_text": [{"text": {"content": book_data.get('author', '')}}]
                },
                "publisher": {
                    "rich_text": [{"text": {"content": book_data.get('publisher', '')}}]
                },
                "list price": {
                    "number": list_price
                },
                "page": {
                    "number": page_count
                },
                "cover": {
                    "files": [{"name": "cover.jpg", "external": {"url": book_data.get('image', '')}}]
                }
            }
        )
        print(f"✔️ 페이지 업데이트 성공: {book_data.get('title')}")
    except Exception as e:
        print(f"페이지 업데이트 중 오류 발생: {e}")

def main():
    """
    메인 실행 함수입니다.
    """
    pages_to_update = get_empty_book_pages()

    if not pages_to_update:
        print("💡 업데이트할 페이지가 없습니다.")
        return

    for page in pages_to_update:
        # Notion 'name' 속성에서 페이지 제목을 추출합니다.
        # Notion API의 title 속성은 리스트 형태이므로 첫 번째 요소를 가져옵니다.
        page_title = page['properties']['name']['title'][0]['plain_text']
        print(f"📖 '{page_title}' 페이지를 확인합니다...")

        # 네이버 API로 책을 검색합니다.
        book_items = search_naver_book(page_title)

        if book_items:
            # 검색 결과 중 가장 첫 번째 결과를 사용합니다.
            book_data = book_items[0]
            update_notion_page(page['id'], book_data)
        else:
            print(f"❌ '{page_title}'에 대한 검색 결과를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
