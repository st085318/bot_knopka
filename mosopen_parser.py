import json
import time

import requests
import parser
import bot
from addresses import adds
from bs4 import BeautifulSoup


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'uk,en-US;q=0.9,en;q=0.8,ru;q=0.7',
    'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'
}


adj = {"Cтарый": "Ст", "Новый": "Нов", "Средний": "СР", "Большой": "Б", "Малый": "М"}


def get_list_areas():
    url = "http://mosopen.ru/streets"
    area_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(area_page.text, "html.parser")
    areas_info = soup.findAll("div", {"id": "regions_by_districts"})
    areas_list = str(areas_info).split("<strong>")
    counties_list = []
    counties = {}
    for area in areas_list:
        counties_list.append(area.split("</strong>"))
    counties_list = counties_list[1:]
    for c in counties_list:

        county = get_name(c[0])
        if county != "ЗелАО":
            continue
        print(county)
        districts_html = c[1].split(",<br/>")
        districts = {}
        for d in districts_html:
            streets = []
            streets_list = get_list_streets(get_attr("href", d))
            for s in streets_list:
                if s.rfind("(") != -1:
                    s = s[:s.rfind("(")]
                if s.rfind(",") == -1:
                    suff = s[s.rfind(" "):]
                    pref = s[:s.rfind(" ")]
                    s = pref + "," + suff
                q = is_street_exist(format_county(county), format_district(county, get_name(d)), s)
                time.sleep(0.5)
                if q:
                    streets.append(s)
            districts[format_district(county, get_name(d))] = streets
            time.sleep(1)
            print(districts)
            #print(get_name(d) + " title " + get_attr("title", d))
        counties[county] = districts
        with open("zel.py", "w") as f:
            f.write(str(counties))
    print(counties)

    return counties_list


def format_county(county):
    for c in adds.keys():
        if bot.to_short_county(c) == county:
            return c
        elif county == "ЗелАО":
            return "Зеленоградский административный округ"


def format_district(county, district):
    if county == "ЗелАО":
        county = "Зеленоградский административный округ"
    else:
        county = format_county(county)
    words_in_district = district.split(" ")
    for d in adds[county].keys():
        quantity_en = 0
        for w in words_in_district:
            if d.replace('ё', 'е').upper().find(w.replace('ё', 'е').upper()) != -1:
                quantity_en += 1
        if quantity_en == len(words_in_district):
            return d
    print(district)
    return None


def get_name(html_string):
    html_string = html_string[:html_string.rfind("</a>")]
    return html_string[html_string.rfind(">")+1:]


def get_attr(attr, html_str):
    html_str = html_str[html_str.rfind(attr) + len(attr) + 2:]
    return html_str[:html_str.find('"')]


def get_list_streets(url):
    area_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(area_page.text, "html.parser")
    streets_info = str(soup.findAll("div", {"class": "double_block clearfix"}))
    streets_with_other = streets_info.split("<li>")
    streets = []
    for s in streets_with_other:
        streets.append(s[s.find(">") + 1:s.rfind("</a>")])
    return streets[1:]


def is_street_exist(county, district, street):
    if parser.is_add_exist(bot.address_to_url_str(None, county, district, street, None)):
        return 1
    return 0

if __name__ == "__main__":
    #print(is_street_exist("Восточный административный округ", "Район Вешняки", "Косинская, ул."))
    get_list_areas()