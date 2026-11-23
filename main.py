
import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN ёфт нашуд!")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton("⚽ ТАМОШОИ ПАХШҲО", callback_data="live"),
        InlineKeyboardButton("📅 ҶАДВАЛИ БОЗИҲО", callback_data="schedule"),
        InlineKeyboardButton("🌐 ЗАБОН", callback_data="language")
    )

    bot.send_message(
        message.chat.id,
        "⚽ ХУШ ОМАДЕД БА LIVEBALL TV!\n\n"
        "📺 Тамошои пахшҳои варзишӣ\n"
        "🏆 Футбол ва дигар мусобиқаҳо\n\n"
        "Барои идома тугмаро интихоб кунед:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "live":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "⚽ Рӯйхати пахшҳо ҳоло омода шуда истодааст.")
    elif call.data == "schedule":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📅 Ҷадвали бозиҳо ҳоло омода шуда истодааст.")
    elif call.data == "language":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "🌐 Забон: Тоҷикӣ")

print("LIVEBALL TV started!")
bot.infinity_polling(skip_pending=True)
