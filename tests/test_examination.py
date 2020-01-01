import pytest

from luxmed.examination import LuxMedExamination


@pytest.fixture(scope='module')
def examination(authenticated_transport):
    return LuxMedExamination(authenticated_transport)


@pytest.mark.vcr('examination_results.yaml')
def test_examination_results(examination, today, year_ago):
    assert 'MedicalExaminationId' in next(examination.results(from_date=year_ago, to_date=today))


@pytest.mark.vcr('examination_results.yaml')
def test_examination_result_action_wrapper(examination, today, year_ago):
    assert hasattr(next(examination.results(from_date=year_ago, to_date=today)), 'details')
