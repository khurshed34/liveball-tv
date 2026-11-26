
import os
import time
import json
import base64
import logging
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEB_APP_URL = os.getenv("WEB_APP_URL", "").strip()
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPOSITORY = os.getenv(
    "GITHUB_REPOSITORY", "khurshed34/liveball-tv"
).strip()
BRANCH = os.getenv("GITHUB_REF_NAME", "main").strip() or "main"

TIMEZONE = ZoneInfo("Asia/Dushanbe")
API_URL = "https://v3.football.api-sports.io/fixtures"
JSON_PATH = "matches.json"
UPDATE_INTERVAL = 30 * 60

if not TOKEN:
    raise ValueError("BOT_TOKEN ёфт нашуд!")

if not WEB_APP_URL.startswith("https://"):
    raise ValueError("WEB_APP_URL бояд HTTPS бошад!")

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
# TELEGRAM BUTTONS
# =========================

def create_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton(
            "⚽ ТАМОШОИ ПАХШҲО",
            web_app=WebAppInfo(url=WEB_APP_URL)
        ),
        InlineKeyboardButton(
            "📅 ҶАДВАЛИ БОЗИҲО",
            callback_data="schedule"
        ),
        InlineKeyboardButton(
            "📖 ДАСТУРАМАЛ",
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
    bot.send_message(
        message.chat.id,
        "⚽ ХУШ ОМАДЕД БА LIVEBALL TV!\n\n"
        "🔴 Бозиҳои зинда\n"
        "📅 Ҷадвали бозиҳо\n"
        "🏁 Натиҷаҳои воқеӣ\n\n"
        "Барои идома тугмаро пахш кунед:",
        reply_markup=create_keyboard()
    )


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    bot.answer_callback_query(call.id)

    if call.data == "schedule":
        text = (
            "📅 Ҷадвал ва натиҷаҳо дар саҳифаи "
            "LIVEBALL TV нишон дода мешаванд."
        )

    elif call.data == "help":
        text = (
            "📖 ДАСТУРАМАЛ\n\n"
            "1. Тугмаи ТАМОШОИ ПАХШҲО-ро пахш кунед.\n"
            "2. LIVE, ОЯНДА ё НАТИҶАҲО-ро интихоб кунед.\n"
            "3. Маълумот ба таври худкор нав мешавад.\n\n"
            "Видео танҳо аз манбаи расмӣ ва иҷозатдодашуда "
            "дастрас мешавад."
        )

    elif call.data == "language":
        text = "🌐 Забони бот: Тоҷикӣ"

    else:
        text = (
            "Барои кушодани сайт тугмаи "
            "ТАМОШОИ ПАХШҲО-ро пахш кунед."
        )

    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=create_keyboard()
    )


@bot.message_handler(content_types=["text"])
def other_messages(message):
    bot.send_message(
        message.chat.id,
        "⚽ Барои истифодаи LIVEBALL TV фармони /start-ро пахш кунед.",
        reply_markup=create_keyboard()
    )


# =========================
# FOOTBALL API
# =========================

def classify_status(status):
    live = {
        "1H", "HT", "2H", "ET", "P",
        "LIVE", "INT", "BT"
    }

    finished = {"FT", "AET", "PEN"}

    cancelled = {"PST", "CANC", "ABD", "AWD", "WO"}

    if status in live:
        return "live"

    if status in finished:
        return "finished"

    if status in cancelled:
        return "other"

    return "upcoming"


def fetch_fixtures():

    if not FOOTBALL_API_KEY:
        raise RuntimeError("FOOTBALL_API_KEY ёфт нашуд!")

    today = datetime.now(TIMEZONE).date()
    all_fixtures = {}

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    # Дирӯз то 6 рӯзи оянда
    for offset in range(-1, 2):

        match_date = today + timedelta(days=offset)

        logger.info(
            "Loading fixtures for %s",
            match_date.isoformat()
        )

        response = requests.get(
            API_URL,
            headers=headers,
            params={
                "date": match_date.isoformat(),
                "timezone": "Asia/Dushanbe"
            },
            timeout=45
        )

        response.raise_for_status()
        result = response.json()

        if result.get("errors"):
            raise RuntimeError(str(result["errors"]))

        for item in result.get("response", []):

            fixture = item.get("fixture", {})
            league = item.get("league", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            status = fixture.get("status", {})

            home = teams.get("home", {})
            away = teams.get("away", {})

            short_status = status.get("short", "NS")
            fixture_id = fixture.get("id")

            if not fixture_id:
                continue

            all_fixtures[fixture_id] = {
                "id": fixture_id,
                "date": fixture.get("date"),
                "timestamp": fixture.get("timestamp"),
                "status": short_status,
                "status_text": status.get("long", ""),
                "elapsed": status.get("elapsed"),
                "category": classify_status(short_status),

                "league": league.get("name", "Мусобиқа"),
                "country": league.get("country", ""),
                "league_logo": league.get("logo", ""),
                "country_flag": league.get("flag", ""),

                "home": home.get("name", "Home"),
                "away": away.get("name", "Away"),

                "home_logo": home.get("logo", ""),
                "away_logo": away.get("logo", ""),

                "home_goals": goals.get("home"),
                "away_goals": goals.get("away")
            }

    fixtures = list(all_fixtures.values())

    fixtures.sort(
        key=lambda x: x.get("timestamp") or 0
    )

    return {
        "updated_at": datetime.now(TIMEZONE).isoformat(),
        "timezone": "Asia/Dushanbe",
        "source": "API-Football",
        "fixtures": fixtures
    }


# =========================
# PUBLISH JSON TO GITHUB
# =========================

def publish_json(data):

    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN ёфт нашуд!")

    owner, repo = GITHUB_REPOSITORY.split("/", 1)

    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/contents/{JSON_PATH}"
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    current = requests.get(
        url,
        headers=headers,
        params={"ref": BRANCH},
        timeout=30
    )

    sha = None

    if current.status_code == 200:
        sha = current.json().get("sha")

    elif current.status_code != 404:
        current.raise_for_status()

    raw = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    ).encode("utf-8")

    body = {
        "message": "Update LIVEBALL TV matches",
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": BRANCH
    }

    if sha:
        body["sha"] = sha

    result = requests.put(
        url,
        headers=headers,
        json=body,
        timeout=45
    )

    if result.status_code not in (200, 201):
        raise RuntimeError(
            f"GitHub error {result.status_code}: {result.text[:400]}"
        )

    logger.info(
        "Matches published: %s",
        len(data["fixtures"])
    )


# =========================
# AUTOMATIC UPDATE
# =========================

def update_matches():
    data = fetch_fixtures()
    publish_json(data)


def updater_loop():

    while True:

        try:
            logger.info("Updating football matches...")
            update_matches()

        except Exception:
            logger.exception("Football update failed")

        time.sleep(UPDATE_INTERVAL)


# =========================
# RUN BOT
# =========================

def run_bot():

    logger.info("LIVEBALL TV started")

    threading.Thread(
        target=updater_loop,
        daemon=True
    ).start()

    while True:

        try:
            bot.polling(
                non_stop=False,
                interval=3,
                timeout=30,
                long_polling_timeout=25,
                skip_pending=True
            )

        except telebot.apihelper.ApiTelegramException as error:

            try:
                wait = int(
                    error.result_json.get(
                        "parameters", {}
                    ).get("retry_after", 30)
                ) + 5
            except Exception:
                wait = 35

            logger.error("Telegram error: %s", error)
            time.sleep(wait)

        except requests.exceptions.RequestException:
            logger.exception("Network error")
            time.sleep(30)

        except Exception:
            logger.exception("Bot error")
            time.sleep(30)


if __name__ == "__main__":
    run_bot()
