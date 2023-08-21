from bs4 import BeautifulSoup
import requests
import urllib.request
from requests_html import HTMLSession
import json
import re


def get_info(url: str) -> list:

    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    script = soup.find(id="jet-engine-frontend-js-extra")
    dct_str = re.search('var JetEngineSettings=({.+})', script.text).group(1)
    dct = json.loads(dct_str)

    result = []
    page_num = 1

    # while True:
        # print(page_num)
    endpoint = dct["ajaxlisting"]
    header = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    query = (f'action=jet_engine_ajax&handler=get_listing&'
             f'page_settings%5Bpost_id%5D=5883&'
             f'page_settings%5Bqueried_id%5D=344706%7CWP_Post&'
             f'page_settings%5Belement_id%5D=c1b6043&'
             f'page_settings%5Bpage%5D={page_num}&listing_type=elementor&isEditMode=false')
    response = requests.post(endpoint, headers=header, data=query)
    # page_num += 1
    # if not response:
    #     break
    parsed = json.loads(response.text)

    # print(json.dumps(parsed, indent=4))

    html = parsed["data"]["html"]
    soup = BeautifulSoup(html, "html.parser")
    all_items = soup.find_all("div", class_="jet-listing-grid__item")
    for item in all_items:

        idx = item["data-post-id"]
        name = item.find("h3", class_="elementor-heading-title").text

        address, phones, working_hours = [x.text for x in
                                          item.find_all("div", class_="jet-listing-dynamic-field__content")]
        phones = [x.strip() for x in re.search('.+: (.+)', phones).group(1).split("\n") if x.strip() != ""]
        working_hours = [x.strip() for x in working_hours.split("\n") if x.strip() != ""]
        result.append(
            {
                "id": idx,
                "name": name,
                "address": address,
                "phones": phones,
                "working_hours": working_hours,
            }
        )

    return result


def get_location(url: str) -> None:
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    data = soup.find_all("div", class_="google-provider")
    dct_str = data[0]["data-markers"]
    dct = json.loads(dct_str)
    return dct


def main():
    url = 'https://dentalia.com/clinica/'
    get_info(url)
    print()
    get_location(url)


if __name__ == '__main__':
    main()
