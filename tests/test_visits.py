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


@pytest.mark.vcr('warsaw_internist_visit_reserve.yaml')
def test_warsaw_internist_visit_reserve(visits, payer_details):
    service_id = 4502
    payer = payer_details.copy()
    payer['ServaId'] = service_id

    assert 'ReservedVisitsLimitInfo' in visits.reserve(
        clinic_id=1, doctor_id=10200, room_id=303, service_id=service_id,
        start_date_time='2019-08-22T09:00:00+02:00', payer_data=payer
    )


@pytest.mark.vcr('visit_cancel.yaml')
def test_visit_cancel(visits):
    visits.cancel(0)
