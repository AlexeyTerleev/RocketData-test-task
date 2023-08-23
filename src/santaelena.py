from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import asyncio
import aiohttp


result = []


async def get_coords(session, url):
    async with session.get(url=url) as response:
        soup = BeautifulSoup(await response.text(), "html.parser")
        if url is None:
            return {}
        info = soup.find_all("script")
        data = None
        for line in info:
            try:
                data = re.search('.+pageData = "(\[.+\])"', line.text).group(1)
                break
            except AttributeError:
                ...
        data = data.replace("\\", "")
        data = json.loads(data)
        data = data[1][6][0][4]
        coords = {}
        for d in data:
            try:
                coords[d[5][0][0].lower().replace("punto de venta", "").strip()] = d[4][0][1]
            except IndexError:
                ...
        return coords


async def get_page_data(session, url):
    async with session.get(url=url) as response:
        soup = BeautifulSoup(await response.text(), "html.parser")
        maps_url = soup.select("a.elementor-button.elementor-button-link")
        try:
            maps_url = maps_url[0]["href"]
        except IndexError:
            maps_url = None
        cords_dict = await get_coords(session, maps_url)
        rows = soup.select("div.elementor-container.elementor-column-gap-default")
        for row in rows:
            cols = row.select("div.elementor-column-wrap.elementor-element-populated")
            for col in cols:
                try:
                    name = col.find_all("h3", class_="elementor-heading-title")[0].text
                    name = name.replace("\n", " ").strip()
                    info = col.select("div.elementor-text-editor.elementor-clearfix")[0].text.strip()
                    info = info.replace("\n", " ")
                    regex = r"Dirección:(.+)Teléfono:(.+)Horario de atención:(.+)"

                    try:
                        address = re.search(regex, info).group(1)
                        address = " Local ".join(x.strip() for x in address.split("Local"))
                    except AttributeError:
                        address = None
                    try:
                        phones = re.search(regex, info).group(2)
                        phones = re.search("(Contacto:)?(.+)", phones).group(2)
                        phones = phones.strip()
                    except AttributeError:
                        phones = None
                    try:
                        working_hours = re.search(regex, info).group(3)
                        working_hours = working_hours.lower().strip()
                        replace_dct = (("lunes", "mon"), ("sábados", "sat"), ("viernes", "fri"),
                                       ("domingos", "sun"), ("festivos", "holidays"), ("sábado", "sat"),
                                       ("domingo", "sun"), (" a ", " - "), ("/", "-"), ("–", "-"),
                                       ("prestamos servicio 24 horas.", "mon - sun: 12:00 a.m. - 11:59 p.m."),
                                       ("prestamos servicio las 24 horas.", "mon - sun: 12:00 a.m. - 11:59 p.m."),
                                       (" y ", " and "), ("incluye", "and"))
                        for old, new in replace_dct:
                            working_hours = working_hours.replace(old, new)
                        reg = r"([a-z\s-]+:\s*\d{1,2}:\d{2}\s*[ap]\.\s*m\.\s*-\s*\d{1,2}:\d{2}\s*[ap]\.\s*m\.?)"
                        matches = re.finditer(reg, working_hours, re.MULTILINE)
                        working_hours = [m.group(1).strip() for m in matches]

                        tmp = []
                        for period in working_hours:
                            days, time = period.split(':', 1)
                            time_12 = time.split("-")
                            time_24 = []
                            for t in time_12:
                                t = t.replace(".", "").upper().strip()
                                t = t.replace(" ", "")
                                in_time = datetime.strptime(t, "%I:%M%p")
                                time_24.append(datetime.strftime(in_time, "%H:%M"))
                            tmp.append(f"{days} {' - '.join(time_24)}")

                        working_hours = tmp
                    except AttributeError:
                        working_hours = None

                    cords = None
                    for key, value in cords_dict.items():
                        first = key.replace(" ", "").replace("-", "")
                        second = name.lower().replace(" ", "")
                        if first in second or second in first:
                            cords = value
                    if cords is None:
                        print(f"[ERROR] ({name}) cords not found")

                    result.append(
                        {
                            "name": name,
                            "address": address,
                            "latlon": cords,
                            "phones": phones,
                            "working_hours": working_hours,
                        }
                    )
                except IndexError:
                    pass

    print(f"[INFO] url {url} - completed")


async def gather_data():
    main_url = "https://www.santaelena.com.co/tiendas-pasteleria/"
    async with aiohttp.ClientSession() as session:
        response = await session.get(url=main_url)
        soup = BeautifulSoup(await response.text(), "html.parser")
        cols = soup.find_all("div", class_="elementor-col-20")
        urls = [x.find_all("a")[0]["href"] for x in cols]
        tasks = [asyncio.create_task(get_page_data(session, url)) for url in urls]
        await asyncio.gather(*tasks)


def main(path="./data"):
    asyncio.run(gather_data())
    with open(f"{path}/santaelena.json", "w") as file:
        file.write(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
