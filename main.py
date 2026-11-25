
import os
import time
import logging
import requests
import telebot

from telebot import apihelper
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_APP_URL = os.getenv("WEB_APP_URL", "").strip()

if not TOKEN:
    raise ValueError("BOT_TOKEN дар GitHub Secrets ёфт нашуд!")

# Танҳо суроғаи HTTPS қабул мешавад
if WEB_APP_URL and not WEB_APP_URL.startswith("https://"):
    raise ValueError("WEB_APP_URL бояд бо https:// сар шавад!")

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
# MAIN KEYBOARD
# =========================

def create_keyboard():

    keyboard = InlineKeyboardMarkup(row_width=1)

    # Агар суроғаи сайт бошад, Web App мекушояд
    if WEB_APP_URL:
        keyboard.add(
            InlineKeyboardButton(
                "⚽ ТАМОШОИ ПАХШҲО",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        )
    else:
        keyboard.add(
            InlineKeyboardButton(
                "⚽ ТАМОШОИ ПАХШҲО",
                callback_data="live"
            )
        )

    keyboard.add(
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

    return keyboard


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    try:
        bot.send_message(
            message.chat.id,
            "⚽ ХУШ ОМАДЕД БА LIVEBALL TV!\n\n"
            "📺 Пахши мустақими варзишӣ\n"
            "🏆 Футбол ва мусобиқаҳо\n"
            "🔥 Бозиҳои LIVE\n\n"
            "Барои идома тугмаро интихоб кунед:",
            reply_markup=create_keyboard()
        )

    except Exception:
        logger.exception("Start error")


# =========================
# BUTTONS
# =========================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    try:
        bot.answer_callback_query(call.id)

        if call.data == "live":

            if WEB_APP_URL:
                text = (
                    "⚽ Барои тамошои пахшҳо "
                    "тугмаи менюро истифода баред."
                )
            else:
                text = (
                    "⚽ САҲИФАИ LIVEBALL TV\n\n"
                    "Суроғаи сайт ҳоло ба бот пайваст нашудааст.\n"
                    "Админ бояд Secret-и WEB_APP_URL-ро "
                    "дар GitHub илова кунад."
                )

        elif call.data == "schedule":

            text = (
                "📅 ҶАДВАЛИ БОЗИҲО\n\n"
                "Ҷадвали бозиҳо ҳоло омода карда мешавад."
            )

        elif call.data == "help":

            text = (
                "📖 ДАСТУРАМАЛ\n\n"
                "1. Ба бахши пахшҳо ворид шавед.\n"
                "2. Бозии дилхоҳро интихоб кунед.\n"
                "3. Агар пахши дастрас бошад, онро тамошо кунед.\n\n"
                "⚠️ Дастрасии пахш аз мавҷудияти манбаи "
                "расмии видео вобаста аст."
            )

        elif call.data == "language":

            text = "🌐 Забони бот: Тоҷикӣ"

        else:
            text = "Ин тугма дастрас нест."

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=create_keyboard()
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

    try:
        bot.send_message(
            message.chat.id,
            "⚽ Барои истифодаи LIVEBALL TV "
            "фармони /start-ро пахш кунед.",
            reply_markup=create_keyboard()
        )

    except Exception:
        logger.exception("Message error")


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
    logger.info("Web App configured: %s", bool(WEB_APP_URL))

    while True:

        try:
            logger.info("Connecting to Telegram...")

            bot.polling(
                non_stop=False,
                interval=3,
                timeout=30,
                long_polling_timeout=25,
                skip_pending=True
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
