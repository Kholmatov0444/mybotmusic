import os
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# ПРЯМОЙ ВВОД ТОКЕНА (Удаляем зависимость от os.getenv для теста)
TOKEN = "8761549497:AAEtl7E_mjskOON32rJq4Yb7FAT_oF0h1jI"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- ЛОГИКА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🎧 Привет! Пришли название трека.")

@dp.message()
async def download_music(message: types.Message):
    status_msg = await message.answer("🔍 Ищу...")
    try:
        ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{message.text}", download=True)
            video = info['entries'][0]
            filename = ydl.prepare_filename(video)
        
        await message.answer_audio(types.FSInputFile(filename))
        if os.path.exists(filename): os.remove(filename)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ Ошибка.")

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())