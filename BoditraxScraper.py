import requests_html
import browser_cookie3
import re
import json
from datetime import datetime
from time import sleep
import os


class BoditraxScraper:
    """
        Connect to bodytrax.cloud and read all tracked attributes and dump them to a json file
    """

    def __init__(self) -> None:
        self._session: requests_html.HTMLSession = requests_html.HTMLSession()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0"
        })

        # what attributes shall be tracked
        self._trackedAttributes = ['Weight', 'Muscle', 'fat', 'Water', 'Bone', 'LegMuscleScore', 'PhaseAngle',
                                   'FatFree',
                                   'VisceralFat', 'MetabolicAge', 'BasalMetabolicRate', 'PhysiqueScore']

        # where the json files will be stored
        self._outDir = 'data/' + datetime.today().strftime('%Y-%m-%d') + '/'

    def scrape(self) -> None:
        # create output dir if it does not exist
        if not os.path.exists(self._outDir):
            os.makedirs(self._outDir)

        # get cookies  from the browser
        for domain_name in ["identity.boditrax.com", "boditrax.cloud", "member.boditrax.cloud"]:
            self._session.cookies.update(browser_cookie3.load(domain_name=domain_name))

        # track all attributes
        for attribute in self._trackedAttributes:
            r = self._session.get('https://member.boditrax.cloud/Result/%s/Track' % attribute)

            max_year = int(re.search(r"var maxYear = (\d*);", r.text)[1])
            min_year = int(re.search(r"var minYear = (\d*);", r.text)[1])
            values = list()

            javascript_var = 'readings'
            if attribute == 'PhysiqueScore':
                # for some reason, only the Physique Score has a different javascript variable name
                javascript_var = 'allScans'

            for year in range(max_year, min_year - 1, -1):
                url = "https://member.boditrax.cloud/Result/%s/Track?year=%s" % (attribute, year)
                r = self._session.get(url)
                if r.ok:
                    try:
                        values_string = re.search(r"var %s = JSON.parse\(\'(.*)\'\);" % javascript_var, r.text)[1]
                        values.append(json.loads(values_string))
                    except TypeError:
                        print("Error loading value '%s' from url '%s'" % (javascript_var, url))
                    sleep(1)
                else:
                    raise ConnectionError("Not able to get url '%s': '%s'" % (url, r.status_code))

            # dump all values in a file
            with open(self._outDir + attribute + '.json', 'w') as f:
                json.dump(values, f)


b = BoditraxScraper()
b.scrape()
