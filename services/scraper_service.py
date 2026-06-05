import requests
from bs4 import BeautifulSoup

def get_top_movies_from_html() -> list:
    """Получает топ фильмов методом парсинга HTML-кода страницы"""
    url = "https://www.imdb.com/chart/top/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        movies = []
        titles = soup.select('h3.ipc-title__text')
        for i, title in enumerate(titles[:5]):
            movies.append(f"{i+1}. {title.get_text()}")
            
        return movies if movies else ["Не удалось спарсить данные"]
    except Exception as e:
        return [f"Ошибка при скрапинге: {str(e)}"]