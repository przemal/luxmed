import pytest

from luxmed.visits import LuxMedVisits


@pytest.fixture(scope='module')
def visits(authenticated_transport):
    return LuxMedVisits(authenticated_transport)


@pytest.mark.vcr('warsaw_internist_visits.yaml')
def test_find_warsaw_internist_visits(visits, from_date, to_date, payer_id):
    available = visits.find(
        city_id=1, service_id=4502, language_id=10,
        payer_id=payer_id, from_date=from_date, to_date=to_date)
    assert next(available)['ServiceId'] == 4502


@pytest.mark.vcr('warsaw_internist_visits_none.yaml')
def test_find_warsaw_internist_visits_none(visits, from_date, to_date, payer_id):
    available = visits.find(
        city_id=1, service_id=4502, language_id=10,
        payer_id=payer_id, from_date=from_date, to_date=to_date)
    with pytest.raises(StopIteration):
        next(available)
