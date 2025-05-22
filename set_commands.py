from aiogram.types import BotCommand, BotCommandScopeDefault

from loader import bot


async def set_commands() -> bool:
    commands_list = [
        BotCommand(command="start", description="Начать поиск жилья 🏘")
    ]

    return await bot.set_my_commands(commands=commands_list, scope=BotCommandScopeDefault())
