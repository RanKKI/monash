import re
from lxml.html import tostring


class Unit(object):

    def __init__(self, code, name, faculty):
        self.code = code
        self.name = name
        self.faculty = faculty

        # offer's info
        self.locations = []
        self.s1 = False
        self.s2 = False
        self.prerequisites = ""
        self.prohibitions = ""

        # assessment's info
        self.examination = 0
        self.assessment = 0

    def parse_offers(self, data: list):
        # parse locaiton, semester info
        offer_info = data[0]
        restrictions = data[1].xpath("./*") if len(data) > 1 else None
        if offer_info.xpath("text()")[0] == "Not offered in 2019":
            return
        data = offer_info[2:]
        assert len(data) % 2 == 0, len(data)
        for i in range(0, len(data), 2):
            location = data[i].xpath(".//a/text()")[0]
            if location not in ["Clayton", "Caulfield"]:
                continue
            self.locations.append(location)
            for time in map(lambda x: x.xpath("text()")[0], data[i + 1]):
                if "First" in time:
                    self.s1 = True
                elif "Second" in time:
                    self.s2 = True

        # parse restriction
        if not restrictions:
            return

        if len(restrictions) % 2 != 0:
            split_loc = [i for i, v in enumerate(
                restrictions) if "" in str(v)][1]

        _t = ""
        for restriction in restrictions:
            current_text = restriction.xpath(".//text()")[0]
            if "hbk-preamble-heading" in str(tostring(restriction)):
                _t = current_text.lower()
                continue
            if not hasattr(self, _t):
                continue
            value = " ".join(
                map(lambda x: x.strip(), restriction.xpath(".//text()")))
            setattr(self, _t, getattr(self, _t) + f" {value}")

    def parse_assessment(self, assessments, flag=False):
        if not isinstance(assessments, list):
            raise ValueError("assessment's data are not list")
        for assessment in assessments:
            p = re.findall("examination \((\d{2,3})%\)", assessment.lower())
            if len(p) == 1:
                self.examination = int(p[0])
                self.assessment = 100 - self.examination
                break
            p = re.findall("examination: (\d{2,3})%", assessment.lower())
            if len(p) == 1:
                self.examination = int(p[0])
                self.assessment = 100 - self.examination
                break
            percent = re.findall("(\d{2,3})%", assessment)
            if len(percent) == 1 and "exam" in assessment.lower():
                self.examination = int(percent[0])
                self.assessment = 100 - self.examination
                break
            elif len(percent) == 1 and ("in-semester assessment" in assessment.lower() or "within semester assessment" in assessment.lower()):
                self.assessment = int(percent[0])
                self.examination = 100 - self.assessment
                break
            elif len(percent) == 2 and flag != True:
                for symbol in [";", ",", "+"]:
                    if symbol not in assessment:
                        continue
                    self.parse_assessment(assessment.split(symbol), True)
                    break
            elif "This unit is graded pass grade only".lower() in assessment.lower():
                self.examination = -1
                self.assessment = -1
            elif "exam" not in assessment.lower():
                self.examination = 0
                self.assessment = 100
            elif "Students are required" in assessment:
                continue
            else:
                print(" ".join(assessments))
                self.examination = int(input("exam > "))
                self.assessment = 100 - self.examination

    def __str__(self):
        return f"<Unit {self.code}>"

    def as_dict(self):
        return {
            "unit_code": self.code,
            "unit_name": self.name,
            "faculty": self.faculty,
            "examination": self.examination,
            "assessment": self.assessment,
            "s1": self.s1,
            "s2": self.s2,
            "locations": ",".join(self.locations),
            "prerequisites": self.prerequisites,
            "prohibitions": self.prohibitions,
        }
