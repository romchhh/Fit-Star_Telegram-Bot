from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

buttonbuy1q = KeyboardButton('🌟 Задать один вопрос')
buttonbuy10q = KeyboardButton('😎 Задать 10 вопросов')
buttonbuyc = KeyboardButton('📘 Курс о наборе и сушке тела')
buttoncountb = KeyboardButton('🔢 БЖУ')
buttonmyprofile = KeyboardButton('🙎‍♂️ Мой профиль')
buttontrainings = KeyboardButton('🏋🏽‍♂️Cтандартные программы')

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(buttonbuy1q, buttonbuy10q, buttonbuyc, buttoncountb, buttonmyprofile, buttontrainings)

course_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
course_keyboard.add(KeyboardButton('Восстановления 🛌'), KeyboardButton('Тренировки 🏋️‍♂️'))
course_keyboard.add(KeyboardButton('Питание на сушку 🥗'), KeyboardButton('Питание на массу 🍗'))
course_keyboard.add(KeyboardButton('Назад в меню ↩️'))

training_keyboard = InlineKeyboardMarkup(row_width=2)
training_keyboard.add(
    InlineKeyboardButton("Дважды в неделю", callback_data="twice_per_week"),
    InlineKeyboardButton("Трижды в неделю", callback_data="thrice_per_week"),
    InlineKeyboardButton("Четыре раза в неделю", callback_data="fourth_per_week"),
)

countbju_keyboard = InlineKeyboardMarkup(row_width=2)
countbju_keyboard.add(
    InlineKeyboardButton('На сушку ', callback_data="perDrying"),
    InlineKeyboardButton('На массу', callback_data="perMass"),
)