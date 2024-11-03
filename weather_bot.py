import os
import json
import logging
from datetime import datetime
import pytz
import requests
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
#from apscheduler.schedulers.blocking import BlockingScheduler

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
#CHAT_ID_MOM = os.getenv('CHAT_ID_MOTHER')
TIMEZONE_MY = os.getenv('TIMEZONE_MY')
#TIMEZONE_MOM = os.getenv('TIMEZONE_MOM')


bot = Bot(token=TELEGRAM_BOT_TOKEN)

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

        return data

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching weather for {city}: {http_err}")
        return f"Could not retrieve weather data for {city}."

    except Exception as err:
        logger.error(f"An error occurred while fetching weather for {city}: {err}")
        return f"An error occurred while fetching weather data for {city}."


def send_message(chat_id, message, photo_url=None, videl_url=None):
    """

    """
    try:
        if photo_url:
            bot.send_photo(chat_id=chat_id, photo=photo_url)
            logger.info(f"Send photo to chat ID {chat_id}")
        else:
            bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Send message to chat ID {chat_id}")

    except TelegramError as e:
        logger.error(f"Failed to send the message to chat ID {chat_id}: {e}")


if __name__ == '__main__':
    #get_weather("Cologne")
    pass