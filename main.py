from __future__ import absolute_import
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import BOT_TOKEN, ADMIN_IDS, BOT_DB_PATH, PRIVATE_CHANNEL_ID, CHANNEL_INVITE_LINK, QUESTIONS_DB_PATH, ANOTHER_BANKING_ID, QIWI_PAYMENT_URL_COURSE, QIWI_PAYMENT_URL_1QUEST, QIWI_PAYMENT_URL_10QUESTS, MY_LOGIN, QIWI_SECRET_KEY, PAYMENTS_DB_PATH
from keyboards import keyboard, course_keyboard, countbju_keyboard, training_keyboard
import sqlite3
from db.db import BotDb, QuestionsDb, PaymentsDb
from telebot import types
from admin.admin_keyboards import admin_keyboard
import datetime
import random
import string
from threading import local
import requests
from telebot import types
from SimpleQIWI import *
import threading
import time

bot = telebot.TeleBot(BOT_TOKEN)
bot_db = BotDb(BOT_DB_PATH) 
private_channel_id = PRIVATE_CHANNEL_ID
channel_invite_link = CHANNEL_INVITE_LINK

user_states = {}
thread_locals = local()
questions_db = sqlite3.connect(QUESTIONS_DB_PATH, check_same_thread=False)
payments_db = PaymentsDb(PAYMENTS_DB_PATH)
api_access_token = QIWI_SECRET_KEY
my_login = MY_LOGIN


def payment_history_last(my_login, api_access_token, rows_num, next_TxnId, next_TxnDate):
    s = requests.Session()
    s.headers['authorization'] = 'Bearer ' + api_access_token
    parameters = {'rows': rows_num, 'nextTxnId': next_TxnId, 'nextTxnDate': next_TxnDate}
    h = s.get('https://edge.qiwi.com/payment-history/v2/persons/' + my_login + '/payments', params=parameters)
    return h.json()

lastPayments = payment_history_last(my_login, api_access_token, '30','','')

def update_payments():
    while True:
        try:
            last_payments = payment_history_last(my_login, api_access_token, '30', '', '')

            for payment in last_payments['data']:
                txn_id = payment['txnId']
                amount = payment['sum']['amount']
                currency = payment['sum']['currency']
                date = payment['date']
                comment = payment.get('comment', '')
                status = payment['status']

                if not payments_db.payment_exists(txn_id):
                    payments_db.insert_payment(txn_id, amount, currency, date, comment, status)

            time.sleep(15)

        except Exception as e:
            print(f"Error updating payments: {e}")
            time.sleep(15)
            
threading.Thread(target=update_payments).start()
            
            

questions_cursor = questions_db.cursor()
questions_cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        question_text TEXT,
        answers_text TEXT,
        timestamp NUMERIC,
        question_count INTEGER DEFAULT 1,
        admin_username TEXT
    )''')

questions_db.commit()




@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if(not bot_db.user_exist(message.from_user.id)):
        bot_db.add_user(message.from_user.id, message.from_user.username)

    if message.from_user.username:
        username = message.from_user.username
    elif message.from_user.first_name:
        username = message.from_user.first_name
    else:
        username = "Пользователь"

    bot.send_message(message.chat.id, f"Привет, {username}!", reply_markup=keyboard)
 
 
###   
@bot.message_handler(func=lambda message: message.text == '🙎‍♂️ Мой профиль')
def my_profile_handler(message):
    user_id = message.from_user.id
    user_data = bot_db.get_user_data(user_id)

    if user_data:
        username = user_data['username']
        join_date = user_data['join_date']
        has_course_access = user_data['has_course_access']

        course_access_message = "Доступ к курсу: ✅" if has_course_access else "Доступ к курсу: ❌"

        profile_info = f"<b>Имя пользователя:</b> {username}\n" \
                      f"<b>Дата присоединения:</b> {join_date}\n" \
                      f"{course_access_message}"

        bot.send_message(message.chat.id, profile_info, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "Информация о вашем профиле не найдена.")
 
 
###  
@bot.message_handler(func=lambda message: message.text == '📘 Курс о наборе и сушке тела')
def course_handler(message):
    user_id = message.from_user.id

    if bot_db.user_has_course_access(user_id):
        bot.send_message(user_id, "У вас уже есть доступ к курсу.", reply_markup=course_keyboard)
    else:
        markup = types.InlineKeyboardMarkup()


        buy_1question_button = types.InlineKeyboardButton("Купить курс (QIWI Кошелек)", callback_data="buy_course")
        promocode_course_button = types.InlineKeyboardButton("Использовать промокод", callback_data='use_promocode_for_course')
        another_banking_course_button = types.InlineKeyboardButton("Другой банкинг", callback_data='another_banking_for_course')

        buttons = [buy_1question_button, promocode_course_button, another_banking_course_button]

        for button in buttons:
            markup.add(button)

        course_description = """
        <b>📘 Курс о наборе и сушке весса</b>
        <i>Достигните своей идеальной формы и улучшите свое здоровье с нашим курсом!</i>

        <u>Что вы получите в этом курсе:</u>
        - <strong>План дня:</strong> Узнайте, как правильно организовать свой день для максимальной эффективности.
        - <strong>Тренировки:</strong> Получите советы по тренировкам и инструкции от опытных тренеров.
        - <strong>Питание:</strong> Мы предоставим вам рецепты и рекомендации по здоровому питанию.

        <u>Стоимость курса:</u>
        - 200 гривен (UAH)
        - 500 рублей (RUB)

        Присоединитесь к нам сегодня и начните свой путь к здоровой и красивой жизни! 💪🥗
        """
        bot.send_message(message.chat.id, text=course_description, parse_mode="HTML", reply_markup=markup)



@bot.callback_query_handler(func=lambda call: call.data == 'buy_course')
def buy_course_callback(call):
    user_id = call.from_user.id
    
    markup = types.InlineKeyboardMarkup()
    payment_for_course_url = QIWI_PAYMENT_URL_COURSE.format(user_id=user_id)
    pay_1_quest_button = types.InlineKeyboardButton("Оплатить", url=payment_for_course_url)
    check_course_payment_button = types.InlineKeyboardButton("Проверить платеж", callback_data="check_payment_for_course")
    markup.add(pay_1_quest_button, check_course_payment_button)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Для оплаты нажмите на кнопку ниже:", reply_markup=markup)




@bot.callback_query_handler(func=lambda call: call.data == 'check_payment_for_course')
def check_payment_for_course(call):
    user_id = call.from_user.id
    try:
        conn = sqlite3.connect(PAYMENTS_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        # Check for comments that contain one of the specified variants
        comment_template = f'%Оплата за курс {user_id}%'  # Original variant
        comment_template2 = f'%Оплата_за_курс_{user_id}%'
        comment_template3 = f'Оплата%20за%20курс%{user_id}%'  

        cursor.execute(
            f"SELECT * FROM payments WHERE amount = 500 AND currency = 643 AND status = 'SUCCESS' AND "
            f"(comment LIKE ? OR comment LIKE ? OR comment LIKE ?)",
            (comment_template, comment_template2, comment_template3)
        )
        payment_data_list = cursor.fetchall()

        for payment_data in payment_data_list:
            txn_id, amount, currency, date, comment, status, used = payment_data
            if not used:
                cursor.execute("UPDATE payments SET used = 1 WHERE txn_id = ?", (txn_id,))
                conn.commit()

                bot_db.set_course_access(user_id)
                bot.send_message(call.message.chat.id, "✅ Оплата найдена. Теперь у вас есть доступ к курсу.", reply_markup=course_keyboard)
            else:
                bot.send_message(call.message.chat.id, "❌ Оплата найдена, но уже использована.")

        if not payment_data_list:
            bot.send_message(call.message.chat.id, "❌ Совпадающая оплата не найдена.")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при проверке оплаты: {e}")

    finally:
        conn.close()

def process_and_use_promocode_for_course(message):
    user_id = message.from_user.id
    if not bot_db.user_has_course_access(user_id):
        promo_code = message.text.strip()
        if promo_code in promo_codes_course:
            del promo_codes_course[promo_code]
            save_promo_codes_to_file(promo_codes_course, file_course)
            bot_db.set_course_access(user_id)
            bot.send_message(user_id, "✅ Промокод успешно использован. Теперь у вас есть доступ к курсу.", reply_markup=course_keyboard)
        else:
            bot.send_message(user_id, "❌ Промокод недействителен или уже использован.")
    else:
        bot.send_message(user_id, "✅ У вас уже есть доступ к курсу.", reply_markup=course_keyboard)
        
@bot.callback_query_handler(func=lambda call: call.data == 'another_banking_for_course')
def another_banking_for_course(call):
    user_id = call.from_user.id

    admin_username = bot.get_chat(ANOTHER_BANKING_ID).username
    message_text = f"Вы выбрали другой банкинг." \
                   f"Для уточнения деталей свяжитесь с администратором @fitstarsupport."

    bot.send_message(user_id, message_text)

@bot.callback_query_handler(func=lambda call: call.data == 'use_promocode_for_course')
def use_promocode_for_course(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Пожалуйста, введите промокод:")
    bot.register_next_step_handler(call.message, process_and_use_promocode_for_course)
    
@bot.message_handler(func=lambda message: message.text == 'Назад в меню ↩️')
def back_to_menu(message):
    bot.send_message(message.chat.id, "Вы вернулись в главное меню.", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Восстановления 🛌')
def recovery_course(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Ссылка на курс восстановления", url="https://t.me/c/2143977979/12")
    keyboard.add(url_button)
    
    bot.send_message(message.chat.id, text=f"Присоединяйтесь к нашему частному каналу по ссылке: {channel_invite_link}", parse_mode='HTML', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Тренировки 🏋️‍♂️')
def workouts_course(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Ссылка на курс тренировки", url="https://t.me/c/2143977979/22")
    keyboard.add(url_button)
    bot.send_message(message.chat.id, text=f"Присоединяйтесь к нашему частному каналу по ссылке: {channel_invite_link}", parse_mode='HTML', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Питание на сушку 🥗')
def cutting_diet_course(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Ссылка на курс питание на сушку", url="https://t.me/c/2143977979/54")
    keyboard.add(url_button)
    bot.send_message(message.chat.id, text=f"Присоединяйтесь к нашему частному каналу по ссылке: {channel_invite_link}", parse_mode='HTML', reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Питание на массу 🍗')
def bulking_diet_course(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="Ссылка на курс питание на массу", url="https://t.me/c/2143977979/88")
    keyboard.add(url_button)
    bot.send_message(message.chat.id, text=f"Присоединяйтесь к нашему частному каналу по ссылке: {channel_invite_link}", parse_mode='HTML', reply_markup=keyboard)


###       
@bot.message_handler(func=lambda message: message.text == '🔢 БЖУ')
def countbju_handler(message):
    user_id = message.from_user.id

    if bot_db.user_has_course_access(user_id):
        bot.send_message(message.chat.id, "Выберите категорию, которая вас интересует:", reply_markup=countbju_keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к курсу. Купите курс, чтобы получить доступ к калькулятору БЖУ.", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ["perMass", "perDrying"])
def handle_bju_callback(call):
    if call.data == "perMass":
        bot.send_message(call.message.chat.id, "Введите свой вес:")
        user_states[call.message.chat.id] = 'waiting_for_weight_mass'
    elif call.data == "perDrying":
        bot.send_message(call.message.chat.id, "Введите свой вес:")
        user_states[call.message.chat.id] = 'waiting_for_weight_drying'

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_weight_mass')
def handle_weight_input_mass(message: Message):
    process_bju_input(message, protein_multiplier=2, fat_multiplier=1, carb_multiplier=6, calorie_multiplier=42.1)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_for_weight_drying')
def handle_weight_input_drying(message: Message):
    process_bju_input(message, protein_multiplier=2, fat_multiplier=1, carb_multiplier=4, calorie_multiplier=33.9)

def process_bju_input(message: Message, protein_multiplier, fat_multiplier, carb_multiplier, calorie_multiplier):
    try:
        weight = float(message.text)
        if not (25 <= weight <= 160):
            raise ValueError("Weight should be between 25 and 160 kg.")

        proteins = round(weight * protein_multiplier, 2)
        fats = round(weight * fat_multiplier, 2)
        carbohydrates = round(weight * carb_multiplier, 2)
        calories = round(weight * calorie_multiplier, 2)

        category = user_states.get(message.chat.id)

        if category == 'waiting_for_weight_drying':
            carb_label = "<i>Углеводы:</i>"
        elif category == 'waiting_for_weight_mass':
            carb_label = "<i>Углеводы: от</i>"
        else:
            carb_label = "<i>Углеводы:</i>"

        result_message = f"<b>Результаты расчета для веса {weight} кг:</b>\n\n" \
                         f"<i>Белки:</i> {proteins} г\n" \
                         f"<i>Жиры:</i> {fats} г\n" \
                         f"{carb_label} {carbohydrates} г (в зависимости от вашей активности)\n" \
                         f"<i>Ккал:</i> {calories}"

        bot.send_message(message.chat.id, result_message, parse_mode="HTML")

        user_states[message.chat.id] = None
    except ValueError as e:
        bot.send_message(message.chat.id, f"Пожалуйста, введите корректный вес (в числовом формате)")


###
@bot.message_handler(func=lambda message: message.text == '🌟 Задать один вопрос')
def question_handler(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    
    buy_1question_button = types.InlineKeyboardButton("Купить вопрос (QIWI Кошелек)", callback_data='buy_1_question')
    promocode_1quest_button = types.InlineKeyboardButton("Использовать промокод", callback_data='use_promocode_for_1quest')
    another_banking_1quest_button = types.InlineKeyboardButton("Другой банкинг", callback_data='another_banking_for_1quest')

    buttons = [buy_1question_button, promocode_1quest_button, another_banking_1quest_button]

    for button in buttons:
        markup.add(button)

    question_description = """
    <i>Здесь вы можете получить ответы на свои вопросы от профессионалов.</i>
    <u>Стоимость вопроса:</u>
    - 20 гривен (UAH)
    - 50 рублей (RUB)
    """

    bot.send_message(message.chat.id, text=question_description, parse_mode="HTML", reply_markup=markup)
    
@bot.callback_query_handler(func=lambda call: call.data == 'buy_1_question')
def buy_1question_callback(call):
    user_id = call.from_user.id
    
    markup = types.InlineKeyboardMarkup()
    payment_for_1quest_url = QIWI_PAYMENT_URL_1QUEST.format(user_id=user_id)
    pay_1_quest_button = types.InlineKeyboardButton("Оплатить", url=payment_for_1quest_url)
    check_1_payment_button = types.InlineKeyboardButton("Проверить платеж", callback_data="check_payment_for_1quest")
    markup.add(pay_1_quest_button, check_1_payment_button)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Для оплаты нажмите на кнопку ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'check_payment_for_1quest')
def check_payment_for_1quest(call):
    user_id = call.from_user.id
    try:
        conn = sqlite3.connect(PAYMENTS_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        comment_1quest1 = f'%Оплата за один вопрос {user_id}%'  # Original variant
        comment_1quest2 = f'%Оплата_за_один_вопрос{user_id}%'
        comment_1quest3 = f'Оплата%20за%20один%20вопрос%{user_id}%' 

        cursor.execute(
            f"SELECT * FROM payments WHERE amount = 50 AND currency = 643 AND status = 'SUCCESS' AND"
            f"(comment LIKE ? OR comment LIKE ? OR comment LIKE ?)",
            (comment_1quest1, comment_1quest2, comment_1quest3)
        )
        payment_data_list = cursor.fetchall()
        
        for payment_data in payment_data_list:
            txn_id, amount, currency, date, comment, status, used = payment_data
            if not used:
                cursor.execute("UPDATE payments SET used = 1 WHERE txn_id = ?", (txn_id,))
                conn.commit()

                bot.send_message(call.message.chat.id, "✅ Оплата найдена.")
                ask_for_question(call.message)

            else:
                bot.send_message(call.message.chat.id, "❌ Оплата найдена, но уже использована.")

        if not payment_data_list:
            bot.send_message(call.message.chat.id, "❌ Совпадающая оплата не найдена.")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при проверке оплаты: {e}")

    finally:
        conn.close()

def process_and_use_promocode_for_1quest(message):
    user_id = message.from_user.id
    promo_code = message.text.strip()

    if promo_code in promo_codes_one_question:
        del promo_codes_one_question[promo_code]
        save_promo_codes_to_file(promo_codes_one_question, file_one_question)

        bot.send_message(user_id, "✅ Промокод успешно использован. Теперь вы можете задать вопрос.")
        ask_for_question(message)
    else:
        bot.send_message(user_id, "❌ Промокод недействителен или уже использован.")
        
@bot.callback_query_handler(func=lambda call: call.data == 'another_banking_for_1quest')
def another_banking_for_1quest(call):
    user_id = call.from_user.id

    admin_username = bot.get_chat(ANOTHER_BANKING_ID).username
    message_text = f"Вы выбрали другой банкинг." \
                   f"Для уточнения деталей свяжитесь с администратором @fitstarsupport."
    
    # You may want to add additional logic or messages here as needed
    bot.send_message(user_id, message_text)

@bot.callback_query_handler(func=lambda call: call.data == 'use_promocode_for_1quest')
def use_promocode_for_1question(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Пожалуйста, введите промокод:")
    bot.register_next_step_handler(call.message, process_and_use_promocode_for_1quest)


def ask_for_question(message):
    markup = types.InlineKeyboardMarkup()
    ask_button = types.InlineKeyboardButton("Задать вопрос", callback_data='ask_question')
    markup.add(ask_button)

    message = bot.send_message(message.chat.id, "Нажмите кнопку, чтобы задать ваш вопрос:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'ask_question')
def get_question_text(call):
    bot.send_message(call.message.chat.id, "Пожалуйста, введите ваш вопрос:")
    bot.register_next_step_handler(call.message, save_question)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    

def send_notification_to_admins(question_id, user_id, username, question_text, timestamp):
    for admin_id in ADMIN_IDS:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ответить", callback_data=f'reply_{question_id}'))

        user_info = f"Пользователь: {user_id} (@{username})\n"
        bot.send_message(admin_id, f"{user_info}Новый вопрос ({timestamp}):\n{question_text}", reply_markup=markup)

def save_question(message):
    question_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username

    # Check if the question_text is in the list of ignored phrases
    ignored_phrases = ['📘 Курс о наборе и сушке тела', '🌟 Задать один вопрос', '😎 Задать 10 вопросов', '🔢 БЖУ', '🙎‍♂️ Мой профиль', '🏋🏽‍♂️Cтандартные программы']

    if any(ignored_phrase.lower() in question_text.lower() for ignored_phrase in ignored_phrases):
        bot.send_message(message.chat.id, "Пожалуйста, введите ваш вопрос:")
        bot.register_next_step_handler(message, save_question)
    else:
        if not bot_db.user_exist(user_id):
            bot_db.add_user(user_id, username)

        questions_db = sqlite3.connect('db/questions.db')
        questions_cursor = questions_db.cursor()

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        questions_cursor.execute('INSERT INTO questions (user_id, username, question_text, timestamp) VALUES (?, ?, ?, ?)',
                                (user_id, username, question_text, current_time))
        questions_db.commit()

        question_id = questions_cursor.lastrowid

        questions_cursor.close()
        questions_db.close()

        bot.send_message(message.chat.id, "Наши админы получили ваш вопрос и уже работают над ответом.")

        send_notification_to_admins(question_id, user_id, username, question_text, current_time)
        
   
### 
@bot.message_handler(func=lambda message: message.text == '😎 Задать 10 вопросов')
def question_handler(message):   
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    
    buy_10questions_button = types.InlineKeyboardButton("Купить вопросы (QIWI Кошелек)", callback_data='buy_10_questions')
    promocode_10quests_button = types.InlineKeyboardButton("Использовать промокод", callback_data='use_promocode_for_10quests')
    another_banking_10quests_button = types.InlineKeyboardButton("Другой банкинг", callback_data='another_banking_for_10quests')
    
    
    buttons = [buy_10questions_button, promocode_10quests_button, another_banking_10quests_button]
    
    for button in buttons:
        markup.add(button)
    
    questions10_description = """

    <i>Здесь вы можете получить ответы на свои вопросы от профессионалов.</i>

    <u>Стоимость вопросов:</u>
    - 150 гривен (UAH)
    - 380 рублей (RUB)
    """

    bot.send_message(message.chat.id, text=questions10_description, parse_mode="HTML", reply_markup=markup)
   
@bot.callback_query_handler(func=lambda call: call.data == 'buy_10_questions')
def buy_10_questions_callback(call):
    user_id = call.from_user.id
    
    markup = types.InlineKeyboardMarkup()
    payment_for_10quests_url = QIWI_PAYMENT_URL_10QUESTS.format(user_id=user_id)
    pay_10_quests_button = types.InlineKeyboardButton("Оплатить", url=payment_for_10quests_url)
    check_10_payment_button = types.InlineKeyboardButton("Проверить платеж", callback_data="check_payment_for_10_quests")
    markup.add(pay_10_quests_button, check_10_payment_button)
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Для оплаты нажмите на кнопку ниже:", reply_markup=markup) 
    
@bot.callback_query_handler(func=lambda call: call.data == 'check_payment_for_10_quests')
def check_payment_for_10quests(call):
    user_id = call.from_user.id
    try:
        conn = sqlite3.connect(PAYMENTS_DB_PATH, check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM payments WHERE amount = 280 AND currency = 643 AND status = 'SUCCESS' AND comment = 'Оплата_за_10_вопросов_{user_id}'")
        payment_data = cursor.fetchone()

        if payment_data:
            txn_id, amount, currency, date, comment, status, used = payment_data
            if not used:
                cursor.execute("UPDATE payments SET used = 1 WHERE txn_id = ?", (txn_id,))
                conn.commit()

                bot.send_message(call.message.chat.id, "✅ Оплата найдена.")
                ask_for_questions(call.message)

            else:
                bot.send_message(call.message.chat.id, "❌ Оплата найдена, но уже использована.")

        else:
            bot.send_message(call.message.chat.id, "❌ Совпадающая оплата не найдена.")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при проверке оплаты: {e}")

    finally:
        conn.close()

    
@bot.callback_query_handler(func=lambda call: call.data == 'another_banking_for_10quests')
def another_banking_for_10quests(call):
    user_id = call.from_user.id

    admin_username = bot.get_chat(ANOTHER_BANKING_ID).username
    message_text = f"Вы выбрали другой банкинг." \
                   f"Для уточнения деталей свяжитесь с администратором @fitstarsupport."
    
    # You may want to add additional logic or messages here as needed
    bot.send_message(user_id, message_text)
  
def process_and_use_promocode_for_10quests(message):
    user_id = message.from_user.id
    promo_code = message.text.strip() 

    if promo_code in promo_codes_10_questions:
        del promo_codes_10_questions[promo_code]
        save_promo_codes_to_file(promo_codes_10_questions, file_10_questions)

        bot.send_message(user_id, "✅ Промокод успешно использован. Теперь вы можете задать вопросы.")
        ask_for_questions(message)
    else:
        bot.send_message(user_id, "❌ Промокод недействителен или уже использован.")   
    

@bot.callback_query_handler(func=lambda call: call.data == 'use_promocode_for_10quests')
def use_promocode_for_10questions(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Пожалуйста, введите промокод:")
    bot.register_next_step_handler(call.message, process_and_use_promocode_for_10quests)

def ask_for_questions(message):
    markup = types.InlineKeyboardMarkup()
    ask10_button = types.InlineKeyboardButton("Задать 10 вопросов", callback_data='ask_10_question')
    markup.add(ask10_button)
    bot.send_message(message.chat.id, "Нажмите кнопку, чтобы задать ваши вопросы:(❗Обратите внимание, что все ваши 10 вопросов должны быть в одном сообщении❗)", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'ask_10_question')
def get_questions_text(call):
    bot.send_message(call.message.chat.id, "Пожалуйста, введите ваши вопросы:")
    bot.register_next_step_handler(call.message, save_questions)
    bot.delete_message(call.message.chat.id, call.message.message_id)
      
def send_notification_to_admins(questions_id, user_id, username, question_text, timestamp):
    for admin_id in ADMIN_IDS:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Ответить", callback_data=f'reply_{questions_id}'))

        user_info = f"Пользователь: {user_id} (@{username})\n"
        bot.send_message(admin_id, f"{user_info}Новый вопрос ({timestamp}):\n{question_text}", reply_markup=markup)
               
def save_questions(message):
    question_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    
    ignored_10phrases = ['📘 Курс о наборе и сушке тела', '🌟 Задать один вопрос', '😎 Задать 10 вопросов', '🔢 БЖУ', '🙎‍♂️ Мой профиль', '🏋🏽‍♂️Cтандартные программы']

    if any(ignored_phrase.lower() in question_text.lower() for ignored_phrase in ignored_10phrases):
        bot.send_message(message.chat.id, "Пожалуйста, введите ваши вопросы:")
        bot.register_next_step_handler(message, save_questions)
    else:
        if not bot_db.user_exist(user_id):
            bot_db.add_user(user_id, username)

        questions_db = sqlite3.connect('db/questions.db')
        questions_cursor = questions_db.cursor()

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        questions_cursor.execute('INSERT INTO questions (user_id, username, question_text, timestamp, question_count) VALUES (?, ?, ?, ?, ?)',
                                (user_id, username, question_text, current_time, 10)) 
        questions_db.commit()
        
        questions_id = questions_cursor.lastrowid 

        questions_cursor.close()
        questions_db.close()

        bot.send_message(message.chat.id, "Наши админы получили ваши вопросы и уже работают над ответом")
        
        send_notification_to_admins(questions_id, user_id, username, question_text, current_time)
        

@bot.message_handler(func=lambda message: message.text == '🏋🏽‍♂️Cтандартные программы')
def training_handler(message):
    user_id = message.from_user.id
    if bot_db.user_has_course_access(user_id):
        bot.send_message(message.chat.id, "Сколько раз в неделю вы планируете заниматься?", reply_markup=training_keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к курсу. Купите курс, чтобы получить доступ к стандартным программам.", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ["twice_per_week", "thrice_per_week", "fourth_per_week"])
def callback_handler(call):
    if call.data == "twice_per_week":
        with open(r'training_info\2_times_a_week.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        bot.send_message(call.message.chat.id, content, parse_mode='HTML')
    elif call.data == "thrice_per_week":
        with open(r'training_info\3_times_a_week.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        bot.send_message(call.message.chat.id, content, parse_mode='HTML')  
    elif call.data == "fourth_per_week":
        with open(r'training_info\4_times_a_week.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        bot.send_message(call.message.chat.id, content, parse_mode='HTML')


#admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in ADMIN_IDS:
        bot.send_message(message.chat.id, "👨🏼‍💻Админ панель", reply_markup=admin_keyboard)
 
 
###       
@bot.message_handler(func=lambda message: message.text == '📊 Статистика' and message.from_user.id in ADMIN_IDS)
def send_statistics_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_users = types.KeyboardButton("👥 Статистика пользователей")
    item_admins = types.KeyboardButton("🛡️ Статистика администраторов")
    item_back = types.KeyboardButton("◀️ Назад")
    markup.row(item_users, item_admins)
    markup.row(item_back)
    bot.send_message(message.chat.id, "Выберите опцию для отображения статистики:", reply_markup=markup)


###
@bot.message_handler(func=lambda message: message.text == '👥 Статистика пользователей' and message.from_user.id in ADMIN_IDS)
def send_user_statistics(message):
    try:
        total_users = bot_db.cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        users_with_course_access = bot_db.cursor.execute("SELECT COUNT(*) FROM users WHERE has_course_access = 1").fetchone()[0]
        total_questions_count = get_total_questions_count()
        text = "👥 *Количество пользователей в базе данных:* {0}\n".format(total_users)
        text += "🔒 *Пользователи с доступом к курсу:* {0}\n".format(users_with_course_access)
        text += f"📊 Всего задано вопросов: {total_questions_count}"

        bot.send_message(message.chat.id, text, parse_mode='Markdown')

    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
        
def get_total_questions_count():
    if not hasattr(thread_locals, 'questions_cursor'):
        thread_locals.questions_cursor = questions_db.cursor()

    thread_locals.questions_cursor.execute('''
        SELECT SUM(question_count) FROM questions
    ''')
    total_questions_count = thread_locals.questions_cursor.fetchone()[0]
    return total_questions_count
   
   
###     
@bot.message_handler(func=lambda message: message.text == '🛡️ Статистика администраторов' and message.from_user.id in ADMIN_IDS)
def send_admin_statistics(message):
    admin_statistics = get_admin_statistics()

    statistics_text = "Статистика администраторов:\n"
    for admin in admin_statistics:
        statistics_text += f"👤 Админ @{admin['admin_username']} ответил на {admin['question_count']} вопросов\n"

    bot.send_message(message.chat.id, statistics_text)

def get_admin_statistics():
    if not hasattr(thread_locals, 'questions_cursor'):
        thread_locals.questions_cursor = questions_db.cursor()
        
    thread_locals.questions_cursor.execute('''
        SELECT admin_username, SUM(question_count) AS question_count
        FROM questions
        WHERE admin_username IS NOT NULL
        GROUP BY admin_username
    ''')

    admin_statistics = thread_locals.questions_cursor.fetchall()

    admin_statistics_list = [{'admin_username': admin[0], 'question_count': admin[1]} for admin in admin_statistics]

    return admin_statistics_list

questions_db.commit()


###
@bot.message_handler(func=lambda message: message.text == '◀️ Назад' and message.from_user.id in ADMIN_IDS)
def go_back_to_main_menu(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, "Возврат в админ панель.", reply_markup=admin_keyboard)
        

###            
@bot.message_handler(func=lambda message: message.text == '📩 Рассылка' and message.from_user.id in ADMIN_IDS)
def send_broadcast_prompt(message):

    bot.send_message(message.chat.id, 'Текст рассылки поддерживает разметку *HTML*, то есть:\n'
                                      '<b>*Жирный*</b>\n'
                                      '<i>_Курсив_</i>\n'
                                      '<pre>`Моноширный`</pre>\n'
                                      '<a href="ссылка-на-сайт">[Обернуть текст в ссылку](test.ru)</a>'.format(),
                             parse_mode="markdown")
    bot.send_message(message.chat.id, "Введите текст сообщения или нажмите /skip, чтобы пропустить:")
    bot.register_next_step_handler(message, process_broadcast_text)
def process_broadcast_text(message):
    bot.process_broadcast_text = message.text
    
    bot.send_message(message.chat.id, "Отправьте фото для добавления к сообщению или нажмите /skip, чтобы пропустить:")
    bot.register_next_step_handler(message, process_broadcast_photo)

def process_broadcast_photo(message):
    if message.text == '/skip':
        send_preview(message.chat.id)
    elif message.photo:
        bot.process_broadcast_photo = message.photo[0].file_id
        send_preview(message.chat.id)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте фото или нажмите /skip, чтобы пропустить.")

def send_preview(chat_id):
    markup = types.InlineKeyboardMarkup()
    preview_button = types.InlineKeyboardButton("📤 Отправить", callback_data="send_broadcast")
    cancel_button = types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_broadcast")
    markup.row(preview_button, cancel_button)
    markup.one_time_keyboard = True
    
    text = "📣 *Предварительный просмотр рассылки:*\n\n"
    text += bot.process_broadcast_text 
    
    if hasattr(bot, "process_broadcast_photo"):
        bot.send_photo(chat_id, bot.process_broadcast_photo, caption=text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "send_broadcast")
def send_broadcast_to_users_callback(call):
    text = bot.process_broadcast_text
    photo = bot.process_broadcast_photo if hasattr(bot, "process_broadcast_photo") else None
    send_broadcast_to_users(text, photo, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
def cancel_broadcast_callback(call):
    bot.send_message(call.message.chat.id, "Рассылка отменена.")
    del bot.process_broadcast_text
    if hasattr(bot, "process_broadcast_photo"):
        del bot.process_broadcast_photo
    admin_panel(call.message) 

def send_broadcast_to_users(text, photo, chat_id):
    try:
        user_ids = bot_db.get_all_user_ids() 
        for user_id in user_ids:
            try:
                if photo:
                    bot.send_photo(user_id, photo, caption=text, parse_mode='HTML')
                else:
                    bot.send_message(user_id, text, parse_mode='HTML')
            except Exception as e:
                print(f"Error sending message to user with ID {user_id}: {str(e)}")
        
        bot.send_message(chat_id, f"Рассылка успешно выполнена для {len(user_ids)} пользователей.")
    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")
        
replied_questions = set()


###
@bot.message_handler(func=lambda message: message.text == '🗂 Вигрузити БД' and message.from_user.id in ADMIN_IDS)
def get_DB(message):
    db_users = BotDb(BOT_DB_PATH)
    db_questions = QuestionsDb(QUESTIONS_DB_PATH)

    doc_users = db_users.get_DB()
    doc_questions = db_questions.get_questions_DB()
    bot.send_message(message.chat.id, "Процес вигрузки ...")
    bot.send_document(message.chat.id, doc_users, caption=f"База пользоватилей")
    bot.send_document(message.chat.id, doc_questions, caption=f"База вопросов")

    db_users.close()
    db_questions.close()


###
@bot.message_handler(func=lambda message: message.text == 'Вопросы')
def show_questions(message):
    questions_db = sqlite3.connect('db/questions.db')
    questions_cursor = questions_db.cursor()

    questions_cursor.execute('SELECT id, user_id, username, question_text, timestamp FROM questions WHERE answers_text IS NULL')
    questions = questions_cursor.fetchall()

    if not questions:
        bot.send_message(message.chat.id, "Новых вопросов в базе данных не найдено.")
        return

    for question in questions:
        question_id, user_id, username, question_text, timestamp = question
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Ответить", callback_data=f'reply_{question_id}'))

        user_info = f"Пользователь: {user_id} (@{username})\n"
        time_info = f"Время отправки: {timestamp}\n"
        bot.send_message(message.chat.id, f"{user_info}{time_info}Вопрос от пользователя:\n{question_text}", reply_markup=markup)

    questions_db.close()


###
@bot.message_handler(func=lambda message: message.text == 'Архив вопросов')
def show_archived_questions(message):
    questions_db = sqlite3.connect('db/questions.db')
    questions_cursor = questions_db.cursor()

    questions_cursor.execute('SELECT id, user_id, username, question_text, timestamp, answers_text FROM questions WHERE answers_text IS NOT NULL')
    questions = questions_cursor.fetchall()

    if not questions:
        bot.send_message(message.chat.id, "Архив вопросов пуст.")
        return

    for question in questions:
        question_id, user_id, username, question_text, timestamp, answer_text = question

        user_info = f"Пользователь: {user_id} (@{username})\n"
        time_info = f"Время отправки: {timestamp}\n"
        bot.send_message(message.chat.id, f"{user_info}{time_info}Вопрос от пользователя:\n{question_text}\nОтвет:\n{answer_text}")

    questions_db.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def reply_to_question(call):
    question_id = int(call.data.split('_')[1])

    if question_id in replied_questions:  
        bot.answer_callback_query(call.id, text="Вы уже ответили на этот вопрос", show_alert=True)
        return
    
    user_info = call.message.text.split('\n')[0]
    question_text = call.message.text[len(user_info):]

    bot.send_message(call.message.chat.id, f"Введите ответ на вопрос:\n{question_text}")
    bot.register_next_step_handler(call.message, lambda message: send_reply(message, question_id))
    
    replied_questions.add(question_id)

def create_reply_button(question_id):
    text = "Ответить" if question_id not in replied_questions else "Выполнено"
    button = InlineKeyboardButton(text, callback_data=f'reply_{question_id}')
    return button

def get_user_id_from_question(question_id):
    questions_db = sqlite3.connect('db/questions.db')
    questions_cursor = questions_db.cursor()

    questions_cursor.execute('SELECT user_id FROM questions WHERE id = ?', (question_id,))
    user_id = questions_cursor.fetchone()

    if user_id:
        return user_id[0]

    return None  

def send_reply(message, question_id):
    reply_text = message.text
    admin_username = message.from_user.username 

    # Check if the reply contains any ignored phrases
    ignored_phrases = ['📘 Курс', '🌟 Задать один вопрос', '😎 Задать 10 вопросов', '🔢 Рассчитать БЖУ', '🏋🏽‍♂️Cтандартные программы','🙎‍♂️ Мой профиль', '📊 Статистика', '🗂 Вигрузити БД', '📩 Рассылка', 'Вопросы', 'Згенерировать промокод', 'Архив вопросов', 'Назад в меню ↩️', ]
    if any(phrase in reply_text for phrase in ignored_phrases):
        bot.send_message(message.chat.id, "Введите ответ на вопрос:")
        bot.register_next_step_handler(message, lambda msg: send_reply(msg, question_id))
        return

    user_id = get_user_id_from_question(question_id)
    if user_id:
        bot.send_message(user_id, f"Ответ на ваш вопрос от админа @{admin_username}:\n{reply_text}")

    questions_db = sqlite3.connect('db/questions.db')
    questions_cursor = questions_db.cursor()
    questions_cursor.execute('UPDATE questions SET answers_text = ?, admin_username = ? WHERE id = ?', (reply_text, admin_username, question_id))
    questions_db.commit()
    questions_cursor.close()
    questions_db.close()

    bot.send_message(message.chat.id, "Ответ отправлен пользователю.")

  
###  

@bot.message_handler(func=lambda message: message.text == 'Згенерировать промокод' and message.from_user.id in ADMIN_IDS)
def generate_promo_code_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('Промокод для одного вопроса'))
    markup.add(types.KeyboardButton('Промокод для 10 вопросов'))
    markup.add(types.KeyboardButton('Промокод для курса'))
    markup.add(types.KeyboardButton('◀️ Назад'))
    
    user_states[message.chat.id] = 'generate_promo_code'
    bot.send_message(message.chat.id, "Выберите тип промокода:", reply_markup=markup)
    
def generate_promo_code():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

def save_promo_codes_to_file(promo_codes, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for promo_code, promo_code_type in promo_codes.items():
            file.write(f"{promo_code}\t{promo_code_type}\n")

promo_codes_one_question = {}
promo_codes_10_questions = {}
promo_codes_course = {}

file_one_question = "promocodes/promocodes.promo_codes_one_question.txt"
file_10_questions = "promocodes/promocodes.promo_codes_10_questions.txt"
file_course = "promocodes/promocodes.promo_codes_course.txt"


def load_promo_codes_from_file(filename, promo_codes):
    try:
        with open(filename, 'r', encoding='utf-8') as file: 
            for line in file:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    promo_code, promo_code_type = parts[0], parts[1]
                    promo_codes[promo_code] = promo_code_type
    except FileNotFoundError:
        pass
    
load_promo_codes_from_file(file_one_question, promo_codes_one_question)
load_promo_codes_from_file(file_10_questions, promo_codes_10_questions)
load_promo_codes_from_file(file_course, promo_codes_course)

def generate_promo_code_by_type(message, promo_code_type, promo_codes, file_name):
    promo_code = generate_promo_code()
    promo_codes[promo_code] = promo_code_type
    save_promo_codes_to_file(promo_codes, file_name)
    bot.send_message(message.chat.id, f"Сгенерирован промокод: {promo_code}\nТип промокода: {promo_code_type}", reply_markup=admin_keyboard)

@bot.message_handler(func=lambda message: message.text == 'Згенерировать промокод' and message.from_user.id in ADMIN_IDS)
def generate_promo_code_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    promo_code_types = ['Промокод для одного вопроса', 'Промокод для 10 вопросов', 'Промокод для курса']
    for promo_code_type in promo_code_types:
        markup.add(types.KeyboardButton(promo_code_type))
    
    markup.add(types.KeyboardButton('◀️ Назад'))
    
    user_states[message.chat.id] = 'generate_promo_code'
    bot.send_message(message.chat.id, "Выберите тип промокода:", reply_markup=markup)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'generate_promo_code' and message.text != '◀️ Назад')
def generate_specific_promo_code(message):
    promo_code_type = message.text
    
    if promo_code_type == '◀️ Назад':
        del user_states[message.chat.id]
        bot.send_message(message.chat.id, "Возврат в админ панель.", reply_markup=admin_keyboard)
        return

    if promo_code_type == 'Промокод для одного вопроса':
        generate_promo_code_by_type(message, promo_code_type, promo_codes_one_question, file_one_question)
    elif promo_code_type == 'Промокод для 10 вопросов':
        generate_promo_code_by_type(message, promo_code_type, promo_codes_10_questions, file_10_questions)
    elif promo_code_type == 'Промокод для курса':
        generate_promo_code_by_type(message, promo_code_type, promo_codes_course, file_course)


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print (e)
            
