from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN
from utils.logger import get_user_logger
from services.api_service import get_movie_from_api
from services.scraper_service import get_top_movies_from_html
from services.storage_service import save_movie_to_file
from services.analytics import calculate_user_stats

user_last_movie = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    logger.info("Пользователь запустил бота")
    
    help_text = (
        "🎬 Добро пожаловать в MovieHub Bot!\n\n"
        "Команды:\n"
        "/find <название> - найти фильм (на англ., напр. /find Matrix)\n"
        "/top - топ-5 фильмов (парсинг HTML)\n"
        "/save - сохранить последний найденный фильм\n"
        "/stats - аналитика по сохраненным фильмам"
    )
    await update.message.reply_text(help_text)

async def find_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    
    if not context.args:
        await update.message.reply_text("Укажите название: /find Matrix")
        return
        
    title = " ".join(context.args)
    logger.info(f"Поиск фильма: {title}")
    await update.message.reply_text("⏳ Ищу фильм...")
    
    movie_data = get_movie_from_api(title)
    logger.info(f"Ответ API: {movie_data}")
    
    if "Error" in movie_data:
        await update.message.reply_text(f"❌ {movie_data['Error']}")
    else:
        user_last_movie[user_id] = movie_data
        response = (
            f"🎬 **{movie_data.get('Title')}** ({movie_data.get('Year')})\n"
            f"⭐ IMDb: {movie_data.get('imdbRating')}\n"
            f"🎭 Жанр: {movie_data.get('Genre')}\n"
            f"📝 {movie_data.get('Plot')}\n\n"
            f"Используй /save для сохранения."
        )
        await update.message.reply_text(response, parse_mode='Markdown')

async def get_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    logger.info("Запрос топ-фильмов")
    
    await update.message.reply_text("⏳ Парсю IMDb...")
    top_movies = get_top_movies_from_html()
    logger.info(f"Результат: {top_movies}")
    
    result = "🏆 Топ-5 фильмов:\n" + "\n".join(top_movies)
    await update.message.reply_text(result)

async def save_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    
    movie = user_last_movie.get(user_id)
    if not movie:
        logger.warning("Попытка сохранить без поиска")
        await update.message.reply_text("❌ Сначала найди фильм через /find")
        return
        
    success = save_movie_to_file(user_id, movie)
    logger.info(f"Сохранение '{movie.get('Title')}': {success}")
    
    if success:
        await update.message.reply_text(f"✅ '{movie.get('Title')}' сохранен!")
    else:
        await update.message.reply_text("⚠️ Фильм уже в избранном.")

async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    logger.info("Запрос статистики")
    
    stats = calculate_user_stats(user_id)
    await update.message.reply_text(stats)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("find", find_movie))
    application.add_handler(CommandHandler("top", get_top))
    application.add_handler(CommandHandler("save", save_movie))
    application.add_handler(CommandHandler("stats", get_stats))
    
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()