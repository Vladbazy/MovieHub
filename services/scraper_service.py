import requests
from config import OMDB_API_KEY

def get_movie_from_api(title: str) -> dict:
    """Получает данные о фильме через REST API (JSON)"""
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}&plot=short"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data
        return {"Error": data.get("Error", "Фильм не найден")}
    except requests.exceptions.RequestException as e:
        return {"Error": f"Ошибка сети: {str(e)}"}