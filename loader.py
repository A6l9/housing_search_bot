from aiogram import Bot, Dispatcher
import yaml

from config import ProjectSettings


proj_settings = ProjectSettings()

bot = Bot(token=proj_settings.bot_token)
dp = Dispatcher()
