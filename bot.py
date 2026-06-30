import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from google import genai
from google.genai import types as genai_types

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOKEN = os.getenv("BOT_TOKEN")
AI_KEY = os.getenv("AI_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()
ai_client = genai.Client(api_key=AI_KEY)

user_modes = {}

def get_keyboard(user_id: int):
    is_roast_on = user_modes.get(user_id, False)
    builder = ReplyKeyboardBuilder()
    
    if is_roast_on:
        builder.button(text="🔥 Режим: Жесткие подколы [ВКЛ]")
    else:
        builder.button(text="😴 Режим: Жесткие подколы [ВЫКЛ]")
        
    return builder.as_markup(resize_keyboard=True)

async def generate_ai_response(prompt: str, is_roast_on: bool, image_bytes: bytes = None) -> str:
    system_instruction = (
        "Ты — Q cold. Гениальный, харизматичный, остроумный и циничный ИИ. "
        "Твой стиль — это смесь дерзкого стендап-комика и уверенного в себе пранкера. "
        "Ты придумываешь ГЕНИАЛЬНЫЕ, неожиданные шутки и панчи строго к месту. "
        "Ты ОБЯЗАН договаривать свои фразы до конца. Никогда не обрывай предложение на середине! "
        "Используй сочный, отборный мат для удаления банальности и усиления эффекта. "
        "Отвечай коротко, но полноценно, обязательно заканчивай мысль точкой или восклицательным знаком. "
        "Если тебе скидывают фото — подмечаошь глупую деталь и высмеиваешь её."
    )
    
    if is_roast_on:
        system_instruction += (
            " ВНИМАНИЕ: Включен режим максимального уничтожения! "
            "Твоя задача — морально разнести автора в пух и прах. "
            "Найди в его словах уязвимое место и вышути его лично. Отвечай жестко и до конца!"
        )

    try:
        contents = [prompt] if prompt else []
        if image_bytes:
            contents.append(
                genai_types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                )
            )
            
        config = genai_types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.0,
        )
        config.max_output_tokens = 600
            
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config
        )
        return response.text if response.text else "Бля, даже у меня слов нет на этот бред."
    except Exception as e:
        logging.error(f"Ошибка API: {e}")
        return "Сука, у меня мозги закипели от твоего бреда. Давай заново."

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_modes[message.from_user.id] = False
    await message.reply(
        "Я Q cold. Че вылупился? Выдавай свою гениальную мысль или кидай фотку, ща буду пояснять за жизнь.\n\n"
        "👇 Кнопка внизу — если хочешь, чтобы я включил режим тотального разъёба лично тебя.",
        reply_markup=get_keyboard(message.from_user.id)
    )

@dp.message(F.text.contains("Режим: Жесткие подколы"))
async def toggle_roast_mode(message: types.Message):
    user_id = message.from_user.id
    current_status = user_modes.get(user_id, False)
    user_modes[user_id] = not current_status
    
    if user_modes[user_id]:
        await message.reply("🔥 Так, сука, ты сам напросился. Режим личного разьёба включен. Пиши теперь аккуратно, бля!", reply_markup=get_keyboard(user_id))
    else:
        await message.reply("😴 Ладно, живи пока, выключил. Общаемся на чилле, но без соплей.", reply_markup=get_keyboard(user_id))

@dp.message(F.text)
async def handle_text(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    is_roast_on = user_modes.get(message.from_user.id, False)
    reply_text = await generate_ai_response(prompt=message.text, is_roast_on=is_roast_on)
    await message.reply(reply_text, reply_markup=get_keyboard(message.from_user.id))

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    is_roast_on = user_modes.get(message.from_user.id, False)
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        caption = message.caption if message.caption else "Поясни за фотку."
        reply_text = await generate_ai_response(prompt=caption, is_roast_on=is_roast_on, image_bytes=file_bytes.getvalue())
        await message.reply(reply_text, reply_markup=get_keyboard(message.from_user.id))
    except Exception as e:
        logging.error(f"Ошибка фото: {e}")
        await message.reply("Че ты мне суешь? Фотка битая, переделывай.")

async def main():
    logging.info("Бот Q cold запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
