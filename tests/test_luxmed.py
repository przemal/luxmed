from datetime import date

import pytest

from luxmed.errors import LuxMedAuthenticationError
from luxmed.luxmed import LuxMed


APP_UUID = '3a0cab8a-84f2-4fce-aff3-ddd623e0c4f4'
CLIENT_UUID = 'aeb7c10a-ae52-4593-86b2-195df87f4081'


@pytest.fixture(scope='module')
def luxmed():
    return LuxMed(
        user_name='user',
        password='password',
        app_uuid=APP_UUID,
        client_uuid=CLIENT_UUID)


@pytest.fixture(scope='module')
def from_date():
    return date(year=2019, month=8, day=22)


@pytest.mark.vcr()
def test_failed_authentication():
    luxmed = LuxMed(user_name='username', password='password')
    with pytest.raises(LuxMedAuthenticationError):
        luxmed._authenticate()


@pytest.mark.vcr()
def test_authentication(luxmed):
    luxmed._authenticate()
    assert luxmed.TOKEN_HEADER_NAME in luxmed._session.headers


@pytest.mark.vcr()
def test_warsaw_city(luxmed, from_date):
    assert luxmed.cities(from_date=from_date)[1] == 'Warszawa'


@pytest.mark.vcr()
def test_warsaw_clinic(luxmed, from_date):
    assert luxmed.clinics(city_id=1, from_date=from_date)[1] == 'LX Warszawa - Al. Jerozolimskie 65/79'


@pytest.mark.vcr()
def test_warsaw_allergist_doctor(luxmed, from_date):
    assert luxmed.doctors(city_id=1, service_id=4387, from_date=from_date)[16772].startswith('HANNA')


@pytest.mark.vcr()
def test_english_language(luxmed, from_date):
    assert luxmed.languages(from_date=from_date)[11] == 'english'


@pytest.mark.vcr()
def test_warsaw_allergist_service(luxmed, from_date):
    assert luxmed.services(city_id=1, from_date=from_date)[4387] == 'Konsultacja alergologa'


@pytest.mark.vcr()
def test_user(luxmed):
    assert luxmed.user().user_name == 'user'
