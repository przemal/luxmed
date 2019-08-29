import pytest

from luxmed.luxmed import LuxMed


@pytest.fixture(scope='module')
def luxmed(app_uuid, client_uuid):
    luxmed_ = LuxMed(
        user_name='user',
        password='password',
        app_uuid=app_uuid,
        client_uuid=client_uuid)
    return luxmed_


@pytest.mark.vcr('../test_transport/authenticated.yaml')
def test_authentication(luxmed):
    luxmed._transport.authenticate()


@pytest.mark.vcr('cities_languages.yaml')
def test_warsaw_city(luxmed, from_date):
    assert luxmed.cities(from_date=from_date)[1] == 'Warszawa'


@pytest.mark.vcr('cities_languages.yaml')
def test_english_language(luxmed, from_date):
    assert luxmed.languages(from_date=from_date)[11] == 'english'


@pytest.mark.vcr('city_clinics_services.yaml')
def test_warsaw_clinic(luxmed, from_date):
    assert luxmed.clinics(city_id=1, from_date=from_date)[1] == 'LX Warszawa - Al. Jerozolimskie 65/79'


@pytest.mark.vcr('city_clinics_services.yaml')
def test_warsaw_allergist_service(luxmed, from_date):
    assert luxmed.services(city_id=1, from_date=from_date)[4387] == 'Konsultacja alergologa'


@pytest.mark.vcr('city_clinics_services_doctors_payers.yaml')
def test_warsaw_allergist_doctor(luxmed, from_date):
    assert luxmed.doctors(city_id=1, service_id=4387, from_date=from_date)[16772].startswith('HANNA')


@pytest.mark.vcr('city_clinics_services_doctors_payers.yaml')
def test_warsaw_allergist_payers(luxmed, from_date):
    assert luxmed.payers(city_id=1, service_id=4387, from_date=from_date)[0].id == 10101


@pytest.mark.vcr('user.yaml')
def test_user(luxmed):
    assert luxmed.user().user_name == 'user'
