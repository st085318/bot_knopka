import json
import requests
import time
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


def find_uik_18(address: [], addresses_json: json):
    for adr in addresses_json['addresses']:
        data = adr.split(',')
        if len(data) >= 4:
            if data[2].upper().rfind(address[0].upper()) == 0 and data[3] == address[1]:
                if len(address) == 3:
                    if data[4] == address[2]:
                        return addresses_json["uik #"]
                    else:
                        # TODO: mind about return
                        return None
                else:
                    return addresses_json["uik #"]
    return None


def is_vrn_in_vrns(vrn, vrns):
    for v in vrns:
        if vrn in v.keys():
            return 1
    return 0


def get_address_info(address: str, quantity_return = 2):
    format_address = f"%20".join(address.split(" "))
    url = f"http://www.cikrf.ru/iservices/voter-services/address/search/{format_address}"
    addresses_info = json.loads(requests.get(url, headers=headers).text)
    vrns = set()
    probably_addresses = {}
    id = 0
    for address in addresses_info:
        try:
            uik = get_uik_by_add_id(address['id'])
        except json.decoder.JSONDecodeError:
            continue
        vrn = uik["vrn"]
        vrns.add(vrn)
        if quantity_return == 1:
            return vrns
        if address["leaf"]:
            suff = address['name'].rfind(',')
            pref = address['name'][:suff]
            pref = pref[pref.find(', ') + 1:]
            pref = pref[pref.find(', ') + 1:]
            pref = pref[pref.find(', ') + 2:]
            probably_addresses[pref[:suff]] = {'id': id, 'uik': {'name': uik['name'], 'address': uik["votingAddress"]["address"], "vrn": uik["vrn"]}}
            id += 1
    if quantity_return == 1:
        return vrns
    return vrns, probably_addresses


def get_uik_by_add_id(id):
    url = f"http://www.cikrf.ru/iservices/voter-services/committee/address/{str(id)}"
    response = requests.get(url, headers=headers).text
    return json.loads(response)


def get_uik_info(uik_num):
    url = "http://cikrf.ru/iservices/voter-services/committee/subjcode/77/num/" + str(uik_num)
    return json.loads(requests.get(url, headers=headers).text)


def get_list_of_candidates(UIK_VRN):
    list_of_candidates = []
    CAMPAIGN_VRN = json.loads(requests.get(f"http://cikrf.ru/iservices/voter-services/vibory/committee/{str(UIK_VRN)}",
                                           headers=headers).text)[0]["vrn"]
    mandates = get_nums_districts(CAMPAIGN_VRN)

    # requests.get("http://cikrf.ru/iservices/sgo-visual-rest/vibory/{CAMPAIGN_VRN}/tvd", headers=headers)
    PAGE_NUM = 0
    total_pages = 1
    while PAGE_NUM != total_pages:
        PAGE_NUM += 1
        candidates_json = json.loads(
            requests.get(f"http://cikrf.ru/iservices/sgo-visual-rest/vibory/{CAMPAIGN_VRN}/candidates/?page={PAGE_NUM}",
                         headers=headers).text)
        total_pages = candidates_json["page"]["totalPages"]
        for candidate in candidates_json["_embedded"]["candidateDtoList"]:
            list_of_candidates.append(candidate)
    return list_of_candidates, mandates


def find_uik(id):
    url = f"http://www.cikrf.ru/iservices/voter-services/committee/address/{str(id)}"


def get_mandates(url):
    response = requests.get(url, headers=headers)
    code = response.text
    code = code[code.find("tvdTreeJson = {"):]
    code = code[:code.find("\n")]
    code = code[len("tvdTreeJson = "):]
    mandates_info = json.loads(code)
    return mandates_info["children"]


def get_nums_districts(campaign_vrn):
    url = f"http://www.vybory.izbirkom.ru/region/izbirkom?action=show&root=1&vrn={campaign_vrn}&prver=0&pronetvd=null&region=77&sub_region=77"
    mandates = get_mandates(url)
    uiks = {}
    if mandates == []:
        #TODO
        response = requests.get(url, headers=headers)
        code = response.text
        code = code[code.find("tvdTreeJson = {"):]
        code = code[:code.find("\n")]
        code = code[len("tvdTreeJson = "):]
        mandates_info = json.loads(code)
    else:
        for m in mandates:
            m_name = m["text"]
            m_num = m_name[m_name.rfind(" ") + 1:]
            if m_num.find("№") != -1:
               m_num = m_num[m_num.find("№") + 1:]
            uiks[m_num] = get_list_uiks(m["href"])
    return uiks


def get_list_uiks(url_suffix):
    url = "http://www.vybory.izbirkom.ru/" + url_suffix
    mandates = get_mandates(url)
    list_num_uiks = []
    for m in mandates:
        if m["href"] == url_suffix:
            uiks = m["children"]
            break
    for u in uiks:
        uik_name = u["text"]
        list_num_uiks.append(uik_name[uik_name.rfind(" ") + 2:])
    return list_num_uiks


def is_add_exist(address):
    vrns = get_address_info(address, 1)
    return len(vrns) > 0


if __name__ == "__main__":
    # Город%20Москва%20Восточный%20административный%20округ%20район%20Ивановское%20КУПАВЕНСКИЙ%20Б.%20ПР.%202/
    # "http://www.cikrf.ru/iservices/voter-services/address/search/%D0%93%D0%BE%D1%80%D0%BE%D0%B4%20%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%20%D0%A1%D0%B5%D0%B2%D0%B5%D1%80%D0%BE%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D1%8B%D0%B9%20%D0%B0%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%B8%D0%B2%D0%BD%D1%8B%D0%B9%20%D0%BE%D0%BA%D1%80%D1%83%D0%B3%20%D1%80%D0%B0%D0%B9%D0%BE%D0%BD%20%D0%9C%D0%B0%D1%80%D1%8C%D0%B8%D0%BD%D0%B0%20%D1%80%D0%BE%D1%89%D0%B0%20%D0%94%D0%9E%D0%A1%D0%A2%D0%9E%D0%95%D0%92%D0%A1%D0%9A%D0%9E%D0%93%D0%9E%20%D0%A3%D0%9B%20%D0%B4%204%20%D0%BA%202/"
    # Город%20Москва%20Восточный%20административный%20округ%20район%20Гольяново%20БАЙКАЛЬСКАЯ%20УЛ%2044%20д%203/
    # f"http://www.cikrf.ru/iservices/voter-services/committee/address/141333300347676160000378975"

    #print(get_address_info("Город Москва Восточный административный округ район Ивановское КУПАВЕНСКИЙ Б. ПР. 2"))

    #print(get_list_of_candidates(4774012116710))
    print(get_nums_districts(4774004309365))
    # TODO: сделать словарь {vrn:[num, list_of_candidates]}
    # TODO: пройти по всем uik(4000 + проверка) и выкачать все данные

    # get_list_areas("http://ginfo.ru/ulicy/" + '?okrug=4', "", 1)
    # with open("addresses.json", "w") as f:
    #    f.write(str(get_list_streets("http://ginfo.ru/ulicy/")))
