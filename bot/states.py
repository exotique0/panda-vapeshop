from aiogram.fsm.state import StatesGroup, State

class OrderFSM(StatesGroup):
    country = State()
    catalog = State()
    quantity = State()
    cart = State()
    name = State()
    address = State()
    confirm = State()
