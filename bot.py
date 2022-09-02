import parser
import telebot
import os
import json
from telebot import types
from addresses import adds
#from diss import adds
from keys import TELEGRAM_API_KEY

bot = telebot.TeleBot(TELEGRAM_API_KEY)
NEW_PEOPLE_URL = "https://newpeople.ru/"
change = {'ш.': "ШОССЕ", 'наб.': "НАБ.", 'аллея': "АЛЛЕЯ", 'ул.': "УЛ.", 'кв-л': "КВАРТАЛ", 'туп.': "ТУП.", 'б-р': "БУЛЬВ.", 'пр-т': "ПРОСП.", 'мкр.': "", 'линия': "ЛИНИЯ", 'пр-д': "ПР.", 'пер.': "ПЕР.", 'шоссе': "ШОССЕ", 'набережная': "НАБ.",
          'улица': "УЛ.", 'квартал': "КВАРТАЛ", 'тупик': "ТУП.", 'бульвар': "БУЛЬВ.", 'проспект': "ПРОСП.", 'микрорайон': "",
          'проезд': "ПР.", 'переулок': "ПЕР", "городок": "городок", 'площадь': 'площадь', 'км.': 'км.', 'просек': 'просек'}
quantity_streets_once = 8


adj = {"Старый": "Ст", "Новый": "Нов", "Средний": "СР", "Большой": "Б", "Малый": "М",
       "Старая": "Ст", "Новая": "Нов", "Средняя": "СР", "Большая": "Б", "Малая": "М"}


def create_file(chat_id):
    with open(f"users_info/{chat_id}.json", "w") as f:
        f.write(json.dumps({"MESSAGE_ID": 0, "PREV_MSG_ID": 0, "UIK_NUM": 0,
                     "address": {"county": "", "district": "", "street": "", "house": "", "building": ""},
                     "set_probably_addresses": {}, "my_candidats": []}))


def get_user_info(chat_id):
    with open(f"users_info/{chat_id}.json", "r") as f:
        info = json.loads(f.read())
    return info


def set_user_info(chat_id, var, val):
    user_info = get_user_info(chat_id)
    user_info[var] = val
    with open(f"users_info/{chat_id}.json", "w") as f:
        f.write(json.dumps(user_info))


# Алешинская -> Алшкинская
# TODO: удалять ё
def address_to_url_str(CHAT_ID = None, county=None, district=None, street=None, house=None):
    def format_street(street, suffix):
        street = street.replace(",", "")
        words_street = street.split(" ")
        f_street = ""
        words_street.remove(suffix)

        if ((words_street[0] == "Старый" or words_street[0] == "Старая") and street != "Старый гай") or street == "Новый Зыковский проезд" or words_street[0] == "Новая":
            for w in words_street[1:]:
                f_street += w + " "
            f_street += adj[words_street[0]] + change[suffix]
        elif words_street[0] in ["Большой", "Малый", "Средний", "Большая", "Малая", "Средняя"]:
            for w in words_street[1:]:
                f_street += w + " "
            f_street = + adj[words_street[0]] + change[suffix]
        else:
            for w in words_street:
                f_street += w + " "
            f_street += change[suffix]

        if f_street.find("-") != -1:
            f_street = f_street[:f_street.find("-")] + f_street[f_street.find("-") + 1:]
        return f_street

    try:
        if county is None:
            address = get_user_info(CHAT_ID)["address"]
            county = address['county']
            district = address['district']
            street = address['street']
            house = address["house"]
        if county == "Зеленоградский административный округ":
            district += " Зеленоград г"
        '''
        if district.find("-") != -1:
            b = district[:district.find("-")]
            e = district[district.find("-") + 1:]
            district = b
            if district.upper().find("ОРЕХОВО") == -1:
                district += " "
            district += e
        
        add = f"Город Москва {county} {district.replace('ё', 'е')} "
        '''
        add = "Город Москва "
        if street.find("микрорайон") != -1:
            return add + "д " + str(house)
        for suffix in change.keys():
            if street.find(suffix) != -1:
                street = format_street(street, suffix)
        if street.upper().find("РАЙОН") != -1:
            street = "д"
        if street.upper().find("СЕВЕРНАЯ") != -1:
            part_street = street.split(" ")
            street = part_street[1][:-1] + " " + part_street[0] + " " + part_street[2]
        if house is None:
            return add + street.replace('ё', 'е').upper()
        return add + street.replace('ё', 'е').upper() + " " + house
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


def address_to_str(CHAT_ID):
    try:
        address = get_user_info(CHAT_ID)["address"]
        add = f""
        for k in address.keys():
            if address[k] != "":
                add += address[k] + ", "
        add = add[:-2]
        return add
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


def make_markup_insert_street():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ввести улицу самостоятельно", callback_data="write_street"))
    return markup


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
    button_street = types.InlineKeyboardButton("Ввести адрес самостоятельно", callback_data="write_street")
    # button_candidates = types.InlineKeyboardButton("Посмотреть кандидатов", callback_data="candidates")
    markup.add(button_cik)
    markup.add(button_street)
    # markup.add(button_candidates)
    return markup


def make_county_markup():
    markup = types.InlineKeyboardMarkup()
    for c in adds.keys():
        callback = "county" + str(c)[:10]
        markup.add(types.InlineKeyboardButton(to_short_county(str(c)), callback_data=callback))
    markup.add(types.InlineKeyboardButton("Закрыть", callback_data=f"close"))
    return markup


def make_district_markup(county):
    markup = types.InlineKeyboardMarkup()
    for district in adds[county].keys():
        markup.add(types.InlineKeyboardButton(str(district), callback_data="district" + str(district)[:25]))
    markup.add(types.InlineKeyboardButton("Закрыть", callback_data=f"close"))
    return markup


def make_street_markup(CHAT_ID, county, district, num_street_page=0):
    try:
        markup = types.InlineKeyboardMarkup()
        shift = 0
        global quantity_streets_once
        for c in adds[county][district][num_street_page:num_street_page + quantity_streets_once]:
            # TODO:rewrite on num
            callback = "street" + str(shift) + ":" + str(num_street_page)
            markup.add(types.InlineKeyboardButton(str(c), callback_data=callback))
            shift += 1
        if num_street_page + 7 >= len(adds[county][district]) - 1:
            markup.add(types.InlineKeyboardButton("Моей улицы нет", callback_data="dont_find_street"))
        markup.row(types.InlineKeyboardButton("<<Назад", callback_data=f"-1swipeS{num_street_page}"),
                   types.InlineKeyboardButton("Закрыть", callback_data=f"close"),
                   types.InlineKeyboardButton("Вперед>>", callback_data=f"1swipeS{num_street_page}"))
        return markup
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return None


def make_choose_add_markup(CHAT_ID):
    try:
        markup = types.InlineKeyboardMarkup()
        set_probably_addresses = dict(get_user_info(CHAT_ID)["set_probably_addresses"])
        for add_info in set_probably_addresses.keys():
            callback = "uik" + str(set_probably_addresses[add_info]["id"])
            markup.add(types.InlineKeyboardButton(add_info, callback_data=callback))
        markup.add(types.InlineKeyboardButton("Моего дома нет", callback_data="dont_find_street"))
        return markup
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return None


def to_short_county(county: str):
    if county == "Зеленоградский административный округ":
        return "ЗелАО"
    split_county = county.split(" ")
    split_county[0] = split_county[0].split("-")
    short_county = ""
    for w in split_county[0]:
        short_county += w[0].upper()
    for w in split_county[1:]:
        short_county += w[0].upper()
    return short_county


def delete_message(CHAT_ID, message_id):
    try:
        bot.delete_message(CHAT_ID, message_id)
    except telebot.apihelper.ApiTelegramException:
        pass
        #print(e)


def greeting(message):
    CHAT_ID = message.from_user.id
    href = "https://www.mos.ru/city/projects/vote2022/#who"
    photo = open("media/greeting.png", 'rb')
    bot.send_message(message.from_user.id,
                     "Привет! В этом году состоятся выборы муниципальных депутатов в районах Москвы.\n"
                     "Наш бот поможет найти адрес вашего избирательного участка, и посмотреть список кандидатов, которые идут на выборы в вашем районе.\n\n"
                     "🗳 Приходи на выборы или голосуй онлайн в личном кабинете на сайте mos.ru.\n\n"
                     "Если сомневаешься, вот три причины для того, чтобы обязательно прийти на выборы:\n\n"
                     "1. Муниципальная власть – самая близкая людям. Каждый из нас может лично познакомиться с депутатом, который живёт по соседству и не понаслышке знает о проблемах нашего района\n\n"
                     "2. Чтобы Совет депутатов работал в интересах жителей, необходимо регулярно обновлять депутатский корпус. Голосование на выборах – единственный шанс сделать это\n\n"
                     "3. Если вы не придёте на избирательный участок, выбор за вас сделают другие. Ваш голос не будет услышан, ваше мнение — проигнорируют, а об удобстве и комфорте москвичей будут вспоминать лишь от случая к случаю.\n\n\n"
                     f"Подробнее о предстоящих выборах читай на сайте: {href}\n\n"
                     "Инициатива информирования о выборах  «Жми галочку»  создана при поддержке партии «Новые Люди».",
                     disable_web_page_preview=True)
    bot.send_photo(message.from_user.id, photo)
    msg = bot.send_message(message.from_user.id, "Набор доступных команд:", reply_markup=make_markup())
    set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))


@bot.message_handler(commands=['start'])
def send_welcome(message):
    create_file(message.from_user.id)
    greeting(message)


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("dont_find_street") != -1)
def dont_find_something(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    dont_find(CHAT_ID)


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("write_street") != -1)
def dont_find_something(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    about_format = "Введите улицу, на которой проживаете в формате: <название улицы, вид улицы>\nНапример - Союзный, проспект"
    msg = bot.send_message(CHAT_ID, about_format)
    MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
    delete_message(CHAT_ID, MESSAGE_ID)
    set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    bot.register_next_step_handler(msg, write_street)


def write_street(message):
    try:
        CHAT_ID = message.from_user.id
        address = get_user_info(CHAT_ID)["address"]
        address["street"] = message.text
        address["county"] = ""
        address["district"] = ""
        delete_message(CHAT_ID, message.id)
        set_user_info(CHAT_ID, "address", address)
        msg = bot.send_message(CHAT_ID, "Введите номер дома")
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        delete_message(CHAT_ID, MESSAGE_ID)
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
        bot.register_next_step_handler(msg, get_house)
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")



@bot.callback_query_handler(lambda callback_query: callback_query.data.find("swipeC") != -1)
def swipe_candidates(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        my_candidats = list(get_user_info(CHAT_ID)["my_candidats"])
        delete_message(CHAT_ID, MESSAGE_ID)
        pointer = str(callback_query.data).find("swipeC")
        direction = int(str(callback_query.data)[:pointer])
        page = int(str(callback_query.data)[pointer + 6:])
        msg = bot.send_message(callback_query.from_user.id, "Ваши кандидаты:\n" + my_candidats[
            (page + direction + len(my_candidats)) % (len(my_candidats))],
                               reply_markup=make_markup_swipe_candidates(
                                   (page + direction + len(my_candidats)) % (len(my_candidats))))
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("swipeS") != -1)
def swipe_streets(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        MESSAGE_ID = get_user_info(str(CHAT_ID))["MESSAGE_ID"]
        delete_message(CHAT_ID, MESSAGE_ID)
        pointer = str(callback_query.data).find("swipeS")
        direction = int(str(callback_query.data)[:pointer])
        page_begin = int(str(callback_query.data)[pointer + 6:].split(".")[0])
        county = get_user_info(str(CHAT_ID))["address"]["county"]
        district = get_user_info(str(CHAT_ID))["address"]["district"]
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
                               reply_markup=make_street_markup(CHAT_ID, county, district, new_page))
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def send_address(CHAT_ID, uik):
    user_info = get_user_info(CHAT_ID)
    MESSAGE_ID = user_info["MESSAGE_ID"]
    set_user_info(CHAT_ID, "UIK_NUM", str(int(uik['name'][uik['name'].rfind("№") + 1:])))
    add_msg = f"🏠 Выбранный дом находится по адресу:\n{address_to_str(CHAT_ID)}\n\n🏫 Ваша {uik['name']} находится по адресу:\n" \
              f"{uik['address']}\n\n"
    delete_message(CHAT_ID, MESSAGE_ID)
    msg = bot.send_message(CHAT_ID, add_msg)
    location_msg = bot.send_location(CHAT_ID, uik["lat"], uik["lon"])
    set_user_info(CHAT_ID, "PREV_MSG_ID", str(msg.message_id))
    set_user_info(CHAT_ID, "EXTRA_MSG_ID", str(location_msg.message_id))
    print_candidates(CHAT_ID, uik["vrn"], CHAT_ID)


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("uik") == 0)
def send_choosen_address(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        id = callback_query.data[3:]
        address = ""
        uik = {}
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        try:
            delete_message(CHAT_ID, MESSAGE_ID)
        except telebot.apihelper.ApiTelegramException:
            pass
        set_probably_addresses = dict(get_user_info(CHAT_ID)["set_probably_addresses"])

        for add in set_probably_addresses.keys():
            if str(set_probably_addresses[add]['id']) == id:
                address = add
                uik = set_probably_addresses[add]["uik"]
        send_address(CHAT_ID, uik)
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("find_cik") == 0)
def inline_county(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        PREV_MSG_ID = get_user_info(CHAT_ID)["PREV_MSG_ID"]
        try:
            delete_message(CHAT_ID, MESSAGE_ID)
            delete_message(CHAT_ID, PREV_MSG_ID)
        except telebot.apihelper.ApiTelegramException:
            pass
        bot.answer_callback_query(callback_query.id)
        msg = bot.send_message(callback_query.from_user.id, "Выберите округ:", reply_markup=make_county_markup())
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return ""


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("close") == 0)
def close(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        PREV_MSG_ID = get_user_info(CHAT_ID)["PREV_MSG_ID"]
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        try:
            EXTRA_MESSEGE_ID = get_user_info(CHAT_ID)["EXTRA_MSG_ID"]
            delete_message(CHAT_ID, EXTRA_MESSEGE_ID)
        except BaseException:
            pass
        delete_message(CHAT_ID, MESSAGE_ID)
        if not (PREV_MSG_ID is None):
            delete_message(CHAT_ID, PREV_MSG_ID)

        menu(CHAT_ID)
    except telebot.apihelper.ApiTelegramException:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("county") == 0)
def inline_district(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        bot.answer_callback_query(callback_query.id)
        county = callback_query.data[6:]
        for c in adds.keys():
            if c.find(county) == 0:
                county = c
                break
        address = get_user_info(CHAT_ID)["address"]
        address["county"] = county
        set_user_info(CHAT_ID, "address", address)
        msg = bot.send_message(callback_query.from_user.id, "Выберите район:",
                               reply_markup=make_district_markup(county))
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        delete_message(CHAT_ID, MESSAGE_ID)
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("district") == 0)
def inline_street(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    try:
        address = get_user_info(CHAT_ID)["address"]
        district = callback_query.data[8:]
        for d in adds[address["county"]].keys():
            if d.find(district) == 0:
                district = d
                break
        address["district"] = district
        set_user_info(CHAT_ID, "address", address)
        msg = bot.send_message(callback_query.from_user.id, "Выберите улицу:",
                               reply_markup=make_street_markup(CHAT_ID, address["county"], address["district"]))
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        delete_message(CHAT_ID, MESSAGE_ID)
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.callback_query_handler(lambda callback_query: callback_query.data.find("street") == 0)
def inline_house(callback_query: types.CallbackQuery):
    CHAT_ID = callback_query.from_user.id
    address = get_user_info(CHAT_ID)["address"]
    try:
        shift = int(callback_query.data[6:int(str(callback_query.data).find(":"))])
        page_num = int(callback_query.data[int(str(callback_query.data).find(":")) + 1:])
        street = adds[address["county"]][address["district"]][shift + page_num]
        address["street"] = street
        set_user_info(CHAT_ID, "address", address)
        msg = bot.send_message(callback_query.from_user.id, "Введите номер дома")
        MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
        delete_message(CHAT_ID, MESSAGE_ID)
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
        bot.register_next_step_handler(msg, get_house)
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def get_house(message):
    def format_house(house_num):
        house_num = house_num.replace(" ", "")
        housing = ["корпус", "кор.", "кор", "к.", "к"]
        building = ["строение", "стр.", "стр", "с.", "с"]
        housing_num = None
        building_num = None
        # TODO REFORMAT
        for h_specie in housing:
            if house_num.find(h_specie) != -1:
                housing_num = "К" + " "
                h_pointer = house_num.find(h_specie) + len(h_specie)
                h_start = h_pointer
                while is_digit(house_num[h_pointer]):
                    housing_num += house_num[h_pointer]
                    h_pointer += 1
                    if h_pointer >= len(house_num):
                        break
                house_num = house_num[:h_start] + house_num[min(h_pointer, len(house_num) - 1):]
                break
        for b_specie in building:
            if house_num.find(b_specie) != -1:
                building_num = "стр" + " "
                b_pointer = house_num.find(b_specie) + len(b_specie)
                while is_digit(house_num[b_pointer]):
                    building_num += house_num[b_pointer]
                    b_pointer += 1
                    if b_pointer >= len(house_num):
                        break
                break
        p = 0
        while not is_digit(house_num[p]):
            p += 1
        house_num = house_num[p:]
        p = 0
        while is_digit(house_num[p]):
            p += 1
            if p == len(house_num):
                break
        house_num = house_num[:p]
        if not (housing_num is None):
            house_num += " " + housing_num
        if not (building_num is None):
            house_num += " " + building_num
        return house_num

    try:
        CHAT_ID = message.from_user.id
        user_info = get_user_info(CHAT_ID)
        MESSAGE_ID = user_info["MESSAGE_ID"]
        delete_message(CHAT_ID, MESSAGE_ID)
        delete_message(CHAT_ID, message.id)
        load_msg = bot.send_message(message.from_user.id, "Загрузка... 🔁")
        address = user_info["address"]
        address["house"] = format_house(message.text)
        set_user_info(CHAT_ID, "address", address)
        diff_vrn, info = parser.get_address_info(address_to_url_str(CHAT_ID))
        delete_message(CHAT_ID, load_msg.message_id)
        MESSAGE_ID = load_msg.message_id
        if len(diff_vrn) == 1:
            uik = {}
            for i in info.keys():
                uik = info[i]["uik"]
            send_address(CHAT_ID, uik)
        elif len(diff_vrn) == 0:
            set_user_info(CHAT_ID, "MESSAGE_ID", MESSAGE_ID)
            dont_find(CHAT_ID, 1)
        else:
            set_user_info(CHAT_ID, "set_probably_addresses", info)
            delete_message(CHAT_ID, MESSAGE_ID)
            msg = bot.send_message(message.from_user.id, "Уточните адрес:", reply_markup=make_choose_add_markup(CHAT_ID))
            set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def get_candidates_info(c, cand_mssg, q, CHAT_ID):
    try:
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
            namio = "☑" + namio
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

        cand_msg = "👤" + fio + " (" + str(c["datroj"])[:time_point] + ")\n" + str(namio + "\n\n")


        my_candidats = list(get_user_info(CHAT_ID)["my_candidats"])
        if q % 7 == 0:
            my_candidats.append(cand_msg)
        else:
            if len(my_candidats) == 0:
                my_candidats[0] += cand_msg
            else:
                my_candidats[-1] += cand_msg

        q += 1
        set_user_info(CHAT_ID, "my_candidats", my_candidats)
        return q, cand_msg
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")
        return 0, ""


def print_candidates(message_id, vrn, CHAT_ID):
    def special_people(candidate):
        time_point = str(candidate["datroj"]).rfind(" ")
        if str(candidate["fio"]) == "Ляховецкий Никита Владимирович" and str(candidate["datroj"])[:time_point] == "07.08.1998":
            return 1
        return 0
    try:
        user_info = get_user_info(CHAT_ID)
        load_msg = bot.send_message(message_id, "Загрузка... 🔁")
        set_user_info(CHAT_ID, "my_candidats",  [])
        list_candidates, mandates = parser.get_list_of_candidates(vrn)
        UIK_NUM = user_info["UIK_NUM"]
        numokr = None
        for m in mandates.keys():
            if str(UIK_NUM) in mandates[m]:
                numokr = m
                break
        cand_msg = ""
        q = 0
        for c in list_candidates:
            if (str(c['namio']).find("НОВЫЕ ЛЮДИ") != -1 or special_people(c)) and str(c['numokr']) == str(numokr):
                try:
                    if str(c['registr']) == "зарегистрирован":
                        q, cand_msg = get_candidates_info(c, cand_msg, q, CHAT_ID)
                except KeyError:
                    pass
        '''
        for c in list_candidates:
            if str(c['namio']).find("Самовыдвижение") != -1 and str(c['numokr']) == str(numokr):
                try:
                    if str(c['registr']) == "зарегистрирован":
                        q, cand_msg = get_candidates_info(c, cand_msg, q, CHAT_ID)
                except KeyError:
                    pass
        for c in list_candidates:
            if str(c['namio']).find("НОВЫЕ ЛЮДИ") == -1 and str(c['namio']).find("Самовыдвижение") == -1 and (not special_people(c)) and str(c['numokr']) == str(numokr):
                try:
                    if str(c['registr']) == "зарегистрирован":
                        q, cand_msg = get_candidates_info(c, cand_msg, q, CHAT_ID)
                except KeyError:
                    pass
        '''
        my_candidats = get_user_info(CHAT_ID)["my_candidats"]
        delete_message(CHAT_ID, load_msg.message_id)
        msg = bot.send_message(message_id, f"Список кандидатов по {numokr} избирательному округу:\n" + my_candidats[0],
                               reply_markup=make_markup_swipe_candidates(0))
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except IndexError:
        bot.send_message(CHAT_ID,
                         "👨‍💻 Похоже, что по вашему адресу не проводится голосование в этом году. Напомню, выборы проходят везде, кроме Щукино и Новой Москвы (исключение – Троицк).")
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def menu(CHAT_ID):
    try:
        msg = bot.send_message(CHAT_ID, "Набор доступных команд:", reply_markup=make_markup())
        set_user_info(CHAT_ID, "MESSAGE_ID", str(msg.message_id))
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.message_handler(commands=['menu'])
def send_welcome(message):
    try:
        CHAT_ID = message.from_user.id
        greeting(message)
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


@bot.message_handler(commands=['help'])
def send_welcome(message):
    try:
        CHAT_ID = message.from_user.id
        bot.send_message(CHAT_ID, "💬 Блок «Помощь»\n"
                                  "Бот не отвечает? – Нажмите /start, чтобы его перезапустить.\n"
                                  "Бот не находит ваш УИК?* – Напишите нам в чат обратной связи: @vfv_support_bot")
    except BaseException as e:
        if CHAT_ID != 0:
            bot.send_message(CHAT_ID, "Что-то пошло не так...\nПерезапустите бота")


def dont_find(CHAT_ID, is_add=0):
    MESSAGE_ID = get_user_info(CHAT_ID)["MESSAGE_ID"]
    msg_text = ""
    if is_add:
        msg_text = f"🏠 Выбранный дом находится по адресу:\n{address_to_str(CHAT_ID)}?\n\nК сожалению, не можем найти УИК по выбранному адресу.\n\n"
    msg_text += f"🙋Если вы не можете найти адрес дома, напишите нам: @vfv_support_bot\n\n"
    msg_text += f"🏫 Вы также можете сделать это самостоятельно, перейдя на официальный сайт Избиркома: \n" \
          "http://www.cikrf.ru/digital-services/naydi-svoy-izbiratelnyy-uchastok"
    delete_message(CHAT_ID, MESSAGE_ID)
    msg = bot.send_message(CHAT_ID, msg_text, reply_markup=make_markup_insert_street())
    set_user_info(CHAT_ID, "PREV_MSG_ID", msg.message_id)
    menu(CHAT_ID)


def is_digit(char):
    return 9 >= ord(char) - ord("0") >= 0


if __name__ == "__main__":
    path = "users_info"
    if os.path.exists(path):
        pass
    else:
        os.mkdir(path)
    try:
        bot.infinity_polling()
    except BaseException:
        pass
