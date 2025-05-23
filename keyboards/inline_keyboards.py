from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_objects_keyboard(objects_list: list, page_num: int, no_pagination: bool=False) -> types.InlineKeyboardMarkup:
    inline_builder = InlineKeyboardBuilder()
    for obj in objects_list:
        inline_builder.add(types.InlineKeyboardButton(text=obj or "Untitled", callback_data="open-wrap:" + obj or "untitled"))
    inline_builder.adjust(1)

    if not no_pagination:
        inline_builder.row(
            types.InlineKeyboardButton(text="⬅️", callback_data="foreign:back"),
            types.InlineKeyboardButton(text=f"{page_num}", callback_data="None"), 
            types.InlineKeyboardButton(text="➡️", callback_data="foreign:next")
            )
    
    return inline_builder.as_markup()


def create_wrap_objects_keyboard(types_list: list, types_ids_dict: dict, page_num: int, no_pagination: bool=False) -> types.InlineKeyboardMarkup:
    inline_builder = InlineKeyboardBuilder()
    for elem in types_list:
        inline_builder.add(types.InlineKeyboardButton(text=elem, callback_data=f"wrap-obj:{types_ids_dict[elem]}"))
    inline_builder.adjust(1)

    if not no_pagination:
        inline_builder.row(
            types.InlineKeyboardButton(text="⬅️", callback_data="wrap:back"),
            types.InlineKeyboardButton(text=f"{page_num}", callback_data="None"), 
            types.InlineKeyboardButton(text="➡️", callback_data="wrap:next")
            )
    
    inline_builder.row(types.InlineKeyboardButton(text="Назад", callback_data="go-back:foreign"))

    return inline_builder.as_markup()


def create_wrap_object_keyboard() -> types.InlineKeyboardMarkup:
    inline_keyboard = [
        [types.InlineKeyboardButton(text="Написать по номеру", url="example.com")],
        [types.InlineKeyboardButton(text="Назад", callback_data="go-back:wrap")]
                       ]

    return types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
