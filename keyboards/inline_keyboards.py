from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_objects_keyboard(objects_list: list) -> types.InlineKeyboardMarkup:
    inline_builder = InlineKeyboardBuilder()
    for obj in objects_list:
        inline_builder.add(obj)
