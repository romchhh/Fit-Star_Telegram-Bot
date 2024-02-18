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
            f"SELECT * FROM payments WHERE amount = 500 AND currency = 643 AND "
            f"(comment LIKE ? OR comment LIKE ? OR comment LIKE ?)",
            (comment_template, comment_template2, comment_template3)
        )
        payment_data_list = cursor.fetchall()

        for payment_data in payment_data_list:
            txn_id, amount, currency, date, comment, used = payment_data
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