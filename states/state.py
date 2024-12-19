from aiogram.fsm.state import State, StatesGroup


class registration(StatesGroup):
    pref_name = State()


class registration_game(StatesGroup):
    pref1_name = State()


class new_game(StatesGroup):
    number_of_players = State()
    
class NewGameState(StatesGroup):
    waiting_for_nfgame = State()
