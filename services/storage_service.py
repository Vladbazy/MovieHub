import json
import os

def save_movie_to_file(user_id: int, movie_data: dict) -> bool:
    """Сохраняет фильм в локальный JSON-файл пользователя"""
    filename = f"favorites_{user_id}.json"
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                favorites = json.load(f)
            except json.JSONDecodeError:
                favorites = []
    else:
        favorites = []
        
    if not any(m.get('Title') == movie_data.get('Title') for m in favorites):
        favorites.append({
            "Title": movie_data.get("Title"),
            "Year": movie_data.get("Year"),
            "imdbRating": movie_data.get("imdbRating")
        })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, indent=4, ensure_ascii=False)
        return True
    return False

def load_favorites(user_id: int) -> list:
    """Загружает список избранных фильмов пользователя"""
    filename = f"favorites_{user_id}.json"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []