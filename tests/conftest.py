import hashlib
import json
import re
from copy import deepcopy
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from itertools import chain
from os import environ
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from uuid import uuid4

import pytest
from vcr import VCR
from vcr.filters import replace_post_data_parameters

from luxmed.transport import LuxMedTransport
from luxmed.urls import VISIT_RESERVE_TEMPORARY_URL
from luxmed.urls import VISIT_RESERVE_URL
from luxmed.urls import VISIT_TERMS_URL
from luxmed.urls import VISIT_TERMS_VALUATION_URL


DATE_TIME = datetime(year=2012, month=12, day=12, hour=12, minute=12, second=12, tzinfo=timezone.utc)


DATE_TIME_FORMATS = (
    '%Y-%m-%dT%H:%M:%S%z',  # ISO-8601
    '%d %b %Y')


FIELD_MASK = {
    'access_token': 'S3Cr3tT0k3n',
    'refresh_token': '9f7fe8cb-74f6-eeee-896c-615bfd7ee589',
    'AccountId': '2f2b85e0-e56a-4939-beff-a5fe9edb078f',
    'UserName': 'user',
    'FirstName': 'John',
    'LastName': 'Doe'}


ID_RANGE = range(10100, 11000)


PAYER = {
    'Id': 10101,
    'IsFeeForService': False,
    'Name': 'Acme Corporation'}


PAYER_DETAILS = {
    'PayerId': PAYER['Id'],
    'PayerName': PAYER['Name'],
    'ContractId': 1000,
    'ProductInContractId': 1001,
    'ProductId': 1010,
    'BrandId': 1011,
    'ProductElementId': 1101,
    'ServaId': 0,  # requested service id
    'ServaAppId': 0}


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


def replace_pattern_in_values(data: Dict, pattern: str, replacement: str, pattern_flags: int = re.IGNORECASE):
    """Replace given pattern with a replacement string in all values."""
    replace = re.compile(pattern, flags=pattern_flags)
    for key, value in data.items():
        try:
            new_value, replaced_count = replace.subn(replacement, value)
        except TypeError:
            continue
        if replaced_count > 0:
            data[key] = new_value


def replace_with_datetime(source: str, target: datetime) -> str:
    """Replace date and/or time string with custom target while preserving source format.


    Args:
        source (str): Date and/or time string to be replaced.
        target (datetime): Replace with this.

    Returns:
        Date and/or time string.

    Raises:
        ValueError: When source datetime format is unknown.
    """
    for format_ in DATE_TIME_FORMATS:
        try:
            datetime.strptime(source, format_)
        except ValueError:
            continue
        else:
            return target.strftime(format_)
    raise ValueError('Unknown datetime format.')


def filter_request(request):
    """Prevents secret request data from being saved in the cassettes."""
    request = deepcopy(request)  # do not destroy the original request
    if 'Authorization' in request.headers:
        request.headers['Authorization'] = 'bearer XYZ'

    # protect payer
    if VISIT_TERMS_URL in request.uri:
        request.uri = re.sub(
            '(filter.PayerId=)(?:\d+)',
            r'\g<1>{}'.format(PAYER['Id']),
            request.uri)

    replace_post_data_parameters(request, {
        'username': 'user',
        'password': 'password'})

    if request.method == 'POST' and request.body:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            pass
        else:
            if (request.uri.startswith(VISIT_RESERVE_TEMPORARY_URL)
                or request.uri.startswith(VISIT_TERMS_VALUATION_URL)) \
                    and 'PayerDetailsList' in data:
                payer_details_ = PAYER_DETAILS.copy()
                payer_details_['ServaId'] = data['ServiceId']
                data['PayerDetailsList'] = [payer_details_]

            if request.uri.startswith(VISIT_RESERVE_URL) and 'PayerData' in data:
                payer_details_ = PAYER_DETAILS.copy()
                payer_details_['ServaId'] = data['ServiceId']
                data['PayerData'] = payer_details_

            request.body = json.dumps(data).encode()

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

    # doctor appointments
    for key in ('AgregateAvailableVisitTerms', 'AgregateAvailableAdditionalVisitTerms'):
        if key not in data:
            continue
        data[key] = data[key][:2]
        for visits_index in range(len(data[key])):
            data[key][visits_index]['AvailableVisitsTermPresentation'] = \
                data[key][visits_index]['AvailableVisitsTermPresentation'][:2]

    for visits in chain(
            data.get('AgregateAvailableVisitTerms', []),
            data.get('AgregateAvailableAdditionalVisitTerms', [])):
        for visit in visits['AvailableVisitsTermPresentation']:
            visit['Doctor']['Name'] = hashlib.sha1(visit['Doctor']['Name'].encode()).hexdigest()
            payer_details_ = PAYER_DETAILS.copy()
            payer_details_['ServaId'] = visit['ServiceId']
            visit['PayerDetailsList'] = [payer_details_]

    if 'CorrelationId' in data:
        data['CorrelationId'] = str(uuid4())

    # doctor appointment reservation
    for visit in data.get('VisitTermVariants', []):
        visit['ValuationDetail']['PayerData'] = PAYER_DETAILS

    # examination results
    try:
        data['MedicalExaminationsResults'] = data['MedicalExaminationsResults'][:2]
    except (KeyError, TypeError):  # TypeError is raised for user permissions data
        pass
    else:
        id_range = iter(ID_RANGE)
        for examination in data['MedicalExaminationsResults']:
            # protect examination ID
            examination_id = str(next(id_range))
            examination['MedicalExaminationId'] = examination_id
            for link in chain(examination['DownloadLinks'], examination['Links']):
                replace_pattern_in_values(link, '[0-9]{5,10}', examination_id)

            # change examination date
            for name, date_time in examination['Date'].items():
                examination['Date'][name] = replace_with_datetime(date_time, DATE_TIME)

    # string body messes up diff causing CannotOverwriteExistingCassetteException
    response['body']['string'] = json.dumps(data).encode()
    return response


@pytest.fixture(scope='session')
def app_uuid():
    return '3a0cab8a-84f2-4fce-aff3-ddd623e0c4f4'


@pytest.fixture(scope='session')
def client_uuid():
    return 'aeb7c10a-ae52-4593-86b2-195df87f4081'


@pytest.fixture(scope='session')
def from_date():
    return date(year=2019, month=8, day=22)


@pytest.fixture(scope='session')
def to_date():
    return date(year=2019, month=8, day=28)


@pytest.fixture(scope='session')
def today():
    return date(year=2019, month=8, day=22)


@pytest.fixture(scope='session')
def year_ago(today):
    return today - timedelta(days=365)


@pytest.fixture(scope='session')
def vcr_cassette_dir():
    return str(Path(__file__).parent / 'cassettes')


@pytest.fixture(scope='session')
def vcr_config():
    return dict(
        before_record_request=filter_request,
        before_record_response=filter_response)


@pytest.fixture(scope='session')
def payer_id(record_mode):
    if record_mode != 'none':
        try:
            return int(environ['LUXMED_PAYER'])
        except (KeyError, ValueError):
            raise pytest.skip('Recording requires payer ID present in the LUXMED_PAYER environment variable.')
    return PAYER['Id']


@pytest.fixture(scope='session')
def payer_details():
    return PAYER_DETAILS


@pytest.fixture(scope='session')
def credentials(record_mode):
    user_name = environ.get('LUXMED_USER')
    password = environ.get('LUXMED_PASS')
    if record_mode != 'none' and not (user_name and password):
        pytest.skip('Recording requires LUXMED_USER and LUXMED_PASS variables present in the environment.')
    return user_name, password


@pytest.fixture(scope='session')
def authenticated_transport(app_uuid, client_uuid, credentials, record_mode, vcr_cassette_dir, vcr_config):
    user_name, password = credentials
    transport = LuxMedTransport(
        user_name=user_name,
        password=password,
        app_uuid=app_uuid,
        client_uuid=client_uuid)
    with VCR(cassette_library_dir=vcr_cassette_dir, record_mode=record_mode).\
            use_cassette('authenticated.yaml', **vcr_config):
        transport.authenticate()
    yield transport
