import asyncio
import os
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Получаем токен из переменных окружения Render
# Было:
# TOKEN = os.getenv('TOKEN')

# Сделай так (вставь свой токен):
TOKEN = os.getenv('TOKEN', '8761549497:AAEtl7E_mjskOON32rJq4Yb7FAT_oF0h1jI')
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настройки yt_dlp для стабильной работы
YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
}

async def health_check(request):
    return web.Response(text="Bot is alive")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🎧 Привет! Пришли название трека, я его найду.")

@dp.message()
async def download_music(message: types.Message):
    status_msg = await message.answer("🔍 Ищу и скачиваю...")
    file_name = f"music_{message.from_user.id}.mp3"
    
    try:
        ydl_opts = YDL_OPTS.copy()
        ydl_opts['outtmpl'] = file_name
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{message.text}", download=True)
            video = info['entries'][0]
            real_filename = ydl.prepare_filename(video)
        
        audio = types.FSInputFile(real_filename)
        await message.answer_audio(audio, title=video.get('title'), performer=video.get('uploader'))
        
        # Удаляем файл после отправки
        if os.path.exists(real_filename):
            os.remove(real_filename)
        await status_msg.delete()
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: попробуй другое название.")
        print(f"Error: {e}")

async def main():
    # Запускаем веб-сервер для прохождения проверки порта
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Принудительно задаем порт 8080
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Server started on port {port}")
    
    # Запускаем бота
    print("Bot polling started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())