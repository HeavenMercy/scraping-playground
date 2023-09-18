from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

class VaCourtsTool:
    NAMES_KEY = 'courtName'
    FIPS_KEY = 'courtFips'
    BASE_URL = 'https://eapps.courts.state.va.us/gdcourts'

    def __init__(self, debug:bool = False) -> None:
        self._debug :bool = debug
        self._session :requests.Session = None

        self._court_data :dict = {}

    def _dprint(self, *input):
        if self._debug: print(*input)

    def initialize(self):
        self._session = None
        try:
            self._dprint(f"initializing scraper...")

            sess = requests.Session()
            sess.headers.update({
                'Cache-Control': 'max-age=0',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',

                'Host': 'eapps.courts.state.va.us',
                'Origin': 'https://eapps.courts.state.va.us',
                'Referer': f'{self.BASE_URL}/caseSearch.do'
            })

            sess.get(f'{self.BASE_URL}/landing.do?landing=landing')

            resp = sess.post(f'{self.BASE_URL}/landing.do', data={'accept':'Accept'})

            if resp.status_code != 200:
                self._dprint(f'failed to init the session {resp.status_code}')
                return (False, 'failed to init the session', resp.status_code)

            if self._debug:
                with open('caught.html', 'wb') as f:
                    f.write(resp.content)

            self._court_data = {}
            bs = BeautifulSoup(resp.text, 'lxml')

            for _input in bs.find_all('input', {'type':'hidden'}):
                _iname = _input.get('name', '')
                if _iname != '':
                    if _iname not in self._court_data: self._court_data[_iname] = []
                    self._court_data[_iname].append(_input.get('value', ''))

            self._dprint(f"Hidden courts data found ({self.get_courts_count()})")

            self._session = sess
            return (True,)
        except Exception as e:
            self._dprint(f"An error occured:", e)
            return (False, -1, e)


    def _get_case_formdata(self, courtFip: str, date: datetime, _next:bool = False):
        formdata = {
            'formAction': None,
            'curentFipsCode': courtFip,
            'searchTerm': self._date_to_string(date),
            'searchHearingTime': None,
            'searchCourtroom': None,
            'lastName': None,
            'firstName': None,
            'middleName': None,
            'suffix': None,
            'searchHearingType': None,
            'searchUnitNumber': None,
            'searchFipsCode': courtFip,
            'unCheckedCases': None
        }

        if not _next: formdata['caseSearch'] = 'Search'
        else: formdata['caseInfoScrollForward'] = 'Next'

        return formdata

    def _case_row_to_json(self, case):
        try:
            data = {}
            _data = case.find_all('td')

            # data['Details URL'] = f"{self.BASE_URL}/{_data[1].find('a')['href']}"
            data['Case #'] = _data[1].text.strip()
            data['Defendant'] = _data[2].text.strip()
            data['Complainant'] = _data[3].text.strip()
            data['Charge'] = _data[4].text.strip()
            data['Hearing Time'] = _data[5].text.strip()
            data['Result'] = _data[6].text.strip()

            return data
        except Exception as e:
            self._dprint(f"parsing failed", e)

    def get_cases_for(self, courtIdx: int, date: datetime):
        """_summary_

        Args:
            courtIdx (int): the court Idx
            date (DateTime): the date to extract

        Returns:
            _type_: tuple with a boolean telling if success
        """
        courtName = self._court_data[self.NAMES_KEY][courtIdx]
        courtFip = self._court_data[self.FIPS_KEY][courtIdx]

        try:
            resp = self._session.post(f'{self.BASE_URL}/changeCourt.do',
                data={
                    'electedCourtsName': courtName,
                    'selectedCourtsFipCode': courtFip,
                    'sessionCourtsFipCode': '' } )

            if resp.status_code == 200:
                resp = self._session.get(f'{self.BASE_URL}/caseSearch.do?fromSidebar=true&' \
                    + 'searchLanding=searchLanding&searchType=hearingDate&searchDivision=T&searchFipsCode={courtFip}&curentFipsCode={courtFip}')

            if resp.status_code != 200:
                self._dprint(f'failed to change court ({resp.status_code})')
                return (False, 'failed to change court', resp.status_code)

            # -------------------------------------------------------------------------------------------------------

            _cases = []
            _next = False
            while True:
                resp = self._session.post(f'{self.BASE_URL}/caseSearch.do',
                    data=self._get_case_formdata(courtFip, date, _next) )

                if resp.status_code != 200: break

                bs = BeautifulSoup(resp.content, 'lxml')
                for case in bs.find_all('tr', {'class': ['evenRow', 'oddRow']}):
                    case = self._case_row_to_json(case)
                    case['Hearing Date'] = date
                    case['Court FIP'] = courtFip
                    case['Court Name'] = courtName
                    _cases.append( case )

                _next = True
                if 'value="Next"' not in resp.text: break


            if resp.status_code != 200:
                self._dprint(f'failed to extract court data ({resp.status_code})')
                return (False, 'failed to extract court data', resp.status_code)

            self._dprint(f"{self._date_to_string(case['Hearing Date'])}: court '{case['Court Name']}' data extracted...", len(_cases))
            if self._debug: # this is where we stopped
                with open('caught.html', 'wb') as f:
                    f.write(resp.content)

            return (True, _cases)
        except Exception as e: return (False, e)


    def get_courts_count(self):
        return min(
            len(self._court_data[self.NAMES_KEY]),
            len(self._court_data[self.FIPS_KEY]))

    def get_all_cases(self, _from: datetime, _to: datetime = None):
        if _to == None: _to = _from

        _cases = []
        exception = None

        current = _from
        while current <= _to:
            try:
                self._dprint(f"# --- extracting data from {self._date_to_string(current)}...")
                for i in range(self.get_courts_count()):
                    result = self.get_cases_for(i, current)
                    if result[0]: _cases.extend(result[1])
                    else: raise result[1]

                current = current + timedelta(days=1)
                self._dprint(self._date_to_string(current), self._date_to_string(_to), "can move on?", (current <= _to))
            except Exception as e:
                exception = e
                self._dprint('an error occured:', e)
                break

        self._dprint(f"# --- extracted {len(_cases)} cases from {self._date_to_string(_from)} to {self._date_to_string(current)}")
        return (exception == None, _cases, exception)

    def _date_to_string(self, date: datetime):
        return date.strftime('%m/%d/%Y')

