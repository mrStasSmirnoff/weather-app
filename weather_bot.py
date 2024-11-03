import os
import json
import logging
from datetime import datetime
import pytz
import requests
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.FileHandler("weather_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID_MY = os.getenv('CHAT_ID_MY')
CHAT_ID_MOM = os.getenv('CHAT_ID_MOM')
TIMEZONE_MY = os.getenv('TIMEZONE_MY')
TIMEZONE_MOM = os.getenv('TIMEZONE_MOM')

bot = Bot(token=TELEGRAM_BOT_TOKEN)

with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)


def get_weather(city):
    """
    Fetches weather data for a given city using the OpenWeatherMap API.
    Returns a formatted string with weather description and temperature.
    """

    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?q={city}&APPID={OPENWEATHER_API_KEY}&units=metric"
        )
        # 5d, 3h window forecast call
        #https://api.openweathermap.org/data/2.5/forecast?q=Cologne&APPID=&units=metric
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        weather_desc = data['weather'][0]['description'].capitalize()
        temp = data['main']['temp']
        temp_feels_lile = data['main']['feels_like']
        logger.info(f"Weather in {city}: {weather_desc}, Temperature: {temp}°C, Feels like: {temp_feels_lile} °C")

        return f"Погода сейчас в {city}: {weather_desc}, Температура: {temp}°C, По ощущениям как: {temp_feels_lile} °C"

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching weather for {city}: {http_err}")
        return f"Could not retrieve weather data for {city}."

    except Exception as err:
        logger.error(f"An error occurred while fetching weather for {city}: {err}")
        return f"An error occurred while fetching weather data for {city}."


def send_message(chat_id, message, media_url=None):
    """
    Sends a message to a specified Telegram chat ID.
    If photo_url or video_url is provided, sends the media with the message as a caption.
    """
    try:
        if media_url:
            bot.send_photo(chat_id=chat_id, photo=media_url)
            logger.info(f"Send photo to chat ID {chat_id}")
        else:
            bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Send message to chat ID {chat_id}")

    except TelegramError as e:
        logger.error(f"Failed to send the message to chat ID {chat_id}: {e}")


def send_daily_message(recipient):
    """
    Constructs and sends the daily message to the specified recipient.
    """
    greetings = config['greetings'].get(recipient, "Доброе утро!")
    city = config['cities'].get(recipient, "Unknown city")
    media_url = config['media'].get(recipient, None)
    extra_content = config['extras'].get(recipient, "")
    chat_id = CHAT_ID_MY if recipient == 'Me' else CHAT_ID_MOM

    weather_info = get_weather(city)

    msg = f"{greetings}\n\n{weather_info}"
    if extra_content:
        msg += f"\n\n{extra_content}"

    send_message(chat_id, msg, media_url)


def schedule_jobs():
    """
    Schedules the daily messages using APScheduler.
    """
    scheduler = BlockingScheduler(timezone=pytz.utc)

    # my scheduler
    timezone_you = pytz.timezone(TIMEZONE_MY)
    scheduler.add_job(
        send_daily_message,
        args=["Me"],
        trigger='cron',
        hour=7,
        minute=8,
        timezone=timezone_you,
        id='my_cron_job'
    )
    logger.info("Scheduled daily message for 'you' at 7 AM in timezone: " + TIMEZONE_MY)

    timezone_mother = pytz.timezone(TIMEZONE_MOM)
    scheduler.add_job(
        send_daily_message,
        trigger='cron',
        args=['mother'],
        hour=7,
        minute=0,
        timezone=timezone_mother,
        id='job_mother'
    )
    logger.info("Scheduled daily message for 'mother' at 7 AM in timezone: " + TIMEZONE_MOM)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")

if __name__ == '__main__':
    #get_weather("Cologne")
    send_daily_message("Me")
    send_daily_message("Mom")
