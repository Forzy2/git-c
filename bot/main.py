import hashlib
import datetime
import random

import asyncio 

import calendar

from time import time
from aiogram import *
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .funcs import is_admin
from .database import connect, create_tables

from .kbmarkup import *
from .states import *
from .config import *


connection, cursor = connect(path=BASE_DIR / "assets/database/database.sqlite3")
com = connection.commit

bot, dp = Bot(token=config.TOKEN.get_secret_value()), Dispatcher()


@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext) -> None:
    if message.from_user.id in OWN_USER_ID:
        await state.set_state(Choice.choice)
        
        await message.answer("Привет!")
        await message.answer("1. Просмотр. \n2. Зарегистрировать профиль ученика. ", reply_markup=kb1())

        return

    await message.answer(text="Привет! Я - memobot, с моей помощью ты можешь отправлять задания преподавателю.\nЧтобы начать пользоваться ботом, авторизируйся.",
                        reply_markup=kb4())


@dp.message(Command("stop"))
@dp.message(F.text == "stop")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state is None: return

    await state.clear()
    await message.answer("Команда выполнена", reply_markup=types.ReplyKeyboardRemove())


@dp.message(Choice.choice, F.text == "1")
async def process_choice_first(message: types.Message, state: FSMContext) -> None:
    await check_command(message)


@dp.message(Choice.choice, F.text == "2")
async def process_choice_first(message: types.Message, state: FSMContext):
    await state.set_state(RegisterForm.name)
    await message.answer("Введите имя человека:", reply_markup=kb3())


@dp.message(RegisterForm.name)
async def process_regform_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await state.set_state(RegisterForm.surename)
    await message.answer("Введите фамилию человека:", reply_markup=kb3())


@dp.message(RegisterForm.surename)
async def process_regform_surename(message: types.Message, state: FSMContext):
    await state.update_data(surename=message.text)

    await state.set_state(RegisterForm.login)
    await message.answer("Введите логин:", reply_markup=kb3())


@dp.message(RegisterForm.login)
async def process_regform_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)

    await state.set_state(RegisterForm.password)
    await message.answer("Введите пароль:", reply_markup=kb3())


@dp.message(RegisterForm.password)
async def process_regform_password(message: types.Message, state: FSMContext):
    data = await state.get_data()

    hashedpassword = hashlib.sha256((message.text).encode())
    print(f"INSERT INTO users VALUES ('{data['name']}', '{data['surename']}', '{data['login']}', '{hashedpassword.hexdigest()}', NULL)")
    cursor.execute(f"INSERT INTO users VALUES ('{data['name']}', '{data['surename']}', '{data['login']}', '{hashedpassword.hexdigest()}', NULL)")

    com()

    await message.answer("Регистрация прошла успешно, аккаунт создан.", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()


@dp.message(Command("register"))
@is_admin
async def register(message: types.Message, state: FSMContext) -> None:
    await process_choice_first(message, state)


@dp.message(Command("login"))
async def login(message: types.Message, state: FSMContext) -> None:
    cursor.execute(f"SELECT EXISTS(SELECT logged_account_id FROM users WHERE logged_account_id={message.from_user.id})")

    if not cursor.fetchone()[0]:
        await state.set_state(LoginForm.login)
        await message.answer("Введи логин:", reply_markup=kb3())

    else: await message.answer("Ты уже авторизирован!", reply_markup=types.ReplyKeyboardRemove())


@dp.message(LoginForm.login)
async def process_logform_login(message: types.Message, state: FSMContext) -> None:

    cursor.execute(f"SELECT EXISTS(SELECT login FROM users WHERE login='{message.text}')")

    if cursor.fetchone()[0]:
        await state.update_data(_login=message.text)
        await state.set_state(LoginForm.password)
        await message.answer("Логин принят, введи пароль:", reply_markup=kb3())
    else: await message.answer("Неверный логин, попробуй еще раз!", reply_markup=kb3())


@dp.message(LoginForm.password)
async def process_logform_password(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()

    hashedpassword = hashlib.sha256((message.text).encode())

    cursor.execute(f"SELECT IIF((SELECT password FROM users WHERE login='{data['_login']}') = '{hashedpassword.hexdigest()}', true, false)")
    
    if cursor.fetchone()[0]:
        cursor.execute(f"UPDATE users SET logged_account_id={message.from_user.id} WHERE login='{data['_login']}'")

        cursor.execute(f"SELECT EXISTS(SELECT user_id FROM newsletter WHERE user_id={message.from_user.id})")
        if not cursor.fetchone()[0]:
            cursor.execute(f"INSERT INTO newsletter VALUES ({message.from_user.id}, false)")
        com()

        await message.answer("Авторизация прошла успешно!", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
    else: await message.answer("Ты ввел неправильный пароль, попробуй еще раз!", reply_markup=kb3())


@dp.message(Command("unlogin"))
async def unlogin(message: types.Message) -> None:
    cursor.execute(f"UPDATE users SET logged_account_id=0 WHERE logged_account_id={message.from_user.id}")
    cursor.execute(f"DELETE FROM newsletter WHERE user_id={message.from_user.id}")
    com()

    await message.answer("Ты вышел из аккаунта!")


@dp.message(Command("send"))
async def send(message: types.Message, state: FSMContext) -> None:
    cursor.execute(f"SELECT EXISTS(SELECT logged_account_id FROM users WHERE logged_account_id={message.from_user.id})")
    if cursor.fetchone()[0]:
        await state.set_state(Send.send)
        await message.answer("Отправь видео для пересылки", reply_markup=kb3())
    else:
        await message.answer(text="Ты не авторизирован!")


@dp.message(Send.send)
async def process_sendform_send(message: types.Message, state: FSMContext) -> None:
    try:
        if (
            message.video or 
            message.video_note or
            message.voice
        ):
            cursor.execute(f"SELECT name, surename FROM users WHERE logged_account_id={message.from_user.id}")
            info = cursor.fetchone()
            
            await message.send_copy(chat_id=OWN_USER_ID[0])
            await bot.send_message(chat_id=OWN_USER_ID[0], text=f"By {info[1]} {info[0]}", reply_markup=InlineKeyboardBuilder().row(
                types.InlineKeyboardButton(text="✅", callback_data=f"✅/{message.from_user.id}"), types.InlineKeyboardButton(text="❌", callback_data=f"❌/{message.from_user.id}")
            ).as_markup())
            
            await message.answer("Видео отправлено", reply_markup=types.ReplyKeyboardRemove())
            
            await state.clear()
        else: await message.answer("Ты отправил что-то не то, попробуй еще раз", reply_markup=kb3())
    except TypeError: await message.answer("Ты отправил что-то не то, попробуй еще раз")


@dp.message(Command("check"))
@is_admin
async def check_command(message: types.Message) -> None:
    if message.from_user.id in OWN_USER_ID:
        cursor.execute("SELECT name, surename, logged_account_id from users WHERE logged_account_id <> 0")
        data = cursor.fetchall()

        builder = InlineKeyboardBuilder()

        for _data in data:
            builder.row(
                types.InlineKeyboardButton(
                    text=f" {_data[0]} {_data[1]} ",
                    callback_data=f"check/{_data[2]}"
                )
            )

        await message.answer(
            text="Выберите пользователя",
            reply_markup=builder.as_markup()
        )


@dp.message(Command("announcement"))
@is_admin
async def announcement(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Adt.message)
    await message.answer("Отправьте объявление:", reply_markup=kb3())

        
@dp.message(Adt.message)
async def message_announcement(message: types.Message, state: FSMContext) -> None:
    cursor.execute("SELECT logged_account_id from users WHERE logged_account_id <> 0")
    
    ids = cursor.fetchall()
    
    for i in ids: 
        await bot.send_message(i[0], text="Объявление:")
        await message.send_copy(i[0])
    await state.clear()


@dp.message(Command("message"))
@is_admin
async def message_user(message: types.Message, state: FSMContext) -> None:
    cursor.execute("SELECT name, surename, logged_account_id from users WHERE logged_account_id <> 0")
    data = cursor.fetchall()

    builder = InlineKeyboardBuilder()

    for _data in data:
        builder.row(types.InlineKeyboardButton(text=f" {_data[0]} {_data[1]} ", callback_data=f"msg/{_data[2]}"))

    await message.answer(text="Выберите пользователя", reply_markup=builder.as_markup())


@dp.message(Command("help"))
async def help(message: types.Message) -> None:
    if message.from_user.id in OWN_USER_ID:
        text = """
Привет, вот список команд доступных тебе
    <i><strong>/register</strong> - Зарегистрировать пользователя</i>
    <i><strong>/check</strong> - Проверить кто когда отправлял дз</i>
    <i><strong>/message</strong> - Отправить сообщение</i>
    <i><strong>/announcement</strong> - Отправить объявление</i>
        """   
    else:
        text = """
Я - <i>memobot</i>, с моей помощью ты можешь отправлять задания
Вот список команд доступных тебе
    <i><strong>/login</strong> - Войти в аккаунт</i>
    <i><strong>/unlogin</strong> - Выйти из аккаунта</i>
    <i><strong>/send</strong> - Отправить дз</i>
        """   
    await message.answer(
        text=text,
        parse_mode=enums.ParseMode.HTML
    )


@dp.message(Command("id"))
async def get_id(message: types.Message) -> None:
    await message.answer(str(message.from_user.id))
    print(message.from_user.id)

    
@dp.callback_query()
async def callback_query(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.data[0] in ["✅", "❌"]:
        if callback.data[0] == "✅":
            user_id = callback.data.split("/")[1]
            
            cursor.execute(f"INSERT INTO hmtable VALUES ({time()}, true, {user_id})")
            cursor.execute(f"UPDATE newsletter SET newsletter_sended=true WHERE user_id={user_id}")
            com()
        
    elif callback.data.split("/")[0] == "check":
        cb = callback.data.split("/")
        now = datetime.datetime.now()
        
        _, last_day = calendar.monthrange(
            year=now.year, month=now.month
        )
        _list1 = list()
        
        for i in range(1, last_day+1):
            i = i if i > 9 else f'0{i}'
            cursor.execute(f"""SELECT timestamp, sended FROM hmtable 
                                WHERE logged_account_id_={cb[1]} AND strftime('%d', DATETIME(timestamp, 'unixepoch'))='{i}' ORDER BY timestamp DESC LIMIT 1
                                """)
            c = cursor.fetchall()
            if c: _list1.append(c)
            
        _list2 = [f"+{'-'*37}+", "| Дата        | Отправлено |", f"+{'-'*37}+"]

        for i in range(len(_list1)):
            _list2.append(f'| {datetime.datetime.fromtimestamp(_list1[i][0][0]).strftime("%d/%m/%y")} |          {"✅" if _list1[i][0][1] else "❌"}         |')
        _list2.append(f"+{'-'*37}+")
        await callback.message.answer("\n".join(_list2))
        
    elif callback.data.split("/")[0] == "msg":
        await state.set_state(Message.message)
        await state.update_data(user_id=callback.data.split("/")[1])
        
        await callback.message.answer("Отправьте сообщение:", reply_markup=kb3())


@dp.message(Message.message)        
async def message_msg(message: types.Message, state: FSMContext) -> None:
    data = await state.get_data()
    user_id = data["user_id"]

    await bot.send_message(user_id, text="Учитель отправил тебе сообщение:")
    await message.send_copy(user_id)
    

async def setup_bot_commands() -> None:
    await bot.set_my_commands(commands=[
                                            types.BotCommand(command="login", description="Войти в аккаунт"),
                                            types.BotCommand(command="unlogin", description="Выйти из аккаунта"),
                                            types.BotCommand(command="send", description="Отправить дз")
                                        ], scope=types.BotCommandScopeAllPrivateChats())
    for id in OWN_USER_ID:
        await bot.set_my_commands(commands=[
                                                types.BotCommand(command="register", description="Зарегистрировать пользователя"),
                                                types.BotCommand(command="check", description="Проверить кто отправлял дз"),
                                                types.BotCommand(command="message", description="Отправить сообщение"),
                                                types.BotCommand(command="announcement", description="Сделать объявление")
                                            ], scope=types.BotCommandScopeChat(chat_id=id))


async def newsletter_sender() -> None:
    text = (
        "Не видел задания от тебя сегодня!",
        "Самое время прислать задание!",
        "Не откладывай на потом, время прислать задание!",
        "Как насчет того, чтобы прислать задание?"
    )
    
    cursor.execute("SELECT EXISTS(SELECT newsletter_sended FROM newsletter WHERE newsletter_sended=false)")
    if cursor.fetchone()[0]:
        cursor.execute(f"SELECT user_id FROM newsletter WHERE newsletter_sended=false")
        auth_users = cursor.fetchall()

        for user_id in auth_users:
            user_id = user_id[0]
            
            date_now = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3, minutes=0)
            
            
            if (
                    date_now.hour >= TIME
                ):
                cursor.execute(f"UPDATE newsletter SET newsletter_sended=true WHERE user_id={user_id}")
                await bot.send_message(chat_id=user_id, text=random.choice(text))
                print(f"sended for {user_id}")
                com()

async def hmtable() -> None:
    cursor.execute("SELECT timestamp FROM hmtable ORDER BY timestamp DESC LIMIT 1")

    try:
        date = datetime.datetime.fromtimestamp(cursor.fetchone()[0])
    except TypeError:

        cursor.execute("SELECT logged_account_id FROM users WHERE logged_account_id<>0")
        ids = cursor.fetchall()

        for _id in ids:
            cursor.execute(f"INSERT INTO hmtable VALUES ({time()}, false, {_id[0]})")
            cursor.execute(f"UPDATE newsletter SET newsletter_sended=false WHERE user_id={_id[0]}")
        com()
        
    else:
        date_now = datetime.datetime.now()

        if date_now.hour >= 0 and date_now.day != date.day:
            cursor.execute("SELECT logged_account_id FROM users WHERE logged_account_id<>0")
            ids = cursor.fetchall()

            for _id in ids:
                cursor.execute(f"INSERT INTO hmtable VALUES ({time()}, false, {_id[0]})")
                cursor.execute(f"UPDATE newsletter SET newsletter_sended=false WHERE user_id={_id[0]}")
            com()

async def main() -> None: 
    create_tables(connection, cursor)

    await setup_bot_commands()
    asyncio.create_task(dp.start_polling(bot))
    
    while True:
        await hmtable()
        await newsletter_sender()
        
        await asyncio.sleep(15)