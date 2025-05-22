import asyncio
import logging

from aiogram.types import BotCommandScopeDefault

from loader import bot, dp
from set_commands import set_commands
from handlers import start_router 


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def main() -> None:
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    await set_commands()
    dp.include_router(start_router)
    bot_info = await bot.get_me()
    logger.info(f"Bot has {bot_info.full_name} started working")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
