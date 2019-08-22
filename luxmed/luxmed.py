from datetime import date
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Union
from uuid import uuid4

from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import Timeout
from requests import Session

from luxmed.errors import LuxMedError
from luxmed.errors import LuxMedConnectionError
from luxmed.errors import LuxMedTimeoutError
from luxmed.transformers import filter_args
from luxmed.transformers import map_id_name
from luxmed.transformers import underscored_named_tuple


class LuxMed:
    """LUX MED Group patient portal (unofficial) API client."""

    HOST = 'portalpacjenta.luxmed.pl'
    BASE_URL = f'https://{HOST}/PatientPortalMobileAPI/api'
    TOKEN_URL = f'{BASE_URL}/token'
    ACCOUNT_URL = f'{BASE_URL}/account'
    USER_URL = f'{ACCOUNT_URL}/user'
    VISITS_URL = f'{BASE_URL}/visits'
    VISIT_TERMS_URL = f'{VISITS_URL}/available-terms'
    VISIT_TERMS_RESERVATION_URL = f'{VISIT_TERMS_URL}/reservation-filter'

    TOKEN_HEADER_NAME = 'Authorization'

    def __init__(self, user_name: str, password: str, app_uuid: str = None, client_uuid: str = None,
                 lang_code: str = 'en'):
        """Args:
            user_name (str): Your LUX MED login.
            password (str): Your LUX MED password.
            app_uuid (str, optional): Application UUID. Defaults to random UUID.
            client_uuid (str, optional): Client UUID. Defaults to random UUID.
            lang_code (str, optional): Two letter (ISO 639-1) language code. Defaults to en.
        """
        self.user_name = user_name
        self.password = password
        self.app_uuid = app_uuid or str(uuid4())
        self.client_uuid = client_uuid or str(uuid4())
        self.lang_code = lang_code

        self._session = Session()
        self._session.headers = {
            'x-api-client-identifier': 'Android',
            'Accept-Language': self.lang_code,
            'Custom-User-Agent': 'Patient Portal; 3.17.0; '
                                 f'{self.app_uuid}; '
                                 'Android; 28; generic_x86 Android SDK built for x86',
            'Host': self.HOST,
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/3.11.0'}

    def _request(self, method: str, url: str, **kwargs):
        response = self._session.request(method, url, **kwargs)
        try:
            response.raise_for_status()
        except HTTPError as error:
            raise LuxMedError.from_response(response) from error
        except ConnectionError as error:
            raise LuxMedConnectionError('Connection failed') from error
        except Timeout as error:
            raise LuxMedTimeoutError('Request timed out') from error
        return response.json()

    def _authenticate(self):
        """Authenticates current session with the credentials given during initialization."""
        token = self._request('POST', self.TOKEN_URL, data={
            'client_id': self.client_uuid,
            'grant_type': 'password',
            'username': self.user_name,
            'password': self.password})
        self._session.headers[self.TOKEN_HEADER_NAME] = token['token_type'] + ' ' + token['access_token']

    def _visit_filters(self, category: str, **kwargs) -> Dict[int, str]:
        return map_id_name(self.get(self.VISIT_TERMS_RESERVATION_URL, params=filter_args(**kwargs))[category])

    def request(self, method: str, url: str, **kwargs) -> Union[Dict, List]:
        """Sends request via given HTTP method to a URL with all the required headers set.

        Args:
            method: The HTTP method.
            url: Requested URL.
            **kwargs: Remaining request parameters forwarded to the underlying `requests.request` method.

        Returns:
            Parsed JSON.
        """
        if self.TOKEN_HEADER_NAME not in self._session.headers:
            self._authenticate()
        return self._request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def cities(self, from_date: date = None) -> Dict[int, str]:
        """Cities the service is available in.

        Args:
            from_date (date): A day in time at which the availability should be queried?? Defaults to the current date.
        """
        return self._visit_filters('Cities', from_date=from_date)

    def clinics(self, city_id: int, from_date: date = None) -> Dict[int, str]:
        """Clinics available in the given city."""
        return self._visit_filters('Clinics', city_id=city_id, from_date=from_date)

    def doctors(self, city_id: int, service_id: int, clinic_id: int = None, from_date: date = None) -> Dict[int, str]:
        """Doctors available in the given city and providing specified service."""
        return self._visit_filters(
            'Doctors', city_id=city_id, clinic_id=clinic_id, from_date=from_date, service_id=service_id)

    def languages(self, from_date: date = None) -> Dict[int, str]:
        """Languages the service is accessible in."""
        return self._visit_filters('Languages', from_date=from_date)

    def services(self, city_id: int, clinic_id: int = None, from_date: date = None) -> Dict[int, str]:
        """Services available in the given city."""
        return self._visit_filters('Services', city_id=city_id, clinic_id=clinic_id, from_date=from_date)

    def user(self) -> NamedTuple:
        """User profile."""
        return underscored_named_tuple(self.get(self.USER_URL))
