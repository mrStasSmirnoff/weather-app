"""
Get chat ids from telegram bot
"""

import os
from telegram.ext import Updater, MessageHandler, Filters
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def handle_message(update, context):
    """
    Handler function that processes incoming messages.
    """
    chat_id = update.message.chat.id
    username = update.message.chat.username
    logging.info(f"Chat ID: {chat_id} | Username: {username}")

    # respons back to the user with its chat_id
    update.message.reply_text(f"Your chat ID is {chat_id}")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher # registers handlers and dispatches incoming updates to them.

    # to register a MessageHandler to handle all incoming messages
    dp.add_handler(MessageHandler(Filters.all, handle_message))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

