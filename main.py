
import os
import time
import logging
import telebot
import requests

from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN дар GitHub Secrets ёфт нашуд!")

CHANNEL_NAME = "LIVEBALL TV"

# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# =========================
# TELEGRAM CONNECTION
# =========================

apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 60
apihelper.RETRY_ON_ERROR = False

bot = telebot.TeleBot(TOKEN)

# =========================
# START COMMAND
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton("⚽ ТАМОШОИ ПАХШҲО", callback_data="live"),
        InlineKeyboardButton("📅 ҶАДВАЛИ БОЗИҲО", callback_data="schedule"),
        InlineKeyboardButton("📖 ЧӢ ТАВР ТАМОШО КУНЕМ?", callback_data="help"),
        InlineKeyboardButton("🌐 ЗАБОН", callback_data="language"),
        InlineKeyboardButton("📤 МУБОДИЛА", url="https://t.me/Liveballtvi_bot")
    )

    bot.send_message(
        message.chat.id,
        "⚽ ХУШ ОМАДЕД БА LIVEBALL TV!\n\n"
        "📺 Пахши мустақими варзишӣ\n"
        "🏆 Футбол ва мусобиқаҳо\n"
        "🔥 Бозиҳои LIVE\n\n"
        "Барои идома тугмаро интихоб кунед:",
        reply_markup=keyboard
    )


# =========================
# BUTTON HANDLERS
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    try:
        bot.answer_callback_query(call.id)

        if call.data == "live":
            bot.send_message(
                call.message.chat.id,
                "⚽ РӮЙХАТИ ПАХШҲО\n\n"
                "Ҳоло рӯйхати пахшҳо омода карда мешавад."
            )

        elif call.data == "schedule":
            bot.send_message(
                call.message.chat.id,
                "📅 ҶАДВАЛИ БОЗИҲО\n\n"
                "Ҷадвали бозиҳо ҳоло омода карда мешавад."
            )

        elif call.data == "help":
            bot.send_message(
                call.message.chat.id,
                "📖 ДАСТУРАМАЛ\n\n"
                "1. Ба пахшҳо ворид шавед.\n"
                "2. Бозии дилхоҳро интихоб кунед.\n"
                "3. Пахши дастрасро тамошо кунед."
            )

        elif call.data == "language":
            bot.send_message(
                call.message.chat.id,
                "🌐 Забони бот: Тоҷикӣ"
            )

    except Exception:
        logger.exception("Callback error")


# =========================
# OTHER MESSAGES
# =========================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: True
)
def other_messages(message):
    bot.send_message(
        message.chat.id,
        "⚽ Барои истифодаи LIVEBALL TV "
        "фармони /start-ро пахш кунед."
    )


# =========================
# START BOT
# =========================

def run_bot():
    logger.info("LIVEBALL TV starting...")

    while True:
        try:
            logger.info("Connecting to Telegram...")

            # Хориҷ кардани webhook-и кӯҳна
            bot.delete_webhook(drop_pending_updates=False)

            # Танҳо як polling
            bot.polling(
                non_stop=False,
                interval=1,
                timeout=30,
                long_polling_timeout=25,
                skip_pending=False
            )

        except telebot.apihelper.ApiTelegramException as e:
            retry_after = 30

            try:
                data = e.result_json
                retry_after = data.get(
                    "parameters", {}
                ).get("retry_after", 30)
            except Exception:
                pass

            wait_time = int(retry_after) + 5

            logger.error("Telegram API error: %s", e)
            logger.warning(
                "Telegram талаб мекунад %s сония интизор шавем.",
                wait_time
            )

            time.sleep(wait_time)

        except requests.exceptions.RequestException:
            logger.exception("Network connection error")
            time.sleep(30)

        except Exception:
            logger.exception("Bot error")
            time.sleep(30)


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    run_bot()
