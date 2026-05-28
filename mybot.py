import telebot
from telebot import types
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

TOKEN = '8851515467:AAELflDDkFhTzCmXzDSKKRsgUWKf1eOIsXk' 
ADMIN_ID = 7048680111

bot = telebot.TeleBot(TOKEN)
DB_FILE = 'users.txt'

# Заглушка для веб-сервера Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), HealthCheckHandler)
    server.serve_forever()

def save_user_info(user_id, first_name, username):
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f: pass
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    user_exists = False
    for line in lines:
        if line.startswith(f"ID: {user_id} |"):
            user_exists = True
            break
    if not user_exists:
        username_str = f"@{username}" if username else "Нет юзернейма"
        new_line = f"ID: {user_id} | Имя: {first_name} | Ссылка: {username_str}\n"
        with open(DB_FILE, 'a', encoding='utf-8') as f:
            f.write(new_line)

def get_users_count():
    if not os.path.exists(DB_FILE): return 0
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    return len(lines)

def get_main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    site_button = types.InlineKeyboardButton(text="Начать зарабатывать 💰", url="https://taskpay.ru")
    # Добавлена ваша кнопка со ссылкой на ТГ-канал
    channel_button = types.InlineKeyboardButton(text="♦️Мой ТГК с Советами♦️", https://t.me/+YdiIQ74RknBmYmZi")
    faq_button = types.InlineKeyboardButton(text="F.A.Q. ❓", callback_data="open_faq")
    
    # Добавляем все три кнопки в меню по очереди
    markup.add(site_button, channel_button, faq_button)
    return markup

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id == ADMIN_ID:
        count = get_users_count()
        bot.send_message(message.chat.d, f"📊 **Статистика бота:**\nВсего уникальных пользователей: {count}\n\n💬 `/users` — посмотреть список текстом\n📁 `/getfile` — скачать файл базы данных")

@bot.message_handler(commands=['users'])
def show_users_list(message):
    if message.from_user.id == ADMIN_ID:
        if not os.path.exists(DB_FILE) or get_users_count() == 0:
            bot.send_message(message.chat.id, "👥 Список пользователей пока пуст.")
            return
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            users_data = f.read()
        if len(users_data) > 4000:
            for x in range(0, len(users_data), 4000):
                bot.send_message(message.chat.id, f"👥 **Список пользователей (часть):**\n\n{users_data[x:x+4000]}")
        else:
            bot.send_message(message.chat.id, f"👥 **Список пользователей:**\n\n{users_data}")

@bot.message_handler(commands=['getfile'])
def send_db_file(message):
    if message.from_user.id == ADMIN_ID:
        if not os.path.exists(DB_FILE) or get_users_count() == 0:
            bot.send_message(message.chat.id, "📁 Файл базы данных пуст или еще не создан.")
            return
        with open(DB_FILE, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📁 Полный файл базы данных пользователей (users.txt)")

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
    video1_button = types.InlineKeyboardButton(text="Как зарегистрироваться 📺", url="https://youtu.be/-kwNwb_SXls?si=7o3ZooziWDYKs23p")
    video2_button = types.InlineKeyboardButton(text="Как делать задания 📺", url="https://youtu.be/U6aUUtqCQfU?si=s63YKnjZsRIyUWHt")
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
    # Запуск веб-сервера в отдельном потоке для Render
    threading.Thread(target=run_health_server, daemon=True).start()
    bot.infinity_polling()
