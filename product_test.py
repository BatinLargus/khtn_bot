from functools import partial
import telebot
from telebot import types
import sqlite3
from tkinter import messagebox

users = {}
token = '7560294327:AAF5KyOSYzwoBnpQXZPHMtepJZZMmUuq2dc'
# users = {}
bot = telebot.TeleBot(token)

init_mes = None

state = True

state1 = True

functions = ["Посмотреть пользователей", "Написать сообщение"]
topics = ["Общий вопрос", "Заключение договора", "Документооборот", "Бизнес-модель", "Инвестиционное обеспечение",
          "Расторжение договора"]
menu_func = ["Выйти из чата", "Поменять тему"]

sender = []
recipient = []
temp_dems = []


def add_users():
    new_connect = connect_db("khtn_db.db")
    sql = new_connect.execute_sql(f"select * from users")
    for line in sql.fetchall():
        tg_id, tg_tag = line
        users[tg_tag] = tg_id


class connect_db:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connector = sqlite3.connect(self.db_name)
        self.cursor = self.connector.cursor()

    def execute_sql(self, sql_text):
        try:
            self.sql_text = sql_text
            return self.cursor.execute(self.sql_text)

        except:
            messagebox.showerror("Ошибка!", "Невозможно выполнить запрос!")

    def close_db(self):
        self.connector.commit()
        self.cursor.close()
        self.connector.close()


def chat_functions():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for func in menu_func:
        menu.add(types.KeyboardButton(func))

    return menu


def user_list():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for user in users:
        menu.add(types.KeyboardButton(user))

    return menu


def choose_topic():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for topic in topics:
        menu.add(types.KeyboardButton(topic))

    return menu


def choice_menu():
    menu = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for choice in functions:
        menu.add(types.KeyboardButton(choice))

    return menu


@bot.message_handler(commands=['start'])
def start(message):
    global sender, recipient
    sender = "@" + message.from_user.username, message.chat.id
    menu = choice_menu()
    bot.send_message(sender[1],
                     "Привет, {0.first_name}! Выберете опцию из предложенных ниже:  ".format(message.from_user),
                     reply_markup=menu)


@bot.message_handler(content_types=['text'])
def user_message(message):
    global sender
    if (sender[1] != message.chat.id): sender = message.from_user.id, message.chat.id
    if message.text == "Написать сообщение":
        menu = user_list()
        bot.send_message(message.chat.id, "Выберете пользователя, которому вы хотите отправить сообщение: ",
                         reply_markup=menu)
        bot.register_next_step_handler(message, messenger)

    elif message.text == "Посмотреть пользователей":
        bot.send_message(sender[1], "Вот список доступных пользователей! ")
        for pers in users:
            bot.send_message(sender[1], pers)


def messenger(message):
    global recipient

    menu = choose_topic()

    if message.text not in users:
        bot.send_message(sender[1], "Такого пользователя нет в системе! ")

    else:
        recipient = message.text, users[message.text]

        topic = bot.send_message(sender[1], "Отлично! Выберем тему для Вашего разговора: ", reply_markup=menu)
        bot.register_next_step_handler(topic, generate_first_message)


def generate_first_message(message):
    topic = message.text

    bot.send_message(sender[1], "Отлично, что ему отправим: ", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, partial(ask_for_permission, recip=recipient, send=sender, topic=topic))


def ask_for_permission(message, recip, send, topic):
    letter = message.text
    msg = bot.send_message(recip[1],
                           f"С вами хочет начать диалог: {sender[0]} на тему {topic}. Начать разговор? (Да/Нет)")
    bot.register_next_step_handler(msg, partial(msgr_send_message, recip=recip, send=send, letr=letter, msg=msg,
                                                topic=topic))


def msgr_send_message(message, recip, send, letr, msg, topic):
    if "да" in message.text.lower():
        bot.send_message(recip[1], letr)
        bot.send_message(send[1], f"-----ТЕМА РАЗГОВОРА: {topic}-----")
        bot.send_message(send[1], "Да начнется чат!")

        bot.send_message(recip[1], f"-----ТЕМА РАЗГОВОРА: {topic}-----")
        bot.send_message(recip[1], "Да начнется чат!")

        if state:
            summon()
        else:
            start(message)



    elif "нет" in message.text.lower():
        bot.send_message(send[1], "Запрос отклонен! ")
        bot.send_message(recip[1], "Запрос отклонен! ")

    else:
        bot.send_message(send[1], "Простите, боюсь, что я вас не понял. Повторите еще раз! ")
        start(message)


def summon():
    bot.clear_step_handler_by_chat_id(sender[1])
    bot.clear_step_handler_by_chat_id(recipient[1])

    if state:
        bot.register_next_step_handler_by_chat_id(sender[1], func1) or bot.register_next_step_handler_by_chat_id(
            recipient[1], func2)


def func1(message):
    global state

    if not state:
        start(message)

    else:
        menu = chat_functions()
        if message.text == "Выйти из чата":
            bot.send_message(recipient[1], f"Разговор закончен по инициативе: {sender[0]}",
                             reply_markup=types.ReplyKeyboardMarkup())
            state = not state
            start(message)

        elif message.text == "Поменять тему":
            menu = choose_topic()
            topic = bot.send_message(message.chat.id, "Выберете тему для смены: ", reply_markup=menu)
            bot.register_next_step_handler(topic, generate_first_message)

        else:
            bot.send_message(recipient[1], message.text, reply_markup=menu)
            summon()


def func2(message):
    global sender
    global recipient

    global state

    if not state:
        start(message)

    else:
        menu = chat_functions()
        if message.text == "Выйти из чата" and state:
            bot.send_message(sender[1], f"Разговор закончен по инициативе: {recipient[0]}",
                             reply_markup=types.ReplyKeyboardMarkup())
            state = not state
            start(message)

        elif message.text == "Выйти из чата" and not state:
            start(message)

        elif message.text == "Поменять тему":
            temp = recipient
            recipient = sender
            sender = temp
            menu = choose_topic()
            topic = bot.send_message(message.chat.id, "Выберете тему для смены: ", reply_markup=menu)
            bot.register_next_step_handler(topic, generate_first_message)

        else:
            bot.send_message(sender[1], message.text, reply_markup=menu)
            summon()


add_users()

bot.polling()



