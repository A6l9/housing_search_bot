import asyncio

from aiogram import types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from config import bot_messages
from utils import process_real_estate_query
from keyboards import create_objects_keyboard
from states_storage import HousingSearchStates


router = Router(name="start")


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext) -> None:
    await state.clear()

    await message.answer(text=bot_messages["BOT_GREETINGS"])

    await state.set_state(HousingSearchStates.get_user_request)


@router.message(HousingSearchStates.get_user_request)
async def get_user_request(message: types.Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    user_request = state_data.get("user_request", "") + f" {message.text}"
    await state.set_data(data={"user_request": user_request.strip()})
    result = await asyncio.to_thread(process_real_estate_query, user_request)

    status = result.get("status", "no_search")
    message_text = result.get("message")
    if not message_text:
            await message.answer(text=bot_messages["ERROR"])
    if status == "no_search":
        await message.answer(text=message_text)
    elif status == "success":
        await state.set_state(HousingSearchStates.results_viewing)
        state_data["index"] = 0
        state_data["resutl"] = result
        results_names_list = list(result.get("results", {}).keys())
        chunk_size = 5
        state_data["objects_names_list_chunks"] = [
                                                   results_names_list[i:i+chunk_size] 
                                                   for i in range(0, len(results_names_list), chunk_size)
                                                   ]
        await state.set_data(data=state_data)

        await message.answer(text=message_text, reply_markup=create_objects_keyboard(state_data["objects_names_list_chunks"][0]))
