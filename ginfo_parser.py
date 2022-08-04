import requests
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


def get_list_areas(url, suffix="", depth=0):
    area_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(area_page.text, "html.parser")
    areas_list = soup.findAll("div", {"class": "rayon_list"})
    areas_list = BeautifulSoup(str(areas_list[depth]), "html.parser").findAll('a', href=True)
    areas = {}
    for county in areas_list:
        format_county = str(county)[9:-4].split(f"\">")
        if county != areas_list[0]:
            val = format_county[0]
            trash = val.find(r"amp;")
            if trash != -1:
                val = val[:trash] + val[trash + 4:]
            areas[format_county[1] + suffix] = val
    return areas


def get_districts_streets(url):
    streets_page = requests.get(url, headers=headers)
    soup = BeautifulSoup(streets_page.text, "html.parser")
    print("    soup: " + str(soup))
    streets_list_info = soup.findAll("div", {"class": "street_unit"})
    streets_list = []
    for s in streets_list_info:
        streets_list.append(str(s.text))
    return streets_list


def get_list_streets(url):
    cs = {}
    counties = get_list_areas(url, " административный округ")
    for c in counties.keys():
        ds = {}
        districts = get_list_areas(url + counties[c], "", 1)
        time.sleep(1)
        print(districts)
        for d in districts.keys():
            streets = get_districts_streets(url + districts[d])
            ds[d] = streets
        cs[c] = ds
    return cs