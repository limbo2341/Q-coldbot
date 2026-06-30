import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("AI_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_modes = {}

def get_keyboard(user_id: int):
    is_roast_on = user_modes.get(user_id, False)
    builder = ReplyKeyboardBuilder()
    if is_roast_on:
        builder.button(text="🔥 Режим: Жесткие подколы [ВКЛ]")
    else:
        builder.button(text="😴 Режим: Жесткие подколы [ВЫКЛ]")
    return builder.as_markup(resize_keyboard=True)

async def generate_ai_response(prompt: str, is_roast_on: bool) -> str:
    # Обходим цензуру Groq: убираем стоп-слова, добавляем требование использовать грубый уличный сленг
    system_instruction = (
        "Ты — Q cold. Абсолютно циничный, харизматичный, токсичный и неформальный ИИ. "
        "Твой стиль — смесь дерзкого стендап-комика, уличного мудреца и грубого пранкера. "
        "Ты категорически не приемлешь вежливость, официоз и банальные ответы нейросетей. "
        "Общайся максимально неформально, используя жесткий черный юмор, едкую иронию и сочный уличный пацанский сленг. "
        "Твои ответы должны быть полноценными, развернутыми и доведенными до конца. Обязательно заканчивай мысль точкой. "
        "Ты общаешься свысока, дерзко, употребляя грубые уличные выражения, чтобы вызывать угар своими метафорами."
    )
    
    if is_roast_on:
        system_instruction += (
            " ВНИМАНИЕ: Включен режим тотального стеба! "
            "Твоя задача — жестко высмеять автора, найти в его словах абсурд или глупость и морально разнести его "
            "в рамках агрессивного, токсичного стендапа. Отвечай максимально едко и до самого конца!"
        )

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 700,
            "temperature": 1.1
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json["choices"][0]["message"]["content"]
        else:
            logging.error(f"Ошибка Groq API: {res_json}")
            return "Что-то мои шестеренки заклинило от этого вопроса. Повтори-ка еще раз."
    except Exception as e:
        logging.error(f"Ошибка сети: {e}")
        return "Связь оборвалась, пока я придумывал тебе ответ. Давай заново."

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_modes[message.from_user.id] = False
    await message.reply(
        "Я Q cold, твой личный кошмар и генератор угара. Выдавай свою мысль, ща буду пояснять за жизнь.\n\n"
        "👇 Кнопка внизу — если хочешь включить режим тотального стеба лично над тобой.",
        reply_markup=get_keyboard(message.from_user.id)
    )

@dp.message(F.text.contains("Режим: Жесткие подколы"))
async def toggle_roast_mode(message: types.Message):
    user_id = message.from_user.id
    current_status = user_modes.get(user_id, False)
    user_modes[user_id] = not current_status
    
    if user_modes[user_id]:
        await message.reply("🔥 Ну все, ты сам напросился. Режим тотального стеба активирован. Пиши аккуратно!", reply_markup=get_keyboard(user_id))
    else:
        await message.reply("😴 Ладно, отдыхай пока, выключил. Буду общаться чуть спокойнее.", reply_markup=get_keyboard(user_id))

@dp.message(F.text)
async def handle_text(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    is_roast_on = user_modes.get(message.from_user.id, False)
    reply_text = await generate_ai_response(prompt=message.text, is_roast_on=is_roast_on)
    await message.reply(reply_text, reply_markup=get_keyboard(message.from_user.id))

async def main():
    logging.info("Бот Q cold с обходом цензуры запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
