import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

TOKEN = os.environ.get('BOT_TOKEN', '')
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Cache for track links
link_cache = {}
cache_id = 0

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🎧 Привет! Пришли название песни, и я найду её.")

@dp.message()
async def search(message: types.Message):
    global cache_id
    wait_msg = await message.answer("🔍 Ищу...")

    ydl_opts = {'quiet': True, 'default_search': 'scsearch5', 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"scsearch5:{message.text}", download=False)
            results = info.get('entries', [])
        except Exception:
            results = []

    await wait_msg.delete()
    if not results:
        await message.answer("❌ Ничего не найдено. Попробуй другое название.")
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
        await call.answer("❌ Трек устарел, выполните поиск заново.")
        return

    wait_msg = await call.message.answer("⏳ Скачиваю и создаю плеер...")
    filename = f"music_{call.from_user.id}.mp3"

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

        await call.message.answer_audio(
            audio=types.FSInputFile(filename),
            title=title,
            performer=performer
        )
        await wait_msg.delete()
    except Exception:
        await call.message.answer("❌ Ошибка: не удалось скачать трек (возможно, автор ограничил доступ).")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
    await call.answer()

# ── Health-check HTTP server ────────────────────────────────────────────────

async def health(request):
    return web.Response(text="OK")

async def run_health_server():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health server listening on 0.0.0.0:{port}", flush=True)
    # Keep running forever
    while True:
        await asyncio.sleep(3600)

async def run_bot():
    print("Бот запущен...", flush=True)
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(
        run_health_server(),
        run_bot(),
    )

if __name__ == '__main__':
    asyncio.run(main())
