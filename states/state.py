from aiogram.fsm.state import State, StatesGroup


class registration(StatesGroup):
    pref_name = State()


class registration_game(StatesGroup):
    pref1_name = State()


class new_game(StatesGroup):
    number_of_players = State()
    
class NewGameState(StatesGroup):
    waiting_for_nfgame = State()

class MessagetoAdmin(StatesGroup):
    msgt = State()
    
class messagetouser(StatesGroup):
    messag = State()
    
class Adminid(StatesGroup):
    admin_id = State()
    
class msgtoall(StatesGroup):
    sendallanonym = State()
    
class msgtoindividual(StatesGroup):
    userid = State()
    sendtoone = State()
    
class UserInformations(StatesGroup):
    userid_state = State()
    
class awaiting_game_number(StatesGroup):
    waiting = State()