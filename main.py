from aiogram import types
from loader import dp, bot 
from aiogram.utils import executor
from models import Person
from states import StartState, CahngeProfileState, Adm_State, Dialogue_State
from aiogram.dispatcher import FSMContext
import re
import asyncio



@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    admin_role_button = types.InlineKeyboardButton('Администратор', callback_data='admin_role_button')
    user_role_button = types.InlineKeyboardButton('Пользователь', callback_data='user_role_button')
    keyboard = types.InlineKeyboardMarkup().row(admin_role_button, user_role_button)
    await msg.answer('Выберите роль для демонстрации.', reply_markup=keyboard)

@dp.message_handler(commands=['schedule'])
async def schedule(msg: types.Message):
    message = '''Тренировки на эту неделю:


Пятница 18:00 - Спортивный комплекс Лужники | ул. Лужники, 24, стр. 22, Москва

Среда 17:00 - Спортивный комплекс Лужники | ул. Лужники, 24, стр. 22, Москва

Понедельник 19:00 - Спортивный комплекс Лужники | ул. Лужники, 24, стр. 22, Москва

'''
    await msg.answer(message)


async def get_user_profile(msg):
    user_data = Person.get(Person.telegram_id == msg.from_user.id)
    if not user_data:
        await msg.answer('Для использования команды нужно зарегистрироваться.')
        return
    name = user_data.name
    phone = user_data.phone
    birthday = user_data.birthday
    message = f'''
ФИО: {name}
Номер телефона: {phone}
День рождения: {birthday}

Что желаете изменить?
'''
    change_name_button = types.InlineKeyboardButton('ФИО', callback_data='change_button_name')
    change_phone_button = types.InlineKeyboardButton('Номер телефона', callback_data='change_button_phone')
    change_birthday_button = types.InlineKeyboardButton('День рождения', callback_data='change_button_birthday')
    keyboard = types.InlineKeyboardMarkup().row(change_name_button, change_phone_button).add(change_birthday_button)
    await msg.answer(message, reply_markup=keyboard)

@dp.message_handler(commands=['my_profile'])
async def change_profile_data(msg: types.Message):
    person = Person.get_or_none(Person.telegram_id == msg.from_user.id)
    if person.role == 'admin':
        await msg.answer('Эта команда для игроков')
        return
    await get_user_profile(msg)

@dp.callback_query_handler(lambda call: call.data.startswith('change_button'))
async def change_data(call: types.CallbackQuery):
    await call.message.delete()
    data_for_change = call.data.split('_')[2]
    if data_for_change == 'name':
        await call.message.answer('Напишите ФИО')
        await CahngeProfileState.name.set()
    if data_for_change == 'phone':
        await call.message.answer('Напишите номер телефона в формате: 89000000000(числа подряд)')
        await CahngeProfileState.phone_number.set()
    if data_for_change == 'birthday':
        await call.message.answer('Напишите день рождения в формате: 01.01.1970')
        await CahngeProfileState.birthday.set()


@dp.message_handler(state=CahngeProfileState.name)
async def change_name(msg: types.Message, state: FSMContext):
    person = Person.get(Person.telegram_id == msg.from_user.id)
    person.name = msg.text
    person.save()
    await msg.answer('Имя изменено')
    await get_user_profile(msg)
    await state.finish()

@dp.message_handler(state=CahngeProfileState.phone_number)
async def change_phone(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and len(msg.text) == 11:
        person = Person.get(Person.telegram_id == msg.from_user.id)
        person.phone = msg.text
        person.save()
        await msg.answer('Номер телефона изменен')
        await get_user_profile(msg)
        await state.finish()
    else:
        await msg.answer('Неверный формат. Повторите ввод.')

@dp.message_handler(state=CahngeProfileState.birthday)
async def change_birthday(msg: types.Message, state: FSMContext):
    regex = r"\d{2}\.\d{2}\.\d{4}"
    if not re.search(regex, msg.text):
        await msg.answer('Неверный формат даты. Повторите ввод.')
        return
    person = Person.get(Person.telegram_id == msg.from_user.id)
    person.birthday = msg.text
    person.save()
    await msg.answer('Дата рождения изменена')
    await get_user_profile(msg)
    await state.finish()

@dp.message_handler(commands=['training_today'])
async def get_training_info(msg: types.Message):
    person = Person.get_or_none(Person.telegram_id == msg.from_user.id)
    if person.role == 'admin':
        await msg.answer('Эта команда для игроков')
        return
    message = f'''Уважаемый игрок!
Сегодня 31.10.2023 в 18:00 тренировка
🏟 Стадион: Спортивный комплекс Лужники
📍Адрес: ул. Лужники, 24, стр. 22, Москва

Вы пойдёте на тренировку?

<a href="https://yandex.ru/maps/-/CDa1zP5v">Построить маршрут</a>
'''
    second_accept_button = types.InlineKeyboardButton('Пойду', callback_data='accept_button')
    declain_button = types.InlineKeyboardButton('Не пойду', callback_data='declain_button')
    keyboard = types.InlineKeyboardMarkup().row(declain_button, second_accept_button)
    await bot.send_message(disable_web_page_preview=True, chat_id=msg.from_user.id, text=message, reply_markup=keyboard)



@dp.callback_query_handler(lambda call: call.data == 'admin_role_button')
async def set_admin_role(call: types.CallbackQuery):
    await call.message.delete()
    person = Person.get_or_none(Person.telegram_id == call.from_user.id)
    if not person:
        Person.create(telegram_id=call.from_user.id, role='admin')
    else:
        person.role = 'admin'
        person.save()
    button_1 = types.KeyboardButton('Запись на тренировку 🏒')
    button_2 = types.KeyboardButton('Рупор 📢')
    button_3 = types.KeyboardButton('Оценки тренировок 📊')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(button_3, button_1)
    keyboard.row(button_2)
    await call.message.answer('Роль администратора выбрана.', reply_markup=keyboard)

@dp.message_handler(content_types=['text'])
async def admin_commands(msg: types.Message):
    person = Person.get_or_none(Person.telegram_id == msg.from_user.id)
    if person.role == 'admin':
        if msg.text == 'Запись на тренировку 🏒':
            persons = Person.select().where(Person.role == 'user')
            if persons:
                message = 'На тренировку придут:\n\n'
                count = 1
                for person in persons:
                    message += f'✅ {count}) {person.name}\n'
                    count += 1  
                await msg.answer(message)
            else:
                await msg.answer('Пока никто не записался')
        elif msg.text == 'Рупор 📢':
            cancel_megaphone_button = types.InlineKeyboardButton('Отменить', 
                                                                callback_data='cancel_megaphone_button')
            keyboard = types.InlineKeyboardMarkup().add(cancel_megaphone_button)
            await msg.answer('Напишите сообщение, которое увидят все игроки.', reply_markup=keyboard)
            await Adm_State.megaphone.set()
        elif msg.text == 'Оценки тренировок 📊':
            message = '''Оценка прошедшей тренировки:

Игрок1 (ФИО) - 3
Игрок2 (ФИО) - 4
Игрок3 (ФИО) - 5
Игрок4 (ФИО) - 5
Игрок5 (ФИО) - 5
Игрок6 (ФИО) - 5

Средний бал: 4.5
'''
            await msg.answer(message)


@dp.callback_query_handler(lambda call: call.data == 'cancel_megaphone_button', state=Adm_State.megaphone)
async def cancel_megaphone(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await state.finish()
    await call.message.answer('Оповещение игроков отменено.')

@dp.message_handler(state=Adm_State.megaphone)
async def send_megaphone(msg: types.Message, state: FSMContext):
    await msg.answer('Оповещение игрокам отправлено.')
    await state.finish()
    persons = Person.select().where(Person.role == 'user')
    if persons:
        for person in persons:
            message = '❗️Оповещение от администратора❗️\n\n'
            message += msg.text
            await bot.send_message(person.telegram_id, message)

@dp.callback_query_handler(lambda call: call.data == 'user_role_button')
async def set_user_role(call: types.CallbackQuery):
    await call.message.delete()
    person = Person.get_or_none(Person.telegram_id == call.from_user.id)
    if not person:
        Person.create(telegram_id=call.from_user.id, role='user')
    else:
        person.role = 'user'
        person.save()
    sign_up_button = types.InlineKeyboardButton('Регистрация', callback_data='sign_up_button')
    keyboard = types.InlineKeyboardMarkup().add(sign_up_button)
    await call.message.answer('Роль Пользователя выбрана.', reply_markup=types.ReplyKeyboardRemove())
    await call.message.answer('Добро пожаловать!\n\nПройдите пожалуйста быструю регистрацию', 
                            reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data == 'sign_up_button')
async def sign_up(call: types.CallbackQuery):
    await call.message.delete()
    message = '''
Давайте знакомится. Напишите пожалуйста Ваши ФИО.'''

    await call.message.answer(message)
    await StartState.name.set()

@dp.message_handler(state=StartState.name)
async def get_name(msg: types.Message):
    person = Person.get_or_none(Person.telegram_id == msg.from_user.id)
    person.name = msg.text
    person.save()
    await msg.answer('''Принято. Теперь укажите Ваш номер телефона.
В формате: 89000000000(числа подряд)''')
    await StartState.phone_number_sign_up.set()

@dp.message_handler(state=StartState.phone_number_sign_up)
async def get_tel_number(msg: types.Message, state: FSMContext):
    if msg.text.isdigit() and len(msg.text) == 11:
        person = Person.get_or_none(Person.telegram_id == msg.from_user.id)
        person.phone = msg.text
        person.save()
        await msg.answer('''И последний вопрос. Когда у Вас день рождения?
Укажите в формате: 01.01.1970''')
        await StartState.birthday.set()
    else:
        await msg.answer('Вы неверно ввели номер телефона. Должно быть 11 цифр. Пожалуйста повторите попытку.')

@dp.message_handler(state=StartState.birthday)
async def get_birthday(msg: types.Message, state: FSMContext):
    regex = r"\d{2}\.\d{2}\.\d{4}"
    if not re.search(regex, msg.text):
        await msg.answer('Неверный формат даты. Повторите ввод.')
        return
    person = Person.get_or_none(Person.telegram_id == msg.from_user.id)
    person.birthday = msg.text
    person.save()
    await msg.answer(f'''
ФИО: {person.name}
Номер телефона: {person.phone}
День рождения: {msg.text}

Регистрация прошла успешно. Рады приветствовать!
Вы всегда можете изменить свои данные с помощью команды /my_profile
Совсем скоро я сообщу Вам место и время проведения Вашей первой тренировки.

(Для демонстрации оповещение будет выслано через 2 секунды)
''')
    await state.finish()
    await asyncio.sleep(2)

    message = f'''Уважаемый игрок!
Сегодня 31.10.2023 в 18:00 тренировка
🏟 Стадион: Спортивный комплекс Лужники
📍Адрес: ул. Лужники, 24, стр. 22, Москва

Вы пойдёте на тренировку?

<a href="https://yandex.ru/maps/-/CDa1zP5v">Построить маршрут</a>
'''
    second_accept_button = types.InlineKeyboardButton('Пойду', callback_data='accept_button')
    declain_button = types.InlineKeyboardButton('Не пойду', callback_data='declain_button')
    keyboard = types.InlineKeyboardMarkup().row(declain_button, second_accept_button)
    await bot.send_message(disable_web_page_preview=True, chat_id=msg.from_user.id, text=message, reply_markup=keyboard)

@dp.callback_query_handler(lambda call: call.data == 'accept_button')
async def accept(call: types.CallbackQuery):
    await call.message.delete()
    person = Person.get_or_none(Person.telegram_id == call.from_user.id)
    person.accept = True
    person.save()
    await call.message.answer('Запись успешно прошла. Ждём Вас на тренировке!')

@dp.callback_query_handler(lambda call: call.data == 'declain_button')
async def declain(call: types.CallbackQuery):
    await call.message.delete()
    person = Person.get_or_none(Person.telegram_id == call.from_user.id)
    person.accept = False
    person.save()
    await call.message.answer('Тренировка отклонена. Ждём Вас в следующий раз!')



if __name__ == '__main__':
    executor.start_polling(dp)