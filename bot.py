import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# Вставьте ваш токен
TOKEN = '8761549497:AAEtl7E_mjskOON32rJq4Yb7FAT_oF0h1jI'
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Кэш для хранения ссылок на треки SoundCloud
link_cache = {}
cache_id = 0

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎧 Привет! Пришли название песни, и я найду её.")
  
@dp.message()
async def search(message: types.Message):
    global cache_id
    wait_msg = await message.answer("🔍 Ищу...")
    
    # Поиск именно по SoundCloud
    ydl_opts = {'quiet': True, 'default_search': 'scsearch5', 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"scsearch5:{message.text}", download=False)
            results = info.get('entries', [])
        except:
            results = []

    await wait_msg.delete()
    if not results:
        await message.answer("❌ Ничего не найдено. Попробуй другое название.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for s in results:
        cache_id += 1
        link_cache[str(cache_id)] = s['webpage_url']
        
        # Короткий текст кнопки (автор - название)
        name = f"{s.get('uploader', 'Artist')} - {s.get('title', 'Track')}"[:60]
        kb.inline_keyboard.append([InlineKeyboardButton(text=name, callback_data=f"play_{cache_id}")])
    
    await message.answer("Выберите трек:", reply_markup=kb)

@dp.callback_query(F.data.startswith("play_"))
async def play(call: types.CallbackQuery):
    c_id = call.data.split('_')[1]
    url = link_cache.get(c_id)
    
    if not url:
        await call.answer("❌ Трек устарел, выполните поиск заново.")
        return

    wait_msg = await call.message.answer("⏳ Скачиваю и создаю плеер...")
    filename = f"music_{call.from_user.id}.mp3"
    
    # Настройки для SoundCloud
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Music')
            performer = info.get('uploader', 'Artist')
        
        # Отправка аудио — это превращает файл в плеер Telegram
        await call.message.answer_audio(
            audio=types.FSInputFile(filename),
            title=title,
            performer=performer
        )
        await wait_msg.delete()
    except Exception as e:
        await call.message.answer("❌ Ошибка: не удалось скачать трек (возможно, автор ограничил доступ).")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
    await call.answer()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())