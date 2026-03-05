import telebot
from telebot import types
import datetime
import time
import threading
import os

bot = telebot.TeleBot ("8662761621:AAEuB0yRJ2dlJqgfZH0QpWVMQ3gvHlUM7f4")
ticket_counter = 0
ADMIN_ID = 1600262158
active_chats = {}
ticket_messages = {}
canceled_tickets = set()

if not os.path.exists("logs"):
    os.makedirs("logs")

def log_message(ticket_id, text):
    with open(f"logs/logs{ticket_id}.txt", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def main_menu(name):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_support = types.InlineKeyboardButton("🧑‍💻 Зв'язок з службою підтримки", callback_data="support")
    btn_recovery = types.InlineKeyboardButton("🔑 Відновити пароль до акаунту", url="https://www.staff-rp.com.ua/")
    btn_site = types.InlineKeyboardButton("🌐 Сайт", url="https://www.staff-rp.com.ua/")
    btn_forum = types.InlineKeyboardButton("📔 Форум", url="https://forum.staff-rp.com.ua/index.php?forums/")
    btn_shop = types.InlineKeyboardButton("🏪 Магазин", url="https://www.staff-rp.com.ua/")
    markup.add(btn_support, btn_recovery)
    markup.row(btn_site, btn_forum, btn_shop)
    text = (
        f"Вітаю, {name}!\n\n"
        "Я — твій віртуальний помічник у світі "
        "<b>STAFF RP.</b>\n\n"
        "Для початку, обери бажану дію:"
    )
    return text, markup

@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    photo_path = "img/start.png"
    text, markup = main_menu(name)
    with open(photo_path, 'rb') as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )

def send_operator_messages(user_id, ticket_id, user_name, chat_id, chat_message_id):
    accept_markup = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Прийняти", callback_data=f"accept_{ticket_id}_{user_id}_{chat_id}_{chat_message_id}")
    accept_markup.add(btn_accept)
    bot.send_message(
        ADMIN_ID,
        f"Новий тікет #{ticket_id}\nВід: @{user_name}",
        reply_markup=accept_markup
    )
    with open(f"logs/logs{ticket_id}.txt", "w", encoding="utf-8") as f:
        f.write(f"Новий тікет #{ticket_id}\nВід: @{user_name}\n")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global ticket_counter
    name = call.from_user.first_name
    username = call.from_user.username or name
    current_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    hour = current_time.hour + current_time.minute / 60

    if call.data == "support":
        if 10.5 <= hour <= 21:
            ticket_counter += 1
            markup = types.InlineKeyboardMarkup()
            btn_cancel = types.InlineKeyboardButton(
                "❌ Скасувати тікет",
                callback_data=f"cancel_ticket_{ticket_counter}_{call.from_user.id}_{username}_{call.message.chat.id}_{call.message.message_id}"
            )
            markup.add(btn_cancel)
            text = (
                f"Вітаю, {name}!\n\n"
                f"Номер тікету: #{ticket_counter}\n"
                f"Статус: Очікується з'єднання з оператором..."
            )
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
            ticket_messages[ticket_counter] = (call.message.chat.id, call.message.message_id, text)
            threading.Thread(target=send_operator_messages, args=(call.from_user.id, ticket_counter, username, call.message.chat.id, call.message.message_id)).start()
        else:
            markup = types.InlineKeyboardMarkup()
            btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")
            markup.add(btn_back)
            text = (
                f"Вітаю, {username}!\n\n"
                f"Графік роботи:\nз 10:30 до 21:00\n\n"
                f"<i>Служба тех. підтримки STAFF RP не на зв'язку.\n"
                f"Зверніться до нас пізніше або згідно з графіком роботи.</i>"
            )
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )

    elif call.data.startswith("cancel_ticket_"):
        parts = call.data.split("_")
        ticket_id = int(parts[2])
        user_name_from_ticket = parts[4]
        chat_id_from_ticket, chat_message_id_from_ticket, old_caption = ticket_messages[ticket_id]
        canceled_tickets.add(ticket_id)
        caption = old_caption.split("Статус:")[0] + "Статус: З'єднання з оператором скасовано."
        markup = types.InlineKeyboardMarkup()
        btn_back = types.InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")
        markup.add(btn_back)
        bot.edit_message_caption(
            chat_id=chat_id_from_ticket,
            message_id=chat_message_id_from_ticket,
            caption=caption,
            reply_markup=markup,
            parse_mode="HTML"
        )
        bot.send_message(ADMIN_ID, f"Тікет: #{ticket_id} було скасовано @{user_name_from_ticket}")
        log_message(ticket_id, f"Тікет #{ticket_id} скасовано @{user_name_from_ticket}")
        if ticket_id in active_chats:
            del active_chats[ticket_id]

    elif call.data == "back_to_start":
        text, markup = main_menu(name)
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=text,
            reply_markup=markup,
            parse_mode="HTML"
        )

    elif call.data.startswith("accept_"):
        parts = call.data.split("_")
        ticket_id = int(parts[1])
        if ticket_id in canceled_tickets:
            bot.answer_callback_query(call.id, text="Тікет скасовано, прийняти неможливо")
            return
        user_id = int(parts[2])
        chat_id_from_ticket = int(parts[3])
        chat_message_id_from_ticket = int(parts[4])
        active_chats[ticket_id] = (ADMIN_ID, user_id)
        _, _, old_caption = ticket_messages[ticket_id]
        new_caption = old_caption.split("Статус:")[0] + "Статус: З'єднання з оператором встановлено..."
        bot.edit_message_caption(
            chat_id=chat_id_from_ticket,
            message_id=chat_message_id_from_ticket,
            caption=new_caption,
            reply_markup=None,
            parse_mode="HTML"
        )
        bot.send_message(user_id, f"Оператор Юрій Архангел підключився до вашого тікету.")
        log_message(ticket_id, "Оператор Юрій Архангел підключився до тікету")
        def follow_up():
            time.sleep(5)
            bot.send_message(user_id, "Вітаю! Мене звати Юрій, чим я можу Вам допомогти?")
        threading.Thread(target=follow_up).start()
        bot.answer_callback_query(call.id, text="Тікет прийнято")

@bot.message_handler(func=lambda message: True)
def forward_messages(message):
    if message.from_user.id == ADMIN_ID:
        if message.text == "/stop":
            for ticket_id, (admin_id, user_id) in list(active_chats.items()):
                if admin_id == ADMIN_ID:
                    photo = open("img/start.png", 'rb')
                    markup = types.InlineKeyboardMarkup()
                    btn_back = types.InlineKeyboardButton("⬅️ Повернутися в головне меню", callback_data="back_to_start")
                    btn_support = types.InlineKeyboardButton("🧑‍💻 Зв'язок з службою підтримки", callback_data="support")
                    markup.add(btn_back)
                    markup.add(btn_support)
                    chat_id, msg_id, old_caption = ticket_messages.get(ticket_id, (None, None, ""))
                    user_name = old_caption.split("Від: @")[-1].split("\n")[0] if old_caption else "Користувач"
                    bot.send_photo(
                        user_id,
                        photo,
                        caption=f" {user_name}!\n\nВаше звернення було зачинено оператором.\n\nБудь ласка, оберіть бажану дію:",
                        reply_markup=markup
                    )
                    log_message(ticket_id, "Тікет закрито")
                    del active_chats[ticket_id]
            return
        sent = False
        for ticket_id, (admin_id, user_id) in active_chats.items():
            if admin_id == ADMIN_ID:
                bot.send_message(user_id, message.text)
                log_message(ticket_id, f"Відповідь від Адміністратора: {message.text}")
                sent = True
        if not sent:
            bot.send_message(ADMIN_ID, "Наразі ви не підключені до жодного тікету.")
    else:
        for ticket_id, (admin_id, user_id) in active_chats.items():
            if user_id == message.from_user.id:
                bot.send_message(ADMIN_ID, f"Повідомлення від @{message.from_user.username or message.from_user.first_name}: {message.text}")
                log_message(ticket_id, f"Повідомлення від @{message.from_user.username or message.from_user.first_name}: {message.text}")
                return
        bot.send_message(message.chat.id, "Я не розумію вас. Якщо ви заблудились - використайте команду: /start")

bot.polling(none_stop=True)
