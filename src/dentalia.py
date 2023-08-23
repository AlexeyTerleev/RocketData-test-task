from bs4 import BeautifulSoup
import requests
import json
import re
import asyncio
import aiohttp


location = []
clinics = {}


async def get_page_data(session, url):
    async with session.get(url=url) as response:
        soup = BeautifulSoup(await response.text(), "html.parser")
        script = soup.find(id="jet-engine-frontend-js-extra")
        dct_str = re.search("var JetEngineSettings=({.+})", script.text).group(1)
        dct = json.loads(dct_str)

        endpoint = dct["ajaxlisting"]
        header = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        query = (f'action=jet_engine_ajax&handler=get_listing&'
                 f'page_settings%5Bpost_id%5D=5883&'
                 f'page_settings%5Bqueried_id%5D=1288%7CWP_Post&'
                 f'page_settings%5Belement_id%5D=c1b6043&'
                 f'page_settings%5Bpage%5D=1&listing_type=elementor')
        response = requests.post(endpoint, headers=header, data=query)

        parsed = json.loads(response.text)

        html = parsed["data"]["html"]
        soup = BeautifulSoup(html, "html.parser")
        all_items = soup.find_all("div", class_="jet-listing-grid__item")
        for item in all_items:

            idx = item["data-post-id"]

            if clinics.get(idx, 0):
                continue

            name = item.find("h3", class_="elementor-heading-title").text

            address, phones, working_hours = [x.text for x in
                                              item.find_all("div", class_="jet-listing-dynamic-field__content")]
            phones = [x.strip() for x in re.search('.+: (.+)', phones).group(1).split("\n") if x.strip() != ""]
            working_hours = [x.strip() for x in working_hours.split("\n") if x.strip() != ""]
            clinics[idx] = {
                "name": name,
                "address": address,
                "phones": phones,
                "working_hours": working_hours,
            }

    print(f"[INFO] url {url} - completed")


async def get_locations(session, url):
    global location
    async with session.get(url=url) as response:
        soup = BeautifulSoup(await response.text(), "html.parser")
        data = soup.find_all("div", class_="google-provider")
        data = data[0]["data-markers"]
        location = json.loads(data)
    print(f"[INFO] collecting locations - completed")


async def gather_data():
    main_url = "https://dentalia.com/"
    async with aiohttp.ClientSession() as session:
        response = await session.get(url=main_url)
        soup = BeautifulSoup(await response.text(), "html.parser")
        urls = [x["id"] for x in soup.find_all("section", class_="LinkToClinic")]
        tasks = [asyncio.create_task(get_page_data(session, url)) for url in urls]
        tasks.append(asyncio.create_task(get_locations(session, "https://dentalia.com/clinica/")))
        await asyncio.gather(*tasks)


def main(path="./data"):
    print(f"[INFO] starting collecting (dentilia)")
    asyncio.run(gather_data())

    for loc in location:
        try:
            clinics[str(loc["id"])]["latlon"] = [float(loc["latLang"]["lat"]), float(loc["latLang"]["lng"])]
        except KeyError:
            print(f"[ERROR] id {loc['id']} - not found")

    with open(f"{path}/dentalia.json", "w") as file:
        file.write(json.dumps(list(clinics.values()), indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
