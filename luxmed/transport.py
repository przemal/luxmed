from json import JSONDecodeError
from typing import Dict
from typing import List
from typing import Union
from uuid import uuid4

from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import Timeout
from requests import Session

from luxmed.errors import LuxMedError
from luxmed.errors import LuxMedConnectionError
from luxmed.errors import LuxMedTimeoutError
from luxmed.urls import HOST
from luxmed.urls import TOKEN_URL


class LuxMedTransport:
    """Responsible for communication with the API."""

    TOKEN_HEADER_NAME = 'Authorization'

    def __init__(self, user_name: str, password: str,
                 app_uuid: str = None, client_uuid: str = None, lang_code: str = 'en'):
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
            'Host': HOST,
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
        try:
            return response.json()
        except JSONDecodeError:
            return

    def authenticate(self):
        """Authenticates session with the credentials given during initialization."""
        token = self._request('POST', TOKEN_URL, data={
            'client_id': self.client_uuid,
            'grant_type': 'password',
            'username': self.user_name,
            'password': self.password})
        self._session.headers[self.TOKEN_HEADER_NAME] = token['token_type'] + ' ' + token['access_token']

    def request(self, method: str, url: str, **kwargs) -> Union[Dict, List, None]:
        """Sends request via given HTTP method to a URL with all the required headers set.

        Args:
            method: The HTTP method.
            url: Requested URL.
            **kwargs: Remaining request parameters forwarded to the underlying `requests.request` method.

        Returns:
            Parsed JSON or None when not available.
        """
        if self.TOKEN_HEADER_NAME not in self._session.headers:
            self.authenticate()
        return self._request(method, url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request('DELETE', url, **kwargs)

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs):
        return self.request('POST', url, **kwargs)
