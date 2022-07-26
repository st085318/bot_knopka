import os
import re

import telebot
from telebot import types

bot = telebot.TeleBot('')


def make_markup():
    markup = types.InlineKeyboardMarkup()
    button_cik = types.InlineKeyboardButton("Найти мой УИК", callback_data="cik")
    button_candidates = types.InlineKeyboardButton("Посмотреть кандидатов", callback_data="candidates")
    markup.add(button_cik)
    markup.add(button_candidates)
    return markup


def greeting(message):
    bot.send_message(message.from_user.id, "Привет! Я бот! Ты можешь найти свой УИК")
    bot.send_message(message.from_user.id, "Что теперь будем делать?", reply_markup=make_markup())
    bot.send_message(message.from_user.id, "Инициатива создания проекта исходит от ПП Новые Люди")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    greeting(message)

@bot.callback_query_handler(lambda callback_query: callback_query.data == "cik")
def find_cik(callback_query: types.CallbackQuery):
    bot.answer_callback_query(callback_query.id)
    bot.send_message(callback_query.from_user.id, "введите адрес в специальном формате:")

@bot.message_handler(content_types=['text'])
def change_link(message):
    pass


bot.infinity_polling()
