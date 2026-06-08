import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import BOT_TOKEN
from utils.logger import get_user_logger
from services.api_service import get_movie_from_api
from services.storage_service import save_movie_to_file
from services.analytics import calculate_user_stats
from services.movie_service import MovieService

# Глобальные переменные
user_last_movie = {}
aio_session: aiohttp.ClientSession = None
movie_service: MovieService = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    logger.info("Пользователь запустил бота")
    
    keyboard = [
        [InlineKeyboardButton("🎬 Найти фильм", callback_data='cmd_find')],
        [InlineKeyboardButton("🔥 Топ-5 фильмов", callback_data='cmd_top')],
        [InlineKeyboardButton("📊 Моя статистика", callback_data='cmd_stats')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Добро пожаловать в MovieHub Bot!\nВыберите действие:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    logger = get_user_logger(user_id)

    if data == 'cmd_find':
        await query.edit_message_text("📝 Введите название фильма (на английском или русском), например: Matrix или Побег из Шоушенка")
        context.user_data['awaiting_title'] = True

    elif data == 'cmd_top':
        logger.info("Запрос топ-5 фильмов")
        await query.edit_message_text("⏳ Парсю топ фильмов...")
        
        top_movies = await movie_service.get_top_movies()
        logger.info(f"Результат: {top_movies}")
        
        result = "🏆 **Топ-5 фильмов:**\n\n" + "\n".join(top_movies)
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='cmd_menu')]]
        await query.edit_message_text(result, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'cmd_save':
        logger.info("Попытка сохранения через кнопку")
        movie = user_last_movie.get(user_id)
        if not movie:
            await query.edit_message_text("❌ Сначала найдите фильм через 'Найти фильм'")
            return
        
        success = save_movie_to_file(user_id, movie)
        logger.info(f"Сохранение '{movie.get('Title')}': {success}")
        
        msg = f"✅ '{movie.get('Title')}' сохранен!" if success else "⚠️ Фильм уже в избранном."
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='cmd_menu')]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'cmd_stats':
        logger.info("Запрос статистики через кнопку")
        stats = calculate_user_stats(user_id)
        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='cmd_menu')]]
        await query.edit_message_text(stats, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'cmd_menu':
        keyboard = [
            [InlineKeyboardButton("🎬 Найти фильм", callback_data='cmd_find')],
            [InlineKeyboardButton("🔥 Топ-5 фильмов", callback_data='cmd_top')],
            [InlineKeyboardButton("📊 Моя статистика", callback_data='cmd_stats')],
        ]
        await query.edit_message_text("📋 Главное меню:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (названия фильма)"""
    user_id = update.effective_user.id
    logger = get_user_logger(user_id)
    
    if context.user_data.get('awaiting_title'):
        title = update.message.text
        logger.info(f"Поиск фильма (через текст): {title}")
        
        await update.message.reply_text("⏳ Ищу фильм через API...")
        movie_data = get_movie_from_api(title)
        logger.info(f"Ответ API: {movie_data}")
        
        context.user_data['awaiting_title'] = False
        
        if "Error" in movie_data:
            await update.message.reply_text(f"❌ {movie_data['Error']}")
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data='cmd_menu')]]
            await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            user_last_movie[user_id] = movie_data
            
            # Формируем красивое сообщение на русском
            poster_url = f"https://image.tmdb.org/t/p/w500{movie_data.get('Poster', '')}" if movie_data.get('Poster') else ""
            
            response = (
                f"🎬 **{movie_data.get('Title')}** ({movie_data.get('Year')})\n\n"
                f"⭐ **Рейтинг TMDB:** {movie_data.get('imdbRating')}/10\n"
                f"🎭 **Жанр:** {movie_data.get('Genre')}\n\n"
                f"📝 **Описание:**\n{movie_data.get('Plot')}"
            )
            
            # Если есть постер — отправляем с картинкой
            if poster_url:
                try:
                    await update.message.reply_photo(
                        photo=poster_url,
                        caption=response,
                        parse_mode='Markdown'
                    )
                except:
                    await update.message.reply_text(response, parse_mode='Markdown')
            else:
                await update.message.reply_text(response, parse_mode='Markdown')
            
            # Кнопки сохранения
            keyboard = [
                [InlineKeyboardButton("💾 Сохранить в избранное", callback_data='cmd_save')],
                [InlineKeyboardButton("🔙 Главное меню", callback_data='cmd_menu')]
            ]
            await update.message.reply_text("Что делать дальше?", reply_markup=InlineKeyboardMarkup(keyboard))

async def post_init(application: Application):
    """Инициализирует aiohttp-сессию после запуска event loop"""
    global aio_session, movie_service
    aio_session = aiohttp.ClientSession()
    movie_service = MovieService(aio_session)
    print("✅ Aiohttp-сессия и MovieService инициализированы")

async def post_shutdown(application: Application):
    """Закрывает aiohttp-сессию при остановке бота"""
    global aio_session
    if aio_session and not aio_session.closed:
        await aio_session.close()
        print("✅ Aiohttp-сессия закрыта")

def main():
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    print("🤖 Бот с парсером фильмов запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()