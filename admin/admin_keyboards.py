from telebot.types import *
from telebot import types

admin_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
admin_keyboard.add(KeyboardButton('📊 Статистика'), KeyboardButton('🗂 Вигрузити БД'))
admin_keyboard.add(KeyboardButton('📩 Рассылка'), KeyboardButton('Вопросы'))
admin_keyboard.add(KeyboardButton('Згенерировать промокод'), KeyboardButton('Архив вопросов'))
admin_keyboard.add(KeyboardButton('Назад в меню ↩️'))