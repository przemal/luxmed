import pytest

from luxmed.luxmed import LuxMed
from tests.conftest import FIELD_MASK


@pytest.fixture(scope='module')
def luxmed(authenticated_transport):
    luxmed_ = LuxMed(user_name='', password='')
    luxmed_._transport = authenticated_transport
    return luxmed_


@pytest.mark.vcr('cities_languages.yaml')
def test_warsaw_city(luxmed, today):
    assert luxmed.cities(from_date=today)[1] == 'Warszawa'


@pytest.mark.vcr('cities_languages.yaml')
def test_english_language(luxmed, today):
    assert luxmed.languages(from_date=today)[11] == 'english'


@pytest.mark.vcr('city_clinics_services.yaml')
def test_warsaw_clinic(luxmed, today):
    assert luxmed.clinics(city_id=1, from_date=today)[1] == 'LX Warszawa - Al. Jerozolimskie 65/79'


@pytest.mark.vcr('city_clinics_services.yaml')
def test_warsaw_allergist_service(luxmed, today):
    assert luxmed.services(city_id=1, from_date=today)[4387] == 'Konsultacja alergologa'


@pytest.mark.vcr('city_clinics_services_doctors_payers.yaml')
def test_warsaw_allergist_doctor(luxmed, today):
    assert luxmed.doctors(city_id=1, service_id=4387, from_date=today)[16772].startswith('HANNA')


@pytest.mark.vcr('city_clinics_services_doctors_payers.yaml')
def test_warsaw_allergist_payers(luxmed, today):
    assert luxmed.payers(city_id=1, service_id=4387, from_date=today)[0]['Id'] == 10101


@pytest.mark.vcr('user.yaml')
def test_user(credentials, luxmed):
    user_name, password = credentials
    assert luxmed.user()['UserName'] == user_name or FIELD_MASK['UserName']


@pytest.mark.vcr('user_permissions.yaml')
def test_user_permissions(luxmed):
    assert 'Visits' in luxmed.user_permissions()
