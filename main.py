import asyncio
import nest_asyncio
from bot import NightWatcherBot
from dotenv import load_dotenv
import os

load_dotenv()

nest_asyncio.apply()

if __name__ == "__main__":
    bot = NightWatcherBot()
    asyncio.run(bot.run())