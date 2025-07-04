import asyncio
import nest_asyncio
from bot import NightWatcherBot


nest_asyncio.apply()

if __name__ == "__main__":
    bot = NightWatcherBot()
    asyncio.run(bot.run())