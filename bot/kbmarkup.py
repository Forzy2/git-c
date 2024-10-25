from aiogram import types


def kb1() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[types.KeyboardButton(text="1"), 
                   types.KeyboardButton(text="2")]])

def kb2() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[types.KeyboardButton(text="1")]])

def kb3() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        resize_keyboard=True,                   
        keyboard=[[types.KeyboardButton(text="stop")]])

def kb4() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[types.KeyboardButton(text="/login")]])
    