from services.storage_service import load_favorites

def calculate_user_stats(user_id: int) -> str:
    """Алгоритмически обрабатывает сохраненные данные"""
    favorites = load_favorites(user_id)
    
    if not favorites:
        return "У вас пока нет сохраненных фильмов для аналитики."
        
    total_movies = len(favorites)
    valid_ratings = [float(m['imdbRating']) for m in favorites if m['imdbRating'] != 'N/A']
    
    if valid_ratings:
        avg_rating = sum(valid_ratings) / len(valid_ratings)
        return (f"📊 Ваша статистика:\n"
                f"Всего фильмов в избранном: {total_movies}\n"
                f"Средний рейтинг IMDb: {avg_rating:.1f}/10")
    else:
        return f"Всего фильмов в избранном: {total_movies}. Рейтинги не указаны."