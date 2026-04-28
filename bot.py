import asyncio
import base64
import logging
import os
import re
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemma-3-27b-it") # Вказуємо Gemma як стандартну модель

allowed_ids_str = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS = [
    int(user_id.strip())
    for user_id in allowed_ids_str.split(",")
    if user_id.strip().isdigit()
]

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

ALLOWED_USERS_FILTER = F.from_user.id.in_(ALLOWED_USER_IDS)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
nv_client = AsyncOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
    timeout=300.0, # Обмеження таймауту в 5 хвилин для довгих генерацій
    max_retries=0
)

# --- Функція для статусного рядка (Progress Bar) ---       
async def update_progress_bar(status_msg: Message):
    progress_states = [15, 30, 45, 60, 75, 88, 95, 99]
    try:
        for progress in progress_states:
            bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))    
            await status_msg.edit_text(f"⏳ Готую відповідь...\n[{bar}] {progress}%")
            await asyncio.sleep(1.5)

        # Симуляція очікування на 99%
        dots = 1
        while True:
            bar = "█" * 9 + "▓"
            await status_msg.edit_text(f"⏳ Готую відповідь...\n[{bar}] 99%" + "." * dots)
            dots = (dots % 3) + 1
            await asyncio.sleep(1.5)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Помилка оновлення статус-бару: {e}")

async def keep_typing(chat_id: int):
    try:
        while True:
            await bot.send_chat_action(chat_id, 'typing')
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.error(f"Помилка typing action: {e}")


@dp.message(~ALLOWED_USERS_FILTER)
async def access_denied(message: Message):
    await message.answer(
        f"⛔️ Доступ заборонено.\n"
        f"Ваш Telegram ID: `{message.from_user.id}`\n"
        f"Зверніться до адміністратора.",
        parse_mode="Markdown"
    )


@dp.message(CommandStart(), ALLOWED_USERS_FILTER)
async def cmd_start(message: Message):
    await message.answer(
        f"🤖 Привіт, *{message.from_user.first_name}*!\n\n"
        f"Я твій особистий AI-асистент на базі розумної моделі від NVIDIA.\n"
        "🟢 *Мої можливості:*\n"
        "• Змістовно відповідаю на складні запитання.\n"
        "• Пишу та форматую програмний код.\n"
        "• Працюю із зображеннями (просто прикріпи фотографію).\n\n"
        "⚠️ *Важливо:* Я відповідаю на кожне повідомлення як на нове і **не запам'ятовую** історію розмови. Будь ласка, формулюй свої питання повно і чітко з першого разу.\n\n"
        "📝 _Напиши мені питання, і ми розпочнемо!_",
        parse_mode="Markdown"
    )

@dp.message(F.text, ALLOWED_USERS_FILTER)
async def handle_text(message: Message):
    status_deleted = False
    typing_task = asyncio.create_task(keep_typing(message.chat.id))
    status_msg = await message.answer("⏳ Обробка запиту...\n[░░░░░░░░░░] 0%")
    
    progress_task = asyncio.create_task(update_progress_bar(status_msg))
    
    try:
        response = await nv_client.chat.completions.create(
            messages=[{"role": "user", "content": message.text}],
            model=MODEL_NAME,
            max_tokens=4000, # Оптимальний ліміт токенів для стабільності з'єднання (запобігає Error 504)
            temperature=0.7,
        )
        
        reply_text = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason
        
        if not reply_text:
            if finish_reason == "length":
                reply_text = "⚠️ Модель згенерувала максимум тексту (для запобігання обриву з'єднання). Напишіть 'продовжуй', щоб побачити решту."
            else:
                reply_text = "⚠️ Модель нічого не відповіла."
        
        # Зупинка статусного-бару і показ 100% при успіху
        progress_task.cancel()
        await status_msg.edit_text("✅ Відповідь згенерована!\n[██████████] 100%")
        await asyncio.sleep(0.5)
        await status_msg.delete()
        status_deleted = True
        
        # Конвертація надійного HTML для Telegram
        html_text = reply_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_text = re.sub(r'```[\w\-]*\n(.*?)```', r'<pre><code>\1</code></pre>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'`(.*?)`', r'<code>\1</code>', html_text)
        html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_text)
        
        # Запобігання розривам блоків при довгих текстах Telegram (4000 знаків)
        chunks = []
        current_chunk = ""
        in_pre = False
        
        for line in html_text.split("\n"):
            if "<pre><code>" in line: in_pre = True
            if "</code></pre>" in line: in_pre = False
                
            if len(current_chunk) + len(line) + 1 > 4000:
                if in_pre and "</code></pre>" not in line:
                    current_chunk += "\n</code></pre>"
                    chunks.append(current_chunk)
                    current_chunk = "<pre><code>\n" + line
                else:
                    chunks.append(current_chunk)
                    current_chunk = line
            else:
                current_chunk += ("\n" + line) if current_chunk else line
                
        if current_chunk:
            chunks.append(current_chunk)
            
        for chunk in chunks:
            try:
                await message.answer(chunk, parse_mode="HTML")
            except Exception as parse_error:
                logging.warning(f"HTML Parse error: {parse_error}")
                # Fallback: прибираємо теги
                clean = chunk.replace("<b>","").replace("</b>","").replace("<pre><code>","").replace("</code></pre>","").replace("<code>","").replace("</code>","").replace("<i>","").replace("</i>","")
                await message.answer(clean)
        
    except Exception as e:
        logging.error(f"Text API Error: {e}")
        if status_deleted:
            await message.answer(f"❌ Помилка надсилання: {e}")
        else:
            await status_msg.edit_text(f"❌ Помилка сервера (можливо тайм-аут API) спробуйте ще раз: {e}")
    finally:
        progress_task.cancel()
        typing_task.cancel()


@dp.message(F.photo, ALLOWED_USERS_FILTER)
async def handle_photo(message: Message):
    status_deleted = False
    typing_task = asyncio.create_task(keep_typing(message.chat.id))
    
    # Отримуємо фото з найбільшою роздільною здатністю (останнє в масиві)
    photo = message.photo[-1]
    
    status_msg = await message.answer("⏳ Аналізую фото...\n[░░░░░░░░░░] 0%")
    progress_task = asyncio.create_task(update_progress_bar(status_msg))
    
    try:
        # Завантажуємо файл фотографії
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        # Конвертуємо у Base64
        image_data = downloaded_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Визначаємо текст запиту (caption або стандартний)
        prompt_text = message.caption if message.caption else "Що ти бачиш на цьому зображенні?"
        
        # Формуємо повідомлення у форматі Vision
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                }
            ]
        }]
        
        response = await nv_client.chat.completions.create(
            messages=messages,
            model=MODEL_NAME, 
            max_tokens=1024,
            temperature=0.7,
        )
        
        reply_text = response.choices[0].message.content
        if not reply_text:
            reply_text = "⚠️ Модель не повернула тексту для цього зображення."
            
        progress_task.cancel()
        await status_msg.edit_text("✅ Фото проаналізовано!\n[██████████] 100%")
        await asyncio.sleep(0.5)
        await status_msg.delete()
        status_deleted = True

        html_text = reply_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_text = re.sub(r'```[\w\-]*\n(.*?)```', r'<pre><code>\1</code></pre>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'`(.*?)`', r'<code>\1</code>', html_text)
        html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', html_text, flags=re.DOTALL)
        html_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html_text)

        try:
            await message.answer(html_text, parse_mode="HTML")
        except Exception as e:
            logging.warning(f"Parse error in photo handler, fallback to plain text: {e}")
            clean_chunk = html_text.replace("<b>", "").replace("</b>", "").replace("<pre><code>", "").replace("</code></pre>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", "")
            await message.answer(clean_chunk)

    except Exception as e:
        logging.error(f"Vision API Error: {e}")
        if status_deleted:
            await message.answer(f"❌ Помилка надсилання: {e}")
        else:
            await status_msg.edit_text(
                f"❌ Помилка обробки фото (можливо модель не підтримує Vision): {e}"
            )
    finally:
        progress_task.cancel()
        typing_task.cancel()

@dp.message(ALLOWED_USERS_FILTER)
async def handle_unsupported(message: Message):
    await message.answer(
        "⚠️ Я поки розумію лише текстові повідомлення та фотографії. "
        "Будь ласка, надішліть інший формат."
    )

async def main():
    try:
        logging.info("Starting bot...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
