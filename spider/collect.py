import os
import json

import requests
from lxml import etree
from lxml.html import tostring

from models import Unit

base_url = "http://www.monash.edu/pubs/2019handbooks/units"

urls = {
    "/index-byfaculty-ada.html": "Art, Design and Architecture",
    "/index-byfaculty-it.html": "Information Technology",
    "/index-byfaculty-arts.html": "Arts",
    "/index-byfaculty-bus.html": "Business and Economics",
    "/index-byfaculty-edu.html": "Education",
    "/index-byfaculty-eng.html": "Engineering",
    "/index-byfaculty-law.html": "Law",
    "/index-byfaculty-med.html": "Medicine, Nursing and Health Sciences",
    "/index-byfaculty-pha.html": "Pharmacy and Pharmaceutical Sciences",
    "/index-byfaculty-sci.html": "Science"
}


def get_units():
    units_object = []

    for url in urls.keys():
        file_path = f"cache/{url}"
        if not os.path.exists(file_path):
            html = requests.get(base_url + url).text
            print(f"requesting {base_url + url}")
            with open(file_path, "w") as f:
                f.write(html)
        with open(file_path, "r") as f:
            data = etree.HTML(f.read())

        for unit in data.xpath("//*[@id='content_container_']/ul/li"):
            code = unit.xpath(".//a/text()")[0].strip()
            name = unit.xpath("text()")
            if len(name) == 0:
                continue
            units_object.append(Unit(code, name[0].strip(), urls.get(url)))

    return units_object


def get_unit_details(unit, flag=False):
    file_dir = f"cache/{unit.code[:3]}"

    if not os.path.exists(file_dir):
        os.mkdir(file_dir)

    file_path = f"{file_dir}/{unit.code}.html"

    if not os.path.exists(file_path):
        url = f"{base_url}/{unit.code}.html"
        print(f"requesting {url}")
        html = requests.get(url)
        if html.status_code != 200:
            return unit
        with open(file_path, "w") as f:
            f.write(html.text)
    print(f"loading {unit.code}")
    with open(file_path) as f:
        data = etree.HTML(f.read())

    # offer locations
    preamble_data = data.xpath("//div[@class='hbk-preamble ']")
    if len(preamble_data) == 0 and not flag:
        if os.path.exists(file_path):
            os.remove(file_path)
        return get_unit_details(unit, True)
    unit.parse_offers(preamble_data[0])  # TODO BMA1012 out of range
    if unit.locations == []:
        return unit

    # get assessment
    items = data.xpath("//div[@id='content_container_']/*")
    for index, item in enumerate(items):
        if item.xpath("text()")[0] == "Assessment":
            assessment_text = items[index + 1].xpath(".//*/text()")
            unit.parse_assessment(assessment_text)
            break

    return unit


def main():
    full = []
    for unit in get_units():
        if len(unit.code) == 7 and unit.code[3].isnumeric() and int(unit.code[3]) >= 3:
            continue
        elif len(unit.code) == 8 and unit.code[4].isnumeric() and int(unit.code[4]) >= 3:
            continue
        data = get_unit_details(unit)
        if data.locations == []:  # when this unit is not offering Clay or Cau
            continue
        full.append(data.as_dict())
    with open("./output.json", "w") as f:
        json.dump(full, f)


if __name__ == '__main__':
    main()
