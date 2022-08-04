import parser
import telebot
from telebot import types
from addresses import adds
from keys import TELEGRAM_API_KEY

bot = telebot.TeleBot(TELEGRAM_API_KEY)
NEW_PEOPLE_URL = "https://newpeople.ru/"
address = {"county": "", "district": "", "street": "", "house": "", "building": ""}
MESSAGE_ID = 0
PREV_MSG_ID = None
CHAT_ID = 0
change = {'ш.': "ШОССЕ", 'наб.': "НАБ.", 'аллея': "АЛЛЕЯ", 'ул.': "УЛ.", 'кв-л': "КВАРТАЛ", 'туп.': "ТУП.",
          'б-р': "БУЛЬВ.", 'пр-т': "ПРОСП.", 'мкр.': "", 'линия': "ЛИНИЯ", 'пр-д': "ПР.", 'пер.': "ПЕР."}
set_probably_addresses = {}
my_candidats = []
quantity_streets_once = 8


# Алешинская -> Алшкинская
# TODO: удалять ё
def address_to_url_str():
    try:
        add = f"Город Москва {address['county']} {address['district']} "
        street = address['street']
        for suffix in change.keys():
            if street.find(suffix) != -1:
                street = street[:street.find(suffix) - 2] + " " + change[suffix]
        return add + street.replace('ё', '').upper() + " " + address["house"]
    except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


def address_to_str():
    try:
        add = f""
        for k in address.keys():
            if address[k] != "":
                add += address[k] + ", "
        add = add[:-2]
        return add
    except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


def make_markup_swipe_candidates(page):
    markup = types.InlineKeyboardMarkup()
    # markup.add(types.InlineKeyboardButton("Вперед>>", callback_data=f"{direction}swipe{page}"))
    # markup.add(types.InlineKeyboardButton("<<Назад", callback_data=f"{direction}swipe{page}"))
    markup.row(types.InlineKeyboardButton("<<Назад", callback_data=f"-1swipeC{page}"),
               types.InlineKeyboardButton("Закрыть", callback_data=f"close"),
               types.InlineKeyboardButton("Вперед>>", callback_data=f"1swipeC{page}"))
    return markup


def make_markup():
    markup = types.InlineKeyboardMarkup()
    button_cik = types.InlineKeyboardButton("Найти мой УИК", callback_data="find_cik")
    # button_candidates = types.InlineKeyboardButton("Посмотреть кандидатов", callback_data="candidates")
    markup.add(button_cik)
    # markup.add(button_candidates)
    return markup


def make_county_markup():
    markup = types.InlineKeyboardMarkup()
    for c in adds.keys():
        callback = "county" + str(c)[:7]
        markup.add(types.InlineKeyboardButton(str(c), callback_data=callback))
    markup.add(types.InlineKeyboardButton("Закрыть", callback_data=f"close"))
    return markup


def make_district_markup(county):
    markup = types.InlineKeyboardMarkup()
    for district in adds[county].keys():
        markup.add(types.InlineKeyboardButton(str(district), callback_data="district" + str(district)[:10]))
    markup.add(types.InlineKeyboardButton("Закрыть", callback_data=f"close"))
    return markup


def make_street_markup(county, district, num_street_page=0):
    try:
        markup = types.InlineKeyboardMarkup()
        shift = 0
        global quantity_streets_once
        for c in adds[county][district][num_street_page:num_street_page + quantity_streets_once]:
            # TODO:rewrite on num
            callback = "street" + str(shift)
            markup.add(types.InlineKeyboardButton(str(c), callback_data=callback))
            shift += 1
        if num_street_page + 7 >= len(adds[county][district]) - 1:
            markup.add(types.InlineKeyboardButton("Моей улицы нет", callback_data="dont_find_street"))
        markup.row(types.InlineKeyboardButton("<<Назад", callback_data=f"-1swipeS{num_street_page}"),
                   types.InlineKeyboardButton("Закрыть", callback_data=f"close"),
                   types.InlineKeyboardButton("Вперед>>", callback_data=f"1swipeS{num_street_page}"))
        return markup
    except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return None


def make_choose_add_markup():
    try:
        markup = types.InlineKeyboardMarkup()
        for add_info in set_probably_addresses.keys():
            callback = "uik" + str(set_probably_addresses[add_info]["id"])
            markup.add(types.InlineKeyboardButton(add_info, callback_data=callback))
        markup.add(types.InlineKeyboardButton("Моего дома нет", callback_data="dont_find_street"))
        return markup
    except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return None


def delete_message(message_id):
    try:
        bot.delete_message(CHAT_ID, message_id)
    except Exception as e:
        pass


def greeting(message):
    global CHAT_ID, MESSAGE_ID, PREV_MSG_ID
    CHAT_ID = message.from_user.id
    msg1 = bot.send_message(message.from_user.id, "🏙 Привет, москвич! В этом году проходит переизбрание муниципальных "
                                           "депутатов в каждом районе Москвы, кроме Щукино.  Бот подскажет, "
                                           "куда и за кого ты можешь пойти и проголосовать."
                                           "\n\n"
                                           "Подробнее о предстоящих выборах читай на сайте:\n"
                                           "https://www.mos.ru/city/projects/vote2022/#who"
                                           "\n\n"
                                           "🗳 Голосуй, не упусти шанс помочь своему району стать лучше!")
    msg2 = bot.send_message(message.from_user.id, "Набор доступных команд:", reply_markup=make_markup())
    MESSAGE_ID = msg2.message_id
    PREV_MSG_ID = msg1.message_id
    bot.send_message(message.from_user.id,
                     "Инициатива создания проекта «Жми галочку» исходит от партии «Новые Люди». Мы рекомендуем вам пойти на выборы и выразить свою гражданскую позицию. Нажмите правильную галочку ✅")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    greeting(message)


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("dont_find_street") != -1)
def dont_find_something(callback_query: types.CallbackQuery):
    dont_find()


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("swipeC") != -1)
def swipe_candidates(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    try:
        global MESSAGE_ID
        delete_message(MESSAGE_ID)
        pointer = str(callback_query.data).find("swipeC")
        direction = int(str(callback_query.data)[:pointer])
        page = int(str(callback_query.data)[pointer + 6:])
        msg = bot.send_message(callback_query.from_user.id, "Ваши кандидаты:\n" + my_candidats[
            (page + direction + len(my_candidats)) % (len(my_candidats))],
                               reply_markup=make_markup_swipe_candidates(
                                   (page + direction + len(my_candidats)) % (len(my_candidats))))
        MESSAGE_ID = msg.message_id
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("swipeS") != -1)
def swipe_streets(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    try:
        global MESSAGE_ID
        delete_message(MESSAGE_ID)
        pointer = str(callback_query.data).find("swipeS")
        direction = int(str(callback_query.data)[:pointer])
        page_begin = int(str(callback_query.data)[pointer + 6:].split(".")[0])
        county = address["county"]
        district = address["district"]
        quantity = len(adds[county][district])
        new_page = 0
        global quantity_streets_once
        if direction == -1 and page_begin == 0:
            new_page = quantity - quantity % quantity_streets_once
        elif direction == -1:
            new_page = (page_begin - 8) % quantity
        if new_page == quantity:
            new_page = quantity - quantity_streets_once
        elif direction == 1:
            new_page = page_begin + 8
        if new_page >= quantity:
            new_page = 0

        msg = bot.send_message(callback_query.from_user.id, "Выберите улицу:",
                               reply_markup=make_street_markup(county, district, new_page))
        MESSAGE_ID = msg.message_id
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("uik") == 0)
def send_address(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    try:
        id = callback_query.data[3:]
        address = ""
        uik = {}
        global MESSAGE_ID
        try:
            delete_message(MESSAGE_ID)
        except Exception:
            pass
        for add in set_probably_addresses.keys():
            if str(set_probably_addresses[add]['id']) == id:
                address = add
                uik = set_probably_addresses[add]["uik"]
        add_msg = f"🏠 Ваш адрес: {address}\n\n🏫 Ваша {uik['name']} находится по адресу:\n" \
                  f"{uik['address']}"
        msg = bot.send_message(callback_query.from_user.id, add_msg)
        global PREV_MSG_ID
        PREV_MSG_ID = msg.message_id
        print_candidates(callback_query.from_user.id, uik["vrn"])
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("find_cik") == 0)
def inline_county(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    global MESSAGE_ID
    try:
        try:
            delete_message(MESSAGE_ID)
            delete_message(PREV_MSG_ID)
        except Exception as e:
            pass
        bot.answer_callback_query(callback_query.id)
        msg = bot.send_message(callback_query.from_user.id, "Выберите округ:", reply_markup=make_county_markup())
        MESSAGE_ID = msg.message_id
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("close") == 0)
def close(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    try:
        global MESSAGE_ID, PREV_MSG_ID
        delete_message(MESSAGE_ID)
        if not (PREV_MSG_ID is None):
            delete_message(PREV_MSG_ID)
        PREV_MSG_ID = None
        menu()
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("county") == 0)
def inline_district(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    try:
        bot.answer_callback_query(callback_query.id)
        county = callback_query.data[6:]
        for c in adds.keys():
            if c.find(county) == 0:
                county = c
                break
        address["county"] = county
        msg = bot.send_message(callback_query.from_user.id, "Выберите район:",
                               reply_markup=make_district_markup(county))
        global MESSAGE_ID
        delete_message(MESSAGE_ID)
        MESSAGE_ID = msg.message_id
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("district") == 0)
def inline_street(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    try:
        district = callback_query.data[8:]
        for d in adds[address["county"]].keys():
            if d.find(district) == 0:
                district = d
                break
        address["district"] = district
        msg = bot.send_message(callback_query.from_user.id, "Выберите улицу:",
                               reply_markup=make_street_markup(address["county"], address["district"]))
        global MESSAGE_ID
        delete_message(MESSAGE_ID)
        MESSAGE_ID = msg.message_id
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("street") == 0)
def inline_street(callback_query: types.CallbackQuery):
    global CHAT_ID
    CHAT_ID = callback_query.from_user.id
    #try:
    shift = int(callback_query.data[6:])
    street = adds[address["county"]][address["district"]][shift]
    address["street"] = street
    print("STREET:" + street)
    msg = bot.send_message(callback_query.from_user.id, "Введите номер дома")
    global MESSAGE_ID
    delete_message(MESSAGE_ID)
    MESSAGE_ID = msg.message_id
    bot.register_next_step_handler(msg, get_street)
    '''except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")'''


def get_street(message):
    #try:
    global MESSAGE_ID
    delete_message(MESSAGE_ID)
    delete_message(message.id)
    load_msg = bot.send_message(message.from_user.id, "Загрузка... 🔁")
    address["house"] = message.text
    diff_vrn, info = parser.get_address_info(address_to_url_str())
    MESSAGE_ID = load_msg.message_id
    if len(diff_vrn) == 1:
        uik = {}
        for i in info.keys():
            uik = info[i]["uik"]
        add_msg = f"🏠 Ваш адрес: {address_to_str()}\n\n🏫 Ваша {uik['name']} находится по адресу:\n" \
                  f"{uik['address']}\n\n"
        delete_message(MESSAGE_ID)
        msg = bot.send_message(message.from_user.id, add_msg)
        global PREV_MSG_ID
        PREV_MSG_ID = msg.message_id
        print_candidates(message.from_user.id, uik["vrn"])
    elif len(diff_vrn) == 0:
        dont_find(1)
    else:
        global set_probably_addresses
        set_probably_addresses = info
        delete_message(MESSAGE_ID)
        msg = bot.send_message(message.from_user.id, "Уточните адрес:", reply_markup=make_choose_add_markup())
        MESSAGE_ID = msg.message_id
    '''except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")'''


def get_candidates_info(c, cand_msg, q=0):
    try:
        global my_candidats
        time_point = str(c["datroj"]).rfind(" ")
        namio_point = c["namio"].find("партии")
        if namio_point == -1:
            namio_point = -7
        namio = c["namio"][namio_point + 7:]
        fio = str(c["fio"])
        if namio == "\"НОВЫЕ ЛЮДИ\"":
            fio = fio
        if namio == "Самовыдвижение":
            namio = "⬜" + namio
        elif namio == "\"НОВЫЕ ЛЮДИ\"":
            namio = "🗳" + namio
        elif namio == "\"КОММУНИСТИЧЕСКАЯ ПАРТИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ\"":
            namio = "🟥" + namio
        elif namio == "\"ЕДИНАЯ РОССИЯ\"":
            namio = "🟦" + namio
        elif namio == "СПРАВЕДЛИВАЯ РОССИЯ - ПАТРИОТЫ - ЗА ПРАВДУ в городе Москве":
            namio_point = namio.find("РОССИЯ")
            namio = "🟧" + namio[:namio_point + 6]
        elif namio == "ЛДПР - Либерально-демократической партии России":
            namio = "🟨" + namio
        elif namio.upper().find("ЯБЛОКО") != -1:
            namio = "🟩" + namio

        cand_msg += "👤" + fio + " (" + str(c["datroj"])[:time_point] + ")\n" + str(namio + "\n\n")
        q += 1
        if q % 7 == 0:
            my_candidats.append(cand_msg)
            cand_msg = ""
        return q, cand_msg
    except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return 0, ""


def print_candidates(message_id, vrn):
    try:
        global my_candidats
        global MESSAGE_ID
        load_msg = bot.send_message(message_id, "Загрузка... 🔁")
        list_candidates = parser.get_list_of_candidates(vrn)
        cand_msg = ""
        q = 0
        for c in list_candidates:
            if str(c['namio']).find("НОВЫЕ ЛЮДИ") != -1:
                q, cand_msg = get_candidates_info(c, cand_msg, q)
        for c in list_candidates:
            if str(c['namio']).find("НОВЫЕ ЛЮДИ") == -1:
                q, cand_msg = get_candidates_info(c, cand_msg, q)
        delete_message(load_msg.message_id)
        msg = bot.send_message(message_id, "Ваши кандидаты:\n" + my_candidats[0],
                               reply_markup=make_markup_swipe_candidates(0))
        MESSAGE_ID = msg.message_id
    except Exception as e:
        global CHAT_ID
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def menu():
    global CHAT_ID, MESSAGE_ID
    try:
        msg = bot.send_message(CHAT_ID, "Набор доступных команд:", reply_markup=make_markup())
        MESSAGE_ID = msg.message_id
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.message_handler(commands=['menu'])
def send_welcome(message):
    global CHAT_ID
    try:
        CHAT_ID = message.from_user.id
        greeting(message)
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.message_handler(commands=['help'])
def send_welcome(message):
    global CHAT_ID
    try:
        CHAT_ID = message.from_user.id
        bot.send_message(CHAT_ID, "💬 Блок «Помощь»\n"
                                  "Бот не отвечает? – Нажмите /start, чтобы его перезапустить.\n"
                                  "Бот не находит ваш УИК?* – Напишите нам в чат обратной связи: @vfv_support_bot")
    except Exception as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def dont_find(is_add=0):
    global MESSAGE_ID, PREV_MSG_ID
    msg_text = ""
    if is_add:
        msg_text = f"🏠 Ваш адрес: {address_to_str()}?\nК сожалению, не можем найти УИК по выбранному адресу.\n\n"
    msg_text += f"🙋Если вы не можете найти адрес дома, напишите нам: @vfv_support_bot\n\n"
    msg_text += f"🏫Вы также можете сделать это самостоятельно, перейдя на официальный сайт Избиркома: \n" \
          "http://www.cikrf.ru/digital-services/naydi-svoy-izbiratelnyy-uchastok"
    delete_message(MESSAGE_ID)
    msg = bot.send_message(CHAT_ID, msg_text)
    PREV_MSG_ID = msg.message_id
    menu()

try:
    bot.infinity_polling()
except Exception as e:
    bot.send_message(CHAT_ID, "Что-то пошло не так, перезапустите бота командой /start")
