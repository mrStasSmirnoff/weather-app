import os
import sys
import time
import json
import logging
from datetime import datetime
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytz
import requests
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
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
    logger.info(f"Executing send_daily_message for recipient: {recipient}")
    try:
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
    except Exception as e:
        logger.exception(f"Error in send_daily_message for recipient {recipient}: {e}")


def schedule_jobs():
    """
    Schedules the daily messages using APScheduler.
    """
    scheduler = BackgroundScheduler(timezone=pytz.utc)

    # my scheduler
    timezone_you = pytz.timezone(TIMEZONE_MY)
    scheduler.add_job(
        send_daily_message,
        args=['Me'],
        trigger='cron',
        hour=7,
        minute=8,
        timezone=timezone_you,
        id='my_cron_job'
    )
    logger.info("Scheduled daily message for 'Me' at 7 AM in timezone: " + TIMEZONE_MY)

    timezone_mother = pytz.timezone(TIMEZONE_MOM)
    scheduler.add_job(
        send_daily_message,
        trigger='cron',
        args=['Mom'],
        hour=7,
        minute=0,
        timezone=timezone_mother,
        id='job_mother'
    )
    logger.info("Scheduled daily message for 'Mom' at 7 AM in timezone: " + TIMEZONE_MOM)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Weather Bot is running.")

    def log_message(self, format, *args):
        return


def run_web_server():
    """
    Starts a simple HTTP server to satisfy Render's requirement for an open port for Free Tier hosting
    """
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    logger.info(f"Starting web server on port {port}")
    server.serve_forever()


if __name__ == '__main__':
    logger.info("Application is starting...")
    # start a webserver in a separate thread
    web_server_thread = threading.Thread(target=run_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()

    schedule_jobs()

    # keep the main thread runnning
    try:
        while True:
            time.sleep(1)
    except Exception as e:
        logger.exception(f"An unhandled exception occurred: {e}")
