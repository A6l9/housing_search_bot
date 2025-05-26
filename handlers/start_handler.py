import asyncio
from uuid import uuid4

from aiogram import types, Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from config import bot_messages
from loader import bot
from utils import process_real_estate_query, create_whatsapp_link
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
    result = await process_real_estate_query(user_request, user_id=message.from_user.id)

    status = result.get("status", "no_search")
    message_text = result.get("message")
    if not message_text:
            await loader_message.edit_text(text=bot_messages["ERROR"])
    if status == "no_search":
        await loader_message.edit_text(text=message_text)
    elif status == "not_found":
        await loader_message.edit_text(text=message_text)

        await state.set_data(data={})
    elif status == "success":
        await state.set_state(HousingSearchStates.results_viewing)
        state_data["index"] = 0
        results_names_list = list(result.get("results", {}).keys())
        state_data["names_uuid_dict"] = dict(zip(results_names_list, [str(uuid4()) for _ in results_names_list]))
        state_data["result"] = {
            "status": result["status"],
            "message": result["message"],
            "results": {state_data["names_uuid_dict"][key]: val for key, val in result["results"].items()}
            }
        state_data["message_text"] = message_text
        chunk_size = 5
        state_data["objects_names_list_chunks"] = [
                                                   results_names_list[i:i+chunk_size] 
                                                   for i in range(0, len(results_names_list), chunk_size)
                                                   ]
        await state.set_data(data=state_data)

        await loader_message.edit_text(text=message_text, reply_markup=keyboards.create_objects_keyboard(
                                                        objects_list=state_data["objects_names_list_chunks"][0],
                                                        uuid_dict=state_data["names_uuid_dict"],
                                                        page_num=1,
                                                        no_pagination=False if len(state_data["objects_names_list_chunks"]) - 1 else True
                                                        ))


@router.callback_query(F.data.startswith("foreign:"), StateFilter(HousingSearchStates.results_viewing))
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
                                            uuid_dict=state_data["names_uuid_dict"],
                                            page_num=index+1
                                            ))

    state_data["index"] = index
    await state.set_data(data=state_data)


@router.callback_query(F.data.startswith("open-wrap:"), StateFilter(HousingSearchStates.results_viewing))
async def open_wrap_list(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    result_dict = state_data.get("result", {}).get("results", {})

    wrap_object_name = call.data.split(":")[1]
    state_data["wrap_object_name"] = wrap_object_name
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

    await call.message.edit_text(text=bot_messages["SELECT_OBJECT"], reply_markup=keyboards.create_wrap_objects_keyboard(
                                                    types_list=state_data["wrap_types_list_chunks"][0],
                                                    types_ids_dict=state_data["wrap_types_ids_list"],
                                                    page_num=1,
                                                    no_pagination=False if len(state_data["wrap_types_list_chunks"]) - 1 else True
                                                    ))


@router.callback_query(F.data.startswith("wrap-obj:"), StateFilter(HousingSearchStates.results_viewing))
async def open_wrap_object(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()

    wrap_id = int(call.data.split(":")[1])
    wrap_obj_info = state_data["wrap_result"][wrap_id]
    link = create_whatsapp_link(message=bot_messages["WHATSAPP_MESSAGE"].format(agent_name=wrap_obj_info["agent_name"], 
                                                                                building=wrap_obj_info["building"]
                                                                                ), phone_number=wrap_obj_info["agent_whatsapp"])
    await call.message.edit_text(text=bot_messages["OBJECT_INFO"].format(
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
                                                                      ), reply_markup=keyboards.create_wrap_object_keyboard(link),
                                                                      parse_mode="markdown")


@router.callback_query(F.data.startswith("wrap:"), StateFilter(HousingSearchStates.results_viewing))
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


@router.callback_query(F.data.startswith("go-back:"), StateFilter(HousingSearchStates.results_viewing))
async def go_back(call: types.CallbackQuery, state: FSMContext) -> None:
    state_data = await state.get_data()
    
    action_type = call.data.split(":")[1]
    if action_type == "foreign":
        await call.message.edit_text(text=state_data["message_text"], reply_markup=keyboards.create_objects_keyboard(
                                                        objects_list=state_data["objects_names_list_chunks"][state_data["index"]],
                                                        page_num=state_data["index"] + 1,
                                                        uuid_dict=state_data["names_uuid_dict"],
                                                        no_pagination=False if len(state_data["objects_names_list_chunks"]) - 1 else True
                                                        ))
    else:
        await call.message.edit_text(text=bot_messages["SELECT_OBJECT"], reply_markup=keyboards.create_wrap_objects_keyboard(
                                                    types_list=state_data["wrap_types_list_chunks"][state_data["wrap_index"]],
                                                    types_ids_dict=state_data["wrap_types_ids_list"],
                                                    page_num=state_data["wrap_index"] + 1,
                                                    no_pagination=False if len(state_data["wrap_types_list_chunks"]) - 1 else True
                                                    ))
