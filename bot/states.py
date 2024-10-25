from aiogram.filters.state import State, StatesGroup


class RegisterForm(StatesGroup):
    name = State()
    surename = State()
    login = State()
    password = State()

class LoginForm(StatesGroup):
    login = State()
    password = State()

class Choice(StatesGroup):
    choice = State()

class Send(StatesGroup):
    send = State()
    
class Adt(StatesGroup):
    message = State()

class Message(StatesGroup):
    message = State()