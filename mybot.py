import telebot
from telebot import types
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import psycopg2  # Библиотека для работы с PostgreSQL
import io

TOKEN = '8851515467:AAELflDDkFhTzCmXzDSKKRsgUWKf1eOIsXk' 
ADMIN_ID = 7048680111

# Строка подключения к Supabase с добавленным параметром sslmode=disable против ошибок соединений
DB_URI = "postgresql://postgres:o8llCYjtDOIgRRWL@db.bjrwsrvvyeueawxwbstd.supabase.co:5432/postgres?sslmode=disable"

bot = telebot.TeleBot(TOKEN)

# Заглушка для веб-сервера Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), HealthCheckHandler)
    server.serve_forever()

# Функция инициализации таблицы в базе данных
def init_db():
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            first_name TEXT,
            username TEXT
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def save_user_info(user_id, first_name, username):
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        
        # ON CONFLICT DO NOTHING предотвращает дублирование пользователей
        cursor.execute("""
            INSERT INTO users (user_id, first_name, username)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING;
        """, (user_id, first_name, username))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при работе с БД: {e}")

def get_users_count():
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users;")
        count = cursor.fetchone()[0] # Исправлено: извлекаем число из кортежа напрямую
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Ошибка при получении количества: {e}")
        return 0

def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    site_button = types.InlineKeyboardButton(text="Начать зарабатывать 💰", url="https://taskpay.ru")
    channel_button = types.InlineKeyboardButton(text="♦️Мой ТГК с Советами♦️", url="https://t.me/+YdiIQ74RknBmYmZi")
    faq_button = types.InlineKeyboardButton(text="F.A.Q. ❓", callback_data="open_faq")
    markup.add(site_button, channel_button, faq_button)
    return markup

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        bot.send_message(message.chat.id, f"📊 **Статистика бота:**\nВсего уникальных пользователей: {count}\n\n💬 `/users` — посмотреть список текстом\n📁 `/getfile` — скачать файл базы данных")

@bot.message_handler(commands=['users'])
def show_users_list(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        if count == 0:
            bot.send_message(message.chat.id, "👥 Список пользователей пока пуст.")
            return
        
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name, username FROM users;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        users_list = []
        for row in rows:
            u_id, name, uname = row
            username_str = f"@{uname}" if uname else "Нет юзернейма"
            users_list.append(f"ID: {u_id} | Имя: {name} | Ссылка: {username_str}")
        
        users_data = "\n".join(users_list)
        
        if len(users_data) > 4000:
            for x in range(0, len(users_data), 4000):
                bot.send_message(message.chat.id, f"👥 **Список пользователей (часть):**\n\n{users_data[x:x+4000]}")
        else:
            bot.send_message(message.chat.id, f"👥 **Список пользователей:**\n\n{users_data}")

@bot.message_handler(commands=['getfile'])
def send_db_file(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        if count == 0:
            bot.send_message(message.chat.id, "📁 База данных пуста.")
            return
        
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, first_name, username FROM users;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Генерируем виртуальный файл в памяти для отправки в Telegram
        file_buffer = io.BytesIO()
        for row in rows:
            u_id, name, uname = row
            username_str = f"@{uname}" if uname else "Нет юзернейма"
            line = f"ID: {u_id} | Имя: {name} | Ссылка: {username_str}\n"
            file_buffer.write(line.encode('utf-8'))
        
        file_buffer.seek(0)
        file_buffer.name = "users.txt"
        
        bot.send_document(message.chat.id, file_buffer, caption="📁 Полный файл базы данных пользователей (users.txt)")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    username = message.from_user.username
    save_user_info(user_id, name, username)
    text = f"Привет, {name}! 👋 Вот ссылка🔗 на сайт на котором я работаю и зарабатываю деньги!👇"
    bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "open_faq")
def callback_faq(call):
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception: pass
    markup = types.InlineKeyboardMarkup(row_width=1)
    video1_button = types.InlineKeyboardButton(text="Как зарегистрироваться 📺", url="https://youtu.be")
    video2_button = types.InlineKeyboardButton(text="Как делать задания 📺", url="https://youtu.be")
    back_button = types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")
    markup.add(video1_button, video2_button, back_button)
    name = call.from_user.first_name
    faq_text = f"Привет, {name}! Я смотрю ты хочешь подзаработать деньжат на сайте TaskPay и не знаешь как? Вот ссылки на мои ролики на YouTube где я всё объяснил и рассказал:👇"
    bot.send_message(call.message.chat.id, faq_text, reply_markup=markup)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def callback_back_to_main(call):
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception: pass
    name = call.from_user.first_name
    text = f"Привет, {name}! 👋 Вот ссылка🔗 на сайт на котором я работаю и зарабатываю деньги!👇"
    bot.send_message(call.message.chat.id, text, reply_markup=get_main_menu_keyboard())
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    # Автоматически создаем таблицу пользователей при первом запуске
    init_db()
    # Запуск веб-сервера для Render
    threading.Thread(target=run_health_server, daemon=True).start()
    bot.infinity_polling()
