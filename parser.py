import json
import requests
import wget
from requests_ip_rotator import ApiGateway
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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


def get_address_info(address: str):
    format_address = f"%20".join(address.split(" "))
    url = f"http://www.cikrf.ru/iservices/voter-services/address/search/{format_address}"
    print(url)
    #return requests.get(url, headers=headers)


def get_uik_vrn(uik_num):
    url = "http://cikrf.ru/iservices/voter-services/committee/subjcode/77/num/" + str(uik_num)
    return json.loads(requests.get(url, headers=headers).text)["vrn"]


def get_list_of_candidates(UIK_VRN):
    list_of_candidates = []
    CAMPAIGN_VRN = json.loads(requests.get("http://cikrf.ru/iservices/voter-services/vibory/committee/" + str(UIK_VRN), headers=headers).text)[0]["vrn"]
    #requests.get("http://cikrf.ru/iservices/sgo-visual-rest/vibory/{CAMPAIGN_VRN}/tvd", headers=headers)

    PAGE_NUM = 0
    total_pages = 1
    while PAGE_NUM != total_pages:
        PAGE_NUM += 1
        candidates_json = json.loads(requests.get(f"http://cikrf.ru/iservices/sgo-visual-rest/vibory/{CAMPAIGN_VRN}/candidates/?page={PAGE_NUM}", headers=headers).text)
        total_pages = candidates_json["page"]["totalPages"]
        for candidate in candidates_json["_embedded"]["candidateDtoList"]:
            list_of_candidates.append(candidate)
    return list_of_candidates





#Город%20Москва%20Восточный%20административный%20округ%20район%20Гольяново%20БАЙКАЛЬСКАЯ%20УЛ%2044%20д%203/
#Город%20Москва%20Восточный%20административный%20округ%20район%20Ивановское%20КУПАВЕНСКИЙ%20Б.%20ПР.%202/
#"http://www.cikrf.ru/iservices/voter-services/address/search/%D0%93%D0%BE%D1%80%D0%BE%D0%B4%20%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%20%D0%A1%D0%B5%D0%B2%D0%B5%D1%80%D0%BE%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D1%8B%D0%B9%20%D0%B0%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%B8%D0%B2%D0%BD%D1%8B%D0%B9%20%D0%BE%D0%BA%D1%80%D1%83%D0%B3%20%D1%80%D0%B0%D0%B9%D0%BE%D0%BD%20%D0%9C%D0%B0%D1%80%D1%8C%D0%B8%D0%BD%D0%B0%20%D1%80%D0%BE%D1%89%D0%B0%20%D0%94%D0%9E%D0%A1%D0%A2%D0%9E%D0%95%D0%92%D0%A1%D0%9A%D0%9E%D0%93%D0%9E%20%D0%A3%D0%9B%20%D0%B4%204%20%D0%BA%202/"
#f"http://www.cikrf.ru/iservices/voter-services/committee/address/141333300347676160000378975"

get_address_info("Город Москва Восточный административный округ район Ивановское КУПАВЕНСКИЙ Б. ПР. 2")

#TODO: сделать словарь {vrn:[num, list_of_candidates]}
#TODO: пройти по всем uik(4000 + проверка) и выкачать все данные