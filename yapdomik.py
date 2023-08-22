from bs4 import BeautifulSoup
import requests
import json
import re
import asyncio
import aiohttp


result = []


async def get_page_data(session, url):
    async with session.get(url=url) as response:
        soup = BeautifulSoup(await response.text(), "html.parser")
        info = soup.find_all("script")
        data = None
        for line in info:
            try:
                data = re.search("window.initialState = (\{.+\})", line.text).group(1)
                break
            except AttributeError:
                ...
        return json.loads(data)


def get_working_hours(working_hours):
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    working_hours = [x for x in working_hours if x['type'] == "default"]
    dct = {}
    for line in working_hours:
        try:
            start = line['from'] // 60 % 24
            end = line['to'] // 60 % 24
            start_after_dot = line['from'] % 60
            end_after_dot = line['to'] % 60
            dct[line['day']] = (
                    f"{start if start > 9 else '0' + str(start)}:{start_after_dot if start_after_dot else '00'} - "
                    f"{end if end > 9 else '0' + str(end)}:{end_after_dot if end_after_dot else '00'}"
            )
        except TypeError:
            print(f"[ERROR] unexpected start or end time {line}")

    res = {}
    start_key, start_value = 1, dct[1]
    for key, value in dct.items():
        if start_value == value:
            continue
        if start_key == key - 1:
            res[days[start_key - 1]] = start_value
        else:
            res[f"{days[start_key - 1]} - {days[key - 2]}"] = start_value
        start_key, start_value = key, value
    if start_key == list(dct.keys())[-1]:
        res[days[start_key - 1]] = start_value
    else:
        res[f"{days[start_key - 1]} - {days[-1]}"] = start_value

    return [f"{key} {value}" for key, value in res.items()]


async def get_city_data(session, city_name):
    global result
    data = await get_page_data(session, f"https://{city_name['translitAlias']}.yapdomik.ru")

    if data is None:
        print(f"[ERROR] bad url https://{city_name['translitAlias']}.yapdomik.ru")
        return

    city = data["city"]
    shops = data["shops"]

    result += [{
        "name": "Японский Домик",
        "address": f"{city['name']}, {shop['address']}",
        "latlon": [shop['coord']['latitude'], shop['coord']['longitude']],
        "phones": [city["callCenterPhoneParameters"]["number"]],
        "working_hours": get_working_hours(shop["workingHours"])
    } for shop in shops]

    print(f"[INFO] city {city_name['name']} completed")


async def gather_data():
    url = "https://omsk.yapdomik.ru"
    async with aiohttp.ClientSession() as session:
        data = await get_page_data(session, url)

        if data is None:
            print(f"[ERROR] something went wrong")

        tasks = [asyncio.create_task(get_city_data(session, city_name)) for city_name in data["cityList"]]
        await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data())
    with open("yapdomik.json", "w") as file:
        file.write(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
