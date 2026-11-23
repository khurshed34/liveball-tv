
import os
import time
import logging
import requests
import telebot

from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN дар GitHub Secrets ёфт нашуд!")

# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("LIVEBALL_TV")

apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 60
apihelper.RETRY_ON_ERROR = False

bot = telebot.TeleBot(TOKEN)

# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "⚽ ТАМОШОИ ПАХШҲО",
            callback_data="live"
        ),
        InlineKeyboardButton(
            "📅 ҶАДВАЛИ БОЗИҲО",
            callback_data="schedule"
        ),
        InlineKeyboardButton(
            "📖 ЧӢ ТАВР ТАМОШО КУНЕМ?",
            callback_data="help"
        ),
        InlineKeyboardButton(
            "🌐 ЗАБОН",
            callback_data="language"
        ),
        InlineKeyboardButton(
            "📤 МУБОДИЛА",
            url="https://t.me/Liveballtvi_bot"
        )
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
# BUTTONS
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    try:
        bot.answer_callback_query(call.id)

        if call.data == "live":
            text = (
                "⚽ РӮЙХАТИ ПАХШҲО\n\n"
                "Ҳоло рӯйхати пахшҳо омода карда мешавад."
            )

        elif call.data == "schedule":
            text = (
                "📅 ҶАДВАЛИ БОЗИҲО\n\n"
                "Ҷадвали бозиҳо ҳоло омода карда мешавад."
            )

        elif call.data == "help":
            text = (
                "📖 ДАСТУРАМАЛ\n\n"
                "1. Ба пахшҳо ворид шавед.\n"
                "2. Бозии дилхоҳро интихоб кунед.\n"
                "3. Пахши дастрасро тамошо кунед."
            )

        elif call.data == "language":
            text = "🌐 Забони бот: Тоҷикӣ"

        else:
            text = "Ин тугма дастрас нест."

        bot.send_message(call.message.chat.id, text)

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
# ERROR WAIT
# =========================

def get_retry_time(error):

    try:
        return int(
            error.result_json.get(
                "parameters", {}
            ).get("retry_after", 30)
        ) + 5

    except Exception:
        return 35


# =========================
# RUN BOT
# =========================

def run_bot():

    logger.info("LIVEBALL TV starting...")

    while True:

        try:
            logger.info("Connecting to Telegram...")

            bot.polling(
                non_stop=False,
                interval=2,
                timeout=30,
                long_polling_timeout=25,
                skip_pending=False
            )

        except telebot.apihelper.ApiTelegramException as error:

            wait = get_retry_time(error)

            logger.error("Telegram API error: %s", error)
            logger.warning("Waiting %s seconds...", wait)

            time.sleep(wait)

        except requests.exceptions.RequestException:

            logger.exception("Network error")
            time.sleep(30)

        except Exception:

            logger.exception("Unexpected bot error")
            time.sleep(30)


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    run_bot()
