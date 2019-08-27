import json
from copy import deepcopy
from datetime import date
from typing import Dict
from typing import Iterable
from typing import List

import pytest
from vcr.filters import replace_post_data_parameters


FIELD_MASK = {
    'access_token': 'S3Cr3tT0k3n',
    'refresh_token': '9f7fe8cb-74f6-eeee-896c-615bfd7ee589',
    'AccountId': '2f2b85e0-e56a-4939-beff-a5fe9edb078f',
    'UserName': 'user',
    'FirstName': 'John',
    'LastName': 'Doe'}


PAYER = {
    'Id': 10101,
    'IsFeeForService': False,
    'Name': 'Acme Corporation'}


def sort_by_key(data: List[Dict], key: str = 'Id') -> Iterable:
    """Sorts list of dictionaries by the given key.

    Args:
        data (list of dict): List of dictionaries to sort.
        key (str): Name of the key to sort dictionaries by.  Defaults to 'Id'.

    Returns:
        Sorted list of dictionaries.
    """
    return sorted(data, key=lambda d: d[key])


def first_words(sentence: str, limit: int = 1) -> str:
    return ' '.join(sentence.split(' ')[:limit])


def shrink_words_in_key(list_: List[Dict], key: str = 'Name', to: int = 1) -> Iterable[Dict]:
    for dict_ in list_:
        yield {**dict_, key: first_words(dict_[key], limit=to)}


def filter_request(request):
    """Prevents secret request data from being saved in the cassettes."""
    request = deepcopy(request)  # do not destroy the original request
    if 'Authorization' in request.headers:
        request.headers['Authorization'] = 'bearer XYZ'
    replace_post_data_parameters(request, {
        'username': 'user',
        'password': 'password'})
    return request


def filter_response(response):
    """Prevents large and secret response data from being saved in the cassettes."""
    try:
        data = json.loads(response['body']['string'])
    except json.JSONDecodeError:
        return response

    for key in FIELD_MASK:
        if key in data:
            data[key] = FIELD_MASK[key]

    if 'DefaultPayer' in data:
        data['DefaultPayer'] = [PAYER]
    if 'Payers' in data:
        data['Payers'] = [PAYER]

    # protect doctor names
    try:
        data['Doctors'] = list(shrink_words_in_key(data['Doctors']))
    except KeyError:
        pass

    # can become large and fraction of that is more than enough for the tests
    for key, max_length in [('Cities', 10), ('Clinics', 20), ('Doctors', 20), ('Services', 100)]:
        try:
            data[key] = sort_by_key(data[key])[:max_length]
        except KeyError:
            pass

    # string body messes up diff causing CannotOverwriteExistingCassetteException
    response['body']['string'] = json.dumps(data).encode()
    return response


@pytest.fixture(scope='module')
def app_uuid():
    return '3a0cab8a-84f2-4fce-aff3-ddd623e0c4f4'


@pytest.fixture(scope='module')
def client_uuid():
    return 'aeb7c10a-ae52-4593-86b2-195df87f4081'


@pytest.fixture(scope='module')
def from_date():
    return date(year=2019, month=8, day=22)


@pytest.fixture(scope='module')
def vcr_config():
    return dict(
        before_record_request=filter_request,
        before_record_response=filter_response)
