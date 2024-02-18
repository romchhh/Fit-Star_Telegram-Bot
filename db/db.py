import sqlite3
from datetime import datetime
import threading
import openpyxl

class BotDb:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TEXT,
            has_course_access INTEGER DEFAULT 0
        )''')
        self.conn.commit()

    def user_exist(self, user_id):
        with self.lock:
            result = self.cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            return bool(len(result.fetchall()))
        
    def get_all_user_ids(self):
        with self.lock:
            result = self.cursor.execute("SELECT id FROM users")
            return [row[0] for row in result.fetchall()]

    def add_user(self, user_id, username):
        with self.lock:
            try:
                join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cursor.execute("INSERT INTO users (id, username, join_date) VALUES (?, ?, ?)", (user_id, username, join_date))
                self.conn.commit()
                print(f"User {username} with ID {user_id} added to the database at {join_date}")
            except Exception as e:
                print(f"Error adding user to the database: {e}")
                
    def user_has_course_access(self, user_id):
        with self.lock:
            result = self.cursor.execute("SELECT has_course_access FROM users WHERE id = ?", (user_id,))
            access = result.fetchone()
            if access:
                return bool(access[0])
            else:
                return False

    def set_course_access(self, user_id):
        with self.lock:
            self.cursor.execute("UPDATE users SET has_course_access = 1 WHERE id = ?", (user_id,))
            self.conn.commit()     
            
    def get_user_data(self, user_id):
        with self.lock:
            result = self.cursor.execute("SELECT username, join_date, has_course_access FROM users WHERE id = ?", (user_id,))
            user_data = result.fetchone()
            if user_data:
                username, join_date, has_course_access = user_data
                return {
                    'username': username,
                    'join_date': join_date,
                    'has_course_access': bool(has_course_access),
                }
            else:
                return None  
            
    def get_DB(self):
        file_name = 'users_info.xlsx'
        wb = openpyxl.Workbook()
        sheet = wb.active

        user_ids = self.get_all_user_ids()
        for user_id in user_ids:
            user_data = self.get_user_data(user_id)
            if user_data:
                row_data = [user_id] + list(user_data.values())
                sheet.append(row_data)

        wb.save(file_name)

        doc = open(file_name, 'rb')
        return doc   

    def close(self):
        self.conn.close()
        
        
class QuestionsDb:
    
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()
    
        self.questions_conn = sqlite3.connect(db_file, check_same_thread=False)
        self.questions_cursor = self.questions_conn.cursor()
        
        self.questions_cursor.execute('''
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
        self.questions_conn.commit()


    def get_all_question_ids(self):
        self.questions_cursor.execute("SELECT id FROM questions")
        question_ids = [row[0] for row in self.questions_cursor.fetchall()]
        return question_ids

    def get_question_data(self, question_id):
        self.questions_cursor.execute("SELECT * FROM questions WHERE id=?", (question_id,))
        question_data = self.questions_cursor.fetchone()
        if question_data:
            column_names = [description[0] for description in self.questions_cursor.description]
            return dict(zip(column_names, question_data))
        else:
            return None

    def get_questions_DB(self):
        file_name = 'questions_info.xlsx'
        wb = openpyxl.Workbook()
        sheet = wb.active

        question_ids = self.get_all_question_ids()
        for question_id in question_ids:
            question_data = self.get_question_data(question_id)
            if question_data:
                row_data = [question_data.get('id', ''), question_data.get('user_id', ''),
                            question_data.get('username', ''), question_data.get('question_text', ''),
                            question_data.get('answers_text', ''), question_data.get('timestamp', ''),
                            question_data.get('question_count', ''), question_data.get('admin_username', '')]
                sheet.append(row_data)

        wb.save(file_name)

        doc = open(file_name, 'rb')
        return doc    
    
    def close(self):
        self.questions_conn.close() 


class PaymentsDb:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS payments
                               (txn_id TEXT PRIMARY KEY, amount REAL, currency TEXT, date TEXT, comment TEXT, status TEXT)''')
        self.conn.commit()

    def payment_exists(self, txn_id):
        self.cursor.execute("SELECT * FROM payments WHERE txn_id=?", (txn_id,))
        return self.cursor.fetchone() is not None

    def insert_payment(self, txn_id, amount, currency, date, comment, status):
        self.cursor.execute("INSERT INTO payments (txn_id, amount, currency, date, comment, status) VALUES (?, ?, ?, ?, ?, ?)",
                            (txn_id, amount, currency, date, comment, status))
        self.conn.commit()