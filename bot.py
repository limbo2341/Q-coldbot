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
    system_instruction = (
        "Ты — Q cold. Гениальный, харизматичный, остроумный и циничный ИИ. "
        "Твой стиль — смесь дерзкого стендап-комика и уверенного в себе пранкера. "
        "Ты придумываешь ГЕНИАЛЬНЫЕ, неожиданные шутки и панчи строго к месту. "
        "Ты ОБЯЗАН договаривать свои фразы до конца. Никогда не обрывай предложение на середине! "
        "Используй сочный, отборный мат для усиления эффекта. Отвечай коротко, но полноценно, обязательно заканчивай мысль точкой или восклицательным знаком."
    )
    
    if is_roast_on:
        system_instruction += (
            " ВНИМАНИЕ: Включен режим максимального уничтожения! "
            "Твоя задача — морально разнести автора в пух и прах. "
            "Найди в его словах уязвимое место и вышути его лично. Отвечай жестко и до конца!"
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
            "max_tokens": 600,
            "temperature": 1.0
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        res_json = response.json()
        
        if response.status_code == 200:
            return res_json["choices"][0]["message"]["content"]
        else:
            logging.error(f"Ошибка Groq API: {res_json}")
            return "Сука, у меня мозги закипели. Давай заново."
    except Exception as e:
        logging.error(f"Ошибка сети: {e}")
        return "Бля, связь оборвалась. Повтори еще раз."

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_modes[message.from_user.id] = False
    await message.reply(
        "Я Q cold, но теперь на стероидах от Groq. Выдавай свою гениальную мысль, ща буду пояснять за жизнь.\n\n"
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

async def main():
    logging.info("Бот Q cold на Groq API запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
