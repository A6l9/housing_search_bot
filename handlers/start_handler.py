import asyncio

from aiogram import types, Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from config import bot_messages
from loader import bot
from utils import process_real_estate_query
import keyboards
from states_storage import HousingSearchStates


router = Router(name="start")


@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext) -> None:
    await state.clear()

    await message.answer(text=bot_messages["BOT_GREETINGS"])

    await state.set_state(HousingSearchStates.get_user_request)


@router.message(HousingSearchStates.get_user_request)
async def get_user_request(message: types.Message, state: FSMContext) -> None:
    loader_message = await message.answer(text=bot_messages["LOADER_MESSAGE"])
    state_data = await state.get_data()
    user_request = state_data.get("user_request", "") + f" {message.text}"
    await state.set_data(data={"user_request": user_request.strip()})
    result = await asyncio.to_thread(process_real_estate_query, user_request)

    await loader_message.delete()

    status = result.get("status", "no_search")
    message_text = result.get("message")
    if not message_text:
            await message.answer(text=bot_messages["ERROR"])
    if status == "no_search":
        await message.answer(text=message_text)
    elif status == "not_found":
        await message.answer(text=message_text)

        await state.set_data(data={})
    elif status == "success":
        await state.set_state(HousingSearchStates.results_viewing)
        state_data["index"] = 0
        state_data["result"] = result
        state_data["message_text"] = message_text
        results_names_list = list(result.get("results", {}).keys())
        chunk_size = 5
        state_data["objects_names_list_chunks"] = [
                                                   results_names_list[i:i+chunk_size] 
                                                   for i in range(0, len(results_names_list), chunk_size)
                                                   ]
        await state.set_data(data=state_data)

        await message.answer(text=message_text, reply_markup=keyboards.create_objects_keyboard(
                                                        objects_list=state_data["objects_names_list_chunks"][0],
                                                        page_num=1,
                                                        no_pagination=False if len(state_data["objects_names_list_chunks"]) - 1 else True
                                                        ))


@router.callback_query(F.data.startswith("foreign:"), StateFilter(HousingSearchStates))
async def foreign_pagination(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    index = state_data.get("index", 0)
    objects_list = state_data.get("objects_names_list_chunks")

    action_type = call.data.split(":")[1]

    if action_type == "next":
        if index == len(objects_list) - 1:
            index = 0
        else:
            index += 1
    elif action_type == "back":
        if not index:
            index = len(objects_list) - 1
        else:
            index -= 1
    
    await call.message.edit_reply_markup(reply_markup=keyboards.create_objects_keyboard(
                                            objects_list=state_data["objects_names_list_chunks"][index],
                                            page_num=index+1
                                            ))

    state_data["index"] = index
    await state.set_data(data=state_data)


@router.callback_query(F.data.startswith("open-wrap:"), StateFilter(HousingSearchStates))
async def open_wrap_list(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    result_dict = state_data.get("result", {}).get("results", {})

    wrap_object_name = call.data.split(":")[1]
    state_data["wrap_index"] = 0
    state_data["wrap_result"] = {elem["id"]: elem for elem in result_dict.get(wrap_object_name, [])}
    state_data["wrap_types_list"] = [elem.get("type_unit") + f": {elem.get("id")}" for elem in result_dict.get(wrap_object_name, [])]
    state_data["wrap_types_ids_list"] = {elem.get("type_unit") + f": {elem.get("id")}": elem.get("id")  for elem in result_dict.get(wrap_object_name, [])}
    chunk_size = 5
    state_data["wrap_types_list_chunks"] = [
                                            state_data["wrap_types_list"][i:i+chunk_size] 
                                            for i in range(0, len(state_data["wrap_types_list"]), chunk_size)
                                            ]
    await state.set_data(data=state_data)

    await call.message.answer(text=bot_messages["SELECT_OBJECT"], reply_markup=keyboards.create_wrap_objects_keyboard(
                                                    types_list=state_data["wrap_types_list_chunks"][0],
                                                    types_ids_dict=state_data["wrap_types_ids_list"],
                                                    page_num=1,
                                                    no_pagination=False if len(state_data["wrap_types_list_chunks"]) - 1 else True
                                                    ))


@router.callback_query(F.data.startswith("wrap-obj:"), StateFilter(HousingSearchStates))
async def open_wrap_object(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()

    wrap_id = int(call.data.split(":")[1])
    wrap_obj_info = state_data["wrap_result"][wrap_id]
    await call.message.answer(text=bot_messages["OBJECT_INFO"].format(
                                                                price=wrap_obj_info.get("price") or "No data",
                                                                type_unit=wrap_obj_info.get("type_unit") or "No data",
                                                                purpose=wrap_obj_info.get("purpose") or "No data",
                                                                completion=wrap_obj_info.get("completion") or "No data",
                                                                handover_date=wrap_obj_info.get("handover_date") or "No data",
                                                                furnishing=wrap_obj_info.get("furnishing") or "No data",
                                                                studio=wrap_obj_info.get("studio") or "No data",
                                                                sqft=wrap_obj_info.get("sqft") or "No data",
                                                                baths=wrap_obj_info.get("baths") or "No data",
                                                                beds=wrap_obj_info.get("beds") or "No data",
                                                                view=wrap_obj_info.get("view") or "No data",
                                                                vacant=wrap_obj_info.get("vacant") or "No data",
                                                                area=wrap_obj_info.get("area") or "No data",
                                                                building=wrap_obj_info.get("building") or "No data"
                                                                      ), reply_markup=keyboards.create_wrap_object_keyboard(),
                                                                      parse_mode="markdown")


@router.callback_query(F.data.startswith("wrap:"), StateFilter(HousingSearchStates))
async def wrap_pagination(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    index = state_data.get("wrap_index", 0)
    wrap_types_list_chunks = state_data.get("wrap_types_list_chunks")

    action_type = call.data.split(":")[1]

    if action_type == "next":
        if index == len(wrap_types_list_chunks) - 1:
            index = 0
        else:
            index += 1
    elif action_type == "back":
        if not index:
            index = len(wrap_types_list_chunks) - 1
        else:
            index -= 1
    
    await call.message.edit_reply_markup(reply_markup=keyboards.create_wrap_objects_keyboard(
                                            types_list=wrap_types_list_chunks[index],
                                            types_ids_dict=state_data["wrap_types_ids_list"],
                                            page_num=index+1
                                            ))

    state_data["wrap_index"] = index
    await state.set_data(data=state_data)
