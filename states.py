from aiogram.fsm.state import StatesGroup, State

class PhotoUpload(StatesGroup):
    waiting_for_group = State()
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_column = State() 
