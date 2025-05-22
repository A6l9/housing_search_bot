from aiogram.fsm.state import State, StatesGroup


class HousingSearchStates(StatesGroup):
    get_user_request = State()
    results_viewing = State()
