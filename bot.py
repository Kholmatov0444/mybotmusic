import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
from aiohttp import web

# Получаем токен из настроек Render, если он там есть
# Если нет — используем токен, прописанный здесь (для тестов)
TOKEN = os.getenv('TOKEN', '8761549497:AAEtl7E_mjskOON32rJq4Yb7FAT_oF0h1jI')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Файл для учета пользователей
USERS_FILE = "users.txt"
link_cache = {}
cache_id = 0

def add_user(user_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: f.write(str(user_id) + "\n")
    else:
        with open(USERS_FILE, "r") as f: users = f.read().splitlines()
        if str(user_id) not in users:
            with open(USERS_FILE, "a") as f: f.write(str(user_id) + "\n")

def get_user_count():
    if not os.path.exists(USERS_FILE): return 0
    with open(USERS_FILE, "r") as f: return len(f.read().splitlines())

# Веб-сервер для того, чтобы Render не отключал бота
async def handle(request):
    return web.Response(text="Bot is active")

@dp.message(Command("start"))
async def start(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(f"🎧 Привет! Пришли название песни, и я найду её.\n📊 Всего пользователей бота: {get_user_count()}")

@dp.message()
async def search(message: types.Message):
    global cache_id
    wait_msg = await message.answer("🔍 Ищу...")
    
    # Поиск по SoundCloud
    ydl_opts = {'quiet': True, 'default_search': 'ytsearch5', 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"scsearch5:{message.text}", download=False)
            results = info.get('entries', [])
        except Exception:
            results = []
    
    await wait_msg.delete()
    if not results:
        await message.answer("❌ Ничего не найдено.")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s in results:
        cache_id += 1
        link_cache[str(cache_id)] = s['webpage_url']
        name = f"{s.get('uploader', 'Artist')} - {s.get('title', 'Track')}"[:60]
        kb.inline_keyboard.append([InlineKeyboardButton(text=name, callback_data=f"play_{cache_id}")])
    
    await message.answer("Выберите трек:", reply_markup=kb)

@dp.callback_query(F.data.startswith("play_"))
async def play(call: types.CallbackQuery):
    c_id = call.data.split('_')[1]
    url = link_cache.get(c_id)
    
    if not url:
        await call.answer("❌ Трек устарел. Попробуйте найти снова.")
        return

    wait_msg = await call.message.answer("⏳ Скачиваю аудио, пожалуйста, подождите...")
    filename = f"music_{call.from_user.id}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename,
        'quiet': False,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            real_filename = ydl.prepare_filename(info)
            
        await call.message.answer_audio(
            audio=types.FSInputFile(real_filename),
            title=info.get('title', 'Music'),
            performer=info.get('uploader', 'Artist')
        )
        await wait_msg.delete()
        
        # Удаляем файл после отправки
        if os.path.exists(real_filename):
            os.remove(real_filename)
            
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        await call.message.answer("❌ Не удалось скачать этот трек. Возможно, он защищен или недоступен.")
    
    await call.answer()

async def main():
    # Запуск веб-сервера (обязательно для Render)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Бот успешно запущен на порту {port}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())